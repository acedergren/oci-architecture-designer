#!/usr/bin/env python3
"""Fetch Oracle's real draw.io toolkit into a task-local cache, never the plugin."""
import argparse
import hashlib
import io
import json
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
import urllib.parse
import urllib.request
import zipfile

URL = 'https://docs.oracle.com/iaas/Content/Resources/Assets/OCI-Style-Guide-for-Drawio.zip'
SHA256 = '8e20646de88b6197f7b2ce941219fdb61e88b2b6276e3e7b5e0ce046445174e8'
MAX_DOWNLOAD = 32 * 1024 * 1024
MAX_EXPANDED = 64 * 1024 * 1024
FILES = ('OCI Architecture Diagram Toolkit v24.2.drawio', 'OCI Library.xml', 'Read-ME.drawio')


def check_cache(cache_dir):
    resolved = Path(cache_dir).resolve()
    plugin = Path(__file__).resolve().parents[3]
    if resolved.is_relative_to(plugin):
        raise ValueError('Toolkit cache must be outside the plugin package')
    return resolved


def check_url(url):
    p = urllib.parse.urlsplit(url)
    if p.scheme != 'https' or p.hostname != 'docs.oracle.com' or p.username or p.password or p.port not in (None, 443):
        raise ValueError('Only HTTPS downloads from docs.oracle.com are allowed')


class OracleRedirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        check_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def unpack(data, expected_hash):
    actual = hashlib.sha256(data).hexdigest()
    if actual != expected_hash:
        raise ValueError(f'Toolkit SHA-256 changed: {actual}. Verify the official source, reindex and review before accepting a new hash.')
    result = {}
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        entries = z.infolist()
        if len(entries) > 32 or sum(i.file_size for i in entries) > MAX_EXPANDED:
            raise ValueError('Unexpected toolkit archive size')
        for i in entries:
            name = PurePosixPath(i.filename)
            if name.is_absolute() or '..' in name.parts or '\\' in i.filename or ((i.external_attr >> 16) & 0o170000) == 0o120000:
                raise ValueError('Unsafe toolkit archive member')
            if i.is_dir():
                continue
            if len(name.parts) != 2 or name.parts[0] != 'OCI Style Guide for Drawio' or name.name not in FILES or name.name in result:
                raise ValueError(f'Unexpected toolkit member: {i.filename}')
            result[name.name] = z.read(i)
    if set(result) != set(FILES):
        raise ValueError('Official toolkit files missing')
    return actual, result


def fetch(cache_dir, refresh=False, expected_hash=SHA256):
    cache_dir = check_cache(cache_dir)
    archive = cache_dir / 'OCI-Style-Guide-for-Drawio.zip'
    reused = archive.exists() and not refresh
    headers = {}
    if reused:
        data = archive.read_bytes()
    else:
        check_url(URL)
        opener = urllib.request.build_opener(OracleRedirects())
        req = urllib.request.Request(URL, headers={'User-Agent': 'OCI-Architecture-Designer/0.1.2'})
        with opener.open(req, timeout=45) as response:
            check_url(response.geturl())
            data = response.read(MAX_DOWNLOAD + 1)
            headers = {'last_modified': response.headers.get('Last-Modified'), 'final_url': response.geturl()}
    if len(data) > MAX_DOWNLOAD:
        raise ValueError('Toolkit download exceeds maximum size')
    actual, files = unpack(data, expected_hash)
    cache_dir.mkdir(parents=True, exist_ok=True)
    archive.write_bytes(data)
    for name, content in files.items():
        (cache_dir / name).write_bytes(content)
    record = {'source_url': URL, 'sha256': actual, 'size_bytes': len(data), 'cache_reused': reused,
              'verified_at_utc': datetime.now(timezone.utc).isoformat(),
              'artwork_bundled_in_plugin': False, 'files': [
                  {'file': name, 'sha256': hashlib.sha256(content).hexdigest(), 'size_bytes': len(content)}
                  for name, content in files.items()], **headers}
    (cache_dir / 'toolkit-provenance.json').write_text(json.dumps(record, indent=2) + '\n')
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache-dir', required=True, type=Path, help='Task-local output/cache directory outside the plugin package')
    parser.add_argument('--refresh', action='store_true')
    parser.add_argument('--expected-sha256', default=SHA256, help='Override only after verifying and reviewing a newer official archive')
    args = parser.parse_args()
    if len(args.expected_sha256) != 64 or any(c not in '0123456789abcdef' for c in args.expected_sha256):
        parser.error('Expected SHA-256 must be 64 lowercase hexadecimal characters')
    print(json.dumps(fetch(args.cache_dir, args.refresh, args.expected_sha256), indent=2))


if __name__ == '__main__':
    main()
