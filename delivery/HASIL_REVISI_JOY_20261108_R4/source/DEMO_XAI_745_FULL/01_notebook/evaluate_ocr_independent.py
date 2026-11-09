#!/usr/bin/env python3
"""Bekukan lalu evaluasi OCR pada 60 sampul yang tidak dipakai diagnosis lama.

Urutan wajib:
  python evaluate_ocr_independent.py freeze
  python evaluate_ocr_independent.py run

`freeze` hanya membaca dataset/gambar dan menulis ground truth + hash input.
`run` menolak manifest yang berubah, baru kemudian menjalankan OCR produksi.
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
import sys
import time
import unicodedata
from collections import defaultdict
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "04_hasil_eksperimen" / "revisi_week3" / "ocr_independent"
MANIFEST = OUT / "manifest_frozen.json"
MANIFEST_SHA = OUT / "manifest_frozen.sha256"
RESULT = OUT / "results.json"
OLD_MANIFEST = ROOT / "04_hasil_eksperimen" / "revisi_week3" / "ocr_manifest.json"
DATASET = ROOT / "03_data" / "DATASET_740_TASK2_DOMAIN.csv"
SEED = "tempo-ocr-independent-v1-2026-10-17"
PER_CLASS = 6


def canonical_bytes(value) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def image_path(sample_id: str) -> Path:
    for ext in (".jpg", ".jpeg", ".png", ".webp"):
        p = ROOT / "05_gambar" / f"{sample_id}{ext}"
        if p.exists():
            return p
    raise FileNotFoundError(sample_id)


def normalize(value: str) -> str:
    value = unicodedata.normalize("NFKC", value or "").upper()
    value = re.sub(r"[^0-9A-ZÀ-ÖØ-Ý\s]", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def edit_distance(a: str, b: str) -> int:
    previous = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        current = [i]
        for j, y in enumerate(b, 1):
            current.append(min(current[-1] + 1, previous[j] + 1,
                               previous[j - 1] + (x != y)))
        previous = current
    return previous[-1]


def token_f1(truth: str, prediction: str) -> float:
    truth_tokens = normalize(truth).split()
    prediction_tokens = normalize(prediction).split()
    if not truth_tokens and not prediction_tokens:
        return 1.0
    if not truth_tokens or not prediction_tokens:
        return 0.0
    remaining = list(prediction_tokens)
    match = 0
    for token in truth_tokens:
        if token in remaining:
            remaining.remove(token)
            match += 1
    precision = match / len(prediction_tokens)
    recall = match / len(truth_tokens)
    return 2 * precision * recall / (precision + recall) if match else 0.0


def freeze() -> None:
    if MANIFEST.exists() or RESULT.exists():
        raise SystemExit("Manifest/output sudah ada; hapus hanya melalui plan baru bila ingin membekukan ulang.")
    rows = list(csv.DictReader(DATASET.open(encoding="utf-8-sig")))
    old = json.loads(OLD_MANIFEST.read_text(encoding="utf-8"))
    excluded = {item["sample_id"] for item in old}
    groups = defaultdict(list)
    for row in rows:
        if row["sample_id"] in excluded:
            continue
        key = hashlib.sha256(f"{SEED}:{row['sample_id']}".encode()).hexdigest()
        groups[row["task1_issue"]].append((key, row))
    selected = []
    for task in sorted(groups):
        candidates = sorted(groups[task])
        if len(candidates) < PER_CLASS:
            raise RuntimeError(f"Kelas {task} hanya memiliki {len(candidates)} kandidat")
        selected.extend(row for _, row in candidates[:PER_CLASS])
    selected.sort(key=lambda row: row["sample_id"])
    items = []
    for row in selected:
        image = image_path(row["sample_id"])
        items.append({
            "sample_id": row["sample_id"],
            "task1_issue": row["task1_issue"],
            "headline_truth": row["headline_verified"],
            "supporting_truth": row["supporting_text_verified"],
            "image": str(image.relative_to(ROOT)),
            "image_sha256": sha256_file(image),
        })
    manifest = {
        "schema": "tempo-ocr-independent-v1",
        "frozen_at": "2026-10-17",
        "selection": {
            "seed": SEED,
            "rule": "exclude prior 30 diagnosis IDs; SHA-256 rank within Task1; first 6 per class",
            "per_task1_class": PER_CLASS,
            "count": len(items),
            "excluded_prior_ids": len(excluded),
        },
        "dataset_sha256": sha256_file(DATASET),
        "prior_manifest_sha256": sha256_file(OLD_MANIFEST),
        "items": items,
    }
    payload = canonical_bytes(manifest)
    OUT.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_bytes(payload)
    MANIFEST_SHA.write_text(f"{sha256_bytes(payload)}  {MANIFEST.name}\n", encoding="ascii")
    print(json.dumps({"status": "frozen", "count": len(items),
                      "manifest_sha256": sha256_bytes(payload)}, indent=2))


def summarize(rows: list[dict], truth_key: str, prediction_key: str) -> dict:
    usable = [row for row in rows if normalize(row[truth_key])]
    exact = [normalize(row[truth_key]) == normalize(row[prediction_key]) for row in usable]
    cer = [edit_distance(normalize(row[truth_key]), normalize(row[prediction_key])) /
           max(len(normalize(row[truth_key])), 1) for row in usable]
    f1 = [token_f1(row[truth_key], row[prediction_key]) for row in usable]
    return {
        "count_with_truth": len(usable),
        "exact_correct": int(sum(exact)),
        "exact_accuracy": float(np.mean(exact)) if exact else None,
        "mean_character_error_rate": float(np.mean(cer)) if cer else None,
        "median_character_error_rate": float(np.median(cer)) if cer else None,
        "mean_token_f1": float(np.mean(f1)) if f1 else None,
    }


def run() -> None:
    if not MANIFEST.exists() or not MANIFEST_SHA.exists():
        raise SystemExit("Jalankan mode freeze lebih dulu.")
    manifest_bytes = MANIFEST.read_bytes()
    expected = MANIFEST_SHA.read_text(encoding="ascii").split()[0]
    actual = sha256_bytes(manifest_bytes)
    if expected != actual:
        raise SystemExit(f"Manifest berubah: expected {expected}, actual {actual}")
    if RESULT.exists():
        raise SystemExit("Output sudah ada; evaluasi tidak boleh ditimpa.")
    manifest = json.loads(manifest_bytes)
    prior_ids = {item["sample_id"] for item in json.loads(OLD_MANIFEST.read_text(encoding="utf-8"))}
    selected_ids = {item["sample_id"] for item in manifest["items"]}
    overlap = sorted(prior_ids & selected_ids)
    if overlap:
        raise SystemExit(f"Overlap dengan diagnosis lama: {overlap}")

    sys.path.insert(0, str(ROOT / "02_web_demo"))
    import ocr_headline
    torch.set_num_threads(4)
    selector_sha = sha256_file(ROOT / "02_web_demo" / "ocr_headline.py")
    results = []
    for index, item in enumerate(manifest["items"], 1):
        image = ROOT / item["image"]
        if sha256_file(image) != item["image_sha256"]:
            raise RuntimeError(f"Hash gambar berubah: {item['sample_id']}")
        started = time.perf_counter()
        output = ocr_headline.baca(image)
        elapsed = time.perf_counter() - started
        result = {
            **item,
            "headline_prediction": output.get("headline", ""),
            "supporting_prediction": output.get("pendukung", ""),
            "seconds": elapsed,
            "ocr": output,
        }
        results.append(result)
        print(f"[{index:02d}/{len(manifest['items'])}] {item['sample_id']} "
              f"headline_exact={normalize(item['headline_truth']) == normalize(result['headline_prediction'])} "
              f"seconds={elapsed:.2f}", flush=True)
    report = {
        "schema": "tempo-ocr-independent-results-v1",
        "manifest_sha256": actual,
        "selector_sha256": selector_sha,
        "engine": ocr_headline.mesin_aktif(),
        "overlap_with_prior_diagnosis": overlap,
        "headline": summarize(results, "headline_truth", "headline_prediction"),
        "supporting_proxy": summarize(results, "supporting_truth", "supporting_prediction"),
        "supporting_caveat": (
            "supporting_text_verified adalah anotasi konten dataset dan belum dibuktikan sebagai "
            "transkripsi lengkap seluruh teks visual; metrik ini proxy, bukan acceptance OCR penuh."
        ),
        "latency_seconds": {
            "median": float(np.median([row["seconds"] for row in results])),
            "p95": float(np.percentile([row["seconds"] for row in results], 95)),
            "total": float(sum(row["seconds"] for row in results)),
        },
        "results": results,
    }
    RESULT.write_bytes(canonical_bytes(report))
    print(json.dumps({k: report[k] for k in ("headline", "supporting_proxy", "latency_seconds")},
                     ensure_ascii=False, indent=2))


def verify() -> None:
    manifest_bytes = MANIFEST.read_bytes()
    expected = MANIFEST_SHA.read_text(encoding="ascii").split()[0]
    assert sha256_bytes(manifest_bytes) == expected
    manifest = json.loads(manifest_bytes)
    report = json.loads(RESULT.read_text(encoding="utf-8"))
    assert report["manifest_sha256"] == expected
    prior_ids = {item["sample_id"] for item in json.loads(OLD_MANIFEST.read_text(encoding="utf-8"))}
    selected_ids = {item["sample_id"] for item in manifest["items"]}
    assert len(selected_ids) == 60 and not (prior_ids & selected_ids)
    assert {row["sample_id"] for row in report["results"]} == selected_ids
    assert report["selector_sha256"] == sha256_file(ROOT / "02_web_demo" / "ocr_headline.py")
    headline = summarize(report["results"], "headline_truth", "headline_prediction")
    supporting = summarize(report["results"], "supporting_truth", "supporting_prediction")
    assert headline == report["headline"]
    assert supporting == report["supporting_proxy"]
    for item in manifest["items"]:
        assert sha256_file(ROOT / item["image"]) == item["image_sha256"]
    print(json.dumps({"status": "verified", "count": len(selected_ids),
                      "overlap": 0, "headline": headline,
                      "supporting_proxy": supporting}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in {"freeze", "run", "verify"}:
        raise SystemExit("Usage: evaluate_ocr_independent.py freeze|run|verify")
    {"freeze": freeze, "run": run, "verify": verify}[sys.argv[1]]()
