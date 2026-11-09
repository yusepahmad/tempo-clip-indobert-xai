"""Wait for verified cached E18 and completed E15; dispatch CPU E20 once."""
import argparse
from datetime import datetime, timezone
import fcntl
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / '01_notebook'
RESULT = ROOT / '04_hasil_eksperimen'
OUT = RESULT / 'e20_dispatch'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
NAMES = ('watch_e20.py', 'e20_zero_shot_fusion.py', 'e20_zero_shot_fusion_verify.py',
         'e18_hosted/watch_final.py', 'e18_hosted/parse_v2.py',
         'e18_hosted/evaluate_parsed_v2.py', 'e18_hosted/evaluate_valid.py',
         'e18_hosted/valid_labels.py', 'kaggle_e15/verify.py')

def alive(pid, starttime):
    try:
        fields = Path(f'/proc/{pid}/stat').read_text().rsplit(')', 1)[1].split()
        return fields[19] == starttime and fields[0] != 'Z'
    except FileNotFoundError:
        return False

def gate():
    e18 = RESULT / 'e18_hosted'
    state = json.loads((e18 / 'final_watch_state.json').read_text())
    assert state['phase'] == 'verified_pending_root_copy_audit'
    final = json.loads((e18 / 'valid/verification.json').read_text())
    assert final['status'] == 'verified' and final['samples'] == 740
    assert final['verifier_sha256'] == sha(SOURCE / 'e18_hosted/evaluate_valid.py')
    assert final['fallback_source_sha256'] == sha(SOURCE / 'e18_hosted/valid_labels.py')
    for name, digest in final['sha256'].items():
        assert sha(e18 / 'valid' / name) == digest
    e15 = RESULT / 'e15_nested'
    verified = json.loads((e15 / 'verification.json').read_text())
    assert verified['status'] == 'verified' and verified['samples'] == 740
    assert verified['verifier_sha256'] == sha(SOURCE / 'kaggle_e15/verify.py')
    for name, digest in verified['sha256'].items():
        assert sha(e15 / name) == digest
    assert set(final['routes']) == {'strict', 'v1', 'v2'}
    return any(float(record['macro_f1']) >= .70 for record in final['routes'].values())

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--audit-pid', type=int, required=True)
    parser.add_argument('--audit-starttime', required=True)
    args = parser.parse_args()
    OUT.mkdir(exist_ok=True)
    lock = (OUT / 'dispatch.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    path = OUT / 'state.json'
    assert not path.exists(), 'Prior dispatch needs root inspection; no automatic retry'
    assert not (RESULT / 'e20_zero_shot_fusion').exists()
    hashes = {name: sha(SOURCE / name) for name in NAMES}
    state = dict(phase='waiting_final_e18_audit', audit_pid=args.audit_pid,
                 audit_starttime=args.audit_starttime, source_sha256=hashes)
    def save():
        state['updated_at'] = datetime.now(timezone.utc).isoformat()
        temp = path.with_suffix('.tmp')
        temp.write_text(json.dumps(state, indent=2) + '\n'); temp.replace(path)
    save()
    try:
        while alive(args.audit_pid, args.audit_starttime):
            time.sleep(45); save()
        for name, digest in hashes.items():
            assert sha(SOURCE / name) == digest, 'Frozen source changed'
        if gate():
            state['phase'] = 'e18_target_candidate_pending_root_audit'; save(); return
        for phase, script in (('training', 'e20_zero_shot_fusion.py'),
                              ('auditing', 'e20_zero_shot_fusion_verify.py')):
            state['phase'] = phase; save()
            with (OUT / f'{phase}.log').open('x') as log:
                subprocess.run([sys.executable, str(SOURCE / script)], cwd=ROOT,
                               stdout=log, stderr=subprocess.STDOUT, check=True)
        verified = json.loads((RESULT / 'e20_zero_shot_fusion/verification.json').read_text())
        assert verified['status'] == 'verified' and verified['samples'] == 740
        state['phase'] = 'verified_pending_root_copy_audit'; save()
    except Exception as error:
        state.update(phase='halted_needs_root_audit', error_type=type(error).__name__)
        save(); raise

if __name__ == '__main__':
    main()
