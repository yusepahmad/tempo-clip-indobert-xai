"""Frozen offline BGE-M3 CPU features from audited grounded source/target explanations."""
import os
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
os.environ['HF_HOME'] = str(ROOT / '.cache/e22_hf')
for key in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'):
    os.environ[key] = '8'
os.environ['TOKENIZERS_PARALLELISM'] = 'false'
import argparse
import fcntl
import hashlib
import json
import time

import numpy as np
import pandas as pd
import torch
import transformers
from transformers import AutoModel, AutoTokenizer

OUT = ROOT / '04_hasil_eksperimen/e28_embeddings'
CAP = ROOT / '04_hasil_eksperimen/e28_mapping_run'
MODEL = 'BAAI/bge-m3'
REVISION = '5617a9f61b028005a4858fdac845db406aefb181'
DATA_SHA = 'cba20f8250bcb59481ed2d3d7d5d42fb8242c96a7ba2d11a2cd02ad80862961a'
FILES = ['config.json', 'pytorch_model.bin', 'tokenizer.json', 'tokenizer_config.json',
         'special_tokens_map.json', 'sentencepiece.bpe.model']


def sha(path):
    result = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            result.update(block)
    return result.hexdigest()


def save(path, value):
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, indent=2) + '\n')
    temporary.replace(path)


def text_views(df, explanations):
    return dict(interpretation=[r['explanation'] for r in explanations],
                interpretation_context=[r['explanation'] + '\n' + title + ' ' + support
                                 for r, title, support in zip(explanations, df.headline_verified,
                                                            df.supporting_text_verified)])


def inputs():
    verified = json.loads((CAP / 'verification.json').read_text())
    assert verified['status'] == 'verified' and verified['samples'] == 740
    assert verified['verifier_sha256'] == sha(Path(__file__).with_name('verify.py'))
    for name, digest in verified['sha256'].items():
        assert sha(CAP / name) == digest
    for name, digest in verified['prepared_sha256'].items():
        assert sha(ROOT / '04_hasil_eksperimen/e28_mapping' / name) == digest
    csv = ROOT / '03_data/DATASET_740_TASK2_DOMAIN.csv'
    assert sha(csv) == DATA_SHA
    df = pd.read_csv(csv).fillna('')
    rows = [json.loads(line) for line in (CAP / 'sources.jsonl').read_text().splitlines()]
    assert len(df) == len(rows) == 740 and df.sample_id.is_unique
    assert [r['index'] for r in rows] == list(range(740))
    assert [r['sample_id'] for r in rows] == df.sample_id.to_list()
    assert all(isinstance(r['explanation'], str) and len(r['explanation']) >= 40 for r in rows)
    run_config = json.loads((CAP / 'run_config.json').read_text())
    assert run_config['worker_sha256'] == sha(Path(__file__).with_name('run.py'))
    assert run_config['schema_sha256'] == sha(Path(__file__).with_name('schema.py'))
    prepared = ROOT / '04_hasil_eksperimen/e28_mapping'
    assert run_config['preparation_sha256'] == sha(Path(__file__).with_name('prepare.py'))
    assert run_config['config_sha256'] == sha(prepared / 'config.json') and run_config['inputs_sha256'] == sha(prepared / 'inputs.jsonl')
    texts = text_views(df, rows)
    changed = df.copy()
    for column in changed.columns:
        if column not in ('sample_id', 'image_path', 'headline_verified', 'supporting_text_verified'):
            changed[column] = ['UNRELATED_ANNOTATION_OR_LABEL'] * len(df)
    assert texts == text_views(changed, rows)
    signature = dict(explanations_verification_sha256=sha(CAP / 'verification.json'),
                     explanations_sha256=sha(CAP / 'sources.jsonl'), csv_sha256=DATA_SHA,
                     worker_sha256=sha(Path(__file__)), previous_model_preparation_sha256=sha(ROOT / '04_hasil_eksperimen/e22_embeddings/preparation.json'), model=MODEL, revision=REVISION,
                     pooling='CLS then L2', prefix='', dtype='float32', device='cpu', threads=8,
                     max_length=1024, batch=4, views=list(texts),
                     torch=str(torch.__version__), transformers=transformers.__version__)
    return df, texts, signature


