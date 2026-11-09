"""Inspect/collect one submitted deployment job. Never pushes or retrains."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

import build

REF = 'research-account/tempo-micro-e14-deployment-refit'
OUT = build.APP/'04_hasil_eksperimen/next_research_20261017/07_micro_e14_deployment'


def status():
    run = subprocess.run(['kaggle','kernels','status',REF], capture_output=True, text=True, timeout=90)
    match = re.search(r'KernelWorkerStatus\.([A-Z_]+)',run.stdout)
    if run.returncode or not match:
        raise RuntimeError('Cannot verify job status: '+(run.stderr or run.stdout)[:1000])
    record = dict(kernel=REF, submitted_version=1, status=match[1], observed_at=datetime.now(timezone.utc).isoformat(),
                  note='Status observation only. No duplicate push/retry is performed.')
    OUT.mkdir(parents=True, exist_ok=True)
    build.write(OUT/'job_state.json', record)
    print(json.dumps(record))
    return match[1]


def verify(folder):
    manifest = json.loads((build.HERE/'build_manifest.json').read_text())
    for name, expected in manifest['files'].items():
        assert build.sha(build.HERE/name) == expected, name
    result = json.loads((folder/'result.json').read_text())
    protocol = json.loads((build.HERE/'deployment_protocol.json').read_text())
    assert result['status'] == 'complete' and result['version'] == 'micro-e14-qlora-v1'
    assert result['source_sha256'] == build.sha(build.HERE/'deployment_worker.py')
    assert result['protocol_sha256'] == build.sha(build.HERE/'deployment_protocol.json')
    assert result['data_sha256'] == protocol['dataset_sha256']
    assert result['train_samples'] == 740 and result['epochs'] == protocol['epochs'] == 3
    assert [r['epoch'] for r in result['refit_history']] == [1,2,3]
    assert result['deployment_benchmark'] == 'Not Evaluated'
    assert result['smoke']['samples'] == 1
    assert all(0 <= v <= 1e-4 for v in result['smoke']['max_probability_difference'].values())
    assert build.sha(folder/'input_audit.jsonl') == result['input_audit_sha256']
    for name in ('adapter/adapter_config.json','adapter/adapter_model.safetensors'):
        assert name in result['artifacts']
    for name, expected in result['artifacts'].items():
        assert (folder/name).resolve().parent == (folder/'adapter').resolve()
        assert build.sha(folder/name) == expected
    adapter = json.loads((folder/'adapter/adapter_config.json').read_text())
    assert adapter['r'] == 16 and adapter['lora_alpha'] == 32 and adapter['lora_dropout'] == .05
    assert adapter['base_model_name_or_path'] == protocol['model'] and adapter['revision'] == protocol['revision']
    assert set(adapter['target_modules']) == {'q_proj','k_proj','v_proj','o_proj'}
    # Exact equality to historical audits proves image/prompt/token equivalence.
    historical = [json.loads(line) for line in (build.OOF/'fold5/input_audit.jsonl').read_text().splitlines()]
    actual = [json.loads(line) for line in (folder/'input_audit.jsonl').read_text().splitlines()]
    assert actual == historical and len(actual) == 2220
    record = dict(status='verified', collected_at=datetime.now(timezone.utc).isoformat(), kernel=REF,
                  result_sha256=build.sha(folder/'result.json'), artifacts=result['artifacts'],
                  checks=['source/protocol/data hashes','740 refit, three epochs','2220 input audits identical to CV',
                          'PEFT artifact hashes/config','GPU save/reload probability parity'],
                  limitation='Kaggle in-sample smoke only; local GPU runtime/clean Windows not tested; no new deployment benchmark')
    build.write(folder/'verification.json',record)
    return record


def collect():
    if status() != 'COMPLETE':
        print('Not complete; no files installed, no resubmission.')
        return
    raw = OUT/'raw_kaggle'
    raw.mkdir(exist_ok=True)
    subprocess.run(['kaggle','kernels','output',REF,'-p',str(raw),'--force','--file-pattern',
        r'^e14_deploy/(result\.json|input_audit\.jsonl|adapter/adapter_config\.json|adapter/adapter_model\.safetensors)$'],check=True,timeout=1800)
    folder = raw/'e14_deploy'
    record = verify(folder)
    # Preserve an existing installed checkpoint unless byte-identical.
    names = ['result.json','input_audit.jsonl','verification.json', *record['artifacts']]
    for name in names:
        target = build.PACKAGE/name
        if target.exists() and name != 'verification.json':
            assert build.sha(target) == build.sha(folder/name), f'Existing checkpoint differs: {name}'
    for name in names:
        target = build.PACKAGE/name
        target.parent.mkdir(exist_ok=True, parents=True)
        shutil.copyfile(folder/name,target)
    build.write(OUT/'verification.json',record)
    print('VERIFIED and installed in',build.PACKAGE)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['status','collect'])
    args = parser.parse_args()
    {'status':status,'collect':collect}[args.action]()
