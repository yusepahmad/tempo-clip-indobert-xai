"""Dispatch E15 once into a free slot while E12 new submissions are explicitly held."""
import ast
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time
from monitor_e12 import ROOT, cli, quota, status

OUT = ROOT / '04_hasil_eksperimen/e15_monitor'
SLUG = 'research-account/tempo-e15-vlm-features'
LIMIT = 3600
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()

def save(state):
    state['updated_at'] = datetime.now(timezone.utc).isoformat()
    temporary = OUT / 'state.tmp'
    temporary.write_text(json.dumps(state, indent=2) + '\n')
    temporary.replace(OUT / 'state.json')

def event(kind, **fields):
    row = {'at': datetime.now(timezone.utc).isoformat(), 'event': kind, **fields}
    with (OUT / 'events.jsonl').open('a') as f:
        f.write(json.dumps(row) + '\n')
    print(json.dumps(row), flush=True)

def launcher():
    folder = ROOT / '01_notebook/kaggle_e15/full'
    meta = json.loads((folder / 'kernel-metadata.json').read_text())
    assert meta['id'] == SLUG and meta['is_private'] and meta['enable_gpu']
    expected = {'e15_worker.py': ('worker.py', '30a2c29b499c75879192c1dcc0b0b47570fb293d3dd12718f449984b06cda4cd'),
                'e15_prompt.py': ('prompt.py', 'a1731aad122005377bfc5d6801cb70f3ab18fb89129d2ba57d2ab50e5e238cbf')}
    embedded = {}
    timeouts = []
    for node in ast.walk(ast.parse((folder / 'launch.py').read_text())):
        if not isinstance(node, ast.Call):
            continue
        for kw in node.keywords:
            if kw.arg == 'timeout':
                timeouts.append(ast.literal_eval(kw.value))
        if isinstance(node.func, ast.Attribute) and node.func.attr == 'write_text':
            name = Path(ast.literal_eval(node.func.value.args[0])).name
            embedded[name] = hashlib.sha256(ast.literal_eval(node.args[0]).encode()).hexdigest()
    assert sorted(timeouts) == [600, 3000] and set(embedded) == set(expected)
    for name, (local, digest) in expected.items():
        assert embedded[name] == sha(folder.parent / local) == digest
    return folder

def check_hold():
    base = ROOT / '04_hasil_eksperimen/e12_monitor'
    state = json.loads((base / 'state.json').read_text())
    assert state['phase'] == 'watching' and state['hold_new_submissions'] is True
    assert state['folds']['5']['phase'] == 'pending'
    pid = state['monitor_pid']
    proc = Path(f'/proc/{pid}')
    assert proc.exists() and proc.joinpath('stat').read_text().rsplit(') ', 1)[1].split()[0] != 'Z'
    command = proc.joinpath('cmdline').read_bytes()
    assert b'monitor_e12.py' in command and b'--hold-new-submissions' in command
    with (base / 'monitor.lock').open('r') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return
        raise RuntimeError('E12 monitor lock is not held')

def main():
    folder = launcher()
    OUT.mkdir(exist_ok=True)
    lock = (OUT / 'monitor.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    state = json.loads((OUT / 'state.json').read_text()) if (OUT / 'state.json').exists() else {'phase': 'pending'}
    assert state['phase'] in ('pending', 'submitted'), 'Root audit required before resuming this state'
    state['monitor_pid'] = os.getpid()
    save(state)
    event('started', pid=os.getpid())
    while True:
        try:
            if state['phase'] == 'pending':
                check_hold()
                statuses = {str(k): status(k) for k in (3, 4)}
                assert all(value in ('RUNNING', 'QUEUED', 'COMPLETE') for value in statuses.values())
                state['e12_statuses'] = statuses
                active = sum(value in ('RUNNING', 'QUEUED') for value in statuses.values())
                if active < 2:
                    q = quota()
                    state['quota'] = q
                    if q['available_seconds'] - active * 28800 >= LIMIT:
                        # Auth works for this owner's active jobs. Refuse to overwrite an accessible E15 kernel.
                        existing = cli('kernels', 'status', SLUG)
                        if existing.returncode == 0 or 'Cannot access kernel' not in existing.stdout + existing.stderr:
                            state['phase'] = 'needs_root_audit'
                            save(state)
                            event('existing_or_uncertain_e15_kernel');return
                        check_hold()
                        state.update(phase='submitting', launcher_sha256=sha(folder / 'launch.py'))
                        (OUT / 'submitted.py').write_text((folder / 'launch.py').read_text())
                        save(state)
                        result = cli('kernels', 'push', '-p', str(folder), '--accelerator', 'NvidiaTeslaT4',
                                     '--timeout', str(LIMIT))
                        (OUT / 'push.log').write_text(result.stdout + result.stderr)
                        if result.returncode != 0 or 'successfully pushed' not in result.stdout:
                            state['phase'] = 'needs_root_audit';save(state)
                            event('uncertain_submission');return
                        state['phase'] = 'submitted';save(state)
                        event('submitted', quota=q, e12_statuses=statuses)
                save(state)
            elif state['phase'] == 'submitted':
                result = cli('kernels', 'status', SLUG)
                if result.returncode:
                    raise RuntimeError('E15 status observation failed')
                match = re.search(r'KernelWorkerStatus\.([A-Z_]+)', result.stdout)
                if not match:
                    raise RuntimeError('Unrecognized E15 status')
                state['status'] = match.group(1);save(state)
                if state['status'] == 'COMPLETE':
                    target = ROOT / '04_hasil_eksperimen/e15_vlm_features'
                    result = cli('kernels', 'output', SLUG, '-p', str(target),
                                 '--file-pattern', r'^e15_vlm_features/.*\.(json|jsonl|npz)$', timeout=600)
                    if result.returncode:
                        raise RuntimeError('Complete E15 download not yet available')
                    feature = target / 'e15_vlm_features'
                    audit = subprocess.run([str(ROOT / 'venv/bin/python'),
                                            str(ROOT / '01_notebook/kaggle_e15/verify_features.py'), str(feature)],
                                           capture_output=True, text=True, timeout=300)
                    (OUT / 'feature_audit.log').write_text(audit.stdout + audit.stderr)
                    state['phase'] = 'features_verified_ready_for_evaluation' if audit.returncode == 0 else 'needs_root_audit'
                    save(state);event('feature_audited', exit_code=audit.returncode);return
                if state['status'] not in ('RUNNING', 'QUEUED'):
                    state['phase'] = 'needs_root_audit';save(state)
                    event('unexpected_terminal_status', status=state['status']);return
        except Exception as error:
            event('observation_error', error=str(error))
            if state['phase'] == 'submitting':
                state['phase'] = 'needs_root_audit';save(state);return
        time.sleep(45)

if __name__ == '__main__':
    main()