def load_model():
    torch.set_num_threads(8); torch.manual_seed(42)
    previous = ROOT / '04_hasil_eksperimen/e22_embeddings/preparation.json'
    assert sha(previous) == '6e3a59e8a002a758135f04eab0cbb1bfbdf2b415b05f95d1ffbf4da523387709'
    preparation = json.loads(previous.read_text())
    assert preparation['status'] == 'model_preparation_verified'
    assert preparation['worker_sha256'] == sha(ROOT / '01_notebook/e22_caption_low/embed.py') == '139fac0c8b4010d13250600707e9d157e459514065c8912b5fee415010091a7f'
    model_meta = preparation['model']
    assert model_meta['model'] == MODEL and model_meta['revision'] == REVISION
    snapshot = ROOT / '.cache/e22_hf/hub/models--BAAI--bge-m3/snapshots' / REVISION
    assert snapshot.is_dir() and set(model_meta['file_sha256']) == set(FILES)
    files = {name: sha(snapshot / name) for name in FILES}
    assert files == model_meta['file_sha256']
    expected_sha = model_meta['official_weight_sha256']
    assert files['pytorch_model.bin'] == expected_sha == 'b5e0ce3470abf5ef3831aa1bd5553b486803e83251590ab7ff35a117cf6aad38'
    tokenizer = AutoTokenizer.from_pretrained(snapshot, local_files_only=True, trust_remote_code=False)
    model = AutoModel.from_pretrained(snapshot, local_files_only=True, trust_remote_code=False,
                                      use_safetensors=False, weights_only=True, dtype=torch.float32).cpu().eval()
    for parameter in model.parameters():
        parameter.requires_grad_(False)
    assert not model.training and all(not p.requires_grad for p in model.parameters())
    return tokenizer, model, dict(model=MODEL, revision=REVISION, file_sha256=files,
                                  official_weight_sha256=expected_sha)


def encode(tokenizer, model, texts):
    result = []
    with torch.inference_mode():
        for start in range(0, len(texts), 4):
            batch = tokenizer(texts[start:start + 4], padding=True, truncation=True,
                              max_length=1024, return_tensors='pt')
            h = model(**batch).last_hidden_state[:, 0].float()
            h = torch.nn.functional.normalize(h, p=2, dim=1)
            assert torch.isfinite(h).all()
            result.append(h.numpy())
    values = np.concatenate(result)
    assert values.shape == (len(texts), 1024)
    assert np.allclose(np.linalg.norm(values, axis=1), 1, atol=1e-5)
    return values


def main(prepare_only):
    # Full gate runs before downloading/loading a model or writing feature outputs.
    loaded = None if prepare_only else inputs()
    OUT.mkdir(exist_ok=True)
    lock = (OUT / 'run.lock').open('a'); fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    tokenizer, model, model_meta = load_model()
    probes = ['A red bicycle stands beside a stone wall.', 'A bird rests on a branch.',
              'A small boat floats on a river.', 'A mechanical wheel turns beside a pipe.']
    first = encode(tokenizer, model, probes)
    assert np.allclose(first, encode(tokenizer, model, probes), rtol=0, atol=1e-6)
    assert np.allclose(first[:1], encode(tokenizer, model, probes[:1]), rtol=0, atol=1e-5)
    if prepare_only:
        save(OUT / 'preparation.json', dict(status='model_preparation_verified', model=model_meta,
             worker_sha256=sha(Path(__file__)), previous_model_preparation_sha256=sha(ROOT / '04_hasil_eksperimen/e22_embeddings/preparation.json'), synthetic_samples=4, device='cpu', dtype='float32',
             torch=str(torch.__version__), transformers=transformers.__version__,
             checks=['previously official-audited revision/weight/snapshot hashes, offline local loading', 'frozen CLS1024 finite unit vectors',
                     'repeatability and single-vs-batch agreement'], full_embedding_started=False))
        print('MODEL PREPARATION VERIFIED', flush=True)
        return
    df, texts, signature = loaded
    signature['model_snapshot'] = model_meta
    protocol = OUT / 'protocol.json'
    if protocol.exists():
        assert json.loads(protocol.read_text()) == signature
    else:
        save(protocol, signature)
    assert not (OUT / 'embeddings.npz').exists(), 'Audit existing features; no automatic overwrite'
    audit, vectors, seconds = [], {}, {}
    for name, items in texts.items():
        for i, text in enumerate(items):
            length = len(tokenizer.encode(text, add_special_tokens=True, truncation=False))
            audit.append(dict(view=name, index=i, sample_id=df.sample_id.iloc[i],
                              text_sha256=hashlib.sha256(text.encode()).hexdigest(),
                              untruncated_tokens=length, truncated=length > 1024))
        started = time.monotonic(); vectors[name] = encode(tokenizer, model, items)
        seconds[name] = time.monotonic() - started
        print('Encoded', name, 740, seconds[name], flush=True)
    (OUT / 'input_audit.jsonl').write_text(''.join(json.dumps(r) + '\n' for r in audit))
    np.savez_compressed(OUT / 'embeddings.npz', sample_id=df.sample_id.to_numpy(dtype=str), **vectors)
    save(OUT / 'meta.json', dict(status='complete', samples=740, dimension=1024, signature=signature,
         embeddings_sha256=sha(OUT / 'embeddings.npz'), input_audit_sha256=sha(OUT / 'input_audit.jsonl'),
         seconds_by_view=seconds, truncated_by_view={name: sum(r['truncated'] for r in audit if r['view'] == name)
                                                    for name in texts}))
    print('EMBEDDINGS COMPLETE; audit required', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--prepare-only', action='store_true')
    main(parser.parse_args().prepare_only)
