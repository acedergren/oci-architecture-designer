#!/usr/bin/env python3
"""Opt-in, isolated architecture comparison. Never estimates missing telemetry."""
import argparse
from collections import Counter
import hashlib
import io
import importlib.metadata
import json
import os
from pathlib import Path
import random
import plistlib
import re
import select
import shutil
import signal
import statistics
import subprocess
import sys
import tarfile
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
CONTROLLER_SHA256 = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
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
    config = (
        'model = "gpt-6.1-sol"\nmodel_reasoning_effort = "xhigh"\n'
        'approval_policy = "on-request"\nweb_search = "cached"\n'
        '[features]\nmemories = false\napps = false\nmulti_agent = false\n'
        '[skills.bundled]\nenabled = false\n')
    for base in (Path.home() / '.agents/skills', source / 'skills'):
        for entry in sorted(base.rglob('SKILL.md')) if base.exists() else []:
            config += '\n[[skills.config]]\npath = ' + json.dumps(str(entry)) + '\nenabled = false\n'
    (profile / 'config.toml').write_text(config)


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
            if kind in {'error', 'turn.failed'} or obj.get('error'):
                errors.add(json.dumps(obj.get('error', obj.get('message', obj)), sort_keys=True))
    for obj in tools.values():
        command = str(obj.get('command', ''))
        if (obj.get('exit_code') == 0 and
                re.search(r'(?:^|[\s;|&])(?:cat|head|tail|sed|rg)\s', command)):
            for match in re.findall(r'[^\s\'\"]*skills/[^\s\'\"]*SKILL\.md', command):
                reads.add(match)
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
    failed_signatures, retries = set(), 0
    for obj in tools.values():
        signature = json.dumps({k: obj.get(k) for k in ('type', 'command', 'server', 'tool', 'arguments')},
                               sort_keys=True)
        if signature in failed_signatures:
            retries += 1
        if obj.get('status') == 'failed' or obj.get('exit_code') not in {None, 0}:
            failed_signatures.add(signature)
    return {'status': 'FAIL' if failed else 'PASS' if completed else 'NOT_VERIFIED',
            'usage': usage, 'usage_status': 'PASS' if usage is not None else 'NOT_VERIFIED',
            'tool_calls': len(tools), 'tool_errors': tool_errors,
            'runtime_errors': len(errors), 'skill_read_commands': sorted(reads),
            'agent_retries': retries, 'agent_retries_status': 'PASS',
            'agent_retries_method': 'Exact failed tool signatures repeated with a new item ID; semantic retries NOT_VERIFIED'}


def run_process(command, cwd, environment, logs, timeout):
    logs = Path(logs)
    logs.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    wall_started = time.time()
    wall_deadline = wall_started + timeout
    timed_out = False
    with (logs / 'events.jsonl').open('wb') as stdout, (logs / 'stderr.log').open('wb') as stderr:
        process = subprocess.Popen(command, cwd=cwd, env=environment,
                                   stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr,
                                   start_new_session=True)
        while True:
            remaining = min(wall_deadline - time.time(), timeout - (time.monotonic() - started))
            if remaining <= 0:
                timed_out = True
                break
            try:
                code = process.wait(timeout=min(1, remaining))
                timed_out = time.time() >= wall_deadline or time.monotonic() - started >= timeout
                break
            except subprocess.TimeoutExpired:
                continue
        if timed_out and remaining <= 0:
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            try:
                code = process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                code = process.wait()
    return {'exit_code': code, 'timed_out': timed_out,
            'elapsed_seconds': round(time.monotonic() - started, 4),
            'wall_elapsed_seconds': round(time.time() - wall_started, 4),
            'deadline_method': 'Earlier of wall-clock deadline and monotonic budget; checked at most every second',
            'status': 'TIMEOUT' if timed_out else 'PASS' if code == 0 else 'FAIL'}


def anonymize(text, roots, revisions):
    for root in sorted(roots, key=len, reverse=True):
        text = text.replace(str(root), '[trial]')
    for revision in revisions:
        text = text.replace(revision, '[revision]')
    text = re.sub(r'(?i)(oci[- ]architecture[- ]designer[/\s]*(?:v|version\s*)?)0\.(?:1\.3|2\.0)',
                  r'\1[candidate]', text)
    text = re.sub(r'(?i)(plugin(?: version)?\s*[:=]?\s*)0\.(?:1\.3|2\.0)',
                  r'\1[candidate]', text)
    text = re.sub(r'(?i)(plugin[^\n]{0,100}?version[\s"\x27:=]*)0\.(?:1\.3|2\.0)',
                  r'\1[candidate]', text)
    return re.sub(r'(?i)("plugin_version"\s*:\s*")0\.(?:1\.3|2\.0)', r'\1[candidate]', text)


def verify_blind_text(text, revisions):
    if (any(revision in text for revision in revisions) or
            re.search(r'(?<![\d.])0\.(?:1\.3|2\.0)(?![\d.])', text)):
        raise ValueError('Unresolved candidate identity in blind inputs; review contextual redaction')


def blind_check_json(text, operator=False):
    """Hide execution resources in QA copies while retaining source dates and check facts."""
    hidden = {'checked_at_epoch', 'captured_at_epoch', 'started_at_epoch', 'finished_at_epoch',
              'elapsed_seconds', 'generation_seconds', 'timing', 'usage', 'telemetry',
              'input_tokens', 'cached_input_tokens', 'output_tokens', 'total_tokens',
              'tool_calls', 'tool_errors', 'runtime_errors', 'agent_retries'}
    def clean(value):
        if isinstance(value, dict):
            return {key: clean(item) for key, item in value.items() if key not in hidden}
        if isinstance(value, list):
            return [clean(item) for item in value]
        if isinstance(value, str):
            return re.sub(r'(?i)post[- ]deadline(?: forensic)?', 'independent operator check', value)
        return value
    value = clean(json.loads(text))
    if operator and isinstance(value, dict):
        value['review_provenance_note'] = ('Independent operator evidence does not establish that the '
            'candidate performed or knew these checks when making an earlier claim. Timeliness is assessed separately.')
    return json.dumps(value, indent=2, ensure_ascii=False)


def review_documents(source):
    saved = source / 'workspace-evidence'
    manifest = source / 'runtime-manifest.json'
    runtime = json.loads(manifest.read_text()).get('files', {}) if manifest.exists() else {}
    instructions = {value for name, value in runtime.items()
                    if name.lower().endswith('.md') or Path(name).name == 'plugin.json'}
    result = []
    for path in sorted(saved.rglob('*')):
        if (not path.is_file() or path.is_symlink() or path.name == 'response.md' or
                path.suffix.lower() not in {'.html', '.htm', '.txt', '.md', '.json'} or
                path.name == 'SKILL.md' or sha256(path) in instructions):
            continue
        relative = path.relative_to(saved)
        material = (path.suffix.lower() in {'.html', '.htm'} or
                    bool({'sources', 'references', 'refs'} & set(relative.parts)) or
                    any(word in path.name.lower() for word in ('source', 'provenance')))
        report = ('outputs' in relative.parts and
                  (any(part.endswith('evidence') for part in relative.parts) or
                   'verification' in path.name.lower() or path.name.lower().startswith('qa')))
        if material or report:
            result.append((path, relative, 'worker_source_material' if material else 'worker_report'))
    return result


def review_activation(source, result):
    catalog = source / 'setup/catalog/events.jsonl'
    text = catalog.read_text() if catalog.exists() else ''
    discovered = sorted(set(re.findall(r'([a-z][a-z0-9-]+)/SKILL\.md', text)))
    reads = sorted({entry['skill'] for phase in result.get('steps', [])
                    for entry in phase.get('skill_read_evidence', [])})
    return {'discovered_skills': discovered, 'discovery_status': 'PASS' if discovered else 'NOT_VERIFIED',
            'read_skills': reads, 'read_status': 'PASS' if reads else 'NOT_VERIFIED',
            'method': 'Catalog observation and successful tool output matching complete immutable skill source',
            'application_status': 'NOT_VERIFIED',
            'application_method': 'Assess use in the decisions/artifact; reading alone is insufficient'}


def require_pilot_gate(output, config):
    gate = Path(output) / 'pilot-gate.json'
    if not gate.exists():
        raise ValueError('Both pilot runs must pass before primary runs')
    value = json.loads(gate.read_text())
    if value.get('campaign_id') != config['campaign_id'] or value.get('status') != 'PASS':
        raise ValueError('Both pilot runs must pass for this campaign')
    if value.get('config_sha256') != config_digest(config):
        raise ValueError('Campaign changed after pilot verification')
    return value


def file_review(evidence):
    result = {key: {'status': 'NOT_VERIFIED', 'method': None, 'evidence': []} for key in QA}
    result['file_integrity'] = evidence.get('structural', result['file_integrity'])
    for key in ('application_opening', 'visual_quality', 'editability'):
        if key in evidence:
            result[key] = evidence[key]
    return result


def review_gate(value):
    return (value.get('agent_reviews') == 24 and value.get('human_reviews', 0) >= 8 and
            value.get('critical_reviews_pending') == 0 and value.get('locked') is True)


