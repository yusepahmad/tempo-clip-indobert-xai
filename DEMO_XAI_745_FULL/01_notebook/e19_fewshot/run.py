"""Fixed outer-training few-shot740; only run after E18 terminal/audited and below target."""
import os
for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'):os.environ[key]='1'
import base64
from datetime import datetime,timezone
import fcntl
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import time
import requests
from PIL import Image
from verify_inputs import ROOT,check_inputs
sys.path.insert(0,str(ROOT/'01_notebook/e18_hosted'))
from parse_v2 import parse_answer

sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
prior=ROOT/'04_hasil_eksperimen/e18_hosted'
prior_verification=json.loads((prior/'verification.json').read_text())
prior_parsed=json.loads((prior/'parsed/metrics.json').read_text())
prior_v2=json.loads((prior/'parsed_v2/metrics.json').read_text())
assert prior_verification['status']=='verified' and prior_verification['samples']==740
assert prior_parsed['status']=='verified' and prior_parsed['samples']==740
assert prior_v2['status']=='verified' and prior_v2['samples']==740
valid=json.loads((prior/'valid/verification.json').read_text())
assert valid['status']=='verified' and valid['samples']==740 and set(valid['routes'])=={'strict','v1','v2'}
assert valid['verifier_sha256']==sha(ROOT/'01_notebook/e18_hosted/evaluate_valid.py')
assert valid['fallback_source_sha256']==sha(ROOT/'01_notebook/e18_hosted/valid_labels.py')
for name,digest in valid['sha256'].items():assert sha(prior/'valid'/name)==digest
assert max(r['macro_f1'] for r in valid['routes'].values())<0.70, 'Valid target candidate available; root completion audit first'
assert prior_parsed['strict_verification_sha256']==sha(prior/'verification.json')
assert prior_v2['strict_verification_sha256']==sha(prior/'verification.json')
assert prior_v2['parser_sha256']==sha(ROOT/'01_notebook/e18_hosted/parse_v2.py')
assert prior_v2['evaluator_sha256']==sha(ROOT/'01_notebook/e18_hosted/evaluate_parsed_v2.py')
assert prior_v2['oof_sha256']==sha(prior/'parsed_v2/oof.csv')
assert json.loads((prior/'watch_state.json').read_text())['phase']=='verified_pending_root_copy_audit'
original_pid=json.loads((prior/'watch_state.json').read_text())['worker_pid']
assert not Path(f'/proc/{original_pid}').exists(), 'Wait for prior original process terminal; do not overlap inference'
input_config,inputs,df,fold=check_inputs()
folder=ROOT/'04_hasil_eksperimen/e19_fewshot'
lock=(folder/'run.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
records=folder/'records';records.mkdir(exist_ok=True)
config=dict(model=input_config['model'],max_tokens=4096,max_image_side=384,image_format='PNG',
            protocol='outer5_training_retrieval14_fixed_no_tuning_no_retries_training_majority_fallback',budget_usd=6.0,
            request_reserve_usd=0.05,minimum_balance_usd=0.10,
            preparation_config_sha256=sha(folder/'config.json'),inputs_sha256=input_config['inputs_sha256'],
            worker_sha256=sha(Path(__file__)),input_verifier_sha256=sha(Path(__file__).with_name('verify_inputs.py')),
            parser_sha256=sha(ROOT/'01_notebook/e18_hosted/parse_v2.py'),
            quota_source_sha256=sha(ROOT/'01_notebook/e18_hosted/quota.py'),
            fallback_source_sha256=sha(ROOT/'01_notebook/e18_hosted/valid_labels.py'),
            prior_valid_verification_sha256=sha(prior/'valid/verification.json'),
            prior_verification_sha256=sha(prior/'verification.json'),
            prior_v2_metrics_sha256=sha(prior/'parsed_v2/metrics.json'),classes=input_config['classes'])
def save(path,obj):
    tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(obj,indent=2)+'\n');tmp.replace(path)
def quota():
    env=os.environ.copy();env['KAGGLE_CONFIG_DIR']='/home/research-user/workspace/learn/.kaggle'
    result=json.loads(subprocess.check_output(['/home/research-user/workspace/learn/.kaggle/cli/bin/python',
                   str(ROOT/'01_notebook/e18_hosted/quota.py')],env=env,text=True))
    assert len(result)==2 and all(b['remaining']>=0.10 for b in result)
    return result
runconfig=folder/'run_config.json'
if runconfig.exists():assert json.loads(runconfig.read_text())==config
else:
    initial=quota();assert min(b['remaining'] for b in initial)>=6.1, 'Wait for enough quota for the planned budget'
    save(runconfig,config)
