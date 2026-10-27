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
from unittest.mock import patch
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


    def followup_fixture(self, root):
        config_file = root / 'primary-config.json'
        source = json.loads((ROOT / 'tests/benchmark/campaign.json').read_text())
        source['requests'] = str(ROOT / 'tests/fixtures/architecture-requests.json')
        BENCH.write_json(config_file, source)
        primary = BENCH.load_config(config_file)
        parent = root / 'primary'
        index = []
        (parent / 'reviews').mkdir(parents=True)
        (parent / 'reviews/rubric.md').write_text('Synthetic fixed rubric')
        candidate = {'task_status': 'PASS', 'mandatory_checks': [{'status': 'PASS', 'evidence': 'Fixture'}],
                     'qa': {k: {'status': 'NOT_VERIFIED', 'method': 'Synthetic lock fixture'}
                            for k in BENCH.QA + BENCH.DESIGN_QA}}
        for i in range(24):
            folder = parent / f'reviews/packs/pair-{i:02}'
            folder.mkdir(parents=True)
            (folder / 'A.md').write_text('Synthetic A')
            (folder / 'B.md').write_text('Synthetic B')
            row = {'pair_id': folder.name, 'scenario_id': primary['scenarios'][i % 8]['id'],
                   'input_sha256': BENCH.review_inputs(folder)}
            index.append(row)
            for kind in (('agent', 'human') if i < 8 else ('agent',)):
                BENCH.write_json(parent / f'reviews/{kind}/{folder.name}.json',
                    dict(row, reviewer_kind=kind, candidates={'A': candidate, 'B': candidate},
                         findings=[], preference='TIE'))
        BENCH.write_json(parent / 'reviews/index.json', {'pairs': index})
        BENCH.write_json(parent / 'reviews/human-sample.json', {'pairs': index[:8]})
        (parent / 'reviews/rubric.md').write_text('Synthetic fixed rubric')
        BENCH.write_json(parent / 'private/conclusion-inputs.json', BENCH.conclusion_inputs(parent))
        BENCH.lock_reviews(parent)
        BENCH.write_json(parent / 'pilot-gate.json', {'config_sha256': BENCH.config_digest(primary),
            'cli_runtime_identity': {'executable_sha256': 'frozen-cli', 'code_mode_host_sha256': 'frozen-helper'}})
        settings = {'schema_version': 2, 'campaign_id': 'confirmed-pptx-fix', 'seed': 2701026,
                    'primary_config': str(config_file), 'parent_output': str(parent),
                    'parent_lock_sha256': BENCH.sha256(parent / 'reviews/lock.json'),
                    'candidate_revision': 'f' * 40, 'scenario_ids': ['native-pptx']}
        path = root / 'followup.json'
        BENCH.write_json(path, settings)
        return path, settings, primary

    def test_followup_repeats_only_affected_unchanged_requests_against_parent_candidate(self):
        with tempfile.TemporaryDirectory() as tmp:
            path, settings, primary = self.followup_fixture(Path(tmp))
            config = BENCH.load_config(path)
            schedule = BENCH.make_schedule(config)
            self.assertEqual(len(schedule), 6)
            self.assertEqual({r['repetition'] for r in schedule}, {1, 2, 3})
            self.assertEqual({r['scenario_id'] for r in schedule}, {'native-pptx'})
            self.assertEqual(config['revisions'], {'before': primary['revisions']['after'], 'after': 'f' * 40})
            self.assertEqual(config['scenarios'], [primary['scenarios'][-1]])
            self.assertEqual((config['model'], config['reasoning_effort'], config['timeout_seconds']),
                             ('gpt-6.1-sol', 'xhigh', 1200))
            self.assertEqual(len(BENCH.make_schedule(primary)), 48)

    def test_followup_requires_unchanged_locked_parent_and_known_affected_tasks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path, settings, _ = self.followup_fixture(root)
            lock_path = root / 'primary/reviews/lock.json'
            original = lock_path.read_bytes()
            BENCH.write_json(lock_path, {'locked': False})
            with self.assertRaisesRegex(ValueError, 'locked parent'):
                BENCH.load_config(path)
            lock_path.write_bytes(original)
            for invalid in [dict(settings, parent_lock_sha256='0' * 64),
                            dict(settings, scenario_ids=['invented-task']),
                            dict(settings, scenario_ids=[]),
                            dict(settings, candidate_revision='HEAD')]:
                BENCH.write_json(path, invalid)
                with self.assertRaises(ValueError):
                    BENCH.load_config(path)
            BENCH.write_json(path, settings)
            BENCH.write_json(root / 'primary/pilot-gate.json', {'config_sha256': 'changed-prompt'})
            with self.assertRaisesRegex(ValueError, 'primary configuration'):
                BENCH.load_config(path)

    def test_followup_refuses_other_cli_runtime_before_inference(self):
        with tempfile.TemporaryDirectory() as tmp:
            path, _, _ = self.followup_fixture(Path(tmp))
            config = BENCH.load_config(path)
            args = SimpleNamespace(output=Path(tmp) / 'followup-results', command='preflight',
                                   reprocess_pilots=False, toolkits=Path(tmp), codex='fake-external-cli')
            with patch.object(BENCH, 'cli_runtime_identity', return_value={'changed': True}), \
                 patch.object(BENCH, '_pilot', side_effect=AssertionError('Do not infer with another runtime')):
                with self.assertRaisesRegex(ValueError, 'parent CLI runtime'):
                    BENCH.execute_command(args, config)

    def test_followup_cannot_write_into_parent_or_reinterpret_its_blind_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path, settings, _ = self.followup_fixture(root)
            for out in [root, Path(settings['parent_output']), Path(settings['parent_output']) / 'child']:
                with self.assertRaisesRegex(ValueError, 'separate from the primary evidence'):
                    BENCH.main(['report', '--config', str(path), '--output', str(out)])
            with self.assertRaisesRegex(ValueError, 'primary 24-pair review gate is unchanged'):
                BENCH.main(['review-pack', '--config', str(path), '--output', str(root / 'followup')])

    def test_followup_report_keeps_execution_and_unchecked_architecture_separate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path, _, _ = self.followup_fixture(root)
            config = BENCH.load_config(path)
            out = root / 'followup-results'
            BENCH.write_json(out / 'runs/example/result.json', {'run_id': 'example', 'arm': 'before',
                'scenario_id': 'native-pptx', 'repetition': 1, 'workflow_state': 'COMPLETE',
                'status': 'TIMEOUT', 'steps': [], 'telemetry': {'usage': None, 'usage_status': 'NOT_VERIFIED'}})
            report = BENCH.campaign_report(out, config)
            self.assertEqual(report['planned_workflows'], 6)
            self.assertEqual(report['workflows_completed'], 1)
            self.assertEqual(report['architecture_comparison_status'], 'NOT_VERIFIED')
            self.assertFalse(report['unblinded'])
            self.assertEqual(report['versions']['before']['execution_status_counts'], {'TIMEOUT': 1})
            self.assertEqual(report['versions']['before']['resources']['usage_status'], 'NOT_VERIFIED')
            self.assertIsNone(report['versions']['before']['resources']['tokens_per_accepted_task'])
            self.assertIn('Follow-up execution', (out / 'report.md').read_text())

    def test_blind_native_evidence_hides_local_files_and_cross_run_paths(self):
        local_root = '/' + 'Users/'
        raw = (f'Saved {local_root}example/Downloads/benchmark-v3-602e6fc7f0db5f23-move.drawio; '
               'compare runs/602e6fc7f0db5f23/application/reopened.png. '
               'Official source https://docs.oracle.com/iaas/toolkit and Icons/source-cell stay visible.')
        clean = BENCH.anonymize(raw, [], [])
        self.assertNotIn(local_root, clean)
        self.assertNotIn('602e6fc7f0db5f23', clean)
        self.assertIn('https://docs.oracle.com/iaas/toolkit', clean)
        self.assertIn('Icons/source-cell', clean)

    def test_blind_source_capture_uses_actual_web_output_without_private_tool_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            session = root / 'profile/sessions/trace.jsonl'
            session.parent.mkdir(parents=True)
            body = ('Networking (https://docs.oracle.com/network)\n'
                    '[wordlim: 200] Content type: text/html; Source: open(...); Total lines: 2\n'
                    'L0: Regional subnets\nL1: Workload placement is a separate decision.')
            payload = {'type': 'custom_tool_call_output', 'call_id': 'web-call',
                       'output': [{'type': 'input_text', 'text': json.dumps({'i': 0, 'value': body})},
                                  {'type': 'input_text', 'text': json.dumps({'value': {
                                      'output': 'synthetic private tool output must not reach reviewer'}})}]}
            payload['output'].append({'type': 'input_text',
                'text': 'Warning: truncated output\n\n' +
                        json.dumps({'private': 'synthetic private tool output must not reach reviewer'}) +
                        '\n' + body + '\nL2: partial …34 tokens truncated… synthetic private tool output must not reach reviewer\n' +
                        json.dumps({'private': 'synthetic private tool output must not reach reviewer'})})
            session.write_text(json.dumps({'payload': {'type': 'custom_tool_call', 'call_id': 'web-call', 'name': 'exec', 'input': 'tools.web__run(...)'}}) + '\n' + json.dumps({'timestamp': '2026-10-26T10:00:00Z', 'payload': payload}) + '\n')
            BENCH.archive_profile_sessions(root / 'profile', root / 'run')
            session.write_text(session.read_text() + '{"type":"follow-up"}\n')
            BENCH.archive_profile_sessions(root / 'profile', root / 'run')
            result = BENCH.archived_web_sources(root / 'run')
            self.assertEqual(result['status'], 'PASS')
            self.assertEqual(len(result['captures']), 1)
            self.assertEqual(result['captures'][0]['content'], body)
            self.assertEqual(result['captures'][0]['observed_at'], '2026-10-26T10:00:00Z')
            self.assertEqual(result['captures'][0]['content_sha256'],
                             BENCH.hashlib.sha256(body.encode()).hexdigest())
            self.assertNotIn('synthetic private tool output', json.dumps(result))
            self.assertEqual(BENCH.archived_web_sources(root / 'missing')['status'], 'NOT_VERIFIED')
            manifest = json.loads((root / 'run/private-session-manifest.json').read_text())
            (root / 'run' / manifest['snapshots'][0]['file']).write_text('changed')
            with self.assertRaisesRegex(ValueError, 'checksum'):
                BENCH.archived_web_sources(root / 'run')

    def test_private_session_archive_excludes_auth_config_and_symlinks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile, output = root / 'profile', root / 'evidence'
            session = profile / 'sessions/2026/trace.jsonl'
            session.parent.mkdir(parents=True)
            raw = b'{"type":"event_msg","payload":{"type":"token_count"}}\n'
            session.write_bytes(raw)
            (profile / 'auth.json').write_text('synthetic authentication must stay outside archives')
            (profile / 'config.toml').write_text('synthetic configuration')
            (session.parent / 'linked.jsonl').symlink_to(profile / 'auth.json')
            manifest = BENCH.archive_profile_sessions(profile, output)
            self.assertEqual(manifest['status'], 'PASS')
            self.assertEqual(len(manifest['snapshots']), 1)
            archived = output / manifest['snapshots'][0]['file']
            self.assertEqual(archived.read_bytes(), raw)
            self.assertEqual(archived.stat().st_mode & 0o777, 0o600)
            self.assertEqual((output / 'private-session-manifest.json').stat().st_mode & 0o777, 0o600)
            self.assertEqual(BENCH.sha256(archived), manifest['snapshots'][0]['sha256'])
            self.assertEqual(manifest['snapshots'][0]['source'], 'sessions/2026/trace.jsonl')
            self.assertNotIn('synthetic authentication', json.dumps(manifest))
            self.assertEqual(list(output.rglob('auth.json')), [])
            self.assertEqual(list(output.rglob('config.toml')), [])

    def test_session_snapshots_retain_prior_bytes_when_follow_up_appends(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / 'profile/sessions/trace.jsonl'
            source.parent.mkdir(parents=True)
            first = b'{"type":"first"}\n'
            source.write_bytes(first)
            a = BENCH.archive_profile_sessions(root / 'profile', root / 'evidence')
            source.write_bytes(first + b'{"type":"follow_up"}\n')
            b = BENCH.archive_profile_sessions(root / 'profile', root / 'evidence')
            self.assertEqual(len(b['snapshots']), 2)
            self.assertEqual((root / 'evidence' / a['snapshots'][0]['file']).read_bytes(), first)
            c = BENCH.archive_profile_sessions(root / 'profile', root / 'evidence')
            self.assertEqual(len(c['snapshots']), 2)

    def test_changed_archived_session_is_detected_before_appending(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / 'profile/sessions/trace.jsonl'
            source.parent.mkdir(parents=True)
            source.write_text('{"type":"first"}\n')
            original = BENCH.archive_profile_sessions(root / 'profile', root / 'evidence')
            archived = root / 'evidence' / original['snapshots'][0]['file']
            archived.write_text('changed archived bytes')
            source.write_text('{"type":"first"}\n{"type":"follow_up"}\n')
            with self.assertRaisesRegex(ValueError, 'checksum'):
                BENCH.archive_profile_sessions(root / 'profile', root / 'evidence')
            self.assertEqual(archived.read_text(), 'changed archived bytes')

    def test_absent_or_malformed_session_logs_are_not_verified(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            missing = BENCH.archive_profile_sessions(root / 'profile', root / 'missing')
            self.assertEqual(missing['status'], 'NOT_VERIFIED')
            self.assertEqual(missing['snapshots'], [])
            source = root / 'profile/sessions/trace.jsonl'
            source.parent.mkdir(parents=True)
            source.write_bytes(b'{"type":"valid"}\ntruncated')
            malformed = BENCH.archive_profile_sessions(root / 'profile', root / 'malformed')
            self.assertEqual(malformed['status'], 'NOT_VERIFIED')
            self.assertEqual(malformed['snapshots'][0]['malformed_lines'], 1)
            self.assertEqual((root / 'malformed' / malformed['snapshots'][0]['file']).read_bytes(), source.read_bytes())

    def test_finishing_trial_archives_raw_session_evidence_without_inference(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            workspace = root / 'workspace'
            workspace.mkdir()
            folder = root / 'run'
            folder.mkdir()
            profile = root / 'profile'
            source = profile / 'sessions/trace.jsonl'
            source.parent.mkdir(parents=True)
            source.write_text('{"type":"synthetic"}\n')
            BENCH.write_json(folder / 'context.json', {'workspace': str(workspace), 'profile': str(profile)})
            with patch.object(BENCH, 'inference', side_effect=AssertionError('No inference during archival')):
                BENCH.finish_trial(folder, {'run_id': 'synthetic'}, [], 'PASS', 0)
            manifest = json.loads((folder / 'private-session-manifest.json').read_text())
            self.assertEqual(manifest['status'], 'PASS')
            self.assertEqual(len(manifest['snapshots']), 1)

    def test_missing_usage_is_unknown_not_zero(self):
        result = BENCH.summarize_events([{'type': 'turn.failed', 'error': {'message': 'offline'}}])
        self.assertIsNone(result['usage'])
        self.assertEqual(result['usage_status'], 'NOT_VERIFIED')
        self.assertEqual(result['status'], 'FAIL')

    def test_actual_model_and_effort_must_match_and_absent_context_is_unknown(self):
        config = {'model': 'gpt-6.1-sol', 'reasoning_effort': 'xhigh'}
        self.assertEqual(BENCH.model_status([], config), 'NOT_VERIFIED')
        self.assertEqual(BENCH.model_status([{'model': 'gpt-6.1-sol', 'effort': 'xhigh'}], config), 'PASS')
        self.assertEqual(BENCH.model_status([{'model': 'other', 'effort': 'xhigh'}], config), 'FAIL')

    def test_cli_inventory_uses_the_isolated_profile_environment(self):
        with tempfile.TemporaryDirectory() as tmp:
            command = Path(tmp) / 'codex-probe'
            command.write_text('#!/bin/sh\nprintf %s "$CODEX_HOME"\n')
            command.chmod(0o700)
            env = dict(os.environ, CODEX_HOME=str(Path(tmp) / 'isolated'))
            result = BENCH.environment_inventory(str(command), env)
            self.assertEqual(result['codex']['version'], env['CODEX_HOME'])
            self.assertEqual(result['codex']['sha256'], BENCH.sha256(command))

    def test_controller_hash_describes_loaded_code_when_file_changes_later(self):
        with tempfile.TemporaryDirectory() as tmp:
            replacement = Path(tmp) / 'later-controller.py'
            replacement.write_text('new file content after import')
            command = Path(tmp) / 'codex-probe'
            command.write_text('#!/bin/sh\nprintf synthetic-version\n')
            command.chmod(0o700)
            original = BENCH.environment_inventory(str(command), dict(os.environ))['controller_sha256']
            with patch.object(BENCH, '__file__', str(replacement)):
                observed = BENCH.environment_inventory(str(command), dict(os.environ))['controller_sha256']
            self.assertEqual(observed, original)

    def test_cli_identity_requires_the_external_code_mode_helper(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            executable = root / 'CodexCLI.app/Contents/MacOS/codex'
            executable.parent.mkdir(parents=True)
            executable.write_bytes(b'synthetic vendor executable')
            with self.assertRaisesRegex(ValueError, 'code-mode'):
                BENCH.cli_runtime_identity(str(executable))
            helper = root / 'bin/codex-code-mode-host'
            helper.parent.mkdir()
            helper.write_bytes(b'synthetic vendor helper')
            identity = BENCH.cli_runtime_identity(str(executable))
            self.assertEqual(identity['code_mode_host_sha256'], BENCH.sha256(helper))

    def test_missing_code_mode_host_is_an_infrastructure_failure_even_after_a_final_answer(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            workspace, logs = root / 'workspace', root / 'logs'
            workspace.mkdir()
            def process(*args):
                logs.mkdir()
                (logs / 'events.jsonl').write_text('{"type":"turn.completed","usage":{"input_tokens":2,"output_tokens":1}}\n')
                (logs / 'stderr.log').write_text('ERROR failed to spawn code-mode host: No such file or directory')
                return {'status': 'PASS', 'elapsed_seconds': 1, 'exit_code': 0}
            config = {'model': 'gpt-6.1-sol', 'reasoning_effort': 'xhigh'}
            context = {'workspace': workspace, 'profile': root / 'profile', 'env': {}}
            with patch.object(BENCH, 'run_process', side_effect=process), \
                 patch.object(BENCH, 'profile_total', side_effect=[None, {'input_tokens': 2, 'output_tokens': 1, 'cached_input_tokens': 0, 'total_tokens': 3}]), \
                 patch.object(BENCH, 'actual_context', return_value=[{'model': 'gpt-6.1-sol', 'effort': 'xhigh'}]):
                result = BENCH.inference(SimpleNamespace(codex='synthetic'), config, context, 'request', logs, 20)
            self.assertEqual(result['status'], 'FAIL')
            self.assertIn('runtime', result['protocol_error'])
            self.assertEqual(result['telemetry']['usage']['total_tokens'], 3)

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

    def test_native_profile_denies_other_home_and_shared_temporary_candidates(self):
        import tomllib
        with tempfile.TemporaryDirectory() as tmp:
            trial = Path(tmp)
            profile = trial / 'profile'
            profile.mkdir()
            (profile / 'config.toml').write_text('')
            BENCH.native_permissions({'trial': trial, 'workspace': trial / 'workspace',
                                      'profile': profile,
                                      'codex': trial / 'tools/CodexCLI.app/Contents/MacOS/codex'},
                                     trial / 'controller')
            policy = tomllib.loads((profile / 'config.toml').read_text())
            rules = policy['permissions']['architecture-benchmark']['filesystem']
            self.assertEqual(rules['/private/tmp'], 'deny')
            self.assertEqual(rules['/tmp'], 'deny')
            self.assertEqual(rules[str(Path.home())], 'deny')
            self.assertEqual(rules[str(Path.home() / '.cache/codex-runtimes')], 'read')
            self.assertEqual(rules[str(trial / 'workspace')], 'write')
            self.assertEqual(rules[str(trial / 'workspace/inputs')], 'read')
            self.assertEqual(rules[str((trial / 'tools/CodexCLI.app').resolve())], 'read')

    def test_controller_interruption_reaps_the_running_inference(self):
        from unittest.mock import Mock
        process = Mock(pid=12345)
        process.wait.side_effect = [KeyboardInterrupt, -15]
        with tempfile.TemporaryDirectory() as tmp, \
             patch.object(BENCH.subprocess, 'Popen', return_value=process), \
             patch.object(BENCH.os, 'killpg') as kill:
            with self.assertRaises(KeyboardInterrupt):
                BENCH.run_process(['synthetic'], tmp, {}, tmp, timeout=20)
        kill.assert_called_once_with(12345, BENCH.signal.SIGTERM)
        self.assertEqual(process.wait.call_count, 2)

    def test_timeout_is_saved_as_failure_with_raw_logs(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            result = BENCH.run_process([sys.executable, '-c', 'import time; time.sleep(60)'],
                                       folder, dict(), folder, timeout=0.05)
            self.assertTrue(result['timed_out'])
            self.assertEqual(result['status'], 'TIMEOUT')
            self.assertTrue((folder / 'events.jsonl').exists())

    def test_wall_clock_jump_stops_process_before_monotonic_budget_is_used(self):
        clock = [100.0]
        waits = []
        def wait(timeout=None):
            waits.append(timeout)
            if len(waits) == 1:
                clock[0] = 130.0
                raise subprocess.TimeoutExpired('synthetic', timeout)
            return -15
        process = SimpleNamespace(pid=12345, wait=wait)
        with tempfile.TemporaryDirectory() as tmp, \
             patch.object(BENCH.subprocess, 'Popen', return_value=process), \
             patch.object(BENCH.time, 'time', side_effect=lambda: clock[0]), \
             patch.object(BENCH.time, 'monotonic', return_value=0), \
             patch.object(BENCH.os, 'killpg') as kill:
            result = BENCH.run_process(['synthetic'], tmp, {}, tmp, timeout=20)
        self.assertEqual(result['status'], 'TIMEOUT')
        self.assertEqual(result['wall_elapsed_seconds'], 30)
        self.assertLessEqual(waits[0], 1)
        kill.assert_called_once_with(12345, BENCH.signal.SIGTERM)

    def test_process_exit_after_wall_deadline_is_not_a_pass(self):
        clock = [100.0]
        def wait(timeout=None):
            clock[0] = 121.0
            return 0
        with tempfile.TemporaryDirectory() as tmp, \
             patch.object(BENCH.subprocess, 'Popen', return_value=SimpleNamespace(wait=wait)), \
             patch.object(BENCH.time, 'time', side_effect=lambda: clock[0]), \
             patch.object(BENCH.time, 'monotonic', return_value=0):
            result = BENCH.run_process(['synthetic'], tmp, {}, tmp, timeout=20)
        self.assertEqual(result['status'], 'TIMEOUT')
        self.assertEqual(result['exit_code'], 0)

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

    def test_manifest_identity_is_redacted_without_erasing_service_versions(self):
        text = ('Plugin manifest plugin.json reports version 0.2.0. '
                '{"plugin_version":"0.1.3"}; Oracle Database version 19c; toolkit v24.2')
        clean = BENCH.anonymize(text, [], [])
        self.assertNotIn('0.2.0', clean)
        self.assertNotIn('0.1.3', clean)
        self.assertIn('19c', clean)
        self.assertIn('v24.2', clean)

    def test_initial_snapshot_survives_follow_up_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            workspace, evidence = root / 'workspace', root / 'evidence'
            initial = workspace / 'outputs/initial.drawio'
            initial.parent.mkdir(parents=True)
            initial.write_text('<mxGraphModel><root><mxCell id="0"/><mxCell id="1" parent="0"/></root></mxGraphModel>')
            original = initial.read_bytes()
            BENCH.structural_evidence(workspace, evidence, 'drawio', phases=('initial',))
            initial.write_text('overwritten during edit')
            BENCH.structural_evidence(workspace, evidence, 'drawio')
            self.assertEqual((evidence / 'artifacts/initial.drawio').read_bytes(), original)
            value = json.loads((evidence / 'file-evidence.json').read_text())
            self.assertEqual(value['source_changes']['initial']['status'], 'FAIL')

    def test_expired_budget_never_starts_inference(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(BENCH, 'run_process') as process:
            result = BENCH.inference(SimpleNamespace(codex='unused'), {}, {}, 'request', Path(tmp), -1)
            self.assertEqual(result['status'], 'TIMEOUT')
            process.assert_not_called()

    def test_setup_uses_wall_budget_and_late_completion_is_timeout(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            clock = [0]
            row = {'run_id': 'deadline', 'scenario_id': 'reasoning'}
            config = {'timeout_seconds': 10, 'scenarios': [{'id': 'reasoning', 'kind': 'reasoning', 'request': 'q'}]}
            def provision(*args):
                clock[0] = 3
                return {}
            def infer(*args, **kwargs):
                self.assertEqual(args[5], 7)
                clock[0] = 11
                return {'status': 'PASS', 'elapsed_seconds': 8, 'telemetry': {
                    'usage': None, 'usage_status': 'NOT_VERIFIED', 'tool_calls': 0, 'tool_errors': 0,
                    'runtime_errors': 0, 'skill_read_commands': [], 'agent_retries': 0}}
            with patch.object(BENCH, 'make_schedule', return_value=[row]), \
                 patch.object(BENCH, 'provision_trial', side_effect=provision), \
                 patch.object(BENCH, 'confinement_checks'), \
                 patch.object(BENCH, 'campaign_report'), \
                 patch.object(BENCH, 'inference', side_effect=infer), \
                 patch.object(BENCH.time, 'time', side_effect=lambda: clock[0]):
                BENCH.run_campaign(SimpleNamespace(output=out), config)
            result = json.loads((out / 'runs/deadline/result.json').read_text())
            self.assertEqual(result['status'], 'TIMEOUT')
            self.assertEqual(result['elapsed_seconds'], 11)

    def test_observed_failed_usage_survives_unknown_workflow_completeness(self):
        phase = {'elapsed_seconds': 1, 'telemetry': {'usage': {
            'input_tokens': 95, 'cached_input_tokens': 30, 'output_tokens': 5, 'total_tokens': 100},
            'usage_status': 'NOT_VERIFIED', 'tool_calls': 1, 'tool_errors': 1,
            'runtime_errors': 0, 'skill_read_commands': [], 'agent_retries': 0}}
        telemetry = BENCH.combine_telemetry([phase])
        summary = BENCH.resource_summary([{'telemetry': telemetry, 'accepted': False}])
        self.assertIsNone(telemetry['usage'])
        self.assertEqual(summary['observed_total_tokens'], 100)
        self.assertIsNone(summary['tokens_per_accepted_task'])

    def test_native_qa_mutation_invalidates_checked_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            native = root / 'outputs/edited.drawio'
            native.parent.mkdir()
            native.write_text('checked bytes')
            before = BENCH.native_hashes(root)
            native.write_text('modified by final QA')
            with self.assertRaisesRegex(ValueError, 'artifact'):
                BENCH.verify_native_hashes(root, before)

    def test_interrupted_run_preserves_completed_answer_without_repeating_inference(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            row = {'run_id': 'interrupted', 'scenario_id': 'reasoning'}
            folder = out / 'runs/interrupted'
            (folder / 'initial').mkdir(parents=True)
            (folder / 'initial/answer.md').write_text('Completed answer before controller interruption')
            BENCH.write_json(folder / 'initial/outcome.json', {'status': 'PASS', 'elapsed_seconds': 3,
                'telemetry': {'usage': None, 'usage_status': 'NOT_VERIFIED', 'tool_calls': 0,
                              'tool_errors': 0, 'runtime_errors': 0, 'skill_read_commands': [], 'agent_retries': 0}})
            result = BENCH.recover_interrupted_trial(folder, row)
            self.assertEqual(result['status'], 'INTERRUPTED')
            self.assertIsNone(result['elapsed_seconds'])
            self.assertIn('Completed answer', (folder / 'answer.md').read_text())

    def test_interrupted_setup_is_not_counted_as_a_completed_workflow(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            result = BENCH.recover_interrupted_trial(folder, {'run_id': 'setup-only'})
            self.assertNotEqual(result['workflow_state'], 'COMPLETE')

    def test_unresolved_candidate_identity_stops_blind_pack(self):
        with self.assertRaisesRegex(ValueError, 'identity'):
            BENCH.verify_blind_text('Manifest version: 0.2.0', [])
        BENCH.verify_blind_text('Oracle Database 19c; toolkit v24.2', [])

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

    def test_passing_legacy_pilots_cannot_approve_the_hardened_isolation_protocol(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = {'campaign_id': 'test'}
            BENCH.write_json(Path(tmp) / 'pilot-gate.json', {
                'campaign_id': 'test', 'status': 'PASS', 'config_sha256': BENCH.config_digest(config)})
            with self.assertRaisesRegex(ValueError, 'isolation'):
                BENCH.require_pilot_gate(Path(tmp), config)

    def test_frozen_rubric_cannot_be_changed_after_definition_is_locked(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            rubric = BENCH.freeze_rubric(out)
            self.assertIn('Critical', rubric)
            (out / 'frozen/rubric.md').write_text('changed grading criteria')
            with self.assertRaisesRegex(ValueError, 'rubric'):
                BENCH.freeze_rubric(out)

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
            BENCH.write_json(out / 'infrastructure-attempts/setup-only/result.json',
                             {'status': 'FAIL', 'infrastructure_error': 'Nested execution denied', 'steps': [],
                              'observed_usage': {'total_tokens': 105}, 'usage_status': 'NOT_VERIFIED'})
            status = BENCH.main(['report', '--config', str(ROOT / 'tests/benchmark/campaign.json'),
                                 '--output', str(out)])
            self.assertEqual(status, 0)
            result = json.loads((out / 'report.json').read_text())
            self.assertEqual(result['conclusion_status'], 'NOT_VERIFIED')
            self.assertEqual(result['primary_completed'], 0)
            self.assertFalse(result['unblinded'])
            self.assertEqual(result['technical_attempts'][0]['status'], 'FAIL')
            self.assertEqual(result['technical_attempts'][0]['reason'], 'Nested execution denied')
            self.assertEqual(result['technical_attempts'][0]['observed_usage']['total_tokens'], 105)
            self.assertEqual(result['technical_attempts'][0]['usage_status'], 'NOT_VERIFIED')
            self.assertIn('Technical attempts outside primary runs: 1', (out / 'report.md').read_text())
            self.assertIsNone(result['resource_scope']['controller_tokens']['value'])
            self.assertEqual(result['resource_scope']['total_end_to_end_cost_status'], 'NOT_VERIFIED')

    def test_activation_review_observes_reads_without_exposing_instructions(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            catalog = folder / 'setup/catalog/events.jsonl'
            catalog.parent.mkdir(parents=True)
            catalog.write_text('skills/core/SKILL.md\nPRIVATE CANDIDATE INSTRUCTION TEXT')
            result = {'steps': [{'skill_read_evidence': [{'skill': 'core', 'source_sha256': 'private-identity'}]}]}
            value = BENCH.review_activation(folder, result)
            self.assertEqual(value['discovered_skills'], ['core'])
            self.assertEqual(value['read_skills'], ['core'])
            self.assertNotIn('PRIVATE CANDIDATE', json.dumps(value))
            self.assertNotIn('private-identity', json.dumps(value))
            self.assertEqual(BENCH.review_activation(folder, {'steps': []})['read_status'], 'NOT_VERIFIED')

    def test_worker_reports_include_findings_but_exclude_copied_candidate_instructions(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            reports = folder / 'workspace-evidence/outputs/evidence'
            reports.mkdir(parents=True)
            copied = reports / 'candidate-notes.md'
            copied.write_text('Complete candidate instructions copied into evidence')
            (reports / 'architecture-review.md').write_text('Worker findings about the requested architecture')
            BENCH.write_json(folder / 'runtime-manifest.json', {'files': {
                'skills/core/references/architecture-review.md': BENCH.sha256(copied)}})
            selected = [relative.name for _, relative, _ in BENCH.review_documents(folder)]
            self.assertEqual(selected, ['architecture-review.md'])

    def test_blind_documents_keep_primary_design_svg_and_qa_attachments(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            outputs = folder / 'workspace-evidence/outputs'
            (outputs / 'qa').mkdir(parents=True)
            (outputs / 'order-design.md').write_text('An asynchronous acknowledgement is not business completion.')
            (outputs / 'model.json').write_text('{"business_completion":"committed"}')
            (outputs / 'integration.svg').write_text('<svg><text>Durable queue, idempotent consumer</text></svg>')
            (outputs / 'delivery-evidence.json').write_text('{"visual_quality":"NOT_VERIFIED"}')
            (outputs / 'qa/validator.json').write_text('{"opening_review":"NOT_VERIFIED"}')
            (outputs / 'build.py').write_text('synthetic generator implementation')
            (outputs / 'unverified-preview.png').write_bytes(b'synthetic unverified raster')
            selected = {str(relative): kind for _, relative, kind in BENCH.review_documents(folder)}
            self.assertEqual(selected['outputs/order-design.md'], 'worker_artifact')
            self.assertEqual(selected['outputs/model.json'], 'worker_artifact')
            self.assertEqual(selected['outputs/integration.svg'], 'worker_artifact')
            self.assertEqual(selected['outputs/delivery-evidence.json'], 'worker_report')
            self.assertEqual(selected['outputs/qa/validator.json'], 'worker_report')
            self.assertNotIn('outputs/build.py', selected)
            self.assertNotIn('outputs/unverified-preview.png', selected)

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

    def test_a_transferred_but_malformed_pilot_file_cannot_pass_preflight(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            workspace = out / 'workspace'
            (workspace / 'outputs').mkdir(parents=True)
            (workspace / 'outputs/pilot.drawio').write_text('not an editable XML diagram')
            args = SimpleNamespace(output=out, codex='synthetic-cli')
            config = {'revisions': {'before': 'pinned'}, 'model': 'gpt-6.1-sol',
                      'reasoning_effort': 'xhigh', 'timeout_seconds': 10}
            context = {'workspace': workspace, 'env': dict(os.environ), 'discovered_skills': ['core']}
            outcome = {'status': 'PASS', 'actual_context': [{'model': 'gpt-6.1-sol', 'effort': 'xhigh'}],
                       'telemetry': {'usage': {'total_tokens': 1}}, 'skill_read_evidence': [{'skill': 'core'}]}
            with patch.object(BENCH, 'provision_trial', return_value=context), \
                 patch.object(BENCH, 'confinement_checks'), \
                 patch.object(BENCH, 'inference', return_value=outcome), \
                 patch.object(BENCH.subprocess, 'check_output', return_value='synthetic-cli'):
                result = BENCH._pilot(args, config, 'before', out / 'pilots')
            self.assertTrue(result['file_transfer'])
            self.assertEqual(result['status'], 'FAIL')
            self.assertEqual(result['file_structure'], 'FAIL')

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
                BENCH.write_json(folder / 'operator-evidence/source-audit.json',
                                 {'source_identity': 'PASS', 'artwork': 'NOT_VERIFIED',
                                  'checked_at_epoch': 123, 'elapsed_seconds': 1200,
                                  'timing': 'Post-deadline forensic', 'source_access_date': '2026-10-26'})
                source = folder / 'workspace-evidence/evidence/sources/compute.html'
                source.parent.mkdir(parents=True)
                source.write_text('<title>Oracle Compute</title>')
                BENCH.write_json(folder / 'workspace-evidence/outputs/evidence/icon-provenance.json',
                                 {'assets': [{'label': 'Virtual Machine', 'source_position': 'Icons/199'}]})
                BENCH.write_json(folder / 'workspace-evidence/outputs/evidence/sources.json',
                                 {'source_access_date': '2026-10-26', 'input_tokens': 8192})
                BENCH.write_json(folder / 'workspace-evidence/outputs/evidence/validator.json',
                                 {'status': 'PASS', 'elapsed_seconds': 2})
                (folder / 'workspace-evidence/outputs/verification.md').write_text('Executed checks and limitations')
                (folder / 'operator-evidence/reopened.png').write_bytes(b'synthetic native render bytes')
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
            self.assertEqual(json.loads((native_folder / 'A-operator-source-audit.json').read_text())['artwork'],
                             'NOT_VERIFIED')
            operator = json.loads((native_folder / 'A-operator-source-audit.json').read_text())
            self.assertNotIn('checked_at_epoch', operator)
            self.assertNotIn('elapsed_seconds', operator)
            self.assertNotIn('timing', operator)
            self.assertEqual(operator['source_access_date'], '2026-10-26')
            sources = json.loads((native_folder / 'A-sources.json').read_text())
            self.assertEqual(len(sources), 5)
            self.assertTrue(any((native_folder / item['review_file']).read_text() == '<title>Oracle Compute</title>'
                                for item in sources))
            self.assertTrue(any('icon-provenance.json' in item['source_position'] for item in sources))
            source_metadata = next(item for item in sources if item['source_position'].endswith('/sources.json'))
            self.assertEqual(json.loads((native_folder / source_metadata['review_file']).read_text())['input_tokens'], 8192)
            validation = next(item for item in sources if item['source_position'].endswith('/validator.json'))
            self.assertNotIn('elapsed_seconds', json.loads((native_folder / validation['review_file']).read_text()))
            self.assertTrue((native_folder / 'A-activation.json').exists())
            renders = json.loads((native_folder / 'A-renders.json').read_text())
            self.assertEqual(renders[0]['source_position'], 'operator-evidence/reopened.png')
            rendered = native_folder / renders[0]['review_file']
            self.assertEqual(rendered.read_bytes(), b'synthetic native render bytes')
            self.assertEqual(renders[0]['sha256'], BENCH.sha256(rendered))
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

    def test_eval_usage_excludes_unknown_samples_and_preserves_cache(self):
        rows = [{'run_id': 'known', 'telemetry': {'usage_status': 'PASS', 'usage': {
            'input_tokens': 100, 'cached_input_tokens': 40, 'output_tokens': 5, 'total_tokens': 105}}},
                {'run_id': 'unknown', 'telemetry': {'usage_status': 'NOT_VERIFIED', 'usage': None}}]
        result = BENCH.eval_usage(rows)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['usage']['input_token_details']['cached_tokens'], 40)
        self.assertEqual(result[0]['usage']['total_tokens'], 105)

    def test_eval_does_not_convert_unknown_cache_to_a_measured_zero(self):
        row = {'run_id': 'cache-unknown', 'telemetry': {'usage_status': 'PASS', 'usage': {
            'input_tokens': 100, 'cached_input_tokens': None, 'output_tokens': 5, 'total_tokens': 105}}}
        self.assertEqual(BENCH.eval_usage([row]), [])

    def test_durable_workspace_evidence_excludes_inputs_plugins_and_symlinks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            workspace, evidence = root / 'workspace', root / 'evidence'
            for name in ('outputs/file.txt', 'source.html', 'inputs/official.pptx', 'plugins/SKILL.md'):
                path = workspace / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(name)
            (workspace / 'secret-link').symlink_to('/etc/passwd')
            files = BENCH.collect_workspace(workspace, evidence)
            self.assertEqual(set(files), {'outputs/file.txt', 'source.html'})
            self.assertEqual((evidence / 'source.html').read_text(), 'source.html')

    def test_judge_output_missing_checks_is_rejected(self):
        self.assertFalse(BENCH.valid_review({'preference': 'A', 'findings': [],
                                           'candidates': {'A': {'task_status': 'PASS'}, 'B': {'task_status': 'FAIL'}}}))

    def test_judge_pass_without_dimension_evidence_is_rejected(self):
        candidate = {'task_status': 'PASS', 'mandatory_checks': [{'status': 'PASS', 'evidence': 'answer'}],
                     'qa': {k: {'status': 'PASS', 'method': 'claimed check'} for k in BENCH.QA + BENCH.DESIGN_QA}}
        self.assertFalse(BENCH.valid_review({'preference': 'TIE', 'findings': [],
                                           'candidates': {'A': candidate, 'B': candidate}}))

    def test_critical_finding_and_timeout_cannot_be_hidden_by_a_pass_grade(self):
        row = {'status': 'PASS', 'steps': [{'status': 'TIMEOUT'}]}
        candidate = {'task_status': 'PASS', 'mandatory_checks': [{'status': 'PASS'}]}
        findings = [{'candidate': 'A', 'severity': 'Critical'}]
        self.assertEqual(BENCH.acceptance(row, candidate, findings, 'A'),
                         {'architecture_accepted': False, 'delivery_accepted': False})
        self.assertEqual(BENCH.acceptance(row, candidate, [], 'A'),
                         {'architecture_accepted': True, 'delivery_accepted': False})



    def test_failed_blind_review_cost_is_retained_outside_primary_usage(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            BENCH.write_json(out / 'reviews/raw/pair-01/inference/outcome.json', {
                'status': 'PASS', 'elapsed_seconds': 12,
                'telemetry': {'usage_status': 'PASS', 'usage': {'total_tokens': 105},
                              'tool_calls': 2, 'tool_errors': 0}})
            BENCH.write_json(out / 'reviews/failed-attempts/pair-02-attempt-001/inference/outcome.json', {
                'status': 'FAIL', 'elapsed_seconds': 8,
                'telemetry': {'usage_status': 'NOT_VERIFIED', 'usage': None,
                              'observed_usage': {'total_tokens': 55},
                              'tool_calls': 1, 'tool_errors': 1}})
            (out / 'reviews/raw/pair-03').mkdir()
            report = BENCH.campaign_report(out, BENCH.load_config(ROOT / 'tests/benchmark/campaign.json'))
            cost = report['resource_scope']['independent_reviewers']
            self.assertEqual(cost['recorded_attempts'], 3)
            self.assertEqual(cost['failed_attempts'], 1)
            self.assertEqual(cost['attempts_without_outcome'], 1)
            self.assertEqual(cost['known_usage_attempts'], 1)
            self.assertEqual(cost['observed_total_tokens_lower_bound'], 160)
            self.assertEqual(cost['observed_tool_errors'], 1)
            self.assertEqual(cost['observed_generation_seconds'], 20)
            self.assertIsNone(cost['total_tokens'])
            self.assertEqual(cost['status'], 'NOT_VERIFIED')
            self.assertEqual(report['resource_scope']['known_technical_worker_tokens'], 0)
            self.assertEqual(report['primary_completed'], 0)

    def test_explicit_blanket_approval_unlocks_without_fabricated_human_grades(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            (out / 'reviews').mkdir()
            (out / 'reviews/rubric.md').write_text('Frozen synthetic rubric')
            index = []
            for i in range(24):
                folder = out / f'reviews/packs/pair-{i:02}'
                folder.mkdir(parents=True)
                (folder / 'A.md').write_text('A')
                (folder / 'B.md').write_text('B')
                index.append({'pair_id': folder.name, 'scenario_id': 'case-' + str(i % 8),
                              'input_sha256': BENCH.review_inputs(folder)})
            BENCH.write_json(out / 'reviews/index.json', {'pairs': index})
            BENCH.write_json(out / 'reviews/human-sample.json', {'pairs': index[:8]})
            candidate = {'task_status': 'PASS',
                         'mandatory_checks': [{'status': 'PASS', 'evidence': 'A.md:1'}],
                         'qa': {k: {'status': 'NOT_VERIFIED', 'method': 'Not checked here'}
                                for k in BENCH.QA + BENCH.DESIGN_QA}}
            artifacts = {}
            for pair in index:
                path = out / f'reviews/agent/{pair["pair_id"]}.json'
                findings = ([{'candidate': 'A', 'severity': 'Critical', 'consequence': 'Broken delivery',
                              'evidence': 'A.md:1'}] if pair == index[-1] else [])
                BENCH.write_json(path, dict(pair, reviewer_kind='agent',
                    candidates={'A': candidate, 'B': candidate}, findings=findings, preference='TIE'))
                artifacts[str(path.relative_to(out))] = BENCH.sha256(path)
            BENCH.write_json(out / 'private/conclusion-inputs.json', BENCH.conclusion_inputs(out))
            lock = {'agent_reviews': 24, 'human_reviews': 0, 'critical_reviews_pending': 0,
                    'locked': True, 'artifact_sha256': artifacts,
                    'human_review_mode': 'blanket_approval',
                    'conclusion_sha256': BENCH.sha256(out / 'private/conclusion-inputs.json')}
            self.assertFalse(BENCH.verified_review_lock(out, lock))
            approval = {'approval_kind': 'blanket', 'source': 'direct_user_message',
                        'statement': 'Approved across the board; proceed without detailed spotchecks.',
                        'scope': 'all_required_human_reviews',
                        'detailed_human_assessment': 'NOT_VERIFIED', 'human_preference': None,
                        'review_index_sha256': BENCH.sha256(out / 'reviews/index.json'),
                        'pair_input_sha256': {p['pair_id']: p['input_sha256'] for p in index}}
            path = out / 'reviews/human-approval.json'
            BENCH.write_json(path, approval)
            lock['human_approval_sha256'] = BENCH.sha256(path)
            self.assertTrue(BENCH.verified_review_lock(out, lock))
            BENCH.lock_reviews(out)
            stored = json.loads((out / 'reviews/lock.json').read_text())
            self.assertEqual(stored['human_review_mode'], 'blanket_approval')
            self.assertEqual(stored['human_reviews'], 0)
            self.assertEqual(list((out / 'reviews/human').glob('*.json')), [])
            report = BENCH.campaign_report(out, BENCH.load_config(ROOT / 'tests/benchmark/campaign.json'))
            self.assertTrue(report['unblinded'])
            self.assertEqual(report['human_spotcheck_status'], 'NOT_VERIFIED')
            self.assertEqual(report['conclusion_status'], 'NOT_VERIFIED')
            original = path.read_bytes()
            approval['statement'] = ''
            BENCH.write_json(path, approval)
            self.assertFalse(BENCH.verified_review_lock(out, lock))
            lock['human_approval_sha256'] = BENCH.sha256(path)
            self.assertFalse(BENCH.verified_review_lock(out, lock))
            path.write_bytes(original)
            approval['statement'] = 'Proceed'
            approval['pair_input_sha256'].pop(index[-1]['pair_id'])
            BENCH.write_json(path, approval)
            lock['human_approval_sha256'] = BENCH.sha256(path)
            self.assertFalse(BENCH.verified_review_lock(out, lock))
            self.assertFalse(BENCH.review_gate(dict(lock, agent_reviews=23)))

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
                index.append({'pair_id': folder.name, 'scenario_id': 'case-' + str(i % 8),
                              'input_sha256': BENCH.review_inputs(folder)})
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
            BENCH.write_json(out / 'private/conclusion-inputs.json', BENCH.conclusion_inputs(out))
            lock['conclusion_sha256'] = BENCH.sha256(out / 'private/conclusion-inputs.json')
            self.assertTrue(BENCH.verified_review_lock(out, lock))
            original_sample = (out / 'reviews/human-sample.json').read_bytes()
            BENCH.write_json(out / 'reviews/human-sample.json', {'pairs': index[:7] + [index[8]]})
            BENCH.write_json(out / 'private/conclusion-inputs.json', BENCH.conclusion_inputs(out))
            lock['conclusion_sha256'] = BENCH.sha256(out / 'private/conclusion-inputs.json')
            self.assertFalse(BENCH.verified_review_lock(out, lock))
            (out / 'reviews/human-sample.json').write_bytes(original_sample)
            BENCH.write_json(out / 'private/conclusion-inputs.json', BENCH.conclusion_inputs(out))
            lock['conclusion_sha256'] = BENCH.sha256(out / 'private/conclusion-inputs.json')
            path = out / 'reviews/agent/pair-23.json'
            value = json.loads(path.read_text())
            value['findings'] = [{'candidate': 'A', 'severity': 'Critical', 'consequence': 'Lost data', 'evidence': 'A.md:1'}]
            BENCH.write_json(path, value)
            lock['artifact_sha256'][str(path.relative_to(out))] = BENCH.sha256(path)
            self.assertFalse(BENCH.verified_review_lock(out, lock))

    def test_locked_report_counts_failed_run_cost_and_opens_the_key_only_after_reviews(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            config = BENCH.load_config(ROOT / 'tests/benchmark/campaign.json')
            schedule = BENCH.make_schedule(config)
            failed = next(r['run_id'] for r in schedule if r['arm'] == 'before')
            for row in schedule:
                folder = out / 'runs' / row['run_id']
                usage = {'input_tokens': 95, 'output_tokens': 5, 'total_tokens': 100, 'cached_input_tokens': 30}
                BENCH.write_json(folder / 'result.json', dict(row, status='TIMEOUT' if row['run_id'] == failed else 'PASS',
                    isolation_protocol=BENCH.ISOLATION_PROTOCOL, isolation_status='PASS',
                    workflow_state='COMPLETE', telemetry={'usage_status': 'PASS', 'usage': usage},
                    elapsed_seconds=30, generation_seconds=20, steps=[]))
                (folder / 'answer.md').write_text('Synthetic response')
            BENCH.build_review_pack(out, config)
            self.assertFalse(BENCH.campaign_report(out, config)['unblinded'])
            candidate = {'task_status': 'PASS', 'mandatory_checks': [{'status': 'PASS', 'evidence': 'answer'}],
                         'qa': {k: {'status': 'NOT_VERIFIED', 'method': 'No program check'} for k in BENCH.QA + BENCH.DESIGN_QA}}
            index = json.loads((out / 'reviews/index.json').read_text())['pairs']
            sample = json.loads((out / 'reviews/human-sample.json').read_text())['pairs']
            for kind, pairs in [('agent', index), ('human', sample)]:
                for pair in pairs:
                    BENCH.write_json(out / f'reviews/{kind}/{pair["pair_id"]}.json', dict(pair, reviewer_kind=kind,
                                     candidates={'A': candidate, 'B': candidate}, findings=[], preference='TIE'))
            BENCH.lock_reviews(out)
            report = BENCH.campaign_report(out, config)
            self.assertTrue(report['unblinded'])
            before = report['comparison']['versions']['before']['overall']
            self.assertEqual(before['accepted'], 23)
            self.assertAlmostEqual(before['tokens_per_accepted_task'], 2400 / 23)
            self.assertEqual(report['comparison']['blind_preferences'], {'TIE': 24})
            lock = json.loads((out / 'reviews/lock.json').read_text())
            for relative in ('private/version-key.json', 'reviews/human-sample.json',
                             'runs/' + failed + '/result.json'):
                path = out / relative
                original = path.read_bytes()
                value = json.loads(original)
                value['changed_after_lock'] = True
                BENCH.write_json(path, value)
                self.assertFalse(BENCH.verified_review_lock(out, lock), relative)
                path.write_bytes(original)
            human_path = out / 'reviews/human' / (sample[0]['pair_id'] + '.json')
            value = json.loads(human_path.read_text())
            value['findings'] = [{'candidate': 'A', 'severity': 'Critical',
                                 'consequence': 'Lost reference view', 'evidence': 'A.md:1'}]
            BENCH.write_json(human_path, value)
            BENCH.lock_reviews(out)
            report = BENCH.campaign_report(out, config)
            self.assertEqual(sum(v['overall']['critical_findings'] for v in
                                 report['comparison']['versions'].values()), 1)
            self.assertEqual(sum(v['overall']['architecture_accepted'] for v in
                                 report['comparison']['versions'].values()), 47)
            cases = report['comparison']['case_assessments']
            self.assertEqual(len(cases), 48)
            severe = report['comparison']['case_findings']
            self.assertEqual(len(severe), 1)
            self.assertEqual(severe[0]['consequence'], 'Lost reference view')
            self.assertEqual(severe[0]['evidence'], 'A.md:1')
            self.assertEqual(severe[0]['reviewers'], ['human'])
            self.assertTrue(all('qa' in c and 'mandatory_checks' in c for c in cases))
            markdown = (out / 'report.md').read_text()
            self.assertIn('Severe findings', markdown)
            self.assertIn('Lost reference view', markdown)
            self.assertIn('Per-task results', markdown)
            self.assertIn('known samples', markdown)
            self.assertLess(markdown.index('Severe findings'), markdown.index('Per-task results'))

    def test_human_critical_findings_and_failed_checks_affect_acceptance(self):
        candidate = {'task_status': 'PASS', 'mandatory_checks': [{'status': 'PASS'}]}
        human = {'task_status': 'FAIL', 'mandatory_checks': [{'status': 'FAIL'}]}
        result = BENCH.assessed_candidate(candidate, human)
        self.assertEqual(result['task_status'], 'FAIL')
        findings = BENCH.assessed_findings([], [{'candidate': 'A', 'severity': 'Critical',
            'consequence': 'Lost reference view', 'evidence': 'A-reference.png'}])
        self.assertEqual(len(findings), 1)
        self.assertEqual(BENCH.acceptance({'status': 'PASS'}, result, findings, 'A'),
                         {'architecture_accepted': False, 'delivery_accepted': False})

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
