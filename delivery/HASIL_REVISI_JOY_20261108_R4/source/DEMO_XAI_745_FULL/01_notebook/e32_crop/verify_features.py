"""Reconstruct all image input hashes; reproduce six predeclared feature vectors."""
import hashlib
import json
from pathlib import Path
import numpy as np
from PIL import Image
from extract import ROOT, OUT, inputs, load_model, pixels, encode, sha, save, crop_box


def main():
    df, selected = inputs()
    meta = json.loads((OUT / 'meta.json').read_text())
    assert meta['status'] == 'complete' and meta['samples'] == 740 and meta['dimension'] == 768
    assert meta['signature']['worker_sha256'] == sha(Path(__file__).with_name('extract.py'))
    assert meta['signature'] == json.loads((OUT / 'protocol.json').read_text())
    assert meta['embeddings_sha256'] == sha(OUT / 'embeddings.npz')
    assert meta['input_audit_sha256'] == sha(OUT / 'input_audit.jsonl')
    processor, model, model_meta = load_model()
    assert model_meta == meta['signature']['model_snapshot']
    arrays = np.load(OUT / 'embeddings.npz', allow_pickle=False)
    assert set(arrays.files) == {'sample_id', 'image'} and arrays['sample_id'].tolist() == df.sample_id.to_list()
    vectors = arrays['image']; assert vectors.shape == (740, 768) and vectors.dtype == np.float32
    assert np.isfinite(vectors).all() and np.allclose(np.linalg.norm(vectors, axis=1), 1, atol=1e-5)
    audit = [json.loads(line) for line in (OUT / 'input_audit.jsonl').read_text().splitlines()]
    assert len(audit) == 740
    indices = [0, 1, 37, 123, 369, 739]; errors = {}
    for start in range(0, 740, 4):
        images = []
        for sid, name in selected[start:start + 4]:
            with Image.open(ROOT / '05_gambar' / name) as image:
                images.append(image.convert('RGB'))
        processed = pixels(processor, images)
        for offset, (sid, name) in enumerate(selected[start:start + 4]):
            i = start + offset
            expected = dict(index=i, sample_id=sid, image_name=name, image_sha256=sha(ROOT / '05_gambar' / name),
                            original_size=list(images[offset].size),crop_box=list(crop_box(images[offset].size)),
                            pixel_sha256=hashlib.sha256(processed[offset].numpy().tobytes()).hexdigest())
            assert audit[i] == expected
            if i in indices:
                reproduced = encode(model, processed[offset:offset + 1])[0]
                assert np.allclose(reproduced, vectors[i], rtol=0, atol=1e-5)
                errors[str(i)] = float(np.max(np.abs(reproduced - vectors[i])))
    assert len(errors) == 6
    files = ['embeddings.npz', 'meta.json', 'protocol.json', 'preparation.json', 'input_audit.jsonl']
    report = dict(status='verified', samples=740, dimension=768, verifier_sha256=sha(Path(__file__)),
                  sampled_indices=indices, maximum_absolute_errors=errors,
                  sha256={name: sha(OUT / name) for name in files},
                  checks=['original740 source/IDs/image-only invariance', 'official model/weight/snapshot pins',
                          'all740 original image/cropbox and processor pixel hashes reconstructed',
                          'aligned finite float32 unit768 features', 'predeclared6 features reproduced tolerance1e-5'],
                  limitations=['only6 forward outputs reproduced, not all740', 'no Task2 score'])
    save(OUT / 'verification.json', report); print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
