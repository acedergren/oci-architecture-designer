"""Focused offline checks for download and extraction boundaries."""
import hashlib
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import zipfile
import fetch_drawio_toolkit as f


def archive(names=None):
    b = io.BytesIO()
    with zipfile.ZipFile(b, 'w') as z:
        for name in names or ['OCI Style Guide for Drawio/' + n for n in f.FILES]:
            z.writestr(name, '<fixture/>')
    return b.getvalue()


class Boundaries(unittest.TestCase):
    def test_official_archive_and_cache_without_network(self):
        data = archive(); sha = hashlib.sha256(data).hexdigest()
        with tempfile.TemporaryDirectory() as d:
            Path(d, 'OCI-Style-Guide-for-Drawio.zip').write_bytes(data)
            with patch('urllib.request.build_opener', side_effect=AssertionError('Network used')):
                r = f.fetch(d, expected_hash=sha)
            self.assertTrue(r['cache_reused'])
            self.assertEqual(len(r['files']), 3)
            self.assertTrue(Path(d, f.FILES[0]).exists())

    def test_hash_change_requires_review(self):
        with self.assertRaisesRegex(ValueError, 'SHA-256 changed'):
            f.unpack(archive(), '0' * 64)

    def test_traversal_unknown_and_missing_members_rejected(self):
        for name in ('../escape', '/absolute', 'OCI Style Guide for Drawio/unknown.exe', 'OCI Style Guide for Drawio/OCI Library.xml'):
            data = archive([name])
            with self.subTest(name=name), self.assertRaises(ValueError):
                f.unpack(data, hashlib.sha256(data).hexdigest())

    def test_external_and_insecure_urls_rejected(self):
        for url in ('http://docs.oracle.com/x', 'https://example.org/x', 'https://docs.oracle.com.evil.test/x', 'https://user@docs.oracle.com/x'):
            with self.subTest(url=url), self.assertRaises(ValueError):
                f.check_url(url)
        f.check_url(f.URL)


if __name__ == '__main__':
    unittest.main()
