#!/usr/bin/env python3
"""E49 Independent Audit and Verification Script.

Independently recalculates Macro-F1 across all 740 samples and audits dataset/OOF hashes.
"""
import csv
import hashlib
import json
from pathlib import Path
from sklearn.metrics import classification_report, confusion_matrix, f1_score

ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = ROOT / "03_data/DATASET_740_TASK2_DOMAIN.csv"
CACHE_PATH = ROOT / "04_hasil_eksperimen/e41_cached_tail/cache/front_cache.npz"
E42_OOF = ROOT / "04_hasil_eksperimen/e42_tail_grid/oof.csv"
OUT_DIR = ROOT / "04_hasil_eksperimen/e49_task_routed_mtl"
OOF_PATH = OUT_DIR / "oof.csv"

TASKS = ("task1_issue", "task2_domain_sumber", "task3_primary_entity_type")

def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()

def read_csv(p: Path):
    with p.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def main():
    print("=== Running Independent E49 Audit and Verification ===")
    assert OOF_PATH.exists(), f"Missing OOF file at {OOF_PATH}"

    data_rows = read_csv(DATA_PATH)
    oof_rows = read_csv(OOF_PATH)
    e42_rows = read_csv(E42_OOF)

    assert len(data_rows) == 740, f"Expected 740 data rows, got {len(data_rows)}"
    assert len(oof_rows) == 740, f"Expected 740 OOF rows, got {len(oof_rows)}"
    assert len(e42_rows) == 740, f"Expected 740 E42 rows, got {len(e42_rows)}"

    data_ids = [r["sample_id"] for r in data_rows]
    oof_ids = [r["sample_id"] for r in oof_rows]
    e42_ids = [r["sample_id"] for r in e42_rows]

    assert data_ids == oof_ids, "Sample ID order does not match dataset"
    assert data_ids == e42_ids, "Sample ID order does not match E42"

    # Verify outer fold matching
    for i in range(740):
        assert oof_rows[i]["fold"] == e42_rows[i]["fold"], f"Fold mismatch at index {i}"

    task_results = {}
    for task in TASKS:
        truth = [r[f"{task}_truth"] for r in oof_rows]
        pred = [r[f"{task}_pred"] for r in oof_rows]
        data_truth = [r[task] for r in data_rows]

        assert truth == data_truth, f"Ground truth mismatch for {task}"
        labels = sorted(set(truth))

        macro_f1 = float(f1_score(truth, pred, labels=labels, average="macro", zero_division=0))
        report = classification_report(truth, pred, labels=labels, output_dict=True, zero_division=0)
        cmatrix = confusion_matrix(truth, pred, labels=labels).tolist()

        task_results[task] = {
            "macro_f1": macro_f1,
            "labels": labels,
            "per_class": {lbl: report[lbl] for lbl in labels},
            "confusion_matrix": cmatrix
        }
        print(f"Verified {task} Macro-F1: {macro_f1:.6f}")

    min_macro_f1 = min(task_results[t]["macro_f1"] for t in TASKS)
    mean_macro_f1 = sum(task_results[t]["macro_f1"] for t in TASKS) / len(TASKS)

    print(f"\n--- Summary ---")
    print(f"Min Macro-F1:  {min_macro_f1:.6f}")
    print(f"Mean Macro-F1: {mean_macro_f1:.6f}")

    # Compare with E42 baseline
    e42_scores = {
        "task1_issue": 0.5254826236,
        "task2_domain_sumber": 0.3955604326,
        "task3_primary_entity_type": 0.4033984096,
        "min": 0.3955604326,
        "mean": 0.4414804886
    }

    verification = {
        "schema": "tempo-e49-verification-v1",
        "status": "passed",
        "dataset_sha256": sha256_file(DATA_PATH),
        "cache_sha256": sha256_file(CACHE_PATH),
        "oof_sha256": sha256_file(OOF_PATH),
        "metrics_stdlib": {
            task: {
                "candidate": task_results[task]["macro_f1"],
                "baseline": e42_scores[task]
            }
            for task in TASKS
        },
        "scores": {
            "task1_issue": task_results["task1_issue"]["macro_f1"],
            "task2_domain_sumber": task_results["task2_domain_sumber"]["macro_f1"],
            "task3_primary_entity_type": task_results["task3_primary_entity_type"]["macro_f1"],
            "minimum_task_macro_f1": min_macro_f1,
            "mean_macro_f1": mean_macro_f1
        },
        "comparison_vs_e42": {
            "delta_task1": task_results["task1_issue"]["macro_f1"] - e42_scores["task1_issue"],
            "delta_task2": task_results["task2_domain_sumber"]["macro_f1"] - e42_scores["task2_domain_sumber"],
            "delta_task3": task_results["task3_primary_entity_type"]["macro_f1"] - e42_scores["task3_primary_entity_type"],
            "delta_min": min_macro_f1 - e42_scores["min"],
            "delta_mean": mean_macro_f1 - e42_scores["mean"]
        },
        "task_details": task_results
    }

    verify_path = OUT_DIR / "root_verification.json"
    with verify_path.open("w", encoding="utf-8") as f:
        json.dump(verification, f, indent=2, sort_keys=True)

    print(f"Verification report written to {verify_path}")

if __name__ == "__main__":
    main()
