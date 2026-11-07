"""Dispatch cached v2 and valid-seven-class evaluation once; never call model APIs."""
import argparse
from datetime import datetime, timezone
import fcntl
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
SOURCE = Path(__file__).parent
OUT = ROOT / '04_hasil_eksperimen/e18_hosted'
NAMES = ('watch.py', 'verify.py', 'run.py', 'parse.py', 'evaluate_parsed.py',
         'parse_v2.py', 'evaluate_parsed_v2.py', 'valid_labels.py', 'evaluate_valid.py', 'watch_final.py')
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()

def alive(pid, starttime):
    try:
        fields = Path(f'/proc/{pid}/stat').read_text().rsplit(')', 1)[1].split()
        return fields[19] == starttime and fields[0] != 'Z'
    except FileNotFoundError:
        return False

def gate():
    state = json.loads((OUT / 'watch_state.json').read_text())
    assert state['phase'] == 'verified_pending_root_copy_audit'
    assert not alive(state['worker_pid'], state['worker_starttime'])
    progress = json.loads((OUT / 'progress.json').read_text())
    assert progress['status'] == 'predictions_complete_pending_audit' and progress['completed'] == 740
    verified = json.loads((OUT / 'verification.json').read_text())
    assert verified['status'] == 'verified' and verified['samples'] == 740
    assert verified['verifier_sha256'] == sha(SOURCE / 'verify.py')
    for name, digest in verified['sha256'].items():
        assert sha(OUT / name) == digest
    parsed = json.loads((OUT / 'parsed/metrics.json').read_text())
    assert parsed['status'] == 'verified' and parsed['samples'] == 740
    assert parsed['parser_sha256'] == sha(SOURCE / 'parse.py')
    assert parsed['evaluator_sha256'] == sha(SOURCE / 'evaluate_parsed.py')
    assert parsed['strict_verification_sha256'] == sha(OUT / 'verification.json')
    assert parsed['oof_sha256'] == sha(OUT / 'parsed/oof.csv')

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--watcher-pid', type=int, required=True)
    parser.add_argument('--watcher-starttime', required=True)
    args = parser.parse_args()
    lock = (OUT / 'final_watch.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    path = OUT / 'final_watch_state.json'
    assert not path.exists(), 'Inspect prior dispatch state; no automatic retry'
    assert not (OUT / 'parsed_v2').exists() and not (OUT / 'valid').exists()
    hashes = {name: sha(SOURCE / name) for name in NAMES}
    state = dict(phase='watching_initial_auditor', watcher_pid=args.watcher_pid,
                 watcher_starttime=args.watcher_starttime, source_sha256=hashes)
    def save():
        state['updated_at'] = datetime.now(timezone.utc).isoformat()
        temp = path.with_suffix('.tmp')
        temp.write_text(json.dumps(state, indent=2) + '\n'); temp.replace(path)
    save()
    try:
        while alive(args.watcher_pid, args.watcher_starttime):
            time.sleep(45); save()
        for name, digest in hashes.items():
            assert sha(SOURCE / name) == digest, 'Frozen source changed'
        gate()
        for phase, script in (('auditing_v2', 'evaluate_parsed_v2.py'),
                              ('auditing_valid', 'evaluate_valid.py')):
            state['phase'] = phase; save()
            with (ROOT / '04_hasil_eksperimen' / f'e18_{phase}.log').open('x') as log:
                subprocess.run([sys.executable, str(SOURCE / script)], cwd=ROOT,
                               stdout=log, stderr=subprocess.STDOUT, check=True)
        final = json.loads((OUT / 'valid/verification.json').read_text())
        assert final['status'] == 'verified' and final['samples'] == 740
        for name, digest in final['sha256'].items():
            assert sha(OUT / 'valid' / name) == digest
        state['phase'] = 'verified_pending_root_copy_audit'; save()
    except Exception as error:
        state.update(phase='halted_needs_root_audit', error_type=type(error).__name__)
        save(); raise

if __name__ == '__main__':
    main()
