"""Offline package checks and smoke tests; no Oracle artwork required."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / 'skills/oci-drawio-designer/validate_drawio.py'
CATALOG = ROOT / 'skills/oci-architecture-core/scripts/catalog_assets.py'


class PackageChecks(unittest.TestCase):
    def test_json_files_parse(self):
        files = list(ROOT.glob('skills/**/*.json')) + [
            ROOT / 'plugin.json', ROOT / '.codex-plugin/plugin.json',
        ]
        for path in files:
            with self.subTest(path=path.relative_to(ROOT)):
                json.loads(path.read_text())

    def test_manifests_match(self):
        public = json.loads((ROOT / 'plugin.json').read_text())
        compat = json.loads((ROOT / '.codex-plugin/plugin.json').read_text())
        self.assertEqual(compat.pop('interface'), public.pop('extensions')['com.openai']['interface'])
        self.assertEqual(compat.pop('skills'), './skills')
        public.pop('$schema')
        self.assertEqual(public, compat)

    def test_skill_entrypoints_exist(self):
        skills = list((ROOT / 'skills').iterdir())
        self.assertTrue(skills, 'No skills found')
        for skill in skills:
            with self.subTest(skill=skill.name):
                self.assertTrue((skill / 'SKILL.md').is_file())
                self.assertTrue((skill / 'agents/openai.yaml').is_file())

    def test_catalog_cli(self):
        result = subprocess.run([sys.executable, str(CATALOG), '--help'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_graph_validator_accepts_valid_and_rejects_dangling_edge(self):
        graph = ('<mxGraphModel><root><mxCell id="0"/>'
                 '<mxCell id="1" parent="0"/>'
                 '<mxCell id="a" parent="1" vertex="1"/>'
                 '<mxCell id="b" parent="1" vertex="1"/>'
                 '<mxCell id="e" parent="1" edge="1" source="a" target="b"/>'
                 '</root></mxGraphModel>')
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'test.drawio'
            for contents, code, status in [(graph, 0, 'PASS'), (graph.replace('target="b"', 'target="missing"'), 1, 'FAIL')]:
                with self.subTest(status=status):
                    path.write_text(contents)
                    result = subprocess.run([sys.executable, str(VALIDATOR), str(path)], capture_output=True, text=True)
                    self.assertEqual(result.returncode, code, result.stderr)
                    report = json.loads(result.stdout)
                    self.assertEqual(report['graph_integrity'], status)
                    if code:
                        self.assertTrue(any('dangling target' in error for error in report['errors']))


if __name__ == '__main__':
    unittest.main()
