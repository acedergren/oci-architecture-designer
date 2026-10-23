#!/usr/bin/env python3
"""Check OOXML package/graph integrity, never visual quality or application behavior."""
import argparse
import json
from pathlib import Path, PurePosixPath
import posixpath
import sys
import urllib.parse
import xml.etree.ElementTree as ET
import zipfile

P = 'http://schemas.openxmlformats.org/presentationml/2006/main'
A = 'http://schemas.openxmlformats.org/drawingml/2006/main'
R = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
NS = {'p': P, 'a': A}
MAX_EXPANDED = 256 * 1024 * 1024


def relationship_source(part):
    if part == '_rels/.rels':
        return ''
    path = PurePosixPath(part)
    if path.parent.name != '_rels':
        raise ValueError(f'Invalid relationships part: {part}')
    return str(path.parent.parent / path.name[:-5])


def resolve_target(source, target):
    parsed = urllib.parse.urlsplit(target)
    if parsed.scheme or parsed.netloc or '\\' in target:
        raise ValueError(f'Invalid internal target: {target}')
    path = urllib.parse.unquote(parsed.path)
    resolved = posixpath.normpath(path.lstrip('/') if path.startswith('/') else
                                 posixpath.join(posixpath.dirname(source), path))
    if resolved in {'.', '..'} or resolved.startswith('../'):
        raise ValueError(f'Internal target escapes package: {target}')
    return resolved


def inspect_package(archive, result):
    errors = result['errors']
    names = archive.namelist()
    entries = archive.infolist()
    if len(names) > 10000 or sum(i.file_size for i in entries) > MAX_EXPANDED:
        raise ValueError('Package exceeds verification size limit')
    if len(names) != len(set(names)):
        errors.append('Duplicate ZIP part names')
    if any(n.startswith('/') or '..' in PurePosixPath(n).parts or '\\' in n for n in names):
        raise ValueError('Unsafe package member name')
    for required in ('[Content_Types].xml', '_rels/.rels', 'ppt/presentation.xml', 'ppt/_rels/presentation.xml.rels'):
        if required not in names:
            errors.append(f'Missing required part: {required}')
    bad = archive.testzip()
    if bad:
        errors.append(f'CRC failure: {bad}')
    trees = {}
    for name in names:
        if name.endswith(('.xml', '.rels')):
            try:
                trees[name] = ET.fromstring(archive.read(name))
            except ET.ParseError as error:
                errors.append(f'Malformed XML: {name}: {error}')
    relations = {}
    for part, tree in trees.items():
        if not part.endswith('.rels'):
            continue
        source = relationship_source(part)
        if source and source not in names:
            errors.append(f'Orphan relationships part: {part}')
        by_id = {}
        for rel in tree:
            identity, target = rel.get('Id'), rel.get('Target', '')
            if not identity or identity in by_id or not target:
                errors.append(f'Invalid/duplicate relationship ID or empty target: {part}: {identity}')
            by_id[identity] = rel
            if rel.get('TargetMode') == 'External':
                result['external_relationships'].append({'source': source, 'id': identity, 'target': target})
            else:
                resolved = resolve_target(source, target)
                if resolved not in names:
                    errors.append(f'Missing relationship target: {source}: {resolved}')
        relations[source] = by_id
    for part, tree in trees.items():
        if part.endswith('.rels'):
            continue
        for element in tree.iter():
            for attribute, value in element.attrib.items():
                if attribute.startswith('{' + R + '}') and value not in relations.get(part, {}):
                    errors.append(f'Unresolved relationship reference: {part}: {value}')
    presentation = trees.get('ppt/presentation.xml')
    if presentation is None or presentation.tag != '{' + P + '}presentation':
        errors.append('Missing/invalid presentation root')
    else:
        seen = set()
        for slide in presentation.findall('p:sldIdLst/p:sldId', NS):
            identity = slide.get('id')
            if not identity or identity in seen:
                errors.append(f'Missing/duplicate slide ID: {identity}')
            seen.add(identity)
            rel = relations.get('ppt/presentation.xml', {}).get(slide.get('{' + R + '}id'))
            if rel is None or rel.get('TargetMode') == 'External' or rel.get('Type') != R + '/slide':
                errors.append(f'Invalid slide relationship: {identity}')
                continue
            target = resolve_target('ppt/presentation.xml', rel.get('Target', ''))
            if target in result['slide_order']:
                errors.append(f'Duplicate slide target: {target}')
            result['slide_order'].append(target)
            if target not in trees or trees[target].tag != '{' + P + '}sld':
                errors.append(f'Invalid slide XML: {target}')
        if not result['slide_order']:
            errors.append('No slides in presentation order')
    for part, tree in trees.items():
        if not part.startswith('ppt/slides/') or tree.tag != '{' + P + '}sld':
            continue
        identities = [node.get('id') for node in tree.findall('.//p:cNvPr', NS)]
        if any(not i or not i.isdigit() for i in identities) or len(identities) != len(set(identities)):
            errors.append(f'Invalid/duplicate shape IDs: {part}')
        for connector in tree.findall('.//p:cxnSp', NS):
            for connection in connector.findall('.//a:stCxn', NS) + connector.findall('.//a:endCxn', NS):
                if connection.get('id') not in identities:
                    errors.append(f'Dangling connector shape: {part}: {connection.get("id")}')


def check(path):
    result = {'file': str(path), 'file_integrity': 'FAIL', 'slide_order': [], 'external_relationships': [],
              'errors': [], 'visual_review': 'NOT_VERIFIED', 'architecture_review': 'NOT_VERIFIED',
              'opening_review': 'NOT_VERIFIED', 'editability_review': 'NOT_VERIFIED'}
    try:
        with zipfile.ZipFile(path) as archive:
            inspect_package(archive, result)
    except (OSError, ValueError, KeyError, zipfile.BadZipFile, RuntimeError) as error:
        result['errors'].append(str(error))
    if not result['errors']:
        result['file_integrity'] = 'PASS'
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('file', type=Path)
    args = parser.parse_args()
    result = check(args.file)
    print(json.dumps(result, indent=2))
    sys.exit(0 if result['file_integrity'] == 'PASS' else 1)


if __name__ == '__main__':
    main()
