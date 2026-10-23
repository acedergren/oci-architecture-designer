import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

CORE = Path(__file__).resolve().parents[1] / 'skills/oci-architecture-core/scripts'
sys.path.insert(0, str(CORE))


class Lookup(unittest.TestCase):
    def test_lookup_filters_by_format_hash_and_exact_service(self):
        import lookup_assets as lookup
        root = CORE.parent / 'references'
        result = lookup.lookup(root, 'Compute virtual machine', 'drawio',
            'b544991da988625e147dbeb7623bacc1be96699e2415d7f4d548f0d2a532d59e')
        self.assertEqual(result['status'], 'MATCH')
        self.assertEqual([m['label'] for m in result['candidates']], ['Virtual Machine'])
        self.assertNotIn('shape_id', result['candidates'][0])
        self.assertLess(len(json.dumps(result)), 2000)
        gap = lookup.lookup(root, 'not a real OCI service', 'pptx',
            'e18615d90fbb38a3354e3a55d7d8baca59f6ba20de1af0a384addba73ede57ea')
        self.assertEqual(gap['status'], 'NO_EXACT_MATCH')
        with self.assertRaisesRegex(ValueError, 'hash'):
            lookup.lookup(root, 'Compute virtual machine', 'drawio', '0' * 64)


def pptx_bytes():
    data = io.BytesIO()
    with zipfile.ZipFile(data, 'w') as z:
        z.writestr('[Content_Types].xml', '<Types/>')
        z.writestr('ppt/presentation.xml', '<presentation/>')
    return data.getvalue()


class FetchPptx(unittest.TestCase):
    def test_cached_file_is_verified_on_every_use(self):
        import fetch_pptx_toolkit as f
        data = pptx_bytes()
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / 'OCI_Icons.pptx'
            p.write_bytes(data)
            with patch('urllib.request.build_opener', side_effect=AssertionError('Network used')):
                result = f.fetch(tmp, expected_hash=hashlib.sha256(data).hexdigest())
                self.assertTrue(result['cache_reused'])
                p.write_bytes(b'corrupt')
                with self.assertRaisesRegex(ValueError, 'SHA-256 changed'):
                    f.fetch(tmp, expected_hash=hashlib.sha256(data).hexdigest())

    def test_download_and_hash_mismatch_do_not_overwrite_cache(self):
        import fetch_pptx_toolkit as f
        data = pptx_bytes()
        class Response(io.BytesIO):
            headers = {}
            def geturl(self):
                return f.URL
        class Opener:
            def open(self, request, timeout):
                return Response(data)
        with tempfile.TemporaryDirectory() as tmp, patch('urllib.request.build_opener', return_value=Opener()):
            with self.assertRaisesRegex(ValueError, 'SHA-256 changed'):
                f.fetch(tmp, expected_hash='0' * 64)
            self.assertFalse((Path(tmp) / 'OCI_Icons.pptx').exists())
            result = f.fetch(tmp, expected_hash=hashlib.sha256(data).hexdigest())
            self.assertFalse(result['cache_reused'])
            self.assertEqual((Path(tmp) / 'OCI_Icons.pptx').read_bytes(), data)

    def test_cache_inside_plugin_is_rejected_for_both_formats(self):
        import fetch_pptx_toolkit as p
        import fetch_drawio_toolkit as d
        for module in (p, d):
            with self.subTest(module=module.__name__), self.assertRaisesRegex(ValueError, 'outside'):
                module.fetch(CORE / 'cache')


if __name__ == '__main__':
    unittest.main()