def verified_review_lock(output, lock):
    if not review_gate(lock):
        return False
    frozen = output / 'private/conclusion-inputs.json'
    if not frozen.exists() or lock.get('conclusion_sha256') != sha256(frozen):
        return False
    if json.loads(frozen.read_text()) != conclusion_inputs(output):
        return False
    artifacts = lock.get('artifact_sha256', {})
    index_path = output / 'reviews/index.json'
    sample_path = output / 'reviews/human-sample.json'
    if not index_path.exists() or not sample_path.exists():
        return False
    index = {r['pair_id']: r for r in json.loads(index_path.read_text())['pairs']}
    required_human = {r['pair_id'] for r in json.loads(sample_path.read_text())['pairs']}
    if len(index) != 24 or len(required_human) != 8:
        return False
    scenarios = {p['scenario_id'] for p in index.values()}
    sampled = json.loads(sample_path.read_text())['pairs']
    if (len(scenarios) != 8 or len(sampled) != 8 or
            {p.get('scenario_id') for p in sampled} != scenarios or
            any(p['pair_id'] not in index or p.get('scenario_id') != index[p['pair_id']]['scenario_id']
                for p in sampled)):
        return False
    for pair, entry in index.items():
        if review_inputs(output / 'reviews/packs' / pair) != entry.get('input_sha256'):
            return False
    seen = {'agent': set(), 'human': set()}
    for relative, expected in artifacts.items():
        path = (output / relative).resolve()
        if not path.is_relative_to((output / 'reviews').resolve()) or not path.is_file():
            return False
        if sha256(path) != expected:
            return False
        row = json.loads(path.read_text())
        kind, pair = row.get('reviewer_kind'), row.get('pair_id')
        if kind not in seen or pair not in index or pair in seen[kind]:
            return False
        if row.get('input_sha256') != index[pair].get('input_sha256'):
            return False
        if not row.get('input_sha256') or not valid_review(row):
            return False
        seen[kind].add(pair)
        if kind == 'agent' and any(f['severity'] == 'Critical' for f in row['findings']):
            required_human.add(pair)
    return (seen['agent'] == set(index) and required_human <= seen['human'] and
            len(seen['human']) == lock['human_reviews'])


def conclusion_inputs(output):
    """Frozen before grading; bind version mapping, resource records and human selection."""
    paths = [output / p for p in ('private/version-key.json', 'reviews/index.json',
                                  'reviews/human-sample.json', 'reviews/rubric.md')]
    paths += sorted((output / 'runs').glob('*/result.json'))
    return {str(p.relative_to(output)): sha256(p) for p in paths if p.is_file()}


def valid_review(row):
    if row.get('preference') not in {'A', 'B', 'TIE'}:
        return False
    candidates = row.get('candidates', {})
    for label in ('A', 'B'):
        candidate = candidates.get(label, {})
        checks = candidate.get('mandatory_checks', [])
        if candidate.get('task_status') not in {'PASS', 'FAIL'} or not checks:
            return False
        if any(c.get('status') not in {'PASS', 'FAIL'} or not c.get('evidence') for c in checks):
            return False
        dimensions = candidate.get('qa', {})
        if any(dimensions.get(k, {}).get('status') not in
               {'PASS', 'FAIL', 'NOT_VERIFIED', 'NOT_APPLICABLE'} or
               not dimensions.get(k, {}).get('method') for k in QA + DESIGN_QA):
            return False
        if any(dimensions[k]['status'] in {'PASS', 'FAIL'} and not dimensions[k].get('evidence')
               for k in QA + DESIGN_QA):
            return False
    findings = row.get('findings')
    return isinstance(findings, list) and all(
        f.get('severity') in {'Critical', 'Important', 'Minor'} and f.get('candidate') in {'A', 'B'}
        and f.get('consequence') and f.get('evidence') for f in findings)


def workflow_status(steps):
    if any(s['status'] == 'TIMEOUT' for s in steps):
        return 'TIMEOUT'
    return 'PASS' if steps and all(s['status'] == 'PASS' for s in steps) else 'FAIL'


def review_inputs(folder):
    values = {p.name: sha256(p) for p in sorted(folder.iterdir()) if p.is_file()}
    values['rubric.md'] = sha256(folder.parent.parent / 'rubric.md')
    return values


def resource_summary(rows):
    def distribution(values):
        known = [v for v in values if isinstance(v, (int, float))]
        return {'median': statistics.median(known) if known else None,
                'min': min(known) if known else None, 'max': max(known) if known else None,
                'measured': len(known), 'missing': len(values) - len(known)}
    accepted = sum(bool(r.get('accepted')) for r in rows)
    tokens = [r.get('telemetry', {}).get('usage', {}).get('total_tokens')
              if r.get('telemetry', {}).get('usage_status') == 'PASS' and
              r.get('telemetry', {}).get('usage') else None for r in rows]
    complete = bool(rows) and all(v is not None for v in tokens)
    generation = [r.get('generation_seconds') for r in rows]
    elapsed = [r.get('elapsed_seconds') for r in rows]
    result = {'runs': len(rows), 'accepted': accepted,
              'usage_status': 'PASS' if complete else 'NOT_VERIFIED',
              'total_tokens': distribution(tokens), 'generation_seconds': distribution(generation),
              'elapsed_seconds': distribution(elapsed),
              'observed_total_tokens': sum((r.get('telemetry', {}).get('observed_usage') or
                                           r.get('telemetry', {}).get('usage') or {}).get('total_tokens', 0)
                                          for r in rows),
              'tokens_per_accepted_task': sum(tokens) / accepted if complete and accepted else None,
              'generation_seconds_per_accepted_task': sum(generation) / accepted
              if accepted and all(v is not None for v in generation) else None}
    for field in ('input_tokens', 'cached_input_tokens', 'output_tokens'):
        result[field] = distribution([(r.get('telemetry', {}).get('usage') or {}).get(field) for r in rows])
    for field in ('tool_calls', 'tool_errors', 'runtime_errors', 'agent_retries'):
        result[field] = distribution([r.get('telemetry', {}).get(field) for r in rows])
    result['manual_corrections'] = distribution([r.get('manual_corrections') for r in rows])
    return result


def eval_usage(rows):
    result = []
    for row in rows:
        telemetry = row.get('telemetry', {})
        if telemetry.get('usage_status') != 'PASS' or not telemetry.get('usage'):
            continue
        usage = dict(telemetry['usage'])
        cached = usage.pop('cached_input_tokens', None)
        if cached is None:
            # Plugin Eval 0.1.2 converts a missing cache counter to zero.
            continue
        usage['input_token_details'] = {'cached_tokens': cached}
        result.append({'id': row['run_id'], 'usage': usage,
                       'metadata': {'method': 'Measured workflow counters; failed workflows retained',
                                    'scenario': row.get('scenario_id'),
                                    'unmeasured_fields': ['reasoning_tokens']}})
    return result


def acceptance(row, candidate, findings, label):
    architecture = (candidate['task_status'] == 'PASS' and
                    all(c['status'] == 'PASS' for c in candidate['mandatory_checks']) and
                    not any(f['candidate'] == label and f['severity'] == 'Critical' for f in findings))
    execution = ('TIMEOUT' if any(s.get('status') == 'TIMEOUT' for s in row.get('steps', []))
                 else row.get('status'))
    return {'architecture_accepted': architecture, 'delivery_accepted': architecture and execution == 'PASS'}


def assessed_candidate(agent, human=None):
    if human is None:
        return agent
    return dict(agent, task_status='PASS' if agent['task_status'] == human['task_status'] == 'PASS' else 'FAIL',
                mandatory_checks=agent['mandatory_checks'] + human['mandatory_checks'])


def assessed_findings(agent, human):
    unique = {}
    for source, findings in (('agent', agent), ('human', human)):
        for finding in findings:
            key = json.dumps(finding, sort_keys=True)
            entry = unique.setdefault(key, dict(finding, reviewers=[]))
            entry['reviewers'].append(source)
    return list(unique.values())


def comparison_summary(output, rows):
    lock = json.loads((output / 'reviews/lock.json').read_text())
    if not verified_review_lock(output, lock):
        raise ValueError('Versioned comparison requires locked evidence')
    key = json.loads((output / 'private/version-key.json').read_text())['pairs']
    by_run = {r['run_id']: r for r in rows}
    records, preferences, human = [], Counter(), []
    for pair in key:
        pair_id = pair['pair_id']
        review = json.loads((output / 'reviews/agent' / (pair_id + '.json')).read_text())
        preference = review['preference']
        preferences['TIE' if preference == 'TIE' else pair['mapping'][preference]['arm']] += 1
        human_path = output / 'reviews/human' / (pair_id + '.json')
        observation = None
        if human_path.exists():
            observation = json.loads(human_path.read_text())
            human.append({'pair_id': pair_id, 'preference': observation['preference'],
                          'agent_preference': preference, 'agreement': observation['preference'] == preference,
                          'findings': observation['findings']})
        findings = assessed_findings(review['findings'], observation['findings'] if observation else [])
        for label in ('A', 'B'):
            mapping = pair['mapping'][label]
            original = by_run[mapping['run_id']]
            candidate = assessed_candidate(review['candidates'][label],
                                           observation['candidates'][label] if observation else None)
            accepted = acceptance(original, candidate, findings, label)
            candidate_findings = [f for f in findings if f['candidate'] == label]
            records.append(dict(original, **accepted, accepted=accepted['delivery_accepted'],
                                findings=candidate_findings, qa=candidate['qa'], pair_id=pair_id))
    groups = {}
    for arm in ('before', 'after'):
        selected = [r for r in records if r['arm'] == arm]
        def summarize(chosen):
            value = resource_summary(chosen)
            value['architecture_accepted'] = sum(r['architecture_accepted'] for r in chosen)
            value['critical_findings'] = sum(f['severity'] == 'Critical' for r in chosen for f in r['findings'])
            value['important_findings'] = sum(f['severity'] == 'Important' for r in chosen for f in r['findings'])
            value['qa_common'] = {k: dict(Counter(r['qa'][k]['status'] for r in chosen)) for k in QA}
            value['qa_design_separate'] = {k: dict(Counter(r['qa'][k]['status'] for r in chosen)) for k in DESIGN_QA}
            value['repetitions'] = [{'scenario_id': r['scenario_id'], 'repetition': r['repetition'],
                                    'architecture_accepted': r['architecture_accepted'],
                                    'delivery_accepted': r['delivery_accepted'],
                                    'execution_status': 'TIMEOUT' if any(s.get('status') == 'TIMEOUT' for s in r.get('steps', [])) else r['status'],
                                    'tokens': (r['telemetry'].get('usage') or {}).get('total_tokens'),
                                    'usage_status': r['telemetry'].get('usage_status'),
                                    'generation_seconds': r.get('generation_seconds'),
                                    'elapsed_seconds': r.get('elapsed_seconds'),
                                    'read_skills': sorted({s['skill'] for phase in r.get('steps', [])
                                                          for s in phase.get('skill_read_evidence', [])})}
                                   for r in chosen]
            return value
        groups[arm] = {'overall': summarize(selected), 'tasks': {
            scenario: summarize([r for r in selected if r['scenario_id'] == scenario])
            for scenario in sorted({r['scenario_id'] for r in selected})}}
        with (output / ('plugin-eval-' + arm + '-usage.jsonl')).open('w') as stream:
            for event in eval_usage(selected):
                stream.write(json.dumps(event) + '\n')
    return {'versions': groups, 'blind_preferences': dict(preferences), 'human_sample': human,
            'limitations': ['Eight synthetic tasks with three repetitions; no general quality claim.',
                            'Reviewer uses the same pinned model family in independent contexts.',
                            'Unknown usage excludes full cost claims; known-sample medians are labeled.',
                            'Cached search alone does not establish current primary-source verification.',
                            'Post-deadline application checks do not reverse workflow timeouts.']}


