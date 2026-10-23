#!/usr/bin/env python3
"""Offline public-source checks and synthetic regression suite. No downloads."""
import json
from pathlib import Path
import re
import subprocess
import sys
import unittest
import urllib.parse

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / 'skills/oci-architecture-core/scripts'


def package_errors(root, files):
    errors = []
    public = json.loads((root / 'plugin.json').read_text())
    compat = json.loads((root / '.codex-plugin/plugin.json').read_text())
    for key in ('name', 'version', 'description', 'author', 'keywords'):
        if public.get(key) != compat.get(key):
            errors.append(f'manifest mismatch: {key}')
    if public.get('extensions', {}).get('com.openai', {}).get('interface') != compat.get('interface'):
        errors.append('manifest mismatch: interface')
    for rel in files:
        path = root / rel
        if path.suffix.lower() in {'.pptx', '.drawio', '.zip', '.png', '.ico', '.ttf', '.woff', '.woff2'}:
            errors.append(f'Forbidden distributed artwork/binary: {rel}')
        if any(p in {'cache', '__pycache__', '.env', '.venv', 'work', 'dist'} for p in rel.parts):
            errors.append(f'Forbidden distributed cache/private file: {rel}')
        if not path.is_file() or path.suffix not in {'.md', '.json', '.yaml', '.py', '.yml'}:
            continue
        text = path.read_text()
        if re.search(r'\bocid1\.|\bsk-[A-Za-z0-9]{20,}|' + '/' + r'Users/[^/\s]+/|[\w.+-]+@oracle\.com', text):
            errors.append(f'Private identifier/local path: {rel}')
        if path.suffix == '.md':
            for target in re.findall(r'\]\(([^)]+)\)', text):
                target = target.strip('<>').split('#')[0]
                if not target or ':' in target:
                    continue
                dest = (path.parent / urllib.parse.unquote(target)).resolve()
                if not dest.is_relative_to(root.resolve()) or not dest.exists():
                    errors.append(f'Broken/outside link: {rel}: {target}')
    return errors


def main():
    tracked = subprocess.check_output(
        ['git', 'ls-files', '--cached', '--others', '--exclude-standard', '-z'], cwd=ROOT).decode().split('\0')
    errors = package_errors(ROOT, [Path(p) for p in tracked if p])
    skills = sorted((ROOT / 'skills').glob('*/SKILL.md'))
    if len(skills) != 4:
        errors.append('Expected four skill entrypoints')
    for skill in skills:
        text = skill.read_text()
        if not text.startswith('---\nname: ' ) or '\ndescription:' not in text.split('---', 2)[1]:
            errors.append(f'Invalid frontmatter: {skill.name}')
        metadata = skill.parent / 'agents/openai.yaml'
        if not metadata.exists() or 'allow_implicit_invocation: true' not in metadata.read_text():
            errors.append(f'Missing implicit invocation metadata: {skill.parent.name}')
    sys.path[:0] = [str(CORE), str(ROOT / 'skills/oci-drawio-designer'),
                    str(ROOT / 'skills/oci-powerpoint-designer')]
    suite = unittest.TestSuite()
    for directory in (CORE, ROOT / 'tests'):
        suite.addTests(unittest.TestLoader().discover(str(directory), pattern='test_*.py'))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    for error in errors:
        print(error, file=sys.stderr)
    print(f'Package checks: {"FAIL" if errors else "PASS"}; {len(skills)} skills; {len(errors)} errors')
    return 0 if result.wasSuccessful() and not errors else 1


if __name__ == '__main__':
    sys.exit(main())
