"""Verify complete frozen E15 features and reconstruct label-blind input provenance."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
from prompt import DEFINITIONS, build_prompt

ROOT = Path(__file__).resolve().parents[2]
parser = argparse.ArgumentParser()
parser.add_argument('features', type=Path)
args = parser.parse_args()
folder = args.features
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
csv = ROOT / '03_data/DATASET_740_TASK2_DOMAIN.csv'
assert sha(csv) == 'cba20f8250bcb59481ed2d3d7d5d42fb8242c96a7ba2d11a2cd02ad80862961a'
df = pd.read_csv(csv).fillna('')
assert len(df) == 740 and df.sample_id.is_unique
meta = json.loads((folder / 'meta.json').read_text())
assert meta['status'] == 'complete' and meta['samples'] == 740 and meta['dimension'] == 4096
assert meta['model'] == 'Qwen/Qwen3-VL-8B-Instruct'
assert meta['revision'] == '0c351dd01ed87e9c1b53cbc748cba10e6187ff3b'
assert meta['frozen'] is True and meta['dtype'] == 'float16'
assert meta['max_image_side'] == 384 and meta['max_tokens'] == 2048
assert meta['csv_sha256'] == sha(csv)
assert meta['worker_sha256'] == sha(Path(__file__).with_name('worker.py'))
assert meta['prompt_helper_sha256'] == sha(Path(__file__).with_name('prompt.py'))
assert meta['embeddings_sha256'] == sha(folder / 'embeddings.npz')
assert meta['input_audit_sha256'] == sha(folder / 'input_audit.jsonl')
assert meta['device_map'] and all(str(v) not in ('cpu', 'disk') for v in meta['device_map'].values())
z = np.load(folder / 'embeddings.npz', allow_pickle=False)
assert set(z.files) == {'sample_id', 'last_token', 'tail_text_mean'}
assert np.array_equal(z['sample_id'], df.sample_id.to_numpy())
for name in ('last_token', 'tail_text_mean'):
    assert z[name].shape == (740, 4096) and np.isfinite(z[name]).all()
    assert np.allclose(np.linalg.norm(z[name], axis=1), 1, atol=1e-4)

e01 = ROOT / '04_hasil_eksperimen/e01_vlm/kaggle_full/e01_vlm'
expected = {'deskripsi.jsonl': 'c75e8df3f9b71d6786462f8d0f1187ebe4234fb8dd079924f3f35707ff1b8cd2',
            'zeroshot.jsonl': '10c07b06b13fbbf647f2b1ed12a722d9bff8f97caa6b621430d8bc0429ab38c9'}
sources = []
for name, digest in expected.items():
    assert sha(e01 / name) == digest == meta['e01_hashes'][name]
    rows = [json.loads(line) for line in (e01 / name).read_text().splitlines()]
    lookup = {row['sample_id']: row for row in rows}
    assert len(rows) == len(lookup) == 740 and set(lookup) == set(df.sample_id)
    sources.append([lookup[sid] for sid in df.sample_id])
audit = [json.loads(line) for line in (folder / 'input_audit.jsonl').read_text().splitlines()]
assert len(audit) == 740
classes = sorted(DEFINITIONS)
permuted = df.copy()
permuted['task2_domain_sumber'] = df.task2_domain_sumber.iloc[::-1].to_numpy()
for i, row in enumerate(audit):
    assert row['index'] == i and row['sample_id'] == df.sample_id.iloc[i]
    prompt = build_prompt(i, df, *sources, classes)
    assert prompt == build_prompt(i, permuted, *sources, classes)
    assert row['prompt_sha256'] == hashlib.sha256(prompt.encode()).hexdigest()
    image = ROOT / '05_gambar' / Path(df.image_path.iloc[i]).name
    assert row['image_sha256'] == sha(image)
    assert 1 <= row['tokens'] <= 2048 and 1 <= row['tail_tokens'] <= min(128, row['tokens'])
    assert len(row['token_ids_sha256']) == 64
    assert all(c in '0123456789abcdef' for c in row['token_ids_sha256'])
smoke = json.loads((folder / 'smoke.json').read_text())
assert smoke['status'] == 'verified' and smoke['samples'] == 12 and smoke['dimension'] == 4096
assert smoke['frozen'] and smoke['finite'] and smoke['unit_norm']
assert smoke['projected_inference_seconds'] <= 2100
result = {'status': 'verified', 'samples': 740,
          'checks': ['pinned original data/model/source/input hashes',
                     '740 aligned finite unit-norm vectors for both 4096-dimensional pools',
                     '740 prompt hashes reconstructed, invariant under target permutation',
                     '740 original image hashes and index/ID alignment',
                     'token bounds and digest format; tokenization not independently reproduced'],
          'verifier_sha256': sha(Path(__file__)),
          'sha256': {name: sha(folder / name) for name in
                     ('meta.json', 'smoke.json', 'embeddings.npz', 'input_audit.jsonl')}}
(folder / 'verification.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
