"""Import a complete raw prefix without repeating any inference or editing its origin."""
import json
from pathlib import Path
from run import ROOT, OUT, load, save, sha
from schema import decode


def main():
    rows, config = load()
    origin = ROOT / '04_hasil_eksperimen/e28_mapping_run'
    assert not OUT.exists(), 'Audit destination before any migration/resume'
    original_config = json.loads((origin / 'run_config.json').read_text())
    assert original_config['model'] == config['model'] and original_config['inputs_sha256'] == config['inputs_sha256']
    assert original_config['budget_usd'] == config['budget_usd'] == 1.8
    copied = []
    total = 0.0
    # Validate the complete source prefix before creating the destination.
    for i in range(24):
        path = origin / 'records' / f'{i:04d}.json'
        record = json.loads(path.read_text())
        row = rows[i]
        assert sha(path) == config['origin_record_sha256'][path.name]
        assert record['status'] == 'complete' and record['http_status'] == 200
        assert record['run_config_sha256'] == config['origin_run_config_sha256']
        for key in ('index', 'sample_id', 'prompt_sha256', 'image_sha256', 'transmitted_image_sha256', 'image_size'):
            assert record[key] == row[key]
        response = record['response']
        assert response['model'] == config['model'] and len(response['choices']) == 1
        choice = response['choices'][0]
        assert choice['finish_reason'] == record['finish_reason'] == 'stop'
        fields, explanation = decode(choice['message']['content'], 'stop')
        usage = response['usage']
        cost = usage['cost']
        value = (cost['input_tokens_cost_nanodollars'] + cost['output_tokens_cost_nanodollars']) / 1e9
        assert abs(value - record['cost_usd']) < 1e-12 and 0 <= value <= .05
        assert usage['prompt_tokens'] > 0 and usage['completion_tokens'] >= 0
        assert len(record['quota_before']) == len(record['quota_after']) == 2
        for before, after in zip(record['quota_before'], record['quota_after']):
            assert before['period'] == after['period'] and abs(after['used'] - before['used'] - value) < 1e-6
        migrated = dict(record, fields=fields, explanation=explanation, usable=True,
            migration_origin=dict(record_sha256=sha(path), run_config_sha256=config['origin_run_config_sha256']))
        copied.append(migrated)
        total += value
    assert total < config['budget_usd']
    OUT.mkdir()
    (OUT / 'records').mkdir()
    save(OUT / 'run_config.json', config)
    for i, record in enumerate(copied):
        record['run_config_sha256'] = sha(OUT / 'run_config.json')
        save(OUT / 'records' / f'{i:04d}.json', record)
    for name, digest in config['origin_record_sha256'].items():
        assert sha(origin / 'records' / name) == digest
    save(OUT / 'progress.json', dict(status='migrated_prefix_pending_root_audit', completed=24,
                                   samples_required=740, cost_usd=total, inference_requests_added=0))
    save(OUT / 'migration.json', dict(status='migrated_pending_independent_audit', samples=24,
        cost_usd=total, inference_requests_added=0, source_sha256=sha(Path(__file__)),
        origin_run_config_sha256=config['origin_run_config_sha256'],
        origin_record_sha256=config['origin_record_sha256'],
        sha256={'run_config.json': sha(OUT / 'run_config.json'),
                **{'records/' + f'{i:04d}.json': sha(OUT / 'records' / f'{i:04d}.json') for i in range(24)}}))
    print('Migrated24 raw responses; zero new inference requests', flush=True)


if __name__ == '__main__':
    main()
