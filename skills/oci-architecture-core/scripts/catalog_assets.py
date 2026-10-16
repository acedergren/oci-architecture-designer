#!/usr/bin/env python3
"""Index user-provided Oracle toolkits as metadata; never download or emit artwork."""
import argparse
import base64
import hashlib
import html
import json
from pathlib import Path
import re
import urllib.parse
import xml.etree.ElementTree as ET
import zipfile
import zlib


def clean(value):
    return ' '.join(html.unescape(re.sub(r'<[^>]*>', ' ', value)).split())


def models(path):
    root = ET.parse(path).getroot()
    if root.tag == 'mxGraphModel':
        return [('Page-1', root)]
    if root.tag != 'mxfile':
        raise ValueError('Expected mxfile or mxGraphModel')
    result = []
    for diagram in root.findall('diagram'):
        model = diagram.find('mxGraphModel')
        if model is None:
            raw = base64.b64decode(diagram.text or '')
            model = ET.fromstring(urllib.parse.unquote(zlib.decompress(raw, -15).decode()))
        result.append((diagram.get('name', 'Page'), model))
    return result


def cells_for(model):
    root = model.find('root')
    if root is None:
        raise ValueError('Missing graph root')
    cells = []
    for node in root:
        cell = node if node.tag == 'mxCell' else node.find('mxCell')
        if cell is None:
            continue
        data = dict(cell.attrib)
        if node.tag != 'mxCell':
            data['id'] = node.get('id', data.get('id'))
            data['value'] = node.get('label', data.get('value', ''))
        cells.append(data)
    return cells


def drawio_index(path):
    result = []
    for page, model in models(path):
        if page != 'Icons':
            continue
        cells = cells_for(model)
        children = {}
        for cell in cells:
            children.setdefault(cell.get('parent'), []).append(cell)

        def descendants(cell, seen):
            key = cell.get('id')
            if key in seen:
                return []
            seen = seen | {key}
            out = []
            for child in children.get(key, []):
                out.append(child)
                out.extend(descendants(child, seen))
            return out

        for cell in cells:
            if 'group' not in cell.get('style', '').split(';'):
                continue
            nested = descendants(cell, set())
            label = clean(' '.join(x.get('value', '') for x in [cell, *nested]))
            if label and len(label) < 160:
                result.append({'page': page, 'cell_id': cell['id'], 'label': label,
                               'cell_count': len(nested) + 1})
    return result


def library_index(path):
    root = ET.parse(path).getroot()
    if root.tag != 'mxlibrary':
        raise ValueError('Expected mxlibrary')
    return [{'entry_index': n, 'title': item.get('title', '')}
            for n, item in enumerate(json.loads(root.text or '[]'))]


def pptx_index(path):
    ns = {'p': 'http://schemas.openxmlformats.org/presentationml/2006/main',
          'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
          'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}
    result = []
    with zipfile.ZipFile(path) as archive:
        presentation = ET.fromstring(archive.read('ppt/presentation.xml'))
        rels = ET.fromstring(archive.read('ppt/_rels/presentation.xml.rels'))
        targets = {rel.get('Id'): rel.get('Target') for rel in rels}
        for number, slide in enumerate(presentation.findall('p:sldIdLst/p:sldId', ns), 1):
            target = targets[slide.get('{%s}id' % ns['r'])]
            # Resolve package-relative slide relationships without extracting files.
            import posixpath
            part = posixpath.normpath(posixpath.join('ppt', target)) if not target.startswith('/') else target[1:]
            root = ET.fromstring(archive.read(part))
            for group in root.findall('.//p:grpSp', ns):
                label = clean(' '.join(t.text or '' for t in group.findall('.//a:t', ns)))
                identity = group.find('p:nvGrpSpPr/p:cNvPr', ns)
                if identity is not None and label and len(label) < 160:
                    result.append({'slide_number': number, 'part': part,
                                   'shape_id': identity.get('id'), 'label': label,
                                   'element_count': sum(1 for _ in group.iter())})
    return result


def asset(path, kind):
    data = path.read_bytes()
    functions = {'drawio': drawio_index, 'library': library_index, 'pptx': pptx_index}
    return {'file_name': path.name, 'size_bytes': len(data),
            'sha256': hashlib.sha256(data).hexdigest(), 'kind': kind,
            'entries': functions[kind](path)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--drawio', type=Path)
    parser.add_argument('--library', type=Path)
    parser.add_argument('--pptx', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    paths = [(args.drawio, 'drawio'), (args.library, 'library'), (args.pptx, 'pptx')]
    if not any(p is not None for p, _ in paths):
        parser.error('Supply at least one toolkit file')
    result = {'metadata_only': True, 'assets': [asset(p, k) for p, k in paths if p is not None]}
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps({'output': str(args.output), 'assets': len(result['assets']),
                      'entries': sum(len(a['entries']) for a in result['assets'])}))


if __name__ == '__main__':
    main()
