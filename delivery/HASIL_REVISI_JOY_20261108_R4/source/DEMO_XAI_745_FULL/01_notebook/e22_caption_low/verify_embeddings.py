"""All-input/tensor integrity and explicitly sampled frozen embedding reproduction."""
import hashlib
import json
from pathlib import Path
import numpy as np
from embed import OUT, inputs, load_model, encode, sha, save


def main():
    df, texts, signature = inputs()
    meta = json.loads((OUT / 'meta.json').read_text())
    assert meta['status'] == 'complete' and meta['samples'] == 740 and meta['dimension'] == 1024
    assert meta['embeddings_sha256'] == sha(OUT / 'embeddings.npz')
    assert meta['input_audit_sha256'] == sha(OUT / 'input_audit.jsonl')
    tokenizer, model, model_meta = load_model()
    signature['model_snapshot'] = model_meta
    assert meta['signature'] == signature == json.loads((OUT / 'protocol.json').read_text())
    arrays = np.load(OUT / 'embeddings.npz', allow_pickle=False)
    assert set(arrays.files) == {'sample_id', *texts}
    assert arrays['sample_id'].tolist() == df.sample_id.to_list()
    audit = [json.loads(line) for line in (OUT / 'input_audit.jsonl').read_text().splitlines()]
    expected = []
    indices = [0, 1, 37, 123, 369, 739]
    errors = {}
    for name, values in texts.items():
        matrix = arrays[name]
        assert matrix.shape == (740, 1024) and matrix.dtype == np.float32 and np.isfinite(matrix).all()
        assert np.allclose(np.linalg.norm(matrix, axis=1), 1, atol=1e-5)
        for i, text in enumerate(values):
            length = len(tokenizer.encode(text, add_special_tokens=True, truncation=False))
            expected.append(dict(view=name, index=i, sample_id=df.sample_id.iloc[i],
                                 text_sha256=hashlib.sha256(text.encode()).hexdigest(),
                                 untruncated_tokens=length, truncated=length > 1024))
        reproduced = encode(tokenizer, model, [values[i] for i in indices])
        assert np.allclose(reproduced, matrix[indices], rtol=0, atol=1e-5)
        errors[name] = float(np.max(np.abs(reproduced - matrix[indices])))
    assert audit == expected
    assert meta['truncated_by_view'] == {name: sum(r['truncated'] for r in audit if r['view'] == name) for name in texts}
    files = ['embeddings.npz', 'meta.json', 'protocol.json', 'input_audit.jsonl']
    report = dict(status='verified', samples=740, dimension=1024, verifier_sha256=sha(Path(__file__)),
                  sampled_indices=indices, maximum_absolute_errors=errors,
                  sha256={name: sha(OUT / name) for name in files},
                  checks=['fully audited caption740/original inputs and source hashes',
                          'all1480 text/token/truncation audit rows reconstructed',
                          'pinned official model/snapshot hashes and frozen CLS pooling',
                          'all arrays aligned finite float32 unit vectors',
                          'six predeclared indices per view reproduced within1e-5'],
                  limitations=['only12 embeddings independently reproduced, not all1480', 'no Task2 quality score'])
    save(OUT / 'verification.json', report); print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
