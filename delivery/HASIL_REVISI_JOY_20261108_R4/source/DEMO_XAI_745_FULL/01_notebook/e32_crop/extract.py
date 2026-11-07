"""Pinned frozen image-only SigLIP2 features; no hosted inference or training."""
import os
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
os.environ['HF_HOME'] = str(ROOT / '.cache/e23_hf')
for key in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'):
    os.environ[key] = '8'
import fcntl
import hashlib
import json
import time
import numpy as np
import pandas as pd
from PIL import Image
import torch
import transformers
from transformers import AutoModel, AutoImageProcessor
import argparse

OUT = ROOT / '04_hasil_eksperimen/e32_crop'
MODEL = 'google/siglip2-base-patch16-384'
REVISION = 'f775b65a79762255128c981547af89addcfe0f88'
WEIGHT_SHA = 'ed72c0ace85020ae610fc817c2538b9cae5a477b012a50859c60af5b3ad30857'
DATA_SHA = 'cba20f8250bcb59481ed2d3d7d5d42fb8242c96a7ba2d11a2cd02ad80862961a'
FILES = ['config.json', 'preprocessor_config.json', 'model.safetensors']


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def save(path, value):
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, indent=2) + '\n'); temporary.replace(path)


def image_inputs(df):
    return [(sid, Path(path).name) for sid, path in zip(df.sample_id, df.image_path)]


def inputs():
    csv = ROOT / '03_data/DATASET_740_TASK2_DOMAIN.csv'
    assert sha(csv) == DATA_SHA
    df = pd.read_csv(csv).fillna('')
    assert len(df) == 740 and df.sample_id.is_unique
    selected = image_inputs(df)
    changed = df.copy()
    for column in changed.columns:
        if column not in ('sample_id', 'image_path'):
            changed[column] = ['UNRELATED_CONTEXT_OR_LABEL'] * len(df)
    assert selected == image_inputs(changed)
    assert all((ROOT / '05_gambar' / name).is_file() for _, name in selected)
    return df, selected


def load_model():
    torch.set_num_threads(8); torch.manual_seed(42)
    snapshot = ROOT / '.cache/e23_hf/hub/models--google--siglip2-base-patch16-384/snapshots' / REVISION
    expected = {'config.json':'b1b2481aa448d0cd29001bcf5244e72fa8f916dd8348bd18abf9e5533105b96c',
                'preprocessor_config.json':'fb2817d3523ca3b666c859f15320c7138416bc38ffc515e2963f78c868c51c90',
                'model.safetensors':WEIGHT_SHA}
    hashes = {name:sha(snapshot/name) for name in FILES}
    assert hashes == expected
    processor = AutoImageProcessor.from_pretrained(snapshot, use_fast=False, local_files_only=True, trust_remote_code=False)
    model = AutoModel.from_pretrained(snapshot, use_safetensors=True, local_files_only=True,
                                      trust_remote_code=False, dtype=torch.float32).cpu().eval()
    for parameter in model.parameters():
        parameter.requires_grad_(False)
    assert not model.training and all(not p.requires_grad for p in model.parameters())
    return processor, model, dict(model=MODEL, revision=REVISION, file_sha256=hashes,
                                  weight_sha256=WEIGHT_SHA, processor='AutoImageProcessor use_fast=False')


def crop_box(size):
    w,h=size
    return (int(.05*w),int(.12*h),int(.95*w),int(.93*h))


def pixels(processor, images):
    cropped=[image.crop(crop_box(image.size)) for image in images]
    values = processor(images=cropped, return_tensors='pt')['pixel_values']
    assert values.shape == (len(images), 3, 384, 384) and values.dtype == torch.float32
    assert torch.isfinite(values).all()
    return values


def encode(model, values):
    with torch.inference_mode():
        output = model.get_image_features(pixel_values=values, return_dict=True)
        features = torch.nn.functional.normalize(output.pooler_output.float(), p=2, dim=1).numpy()
    assert features.shape == (len(values), 768) and np.isfinite(features).all()
    assert np.allclose(np.linalg.norm(features, axis=1), 1, atol=1e-5)
    return features


