#!/usr/bin/env python3
"""Opt-in fixed synthetic scenario; official input/output binaries stay outside Git.

This is a regression fixture builder, not a general architecture generator.
"""
import argparse
import copy
import hashlib
import io
import json
from pathlib import Path
import posixpath
import re
import sys
import time
import xml.etree.ElementTree as E
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'skills/oci-architecture-core/scripts'),
                str(ROOT / 'skills/oci-drawio-designer'), str(ROOT / 'skills/oci-powerpoint-designer')]
import catalog_assets as catalog
from lookup_assets import lookup
import validate_drawio
import validate_pptx

P, A, R = validate_pptx.P, validate_pptx.A, validate_pptx.R
PKG = 'http://schemas.openxmlformats.org/package/2006/relationships'
NS = {'p': P, 'a': A}
SOURCE_NAMESPACES = {}
for prefix, uri in [('p', P), ('a', A), ('r', R)]:
    E.register_namespace(prefix, uri)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def xml_bytes(element):
    # Some renderers require default namespaces on OPC metadata, despite XML equivalence.
    for uri in (PKG, 'http://schemas.openxmlformats.org/package/2006/content-types'):
        if element.tag.startswith('{' + uri + '}'):
            E.register_namespace('', uri)
    text = E.tostring(element, encoding='utf-8', xml_declaration=True).decode()
    required = set()
    for value in re.findall(r'(?:Requires|Ignorable)="([^"]+)"', text):
        required.update(value.split())
    opening = text.split('?>', 1)[-1].split('>', 1)[0]
    for prefix in sorted(required):
        if f'xmlns:{prefix}=' not in opening:
            uri = SOURCE_NAMESPACES[prefix]
            text = text.replace(opening, opening + f' xmlns:{prefix}="{uri}"', 1)
            opening += f' xmlns:{prefix}="{uri}"'
    return text.encode()