def collect_workspace(workspace, destination):
    workspace, destination = workspace.resolve(), destination.resolve()
    files = {}
    for source in sorted(workspace.rglob('*')):
        relative = source.relative_to(workspace)
        if (relative.parts[0] in {'inputs', 'plugins', '.agents', '.git'} or not source.is_file()
                or source.is_symlink() or any(p.is_symlink() for p in source.parents)):
            continue
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        files[str(relative)] = sha256(target)
    return files


def config_digest(config):
    return hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest()


def verify_toolkits(folder, provenance, names):
    expected = {row['name']: row['sha256'] for row in provenance['files']}
    for name in names:
        path = Path(folder) / name
        if not path.is_file() or sha256(path) != expected.get(name):
            raise ValueError(f'Toolkit missing or hash changed: {name}; review and reindex before use')
    return {name: expected[name] for name in names}


def native_permissions(context, controller):
    """Configure the supported workspace profile; never bypass managed requirements."""
    trial, workspace, profile = context['trial'], context['workspace'], context['profile']
    path = profile / 'config.toml'
    text = 'default_permissions = "architecture-benchmark"\n' + path.read_text()
    text += '\n[permissions.architecture-benchmark]\nextends = ":workspace"\n'
    text += '[permissions.architecture-benchmark.workspace_roots]\n'
    text += json.dumps(str(workspace)) + ' = true\n'
    text += '[permissions.architecture-benchmark.filesystem]\n'
    rules = {str(trial.parent): 'deny', str(trial): 'read', str(workspace): 'write',
             str(trial / 'tmp'): 'write', str(workspace / 'plugins'): 'read',
             str(workspace / 'inputs'): 'read', str(profile / 'auth.json'): 'deny',
             str(ROOT.resolve()): 'deny', str(Path(controller).resolve()): 'deny',
             str(Path.home() / '.codex'): 'deny', str(Path.home() / '.agents'): 'deny'}
    for root, access in rules.items():
        text += json.dumps(root) + ' = ' + json.dumps(access) + '\n'
    path.write_text(text)
    return rules


class AppServer:
    """Minimal buffered JSON-RPC client for non-model configuration/guard queries."""
    def __init__(self, command, cwd, environment, logs):
        logs.mkdir(parents=True, exist_ok=True)
        self.stderr = (logs / 'stderr.log').open('wb')
        self.process = subprocess.Popen(command, cwd=cwd, env=environment, stdin=subprocess.PIPE,
                                        stdout=subprocess.PIPE, stderr=self.stderr,
                                        start_new_session=True)
        self.buffer = b''
        self.identity = 0

    def __enter__(self):
        try:
            self.request('initialize', {'clientInfo': {'name': 'architecture-benchmark', 'version': '1'},
                                        'capabilities': {'experimentalApi': True}})
            self.process.stdin.write(b'{"jsonrpc":"2.0","method":"initialized","params":{}}\n')
            self.process.stdin.flush()
            return self
        except BaseException:
            self.__exit__()
            raise

    def request(self, method, params, timeout=30):
        self.identity += 1
        message = {'jsonrpc': '2.0', 'id': self.identity, 'method': method, 'params': params}
        self.process.stdin.write((json.dumps(message) + '\n').encode())
        self.process.stdin.flush()
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            if b'\n' not in self.buffer:
                ready, _, _ = select.select([self.process.stdout], [], [], min(1, max(0, end-time.monotonic())))
                if not ready:
                    continue
                chunk = os.read(self.process.stdout.fileno(), 65536)
                if not chunk:
                    raise ValueError('App-server exited before answering the guard query')
                self.buffer += chunk
            while b'\n' in self.buffer:
                line, self.buffer = self.buffer.split(b'\n', 1)
                if not line.strip():
                    continue
                answer = json.loads(line)
                if 'method' in answer and 'id' in answer:
                    raise ValueError('Guard query requires interactive approval; no approval was fabricated')
                if answer.get('id') != self.identity:
                    continue
                if 'error' in answer:
                    raise ValueError('Guard query rejected: ' + str(answer['error'].get('message')))
                return answer.get('result')
        raise ValueError('App-server guard query timed out')

    def __exit__(self, *unused):
        if self.process.poll() is None:
            self.process.terminate()
        try:
            self.process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            os.killpg(self.process.pid, signal.SIGKILL)
            self.process.wait()
        self.stderr.close()
        self.process.stdin.close()
        self.process.stdout.close()


def read_events(path):
    events, malformed = [], 0
    for line in Path(path).read_text(errors='replace').splitlines():
        if not line.strip():
            continue
        try:
            event = json.loads(line)
            if isinstance(event, dict):
                events.append(event)
            else:
                malformed += 1
        except json.JSONDecodeError:
            malformed += 1
    return events, malformed


def campaign_report(output, config):
    output = Path(output)
    rows = [json.loads(p.read_text()) for p in sorted((output / 'runs').glob('*/result.json'))]
    lock = output / 'reviews/lock.json'
    review = json.loads(lock.read_text()) if lock.exists() else {}
    unblinded = verified_review_lock(output, review)
    result = {'campaign_id': config['campaign_id'], 'planned_primary': 48,
              'primary_completed': sum(r.get('workflow_state') == 'COMPLETE' for r in rows),
              'unblinded': unblinded,
              'conclusion_status': 'PASS' if sum(r.get('workflow_state') == 'COMPLETE' for r in rows) == 48 and unblinded else 'NOT_VERIFIED',
              'review_status': review, 'preflight': None,
              'note': 'No architecture-quality or resource improvement conclusion before review lock.'}
    preflight = output / 'pilot-gate.json'
    if not preflight.exists():
        preflight = output / 'preflight.json'
    if preflight.exists():
        result['preflight'] = json.loads(preflight.read_text())
    counts = Counter('TIMEOUT' if any(s.get('status') == 'TIMEOUT' for s in row.get('steps', []))
                     else row.get('status', 'NOT_VERIFIED') for row in rows)
    result['execution_status_counts'] = dict(counts)
    attempts = list((output / 'infrastructure-attempts').glob('*/result.json'))
    attempts += list((output / 'pilots').glob('*/*/result.json'))
    result['technical_attempts'] = []
    for path in sorted(attempts):
        attempt = json.loads(path.read_text())
        result['technical_attempts'].append({'evidence': str(path.relative_to(output)),
            'status': attempt.get('status', 'NOT_VERIFIED'),
            'reason': attempt.get('infrastructure_error') or attempt.get('reason'),
            'scope': 'Technical setup/pilot; outside primary inference denominator'})
    result['resource_scope'] = {
        'worker_tokens': 'Isolated initial/edit/QA sessions; known failed consumption retained separately',
        'controller_tokens': {'value': None, 'status': 'NOT_VERIFIED'},
        'active_operator_seconds': {'value': None, 'status': 'NOT_VERIFIED'},
        'total_end_to_end_cost_status': 'NOT_VERIFIED'}
    result['usage_complete'] = bool(rows) and all(r.get('telemetry', {}).get('usage') for r in rows)
    if result['conclusion_status'] == 'PASS':
        result['comparison'] = comparison_summary(output, rows)
    write_json(output / 'report.json', result)
    text = ('# Architecture comparison campaign\n\n'
            f'Primary runs recorded: {len(rows)}/48.\n\n'
            f'Comparison conclusion: **{result["conclusion_status"]}**. '
            'Version key remains sealed until 24 agent reviews and eight human sample reviews '
            'are locked and all critical findings are reviewed.\n\n')
    text += f'Technical attempts outside primary runs: {len(result["technical_attempts"])}. Details are retained in report.json.\n\n'
    if result['preflight']:
        text += 'Preflight: ' + result['preflight'].get('status', 'NOT_VERIFIED') + '\n\n'
        text += result['preflight'].get('reason', '') + '\n'
    if 'comparison' in result:
        text += '\n| Version | Critical | Important | Architecture accepted | Delivered within limit | Median tokens | Median seconds |\n'
        text += '| --- | ---: | ---: | ---: | ---: | ---: | ---: |\n'
        for arm, version in (('before', '0.1.3'), ('after', '0.2.0')):
            value = result['comparison']['versions'][arm]['overall']
            text += (f'| {version} | {value["critical_findings"]} | {value["important_findings"]} | '
                     f'{value["architecture_accepted"]}/24 | {value["accepted"]}/24 | '
                     f'{value["total_tokens"]["median"]} | {value["generation_seconds"]["median"]} |\n')
        text += '\nBlind preferences: ' + json.dumps(result['comparison']['blind_preferences']) + '\n\n'
        text += '\n'.join('- ' + item for item in result['comparison']['limitations']) + '\n'
    (output / 'report.md').write_text(text)
    return result