config_hash=sha(runconfig)
total=0.0
for row in inputs:
    i=row['index'];path=records/f'{i:04d}.json'
    image_path=ROOT/'05_gambar'/Path(df.image_path.iloc[i]).name
    with Image.open(image_path) as im:
        image=im.convert('RGB');image.thumbnail((384,384),Image.Resampling.LANCZOS)
        buffer=io.BytesIO();image.save(buffer,format='PNG')
    data=buffer.getvalue()
    evidence=dict(index=i,sample_id=row['sample_id'],fold=row['fold'],model=config['model'],
                  config_sha256=config_hash,prompt_sha256=row['prompt_sha256'],image_sha256=row['image_sha256'],
                  transmitted_image_sha256=hashlib.sha256(data).hexdigest(),image_size=list(image.size))
    if path.exists():
        previous=json.loads(path.read_text())
        assert all(previous[k]==v for k,v in evidence.items())
        assert previous['status']=='complete', 'Prior request needs audit; no automatic retry'
        total+=previous['cost_usd'];continue
    before=quota()
    assert total+0.05<=6.0 and min(b['remaining'] for b in before)>=0.15, 'Quota/budget guard'
    secret=Path('/home/research-user/workspace/learn/.kaggle/e18_proxy.env')
    assert secret.stat().st_mode&0o777==0o600
    credentials=dict(line.split('=',1) for line in secret.read_text().splitlines())
    expiry=datetime.fromisoformat(credentials['MODEL_PROXY_EXPIRY_TIME'].replace('Z','+00:00'))
    assert (expiry-datetime.now(timezone.utc)).total_seconds()>180, 'Token expiring; refresh officially after audit'
    url=credentials['MODEL_PROXY_URL'].removesuffix('/openapi').removesuffix('/genai')+'/openapi/chat/completions'
    assert url.startswith('https://') and 'kaggle' in url.split('/')[2]
    payload=dict(model=config['model'],messages=[dict(role='user',content=[
        dict(type='image_url',image_url=dict(url='data:image/png;base64,'+base64.b64encode(data).decode())),
        dict(type='text',text=row['prompt'])])],max_tokens=4096,stream=False)
    evidence.update(status='request_started_no_automatic_retry',quota_before=before)
    save(path,evidence);started=time.monotonic()
    try:
        response=requests.post(url,headers={'Authorization':'Bearer '+credentials['MODEL_PROXY_API_KEY']},
                               json=payload,timeout=(20,180))
    except requests.RequestException:
        raise RuntimeError('Observation uncertain; inspect persistent marker before any retry') from None
    evidence.update(http_status=response.status_code,elapsed_seconds=time.monotonic()-started)
    if not response.ok:
        evidence['status']='http_error_no_retry';save(path,evidence)
        raise RuntimeError(f'HTTP {response.status_code}; raw error omitted; root audit required')
    result=response.json()
    evidence.update(status='response_received_pending_quota_audit',response=result);save(path,evidence)
    assert result['model']==config['model'] and len(result['choices'])==1
    after=quota();usage=result['usage'];cost=usage['cost']
    value=(cost['input_tokens_cost_nanodollars']+cost['output_tokens_cost_nanodollars'])/1e9
    assert 0<=value<=0.05 and usage['prompt_tokens']>0 and usage['completion_tokens']>=0
    for b,a in zip(before,after):
        assert b['period']==a['period'] and abs(a['used']-b['used']-value)<1e-6
    content=result['choices'][0]['message'].get('content') or ''
    answer=content.strip();strict=answer if len(answer)==1 and answer in 'ABCDEFG' else 'INVALID'
    code,rule=parse_answer(content,config['classes'])
    evidence.update(status='complete',quota_after=after,cost_usd=value,code=code,strict_code=strict,
                    parsing_rule=rule,finish_reason=result['choices'][0].get('finish_reason'),
                    prediction=config['classes'][ord(code)-ord('A')] if code!='INVALID' else 'INVALID')
    save(path,evidence);total+=value
    save(folder/'progress.json',dict(status='running',completed=i+1,samples_required=740,cost_usd=total,worker_pid=os.getpid()))
    print(i+1,row['sample_id'],code,round(total,6),flush=True)
assert len(list(records.glob('*.json')))==740
save(folder/'progress.json',dict(status='predictions_complete_pending_audit',completed=740,
                              samples_required=740,cost_usd=total,worker_pid=os.getpid()))
print('PREDICTIONS COMPLETE; independent audit required',flush=True)
