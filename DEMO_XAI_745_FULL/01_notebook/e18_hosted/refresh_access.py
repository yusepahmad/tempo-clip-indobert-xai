"""Keep short-lived official Kaggle access valid for one original worker; never print keys."""
import argparse
from datetime import datetime,timezone
import fcntl
import json
import os
from pathlib import Path
import time
from kaggle.api.kaggle_api_extended import KaggleApi

parser=argparse.ArgumentParser();parser.add_argument('--pid',type=int,required=True)
parser.add_argument('--starttime',required=True);args=parser.parse_args()
secret=Path('/home/research-user/workspace/learn/.kaggle/e18_proxy.env')
lock=secret.with_suffix('.refresh.lock').open('a');os.chmod(lock.name,0o600)
fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
def alive():
    try:
        stat=Path(f'/proc/{args.pid}/stat').read_text().rsplit(')',1)[1].split()
        return stat[19]==args.starttime and stat[0]!='Z'
    except FileNotFoundError:return False
assert secret.stat().st_mode&0o777==0o600
renewals=0
attempts=0
next_attempt=0.0
def expiry_advanced(old,new):
    assert new>=old, 'Auth returned an earlier expiry; inspect before replacement'
    return new>old
print(json.dumps(dict(status='watching_original_worker',pid=args.pid)),flush=True)
while alive():
    config=dict(line.split('=',1) for line in secret.read_text().splitlines())
    expiry=datetime.fromisoformat(config['MODEL_PROXY_EXPIRY_TIME'].replace('Z','+00:00'))
    remaining=(expiry-datetime.now(timezone.utc)).total_seconds()
    if remaining<=240:
        print(json.dumps(dict(status='access_near_expiry_needs_root_audit',renewals=renewals,attempts=attempts)),flush=True)
        raise SystemExit(1)
    if remaining<1800 and time.monotonic()>=next_attempt:
        assert renewals<3, 'Renewal limit reached; inspect worker manually'
        assert attempts<12, 'Auth attempt limit reached; inspect worker manually'
        attempts+=1
        next_attempt=time.monotonic()+300
        try:
            api=KaggleApi();api.authenticate()
            fresh=api._fetch_model_proxy_env(source='auth')
        except Exception as error:
            print(json.dumps(dict(status='auth_failed_needs_root_audit',error_type=type(error).__name__)),flush=True)
            raise SystemExit(1)
        assert fresh['MODEL_PROXY_URL']==config['MODEL_PROXY_URL']
        assert fresh['MODEL_PROXY_API_KEY'] and fresh['MODEL_PROXY_EXPIRY_TIME']
        new_expiry=datetime.fromisoformat(fresh['MODEL_PROXY_EXPIRY_TIME'].replace('Z','+00:00'))
        if not expiry_advanced(expiry,new_expiry):
            print(json.dumps(dict(status='access_not_extended',attempts=attempts,
                                  expiry=fresh['MODEL_PROXY_EXPIRY_TIME'])),flush=True)
            time.sleep(45)
            continue
        temporary=secret.with_suffix('.refresh.tmp')
        fd=os.open(temporary,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
        with os.fdopen(fd,'w') as f:
            for key,value in fresh.items():f.write(key+'='+value+'\n')
            f.flush();os.fsync(f.fileno())
        temporary.replace(secret);assert secret.stat().st_mode&0o777==0o600
        renewals+=1
        print(json.dumps(dict(status='access_refreshed',renewals=renewals,expiry=fresh['MODEL_PROXY_EXPIRY_TIME'])),flush=True)
    time.sleep(45)
print(json.dumps(dict(status='original_worker_terminal',renewals=renewals)),flush=True)
