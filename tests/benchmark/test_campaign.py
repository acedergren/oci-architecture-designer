"""Catch lost telemetry, contaminated trials and premature conclusions."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
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

    def test_run_refuses_missing_pilot_gate_before_spawning(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, 'pilot'):
                BENCH.require_pilot_gate(Path(tmp), {'campaign_id': 'test'})

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


if __name__ == '__main__':
    unittest.main()
