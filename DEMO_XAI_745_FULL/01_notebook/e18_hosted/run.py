"""Pinned zero-shot740; official quota, persistent per-request evidence, no auto retry."""
import base64
import fcntl
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from datetime import datetime, timezone
import pandas as pd
from PIL import Image
import requests

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / '01_notebook/kaggle_e15'))
from prompt import DEFINITIONS, build_prompt
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
out = ROOT / '04_hasil_eksperimen/e18_hosted'
out.mkdir(parents=True, exist_ok=True)
lock = (out / 'run.lock').open('a')
fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
csv = ROOT / '03_data/DATASET_740_TASK2_DOMAIN.csv'
assert sha(csv) == 'cba20f8250bcb59481ed2d3d7d5d42fb8242c96a7ba2d11a2cd02ad80862961a'
df = pd.read_csv(csv).fillna('')
assert len(df) == 740 and df.sample_id.is_unique
sources = []
e01 = ROOT / '04_hasil_eksperimen/e01_vlm/kaggle_full/e01_vlm'
for name, digest in [('deskripsi.jsonl', 'c75e8df3f9b71d6786462f8d0f1187ebe4234fb8dd079924f3f35707ff1b8cd2'),
                     ('zeroshot.jsonl', '10c07b06b13fbbf647f2b1ed12a722d9bff8f97caa6b621430d8bc0429ab38c9')]:
    assert sha(e01 / name) == digest
    rows = [json.loads(x) for x in (e01 / name).read_text().splitlines()]
    lookup = {x['sample_id']: x for x in rows}
    assert len(rows) == len(lookup) == 740 and set(lookup) == set(df.sample_id)
    sources.append([lookup[sid] for sid in df.sample_id])
classes = sorted(DEFINITIONS)
permuted = df.copy()
permuted['task2_domain_sumber'] = df.task2_domain_sumber.iloc[::-1].to_numpy()
model = 'google/gemini-3-flash-preview'
config = dict(model=model, max_tokens=2048, max_image_side=384, image_format='PNG',
              budget_usd=6.0, request_reserve_usd=0.03, minimum_balance_usd=0.10,
              csv_sha256=sha(csv), worker_sha256=sha(Path(__file__)),
              quota_source_sha256=sha(Path(__file__).with_name('quota.py')),
              prompt_helper_sha256=sha(ROOT / '01_notebook/kaggle_e15/prompt.py'),
              protocol='zero_shot_no_fit_no_target_in_prompt_no_retries_invalid_counts_wrong',
              classes=classes)
config_path = out / 'config.json'
if config_path.exists():
    assert json.loads(config_path.read_text()) == config, 'Protocol/source changed; stop'
else:
    config_path.write_text(json.dumps(config, indent=2) + '\n')
config_sha = sha(config_path)
def quota():
    env = os.environ.copy(); env['KAGGLE_CONFIG_DIR'] = '/home/research-user/workspace/learn/.kaggle'
    balances = json.loads(subprocess.check_output([
        '/home/research-user/workspace/learn/.kaggle/cli/bin/python', str(Path(__file__).with_name('quota.py'))],
        env=env, text=True))
    assert len(balances) == 2 and all(b['remaining'] >= config['minimum_balance_usd'] for b in balances)
    return balances
def save(path, obj):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(obj, indent=2) + '\n'); temporary.replace(path)
def usage_cost(result):
    usage = result['usage']; cost = usage['cost']
    assert usage['prompt_tokens'] > 0 and usage['completion_tokens'] >= 0
    cents = cost['input_tokens_cost_nanodollars'] + cost['output_tokens_cost_nanodollars']
    assert isinstance(cents, (int, float)) and cents >= 0
    return cents / 1e9
