#!/usr/bin/env python3
"""Rank verified three-task candidates without mixing models or protocols."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "04_hasil_eksperimen"
OUT = RESULTS / "joint_candidate_ranking.json"
TASKS = ("task1_issue", "task2_domain_sumber", "task3_primary_entity_type")
CANDIDATES = {
    "E36": "e36_clip_l14/root_verification.json",
    "E37": "e37_token_pool/root_verification.json",
    "E38": "e38_l14_token/root_verification.json",
    "E39": "e39_feature_norm/root_verification.json",
    "E40": "e40_balanced_mmoe/root_verification.json",
    "E41": "e41_cached_tail/gpu/root_verification.json",
    "E42": "e42_tail_grid/root_verification.json",
    "E43": "e43_spatial_attention/gpu/root_verification.json",
    "E44": "e44_focal_tail/root_verification.json",
    "E46": "e46_label_smoothing/root_verification.json",
    "E47": "e47_task_relations/root_verification.json",
    "E49": "e49_task_routed_mtl/root_verification.json",
}
BASELINE = RESULTS / "hasil_mtl_740_task2domain.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def row(model_id: str, metrics: dict, source: Path, status: str = "passed") -> dict:
    values = {task: float(metrics[task]) for task in TASKS}
    return {
        "model_id": model_id,
        "status": status,
        "samples": 740,
        "protocol": "verified OOF predictions on the fixed 740-sample corpus",
        "metrics": values,
        "minimum_macro_f1": min(values.values()),
        "mean_macro_f1": sum(values.values()) / len(values),
        "all_tasks_at_least_0_70": all(value >= 0.70 for value in values.values()),
        "source": str(source.relative_to(ROOT)),
        "source_sha256": sha256(source),
    }


def build() -> dict:
    baseline_raw = json.loads(BASELINE.read_text(encoding="utf-8"))["fusion MTL (CLIP+IndoBERT)"]
    rows = [row("baseline-delivery", {task: baseline_raw[task]["macro_f1"] for task in TASKS}, BASELINE)]
    for model_id, relative in CANDIDATES.items():
        source = RESULTS / relative
        raw = json.loads(source.read_text(encoding="utf-8"))
        if raw.get("status") != "passed":
            raise RuntimeError(f"{model_id}: root audit tidak passed")
        metrics = raw.get("metrics_stdlib")
        if set(metrics) != set(TASKS):
            raise RuntimeError(f"{model_id}: task tidak lengkap")
        rows.append(row(model_id, {task: metrics[task]["candidate"] for task in TASKS}, source))
    rows.sort(key=lambda item: (-item["minimum_macro_f1"], -item["mean_macro_f1"], item["model_id"]))
    for rank, item in enumerate(rows, 1):
        item["rank_by_minimum_then_mean"] = rank
    return {
        "schema": "tempo-joint-candidate-ranking-v1",
        "selection_rule": "descending minimum Macro-F1 across the same model's three tasks; descending mean as tie-breaker",
        "warning": "Repeated experiments on the same corpus create selection bias; this is not external validation.",
        "excluded": {
            "E33-E35": "reported historically but canonical root-verification artifacts are absent from the current result tree",
            "E45": "full experiment not completed",
            "Task2-only candidates": "not eligible for a joint three-task model decision",
        },
        "candidates": rows,
    }


def verify(report: dict) -> None:
    assert len(report["candidates"]) == 13
    assert report["candidates"][0]["model_id"] == "E42"
    assert not any(row["all_tasks_at_least_0_70"] for row in report["candidates"])
    for index, item in enumerate(report["candidates"], 1):
        assert item["rank_by_minimum_then_mean"] == index
        assert abs(item["minimum_macro_f1"] - min(item["metrics"].values())) < 1e-15
        assert abs(item["mean_macro_f1"] - sum(item["metrics"].values()) / 3) < 1e-15
        source = ROOT / item["source"]
        assert source.exists() and sha256(source) == item["source_sha256"]


if __name__ == "__main__":
    report = build()
    verify(report)
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "verified", "count": len(report["candidates"]),
                      "best": report["candidates"][0]}, ensure_ascii=False, indent=2))
