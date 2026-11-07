"""Immutable grounded source/target JSON cache; one smoke is reused by full inference."""
import argparse
import base64
import csv
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time
from urllib.parse import urlparse

import requests
from prepare import ROOT, MODEL, MAX_SIDE, PROMPT, sha, image_helper, build_prompt, context
from schema import decode
transmitted_image = image_helper()
BASE = ROOT / "04_hasil_eksperimen/e28_mapping"
OUT = ROOT / "04_hasil_eksperimen/e28_mapping_run"


def save(path, value):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, indent=2) + '\n')
    temporary.replace(path)


def usable(content, finish):
    try:
        decode(content, finish)
        return True
    except (ValueError, TypeError):
        return False


def quota():
    env = os.environ.copy()
    env['KAGGLE_CONFIG_DIR'] = '/home/yusep/workspace/learn/.kaggle'
    value = json.loads(subprocess.check_output([
        '/home/yusep/workspace/learn/.kaggle/cli/bin/python',
        str(ROOT / '01_notebook/e18_hosted/quota.py')], env=env, text=True))
    assert len(value) == 2 and all(b['remaining'] >= .10 for b in value)
    return value


def budget_guard(before, total, config):
    reserve = config['request_reserve_usd']
    assert total + reserve <= config['budget_usd'], 'Budget guard before request'
    assert min(b['remaining'] for b in before) >= config['minimum_balance_usd'] + reserve, 'Quota guard before request'


def access_url(credentials, now=None):
    expiry = datetime.fromisoformat(credentials['MODEL_PROXY_EXPIRY_TIME'].replace('Z', '+00:00'))
    assert (expiry - (now or datetime.now(timezone.utc))).total_seconds() > 180, 'Token expiring; audit before official refresh'
    url = credentials['MODEL_PROXY_URL'].removesuffix('/openapi').removesuffix('/genai') + '/openapi/chat/completions'
    parsed = urlparse(url)
    assert parsed.scheme == 'https' and parsed.hostname and parsed.hostname.endswith('.kaggle.net')
    return url


def load():
    prepared = json.loads((BASE / 'preparation_verification.json').read_text())
    assert prepared['status'] == 'preparation_verified' and prepared['samples'] == 740
    assert prepared['source_sha256'] == sha(ROOT / '01_notebook/e28_mapping/prepare.py')
    assert prepared['config_sha256'] == sha(BASE / 'config.json')
    assert prepared['inputs_sha256'] == sha(BASE / 'inputs.jsonl')
    inputs_config = json.loads((BASE / 'config.json').read_text())
    assert inputs_config['inputs_sha256'] == prepared['inputs_sha256']
    assert inputs_config['model'] == MODEL and inputs_config['max_image_side'] == MAX_SIDE == 768
    rows = [json.loads(line) for line in (BASE / 'inputs.jsonl').read_text().splitlines()]
    csv_path = ROOT / '03_data/DATASET_740_TASK2_DOMAIN.csv'
    assert sha(csv_path) == inputs_config['csv_sha256']
    originals = list(csv.DictReader(csv_path.open(encoding='utf-8-sig')))
    assert len(rows) == len(originals) == 740
    for i, (r, original) in enumerate(zip(rows, originals)):
        assert r['index'] == i and r['sample_id'] == original['sample_id']
        assert r['prompt'] == build_prompt(original) and r['original_context'] == context(original)
        assert r['image_name'] == Path(original['image_path']).name
    prior = ROOT / '04_hasil_eksperimen/e27_stacking'
    v = json.loads((prior / 'verification.json').read_text())
    assert v['status'] == 'verified' and v['samples'] == 740 and v['macro_f1'] < .70
    assert v['verifier_sha256'] == sha(ROOT / '01_notebook/e27_stacking/verify.py')
    for name, digest in v['sha256'].items():
        assert sha(prior / name) == digest
    config = dict(model=MODEL, samples=740, max_tokens=4096, max_image_side=768,
                  reasoning_effort="low", budget_usd=1.80, request_reserve_usd=.05, minimum_balance_usd=.10,
                  worker_sha256=sha(Path(__file__)), schema_sha256=sha(Path(__file__).with_name('schema.py')), preparation_sha256=prepared['source_sha256'],
                  config_sha256=prepared['config_sha256'], inputs_sha256=prepared['inputs_sha256'],
                  quota_source_sha256=sha(ROOT / '01_notebook/e18_hosted/quota.py'),
                  prior_verification_sha256=sha(prior / 'verification.json'),
                  protocol='grounded_source_target_original_context_no_labels_no_retry_smoke_reused')
    return rows, config