records = out / 'records'; records.mkdir(exist_ok=True)
total_cost = 0.0
for index, row in df.iterrows():
    path = records / f'{index:04d}.json'
    prompt = build_prompt(index, df, *sources, classes)
    assert prompt == build_prompt(index, permuted, *sources, classes)
    image_path = ROOT / '05_gambar' / Path(row.image_path).name
    with Image.open(image_path) as im:
        image = im.convert('RGB'); image.thumbnail((384,384), Image.Resampling.LANCZOS)
        buf = io.BytesIO(); image.save(buf, format='PNG')
    data = buf.getvalue()
    evidence = dict(index=index, sample_id=row.sample_id, model=model, config_sha256=config_sha,
                    prompt_sha256=hashlib.sha256(prompt.encode()).hexdigest(), image_sha256=sha(image_path),
                    transmitted_image_sha256=hashlib.sha256(data).hexdigest(), image_size=list(image.size))
    if path.exists():
        previous = json.loads(path.read_text())
        assert all(previous[k] == v for k,v in evidence.items())
        assert previous['status'] == 'complete', 'Uncertain previous request; audit before resuming'
        total_cost += usage_cost(previous['response'])
        continue
    before = quota()
    assert total_cost + config['request_reserve_usd'] <= config['budget_usd'], 'Experiment budget guard'
    assert min(b['remaining'] for b in before) >= config['request_reserve_usd'] + config['minimum_balance_usd']
    if index == 0:
        smoke = json.loads((out / 'smoke_attempt.json').read_text())
        assert smoke['status'] == 'response_received' and smoke['valid_single_code']
        assert smoke['worker_sha256'] == sha(Path(__file__).with_name('smoke.py'))
        assert smoke['prompt_helper_sha256'] == config['prompt_helper_sha256']
        assert smoke['max_tokens'] == 2048
        for name in ('sample_id','model','prompt_sha256','image_sha256','transmitted_image_sha256'):
            assert smoke[name] == evidence[name]
        response = json.loads((out / 'smoke_response.json').read_text())
        assert smoke['response_sha256'] == sha(out / 'smoke_response.json')
        evidence.update(reused_smoke=True, quota_before=smoke['quota_before'], quota_after=smoke['quota_after'])
    else:
        secret = Path('/home/research-user/workspace/learn/.kaggle/e18_proxy.env')
        assert secret.stat().st_mode & 0o777 == 0o600
        credentials = dict(x.split('=',1) for x in secret.read_text().splitlines())
        expiry = datetime.fromisoformat(credentials['MODEL_PROXY_EXPIRY_TIME'].replace('Z','+00:00'))
        assert (expiry-datetime.now(timezone.utc)).total_seconds() > 180, 'Token expiring; refresh after audit'
        url = credentials['MODEL_PROXY_URL'].removesuffix('/openapi').removesuffix('/genai')+'/openapi/chat/completions'
        assert url.startswith('https://') and 'kaggle' in url.split('/')[2]
        payload = dict(model=model, messages=[dict(role='user', content=[
            dict(type='image_url',image_url=dict(url='data:image/png;base64,'+base64.b64encode(data).decode())),
            dict(type='text',text=prompt)])], max_tokens=2048, stream=False)
        evidence.update(status='request_started_no_automatic_retry', quota_before=before)
        save(path, evidence)
        started = time.monotonic()
        try:
            r = requests.post(url, headers={'Authorization':'Bearer '+credentials['MODEL_PROXY_API_KEY']},
                              json=payload, timeout=(20,180))
        except requests.RequestException:
            raise RuntimeError('Observation uncertain; request marker retained; no retry') from None
        evidence.update(http_status=r.status_code, elapsed_seconds=time.monotonic()-started)
        if not r.ok:
            evidence['status']='http_error_no_retry'; save(path,evidence)
            raise RuntimeError(f'HTTP {r.status_code}; inspect before any new call')
        response = r.json()
        evidence['response'] = response
        evidence['status'] = 'response_received_pending_quota_audit'
        save(path, evidence)
        evidence['quota_after'] = quota()
    assert response['model'] == model and len(response['choices']) == 1
    choice = response['choices'][0]
    answer = (choice['message'].get('content') or '').strip()
    code = answer if len(answer) == 1 and answer in 'ABCDEFG' else 'INVALID'
    evidence.update(status='complete', response=response, code=code,
                    prediction=classes['ABCDEFG'.index(code)] if code != 'INVALID' else 'INVALID',
                    finish_reason=choice.get('finish_reason'), cost_usd=usage_cost(response))
    assert evidence['cost_usd'] <= config['request_reserve_usd'], 'Observed cost exceeds reserved budget'
    for b,a in zip(evidence['quota_before'],evidence['quota_after']):
        assert b['period'] == a['period']
        assert abs((a['used']-b['used'])-evidence['cost_usd']) < 1e-6, 'Quota and usage do not reconcile'
    save(path, evidence)
    total_cost += evidence['cost_usd']
    save(out / 'progress.json', dict(status='running', completed=index+1, samples_required=740,
                                    cost_usd=total_cost, worker_pid=os.getpid()))
    print(index+1, row.sample_id, code, round(total_cost,6), flush=True)
assert len(list(records.glob('*.json'))) == 740
save(out / 'progress.json', dict(status='predictions_complete_pending_audit', completed=740,
                               samples_required=740,cost_usd=total_cost,worker_pid=os.getpid()))
print('PREDICTIONS COMPLETE; run independent verifier', flush=True)
