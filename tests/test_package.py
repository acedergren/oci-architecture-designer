import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))


class PackageChecks(unittest.TestCase):
    def test_manifest_mismatch_broken_link_and_binary_rejected(self):
        import check
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / '.codex-plugin').mkdir()
            (root / 'plugin.json').write_text(json.dumps({'name': 'a', 'version': '1',
                'extensions': {'com.openai': {'interface': {}}}}))
            (root / '.codex-plugin/plugin.json').write_text(json.dumps({'name': 'b', 'version': '2', 'interface': {}}))
            (root / 'SKILL.md').write_text('[missing](references/missing.md)')
            (root / 'toolkit.pptx').write_bytes(b'not for distribution')
            errors = check.package_errors(root, [Path('.codex-plugin/plugin.json'), Path('plugin.json'),
                                                Path('SKILL.md'), Path('toolkit.pptx')])
            self.assertTrue(any('manifest' in e for e in errors))
            self.assertTrue(any('missing.md' in e for e in errors))
            self.assertTrue(any('toolkit.pptx' in e for e in errors))


if __name__ == '__main__':
    unittest.main()
