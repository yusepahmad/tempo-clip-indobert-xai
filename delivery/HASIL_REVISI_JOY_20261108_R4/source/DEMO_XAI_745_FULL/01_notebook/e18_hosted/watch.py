"""Wait for the original worker; audit once only after complete740; never launch inference."""
import argparse
from datetime import datetime, timezone
import fcntl
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[2]
parser=argparse.ArgumentParser();parser.add_argument('--pid',type=int,required=True)
parser.add_argument('--starttime',required=True);args=parser.parse_args()
out=ROOT/'04_hasil_eksperimen/e18_hosted'
lock=(out/'watch.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
state_path=out/'watch_state.json'
assert not state_path.exists(), 'Existing dispatch state requires inspection; no automatic redispatch'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
source=Path(__file__).parent
hashes={name:sha(source/name) for name in ('run.py','quota.py','verify.py','parse.py','evaluate_parsed.py','watch.py')}
state=dict(phase='watching',worker_pid=args.pid,worker_starttime=args.starttime,source_sha256=hashes)
def save():
    state['updated_at']=datetime.now(timezone.utc).isoformat()
    temp=state_path.with_suffix('.tmp');temp.write_text(json.dumps(state,indent=2)+'\n');temp.replace(state_path)
def original_alive():
    try:
        stat=Path(f'/proc/{args.pid}/stat').read_text().rsplit(')',1)[1].split()
        # Fields after comm begin at field3; starttime is field22.
        return stat[19]==args.starttime and stat[0]!='Z'
    except FileNotFoundError:
        return False
save()
while original_alive():
    time.sleep(45)
    save()
try:
    for name,digest in hashes.items():assert sha(source/name)==digest, 'Source changed while waiting'
    progress=json.loads((out/'progress.json').read_text())
    assert progress['status']=='predictions_complete_pending_audit' and progress['completed']==740
    state['phase']='auditing_strict';save()
    with (ROOT/'04_hasil_eksperimen/e18_strict_audit.log').open('w') as log:
        subprocess.run([sys.executable,str(source/'verify.py')],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,check=True)
    state['phase']='auditing_parsed';save()
    with (ROOT/'04_hasil_eksperimen/e18_parsed_audit.log').open('w') as log:
        subprocess.run([sys.executable,str(source/'evaluate_parsed.py')],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,check=True)
    state['phase']='verified_pending_root_copy_audit';save()
except Exception as error:
    state.update(phase='halted_needs_root_audit',error_type=type(error).__name__)
    save()
    raise
