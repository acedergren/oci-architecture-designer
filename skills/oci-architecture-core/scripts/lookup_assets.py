#!/usr/bin/env python3
"""Return exact service/label matches from verified metadata, never artwork."""
import argparse
import json
from pathlib import Path


def lookup(references, service, kind, sha256):
    references = Path(references)
    mapping = json.loads((references / 'icon-map.json').read_text())
    index = json.loads((references / 'toolkit-index.json').read_text())
    assets = [a for a in index['assets'] if a['kind'] == kind and a['sha256'] == sha256]
    if not assets or mapping['source_hashes'].get(kind) != sha256:
        raise ValueError('Unknown source hash: reindex and review this toolkit before using pinned locators')
    query = ' '.join(service.casefold().split())
    def matches(text):
        return ' '.join(text.casefold().split()) == query
    key = {'drawio': 'drawio_candidates', 'pptx': 'powerpoint_candidates', 'library': 'library_candidates'}[kind]
    mapped = [c for m in mapping['mappings'] if matches(m['service_meaning']) for c in m.get(key, [])]
    allowed = {json.dumps({k: v for k, v in c.items() if k != 'cell_count'}, sort_keys=True) for c in mapped}
    candidates = []
    for asset in assets:
        for entry in asset['entries']:
            locator = {k: v for k, v in entry.items() if k not in {'cell_count', 'element_count'}}
            if matches(entry.get('label', entry.get('title', ''))) or json.dumps(locator, sort_keys=True) in allowed:
                candidates.append(locator)
    return {'status': 'MATCH' if candidates else 'NO_EXACT_MATCH', 'query': service, 'format': kind,
            'source_sha256': sha256, 'candidates': candidates,
            'note': 'Inspect source group/color variant; a metadata match does not verify artwork.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--service', required=True)
    parser.add_argument('--format', choices=['drawio', 'pptx', 'library'], required=True)
    parser.add_argument('--sha256', required=True, help='Hash of the actual source toolkit, not the Draw.io ZIP')
    parser.add_argument('--references', type=Path, default=Path(__file__).resolve().parents[1] / 'references')
    args = parser.parse_args()
    try:
        result = lookup(args.references, args.service, args.format, args.sha256)
    except (ValueError, KeyError, OSError) as error:
        print(json.dumps({'status': 'SOURCE_NOT_VERIFIED', 'error': str(error)}))
        raise SystemExit(1)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
