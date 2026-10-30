#!/usr/bin/env python3
"""Check native draw.io graph integrity, not visual or architectural correctness."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys

path = Path(__file__).resolve().parents[1] / 'oci-architecture-core/scripts/catalog_assets.py'
spec = importlib.util.spec_from_file_location('catalog_assets', path)
catalog = importlib.util.module_from_spec(spec)
spec.loader.exec_module(catalog)


def inspect_layers(cells: list[dict]) -> list[dict]:
    """Read layer state, never infer OCI membership or mutate source cells."""
    roots = [c for c in cells if not c.get('parent') and c.get('vertex') != '1' and c.get('edge') != '1']
    if len(roots) != 1:
        return []
    layers = []
    for cell in cells:
        if cell.get('parent') == roots[0].get('id') and cell.get('vertex') != '1' and cell.get('edge') != '1':
            style = dict(token.split('=', 1) for token in cell.get('style', '').split(';') if '=' in token)
            layers.append(dict(id=cell.get('id'), name=catalog.clean(cell.get('value', '')),
                               visible=cell.get('visible', '1') != '0', locked=style.get('locked') == '1'))
    return layers


def check_views(pages: list[tuple], manifest: dict) -> dict:
    errors = []
    def require(condition, message):
        if not condition:
            raise ValueError(message)
    def text(value):
        return isinstance(value, str) and bool(value.strip())
    def strings(value, field, nonempty=False):
        require(isinstance(value, list) and all(text(v) for v in value), field + ': expected string list')
        require(len(value) == len(set(value)) and (bool(value) or not nonempty), field + ': duplicate/empty IDs')
        return set(value)
    try:
        require(isinstance(manifest, dict), 'sidecar: expected object')
        require(type(manifest.get('schema_version')) is int and manifest['schema_version'] == 1, 'schema_version: expected integer 1')
        declared = manifest.get('pages')
        require(isinstance(declared, list) and bool(declared), 'pages: expected nonempty list')
        seen_pages, seen_views = set(), set()
        for page in declared:
            require(isinstance(page, dict) and text(page.get('page_name')), 'page_name: expected nonempty string')
            name = page['page_name']
            require(name not in seen_pages, name + ': duplicate page declaration')
            seen_pages.add(name)
            models = [model for n, model in pages if n == name]
            require(len(models) == 1, name + ': missing/ambiguous page')
            cells = catalog.cells_for(models[0]); by_id = {c.get('id'): c for c in cells}
            actual = inspect_layers(cells)
            layers = page.get('layers')
            require(isinstance(layers, list) and bool(layers), name + ': layers must be nonempty')
            require(all(isinstance(l, dict) and text(l.get('id')) and text(l.get('name')) and type(l.get('locked')) is bool for l in layers), name + ': invalid layer id/name/locked')
            strings([l['id'] for l in layers], name + ': layer IDs')
            strings([l['name'] for l in layers], name + ': layer names')
            require([{k: l[k] for k in ('id','name','locked')} for l in actual] == layers,
                    name + ': layer inventory/order/name/lock mismatch')
            layer_ids = {l['id'] for l in actual}
            def visible(identity, shown):
                current, visited = identity, set()
                while current in by_id and current not in visited:
                    visited.add(current); cell = by_id[current]
                    if current in layer_ids:
                        return current in shown
                    if cell.get('visible') == '0' or (current != identity and cell.get('collapsed') == '1'):
                        return False
                    current = cell.get('parent')
                return False
            # Every drawable must terminate in a real layer, not directly in the model root.
            for cell in cells:
                if cell.get('vertex') == '1' or cell.get('edge') == '1':
                    current, visited = cell.get('id'), set()
                    while current in by_id and current not in visited and current not in layer_ids:
                        visited.add(current); current = by_id[current].get('parent')
                    require(current in layer_ids, name + ': drawable has no layer ancestry: ' + str(cell.get('id')))
            views = page.get('views')
            require(isinstance(views, list) and bool(views), name + ': views must be nonempty')
            local = {}
            for view in views:
                require(isinstance(view, dict) and all(text(view.get(k)) for k in ('id','purpose','status')), name + ': invalid view id/purpose/status')
                vid = view['id']; prefix = name + '/' + vid
                require(vid not in seen_views, prefix + ': duplicate view ID')
                seen_views.add(vid); local[vid] = view
                shown = strings(view.get('visible_layer_ids'), prefix + ': visible_layer_ids')
                hidden = strings(view.get('hidden_layer_ids'), prefix + ': hidden_layer_ids')
                require(not shown & hidden and shown | hidden == layer_ids, prefix + ': layer states must form an exact partition')
                required = strings(view.get('required_cell_ids'), prefix + ': required_cell_ids', True)
                omissions = view.get('omissions')
                require(isinstance(omissions, list) and all(isinstance(o, dict) and text(o.get('model_id')) and text(o.get('reason')) for o in omissions), prefix + ': invalid omissions')
                for identity in sorted(required):
                    require(identity in by_id, prefix + ': unknown required cell ' + identity)
                    require(visible(identity, shown), prefix + ': required cell hidden/collapsed: ' + identity)
                for cell in cells:
                    if cell.get('edge') == '1' and visible(cell.get('id'), shown):
                        require(all(visible(cell.get(k), shown) for k in ('source','target')),
                                prefix + ': visible edge has hidden/missing terminal: ' + str(cell.get('id')))
            saved = page.get('saved_view_id')
            require(isinstance(saved, str) and saved in local, name + ': unknown saved_view_id')
            require({l['id'] for l in actual if l['visible']} == set(local[saved]['visible_layer_ids']), name + ': saved visibility mismatch')
    except ValueError as error:
        errors.append(str(error))
    return dict(layer_view_integrity='FAIL' if errors else 'PASS', layer_view_errors=errors)


def check(path: Path, views_path: Path | None = None) -> dict:
    errors = []
    pages = catalog.models(path)
    if not pages:
        errors.append('No diagram pages')
    for name, model in pages:
        cells = catalog.cells_for(model)
        ids = [c.get('id') for c in cells]
        if any(not i for i in ids):
            errors.append(f'{name}: missing cell id')
        if len(set(ids)) != len(ids):
            errors.append(f'{name}: duplicate cell id')
        known = set(ids)
        by_id = {c.get('id'): c for c in cells}
        for cell in cells:
            for field in ['parent', 'source', 'target']:
                if cell.get(field) and cell[field] not in known:
                    errors.append(f'{name}: {cell.get("id")} dangling {field}={cell[field]}')
            if cell.get('edge') == '1' and not (cell.get('source') and cell.get('target')):
                errors.append(f'{name}: edge {cell.get("id")} lacks attached source/target; review annotation separately')
            seen = set()
            current = cell.get('id')
            while current in by_id:
                if current in seen:
                    errors.append(f'{name}: parent cycle at {current}')
                    break
                seen.add(current)
                current = by_id[current].get('parent')
    result = {'file': str(path), 'pages': len(pages), 'errors': errors,
              'graph_integrity': 'PASS' if not errors else 'FAIL',
              'file_integrity': 'PASS' if not errors else 'FAIL',
              'layer_inventory': [dict(page_name=n, layers=inspect_layers(catalog.cells_for(m))) for n,m in pages],
              'layer_view_integrity': 'NOT_VERIFIED', 'layer_view_errors': [],
              'visual_review': 'NOT_VERIFIED', 'architecture_review': 'NOT_VERIFIED',
              'opening_review': 'NOT_VERIFIED', 'editability_review': 'NOT_VERIFIED'}
    if views_path is not None:
        try:
            result.update(check_views(pages, json.loads(Path(views_path).read_text())))
        except (OSError, ValueError) as error:
            result.update(layer_view_integrity='FAIL', layer_view_errors=[str(error)])
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('file', type=Path)
    parser.add_argument('--views', type=Path, help='Optional declared layer/view sidecar')
    args = parser.parse_args()
    try:
        result = check(args.file, args.views)
    except Exception as error:
        result = {'file': str(args.file), 'graph_integrity': 'FAIL', 'file_integrity': 'FAIL',
                  'errors': [str(error)], 'layer_inventory': [],
                  'layer_view_integrity': 'NOT_VERIFIED', 'layer_view_errors': [], 'visual_review': 'NOT_VERIFIED',
                  'architecture_review': 'NOT_VERIFIED', 'opening_review': 'NOT_VERIFIED',
                  'editability_review': 'NOT_VERIFIED'}
    print(json.dumps(result, indent=2))
    sys.exit(0 if result['graph_integrity'] == 'PASS' and result['layer_view_integrity'] != 'FAIL' else 1)


if __name__ == '__main__':
    main()
