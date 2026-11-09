"""Synthetic artifact checks; these results are not training metrics."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd
from audit_finetuned_week3 import audit


class TrainingAudit(unittest.TestCase):
    def test_complete_and_duplicate_coverage(self):
        dataset = Path(__file__).resolve().parents[1] / "03_data/DATASET_740_TASK2_DOMAIN.csv"
        df = pd.read_csv(dataset)
        tasks = ["task1_issue", "task2_domain_sumber", "task3_primary_entity_type"]
        classes = {t: sorted(df[t].unique().tolist()) for t in tasks}
        truth = {t: df[t].map({x: i for i, x in enumerate(classes[t])}).to_numpy() for t in tasks}
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            report = {"status": "complete", "config": {"smoke": False, "folds": 5, "epochs": 120, "data_sha256": hashlib.sha256(dataset.read_bytes()).hexdigest()}, "classes": classes, "hasil": {t: {"accuracy": 1., "macro_f1": 1.} for t in tasks}}
            (folder / "hasil_mtl_740_finetuned.json").write_text(json.dumps(report))
            np.savez(folder / "oof_predictions.npz", **truth)
            for fold in range(1, 6):
                indices = np.arange((fold-1)*148, fold*148)
                (folder / f"fold_{fold}.pt").write_bytes(b"synthetic presence fixture only")
                (folder / f"fold_{fold}_metrics.json").write_text(json.dumps({"fold": fold, "smoke": False}))
                np.savez(folder / f"fold_{fold}_predictions.npz", indices=indices, **{t: v[indices] for t, v in truth.items()})
            self.assertEqual(audit(folder, dataset)["status"], "audited")
            indices = np.arange(0, 148)
            np.savez(folder / "fold_5_predictions.npz", indices=indices, **{t: v[indices] for t, v in truth.items()})
            with self.assertRaisesRegex(AssertionError, "exactly once"):
                audit(folder, dataset)
            report["config"]["data_sha256"] = "wrong"
            (folder / "hasil_mtl_740_finetuned.json").write_text(json.dumps(report))
            with self.assertRaisesRegex(AssertionError, "hash mismatch"):
                audit(folder, dataset)


if __name__ == "__main__":
    unittest.main()
