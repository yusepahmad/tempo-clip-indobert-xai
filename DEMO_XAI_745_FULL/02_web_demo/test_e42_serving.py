"""Verifikasi aset dan replay 740 prediksi checkpoint E42."""
from __future__ import annotations

import unittest
from pathlib import Path

import numpy as np
import pandas as pd
import torch

from e42_engine import E42Engine

ROOT = Path(__file__).resolve().parent.parent


class E42ServingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = E42Engine()

    def test_assets_and_outer_fold_coverage(self):
        self.assertEqual(self.engine.description()["version"], "e42-tail-grid-v1")
        self.assertEqual(len(self.engine.df), 740)
        self.assertEqual(set(self.engine._models), {1, 2, 3, 4, 5})
        self.assertEqual(len(self.engine._fold_for_id), 740)

    def test_full_replay_matches_canonical_oof(self):
        reference = pd.read_csv(ROOT / "04_hasil_eksperimen/e42_tail_grid/oof.csv")
        predicted = {task: np.empty(740, dtype=object) for task in self.engine.tasks}
        for fold, model in self.engine._models.items():
            indices = np.array([
                i for i, sample_id in enumerate(self.engine.df.sample_id.astype(str))
                if self.engine._fold_for_id[sample_id] == fold
            ])
            hidden, attention, pool, visual = self.engine._tm.batch_tensors(
                self.engine.cache, indices, "cpu"
            )
            with torch.no_grad():
                output = model(hidden, attention, pool, visual)
            for task in self.engine.tasks:
                predicted[task][indices] = [
                    self.engine.maps[task][index] for index in output[task].argmax(1).tolist()
                ]
        for task in self.engine.tasks:
            self.assertListEqual(predicted[task].tolist(), reference[task + "_pred"].tolist())


if __name__ == "__main__":
    unittest.main()
