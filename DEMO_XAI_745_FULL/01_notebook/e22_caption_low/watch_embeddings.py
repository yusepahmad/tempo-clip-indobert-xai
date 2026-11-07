"""Dispatch CPU embedding once, after the original caption worker and auditor finish."""
import argparse
from datetime import datetime, timezone
import fcntl
import json
from pathlib import Path
import subprocess
import sys
import time
from embed import ROOT, OUT as EMB, inputs, sha, save

OUT = ROOT / '04_hasil_eksperimen/e22_embedding_dispatch'
SOURCE = Path(__file__).resolve().parent
NAMES = ['watch_embeddings.py', 'embed.py', 'verify_embeddings.py', 'run.py', 'verify.py']


def alive(pid, starttime, proc_root=Path('/proc')):
    try:
        fields = (proc_root / str(pid) / 'stat').read_text().rsplit(')', 1)[1].split()
        return fields[19] == str(starttime) and fields[0] != 'Z'
    except FileNotFoundError:
        return False


def gate(hashes):
    for name, digest in hashes.items():
        assert sha(SOURCE / name) == digest, 'Pinned source changed; root audit required'
    df, texts, signature = inputs()
    assert len(df) == 740 and all(len(values) == 740 for values in texts.values())
    prepared = json.loads((EMB / 'preparation.json').read_text())
    assert prepared['status'] == 'model_preparation_verified'
    assert prepared['worker_sha256'] == hashes['embed.py']
    assert not (EMB / 'meta.json').exists() and not (EMB / 'embeddings.npz').exists()
    assert not (EMB / 'protocol.json').exists(), 'Existing full run needs audit; no duplicate dispatch'
    return signature


def main(pid, starttime, session):
    assert alive(pid, starttime), 'Original worker must be live when arming'
    OUT.mkdir(exist_ok=True)
    lock = (OUT / 'run.lock').open('a'); fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    path = OUT / 'state.json'
    assert not path.exists(), 'Prior dispatch needs root audit; no automatic retry'
    hashes = {name: sha(SOURCE / name) for name in NAMES}
    state = dict(phase='waiting_original_caption_worker', caption_pid=pid,
                 caption_starttime=str(starttime), caption_session=session, source_sha256=hashes)
    def update():
        state['updated_at'] = datetime.now(timezone.utc).isoformat()
        save(path, state)
    update()
    try:
        while alive(pid, starttime):
            time.sleep(45); update()
        state['phase'] = 'waiting_original_caption_auditor'; update()
        while subprocess.run(['tmux', 'has-session', '-t', session],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0:
            time.sleep(45); update()
        state['input_signature'] = gate(hashes)
        # Persistent commit precedes child launch; any uncertain launch requires root inspection.
        for phase, script in [('embedding', 'embed.py'), ('auditing_embeddings', 'verify_embeddings.py')]:
            for name, digest in hashes.items():
                assert sha(SOURCE / name) == digest
            state['phase'] = phase + '_launch_committed'; update()
            with (OUT / f'{phase}.log').open('x') as log:
                child = subprocess.Popen([sys.executable, '-u', str(SOURCE / script)], cwd=ROOT,
                                         stdout=log, stderr=subprocess.STDOUT)
                state.update(phase=phase, child_pid=child.pid)
                fields = Path(f'/proc/{child.pid}/stat').read_text().rsplit(')', 1)[1].split()
                state['child_starttime'] = fields[19]; update()
                while child.poll() is None:
                    time.sleep(45); update()
                assert child.returncode == 0, 'Child failed; inspect retained log/artifacts before retry'
        verified = json.loads((EMB / 'verification.json').read_text())
        assert verified['status'] == 'verified' and verified['samples'] == 740
        assert verified['verifier_sha256'] == hashes['verify_embeddings.py']
        for name, digest in verified['sha256'].items():
            assert sha(EMB / name) == digest
        state.update(phase='verified_pending_root_copy_audit', verification_sha256=sha(EMB / 'verification.json'))
        update()
    except Exception as error:
        state.update(phase='halted_needs_root_audit', error_type=type(error).__name__)
        update(); raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--pid', type=int, required=True)
    parser.add_argument('--starttime', required=True)
    parser.add_argument('--session', default='tempo-e22-low')
    args = parser.parse_args()
    main(args.pid, args.starttime, args.session)
