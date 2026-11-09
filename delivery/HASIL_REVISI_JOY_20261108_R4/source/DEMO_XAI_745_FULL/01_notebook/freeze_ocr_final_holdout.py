#!/usr/bin/env python3
"""Freeze the final OCR holdout before any post-decision OCR tuning."""
import csv, hashlib, json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "03_data/DATASET_740_TASK2_DOMAIN.csv"
OLD = ROOT / "04_hasil_eksperimen/revisi_week3/ocr_manifest.json"
DEV = ROOT / "04_hasil_eksperimen/revisi_week3/ocr_independent/manifest_frozen.json"
OUT = ROOT / "04_hasil_eksperimen/revisi_week3/ocr_final_holdout"
MANIFEST = OUT / "manifest_frozen.json"
SHA = OUT / "manifest_frozen.sha256"
SEED = "tempo-ocr-final-holdout-v1-2026-10-17"
PER_CLASS = 8


def file_sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def image_path(sample_id):
    for ext in (".jpg", ".jpeg", ".png", ".webp"):
        path = ROOT / "05_gambar" / f"{sample_id}{ext}"
        if path.exists(): return path
    raise FileNotFoundError(sample_id)


if MANIFEST.exists():
    raise SystemExit("Final holdout sudah dibekukan; tidak boleh ditimpa.")
rows = list(csv.DictReader(DATA.open(encoding="utf-8-sig")))
excluded = {x["sample_id"] for x in json.loads(OLD.read_text())}
excluded |= {x["sample_id"] for x in json.loads(DEV.read_text())["items"]}
groups = defaultdict(list)
for row in rows:
    if row["sample_id"] in excluded: continue
    rank = hashlib.sha256(f"{SEED}:{row['sample_id']}".encode()).hexdigest()
    groups[row["task1_issue"]].append((rank, row))
items = []
for task in sorted(groups):
    chosen = sorted(groups[task])[:PER_CLASS]
    assert len(chosen) == PER_CLASS, task
    for _, row in chosen:
        image = image_path(row["sample_id"])
        items.append({
            "sample_id": row["sample_id"], "task1_issue": task,
            "headline_truth": row["headline_verified"],
            "supporting_truth": row["supporting_text_verified"],
            "image": str(image.relative_to(ROOT)), "image_sha256": file_sha(image),
        })
items.sort(key=lambda x: x["sample_id"])
manifest = {
    "schema": "tempo-ocr-final-holdout-v1", "frozen_at": "2026-10-17",
    "do_not_run_until_candidate_locked": True,
    "selection": {"seed": SEED, "rule": "exclude old30+dev60; SHA-256 rank within Task1; first 8 per class",
                  "per_task1_class": PER_CLASS, "count": len(items), "excluded_development_ids": len(excluded)},
    "dataset_sha256": file_sha(DATA), "old_manifest_sha256": file_sha(OLD),
    "development_manifest_sha256": file_sha(DEV), "items": items,
}
payload = (json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()
OUT.mkdir(parents=True, exist_ok=True); MANIFEST.write_bytes(payload)
digest = hashlib.sha256(payload).hexdigest(); SHA.write_text(f"{digest}  {MANIFEST.name}\n")
print(json.dumps({"status":"frozen-not-run","count":len(items),"excluded":len(excluded),"sha256":digest},indent=2))