def main(prepare_only=False):
    df, selected = inputs()
    OUT.mkdir(exist_ok=True)
    lock = (OUT / 'run.lock').open('a'); fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    assert not (OUT / 'embeddings.npz').exists(), 'Existing features need audit; no overwrite'
    processor, model, model_meta = load_model()
    synthetic = [Image.new('RGB', (400 + i * 10, 300), color) for i, color in
                 enumerate(('red', 'green', 'blue', 'yellow'))]
    values = pixels(processor, synthetic); first = encode(model, values)
    assert np.allclose(first, encode(model, values), rtol=0, atol=1e-6)
    assert np.allclose(first[:1], encode(model, values[:1]), rtol=0, atol=1e-5)
    began=time.monotonic()
    real=[]
    for sid,name in selected[:4]:
        with Image.open(ROOT/'05_gambar'/name) as image:real.append(image.convert('RGB'))
    probe=encode(model,pixels(processor,real))
    smoke_seconds=time.monotonic()-began
    estimate=smoke_seconds/4*740*1.5
    assert estimate<3600
    prep=dict(status='verified',synthetic_samples=4,source_sha256=sha(Path(__file__)),model_snapshot=model_meta,
              real_smoke_samples=4,real_smoke_seconds=smoke_seconds,conservative_740_seconds=estimate,
              checks=['offline official E23 snapshot3SHA','frozen pooler768 finite/unit','repeat/singlebatch','actual4image smoke/runtime <1h'],
              crop_fractions=[.05,.12,.95,.93],quality_score=None,inference_requests=0)
    save(OUT/'preparation.json',prep)
    if prepare_only:
        print(json.dumps(prep,indent=2),flush=True);return
    signature = dict(worker_sha256=sha(Path(__file__)), csv_sha256=DATA_SHA, model_snapshot=model_meta,
                     device='cpu', dtype='float32', threads=8, batch=4, image_size=384,
                     pooling='get_image_features.pooler_output then L2', crop_fractions=[.05,.12,.95,.93], input_fields=['sample_id', 'image_path'],
                     torch=str(torch.__version__), transformers=transformers.__version__)
    protocol = OUT / 'protocol.json'
    if protocol.exists():
        assert json.loads(protocol.read_text()) == signature
    else:
        save(protocol, signature)
    started = time.monotonic(); audit = []; batches = []
    for start in range(0, 740, 4):
        images = []
        for sid, name in selected[start:start + 4]:
            with Image.open(ROOT / '05_gambar' / name) as image:
                images.append(image.convert('RGB'))
        processed = pixels(processor, images)
        for offset, (sid, name) in enumerate(selected[start:start + 4]):
            audit.append(dict(index=start + offset, sample_id=sid, image_name=name,
                              image_sha256=sha(ROOT / '05_gambar' / name),
                              original_size=list(images[offset].size),crop_box=list(crop_box(images[offset].size)),
                              pixel_sha256=hashlib.sha256(processed[offset].numpy().tobytes()).hexdigest()))
        batches.append(encode(model, processed))
        if (start + 4) % 40 == 0:
            print('Encoded image-only', start + 4, '/740', flush=True)
    vectors = np.concatenate(batches)
    assert vectors.shape == (740, 768) and len(audit) == 740
    (OUT / 'input_audit.jsonl').write_text(''.join(json.dumps(row) + '\n' for row in audit))
    np.savez_compressed(OUT / 'embeddings.npz', sample_id=df.sample_id.to_numpy(dtype=str), image=vectors)
    save(OUT / 'meta.json', dict(status='complete', samples=740, dimension=768, signature=signature,
         input_audit_sha256=sha(OUT / 'input_audit.jsonl'), embeddings_sha256=sha(OUT / 'embeddings.npz'),
         seconds=time.monotonic() - started))
    print('FEATURES COMPLETE; audit required', flush=True)


if __name__ == '__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--prepare-only',action='store_true')
    main(parser.parse_args().prepare_only)
