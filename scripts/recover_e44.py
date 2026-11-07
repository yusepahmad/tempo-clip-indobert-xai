"""Observe one authorized job, recover and audit; never launch or restart kernels."""
from pathlib import Path
import subprocess,sys,time,json,hashlib,shutil,datetime
ROOT=Path(__file__).resolve().parents[1]
REF='yusepmuhamadzazuli/tempo-e44-focal-tail-full'
KAGGLE='/home/yusep/.local/bin/kaggle'
SERVER='yusep@10.12.1.31'
REMOTE='/home/yusep/workspace/learn/DEMO_XAI_745_FULL'
REL='04_hasil_eksperimen/e44_focal_tail'
SOURCE='01_notebook/e44_focal_tail'
RECOVERY=ROOT/'docs/server-recovery/2026-10-13/e44_full'
def run(args,capture=False):
    return subprocess.run(['rtk','proxy',*args],cwd=ROOT,check=True,text=True,capture_output=capture)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    deadline=time.monotonic()+1800;last=None
    while True:
        assert time.monotonic()<deadline,'Observation timeout; job state not declared terminal; no restart'
        try:status=run([KAGGLE,'kernels','status',REF],True).stdout.strip()
        except subprocess.CalledProcessError as error:
            print('Status observation error; rechecking same handle',error.returncode,flush=True);time.sleep(30);continue
        if status!=last:print(datetime.datetime.now(datetime.timezone.utc).isoformat(),status,flush=True);last=status
        if 'KernelWorkerStatus.COMPLETE' in status:break
        assert not any(s in status for s in ['KernelWorkerStatus.ERROR','KernelWorkerStatus.CANCELLED','KernelWorkerStatus.CANCELED']),status
        time.sleep(30)
    run([KAGGLE,'kernels','output',REF,'-p',str(RECOVERY),'--file-pattern',r'.*(json|csv|pt|log)$'])
    raw=RECOVERY/'e44_focal_tail';out=ROOT/'DEMO_XAI_745_FULL'/REL
    assert not (out/'result.json').exists(),'Completed result already exists; inspect instead of overwriting'
    for k in range(1,6):assert sha(raw/f'fold{k}.pt')==json.loads((raw/f'fold{k}.json').read_text())['checkpoint_sha256']
    shutil.copytree(raw,out,dirs_exist_ok=True)
    run(['rsync','-a',str(out)+'/',f'{SERVER}:{REMOTE}/{REL}/'])
    command=f'cd {REMOTE} && venv/bin/python {SOURCE}/verify_result.py 04_hasil_eksperimen/e41_cached_tail/cache {REL}'
    run(['ssh',SERVER,command])
    run(['rsync','-a',f'{SERVER}:{REMOTE}/{REL}/',str(out)+'/'])
    run([sys.executable,str(ROOT/'DEMO_XAI_745_FULL'/SOURCE/'root_verify.py'),str(out)])
    assert json.loads((out/'verification.json').read_text())['status']=='passed'
    assert json.loads((out/'root_verification.json').read_text())['status']=='passed'
    run(['scp',str(out/'root_verification.json'),f'{SERVER}:{REMOTE}/{REL}/'])
    result=json.loads((out/'result.json').read_text());assert result['target_reached']==all(v['macro_f1']>=.7 for v in result['metrics'].values())
    print('RECOVERY AND AUDIT PASSED',json.dumps(result['metrics']),flush=True)
    print('No new kernel launched; delivery unchanged; quality threshold alone does not complete delivery/XAI gates.',flush=True)
if __name__=='__main__':main()
