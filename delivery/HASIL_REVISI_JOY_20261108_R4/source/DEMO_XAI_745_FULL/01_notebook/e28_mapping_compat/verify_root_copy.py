"""Read-only evidence audit, then exclusive report; stdlib, no model/API calls."""
import argparse
import ast
import csv
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import zipfile

SOURCE = Path(__file__).resolve().parent
PROJECT = SOURCE.parents[1]
RECOVERY = SOURCE.parents[2] / 'docs/server-recovery/2026-10-11/e28_mapping'
FIELDS = ('source_object', 'source_properties', 'target_situation', 'mapping', 'uncertainty')
DATA_SHA = 'cba20f8250bcb59481ed2d3d7d5d42fb8242c96a7ba2d11a2cd02ad80862961a'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_text())
lines = lambda p: [json.loads(s) for s in p.read_text().splitlines()]
textsha = lambda s: hashlib.sha256(s.encode()).hexdigest()


def manifest(base, values, expected):
    assert set(values) == set(expected)
    for name, digest in values.items():
        assert sha(base / name) == digest, name


def parse(content):
    assert isinstance(content, str) and len(content.strip()) >= 40
    normalized = content.strip()
    if normalized.startswith('```'):
        parts = normalized.splitlines()
        assert len(parts) >= 3 and parts[0].strip() in ('```json', '```') and parts[-1].strip() == '```'
        normalized = '\n'.join(parts[1:-1]).strip()
    assert normalized.startswith('{') and normalized.endswith('}')
    pairs = json.loads(normalized, object_pairs_hook=lambda p: p)
    assert isinstance(pairs, list) and len(pairs) == len(FIELDS)
    assert len({k for k, _ in pairs}) == len(FIELDS)
    fields = dict(pairs)
    assert set(fields) == set(FIELDS)
    assert all(isinstance(fields[k], str) and fields[k].strip() for k in FIELDS)
    return fields, '\n'.join(k + ': ' + fields[k].strip() for k in FIELDS)


