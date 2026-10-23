#!/usr/bin/env python3
"""Comparable deterministic helper timings; never presents estimates as model usage."""
import argparse
import json
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
import time


def run(root, toolkits, diagram):
    rows = []
    with tempfile.TemporaryDirectory() as tmp:
        commands = [
            [sys.executable, str(root / 'skills/oci-architecture-core/scripts/catalog_assets.py'),
             '--drawio', str(toolkits / 'OCI Architecture Diagram Toolkit v24.2.drawio'),
             '--pptx', str(toolkits / 'OCI_Icons.pptx'), '--output', str(Path(tmp) / 'catalog.json')],
            [sys.executable, str(root / 'skills/oci-drawio-designer/validate_drawio.py'), str(diagram)],
        ]
        for command in commands:
            started = time.perf_counter()
            result = subprocess.run(command, capture_output=True, text=True)
            rows.append({'tool': Path(command[1]).name, 'elapsed_seconds': round(time.perf_counter()-started, 4),
                         'exit_code': result.returncode, 'stdout_bytes': len(result.stdout.encode())})
    return rows


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--before', type=Path, required=True)
    p.add_argument('--after', type=Path, default=Path(__file__).resolve().parents[1])
    p.add_argument('--toolkits', type=Path, required=True)
    p.add_argument('--diagram', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    output = {'scenario': 'same official inputs: index both toolkits and validate the same native graph',
              'environment': {'python': platform.python_version(), 'os': platform.system(), 'machine': platform.machine()},
              'kind': 'deterministic helper benchmark; not an agent task/outcome benchmark',
              'observed_model_tokens': None, 'usage_status': 'NOT_VERIFIED',
              'manual_corrections': None, 'manual_corrections_status': 'NOT_APPLICABLE: deterministic commands',
              'before': [run(args.before, args.toolkits, args.diagram) for _ in range(3)],
              'after': [run(args.after, args.toolkits, args.diagram) for _ in range(3)]}
    args.output.write_text(json.dumps(output, indent=2) + '\n')
    print(json.dumps({key: sum(row['exit_code'] != 0 for run in output[key] for row in run)
                      for key in ['before', 'after']}))


if __name__ == '__main__':
    main()