def main(limit):
    assert 1 <= limit <= 740
    rows, config = load()  # Fail before any output/request if preparation/prior incomplete.
    OUT.mkdir(exist_ok=True)
    lock = (OUT / 'run.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    run_config = OUT / 'run_config.json'
    if run_config.exists():
        assert json.loads(run_config.read_text()) == config, 'Immutable protocol/source changed'
    else:
        quota()
        save(run_config, config)
    records = OUT / 'records'
    records.mkdir(exist_ok=True)
    total = 0.0
    for row in rows[:limit]:
        index = row['index']
        path = records / f'{index:04d}.json'
        image_path = ROOT / '05_gambar' / row['image_name']
        data, size = transmitted_image(image_path)
        assert sha(image_path) == row['image_sha256']
        assert hashlib.sha256(data).hexdigest() == row['transmitted_image_sha256'] and size == row['image_size']
        evidence = dict(index=index, sample_id=row['sample_id'], model=MODEL,
                        run_config_sha256=sha(run_config), prompt_sha256=row['prompt_sha256'],
                        image_sha256=row['image_sha256'], transmitted_image_sha256=row['transmitted_image_sha256'],
                        image_size=size)
        if path.exists():
            previous = json.loads(path.read_text())
            assert all(previous[k] == value for k, value in evidence.items())
            assert previous['status'] == 'complete' and previous['usable'], 'Prior request requires audit; no retry'
            total += previous['cost_usd']
            continue
        before = quota()
        budget_guard(before, total, config)
        secret = Path('/home/yusep/workspace/learn/.kaggle/e18_proxy.env')
        assert secret.stat().st_mode & 0o777 == 0o600
        credentials = dict(line.split('=', 1) for line in secret.read_text().splitlines())
        url = access_url(credentials)
        payload = dict(model=MODEL, messages=[dict(role='user', content=[
            dict(type='image_url', image_url=dict(url='data:image/png;base64,' + base64.b64encode(data).decode())),
            dict(type='text', text=row['prompt'])])], max_tokens=4096, reasoning_effort=config["reasoning_effort"], stream=False)
        evidence.update(status='request_started_no_automatic_retry', quota_before=before)
        save(path, evidence)
        started = time.monotonic()
        try:
            response = requests.post(url, headers={'Authorization': 'Bearer ' + credentials['MODEL_PROXY_API_KEY']},
                                     json=payload, timeout=(20, 180))
        except requests.RequestException:
            raise RuntimeError('Uncertain request; marker retained; no automatic retry') from None
        evidence.update(http_status=response.status_code, elapsed_seconds=time.monotonic() - started)
        if not response.ok:
            evidence['status'] = 'http_error_no_retry'
            save(path, evidence)
            raise RuntimeError(f'HTTP {response.status_code}; raw error omitted; audit required')
        result = response.json()
        evidence.update(status='response_pending_audit', response=result)
        save(path, evidence)
        assert result['model'] == MODEL and len(result['choices']) == 1
        after = quota()
        usage = result['usage']; cost = usage['cost']
        value = (cost['input_tokens_cost_nanodollars'] + cost['output_tokens_cost_nanodollars']) / 1e9
        assert 0 <= value <= .05 and usage['prompt_tokens'] > 0 and usage['completion_tokens'] >= 0
        for b, a in zip(before, after):
            assert b['period'] == a['period'] and abs(a['used'] - b['used'] - value) < 1e-6
        content = result['choices'][0]['message'].get('content') or ''
        finish = result['choices'][0].get('finish_reason')
        valid = usable(content, finish)
        fields, explanation = decode(content, finish) if valid else (None, '')
        evidence.update(status='complete', quota_after=after, cost_usd=value,
                        fields=fields, explanation=explanation, finish_reason=finish, usable=valid)
        save(path, evidence)
        assert evidence['usable'], 'Unusable structured explanation retained; root audit required; no retry'
        total += value
        save(OUT / 'progress.json', dict(status='running', completed=index + 1, samples_required=740,
                                        cost_usd=total, worker_pid=os.getpid()))
        print(index + 1, row['sample_id'], 'usable_explanation', round(total, 6), flush=True)
    save(OUT / 'progress.json', dict(status='smoke_complete_pending_audit' if limit < 740 else 'explanations_complete_pending_audit',
                                    completed=limit, samples_required=740, cost_usd=total, worker_pid=os.getpid()))
    print('EXPLANATION CACHE COMPLETE FOR LIMIT', limit, flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--limit', type=int, default=740)
    main(parser.parse_args().limit)