def audit_cache(cap):
    verified = read(cap / 'verification.json')
    assert verified['status'] == 'verified' and verified['samples'] == 740
    assert verified['verifier_sha256'] == sha(SOURCE / 'verify.py')
    names = ['run_config.json', 'sources.jsonl'] + [f'records/{i:04d}.json' for i in range(740)]
    manifest(cap, verified['sha256'], names)
    prepared_dir = RECOVERY / 'prepared_inputs'
    manifest(prepared_dir, verified['prepared_sha256'], ['config.json', 'inputs.jsonl'])
    config = read(cap / 'run_config.json'); prepared = read(prepared_dir / 'config.json')
    assert config == read(RECOVERY / 'compat_prefix24/run_config.json')
    assert sha(cap / 'run_config.json') == '5ecc1f549af1105f9bab77b82fc42ed8af342ab865c762d92fe750dc72549095'
    preparation_audit = read(RECOVERY / 'root_preparation_verification.json')
    assert preparation_audit['status'] == 'verified' and preparation_audit['samples'] == 740
    assert preparation_audit['config_sha256'] == sha(prepared_dir / 'config.json')
    assert preparation_audit['inputs_sha256'] == sha(prepared_dir / 'inputs.jsonl')
    for key, path in [('worker_sha256', SOURCE / 'run.py'), ('schema_sha256', SOURCE / 'schema.py'),
                      ('migrator_sha256', SOURCE / 'migrate.py'),
                      ('preparation_sha256', SOURCE.parent / 'e28_mapping/prepare.py'),
                      ('quota_source_sha256', SOURCE.parent / 'e18_hosted/quota.py')]:
        assert config[key] == sha(path)
    assert config['config_sha256'] == sha(prepared_dir / 'config.json')
    assert config['inputs_sha256'] == sha(prepared_dir / 'inputs.jsonl') == prepared['inputs_sha256']
    assert config['reasoning_effort'] == 'low' and config['max_tokens'] == 4096 and config['max_image_side'] == 768
    assert config['model'] == 'google/gemini-3-flash-preview'
    assert config['prior_verification_sha256'] == sha(RECOVERY.parent / 'e27_stacking/full_oof/verification.json')
    origin = RECOVERY / 'original_prefix24'
    assert config['origin_run_config_sha256'] == sha(origin / 'run_config.json')
    manifest(origin / 'records', config['origin_record_sha256'], [f'{i:04d}.json' for i in range(24)])
    migration = read(cap / 'migration.json')
    assert migration == read(RECOVERY / 'compat_prefix24/migration.json')
    assert migration['samples'] == 24 and migration['inference_requests_added'] == 0
    assert migration['source_sha256'] == config['migrator_sha256']
    assert migration['origin_run_config_sha256'] == config['origin_run_config_sha256']
    assert migration['origin_record_sha256'] == config['origin_record_sha256']
    manifest(cap, migration['sha256'], ['run_config.json'] + [f'records/{i:04d}.json' for i in range(24)])
    csv_path = PROJECT / '03_data/DATASET_740_TASK2_DOMAIN.csv'
    assert sha(csv_path) == prepared['csv_sha256'] == DATA_SHA
    with csv_path.open(encoding='utf-8-sig', newline='') as stream:
        df = list(csv.DictReader(stream))
    inputs = lines(prepared_dir / 'inputs.jsonl'); explanations = lines(cap / 'sources.jsonl')
    assert len(df) == len(inputs) == len(explanations) == 740
    ids = [r['sample_id'] for r in df]; assert len(set(ids)) == 740
    tree = ast.parse((SOURCE.parent / 'e28_mapping/prepare.py').read_text())
    template = [ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign)
                and any(isinstance(t, ast.Name) and t.id == 'PROMPT' for t in n.targets)]
    assert len(template) == 1 and textsha(template[0]) == prepared['prompt_template_sha256']
    image_inputs = lines(RECOVERY.parent / 'e22_caption/inputs.jsonl')
    e22_config = read(RECOVERY.parent / 'e22_caption/full_caption_cache/run_config.json')
    assert e22_config['inputs_sha256'] == sha(RECOVERY.parent / 'e22_caption/inputs.jsonl')
    assert len(image_inputs) == 740
    cost = 0
    for i, (row, request, explanation) in enumerate(zip(df, inputs, explanations)):
        record = read(cap / 'records' / f'{i:04d}.json')
        assert record['status'] == 'complete' and record['index'] == request['index'] == explanation['index'] == i
        assert record['sample_id'] == request['sample_id'] == explanation['sample_id'] == ids[i]
        assert record['run_config_sha256'] == sha(cap / 'run_config.json') and record['http_status'] == 200
        context = dict(headline=row['headline_verified'], supporting_text=row['supporting_text_verified'])
        prompt = template[0] + '\nOriginal verified text (JSON):\n' + json.dumps(context, ensure_ascii=False, sort_keys=True)
        assert request['original_context'] == context and request['prompt'] == prompt
        assert record['prompt_sha256'] == request['prompt_sha256'] == textsha(prompt)
        assert image_inputs[i]['sample_id'] == ids[i]
        for key in ('image_sha256', 'transmitted_image_sha256', 'image_size'):
            assert record[key] == request[key] == image_inputs[i][key]
        assert record['model'] == config['model'] == record['response']['model']
        choices = record['response']['choices']; assert len(choices) == 1
        fields, text = parse(choices[0]['message']['content'])
        assert record['fields'] == explanation['fields'] == fields
        assert record['explanation'] == explanation['explanation'] == text
        assert record['finish_reason'] == choices[0]['finish_reason'] == 'stop' and record['usable'] is True
        usage = record['response']['usage']; pricing = usage['cost']
        value = (pricing['input_tokens_cost_nanodollars'] + pricing['output_tokens_cost_nanodollars']) / 1e9
        assert 0 <= value <= .05 and abs(value - record['cost_usd']) < 1e-12
        assert usage['prompt_tokens'] > 0 and usage['completion_tokens'] >= 0
        assert len(record['quota_before']) == len(record['quota_after']) == 2
        for before, after in zip(record['quota_before'], record['quota_after']):
            assert before['period'] == after['period'] and abs(after['used'] - before['used'] - value) < 1e-6
            assert after['remaining'] >= .10
        if i < 24:
            original_path = origin / 'records' / f'{i:04d}.json'; original = read(original_path)
            assert record['migration_origin'] == dict(record_sha256=sha(original_path), run_config_sha256=sha(origin / 'run_config.json'))
            derived = {'run_config_sha256', 'fields', 'explanation', 'usable', 'migration_origin'}
            assert {k: v for k, v in original.items() if k not in derived} == {k: v for k, v in record.items() if k not in derived}
        else:
            assert 'migration_origin' not in record
        cost += value
    assert abs(cost - verified['cost_usd']) < 1e-12 and cost <= config['budget_usd'] == 1.8
    return df, explanations, cost


