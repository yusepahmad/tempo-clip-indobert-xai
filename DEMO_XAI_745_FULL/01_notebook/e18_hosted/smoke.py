"""One label-blind image request; technical validation only, no quality selection."""
import base64
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import pandas as pd
from PIL import Image
import requests

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / '01_notebook/kaggle_e15'))
from prompt import DEFINITIONS, build_prompt

sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
folder = ROOT / '04_hasil_eksperimen/e18_hosted'
folder.mkdir(parents=True, exist_ok=True)
assert not (folder / 'smoke_attempt.json').exists(), 'Inspect previous attempt before any new request'
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
prompt = build_prompt(0, df, *sources, classes)
permuted = df.copy()
permuted['task2_domain_sumber'] = df.task2_domain_sumber.iloc[::-1].to_numpy()
assert prompt == build_prompt(0, permuted, *sources, classes)
image_path = ROOT / '05_gambar' / Path(df.image_path.iloc[0]).name
with Image.open(image_path) as im:
    image = im.convert('RGB')
    image.thumbnail((384, 384), Image.Resampling.LANCZOS)
    buf = io.BytesIO()
    image.save(buf, format='PNG')
image_bytes = buf.getvalue()
model = 'google/gemini-3-flash-preview'
payload = dict(model=model, messages=[dict(role='user', content=[
    dict(type='image_url', image_url=dict(url='data:image/png;base64,' + base64.b64encode(image_bytes).decode())),
    dict(type='text', text=prompt)])], max_tokens=2048, stream=False)
def quota():
    env = os.environ.copy()
    env['KAGGLE_CONFIG_DIR'] = '/home/research-user/workspace/learn/.kaggle'
    output = subprocess.check_output(['/home/research-user/workspace/learn/.kaggle/cli/bin/python',
                                      str(Path(__file__).with_name('quota.py'))], env=env, text=True)
    balances = json.loads(output)
    assert len(balances) == 2 and all(b['remaining'] >= 0.10 for b in balances)
    return balances
before = quota()
secret = Path('/home/research-user/workspace/learn/.kaggle/e18_proxy.env')
assert secret.stat().st_mode & 0o777 == 0o600
config = dict(line.split('=', 1) for line in secret.read_text().splitlines())
url = config['MODEL_PROXY_URL'].removesuffix('/openapi').removesuffix('/genai') + '/openapi/chat/completions'
assert url.startswith('https://') and 'kaggle' in url.split('/')[2]
meta = dict(status='request_started', index=0, sample_id=df.sample_id.iloc[0], model=model,
            worker_sha256=sha(Path(__file__)), csv_sha256=sha(csv),
            prompt_helper_sha256=sha(ROOT / '01_notebook/kaggle_e15/prompt.py'),
            prompt_sha256=hashlib.sha256(prompt.encode()).hexdigest(), image_sha256=sha(image_path),
            transmitted_image_sha256=hashlib.sha256(image_bytes).hexdigest(),
            image_size=image.size, max_tokens=2048, quota_before=before,
            target_provided=False, purpose='technical_smoke_not_quality_selection')
(folder / 'smoke_attempt.json').write_text(json.dumps(meta, indent=2) + '\n')
started = time.monotonic()
try:
    response = requests.post(url, headers={'Authorization': 'Bearer ' + config['MODEL_PROXY_API_KEY']},
                             json=payload, timeout=(20, 180))
except requests.RequestException:
    meta['status'] = 'request_uncertain_do_not_retry'
    (folder / 'smoke_attempt.json').write_text(json.dumps(meta, indent=2) + '\n')
    raise RuntimeError('Request observation failed; inspect quota and attempt before retry') from None
meta.update(status='http_response', http_status=response.status_code, elapsed_seconds=time.monotonic()-started)
if response.ok:
    result = response.json()
    (folder / 'smoke_response.json').write_text(json.dumps(result, indent=2) + '\n')
    answer = result['choices'][0]['message'].get('content') or ''
    meta.update(status='response_received', response_sha256=sha(folder / 'smoke_response.json'),
                finish_reason=result['choices'][0].get('finish_reason'),
                valid_single_code=answer.strip() in 'ABCDEFG' and len(answer.strip()) == 1,
                usage=result.get('usage'), response_model=result.get('model'))
else:
    # Never log raw server errors: they could echo headers or request contents.
    meta['status'] = 'http_error_no_retry'
meta['quota_after'] = quota()
meta['quota_delta'] = [a['used']-b['used'] for a,b in zip(meta['quota_after'], before)]
(folder / 'smoke_attempt.json').write_text(json.dumps(meta, indent=2) + '\n')
print(json.dumps(meta, indent=2))
