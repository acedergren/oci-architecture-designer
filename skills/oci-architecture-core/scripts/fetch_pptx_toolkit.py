#!/usr/bin/env python3
"""Fetch the official PowerPoint toolkit to a verified cache outside the plugin."""
import argparse
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import urllib.request
import zipfile

from fetch_drawio_toolkit import check_cache, check_toolkit_response, check_url, OracleRedirects

URL = 'https://docs.oracle.com/iaas/Content/Resources/Assets/OCI_Icons.pptx'
SHA256 = 'e18615d90fbb38a3354e3a55d7d8baca59f6ba20de1af0a384addba73ede57ea'
MAX_DOWNLOAD = 32 * 1024 * 1024


def fetch(cache_dir, refresh=False, expected_hash=SHA256):
    cache_dir = check_cache(cache_dir)
    target = cache_dir / 'OCI_Icons.pptx'
    reused = target.exists() and not refresh
    headers = {}
    if reused:
        if target.stat().st_size > MAX_DOWNLOAD:
            raise ValueError('Toolkit exceeds maximum size')
        data = target.read_bytes()
    else:
        check_url(URL)
        opener = urllib.request.build_opener(OracleRedirects())
        request = urllib.request.Request(URL, headers={'User-Agent': 'OCI-Architecture-Designer/0.1.3'})
        with opener.open(request, timeout=45) as response:
            check_url(response.geturl())
            data = response.read(MAX_DOWNLOAD + 1)
            headers = {'last_modified': response.headers.get('Last-Modified'), 'final_url': response.geturl()}
    if len(data) > MAX_DOWNLOAD:
        raise ValueError('Toolkit exceeds maximum size')
    check_toolkit_response(data)
    actual = hashlib.sha256(data).hexdigest()
    if actual != expected_hash:
        raise ValueError(f'Toolkit SHA-256 changed: {actual}. Verify source, reindex and review before accepting a new hash.')
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        if not {'[Content_Types].xml', 'ppt/presentation.xml'}.issubset(archive.namelist()):
            raise ValueError('Not a PowerPoint package')
    cache_dir.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    record = {'source_url': URL, 'sha256': actual, 'size_bytes': len(data), 'cache_reused': reused,
              'verified_at_utc': datetime.now(timezone.utc).isoformat(), 'file': target.name,
              'artwork_bundled_in_plugin': False, **headers}
    (cache_dir / 'pptx-toolkit-provenance.json').write_text(json.dumps(record, indent=2) + '\n')
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache-dir', required=True, type=Path)
    parser.add_argument('--refresh', action='store_true')
    parser.add_argument('--expected-sha256', default=SHA256,
                        help='Override only after verifying and reviewing a newer official file')
    args = parser.parse_args()
    if len(args.expected_sha256) != 64 or any(c not in '0123456789abcdef' for c in args.expected_sha256):
        parser.error('Expected SHA-256 must be 64 lowercase hexadecimal characters')
    print(json.dumps(fetch(args.cache_dir, args.refresh, args.expected_sha256), indent=2))


if __name__ == '__main__':
    main()
