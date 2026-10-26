"""Catch lost telemetry, contaminated trials and premature conclusions."""
import importlib.util
import json
import os
import shutil
from pathlib import Path
import sys
import subprocess
import tempfile
from types import SimpleNamespace
import unittest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / 'scripts/benchmark_architecture.py'
if SCRIPT.exists():
    SPEC = importlib.util.spec_from_file_location('architecture_campaign', SCRIPT)
    BENCH = importlib.util.module_from_spec(SPEC)
    SPEC.loader.exec_module(BENCH)
else:
    BENCH = None


class Campaign(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(BENCH, 'Architecture campaign runner is not implemented')

    def test_missing_usage_is_unknown_not_zero(self):
        result = BENCH.summarize_events([{'type': 'turn.failed', 'error': {'message': 'offline'}}])
        self.assertIsNone(result['usage'])
        self.assertEqual(result['usage_status'], 'NOT_VERIFIED')
        self.assertEqual(result['status'], 'FAIL')

    def test_nested_exit_failure_and_duplicate_events_count_once(self):
        started = {'type': 'item.started', 'item': {'id': 'a', 'type': 'command_execution',
                   'command': 'python validate.py', 'status': 'in_progress'}}
        finished = {'type': 'item.completed', 'item': {'id': 'a', 'type': 'command_execution',
                    'command': 'python validate.py', 'status': 'completed', 'exit_code': 2}}
        done = {'type': 'turn.completed', 'turn_id': 't1', 'usage':
                {'input_tokens': 20, 'cached_input_tokens': 7, 'output_tokens': 5}}
        result = BENCH.summarize_events([started, finished, finished, done, done])
        self.assertEqual(result['tool_calls'], 1)
        self.assertEqual(result['tool_errors'], 1)
        self.assertEqual(result['usage'], {'input_tokens': 20, 'cached_input_tokens': 7,
                                         'output_tokens': 5, 'total_tokens': 25})

    def test_equal_usage_on_distinct_turns_is_not_deduplicated(self):
        events = [{'type': 'turn.completed', 'turn_id': identity,
                   'usage': {'input_tokens': 10, 'output_tokens': 4}}
                  for identity in ('first', 'second')]
        result = BENCH.summarize_events(events)
        self.assertEqual(result['usage']['total_tokens'], 28)
        self.assertIsNone(result['usage']['cached_input_tokens'])

    def test_cached_usage_alias_preserved_without_recursive_double_count(self):
        event = {'type': 'response.completed', 'response': {'id': 'r1', 'usage':
                 {'input_tokens': 40, 'input_tokens_details': {'cached_tokens': 9},
                  'output_tokens': 2, 'total_tokens': 42}}}
        result = BENCH.summarize_events([event])
        self.assertEqual(result['usage']['total_tokens'], 42)
        self.assertEqual(result['usage']['cached_input_tokens'], 9)

    def test_follow_up_usage_uses_counter_difference_not_thread_total_twice(self):
        before = {'input_tokens': 100, 'cached_input_tokens': 60, 'output_tokens': 20}
        after = {'input_tokens': 150, 'cached_input_tokens': 90, 'output_tokens': 25}
        self.assertEqual(BENCH.usage_delta(before, after),
                         {'input_tokens': 50, 'cached_input_tokens': 30,
                          'output_tokens': 5, 'total_tokens': 55})
        self.assertIsNone(BENCH.usage_delta(after, before))

    def test_exact_failed_command_retry_is_separate_from_duplicate_event(self):
        failed = {'type': 'item.completed', 'item': {'id': 'a', 'type': 'command_execution',
                  'command': 'python validate.py', 'status': 'failed', 'exit_code': 2}}
        retried = {'type': 'item.completed', 'item': {'id': 'b', 'type': 'command_execution',
                   'command': 'python validate.py', 'status': 'completed', 'exit_code': 0}}
        result = BENCH.summarize_events([failed, failed, retried])
        self.assertEqual(result['agent_retries'], 1)

    def test_schedule_has_48_trials_in_balanced_version_pairs(self):
        config = BENCH.load_config(ROOT / 'tests/benchmark/campaign.json')
        rows = BENCH.make_schedule(config)
        self.assertEqual(len(rows), 48)
        self.assertEqual(rows, BENCH.make_schedule(config))
        for left, right in zip(rows[::2], rows[1::2]):
            self.assertEqual(left['scenario_id'], right['scenario_id'])
            self.assertEqual(left['repetition'], right['repetition'])
            self.assertEqual({left['arm'], right['arm']}, {'before', 'after'})

    def test_runtime_export_excludes_answers_and_detects_tampering(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / 'plugin'
            manifest = BENCH.export_runtime(ROOT, '7af1ba8', dest)
            self.assertFalse((dest / 'tests').exists())
            self.assertFalse((dest / 'docs').exists())
            self.assertEqual(len(list((dest / 'skills').glob('*/SKILL.md'))), 4)
            BENCH.verify_runtime(dest, manifest)
            (dest / 'skills/architecture-qa/SKILL.md').write_text('tampered')
            with self.assertRaisesRegex(ValueError, 'hash'):
                BENCH.verify_runtime(dest, manifest)

    def test_profile_copies_only_auth_and_sets_private_permissions(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / 'source'
            source.mkdir()
            (source / 'auth.json').write_text('{"test":"synthetic"}')
            (source / 'config.toml').write_text('unrelated = true')
            profile = Path(tmp) / 'isolated'
            BENCH.prepare_profile(profile, source)
            self.assertEqual((profile / 'auth.json').stat().st_mode & 0o777, 0o600)
            self.assertNotIn('unrelated', (profile / 'config.toml').read_text())
            self.assertFalse((source / 'skills').exists())

    def test_timeout_is_saved_as_failure_with_raw_logs(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            result = BENCH.run_process([sys.executable, '-c', 'import time; time.sleep(60)'],
                                       folder, dict(), folder, timeout=0.05)
            self.assertTrue(result['timed_out'])
            self.assertEqual(result['status'], 'TIMEOUT')
            self.assertTrue((folder / 'events.jsonl').exists())

    def test_anonymization_preserves_service_documentation(self):
        text = ('Plugin version 0.2.0, commit 7af1ba8. Source /tmp/trial/plugins/core/SKILL.md. '
                'https://docs.oracle.com/en/database/oracle/oracle-database/19/')
        result = BENCH.anonymize(text, ['/tmp/trial'], ['7af1ba8'])
        self.assertNotIn('0.2.0', result)
        self.assertNotIn('7af1ba8', result)
        self.assertNotIn('/tmp/trial', result)
        self.assertIn('https://docs.oracle.com/en/database/oracle/oracle-database/19/', result)

    def test_blind_cache_paths_and_display_names_do_not_identify_candidate(self):
        text = ('/private/cache/oci-architecture-designer/0.2.0/skills/core/SKILL.md; '
                'OCI Architecture Designer v0.1.3 uses Oracle Database 19c and toolkit v24.2')
        result = BENCH.anonymize(text, [], [])
        self.assertNotIn('0.2.0', result)
        self.assertNotIn('0.1.3', result)
        self.assertIn('19c', result)
        self.assertIn('v24.2', result)

    def test_critical_review_can_add_human_pairs_beyond_the_eight_samples(self):
        self.assertTrue(BENCH.review_gate({'agent_reviews': 24, 'human_reviews': 10,
                                         'critical_reviews_pending': 0, 'locked': True}))

    def test_review_lock_rejects_duplicate_pairs_and_unbound_answers(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            artifacts = {}
            for kind, count in [('agent', 24), ('human', 8)]:
                for i in range(count):
                    path = out / f'reviews/{kind}-{i}.json'
                    BENCH.write_json(path, {'reviewer_kind': kind, 'pair_id': 'pair-01'})
                    artifacts[str(path.relative_to(out))] = BENCH.sha256(path)
            lock = {'agent_reviews': 24, 'human_reviews': 8, 'critical_reviews_pending': 0,
                    'locked': True, 'artifact_sha256': artifacts}
            self.assertFalse(BENCH.verified_review_lock(out, lock))

    def test_timeout_remains_distinct_from_an_architecture_failure(self):
        self.assertEqual(BENCH.workflow_status([{'status': 'PASS'}, {'status': 'TIMEOUT'}]), 'TIMEOUT')

    def test_run_refuses_missing_pilot_gate_before_spawning(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, 'pilot'):
                BENCH.main(['run', '--config', str(ROOT / 'tests/benchmark/campaign.json'),
                            '--output', tmp])

    def test_file_review_never_promotes_parser_to_visual_pass(self):
        result = BENCH.file_review({'structural': {'status': 'PASS'}})
        self.assertEqual(result['file_integrity']['status'], 'PASS')
        for key in ['application_opening', 'visual_quality', 'editability']:
            self.assertEqual(result[key]['status'], 'NOT_VERIFIED')

    def test_blind_conclusion_requires_human_review_lock(self):
        self.assertFalse(BENCH.review_gate({'agent_reviews': 24, 'human_reviews': 0,
                                          'critical_reviews_pending': 0}))
        self.assertTrue(BENCH.review_gate({'agent_reviews': 24, 'human_reviews': 8,
                                         'critical_reviews_pending': 0, 'locked': True}))

    def test_mentioning_a_skill_or_failing_to_read_it_is_not_activation(self):
        events = [{'type': 'item.completed', 'item': {'id': 'a', 'type': 'command_execution',
                   'command': 'echo skills/architecture-qa/SKILL.md', 'exit_code': 0}},
                  {'type': 'item.completed', 'item': {'id': 'b', 'type': 'command_execution',
                   'command': 'cat skills/architecture-qa/SKILL.md', 'exit_code': 1}},
                  {'type': 'item.completed', 'item': {'id': 'c', 'type': 'command_execution',
                   'command': 'cat skills/oci-architecture-core/SKILL.md', 'exit_code': 0}}]
        self.assertEqual(BENCH.summarize_events(events)['skill_read_commands'],
                         ['skills/oci-architecture-core/SKILL.md'])

    def rpc_client(self, root, mode='normal'):
        code = '''import sys,json
mode=sys.argv[1]
for line in sys.stdin:
 r=json.loads(line)
 if r['method']=='initialized': continue
 if r['method']=='initialize':
  answer={'id':r['id'],'result':{}}
  if mode=='reject': answer={'id':r['id'],'error':{'message':'unsupported configuration'}}
 elif mode=='approval': answer={'id':900,'method':'item/commandExecution/requestApproval','params':{}}
 else:
  sys.stdout.write(json.dumps({'method':'notification','params':{}})+'\\n')
  answer={'id':r['id'],'result':{'observed':42}}
 print(json.dumps(answer),flush=True)
'''
        return BENCH.AppServer([sys.executable, '-u', '-c', code, mode], root,
                               dict(os.environ), root / 'logs')

    def test_rpc_handles_buffered_notifications_without_losing_the_response(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.rpc_client(Path(tmp)) as client:
                self.assertEqual(client.request('probe', {}), {'observed': 42})

    def test_rpc_does_not_fabricate_interactive_approval(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.rpc_client(Path(tmp), 'approval') as client:
                with self.assertRaisesRegex(ValueError, 'interactive approval'):
                    client.request('probe', {})

    def test_rejected_rpc_initialization_reaps_the_child(self):
        with tempfile.TemporaryDirectory() as tmp:
            client = self.rpc_client(Path(tmp), 'reject')
            self.addCleanup(client.__exit__)
            with self.assertRaisesRegex(ValueError, 'unsupported configuration'):
                client.__enter__()
            self.assertIsNotNone(client.process.poll())

    def test_changed_campaign_cannot_reuse_pilot_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            BENCH.write_json(out / 'pilot-gate.json', {'campaign_id': 'test', 'status': 'PASS',
                                                      'config_sha256': 'old'})
            with self.assertRaisesRegex(ValueError, 'changed'):
                BENCH.require_pilot_gate(out, {'campaign_id': 'test', 'timeout_seconds': 1200})

    def test_missing_toolkit_or_changed_bytes_block_native_task(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            (folder / 'icons.pptx').write_bytes(b'changed source')
            expected = {'files': [{'name': 'icons.pptx', 'sha256': 'approved'}]}
            with self.assertRaisesRegex(ValueError, 'hash'):
                BENCH.verify_toolkits(folder, expected, ['icons.pptx'])

    def test_skill_read_evidence_requires_successful_output_matching_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / 'skills/core/SKILL.md'
            path.parent.mkdir(parents=True)
            path.write_text('---\nname: core\n---\n# Synthetic skill instructions\n')
            events = [{'type': 'item.completed', 'item': {'id': 'one', 'type': 'command_execution',
                       'status': 'completed', 'exit_code': 0,
                       'command': '/bin/zsh -lc "cat skills/core/SKILL.md"',
                       'aggregated_output': path.read_text()}},
                      {'type': 'item.completed', 'item': {'id': 'two', 'type': 'command_execution',
                       'status': 'failed', 'exit_code': 1, 'aggregated_output': path.read_text()}}]
            result = BENCH.measured_skill_reads(root, events)
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0]['tool_item_id'], 'one')
            self.assertEqual(result[0]['skill'], 'core')

    def test_cli_report_preserves_failure_without_inventing_a_comparison(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            BENCH.write_json(out / 'preflight.json', {'status': 'FAIL', 'reason': 'no activation'})
            status = BENCH.main(['report', '--config', str(ROOT / 'tests/benchmark/campaign.json'),
                                 '--output', str(out)])
            self.assertEqual(status, 0)
            result = json.loads((out / 'report.json').read_text())
            self.assertEqual(result['conclusion_status'], 'NOT_VERIFIED')
            self.assertEqual(result['primary_completed'], 0)
            self.assertFalse(result['unblinded'])

    def test_failed_provisioning_removes_temporary_auth(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            source = out / 'source'
            source.mkdir()
            (source / 'auth.json').write_text('{"test":"synthetic"}')
            args = SimpleNamespace(codex='/usr/bin/false', output=out,
                                   toolkits=None, auth_source=source)
            config = BENCH.load_config(ROOT / 'tests/benchmark/campaign.json')
            BENCH._pilot(args, config, 'before', out / 'pilots')
            context = json.loads((out / 'pilots/before/context.json').read_text())
            self.assertFalse((Path(context['profile']) / 'auth.json').exists())

    def test_review_pack_cannot_hide_missing_primary_runs(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = BENCH.load_config(ROOT / 'tests/benchmark/campaign.json')
            with self.assertRaisesRegex(ValueError, '48'):
                BENCH.build_review_pack(Path(tmp), config)

    def test_review_pack_hides_key_and_selects_one_pair_per_scenario(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            config = BENCH.load_config(ROOT / 'tests/benchmark/campaign.json')
            for row in BENCH.make_schedule(config):
                folder = out / 'runs' / row['run_id']
                BENCH.write_json(folder / 'result.json', dict(row, status='PASS', workflow_state='COMPLETE'))
                (folder / 'answer.md').write_text('Source /tmp/worker; commit 7af1ba8. Synthetic answer.')
                BENCH.write_json(folder / 'application-evidence.json', {'application_opening': {'status': 'NOT_VERIFIED', 'method': 'No renderer'}})
            BENCH.build_review_pack(out, config)
            key = json.loads((out / 'private/version-key.json').read_text())
            sample = json.loads((out / 'reviews/human-sample.json').read_text())
            self.assertEqual(len(key['pairs']), 24)
            self.assertEqual(len(sample['pairs']), 8)
            self.assertEqual(len({r['scenario_id'] for r in sample['pairs']}), 8)
            self.assertFalse((out / 'reviews/packs/version-key.json').exists())
            index = json.loads((out / 'reviews/index.json').read_text())
            self.assertIn('rubric.md', index['pairs'][0]['input_sha256'])
            native = next(p for p in index['pairs'] if p['scenario_id'] == 'native-drawio')
            native_folder = out / 'reviews/packs' / native['pair_id']
            self.assertIn('compute-2', (native_folder / 'request.md').read_text())
            self.assertTrue((native_folder / 'A-application-checks.json').exists())
            for answer in (out / 'reviews/packs').glob('*/[AB].md'):
                self.assertNotIn('7af1ba8', answer.read_text())

    def test_unknown_usage_prevents_claiming_full_cost_per_accepted_task(self):
        rows = [{'accepted': True, 'telemetry': {'usage': {'total_tokens': 100}, 'usage_status': 'PASS'},
                 'elapsed_seconds': 10, 'generation_seconds': 8},
                {'accepted': False, 'telemetry': {'usage': None, 'usage_status': 'NOT_VERIFIED'},
                 'elapsed_seconds': 20, 'generation_seconds': 20}]
        value = BENCH.resource_summary(rows)
        self.assertEqual(value['observed_total_tokens'], 100)
        self.assertIsNone(value['tokens_per_accepted_task'])
        self.assertEqual(value['generation_seconds_per_accepted_task'], 28)
        self.assertEqual(value['generation_seconds']['median'], 14)
        self.assertEqual(value['usage_status'], 'NOT_VERIFIED')

    def test_successful_review_lock_is_bound_to_all_evidence_and_critical_human_checks(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            index = []
            (out / 'reviews').mkdir()
            (out / 'reviews/rubric.md').write_text('Frozen synthetic rubric')
            for i in range(24):
                folder = out / f'reviews/packs/pair-{i:02}'
                folder.mkdir(parents=True)
                (folder / 'A.md').write_text('A')
                (folder / 'B.md').write_text('B')
                index.append({'pair_id': folder.name, 'input_sha256': BENCH.review_inputs(folder)})
            BENCH.write_json(out / 'reviews/index.json', {'pairs': index})
            BENCH.write_json(out / 'reviews/human-sample.json', {'pairs': index[:8]})
            candidate = {'task_status': 'PASS', 'mandatory_checks': [{'status': 'PASS', 'evidence': 'A.md:1'}],
                         'qa': {k: {'status': 'NOT_VERIFIED', 'method': 'No native check'} for k in BENCH.QA + BENCH.DESIGN_QA}}
            artifacts = {}
            for kind, pairs in [('agent', index), ('human', index[:8])]:
                for pair in pairs:
                    path = out / f'reviews/{kind}/{pair["pair_id"]}.json'
                    BENCH.write_json(path, dict(pair, reviewer_kind=kind, candidates={'A': candidate, 'B': candidate},
                                               findings=[], preference='TIE'))
                    artifacts[str(path.relative_to(out))] = BENCH.sha256(path)
            lock = {'agent_reviews': 24, 'human_reviews': 8, 'critical_reviews_pending': 0,
                    'locked': True, 'artifact_sha256': artifacts}
            self.assertTrue(BENCH.verified_review_lock(out, lock))
            path = out / 'reviews/agent/pair-23.json'
            value = json.loads(path.read_text())
            value['findings'] = [{'candidate': 'A', 'severity': 'Critical', 'consequence': 'Lost data', 'evidence': 'A.md:1'}]
            BENCH.write_json(path, value)
            lock['artifact_sha256'][str(path.relative_to(out))] = BENCH.sha256(path)
            self.assertFalse(BENCH.verified_review_lock(out, lock))

    def test_review_counts_alone_cannot_unblind_results(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            config = BENCH.load_config(ROOT / 'tests/benchmark/campaign.json')
            BENCH.write_json(out / 'reviews/lock.json',
                             {'agent_reviews': 24, 'human_reviews': 8,
                              'critical_reviews_pending': 0, 'locked': True})
            self.assertFalse(BENCH.campaign_report(out, config)['unblinded'])


if __name__ == '__main__':
    unittest.main()
