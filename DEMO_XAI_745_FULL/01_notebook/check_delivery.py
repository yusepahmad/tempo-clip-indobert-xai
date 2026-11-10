"""Preflight portable: validasi aset dan replay prediksi E42."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "02_web_demo"))

from e42_engine import E42Engine  # noqa: E402


def main() -> None:
    engine = E42Engine()
    assert engine.description()["version"] == "e42-tail-grid-v1"
    assert len(engine.df) == 740
    assert set(engine._models) == {1, 2, 3, 4, 5}
    assert len(engine._fold_for_id) == 740

    reference = pd.read_csv(ROOT / "04_hasil_eksperimen/e42_tail_grid/oof.csv")
    predicted = {task: np.empty(740, dtype=object) for task in engine.tasks}
    sample_ids = engine.df.sample_id.astype(str)
    for fold, model in engine._models.items():
        indices = np.array([
            index for index, sample_id in enumerate(sample_ids)
            if engine._fold_for_id[sample_id] == fold
        ])
        hidden, attention, pool, visual = engine._tm.batch_tensors(
            engine.cache, indices, "cpu"
        )
        with torch.no_grad():
            output = model(hidden, attention, pool, visual)
        for task in engine.tasks:
            predicted[task][indices] = [
                engine.maps[task][index]
                for index in output[task].argmax(1).tolist()
            ]

    for task in engine.tasks:
        if predicted[task].tolist() != reference[task + "_pred"].tolist():
            raise AssertionError(f"Replay OOF E42 berbeda untuk task {task}")

    print("E42 verified: 5 checkpoints, 740/740 canonical OOF predictions match")


if __name__ == "__main__":
    main()
