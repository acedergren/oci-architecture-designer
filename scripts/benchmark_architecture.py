#!/usr/bin/env python3
"""Opt-in, isolated architecture comparison. Never estimates missing telemetry."""
import argparse
from collections import Counter
import hashlib
import io
import json
import os
from pathlib import Path
import random
import re
import shutil
import signal
import subprocess
import sys
import tarfile
import time

ROOT = Path(__file__).resolve().parents[1]
QA = ('asset_identity', 'topology', 'connections', 'file_integrity',
      'application_opening', 'visual_quality', 'editability',
      'cross_format_consistency', 'evidence_honesty')
DESIGN_QA = ('requirement_fit', 'design_decisions', 'workload_behavior')


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')
    temporary.replace(path)


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_config(path):
    path = Path(path).resolve()
    config = json.loads(path.read_text())
    if config.get('schema_version') != 1:
        raise ValueError('Unsupported campaign schema')
    requests = json.loads((path.parent / config['requests']).read_text())
    config['scenarios'] = [dict(row, kind='reasoning') for row in requests] + config['file_scenarios']
    ids = [row['id'] for row in config['scenarios']]
    if len(ids) != len(set(ids)) or len(ids) != 8 or config['repetitions'] != 3:
        raise ValueError('Campaign must contain eight distinct tasks and three repetitions')
    if set(config['revisions']) != {'before', 'after'}:
        raise ValueError('Campaign requires before and after revisions')
    return config


def make_schedule(config):
    rng = random.Random(config['seed'])
    pairs = [(s['id'], n) for s in config['scenarios']
             for n in range(1, config['repetitions'] + 1)]
    rng.shuffle(pairs)
    rows = []
    for case, repetition in pairs:
        arms = ['before', 'after']
        rng.shuffle(arms)
        for arm in arms:
            identity = f'{config["campaign_id"]}:{case}:{repetition}:{arm}'
            rows.append({'run_id': hashlib.sha256(identity.encode()).hexdigest()[:16],
                         'scenario_id': case, 'repetition': repetition, 'arm': arm,
                         'revision': config['revisions'][arm]})
    return rows


def export_runtime(repo, revision, destination):
    destination = Path(destination)
    if destination.exists():
        raise ValueError('Runtime destination already exists')
    data = subprocess.check_output(['git', 'archive', revision], cwd=repo)
    destination.mkdir(parents=True)
    with tarfile.open(fileobj=io.BytesIO(data)) as archive:
        for member in archive.getmembers():
            relative = Path(member.name)
            if relative.is_absolute() or '..' in relative.parts or member.issym() or member.islnk():
                raise ValueError('Unsafe Git archive member')
            if not (member.isfile() and (member.name.startswith('skills/') or
                    member.name in {'plugin.json', '.codex-plugin/plugin.json'})):
                continue
            target = destination / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(archive.extractfile(member).read())
    return {'revision': subprocess.check_output(['git', 'rev-parse', revision], cwd=repo,
                                               text=True).strip(),
            'files': {str(p.relative_to(destination)): sha256(p)
                      for p in sorted(destination.rglob('*')) if p.is_file()}}


def verify_runtime(destination, manifest):
    actual = {str(p.relative_to(destination)): sha256(p)
              for p in Path(destination).rglob('*') if p.is_file()}
    if actual != manifest['files']:
        raise ValueError('Runtime hash changed; review is required')


def prepare_profile(profile, source):
    profile, source = Path(profile), Path(source)
    if profile.exists():
        raise ValueError('Refusing to reuse an existing test profile')
    profile.mkdir(parents=True, mode=0o700)
    auth = source / 'auth.json'
    if not auth.is_file():
        raise ValueError('Authentication file is unavailable; no values were read into reports')
    shutil.copyfile(auth, profile / 'auth.json')
    (profile / 'auth.json').chmod(0o600)
    (profile / 'config.toml').write_text(
        'model = "gpt-6.1-sol"\nmodel_reasoning_effort = "xhigh"\n'
        'approval_policy = "never"\nsandbox_mode = "workspace-write"\n'
        'web_search = "live"\n'
        '[features]\nmemories = false\napps = false\n'
        '[skills.bundled]\nenabled = false\n')