def drawio(source, output, model):
    source_hash = digest(source)
    src_models = catalog.models(source)
    icons = dict(src_models)['Icons'].find('root')
    nodes = {n.get('id'): n for n in icons}
    parents = {}
    for n in icons:
        cell = n if n.tag == 'mxCell' else n.find('mxCell')
        if cell is not None:
            parents.setdefault(cell.get('parent'), []).append(n)
    mxfile = E.Element('mxfile', host='OCI Architecture Designer fixture')
    page = E.SubElement(mxfile, 'diagram', name='Architecture', id='architecture')
    graph = E.SubElement(page, 'mxGraphModel', page='1', pageWidth='1100', pageHeight='680', background='#ffffff')
    root = E.SubElement(graph, 'root')
    E.SubElement(root, 'mxCell', id='0'); E.SubElement(root, 'mxCell', id='1', parent='0')
    def vertex(identity, label, x, y, w, h, parent='1', style=''):
        cell = E.SubElement(root, 'mxCell', id=identity, value=label, vertex='1', parent=parent,
                            style=style or 'swimlane;horizontal=1;startSize=40;collapsible=0;recursiveResize=0;rounded=0;whiteSpace=wrap;html=1;fillColor=none;swimlaneFillColor=none;strokeColor=#5b6f66;fontSize=16;')
        E.SubElement(cell, 'mxGeometry', x=str(x), y=str(y), width=str(w), height=str(h), **{'as': 'geometry'})
        return cell
    vertex('title', 'Synthetic OCI architecture — internal traffic', 30, 15, 1000, 45,
           style='text;html=1;strokeColor=none;fillColor=none;align=left;fontSize=24;')
    vertex('region', model['region'], 30, 75, 1020, 490)
    vertex('vcn', 'Regional VCN — ' + model['vcn'], 20, 50, 980, 410, 'region')
    assets = []
    for number, node in enumerate(model['nodes']):
        subnet_id = f'subnet-{number}'
        vertex(subnet_id, model['subnets'][number], 20 + number * 315, 50, 295, 325, 'vcn')
        candidates = lookup(ROOT / 'skills/oci-architecture-core/references', node['service'], 'drawio', source_hash)['candidates']
        selected = candidates[0]
        original = nodes[selected['cell_id']]
        group = []
        def collect(n):
            group.append(n)
            for child in parents.get(n.get('id'), []):
                collect(child)
        collect(original)
        ids = {n.get('id'): node['id'] if n is original else node['id'] + '-' + str(i)
               for i, n in enumerate(group)}
        for n in group:
            clone = copy.deepcopy(n)
            for item in clone.iter():
                for key in ('id', 'parent', 'source', 'target'):
                    if item.get(key) in ids:
                        item.set(key, ids[item.get(key)])
            cell = clone if clone.tag == 'mxCell' else clone.find('mxCell')
            if n is original:
                cell.set('parent', subnet_id)
                geometry = cell.find('mxGeometry')
                geometry.set('x', '45'); geometry.set('y', '95')
            root.append(clone)
        vertex(node['id'] + '-resource', node['resource'], 20, 260, 255, 35, subnet_id,
               'text;html=1;strokeColor=none;fillColor=none;fontSize=15;')
        assets.append({'node_id': node['id'], 'label': selected['label'], 'source_sha256': source_hash, 'locator': selected})
    for flow in model['flows']:
        cell = E.SubElement(root, 'mxCell', id=flow['id'], value=flow['label'], edge='1', parent='vcn',
                            source=flow['source'], target=flow['target'],
                            style='edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;endArrow=block;fontSize=13;labelBackgroundColor=#ffffff;')
        E.SubElement(cell, 'mxGeometry', relative='1', **{'as': 'geometry'})
    vertex('assumptions', 'Proposed example • regional subnets • no HA/DR claim • routes/security not deployed', 35, 590, 1010, 45,
           style='text;html=1;strokeColor=none;fillColor=none;fontSize=15;align=left;')
    reference = E.SubElement(mxfile, 'diagram', name='Preserved reference', id='reference')
    rg = E.SubElement(reference, 'mxGraphModel'); rr = E.SubElement(rg, 'root')
    E.SubElement(rr, 'mxCell', id='0'); E.SubElement(rr, 'mxCell', id='1', parent='0')
    c = E.SubElement(rr, 'mxCell', id='note', value='Unchanged reference page', vertex='1', parent='1')
    E.SubElement(c, 'mxGeometry', x='30', y='30', width='300', height='60', **{'as': 'geometry'})
    output.write_bytes(xml_bytes(mxfile))
    edited = copy.deepcopy(mxfile)
    target = edited.find(".//mxCell[@id='compute']/mxGeometry")
    if target is None:
        target = edited.find(".//UserObject[@id='compute']/mxCell/mxGeometry")
    if target is None:
        target = edited.find(".//object[@id='compute']/mxCell/mxGeometry")
    target.set('y', str(float(target.get('y', '0')) + 25))
    assert E.tostring(reference) == E.tostring(edited.findall('diagram')[1])
    edited_path = output.with_name('architecture-edited.drawio'); edited_path.write_bytes(xml_bytes(edited))
    return assets, edited_path