def npy_helpers():
    path = SOURCE.parent / 'e22_caption_low/verify_root_copy.py'
    assert sha(path) == '086d41e070fad216f5693e0cd3dc7fd3faec406f1d6a2f445f91132aab648b6a'
    spec = importlib.util.spec_from_file_location('pinned_root_npy', path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module.npy, module.unit_error


def audit_features(cap, df, explanations):
    emb = RECOVERY / 'full_embeddings'
    v = read(emb / 'verification.json'); meta = read(emb / 'meta.json'); signature = meta['signature']
    assert v['status'] == 'verified' and v['samples'] == 740 and v['dimension'] == 1024
    assert v['verifier_sha256'] == sha(SOURCE / 'verify_embeddings.py')
    manifest(emb, v['sha256'], ['embeddings.npz', 'meta.json', 'protocol.json', 'input_audit.jsonl'])
    assert signature == read(emb / 'protocol.json') and signature['worker_sha256'] == sha(SOURCE / 'embed.py')
    assert signature['explanations_verification_sha256'] == sha(cap / 'verification.json')
    assert signature['explanations_sha256'] == sha(cap / 'sources.jsonl') and signature['migration_sha256'] == sha(cap / 'migration.json')
    assert signature['csv_sha256'] == DATA_SHA and signature['model'] == 'BAAI/bge-m3'
    assert signature['revision'] == '5617a9f61b028005a4858fdac845db406aefb181'
    preparation = read(RECOVERY / 'compat_model_preparation.json')
    assert sha(RECOVERY / 'compat_model_preparation.json') == '63d8d6b61c77be38bc1606f8bbe6540b615b5c0ff6c8d16117c86d641109eb80'
    assert preparation['status'] == 'model_preparation_verified' and preparation['worker_sha256'] == sha(SOURCE / 'embed.py')
    assert signature['model_snapshot'] == preparation['model'] == read(RECOVERY.parent / 'e22_caption/model_preparation.json')['model']
    assert signature['previous_model_preparation_sha256'] == preparation['previous_model_preparation_sha256'] == '6e3a59e8a002a758135f04eab0cbb1bfbdf2b415b05f95d1ffbf4da523387709'
    for key, value in dict(pooling='CLS then L2', prefix='', max_length=1024, batch=4, dtype='float32', device='cpu', threads=8).items():
        assert signature[key] == value
    assert meta['status'] == 'complete' and meta['samples'] == 740 and meta['dimension'] == 1024
    assert meta['embeddings_sha256'] == sha(emb / 'embeddings.npz') and meta['input_audit_sha256'] == sha(emb / 'input_audit.jsonl')
    views = ['interpretation', 'interpretation_context']; assert signature['views'] == views
    audit = lines(emb / 'input_audit.jsonl'); assert len(audit) == 1480
    for j, view in enumerate(views):
        for i, (row, explanation) in enumerate(zip(df, explanations)):
            text = explanation['explanation'] if j == 0 else explanation['explanation'] + '\n' + row['headline_verified'] + ' ' + row['supporting_text_verified']
            a = audit[j * 740 + i]
            assert a['view'] == view and a['index'] == i and a['sample_id'] == row['sample_id'] and a['text_sha256'] == textsha(text)
            assert type(a['untruncated_tokens']) is int and a['untruncated_tokens'] > 0
            assert a['truncated'] == (a['untruncated_tokens'] > 1024)
        assert meta['truncated_by_view'][view] == sum(a['truncated'] for a in audit if a['view'] == view)
    npy, unit_error = npy_helpers(); norms = {}
    with zipfile.ZipFile(emb / 'embeddings.npz') as archive:
        assert len(archive.infolist()) == 3 and set(archive.namelist()) == {'sample_id.npy', *[s + '.npy' for s in views]}
        assert all(a.file_size < 20000000 for a in archive.infolist())
        assert npy(archive.read('sample_id.npy'), (740,)) == [r['sample_id'] for r in df]
        for view in views:
            norms[view] = unit_error(npy(archive.read(view + '.npy'), (740, 1024)), 740, 1024)
    assert v['sampled_indices'] == [0, 1, 37, 123, 369, 739]
    assert set(v['maximum_absolute_errors']) == set(views) and all(0 <= e < 1e-5 for e in v['maximum_absolute_errors'].values())
    return dict(embedding_verification_sha256=sha(emb / 'verification.json'), maximum_norm_errors=norms, dimension=1024)


def main(cache_only=False):
    cap = RECOVERY / 'full_explanation_cache'
    df, explanations, cost = audit_cache(cap)
    report = dict(status='verified', samples=740, explanation_cost_quota_usd=cost,
                  explanations_verification_sha256=sha(cap / 'verification.json'), verifier_sha256=sha(Path(__file__)),
                  checks=['all742 cache manifest/current source/config/prepared/prior pins', 'all740 original IDs/context/prompt/raw5fields/usage/quota/budget', 'all24 original responses preserved and migration manifest verified'],
                  limitations=['PNG reconstruction performed by server auditor, not repeated at root', 'semantic correctness not certified; no Task2 quality score'])
    if not cache_only:
        report.update(audit_features(cap, df, explanations))
        report['checks'] += ['embedding4manifest/currentsource/model/migration pins', 'all1480 text hashes/truncation logic', 'independent nonpickle finitefloat32/unit vectors and740UnicodeIDs']
        report['limitations'] += ['tokenizer counts and12 sampled encoder forwards checked on server, not rerun at root; not all1480 forwards reproduced']
    target = RECOVERY / ('root_full_explanation_verification.json' if cache_only else 'root_full_feature_verification.json')
    with target.open('x') as stream:
        stream.write(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


def selftest():
    import struct
    npy, unit_error = npy_helpers()
    def packet(dtype, shape, data):
        header = repr(dict(descr=dtype, fortran_order=False, shape=shape)).encode() + b'\n'
        return b'\x93NUMPY\x01\x00' + struct.pack('<H', len(header)) + header + data
    assert unit_error(npy(packet('<f4', (2, 2), struct.pack('<4f', 1, 0, 0, 1)), (2, 2)), 2, 2) == 0
    assert npy(packet('<U2', (2,), 'A\x00BC'.encode('utf-32-le')), (2,)) == ['A', 'BC']
    value = json.dumps({k: 'A visible concrete source relation.' for k in FIELDS})
    expected = parse(value)
    assert parse('```json\n' + value + '\n```') == parse('```\n' + value + '\n```') == expected
    invalid = [lambda: parse('prefix' + value), lambda: parse('```python\n' + value + '\n```'),
               lambda: parse(value[:-1] + ',"source_object":"duplicate"}'),
               lambda: parse(json.dumps({k: ([] if k == FIELDS[0] else 'text') for k in FIELDS})),
               lambda: parse('```json\n' + value + '\n```\nprose'),
               lambda: npy(packet('|O', (1,), b'1234'), (1,)),
               lambda: npy(packet('<f4', (1,), struct.pack('<f', float('nan'))), (1,)),
               lambda: unit_error([0, 0], 1, 2), lambda: npy(b'invalid', (1,))]
    for function in invalid:
        try:
            function()
        except (AssertionError, ValueError):
            pass
        else:
            raise AssertionError('Invalid fixture accepted')
    with tempfile.TemporaryDirectory() as name:
        try:
            audit_cache(Path(name))
        except FileNotFoundError:
            pass
        else:
            raise AssertionError('Missing complete-cache gate accepted')
    print('PASS plain/fenced5fields, float32/Unicode/unit,9invalid fixtures,missing complete-cache gate; no verified report written')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--selftest', action='store_true'); parser.add_argument('--cache-only', action='store_true')
    args = parser.parse_args()
    selftest() if args.selftest else main(args.cache_only)