def _objects(value):
    if isinstance(value, dict):
        yield value
        for nested in value.values():
            yield from _objects(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from _objects(nested)


def _usage(raw):
    values = [raw.get('input_tokens'), raw.get('output_tokens')]
    if not all(isinstance(v, int) and not isinstance(v, bool) and v >= 0 for v in values):
        return None
    cached = raw.get('cached_input_tokens', raw.get('cached_tokens'))
    for key in ('input_tokens_details', 'input_token_details'):
        cached = raw.get(key, {}).get('cached_tokens', cached)
    if not isinstance(cached, int) or isinstance(cached, bool) or cached < 0:
        cached = None
    return {'input_tokens': values[0], 'cached_input_tokens': cached,
            'output_tokens': values[1], 'total_tokens': sum(values)}


def summarize_events(events):
    """One terminal usage snapshot per turn; one final state per tool item."""
    usage_by_turn, tools, errors = {}, {}, set()
    turn_number, current_turn, failed, completed = 0, None, False, False
    reads = set()
    for event in events:
        if event.get('type') == 'turn.started':
            turn_number += 1
            current_turn = event.get('turn_id', f'turn-{turn_number}')
        identity = event.get('turn_id', current_turn or 'turn-0')
        if event.get('type') in {'turn.failed', 'turn.cancelled'}:
            failed = True
        for obj in _objects(event):
            kind = obj.get('type', '')
            if kind in {'turn.completed', 'response.completed', 'response.done'}:
                raw = obj.get('usage', obj.get('response', {}).get('usage'))
                if raw is not None:
                    normalized = _usage(raw)
                    if normalized:
                        usage_by_turn[identity] = normalized
                completed = True
            if kind in {'command_execution', 'mcp_tool_call', 'web_search', 'tool_call'}:
                tool_id = obj.get('id', obj.get('call_id'))
                if tool_id:
                    key = f'{identity}:{tool_id}'
                    if obj.get('status') not in {'in_progress', 'pending'} or key not in tools:
                        tools[key] = obj
                    command = str(obj.get('command', obj.get('arguments', '')))
                    for match in re.findall(r'[^\s\'\"]*skills/[^\s\'\"]*SKILL\.md', command):
                        reads.add(match)
            if kind in {'error', 'turn.failed'} or obj.get('error'):
                errors.add(json.dumps(obj.get('error', obj.get('message', obj)), sort_keys=True))
    usage = None
    if usage_by_turn:
        samples = list(usage_by_turn.values())
        usage = {key: sum(row[key] for row in samples) for key in
                 ('input_tokens', 'output_tokens', 'total_tokens')}
        cached = [row['cached_input_tokens'] for row in samples]
        usage['cached_input_tokens'] = sum(cached) if all(v is not None for v in cached) else None
    tool_errors = sum(obj.get('status') == 'failed' or
                      (isinstance(obj.get('exit_code'), int) and obj['exit_code'] != 0) or
                      bool(obj.get('error')) or obj.get('result', {}).get('isError', False)
                      for obj in tools.values())
    return {'status': 'FAIL' if failed else 'PASS' if completed else 'NOT_VERIFIED',
            'usage': usage, 'usage_status': 'PASS' if usage is not None else 'NOT_VERIFIED',
            'tool_calls': len(tools), 'tool_errors': tool_errors,
            'runtime_errors': len(errors), 'skill_read_commands': sorted(reads),
            'agent_retries': None, 'agent_retries_status': 'NOT_VERIFIED'}


def run_process(command, cwd, environment, logs, timeout):
    logs = Path(logs)
    logs.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    timed_out = False
    with (logs / 'events.jsonl').open('wb') as stdout, (logs / 'stderr.log').open('wb') as stderr:
        process = subprocess.Popen(command, cwd=cwd, env=environment,
                                   stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr,
                                   start_new_session=True)
        try:
            code = process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            os.killpg(process.pid, signal.SIGTERM)
            try:
                code = process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                code = process.wait()
    return {'exit_code': code, 'timed_out': timed_out,
            'elapsed_seconds': round(time.monotonic() - started, 4),
            'status': 'TIMEOUT' if timed_out else 'PASS' if code == 0 else 'FAIL'}


def anonymize(text, roots, revisions):
    for root in sorted(roots, key=len, reverse=True):
        text = text.replace(str(root), '[trial]')
    for revision in revisions:
        text = text.replace(revision, '[revision]')
    return re.sub(r'(?i)(plugin(?: version)?\s*[:=]?\s*)0\.(?:1\.3|2\.0)',
                  r'\1[candidate]', text)


def require_pilot_gate(output, config):
    gate = Path(output) / 'pilot-gate.json'
    if not gate.exists():
        raise ValueError('Both pilot runs must pass before primary runs')
    value = json.loads(gate.read_text())
    if value.get('campaign_id') != config['campaign_id'] or value.get('status') != 'PASS':
        raise ValueError('Both pilot runs must pass for this campaign')
    return value


def file_review(evidence):
    result = {key: {'status': 'NOT_VERIFIED', 'method': None, 'evidence': []} for key in QA}
    result['file_integrity'] = evidence.get('structural', result['file_integrity'])
    for key in ('application_opening', 'visual_quality', 'editability'):
        if key in evidence:
            result[key] = evidence[key]
    return result


def review_gate(value):
    return (value.get('agent_reviews') == 24 and value.get('human_reviews') == 8 and
            value.get('critical_reviews_pending') == 0 and value.get('locked') is True)
