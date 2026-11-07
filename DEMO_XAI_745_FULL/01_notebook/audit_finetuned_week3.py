"""Audit downloaded five-fold outputs before demo integration.

Usage: python audit_finetuned_week3.py /path/to/tempo_full
This computes OOF diagnostics, not validation of a newly trained deployment model.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score


def audit(folder, dataset, require_models=True):
    report = json.loads((folder / "hasil_mtl_740_finetuned.json").read_text())
    assert report["status"] == "complete" and not report["config"]["smoke"]
    assert report["config"]["folds"] == 5 and report["config"]["epochs"] == 120
    assert report["config"]["data_sha256"] == hashlib.sha256(dataset.read_bytes()).hexdigest(), "Dataset hash mismatch"
    df = pd.read_csv(dataset).fillna("")
    assert len(df) == 740 and df.sample_id.is_unique
    tasks = list(report["classes"])
    coverage = []
    aggregate = {t: np.full(len(df), -1, dtype=int) for t in tasks}
    for fold in range(1, 6):
        if require_models:
            assert (folder / f"fold_{fold}.pt").is_file(), "Missing model fold"
        meta = json.loads((folder / f"fold_{fold}_metrics.json").read_text())
        assert not meta["smoke"] and meta["fold"] == fold
        with np.load(folder / f"fold_{fold}_predictions.npz") as values:
            indices = values["indices"]
            assert len(indices) == 148 and len(set(indices.tolist())) == 148
            assert np.issubdtype(indices.dtype, np.integer)
            assert np.all((indices >= 0) & (indices < len(df)))
            coverage.extend(indices.tolist())
            for task in tasks:
                predicted = values[task]
                assert len(predicted) == len(indices)
                assert np.issubdtype(predicted.dtype, np.integer)
                assert np.all((predicted >= 0) & (predicted < len(report["classes"][task])))
                aggregate[task][indices] = predicted
    assert sorted(coverage) == list(range(len(df))), "Each sample must occur exactly once in OOF"
    baseline = json.loads((dataset.parents[1] / "04_hasil_eksperimen/hasil_mtl_740_task2domain.json").read_text())["fusion MTL (CLIP+IndoBERT)"]
    diagnostics = {}
    errors = []
    with np.load(folder / "oof_predictions.npz") as oof:
        for task in tasks:
            labels = report["classes"][task]
            assert labels == sorted(df[task].unique().tolist()), "Class mapping mismatch"
            truth = df[task].map({label: i for i, label in enumerate(labels)}).to_numpy()
            predicted = aggregate[task]
            assert np.array_equal(predicted, oof[task]), "OOF differs from fold predictions"
            metrics = {"accuracy": float(accuracy_score(truth, predicted)), "macro_f1": float(f1_score(truth, predicted, average="macro", zero_division=0))}
            for key, value in metrics.items():
                assert abs(value - report["hasil"][task][key]) < 1e-8, "Reported metric mismatch"
            diagnostics[task] = {**metrics, "baseline_macro_f1": baseline[task]["macro_f1"], "macro_f1_difference": metrics["macro_f1"] - baseline[task]["macro_f1"], "class_order": labels, "confusion_matrix": confusion_matrix(truth, predicted, labels=range(len(labels))).tolist(), "per_class": classification_report(truth, predicted, labels=range(len(labels)), target_names=labels, output_dict=True, zero_division=0)}
            for i in np.flatnonzero(truth != predicted):
                errors.append({"sample_id": df.iloc[i].sample_id, "task": task, "truth": labels[truth[i]], "prediction": labels[predicted[i]], "headline": df.iloc[i].headline_verified})
    result = {"status": "audited", "checkpoint_presence_required": require_models, "local_checkpoint_folds": [f for f in range(1,6) if (folder / f"fold_{f}.pt").is_file()], "protocol": "5-fold OOF, seed42; each sample evaluated once", "limitations": "Requires separate inspection of training split construction/checkpoint provenance; OOF audit does not establish deployment performance or improvement significance.", "metrics": diagnostics, "errors": errors}
    (folder / "week3_audit.json").write_text(json.dumps(result, ensure_ascii=False, indent=2))
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("folder", type=Path)
    parser.add_argument("--metrics-only", action="store_true", help="Audit evaluation files without asserting local checkpoint presence; does not authorize integration")
    args = parser.parse_args()
    dataset = Path(__file__).resolve().parents[1] / "03_data/DATASET_740_TASK2_DOMAIN.csv"
    result = audit(args.folder, dataset, require_models=not args.metrics_only)
    print(json.dumps({"status": result["status"], "metrics": {t: x["macro_f1"] for t, x in result["metrics"].items()}}))
