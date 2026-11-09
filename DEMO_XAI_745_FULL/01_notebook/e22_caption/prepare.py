"""Image-only caption inputs: no inference and no target/context in the prompt."""
import argparse
import hashlib
import io
import json
from pathlib import Path

import pandas as pd
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / '04_hasil_eksperimen/e22_caption'
DATA_SHA = 'cba20f8250bcb59481ed2d3d7d5d42fb8242c96a7ba2d11a2cd02ad80862961a'
MODEL = 'google/gemini-3-flash-preview'
MAX_SIDE = 768
PROMPT = """Describe only the visible content of this editorial illustration in English.
Write a compact factual visual inventory of 120-180 words. Identify the main objects,
animals, people, body parts, machines, structures, landscapes and props actually shown.
Describe their shapes, materials, visible condition, actions, physical interactions,
and spatial relationships. Mention unusual combinations or transformations of objects
literally, without explaining what they symbolize. Transcribe clearly legible words
exactly; if text or an object is unclear, state that it is unclear rather than guessing.
Do not infer identities, political events, news context, abstract meanings or categories.
Do not add objects that are not visible. Return only the visual description as plain text.
"""

sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
digest = lambda b: hashlib.sha256(b).hexdigest()


def build_prompt(row):
    # Deliberately ignores all row fields, including original/manual text and labels.
    return PROMPT


def transmitted_image(path):
    with Image.open(path) as source:
        image = source.convert('RGB')
        image.thumbnail((MAX_SIDE, MAX_SIDE), Image.Resampling.LANCZOS)
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        return buffer.getvalue(), list(image.size)


def construct(frame):
    rows = []
    for index, (_, row) in enumerate(frame.iterrows()):
        image_path = ROOT / '05_gambar' / Path(row.image_path).name
        data, size = transmitted_image(image_path)
        rows.append(dict(index=index, sample_id=row.sample_id,
                         image_name=image_path.name, image_sha256=sha(image_path),
                         transmitted_image_sha256=digest(data), image_size=size,
                         prompt=build_prompt(row), prompt_sha256=digest(build_prompt(row).encode())))
    return rows


def main(verify=False):
    csv = ROOT / '03_data/DATASET_740_TASK2_DOMAIN.csv'
    assert sha(csv) == DATA_SHA
    frame = pd.read_csv(csv).fillna('')
    assert len(frame) == 740 and frame.sample_id.is_unique
    rows = construct(frame)
    changed = frame.copy()
    # Change every field except identity/image source, not only the target label.
    for column in changed.columns:
        if column not in ('sample_id', 'image_path'):
            changed[column] = ['UNRELATED_CONTEXT_OR_LABEL'] * len(frame)
    assert rows == construct(changed), 'Caption inputs must be image-only'
    fields = {'index', 'sample_id', 'image_name', 'image_sha256',
              'transmitted_image_sha256', 'image_size', 'prompt', 'prompt_sha256'}
    assert all(set(row) == fields and max(row['image_size']) <= MAX_SIDE for row in rows)
    assert len(set(row['prompt_sha256'] for row in rows)) == 1
    manifest = ''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in rows)
    config = dict(worker_preparation_sha256=sha(Path(__file__)), csv_sha256=DATA_SHA,
                  model=MODEL, samples=740, max_image_side=MAX_SIDE,
                  prompt_sha256=digest(PROMPT.encode()), inputs_sha256=digest(manifest.encode()),
                  target_or_context_provided=False, purpose='image_only_visual_caption_features')
    if verify:
        assert json.loads((OUT / 'config.json').read_text()) == config
        assert (OUT / 'inputs.jsonl').read_text() == manifest
        # Independently decode transmitted PNG and compare dimensions and source IDs.
        for index, record in enumerate(rows):
            assert record['sample_id'] == frame.sample_id.iloc[index] and record['index'] == index
            data, _ = transmitted_image(ROOT / '05_gambar' / record['image_name'])
            with Image.open(io.BytesIO(data)) as image:
                assert image.format == 'PNG' and image.mode == 'RGB'
                assert list(image.size) == record['image_size']
        report = dict(status='preparation_verified', samples=740,
                      config_sha256=sha(OUT / 'config.json'), inputs_sha256=sha(OUT / 'inputs.jsonl'),
                      source_sha256=sha(Path(__file__)), inference_started=False,
                      checks=['original740 and image identities', 'all740 PNG hashes/dimensions reconstructed',
                              'image-only prompt invariant to every nonidentity/nonimage field',
                              'manifest has no target labels or context'],
                      limitations=['no hosted inference or quality result',
                                   'reconstruction shares preparation helper; root independently checks manifest'])
        (OUT / 'preparation_verification.json').write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps(report, indent=2))
    else:
        OUT.mkdir(exist_ok=True)
        assert not (OUT / 'config.json').exists() and not (OUT / 'inputs.jsonl').exists(), 'Audit existing inputs first'
        (OUT / 'inputs.jsonl').write_text(manifest)
        (OUT / 'config.json').write_text(json.dumps(config, indent=2) + '\n')
        print('Prepared image-only caption inputs:', len(rows))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--verify', action='store_true')
    main(parser.parse_args().verify)
