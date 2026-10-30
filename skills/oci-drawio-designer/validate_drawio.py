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


def check(path):
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
    return {'file': str(path), 'pages': len(pages), 'errors': errors,
            'graph_integrity': 'PASS' if not errors else 'FAIL',
            'file_integrity': 'PASS' if not errors else 'FAIL',
            'visual_review': 'NOT_VERIFIED', 'architecture_review': 'NOT_VERIFIED',
            'opening_review': 'NOT_VERIFIED', 'editability_review': 'NOT_VERIFIED'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('file', type=Path)
    args = parser.parse_args()
    try:
        result = check(args.file)
    except Exception as error:
        result = {'file': str(args.file), 'graph_integrity': 'FAIL', 'file_integrity': 'FAIL',
                  'errors': [str(error)], 'visual_review': 'NOT_VERIFIED',
                  'architecture_review': 'NOT_VERIFIED', 'opening_review': 'NOT_VERIFIED',
                  'editability_review': 'NOT_VERIFIED'}
    print(json.dumps(result, indent=2))
    sys.exit(0 if result['graph_integrity'] == 'PASS' else 1)


if __name__ == '__main__':
    main()