def pptx(source, output, model):
    source_hash = digest(source)
    with zipfile.ZipFile(source) as z:
        package = {name: z.read(name) for name in z.namelist() if not name.endswith('/')}
    for name, data in package.items():
        if name.endswith(('.xml', '.rels')):
            for _, ns in E.iterparse(io.BytesIO(data), events=['start-ns']):
                SOURCE_NAMESPACES[ns[0]] = ns[1]
    slide = E.fromstring(package['ppt/slides/slide24.xml'])
    tree = slide.find('p:cSld/p:spTree', NS)
    for element in list(tree):
        if element.tag not in {'{' + P + '}nvGrpSpPr', '{' + P + '}grpSpPr'}:
            texts = element.findall('.//a:t', NS)
            text = ' '.join(n.text or '' for n in texts)
            if text.startswith('Copyright'):
                continue
            tree.remove(element)
    used = {int(n.get('id')) for n in tree.findall('.//p:cNvPr', NS)}
    next_id = max(used | {1}) + 1
    relpart = 'ppt/slides/_rels/slide24.xml.rels'
    reltree = E.fromstring(package[relpart])
    for rel in list(reltree):
        if rel.get('Type') in {R + '/notesSlide', R + '/comments'}:
            reltree.remove(rel)
    def alloc():
        nonlocal next_id
        value = next_id; next_id += 1
        return str(value)
    def shape(label, x, y, w, h, border=False):
        identity = alloc()
        s = E.SubElement(tree, '{' + P + '}sp')
        nv = E.SubElement(s, '{' + P + '}nvSpPr')
        E.SubElement(nv, '{' + P + '}cNvPr', id=identity, name=label)
        E.SubElement(nv, '{' + P + '}cNvSpPr'); E.SubElement(nv, '{' + P + '}nvPr')
        props = E.SubElement(s, '{' + P + '}spPr')
        xf = E.SubElement(props, '{' + A + '}xfrm')
        E.SubElement(xf, '{' + A + '}off', x=str(x), y=str(y)); E.SubElement(xf, '{' + A + '}ext', cx=str(w), cy=str(h))
        geom = E.SubElement(props, '{' + A + '}prstGeom', prst='rect'); E.SubElement(geom, '{' + A + '}avLst')
        E.SubElement(props, '{' + A + '}noFill')
        line = E.SubElement(props, '{' + A + '}ln', w='12700')
        if border:
            E.SubElement(E.SubElement(line, '{' + A + '}solidFill'), '{' + A + '}srgbClr', val='5B6F66')
        else:
            E.SubElement(line, '{' + A + '}noFill')
        tx = E.SubElement(s, '{' + P + '}txBody')
        E.SubElement(tx, '{' + A + '}bodyPr', anchor='t'); E.SubElement(tx, '{' + A + '}lstStyle')
        para = E.SubElement(tx, '{' + A + '}p'); run = E.SubElement(para, '{' + A + '}r')
        rpr = E.SubElement(run, '{' + A + '}rPr', lang='en-US', sz='1400')
        E.SubElement(E.SubElement(rpr, '{' + A + '}solidFill'), '{' + A + '}srgbClr', val='23362D')
        E.SubElement(run, '{' + A + '}t').text = label
        return identity
    shape('Synthetic OCI architecture — internal traffic', 330000, 100000, 11000000, 500000)
    shape(model['region'], 330000, 700000, 11500000, 5100000, True)
    shape('Regional VCN — ' + model['vcn'], 520000, 1200000, 11100000, 4300000, True)
    ids, assets, boxes = {}, [], {}
    for number, node in enumerate(model['nodes']):
        x = 720000 + number * 3550000
        shape(model['subnets'][number], x, 1750000, 3300000, 3350000, True)
        candidates = lookup(ROOT / 'skills/oci-architecture-core/references', node['service'], 'pptx', source_hash)['candidates']
        # Prefer dedicated icon-category pages over example diagrams.
        chosen = next((c for c in candidates if c['slide_number'] >= 34), candidates[0])
        # Same-label groups can include editable label-only groups: choose the actual artwork group.
        source_tree = E.fromstring(package[chosen['part']])
        group = next(g for g in source_tree.findall('.//p:grpSp', NS)
                     if g.find('p:nvGrpSpPr/p:cNvPr', NS).get('id') == chosen['shape_id'])
        clone = copy.deepcopy(group)
        remap = {}
        for nv in clone.findall('.//p:cNvPr', NS):
            remap[nv.get('id')] = alloc(); nv.set('id', remap[nv.get('id')])
        identity = clone.find('p:nvGrpSpPr/p:cNvPr', NS)
        identity.set('name', node['id'])
        # Connect to a real geometry's connection sites inside the preserved group.
        # A group ID alone survived parsing but did not follow movement in PowerPoint.
        anchor = next(s for s in clone.findall('.//p:sp', NS) if s.find('.//a:cxnLst', NS) is not None)
        ids[node['id']] = anchor.find('p:nvSpPr/p:cNvPr', NS).get('id')
        for connection in clone.findall('.//a:stCxn', NS) + clone.findall('.//a:endCxn', NS):
            if connection.get('id') in remap:
                connection.set('id', remap[connection.get('id')])
        xf = clone.find('p:grpSpPr/a:xfrm', NS)
        extent = xf.find('a:ext', NS)
        ratio = int(extent.get('cy')) / int(extent.get('cx'))
        width = 1500000; height = round(width * ratio)
        xf.find('a:off', NS).set('x', str(x + 800000)); xf.find('a:off', NS).set('y', '2900000')
        extent.set('cx', str(width)); extent.set('cy', str(height))
        source_relpart = str(Path(chosen['part']).parent / '_rels' / (Path(chosen['part']).name + '.rels'))
        source_rels = {r.get('Id'): r for r in E.fromstring(package[source_relpart])} if source_relpart in package else {}
        for element in clone.iter():
            for attribute, value in list(element.attrib.items()):
                if attribute.startswith('{' + R + '}'):
                    original_rel = source_rels[value]
                    rel = copy.deepcopy(original_rel); new_id = 'copied' + alloc(); rel.set('Id', new_id)
                    if rel.get('TargetMode') != 'External':
                        target = validate_pptx.resolve_target(chosen['part'], rel.get('Target'))
                        rel.set('Target', posixpath.relpath(target, 'ppt/slides'))
                    reltree.append(rel); element.set(attribute, new_id)
        tree.append(clone)
        boxes[node['id']] = (x + 800000, 2900000, width, height)
        shape(node['resource'], x + 200000, 4450000, 2900000, 400000)
        assets.append({'node_id': node['id'], 'label': chosen['label'], 'source_sha256': source_hash, 'locator': chosen})
    for flow in model['flows']:
        start, end = boxes[flow['source']], boxes[flow['target']]
        x, y = start[0] + start[2], start[1] + start[3] // 2
        ex, ey = end[0], end[1] + end[3] // 2
        connector = E.SubElement(tree, '{' + P + '}cxnSp')
        nv = E.SubElement(connector, '{' + P + '}nvCxnSpPr')
        E.SubElement(nv, '{' + P + '}cNvPr', id=alloc(), name=flow['id'])
        cpr = E.SubElement(nv, '{' + P + '}cNvCxnSpPr')
        E.SubElement(cpr, '{' + A + '}stCxn', id=ids[flow['source']], idx='3')
        E.SubElement(cpr, '{' + A + '}endCxn', id=ids[flow['target']], idx='1')
        E.SubElement(nv, '{' + P + '}nvPr')
        props = E.SubElement(connector, '{' + P + '}spPr')
        xf = E.SubElement(props, '{' + A + '}xfrm')
        E.SubElement(xf, '{' + A + '}off', x=str(x), y=str(min(y, ey)))
        E.SubElement(xf, '{' + A + '}ext', cx=str(ex-x), cy=str(abs(ey-y)))
        E.SubElement(E.SubElement(props, '{' + A + '}prstGeom', prst='line'), '{' + A + '}avLst')
        line = E.SubElement(props, '{' + A + '}ln', w='19050')
        E.SubElement(E.SubElement(line, '{' + A + '}solidFill'), '{' + A + '}srgbClr', val='23362D')
        E.SubElement(line, '{' + A + '}tailEnd', type='triangle')
        shape(flow['label'], x-100000, 2400000, 1800000, 350000)
    shape('Proposed example • regional subnets • no HA/DR claim • routes/security not deployed', 350000, 5900000, 11300000, 500000)
    package['ppt/slides/slide24.xml'] = xml_bytes(slide)
    package[relpart] = xml_bytes(reltree)
    # Keep a second, untouched template slide to exercise scoped edits.
    presentation = E.fromstring(package['ppt/presentation.xml'])
    id_list = presentation.find('p:sldIdLst', NS)
    rels = E.fromstring(package['ppt/_rels/presentation.xml.rels'])
    allowed = {r.get('Id') for r in rels if r.get('Target') in {'slides/slide24.xml', 'slides/slide25.xml'}}
    for node in list(id_list):
        if node.get('{' + R + '}id') not in allowed:
            id_list.remove(node)
    for rel in list(rels):
        if rel.get('Type') == R + '/slide' and rel.get('Id') not in allowed:
            rels.remove(rel)
    package['ppt/presentation.xml'] = xml_bytes(presentation)
    package['ppt/_rels/presentation.xml.rels'] = xml_bytes(rels)
    # Keep only reachable parts, retaining template, master, font, media and notes dependencies.
    reachable, queue = set(), ['']
    while queue:
        source_part = queue.pop()
        if source_part:
            reachable.add(source_part)
        path = Path(source_part)
        relationships = '_rels/.rels' if not source_part else str(path.parent / '_rels' / (path.name + '.rels'))
        if relationships not in package:
            continue
        reachable.add(relationships)
        for rel in E.fromstring(package[relationships]):
            if rel.get('TargetMode') != 'External':
                target = validate_pptx.resolve_target(source_part, rel.get('Target'))
                if target not in reachable:
                    queue.append(target)
    types = E.fromstring(package['[Content_Types].xml'])
    for child in list(types):
        if child.tag.endswith('Override') and child.get('PartName', '').lstrip('/') not in reachable:
            types.remove(child)
    package['[Content_Types].xml'] = xml_bytes(types)
    reachable.add('[Content_Types].xml')
    def save(path, parts):
        with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as z:
            for name in sorted(reachable):
                z.writestr(name, parts[name])
    save(output, package)
    edited = dict(package)
    moved = E.fromstring(package['ppt/slides/slide24.xml'])
    target = next(g for g in moved.findall('.//p:grpSp', NS) if g.find('p:nvGrpSpPr/p:cNvPr', NS).get('name') == 'compute')
    target.find('p:grpSpPr/a:xfrm/a:off', NS).set('y', '3150000')
    edited['ppt/slides/slide24.xml'] = xml_bytes(moved)
    assert edited['ppt/slides/slide25.xml'] == package['ppt/slides/slide25.xml']
    edited_path = output.with_name('architecture-edited.pptx'); save(edited_path, edited)
    return assets, edited_path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--toolkits', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    model = json.loads((ROOT / 'tests/fixtures/architecture.json').read_text())
    started = time.perf_counter()
    results = []
    for kind, source, build, validate in [
        ('drawio', args.toolkits / 'OCI Architecture Diagram Toolkit v24.2.drawio', drawio, validate_drawio.check),
        ('pptx', args.toolkits / 'OCI_Icons.pptx', pptx, validate_pptx.check)]:
        output = args.output / ('architecture.' + kind)
        assets, edited = build(source, output, model)
        reports = []
        for path in (output, edited):
            report = validate(path)
            report['file'] = path.name
            reports.append(report)
        evidence = {'schema_version': 1, 'file': output.name, 'model_id': model['model_id'],
                    'source_toolkits': [{'format': kind, 'sha256': digest(source)}], 'assets': assets,
                    'checks': [{'dimension': 'file_integrity', 'method': 'format validator',
                                'status': r['file_integrity'], 'evidence': r} for r in reports],
                    'assumptions': model['assumptions'], 'icon_gaps': [],
                    'application_opening': 'NOT_VERIFIED', 'visual_review': 'NOT_VERIFIED',
                    'editability_review': 'NOT_VERIFIED', 'scoped_edit_preservation': 'PASS'}
        (args.output / (kind + '-evidence.json')).write_text(json.dumps(evidence, indent=2) + '\n')
        results.append({'format': kind, 'status': 'PASS' if all(r['file_integrity']=='PASS' for r in reports) else 'FAIL',
                        'errors': [e for r in reports for e in r['errors']]})
    summary = {'scenario': model['model_id'], 'results': results,
               'elapsed_seconds': round(time.perf_counter()-started, 3),
               'observed_tokens': None, 'usage_status': 'NOT_VERIFIED',
               'usage_reason': 'No model usage log supplied; this is a deterministic fixture exercise, not a model benchmark.'}
    (args.output / 'integration.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary, indent=2))
    return 0 if all(r['status']=='PASS' for r in results) else 1


if __name__ == '__main__':
    sys.exit(main())
