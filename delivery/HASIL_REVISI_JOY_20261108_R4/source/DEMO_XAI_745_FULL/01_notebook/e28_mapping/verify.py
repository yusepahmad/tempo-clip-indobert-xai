"""Reconstruct grounded source/target requests and audit strict JSON/raw outputs/quota."""
import argparse
import hashlib
import io
import json
from pathlib import Path

import pandas as pd
from PIL import Image
from run import ROOT, OUT, BASE, load, save, sha
from prepare import build_prompt, context
from schema import FIELDS


def main(partial=False):
    inputs, expected = load()
    config = json.loads((OUT / 'run_config.json').read_text())
    assert config == expected
    csv = ROOT / '03_data/DATASET_740_TASK2_DOMAIN.csv'
    df = pd.read_csv(csv).fillna('')
    prepared = json.loads((BASE / 'config.json').read_text())
    assert sha(csv) == prepared['csv_sha256'] and len(df) == 740 and df.sample_id.is_unique
    files = sorted((OUT / 'records').glob('*.json'))
    n = len(files)
    assert (0 < n <= 740) if partial else n == 740
    assert [p.name for p in files] == [f'{i:04d}.json' for i in range(n)]
    explanations, costs, hashes = [], [], {}
    for i, path in enumerate(files):
        record = json.loads(path.read_text()); row = inputs[i]
        assert record['status'] == 'complete' and record['index'] == i
        assert record['sample_id'] == row['sample_id'] == df.sample_id.iloc[i]
        assert record['run_config_sha256'] == sha(OUT / 'run_config.json') and record['model'] == config['model']
        assert row['original_context'] == context(df.iloc[i]) and row['prompt'] == build_prompt(df.iloc[i])
        assert record['prompt_sha256'] == row['prompt_sha256'] == hashlib.sha256(row['prompt'].encode()).hexdigest()
        image_path = ROOT / '05_gambar' / Path(df.image_path.iloc[i]).name
        assert record['image_sha256'] == row['image_sha256'] == sha(image_path)
        with Image.open(image_path) as source:
            image = source.convert('RGB'); image.thumbnail((768, 768), Image.Resampling.LANCZOS)
            buffer = io.BytesIO(); image.save(buffer, format='PNG')
        assert list(image.size) == record['image_size'] == row['image_size']
        assert hashlib.sha256(buffer.getvalue()).hexdigest() == record['transmitted_image_sha256'] == row['transmitted_image_sha256']
        result = record['response']
        assert record['http_status'] == 200 and result['model'] == config['model'] and len(result['choices']) == 1
        content = result['choices'][0]['message'].get('content') or ''
        assert isinstance(content, str) and len(content.strip()) >= 40
        assert content.lstrip().startswith('{') and content.rstrip().endswith('}')
        pairs = json.loads(content, object_pairs_hook=lambda pairs: pairs)
        assert isinstance(pairs, list) and len(pairs) == 5 and len({key for key, _ in pairs}) == 5
        parsed = dict(pairs)
        assert set(parsed) == set(FIELDS) and all(isinstance(parsed[key], str) and parsed[key].strip() for key in FIELDS)
        explanation = '\n'.join(key + ': ' + parsed[key].strip() for key in FIELDS)
        assert record['fields'] == parsed and record['explanation'] == explanation
        assert record['finish_reason'] == result['choices'][0].get('finish_reason') == 'stop' and record['usable'] is True
        usage = result['usage']; cost = usage['cost']
        value = (cost['input_tokens_cost_nanodollars'] + cost['output_tokens_cost_nanodollars']) / 1e9
        assert abs(value - record['cost_usd']) < 1e-12 and 0 <= value <= .05
        assert usage['prompt_tokens'] > 0 and usage['completion_tokens'] >= 0
        assert len(record['quota_before']) == len(record['quota_after']) == 2
        for b, a in zip(record['quota_before'], record['quota_after']):
            assert b['period'] == a['period'] and abs(a['used'] - b['used'] - value) < 1e-6 and a['remaining'] >= .10
        costs.append(value); hashes[str(path.relative_to(OUT))] = sha(path)
        explanations.append(dict(index=i, sample_id=row['sample_id'], fields=parsed, explanation=explanation))
    assert sum(costs) <= config['budget_usd'] == 1.80
    for name in ['run_config.json']:
        hashes[name] = sha(OUT / name)
    if not partial:
        (OUT / 'sources.jsonl').write_text(''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in explanations))
        hashes['sources.jsonl'] = sha(OUT / 'sources.jsonl')
    report = dict(status='partial_verified' if partial else 'verified', samples=n, samples_required=740,
                  prepared_sha256={name: sha(BASE / name) for name in ['config.json', 'inputs.jsonl']},
                  cost_usd=sum(costs), verifier_sha256=sha(Path(__file__)), sha256=hashes,
                  checks=['all cached prefix IDs/input/config/source hashes', 'original image RGB PNG768 independently reconstructed',
                          'raw strict5stringJSON/deterministic explanation/stop and all usage/quota deltas/budget'],
                  limitations=['source/target explanation semantic accuracy not independently certified',
                               'no inference reproduction or Task2 quality score'])
    save(OUT / ('partial_verification.json' if partial else 'verification.json'), report)
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--partial', action='store_true')
    main(parser.parse_args().partial)
