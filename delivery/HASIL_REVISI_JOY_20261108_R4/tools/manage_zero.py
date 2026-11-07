"""Versioned private zero-shot control jobs; full requires verified smoke."""
import argparse
import ast
from datetime import datetime,timezone
import json
from pathlib import Path
import re
import shutil
import subprocess
from evaluate import TASKS,sha,write_json

HERE=Path(__file__).resolve().parent;APP=HERE.parents[1];OUT=APP/'04_hasil_eksperimen/revisi_ii/qwen_zero_jobs'
WORKER=HERE/'qwen_zero_worker.py';REF='yusepmuhamadzazuli/tempo-revisi-ii-qwen-zero-'


def build(mode):
    origin=HERE.parent/'next_research_20261017/kaggle_micro_e14'
    definitions=next(ast.literal_eval(n.value) for n in ast.parse((origin/'worker.py').read_text()).body
                     if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='DEFINITIONS' for t in n.targets))
    protocol=dict(schema='revisi-ii-qwen-zero-v1',model='Qwen/Qwen3-VL-8B-Instruct',revision='0c351dd01ed87e9c1b53cbc748cba10e6187ff3b',
        dataset_sha256='cba20f8250bcb59481ed2d3d7d5d42fb8242c96a7ba2d11a2cd02ad80862961a',
        description_sha256='c75e8df3f9b71d6786462f8d0f1187ebe4234fb8dd079924f3f35707ff1b8cd2',
        zeroshot_sha256='10c07b06b13fbbf647f2b1ed12a722d9bff8f97caa6b621430d8bc0429ab38c9',
        definitions=definitions,quantization='NF4 double quantization FP16 compute',seed=20261101,
        input_basic=['image384','headline_verified','supporting_text_verified'],
        input_rich=['image384','headline_verified','supporting_text_verified','description1000','source_visual250','reason500'],
        wall_seconds_limit=1200 if mode=='smoke' else 7200,evaluation='zero-shot inference only, NOT training OOF',
        controls='same sorted class codes and per-task definitions as historical E14',source_sha256=sha(WORKER))
    kernel=OUT/mode/'kernel';kernel.mkdir(parents=True,exist_ok=True)
    launch='import os,sys,subprocess\nfrom pathlib import Path\n'
    pipline=next(l for l in (origin/'fold5/launch.py').read_text().splitlines() if "'-m','pip'" in l)
    launch+=pipline+'\n'
    launch+=f"os.environ['RII_ZERO_SMOKE']={'1' if mode=='smoke' else '0'!r}\n"
    launch+=f"Path('/kaggle/working/protocol.json').write_text({json.dumps(protocol,indent=2)!r})\n"
    launch+=f"Path('/kaggle/working/zero_worker.py').write_text({WORKER.read_text()!r})\n"
    launch+="subprocess.run([sys.executable,'-u','/kaggle/working/zero_worker.py'],check=True,timeout=7500)\n"
    compile(launch,'launch.py','exec');(kernel/'launch.py').write_text(launch)
    metadata=json.loads((origin/'fold5/kernel-metadata.json').read_text())
    metadata.update(id=REF+mode,title='Tempo Revisi II Qwen Zero '+mode.title(),is_private=True,kernel_sources=['yusepmuhamadzazuli/tempo-e01-vlm'])
    write_json(kernel/'kernel-metadata.json',metadata);write_json(OUT/mode/'protocol.json',protocol)
    return kernel


def status(mode):
    r=subprocess.run(['kaggle','kernels','status',REF+mode],capture_output=True,text=True,timeout=90)
    m=re.search(r'KernelWorkerStatus\.([A-Z_]+)',r.stdout)
    if r.returncode or not m:raise RuntimeError((r.stderr or r.stdout)[:1000])
    result=dict(kernel=REF+mode,status=m[1],observed_at=datetime.now(timezone.utc).isoformat())
    write_json(OUT/mode/'status.json',result);print(json.dumps(result));return m[1]


def submit(mode):
    ledger=OUT/mode/'submission.json'
    if ledger.exists():raise RuntimeError('Submission record exists: use status/collect; do not duplicate push')
    if mode=='full':
        v=json.loads((OUT/'smoke/verification.json').read_text());assert v['status']=='verified' and v['worker_sha256']==sha(WORKER)
    folder=build(mode)
    write_json(ledger,dict(kernel=REF+mode,state='submission_intent',version=1,worker_sha256=sha(WORKER)))
    r=subprocess.run(['kaggle','kernels','push','-p',str(folder)],capture_output=True,text=True,timeout=120)
    write_json(ledger,dict(kernel=REF+mode,state='submitted' if r.returncode==0 else 'push_ambiguous',version=1,worker_sha256=sha(WORKER),output=r.stdout,stderr=r.stderr))
    if r.returncode:raise RuntimeError((r.stderr or r.stdout)[:1500])
    print(r.stdout)


def collect(mode):
    if status(mode)!='COMPLETE':raise RuntimeError('Zero-shot job not complete')
    raw=OUT/mode/'raw';raw.mkdir(parents=True,exist_ok=True)
    r=subprocess.run(['kaggle','kernels','output',REF+mode,'-p',str(raw),'-q','--file-pattern',r'.*\.(json|jsonl|csv)$'],capture_output=True,text=True,timeout=300)
    if r.returncode:raise RuntimeError((r.stderr or r.stdout)[:1000])
    base=raw/('revisi_ii_qwen_zero_smoke' if mode=='smoke' else 'revisi_ii_qwen_zero')
    result=json.loads((base/'result.json').read_text());assert result['status']=='complete' and result['no_training']
    assert result['source_sha256']==sha(WORKER)
    remote_protocol=raw/'protocol.json'
    assert json.loads(remote_protocol.read_text())==json.loads((OUT/mode/'protocol.json').read_text())
    assert result['protocol_sha256']==sha(remote_protocol)
    assert result['samples']==(4 if mode=='smoke' else 740)
    assert sha(base/'input_audit.jsonl')==result['input_audit_sha256']
    for scope,digest in result['predictions_sha256'].items():
        source=base/f'predictions_{scope.lower()}.csv';assert sha(source)==digest
        if mode=='full':
            target=APP/'04_hasil_eksperimen/revisi_ii/experiments'/f'RII_QWEN_ZERO_{scope}'
            target.mkdir(parents=True,exist_ok=True)
            if (target/'predictions.csv').exists():assert sha(target/'predictions.csv')==digest
            else:shutil.copy2(source,target/'predictions.csv')
            write_json(target/'result.json',result)
    write_json(OUT/mode/'verification.json',dict(status='verified',samples=result['samples'],worker_sha256=sha(WORKER),
               protocol_sha256=result['protocol_sha256'],no_training=True))
    print('ZERO VERIFIED',mode)


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['build','submit','status','collect']);ap.add_argument('mode',choices=['smoke','full']);a=ap.parse_args();globals()[a.action](a.mode)