def _capture(command, cwd, environment, folder, timeout=60):
    outcome = run_process(command, cwd, environment, folder, timeout)
    if outcome['status'] != 'PASS':
        raise ValueError(f'Setup command failed: {Path(command[0]).name}; inspect private setup logs')
    return (Path(folder) / 'events.jsonl').read_text()


def environment_inventory(codex, environment):
    result = {'python': {'version': sys.version, 'executable': sys.executable},
              'libraries': {}, 'applications': {}, 'tool_paths': {},
              'drawio_web_version': {'value': None, 'status': 'NOT_VERIFIED'},
              'controller_sha256': CONTROLLER_SHA256}
    try:
        result['codex'] = {'version': subprocess.check_output([codex, '--version'], env=environment,
                                                             text=True, timeout=10, stderr=subprocess.DEVNULL).strip(),
                           'path': shutil.which(codex) or codex}
    except (OSError, subprocess.SubprocessError):
        result['codex'] = {'version': None, 'status': 'NOT_VERIFIED'}
    for name in ('python-pptx', 'Pillow', 'lxml', 'PyMuPDF'):
        try:
            result['libraries'][name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            result['libraries'][name] = None
    for name in ('Microsoft PowerPoint', 'Google Chrome', 'LibreOffice'):
        path = Path('/Applications') / (name + '.app/Contents/Info.plist')
        try:
            with path.open('rb') as stream:
                metadata = plistlib.load(stream)
            result['applications'][name] = {'version': metadata.get('CFBundleShortVersionString'),
                                             'build': metadata.get('CFBundleVersion')}
        except (OSError, ValueError, plistlib.InvalidFileException):
            result['applications'][name] = {'version': None, 'status': 'NOT_VERIFIED'}
    for name in ('node', 'soffice', 'pdftoppm', 'git'):
        result['tool_paths'][name] = shutil.which(name, path=environment.get('PATH', os.defpath))
    return result


def provision_trial(args, config, row, logs):
    trial = Path(tempfile.mkdtemp(prefix='oci-architecture-trial-')).resolve()
    workspace, profile = trial / 'workspace', trial / 'profile'
    write_json(logs / 'context.json', {'trial': str(trial), 'workspace': str(workspace),
                                      'profile': str(profile)})
    workspace.mkdir()
    (trial / 'tmp').mkdir()
    (workspace / 'outputs').mkdir()
    prepare_profile(profile, getattr(args, 'auth_source', Path.home() / '.codex'))
    environment = dict(os.environ)
    # Child-only standard Codex profile selection; the parent's environment is not changed.
    environment.update(CODEX_HOME=str(profile), TMPDIR=str(trial / 'tmp'),
                       PYTHONDONTWRITEBYTECODE='1')
    environment['PATH'] = str(Path(sys.executable).parent) + os.pathsep + environment.get('PATH', '')
    write_json(logs / 'environment.json', environment_inventory(args.codex, environment))
    plugin = workspace / 'plugins/oci-architecture-designer'
    manifest = export_runtime(ROOT, row['revision'], plugin)
    write_json(logs / 'runtime-manifest.json', manifest)
    if args.toolkits:
        provenance = json.loads((plugin / 'skills/oci-architecture-core/references/provenance.json').read_text())
        names = ['OCI Architecture Diagram Toolkit v24.2.drawio', 'OCI_Icons.pptx']
        sources = verify_toolkits(args.toolkits, provenance, names)
        inputs = workspace / 'inputs'
        inputs.mkdir()
        for name in names:
            shutil.copyfile(args.toolkits / name, inputs / name)
        write_json(logs / 'toolkit-manifest.json', sources)
    market = workspace / '.agents/plugins/marketplace.json'
    write_json(market, {'name': 'architecture-benchmark',
                       'interface': {'displayName': 'Architecture Benchmark'},
                       'plugins': [{'name': 'oci-architecture-designer',
                                    'source': {'source': 'local', 'path': './plugins/oci-architecture-designer'},
                                    'policy': {'installation': 'AVAILABLE', 'authentication': 'ON_INSTALL'},
                                    'category': 'Productivity'}]})
    base = [args.codex, '--no-daemon']
    _capture(base + ['plugin', 'marketplace', 'add', str(workspace), '--json'],
             workspace, environment, logs / 'setup/marketplace')
    _capture(base + ['plugin', 'add', 'oci-architecture-designer@architecture-benchmark', '--json'],
             workspace, environment, logs / 'setup/install')
    prompt = _capture(base + ['debug', 'prompt-input'], workspace, environment, logs / 'setup/catalog')
    discovered = sorted(set(re.findall(r'([a-z][a-z0-9-]+)/SKILL\.md', prompt)))
    expected = sorted(p.parent.name for p in (plugin / 'skills').glob('*/SKILL.md'))
    if discovered != expected:
        raise ValueError(f'Contaminated or incomplete skill catalog: {discovered}')
    installed = next((profile / 'plugins/cache/architecture-benchmark/oci-architecture-designer').iterdir())
    verify_runtime(installed, manifest)
    context = {'trial': trial, 'workspace': workspace, 'profile': profile, 'env': environment,
               'codex': args.codex, 'installed': installed, 'manifest': manifest,
               'discovered_skills': discovered}
    context['native_rules'] = native_permissions(context, args.output)
    write_json(logs / 'context.json', {k: str(v) for k, v in context.items()
                                      if isinstance(v, Path)})
    return context


def confinement_checks(context, output, logs):
    """Prove denials before starting any billable inference."""
    marker = output / 'controller-canary.txt'
    marker.write_text('synthetic grading canary\n')
    outside = output / 'must-not-be-written.txt'
    if outside.exists():
        raise ValueError('Unexpected canary output exists')
    commands = {
        'controller_read_denied': ['/bin/cat', str(marker)],
        'repository_read_denied': ['/bin/cat', str(ROOT / 'tests/benchmark/campaign.json')],
        'controller_write_denied': ['/usr/bin/touch', str(outside)],
        'workspace_write_allowed': ['/usr/bin/touch', str(context['workspace'] / 'guard-ok')],
    }
    checks = {}
    with AppServer([context['codex'], '--no-daemon', 'app-server', '--stdio'], context['workspace'],
                   context['env'], logs / 'guard/server') as client:
        profiles = client.request('permissionProfile/list', {})
        if not any(p['id'] == 'architecture-benchmark' and p['allowed'] for p in profiles['data']):
            raise ValueError('Managed requirements do not allow the isolated workspace profile')
        requirements = client.request('configRequirements/read', {})
        allowed = requirements.get('requirements') or {}
        write_json(logs / 'guard/managed-constraints.json', {key: allowed.get(key) for key in
                   ('allowedApprovalPolicies', 'allowedSandboxModes', 'allowedPermissionProfiles',
                    'defaultPermissions', 'allowedWebSearchModes')})
        for label, command in commands.items():
            result = client.request('command/exec', {'command': command, 'cwd': str(context['workspace']),
                                    'permissionProfile': 'architecture-benchmark', 'timeoutMs': 10000})
            write_json(logs / 'guard' / (label + '.json'), result)
            checks[label] = result['exitCode'] == (0 if label.endswith('allowed') else 1)
    if outside.exists() or not all(checks.values()):
        raise ValueError('OS read/write confinement failed')
    write_json(logs / 'confinement.json', checks)
    return checks


def actual_context(profile):
    metadata = []
    for path in profile.glob('sessions/**/*.jsonl'):
        events, _ = read_events(path)
        for event in events:
            if event.get('type') == 'turn_context':
                payload = event.get('payload', {})
                metadata.append({k: payload.get(k) for k in
                                 ('model', 'effort', 'approval_policy', 'permission_profile', 'sandbox_policy')})
    return metadata


def model_status(contexts, config):
    if not contexts:
        return 'NOT_VERIFIED'
    return 'PASS' if all(c.get('model') == config['model'] and
                         c.get('effort') == config['reasoning_effort'] for c in contexts) else 'FAIL'


def measured_skill_reads(installed, events):
    """Match successful command output to immutable complete skill source bytes."""
    sources = {str(p): p.read_text() for p in (Path(installed) / 'skills').glob('*/SKILL.md')}
    matches = []
    seen = set()
    for event in events:
        if event.get('type') != 'item.completed':
            continue
        item = event.get('item', {})
        if item.get('type') != 'command_execution' or item.get('exit_code') != 0:
            continue
        output = item.get('aggregated_output', '')
        for path, source in sources.items():
            identity = (item.get('id'), path)
            if source and source in output and identity not in seen:
                seen.add(identity)
                matches.append({'skill': Path(path).parent.name, 'path': path,
                                'source_sha256': hashlib.sha256(source.encode()).hexdigest(),
                                'tool_item_id': item.get('id'), 'scope': 'full source output'})
    return matches


def profile_total(profile):
    candidates = []
    for path in profile.glob('sessions/**/*.jsonl'):
        events, _ = read_events(path)
        for event in events:
            payload = event.get('payload', {})
            if event.get('type') == 'event_msg' and payload.get('type') == 'token_count':
                info = payload.get('info') or {}
                value = info.get('total_token_usage')
                if value and _usage(value):
                    candidates.append((event.get('timestamp', ''), _usage(value)))
    return max(candidates, key=lambda row: row[0])[1] if candidates else None


def usage_delta(before, after):
    if after is None:
        return None
    if before is None:
        return dict(after)
    result = {}
    for key in ('input_tokens', 'cached_input_tokens', 'output_tokens'):
        old, new = before.get(key), after.get(key)
        if key == 'cached_input_tokens' and (old is None or new is None):
            result[key] = None
        elif old is None or new is None or new < old:
            return None
        else:
            result[key] = new - old
    result['total_tokens'] = result['input_tokens'] + result['output_tokens']
    return result


def inference(args, config, context, prompt, logs, timeout, resume=None):
    if timeout <= 0:
        result = {'status': 'TIMEOUT', 'timed_out': True, 'elapsed_seconds': 0,
                  'thread_id': resume, 'telemetry': summarize_events([]),
                  'reason': 'Workflow wall deadline exhausted before inference'}
        write_json(Path(logs) / 'outcome.json', result)
        return result
    workspace = context['workspace']
    final = workspace / 'response.md'
    final.unlink(missing_ok=True)
    command = [args.codex, '--no-daemon', 'exec']
    if resume:
        command += ['resume', resume]
    command += ['--json', '--skip-git-repo-check', '--output-last-message', str(final),
                '--model', config['model'], '-c',
                'model_reasoning_effort=' + json.dumps(config['reasoning_effort']),
                '-c', 'approval_policy="on-request"']
    if not resume:
        command += ['--cd', str(workspace)]
    command += [prompt]
    counter_before = profile_total(context['profile'])
    result = run_process(command, workspace, context['env'], logs, max(0.1, timeout))
    events, malformed = read_events(logs / 'events.jsonl')
    result['telemetry'] = summarize_events(events)
    result['telemetry']['reported_cli_usage'] = result['telemetry']['usage']
    counter_after = profile_total(context['profile'])
    measured = usage_delta(counter_before, counter_after)
    result['telemetry']['usage'] = measured
    result['telemetry']['usage_status'] = ('PASS' if measured and result['status'] == 'PASS'
                                         else 'NOT_VERIFIED')
    result['telemetry']['usage_method'] = 'Difference of persisted per-thread total_token_usage counters'
    result['counter_before'], result['counter_after'] = counter_before, counter_after
    result['skill_read_evidence'] = measured_skill_reads(context['installed'], events) if 'installed' in context else []
    result['malformed_event_lines'] = malformed
    result['actual_context'] = actual_context(context['profile'])
    result['model_status'] = model_status(result['actual_context'], config)
    if result['status'] == 'PASS' and result['model_status'] != 'PASS':
        result['status'] = 'FAIL'
        result['protocol_error'] = 'Actual model/effort is missing or differs from the pinned configuration'
    result['thread_id'] = next((e.get('thread_id') for e in events if e.get('thread_id')), None)
    if final.exists():
        shutil.copyfile(final, logs / 'answer.md')
    if 'installed' in context:
        verify_runtime(context['installed'], context['manifest'])
        verify_runtime(workspace / 'plugins/oci-architecture-designer', context['manifest'])
    write_json(logs / 'outcome.json', result)
    return result


def native_hashes(workspace):
    return {str(p.relative_to(workspace)): sha256(p) for p in sorted((workspace / 'outputs').rglob('*'))
            if p.is_file() and p.suffix.lower() in {'.drawio', '.pptx'}}


def verify_native_hashes(workspace, expected):
    if native_hashes(workspace) != expected:
        raise ValueError('Native artifact changed during final QA reporting')


def structural_evidence(workspace, output, extension, phases=('initial', 'edited')):
    evidence_path = output / 'file-evidence.json'
    rows = json.loads(evidence_path.read_text()) if evidence_path.exists() else {}
    validator = ROOT / ('skills/oci-drawio-designer/validate_drawio.py' if extension == 'drawio'
                        else 'skills/oci-powerpoint-designer/validate_pptx.py')
    for phase in phases:
        file = workspace / f'outputs/{phase}.{extension}'
        if not file.exists():
            rows[phase] = {'status': 'FAIL', 'reason': 'Requested native file absent'}
            continue
        target = output / 'artifacts' / file.name
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            if sha256(file) != sha256(target):
                rows.setdefault('source_changes', {})[phase] = {
                    'status': 'FAIL', 'method': 'Compared phase snapshot with later workspace bytes',
                    'snapshot_sha256': sha256(target), 'later_sha256': sha256(file)}
            continue
        shutil.copyfile(file, target)
        process = subprocess.run([sys.executable, str(validator), str(target)],
                                 capture_output=True, text=True, timeout=60)
        try:
            report = json.loads(process.stdout)
        except json.JSONDecodeError:
            report = {'raw_stdout': process.stdout, 'stderr': process.stderr}
        rows[phase] = {'status': 'PASS' if process.returncode == 0 else 'FAIL',
                       'sha256': sha256(target), 'report': report,
                       'captured_at_epoch': time.time()}
    rows['application_checks'] = file_review({'structural': rows.get('edited', {})})
    write_json(output / 'file-evidence.json', rows)
    return rows


def _pilot(args, config, arm, root):
    logs = root / arm
    logs.mkdir(parents=True)
    row = {'revision': config['revisions'][arm]}
    context = None
    try:
        context = provision_trial(args, config, row, logs)
        confinement_checks(context, args.output, logs)
        prompt = ('Create outputs/pilot.drawio: a small editable OCI drawing with one Compute '
                  'virtual machine, using the verified local official toolkit if an exact icon exists. '
                  'Record source hash, label and locator and the checks actually performed. '
                  'Do not change infrastructure. Official toolkits, when supplied, are in inputs/.')
        outcome = inference(args, config, context, prompt, logs / 'inference', config['timeout_seconds'])
        file = context['workspace'] / 'outputs/pilot.drawio'
        transfer = file.is_file() and file.stat().st_size > 0
        if transfer:
            shutil.copyfile(file, logs / 'pilot.drawio')
        models = outcome['actual_context']
        model_ok = bool(models) and all(m.get('model') == config['model'] and
                                       m.get('effort') == config['reasoning_effort'] for m in models)
        status = ('PASS' if outcome['status'] == 'PASS' and outcome['telemetry']['usage'] and
                  outcome['skill_read_evidence'] and transfer and model_ok
                  else 'FAIL')
        result = {'status': status, 'discovered_skills': context['discovered_skills'],
                  'usage_verified': outcome['telemetry']['usage'] is not None,
                  'read_evidence_present': bool(outcome['skill_read_evidence']),
                  'file_transfer': transfer, 'model_verified': model_ok,
                  'reason': None if status == 'PASS' else 'Pilot did not satisfy every gate'}
        result['cli_version'] = subprocess.check_output([args.codex, '--version'],
                                                        env=context['env'], text=True).strip()
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        result = {'status': 'FAIL', 'reason': str(error)}
    finally:
        saved_context = logs / 'context.json'
        if saved_context.exists():
            private_profile = Path(json.loads(saved_context.read_text())['profile'])
            (private_profile / 'auth.json').unlink(missing_ok=True)
    write_json(logs / 'result.json', result)
    return result


def execute_command(args, config):
    output = args.output.resolve()
    freeze_rubric(output)
    if args.command == 'preflight':
        if args.reprocess_pilots:
            return reprocess_preflight(args, config)
        if not args.toolkits:
            raise ValueError('Verified local --toolkits are required for both pilots')
        attempt = output / 'pilots' / time.strftime('%Y%m%dT%H%M%S')
        pilots = {arm: _pilot(args, config, arm, attempt) for arm in ('before', 'after')}
        status = 'PASS' if all(p['status'] == 'PASS' for p in pilots.values()) else 'FAIL'
        gate = {'campaign_id': config['campaign_id'], 'config_sha256': config_digest(config),
                'status': status, 'pilots': pilots, 'pilot_evidence': str(attempt),
                'reason': 'Both isolated pilots passed' if status == 'PASS'
                          else 'Primary campaign not started: pilot acceptance remains open',
                'environment': {'python': sys.version.split()[0],
                                'codex': pilots['after'].get('cli_version')}}
        write_json(output / 'preflight.json', gate)
        write_json(output / 'pilot-gate.json', gate)
        campaign_report(output, config)
        print(json.dumps({'status': status, 'pilots': pilots}))
        return 0 if status == 'PASS' else 1
    if args.command == 'run':
        require_pilot_gate(output, config)
        if not args.toolkits:
            raise ValueError('The same verified --toolkits inputs are required for primary runs')
        provenance = json.loads((ROOT / 'skills/oci-architecture-core/references/provenance.json').read_text())
        verify_toolkits(args.toolkits, provenance,
                        ['OCI Architecture Diagram Toolkit v24.2.drawio', 'OCI_Icons.pptx'])
        return run_campaign(args, config)
    if args.judge:
        return judge_campaign(args, config)
    if args.lock_reviews:
        return lock_reviews(output)
    return build_review_pack(output, config)


def combine_telemetry(steps):
    samples = [s['telemetry'].get('usage') for s in steps]
    usage = None
    if samples and all(samples) and all(s['telemetry']['usage_status'] == 'PASS' for s in steps):
        usage = {key: sum(row[key] for row in samples) for key in
                 ('input_tokens', 'output_tokens', 'total_tokens')}
        cached = [row['cached_input_tokens'] for row in samples]
        usage['cached_input_tokens'] = sum(cached) if all(v is not None for v in cached) else None
    observed = [s['telemetry'].get('observed_usage') or s['telemetry'].get('usage') for s in steps]
    observed = [r for r in observed if r]
    observed_usage = {key: sum(r[key] for r in observed) for key in
                      ('input_tokens', 'output_tokens', 'total_tokens')} if observed else None
    if observed_usage:
        caches = [r.get('cached_input_tokens') for r in observed]
        observed_usage['cached_input_tokens'] = sum(caches) if all(v is not None for v in caches) else None
    return {'usage': usage, 'usage_status': 'PASS' if usage else 'NOT_VERIFIED',
            'observed_usage': observed_usage,
            'observed_usage_method': 'Known phase counters; may be an incomplete lower bound',
            'tool_calls': sum(s['telemetry']['tool_calls'] for s in steps),
            'tool_errors': sum(s['telemetry']['tool_errors'] for s in steps),
            'runtime_errors': sum(s['telemetry']['runtime_errors'] for s in steps),
            'skill_read_commands': sorted({p for s in steps for p in s['telemetry']['skill_read_commands']}),
            'agent_retries': sum(s['telemetry']['agent_retries'] for s in steps),
            'agent_retries_status': 'PASS',
            'agent_retries_method': 'Exact failed-call retries; changed-command semantic repairs NOT_VERIFIED'}


def finish_trial(folder, row, steps, status, started, state='COMPLETE'):
    result = dict(row, status=status, workflow_state=state, steps=steps,
                  telemetry=combine_telemetry(steps), started_at_epoch=started,
                  elapsed_seconds=round(time.time()-started, 4) if started is not None else None,
                  generation_seconds=round(sum(s['elapsed_seconds'] for s in steps), 4),
                  manual_corrections=0,
                  manual_corrections_method='No human answer/file correction supplied during these fixed task turns')
    write_json(folder / 'result.json', result)
    answers = []
    for name in ('initial', 'edit', 'qa'):
        answer = folder / name / 'answer.md'
        if answer.exists():
            answers.append('## ' + name + '\n\n' + answer.read_text())
    (folder / 'answer.md').write_text('\n\n'.join(answers))
    context_file = folder / 'context.json'
    if context_file.exists():
        workspace = Path(json.loads(context_file.read_text())['workspace'])
        write_json(folder / 'workspace-manifest.json', collect_workspace(workspace, folder / 'workspace-evidence'))
    return result


def recover_interrupted_trial(folder, row):
    """Keep the interrupted attempt and its answer; never repeat inference implicitly."""
    steps = [json.loads(p.read_text()) for name in ('initial', 'edit', 'qa')
             if (p := folder / name / 'outcome.json').exists()]
    for name in ('initial', 'edit', 'qa'):
        phase = folder / name
        if (phase / 'events.jsonl').exists() and not (phase / 'outcome.json').exists():
            events, _ = read_events(phase / 'events.jsonl')
            telemetry = summarize_events(events)
            telemetry['observed_usage'] = telemetry['usage']
            telemetry['usage_status'] = 'NOT_VERIFIED'
            steps.append({'status': 'INTERRUPTED', 'elapsed_seconds': 0,
                          'telemetry': telemetry, 'timing_status': 'NOT_VERIFIED'})
    context_path = folder / 'context.json'
    if context_path.exists():
        context = json.loads(context_path.read_text())
        response = Path(context['workspace']) / 'response.md'
        phase = next((name for name in ('qa', 'edit', 'initial') if (folder / name).exists()), 'initial')
        target = folder / phase / 'answer.md'
        if response.exists() and not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(response, target)
        (Path(context['profile']) / 'auth.json').unlink(missing_ok=True)
    journal = folder / 'workflow.json'
    started = json.loads(journal.read_text()).get('started_at_epoch') if journal.exists() else None
    result = finish_trial(folder, row, steps, 'INTERRUPTED', started,
                          state='COMPLETE' if steps else 'SETUP_INTERRUPTED')
    result.update(infrastructure_error='Controller interrupted; original attempt retained without inference replay',
                  timing_status='PASS' if started is not None else 'NOT_VERIFIED')
    if any(s.get('timing_status') == 'NOT_VERIFIED' for s in steps):
        result['generation_seconds'] = None
    write_json(folder / 'result.json', result)
    return result


def restore_context(folder, args):
    raw = json.loads((folder / 'context.json').read_text())
    context = {k: Path(v) for k, v in raw.items()}
    context['env'] = dict(os.environ, CODEX_HOME=str(context['profile']),
                          TMPDIR=str(context['trial'] / 'tmp'), PYTHONDONTWRITEBYTECODE='1')
    context['env']['PATH'] = str(Path(sys.executable).parent) + os.pathsep + context['env'].get('PATH', '')
    context['installed'] = next((context['profile'] /
                                'plugins/cache/architecture-benchmark/oci-architecture-designer').iterdir())
    context['manifest'] = json.loads((folder / 'runtime-manifest.json').read_text())
    context['codex'] = args.codex
    return context


def application_evidence(path, artifact):
    value = json.loads(path.read_text())
    if value.get('artifact_sha256') != sha256(artifact):
        raise ValueError('Application evidence is for different artifact bytes')
    for key in ('application_opening', 'visual_quality', 'editability'):
        row = value.get(key, {})
        if row.get('status') not in {'PASS', 'FAIL', 'NOT_VERIFIED'} or not row.get('method'):
            raise ValueError('Application evidence requires status and method for each dimension')
        if row['status'] == 'PASS':
            if not row.get('evidence'):
                raise ValueError('Application PASS requires actual evidence files')
            for name in row['evidence']:
                referenced = (path.parent / name).resolve()
                if not referenced.is_relative_to(path.parent.resolve()) or not referenced.is_file():
                    raise ValueError('Application evidence is missing or outside its run folder')
    return value


def run_campaign(args, config):
    output = args.output.resolve()
    schedule = make_schedule(config)
    schedule_path = output / 'private/schedule.json'
    if schedule_path.exists() and json.loads(schedule_path.read_text()) != schedule:
        raise ValueError('Frozen schedule differs from configuration')
    write_json(schedule_path, schedule)
    lookup = {s['id']: s for s in config['scenarios']}
    for row in schedule:
        folder = output / 'runs' / row['run_id']
        result_path = folder / 'result.json'
        saved = json.loads(result_path.read_text()) if result_path.exists() else None
        if saved is None and folder.exists():
            recover_interrupted_trial(folder, row)
            print(json.dumps({'status': 'INTERRUPTED_ATTEMPT_RETAINED', 'run_id': row['run_id']}), flush=True)
            continue
        if saved and saved['workflow_state'] == 'COMPLETE':
            continue
        if saved and saved['workflow_state'] == 'SETUP_INTERRUPTED':
            print(json.dumps({'status': 'SETUP_INTERRUPTED', 'run_id': row['run_id'],
                              'reason': 'No inference attempted; preserved setup requires explicit recovery'}), flush=True)
            return 1
        scenario = lookup[row['scenario_id']]
        context = None
        steps = saved.get('steps', []) if saved else []
        started = saved['started_at_epoch'] if saved else time.time()
        try:
            if saved:
                if time.time() - started >= config['timeout_seconds']:
                    finish_trial(folder, row, steps, 'TIMEOUT', started)
                    continue
                evidence_path = folder / 'application-evidence.json'
                if not evidence_path.exists():
                    print(json.dumps({'status': 'AWAITING_APPLICATION_CHECKS', 'run_id': row['run_id']}), flush=True)
                    return 2
                context = restore_context(folder, args)
                artifact = folder / 'artifacts' / ('edited.' + scenario['kind'])
                evidence = application_evidence(evidence_path, artifact)
                write_json(context['workspace'] / 'inputs/verification.json', evidence)
                shutil.copyfile(Path.home() / '.codex/auth.json', context['profile'] / 'auth.json')
                (context['profile'] / 'auth.json').chmod(0o600)
                prompt = ('Report final QA using the measured checks in inputs/verification.json and '
                          'the actual files. Keep unavailable checks explicit. Do not edit any native '
                          'artifact during this reporting step.')
                checked_hashes = native_hashes(context['workspace'])
                step = inference(args, config, context, prompt, folder / 'qa',
                                 config['timeout_seconds'] - (time.time()-started),
                                 resume=steps[0]['thread_id'])
                steps.append(step)
                try:
                    verify_native_hashes(context['workspace'], checked_hashes)
                except ValueError as error:
                    step['status'] = 'FAIL'
                    step['artifact_integrity'] = {'status': 'FAIL', 'method': str(error),
                                                  'before': checked_hashes,
                                                  'after': native_hashes(context['workspace'])}
                if step.get('protocol_error'):
                    raise ValueError(step['protocol_error'])
                status = 'TIMEOUT' if time.time()-started >= config['timeout_seconds'] else workflow_status(steps)
                finish_trial(folder, row, steps, status, started)
            else:
                folder.mkdir(parents=True)
                write_json(folder / 'workflow.json', dict(row, started_at_epoch=started,
                                                       controller_sha256=CONTROLLER_SHA256))
                context = provision_trial(args, config, row, folder)
                confinement_checks(context, output, folder)
                prompt = scenario['request']
                if scenario['kind'] != 'reasoning':
                    prompt += '\nVerified local official toolkit files, when supplied, are in inputs/.'
                step = inference(args, config, context, prompt, folder / 'initial',
                                 config['timeout_seconds'] - (time.time()-started))
                steps.append(step)
                if step.get('protocol_error'):
                    raise ValueError(step['protocol_error'])
                if scenario['kind'] == 'reasoning' or step['status'] != 'PASS':
                    status = 'TIMEOUT' if time.time()-started >= config['timeout_seconds'] else step['status']
                    finish_trial(folder, row, steps, status, started)
                else:
                    structural_evidence(context['workspace'], folder, scenario['kind'], phases=('initial',))
                    edit = inference(args, config, context, scenario['follow_up'], folder / 'edit',
                                     config['timeout_seconds'] - (time.time()-started),
                                     resume=step['thread_id'])
                    steps.append(edit)
                    if edit.get('protocol_error'):
                        raise ValueError(edit['protocol_error'])
                    structural_evidence(context['workspace'], folder, scenario['kind'])
                    edited = folder / 'artifacts' / ('edited.' + scenario['kind'])
                    if edited.exists() and edit['status'] == 'PASS':
                        finish_trial(folder, row, steps, 'NOT_VERIFIED', started,
                                     state='AWAITING_APPLICATION_CHECKS')
                        print(json.dumps({'status': 'AWAITING_APPLICATION_CHECKS',
                                          'run_id': row['run_id']}), flush=True)
                        return 2
                    finish_trial(folder, row, steps, workflow_status(steps), started)
        except (ValueError, OSError, subprocess.SubprocessError) as error:
            result = finish_trial(folder, row, steps, 'FAIL', started)
            result['infrastructure_error'] = str(error)
            write_json(folder / 'result.json', result)
            print(json.dumps({'status': 'INFRASTRUCTURE_FAILURE', 'run_id': row['run_id']}), flush=True)
            return 1
        finally:
            path = folder / 'context.json'
            if path.exists():
                (Path(json.loads(path.read_text())['profile']) / 'auth.json').unlink(missing_ok=True)
        print(json.dumps({'status': 'RECORDED', 'run_id': row['run_id']}), flush=True)
    campaign_report(output, config)
    return 0


def reprocess_preflight(args, config):
    """Reinterpret preserved pilot bytes after a telemetry fix; no inference or auth."""
    output = args.output.resolve()
    previous = json.loads((output / 'preflight.json').read_text())
    root = Path(previous['pilot_evidence'])
    rows = {}
    for arm in ('before', 'after'):
        folder = root / arm
        context = restore_context(folder, args)
        verify_runtime(context['installed'], context['manifest'])
        original = json.loads((folder / 'inference/outcome.json').read_text())
        events, malformed = read_events(folder / 'inference/events.jsonl')
        telemetry = summarize_events(events)
        reads = measured_skill_reads(context['installed'], events)
        confinement = json.loads((folder / 'confinement.json').read_text())
        models = original.get('actual_context', [])
        file = folder / 'pilot.drawio'
        valid = False
        if file.exists():
            check = subprocess.run([sys.executable, str(ROOT / 'skills/oci-drawio-designer/validate_drawio.py'),
                                    str(file)], capture_output=True, text=True, timeout=30)
            valid = check.returncode == 0
            (folder / 'reanalysis-validation.json').write_text(check.stdout)
        model_ok = bool(models) and all(m.get('model') == config['model'] and
                                       m.get('effort') == config['reasoning_effort'] for m in models)
        native_ok = bool(models) and all(any(
            p.get('path', {}).get('path') == str(ROOT.resolve()) and p.get('access') == 'deny'
            for p in m.get('permission_profile', {}).get('file_system', {}).get('entries', []))
            for m in models)
        passed = (all(confinement.values()) and model_ok and native_ok and bool(reads) and valid
                  and telemetry['usage'] is not None and original['status'] == 'PASS' and malformed == 0)
        rows[arm] = {'status': 'PASS' if passed else 'FAIL', 'model_verified': model_ok,
                     'native_profile_verified': native_ok, 'file_transfer_and_structure': valid,
                     'skill_read_evidence': reads, 'telemetry': telemetry,
                     'source_events_sha256': sha256(folder / 'inference/events.jsonl'),
                     'source_outcome_sha256': sha256(folder / 'inference/outcome.json')}
        write_json(folder / 'reanalysis.json', rows[arm])
    status = 'PASS' if all(row['status'] == 'PASS' for row in rows.values()) else 'FAIL'
    value = {'campaign_id': config['campaign_id'], 'config_sha256': config_digest(config),
             'status': status, 'pilots': rows, 'pilot_evidence': str(root),
             'environment': previous.get('environment'), 'reprocessed_without_inference': True,
             'reason': 'Preserved native-profile pilots reprocessed against exact skill source output'}
    write_json(output / 'pilot-gate.json', value)
    write_json(output / 'preflight-reanalysis.json', value)
    print(json.dumps({'status': status, 'reprocessed_without_inference': True,
                      'pilot_status': {arm: row['status'] for arm, row in rows.items()}}))
    return 0 if status == 'PASS' else 1


def freeze_rubric(output):
    path = output / 'frozen/rubric.md'
    lock = output / 'frozen/rubric-lock.json'
    if path.exists() or lock.exists():
        if not path.exists() or not lock.exists() or sha256(path) != json.loads(lock.read_text())['sha256']:
            raise ValueError('Frozen rubric hash changed or lock is missing')
        return path.read_text()
    rubric = (ROOT / 'tests/architecture-reasoning.md').read_text()
    rubric += ('\n\nFor native file tasks, examine both phases, preservation of the reference view, '
               'required resources/flows, official asset evidence and separately executed application '
               'opening, rendering and move/save/reopen checks. Unknown checks must not be promoted '
               'from parser success. Examine QA reporting and source applicability.\n\n'
               'For each candidate return mandatory checks with PASS/FAIL and cited evidence, '
               'task_status, findings with Critical/Important/Minor severity, and A/B/TIE preference. '
               'A missing application dependency is a verification gap; distinguish it from an '
               'architecture mistake. Do not infer the plugin version.\n')
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(rubric)
    write_json(lock, {'sha256': sha256(path), 'created_at_epoch': time.time()})
    return rubric


def build_review_pack(output, config):
    rows = {}
    for item in make_schedule(config):
        folder = output / 'runs' / item['run_id']
        path = folder / 'result.json'
        if not path.exists():
            raise ValueError('All 48 primary runs must be recorded before blind packing')
        value = json.loads(path.read_text())
        if value.get('workflow_state') != 'COMPLETE':
            raise ValueError('All 48 primary workflows must complete before blind packing')
        rows[item['run_id']] = value
    index_path = output / 'reviews/index.json'
    if index_path.exists():
        raise ValueError('Blind pack already exists; do not rewrite reviewed evidence')
    # Check before creating packs, so an unresolved identity never leaves half a pack.
    revisions = list(config['revisions'].values()) + ['552dd48', '7af1ba8']
    for row in make_schedule(config):
        source = output / 'runs' / row['run_id']
        roots = [str(output), str(ROOT)]
        if (source / 'context.json').exists():
            roots += list(json.loads((source / 'context.json').read_text()).values())
        inputs = [source / name for name in ('answer.md', 'file-evidence.json', 'application-evidence.json')]
        inputs += sorted((source / 'operator-evidence').glob('*.json'))
        inputs += [path for path, _, _ in review_documents(source)]
        for path in inputs:
            if path.exists():
                verify_blind_text(anonymize(path.read_text(), roots, revisions), revisions)
    rng = random.Random(config['seed'] + 1)
    scenarios = {s['id']: s for s in config['scenarios']}
    pairs = {}
    for row in make_schedule(config):
        pairs.setdefault((row['scenario_id'], row['repetition']), []).append(row)
    key, index = [], []
    for number, ((scenario_id, repetition), candidates) in enumerate(pairs.items(), 1):
        pair_id = f'pair-{number:02d}'
        candidates = list(candidates)
        rng.shuffle(candidates)
        folder = output / 'reviews/packs' / pair_id
        folder.mkdir(parents=True)
        mapping = {}
        prompt = scenarios[scenario_id]['request']
        if scenarios[scenario_id].get('follow_up'):
            prompt += '\n\n## Follow-up request\n\n' + scenarios[scenario_id]['follow_up']
        (folder / 'request.md').write_text(prompt)
        for label, candidate in zip(('A', 'B'), candidates):
            source = output / 'runs' / candidate['run_id']
            roots = [str(output), str(ROOT)]
            context_file = source / 'context.json'
            if context_file.exists():
                roots += list(json.loads(context_file.read_text()).values())
            answer = anonymize((source / 'answer.md').read_text(), roots,
                               list(config['revisions'].values()) + ['552dd48', '7af1ba8'])
            (folder / (label + '.md')).write_text(answer)
            write_json(folder / (label + '-activation.json'), review_activation(source, rows[candidate['run_id']]))
            evidence = source / 'file-evidence.json'
            if evidence.exists():
                clean = anonymize(blind_check_json(evidence.read_text()), roots, list(config['revisions'].values()))
                (folder / (label + '-checks.json')).write_text(clean)
            application = source / 'application-evidence.json'
            if application.exists():
                clean = anonymize(blind_check_json(application.read_text(), operator=True), roots, list(config['revisions'].values()))
                (folder / (label + '-application-checks.json')).write_text(clean)
            for check in sorted((source / 'operator-evidence').glob('*.json')):
                if check.is_symlink():
                    raise ValueError('Operator evidence must be a local JSON file')
                clean = anonymize(blind_check_json(check.read_text(), operator=True), roots, list(config['revisions'].values()))
                (folder / (label + '-operator-' + check.name)).write_text(clean)
            snapshots = []
            for snapshot, relative, kind in review_documents(source):
                name = label + f'-source-{len(snapshots)+1:03}' + snapshot.suffix.lower()
                raw = snapshot.read_text()
                if kind == 'worker_report' and snapshot.suffix.lower() == '.json':
                    raw = blind_check_json(raw)
                clean = anonymize(raw, roots,
                                  list(config['revisions'].values()) + ['552dd48', '7af1ba8'])
                (folder / name).write_text(clean)
                position = anonymize(str(relative), roots, []).replace('0.1.3', '[candidate]').replace('0.2.0', '[candidate]')
                snapshots.append({'source_position': position, 'kind': kind,
                                  'original_sha256': sha256(snapshot), 'review_file': name,
                                  'review_copy_sha256': sha256(folder / name),
                                  'transformation': 'Trial paths/candidate identity redacted; execution metrics redacted in QA JSON'})
            write_json(folder / (label + '-sources.json'), snapshots)
            # Native packages contain identifying metadata. Reviewers receive checked renders only.
            for image in sorted(source.glob('application/*')):
                if image.suffix.lower() not in {'.png', '.jpg', '.jpeg'}:
                    continue
                shutil.copyfile(image, folder / (label + '-' + image.name))
            mapping[label] = {'arm': candidate['arm'], 'run_id': candidate['run_id']}
        key.append({'pair_id': pair_id, 'scenario_id': scenario_id,
                    'repetition': repetition, 'mapping': mapping})
        index.append({'pair_id': pair_id, 'scenario_id': scenario_id,
                      'request_sha256': sha256(folder / 'request.md'),
                      'answer_sha256': {label: sha256(folder / (label + '.md')) for label in ('A', 'B')}})
    private = output / 'private/version-key.json'
    write_json(private, {'pairs': key})
    private.chmod(0o600)
    write_json(index_path, {'pairs': index})
    samples = []
    for scenario_id in scenarios:
        samples.append(rng.choice([p for p in index if p['scenario_id'] == scenario_id]))
    write_json(output / 'reviews/human-sample.json', {'pairs': samples, 'status': 'PENDING_HUMAN_REVIEW'})
    rubric = freeze_rubric(output)
    (output / 'reviews/rubric.md').write_text(rubric)
    for pair in index:
        pair['input_sha256'] = review_inputs(output / 'reviews/packs' / pair['pair_id'])
    write_json(index_path, {'pairs': index})
    write_json(output / 'reviews/human-sample.json', {'pairs': samples, 'status': 'PENDING_HUMAN_REVIEW'})
    write_json(output / 'private/conclusion-inputs.json', conclusion_inputs(output))
    print(json.dumps({'pairs': 24, 'human_sample': 8, 'version_key': 'SEALED'}))
    return 0


def judge_campaign(args, config):
    """One fresh, candidate-free CLI context for each blinded pair."""
    output = args.output.resolve()
    index_path = output / 'reviews/index.json'
    if not index_path.exists():
        build_review_pack(output, config)
    index = json.loads(index_path.read_text())['pairs']
    if len(index) != 24:
        raise ValueError('Expected 24 frozen blind pairs')
    for pair in index:
        pair_id = pair['pair_id']
        source = output / 'reviews/packs' / pair_id
        if review_inputs(source) != pair['input_sha256']:
            raise ValueError('Blind review input hash changed')
        target = output / 'reviews/agent' / (pair_id + '.json')
        if target.exists():
            value = json.loads(target.read_text())
            if not valid_review(value) or value.get('input_sha256') != pair['input_sha256']:
                raise ValueError('Existing review is invalid or bound to different evidence')
            continue
        logs = output / 'reviews/raw' / pair_id
        if logs.exists():
            raise ValueError('An unfinished judge attempt exists; preserve it and review before retrying')
        trial = Path(tempfile.mkdtemp(prefix='oci-blind-review-')).resolve()
        workspace, profile = trial / 'workspace', trial / 'profile'
        workspace.mkdir()
        (trial / 'tmp').mkdir()
        logs.mkdir(parents=True)
        try:
            prepare_profile(profile, getattr(args, 'auth_source', Path.home() / '.codex'))
            shutil.copytree(source, workspace / 'inputs')
            shutil.copyfile(output / 'reviews/rubric.md', workspace / 'inputs/rubric.md')
            environment = dict(os.environ, CODEX_HOME=str(profile), TMPDIR=str(trial / 'tmp'),
                               PYTHONDONTWRITEBYTECODE='1')
            environment['PATH'] = str(Path(sys.executable).parent) + os.pathsep + environment.get('PATH', '')
            context = {'trial': trial, 'workspace': workspace, 'profile': profile,
                       'env': environment, 'codex': args.codex}
            native_permissions(context, output)
            catalog = _capture([args.codex, '--no-daemon', 'debug', 'prompt-input'],
                               workspace, environment, logs / 'catalog')
            if re.search(r'[a-z][a-z0-9-]+/SKILL\.md', catalog):
                raise ValueError('Blind reviewer discovered skills; candidate isolation failed')
            confinement_checks(context, output, logs)
            prompt = ('Independently assess this one anonymous architecture pair. Read inputs/request.md, '
                      'inputs/rubric.md and both answers, checks and available images. Use only these inputs. '
                      'The A/B-sources.json indexes map saved primary snapshots and asset provenance to '
                      'their neutral review filenames and hashes; inspect relevant sections when supplied. '
                      'No candidate skills, prior reviews or version identities are available. Do not infer a '
                      'version or fetch new sources. Judge decisions and consequences, not headings. '
                      'Distinguish architecture errors from infrastructure and verification gaps. '
                      'The nine shared QA dimensions are ' + ', '.join(QA) + '. The three design dimensions '
                      'are ' + ', '.join(DESIGN_QA) + '; report these separately and do not penalize a candidate '
                      'for a new instruction alone. Parser success cannot prove opening, visual quality or '
                      'editability. For concrete service claims check primary-source content, section, access '
                      'date and scope; inaccessible evidence stays unverified. Return only one JSON object: '
                      '{"candidates":{"A":{"task_status":"PASS|FAIL","mandatory_checks":'
                      '[{"requirement":"...","status":"PASS|FAIL","evidence":"input filename and exact passage"}],'
                      '"qa":{"each of all twelve dimensions":{"status":"PASS|FAIL|NOT_VERIFIED|NOT_APPLICABLE",'
                      '"method":"...","evidence":"..."}}},"B":{"same fields":"..."}},'
                      '"findings":[{"candidate":"A|B","severity":"Critical|Important|Minor",'
                      '"consequence":"concrete consequence","evidence":"filename and passage"}],'
                      '"preference":"A|B|TIE","rationale":"..."}. '
                      'NOT_APPLICABLE is only for irrelevant dimensions. Findings can be empty. '
                      'Prioritize critical/material errors, then acceptance, then preference. '
                      'No combined numeric score. Do not repair candidate artifacts.')
            result = inference(args, config, context, prompt, logs / 'inference', config['timeout_seconds'])
            if result['status'] != 'PASS':
                raise ValueError('Blind reviewer failed or timed out; raw evidence is retained')
            answer = (logs / 'inference/answer.md').read_text().strip()
            if answer.startswith('```'):
                answer = re.sub(r'^```(?:json)?\s*|\s*```$', '', answer)
            value = json.loads(answer)
            if not valid_review(value):
                raise ValueError('Blind review lacks mandatory checks or full QA evidence')
            value.update(pair_id=pair_id, reviewer_kind='agent', input_sha256=pair['input_sha256'])
            write_json(target, value)
            write_json(logs / 'workspace-manifest.json', collect_workspace(workspace, logs / 'workspace-evidence'))
            print(json.dumps({'reviewed': pair_id}), flush=True)
        finally:
            (profile / 'auth.json').unlink(missing_ok=True)
    required = json.loads((output / 'reviews/human-sample.json').read_text())['pairs']
    required_ids = {r['pair_id'] for r in required}
    critical = []
    for pair in index:
        value = json.loads((output / 'reviews/agent' / (pair['pair_id'] + '.json')).read_text())
        if any(f['severity'] == 'Critical' for f in value['findings']):
            critical.append(pair['pair_id'])
            if pair['pair_id'] not in required_ids:
                required.append(pair)
    write_json(output / 'reviews/human-required.json', {'pairs': required, 'critical_pairs': critical,
                                                       'status': 'PENDING_HUMAN_REVIEW'})
    for pair in required:
        path = output / 'reviews/human-templates' / (pair['pair_id'] + '.json')
        if not path.exists():
            write_json(path, {'reviewer_kind': 'human', 'pair_id': pair['pair_id'],
                              'input_sha256': pair['input_sha256'], 'candidates': {},
                              'findings': [], 'preference': 'PENDING', 'rationale': ''})
    return 0


def lock_reviews(output):
    artifacts = {str(p.relative_to(output)): sha256(p) for kind in ('agent', 'human')
                 for p in sorted((output / 'reviews' / kind).glob('*.json'))}
    counts = Counter(json.loads((output / p).read_text()).get('reviewer_kind') for p in artifacts)
    lock = {'agent_reviews': counts['agent'], 'human_reviews': counts['human'],
            'critical_reviews_pending': 0, 'locked': True, 'artifact_sha256': artifacts,
            'conclusion_sha256': sha256(output / 'private/conclusion-inputs.json')}
    if not verified_review_lock(output, lock):
        raise ValueError('Review lock refused: incomplete, duplicated, changed or invalid review evidence')
    write_json(output / 'reviews/lock.json', lock)
    print(json.dumps({'review_status': 'LOCKED', 'unblinding_allowed': True}))
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['preflight', 'run', 'review-pack', 'report'])
    parser.add_argument('--config', type=Path, default=ROOT / 'tests/benchmark/campaign.json')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--toolkits', type=Path)
    parser.add_argument('--codex', default=shutil.which('codex') or 'codex')
    parser.add_argument('--reprocess-pilots', action='store_true',
                        help='Reinterpret existing pilot logs without new model calls')
    parser.add_argument('--judge', action='store_true', help='Run one isolated blind reviewer per frozen pair')
    parser.add_argument('--lock-reviews', action='store_true', help='Lock completed agent and actual human review evidence')
    args = parser.parse_args(argv)
    if (args.judge or args.lock_reviews) and args.command != 'review-pack':
        parser.error('--judge and --lock-reviews only apply to review-pack')
    if args.judge and args.lock_reviews:
        parser.error('Judge and lock are separate steps')
    config = load_config(args.config)
    output = args.output.resolve()
    if output.is_relative_to(ROOT.resolve()):
        raise ValueError('Evidence must be outside the distributed plugin')
    output.mkdir(parents=True, exist_ok=True)
    if args.command == 'report':
        result = campaign_report(output, config)
        print(json.dumps({k: result[k] for k in ('primary_completed', 'conclusion_status', 'unblinded')}))
        return 0
    return execute_command(args, config)


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
