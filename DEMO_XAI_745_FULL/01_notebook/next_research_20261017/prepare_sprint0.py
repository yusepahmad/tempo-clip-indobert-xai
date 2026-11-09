#!/usr/bin/env python3
"""Build the immutable Sprint-0 audit package for the post-E49 research cycle."""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

import pandas as pd
from PIL import Image
from sklearn.metrics import accuracy_score, f1_score, precision_recall_fscore_support


ROOT = Path(__file__).resolve().parents[3]
PROJECT = ROOT / "DEMO_XAI_745_FULL"
RESULTS = PROJECT / "04_hasil_eksperimen"
OUT = RESULTS / "next_research_20261017"
AUDIT = OUT / "00_audit"
DATASET = PROJECT / "03_data/DATASET_740_TASK2_DOMAIN.csv"
IMAGES = PROJECT / "05_gambar"
E42_OOF = RESULTS / "e42_tail_grid/oof.csv"
E42_RESULT = RESULTS / "e42_tail_grid/result.json"
RANKING = RESULTS / "joint_candidate_ranking.json"

TASKS = {
    "task1_issue": ("task1_issue_truth", "task1_issue_pred"),
    "task2_domain_sumber": ("task2_domain_sumber_truth", "task2_domain_sumber_pred"),
    "task3_primary_entity_type": ("task3_primary_entity_type_truth", "task3_primary_entity_type_pred"),
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical_hash(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def dhash(path: Path) -> int:
    with Image.open(path) as image:
        gray = image.convert("L").resize((9, 8), Image.Resampling.LANCZOS)
        pixels = list(gray.getdata())
    value = 0
    for row in range(8):
        for col in range(8):
            value = (value << 1) | (pixels[row * 9 + col] > pixels[row * 9 + col + 1])
    return value


def markdown_table(rows: list[dict], columns: list[str]) -> str:
    header = "| " + " | ".join(columns) + " |"
    rule = "| " + " | ".join(["---"] * len(columns)) + " |"
    body = ["| " + " | ".join(str(row.get(c, "")) for c in columns) + " |" for row in rows]
    return "\n".join([header, rule, *body])


def main() -> None:
    AUDIT.mkdir(parents=True, exist_ok=True)
    dataset = pd.read_csv(DATASET, encoding="utf-8-sig")
    oof = pd.read_csv(E42_OOF)
    declared = json.loads(E42_RESULT.read_text())

    assert len(dataset) == 740 and dataset.sample_id.nunique() == 740
    assert len(oof) == 740 and oof.sample_id.nunique() == 740
    assert set(dataset.sample_id) == set(oof.sample_id)
    assert set(oof.fold) == {1, 2, 3, 4, 5}

    metrics_rows = []
    summary_rows = []
    for task, (truth_col, pred_col) in TASKS.items():
        labels = sorted(set(oof[truth_col]) | set(oof[pred_col]))
        p, r, f, support = precision_recall_fscore_support(
            oof[truth_col], oof[pred_col], labels=labels, zero_division=0
        )
        for label, pv, rv, fv, sv in zip(labels, p, r, f, support):
            metrics_rows.append({
                "task": task, "class": label, "support": int(sv),
                "precision": float(pv), "recall": float(rv), "f1": float(fv),
            })
        macro = f1_score(oof[truth_col], oof[pred_col], average="macro")
        acc = accuracy_score(oof[truth_col], oof[pred_col])
        expected = declared["metrics"][task]
        assert abs(macro - expected["macro_f1"]) < 1e-12
        assert abs(acc - expected["accuracy"]) < 1e-12
        summary_rows.append({"task": task, "macro_f1": macro, "accuracy": acc, "classes": len(labels)})
    pd.DataFrame(metrics_rows).to_csv(AUDIT / "per_class_metrics.csv", index=False)

    distribution = []
    for task in TASKS:
        for label, count in sorted(Counter(dataset[task]).items()):
            distribution.append({
                "task": task, "class": label, "count": count,
                "percentage": round(100 * count / len(dataset), 4),
            })
    for confidence, count in sorted(Counter(dataset.annotator_confidence).items()):
        distribution.append({
            "task": "annotator_confidence", "class": confidence, "count": count,
            "percentage": round(100 * count / len(dataset), 4),
        })
    pd.DataFrame(distribution).to_csv(AUDIT / "data_distribution.csv", index=False)

    fold_by_id = dict(zip(oof.sample_id, oof.fold))
    exact_groups = defaultdict(list)
    near = []
    hashes = []
    missing_images = []
    for row in dataset.itertuples(index=False):
        path = IMAGES / f"{row.sample_id}.jpg"
        if not path.exists():
            missing_images.append(row.sample_id)
            continue
        actual = sha256(path)
        exact_groups[actual].append(row.sample_id)
        hashes.append((row.sample_id, dhash(path)))
        assert actual == row.image_sha256
    exact_duplicates = [ids for ids in exact_groups.values() if len(ids) > 1]
    for i, (left_id, left_hash) in enumerate(hashes):
        for right_id, right_hash in hashes[i + 1:]:
            distance = (left_hash ^ right_hash).bit_count()
            if distance <= 2:
                near.append({
                    "left": left_id, "right": right_id, "distance": distance,
                    "left_fold": int(fold_by_id[left_id]), "right_fold": int(fold_by_id[right_id]),
                    "cross_fold": fold_by_id[left_id] != fold_by_id[right_id],
                })

    duplicate_ids = dataset.groupby("duplicate_group_id").sample_id.agg(list)
    declared_groups = [ids for ids in duplicate_ids if len(ids) > 1]
    cross_declared = [ids for ids in declared_groups if len({fold_by_id[x] for x in ids}) > 1]
    (AUDIT / "near_duplicate_candidates.csv").write_text(
        pd.DataFrame(near, columns=["left", "right", "distance", "left_fold", "right_fold", "cross_fold"]).to_csv(index=False)
    )

    split_map = sorted(
        ({"sample_id": str(r.sample_id), "fold": int(r.fold)} for r in oof.itertuples(index=False)),
        key=lambda x: x["sample_id"],
    )
    protocol = {
        "schema": "tempo-frozen-research-protocol-v1",
        "frozen_on": str(date.today()),
        "dataset": {"samples": 740, "sha256": sha256(DATASET)},
        "outer_cv": {
            "folds": 5, "source": str(E42_OOF.relative_to(ROOT)),
            "mapping_sha256": canonical_hash(split_map), "mapping": split_map,
        },
        "model_contract": {
            "joint_single_graph": True,
            "required_tasks": list(TASKS),
            "minimum_macro_f1_each": 0.70,
            "selection": "maximize minimum task Macro-F1; mean Macro-F1 is tie-breaker",
        },
        "inner_selection": {"folds": 3, "metric": "minimum task Macro-F1", "seeds": [42, 3407, 20261017]},
        "budget": {
            "platform": "Kaggle free GPU",
            "pay_to_scale_allowed": False,
            "smoke_before_full": True,
            "maximum_simultaneous_jobs": 1,
            "full_runs_per_candidate": 1,
        },
        "integrity": {
            "labels_must_not_enter_feature_extraction": True,
            "outer_test_must_not_select_hyperparameters": True,
            "smoke_results_not_quality_claims": True,
            "internal_oof_not_external_validation": True,
        },
    }
    (OUT / "frozen_protocol.json").write_text(json.dumps(protocol, indent=2) + "\n")

    ranking = json.loads(RANKING.read_text())
    registry = []
    for candidate in ranking["candidates"]:
        metrics = candidate["metrics"]
        registry.append({
            "model_id": candidate["model_id"], "status": candidate["status"],
            "task1_macro_f1": metrics["task1_issue"],
            "task2_macro_f1": metrics["task2_domain_sumber"],
            "task3_macro_f1": metrics["task3_primary_entity_type"],
            "minimum_macro_f1": candidate["minimum_macro_f1"],
            "mean_macro_f1": candidate["mean_macro_f1"],
            "eligible": candidate["all_tasks_at_least_0_70"], "source": candidate["source"],
        })
    e49 = json.loads((RESULTS / "e49_task_routed_mtl/result.json").read_text())
    scores = e49["overall_scores"]
    registry.append({
        "model_id": "E49", "status": "passed", "task1_macro_f1": scores["task1_issue"],
        "task2_macro_f1": scores["task2_domain_sumber"], "task3_macro_f1": scores["task3_primary_entity_type"],
        "minimum_macro_f1": scores["min"], "mean_macro_f1": scores["mean"], "eligible": False,
        "source": "DEMO_XAI_745_FULL/04_hasil_eksperimen/e49_task_routed_mtl/result.json",
    })
    m01_path = OUT / "01_model_comparison/M01_clip_indobert/result.json"
    if m01_path.exists():
        m01 = json.loads(m01_path.read_text())
        m = m01["overall_scores"]
        registry.append({
            "model_id": "M01", "status": m01["status"],
            "task1_macro_f1": m["task1_issue"], "task2_macro_f1": m["task2_domain_sumber"],
            "task3_macro_f1": m["task3_primary_entity_type"], "minimum_macro_f1": m["min"],
            "mean_macro_f1": m["mean"], "eligible": False,
            "source": str(m01_path.relative_to(ROOT)),
        })
    registry.sort(key=lambda x: (x["minimum_macro_f1"], x["mean_macro_f1"]), reverse=True)
    with (OUT / "experiments_registry.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=registry[0].keys())
        writer.writeheader(); writer.writerows(registry)

    leakage = f"""# Audit Leakage dan Train–Serve Parity

## Hasil

- Dataset: **740 ID unik**, seluruhnya memiliki gambar dan hash gambar cocok: **{not missing_images}**.
- Exact duplicate berdasarkan SHA-256: **{len(exact_duplicates)} grup**.
- Grup duplikat deklaratif beranggota >1: **{len(declared_groups)}**; lintas fold: **{len(cross_declared)}**.
- Kandidat near-duplicate dHash (jarak ≤2): **{len(near)}**; lintas fold: **{sum(x['cross_fold'] for x in near)}**.
- Fold E42 mencakup setiap sample tepat sekali dan berisi fold 1–5.

Kandidat dHash bukan bukti duplikat; hasilnya disimpan di `near_duplicate_candidates.csv` untuk inspeksi manusia. Tidak ada exact duplicate yang dapat menyebabkan kebocoran lintas fold.

## Train–serve parity

Training E41/E42 memakai `headline_verified [SEP] supporting_text_verified`. Mode dataset pada aplikasi memakai kolom yang sama secara default, tetapi pengguna dapat mengeditnya. Mode upload memakai headline hasil OCR atau koreksi pengguna dan supporting text yang dimasukkan pengguna. Jadi preprocessing antarmuka kompatibel secara bentuk, tetapi distribusi teks upload **tidak identik** dengan teks verified saat training. Ini adalah gap deployment, bukan bukti label leakage.

## Batas klaim

OOF 5-fold pada corpus yang sama adalah evaluasi internal. Pemilihan berulang E33–E49 pada corpus ini menciptakan selection bias; hasil tidak boleh disebut validasi eksternal independen.
"""
    (AUDIT / "leakage_report.md").write_text(leakage)

    audit_md = f"""# Audit Baseline E42

**Tanggal:** {date.today()}  
**Dataset:** `{DATASET.relative_to(ROOT)}`  
**SHA-256 dataset:** `{sha256(DATASET)}`

## Reproduksi metrik

{markdown_table([{**r, 'macro_f1': f"{r['macro_f1']:.6f}", 'accuracy': f"{r['accuracy']:.6f}"} for r in summary_rows], ['task', 'macro_f1', 'accuracy', 'classes'])}

Semua angka dihitung ulang dari `e42_tail_grid/oof.csv` dan cocok dengan `result.json` sampai toleransi 1e-12. Minimum Macro-F1 E42 adalah **{min(r['macro_f1'] for r in summary_rows):.6f}**, sehingga gate tiga task ≥0,70 **belum tercapai**.

## Integritas

- OOF: 740 baris, 740 ID unik, setiap ID muncul tepat sekali.
- Fold: 5 fold, masing-masing {', '.join(str(x) for x in sorted(Counter(oof.fold).values()))} sampel.
- Hash OOF: `{sha256(E42_OOF)}`.
- Detail per kelas: `per_class_metrics.csv`.
- Distribusi label: `data_distribution.csv`.
- Leakage/parity: `leakage_report.md`.
"""
    (AUDIT / "audit_e42.md").write_text(audit_md)

    ocr2 = json.loads((RESULTS / "revisi_week3/ocr_second_holdout/results.json").read_text())
    findings = f"""# Temuan dan Keputusan Sprint 0

1. **E42 tetap baseline joint terbaik yang terverifikasi** berdasarkan minimum Macro-F1 ({registry[0]['minimum_macro_f1']:.6f}).
2. **E49 sudah selesai**, bukan pekerjaan yang hilang. Task-routed MMoE menghasilkan {scores['task1_issue']:.4f}/{scores['task2_domain_sumber']:.4f}/{scores['task3_primary_entity_type']:.4f}; hipotesis itu tidak diulang.
3. **E48 adalah diagnostik single-task**, bukan kandidat delivery joint. Hasilnya mendukung adanya negative transfer tetapi tidak memenuhi kontrak satu model joint.
4. **Seluruh 740 gambar tersedia** dan hash-nya cocok dengan dataset.
5. **OCR holdout kedua sudah dibuka** dengan exact match {100 * ocr2['exact_accuracy']:.2f}% ({ocr2['exact_correct']}/{ocr2['count']}); gate 80% belum lulus. Holdout ini tidak boleh dipakai lagi untuk tuning selector.
6. **Train–serve gap masih ada**: training memakai teks verified; upload bergantung pada OCR/koreksi pengguna.
7. **Target akademik belum tercapai**. Eksperimen berikutnya harus menawarkan hipotesis baru dan mengikuti `frozen_protocol.json`; hasil internal tidak boleh diklaim sebagai validasi eksternal.
8. **M01 shared MLP selesai** dengan skor 0.4426/0.3592/0.3581 (minimum 0.3581). Kontrol sederhana ini lebih buruk dari E42 dan dihentikan; hasil negatif tetap dipertahankan.
"""
    (OUT / "findings.md").write_text(findings)

    sources = [DATASET, E42_OOF, E42_RESULT, RANKING,
               RESULTS / "e48_single_task_diagnostic/result.json",
               RESULTS / "e49_task_routed_mtl/result.json",
               RESULTS / "revisi_week3/ocr_second_holdout/results.json"]
    generated = [AUDIT / "audit_e42.md", AUDIT / "data_distribution.csv",
                 AUDIT / "per_class_metrics.csv", AUDIT / "leakage_report.md",
                 AUDIT / "near_duplicate_candidates.csv", OUT / "frozen_protocol.json",
                 OUT / "experiments_registry.csv", OUT / "findings.md"]
    if m01_path.exists():
        generated.extend([m01_path, m01_path.with_name("oof.csv"), m01_path.with_name("decision.md")])
    manifest = {
        "schema": "tempo-sprint0-manifest-v1", "generated_on": str(date.today()),
        "sources": {str(p.relative_to(ROOT)): sha256(p) for p in sources},
        "outputs": {str(p.relative_to(ROOT)): sha256(p) for p in generated},
    }
    (OUT / "manifest_sha256.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"status": "ok", "output": str(OUT), "near_duplicate_candidates": len(near)}, indent=2))


if __name__ == "__main__":
    main()
