"""Wait for one identified E14 worker, then audit once; never restart training."""
import argparse
import fcntl
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--worker-pid', type=int, required=True)
args = parser.parse_args()
out = ROOT / '04_hasil_eksperimen/e14_weighted_fusion'
monitor = ROOT / '04_hasil_eksperimen/e14_monitor'
monitor.mkdir(exist_ok=True)
lock = (monitor / 'monitor.lock').open('a')
fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)

def process():
    try:
        stat = Path(f'/proc/{args.worker_pid}/stat').read_text().rsplit(') ', 1)[1].split()
        return stat[0], stat[19]
    except FileNotFoundError:
        return None

def save(phase, **extra):
    value = {'phase': phase, 'worker_pid': args.worker_pid,
             'updated_at': datetime.now(timezone.utc).isoformat(), **extra}
    temp = monitor / 'state.json.tmp'
    temp.write_text(json.dumps(value, indent=2) + '\n')
    temp.replace(monitor / 'state.json')
    print(json.dumps(value), flush=True)

initial = process()
if initial is None or initial[0] == 'Z':
    save('needs_root_audit', reason='Expected live worker missing at monitor adoption')
    sys.exit(1)
command = Path(f'/proc/{args.worker_pid}/cmdline').read_bytes().replace(b'\0', b' ')
assert b'01_notebook/e14_weighted_fusion.py' in command
save('watching', worker_start_ticks=initial[1])
while True:
    current = process()
    if current is not None and current[1] != initial[1]:
        save('needs_root_audit', reason='Worker PID reused; no audit automatically launched')
        sys.exit(1)
    if current is None or current[0] == 'Z':
        break
    time.sleep(45)
required = ['protocol.json', 'weighted.json', 'weighted_oof.csv',
            'nested_selected.json', 'nested_selected_oof.csv'] + [f'fold_{k}.json' for k in range(1, 6)]
missing = [name for name in required if not (out / name).is_file()]
if missing:
    save('needs_root_audit', reason='Worker terminal without complete outputs', missing=missing)
    sys.exit(1)
save('auditing')
with (monitor / 'audit.log').open('w') as log:
    result = subprocess.run([sys.executable, '-u', str(ROOT / '01_notebook/e14_weighted_fusion_verify.py')],
                            cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
if result.returncode != 0 or not (out / 'verification.json').is_file():
    save('needs_root_audit', reason='Auditor failed; inspect audit.log', returncode=result.returncode)
    sys.exit(1)
verification = json.loads((out / 'verification.json').read_text())
assert verification['status'] == 'verified' and verification['samples'] == 740
save('verified_ready_for_root_copy_audit', scores=verification['scores'],
     verification_sha256=hashlib.sha256((out / 'verification.json').read_bytes()).hexdigest())
