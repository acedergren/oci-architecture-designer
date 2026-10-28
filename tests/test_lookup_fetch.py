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


class DownloadFailures(unittest.TestCase):
    def test_html_site_unavailable_is_not_a_changed_toolkit_and_preserves_cache(self):
        import fetch_drawio_toolkit as drawio
        import fetch_pptx_toolkit as pptx
        html = b'\xef\xbb\xbf \n<!DOCTYPE HTML><html><title>Site Unavailable</title></html>'
        for module, filename in [(drawio, 'OCI-Style-Guide-for-Drawio.zip'),
                                 (pptx, 'OCI_Icons.pptx')]:
            class Response(io.BytesIO):
                headers = {'Content-Type': 'text/html; charset=UTF-8'}
                def geturl(self):
                    return module.URL
            class Opener:
                def open(self, request, timeout):
                    return Response(html)
            for existing in (False, True):
                with self.subTest(format=filename, existing=existing), tempfile.TemporaryDirectory() as tmp:
                    target = Path(tmp) / filename
                    if existing:
                        target.write_bytes(b'previous cache bytes must survive failed refresh')
                    with patch('urllib.request.build_opener', return_value=Opener()):
                        with self.assertRaisesRegex(ValueError, 'DOWNLOAD_UNAVAILABLE') as caught:
                            module.fetch(tmp, refresh=True)
                    self.assertNotIn('SHA-256 changed', str(caught.exception))
                    if existing:
                        self.assertEqual(target.read_bytes(), b'previous cache bytes must survive failed refresh')
                    else:
                        self.assertFalse(target.exists())
                    self.assertEqual(list(Path(tmp).glob('*provenance.json')), [])

    def test_cached_html_is_rejected_even_if_its_hash_was_supplied(self):
        import fetch_drawio_toolkit as drawio
        import fetch_pptx_toolkit as pptx
        html = b'<html><title>Site Unavailable</title></html>'
        for module, filename in [(drawio, 'OCI-Style-Guide-for-Drawio.zip'),
                                 (pptx, 'OCI_Icons.pptx')]:
            with self.subTest(format=filename), tempfile.TemporaryDirectory() as tmp:
                target = Path(tmp) / filename
                target.write_bytes(html)
                with patch('urllib.request.build_opener', side_effect=AssertionError('No network for cached input')):
                    with self.assertRaisesRegex(ValueError, 'DOWNLOAD_UNAVAILABLE'):
                        module.fetch(tmp, expected_hash=hashlib.sha256(html).hexdigest())
                self.assertEqual(target.read_bytes(), html)
                self.assertEqual(list(Path(tmp).glob('*provenance.json')), [])


if __name__ == '__main__':
    unittest.main()
