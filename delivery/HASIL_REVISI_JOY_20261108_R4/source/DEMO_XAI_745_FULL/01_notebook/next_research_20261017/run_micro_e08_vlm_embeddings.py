#!/usr/bin/env python3
"""MICRO-E08: nested three-head fusion of frozen VLM/text/visual embeddings."""
import csv
import hashlib
import json
import time
from pathlib import Path

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import LinearSVC, SVC

ROOT = Path(__file__).resolve().parents[3]
PROJECT = ROOT / "DEMO_XAI_745_FULL"
DATA = PROJECT / "03_data/DATASET_740_TASK2_DOMAIN.csv"
FOLDS = PROJECT / "04_hasil_eksperimen/e42_tail_grid/oof.csv"
E15 = ROOT / "docs/server-recovery/2026-10-11/e15_vlm_features/embeddings.npz"
E22 = ROOT / "docs/server-recovery/2026-10-11/e22_caption/full_embeddings/embeddings.npz"
BGE = ROOT / "docs/server-recovery/2026-10-10/e13_bge_m3/e13_bge_m3/embeddings.npz"
CLIP = PROJECT / "03_data/fitur_clip_indobert_740.npz"
OUT = PROJECT / "04_hasil_eksperimen/next_research_20261017/06_micro_f1/MICRO_E08_vlm_embeddings"
TASKS = ("task1_issue", "task2_domain_sumber", "task3_primary_entity_type")
HEADS = (
    ("linear_c001", "linear", 0.01, None),
    ("linear_c01", "linear", 0.1, None),
    ("linear_c001_bal", "linear", 0.01, "balanced"),
    ("logreg_c001", "logreg", 0.01, None),
    ("logreg_c01", "logreg", 0.1, None),
    ("rbf_c1", "rbf", 1.0, None),
    ("rbf_c10", "rbf", 10.0, None),
)


def read(path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def l2(block):
    block = np.asarray(block, dtype=np.float32)
    return block / (np.linalg.norm(block, axis=1, keepdims=True) + 1e-8)


def model(kind, c_value, class_weight, seed):
    if kind == "linear":
        head = LinearSVC(C=c_value, class_weight=class_weight, max_iter=10000, random_state=seed)
    elif kind == "logreg":
        head = LogisticRegression(C=c_value, class_weight=class_weight, max_iter=3000, solver="liblinear", random_state=seed)
    else:
        head = SVC(C=c_value, gamma="scale", class_weight=class_weight, kernel="rbf", random_state=seed)
    return make_pipeline(StandardScaler(), head)


def main():
    started = time.time()
    OUT.mkdir(parents=True, exist_ok=True)
    rows, fold_rows = read(DATA), read(FOLDS)
    ids = np.asarray([row["sample_id"] for row in rows])
    assert ids.tolist() == [row["sample_id"] for row in fold_rows]
    e15, e22, bge, clip = (np.load(path, allow_pickle=False) for path in (E15, E22, BGE, CLIP))
    assert np.array_equal(e15["sample_id"], ids)
    assert np.array_equal(e22["sample_id"], ids)
    assert np.array_equal(bge["sample_id"], ids)
    blocks = {
        "qwen": l2(e15["last_token"]),
        "caption": l2(e22["caption_context"]),
        "bge": l2(bge["combined"]),
        "clip": l2(clip["img"]),
    }
    views = {
        "qwen": blocks["qwen"],
        "caption_bge": np.hstack((blocks["caption"], blocks["bge"])),
        "qwen_caption": np.hstack((blocks["qwen"], blocks["caption"])),
        "qwen_bge": np.hstack((blocks["qwen"], blocks["bge"])),
        "all": np.hstack(tuple(blocks.values())),
    }
    assert all(value.shape[0] == 740 and np.isfinite(value).all() for value in views.values())
    folds = np.asarray([int(row["fold"]) for row in fold_rows])
    names = {task: sorted({row[task] for row in rows}) for task in TASKS}
    truth = {task: np.asarray([{name: i for i, name in enumerate(names[task])}[row[task]] for row in rows]) for task in TASKS}
    predictions = {task: np.full(740, -1, dtype=int) for task in TASKS}
    details = []

    for fold in range(1, 6):
        train, test = np.where(folds != fold)[0], np.where(folds == fold)[0]
        splits = {
            task: list(StratifiedKFold(3, shuffle=True, random_state=101000 + fold * 10 + ti).split(train, truth[task][train]))
            for ti, task in enumerate(TASKS)
        }
        view_scores = {}
        for vi, (view_name, features) in enumerate(views.items()):
            view_scores[view_name] = {}
            for ti, task in enumerate(TASKS):
                scores = []
                for si, (a, b) in enumerate(splits[task]):
                    a, b = train[a], train[b]
                    estimator = model("linear", 0.01, None, 102000 + fold * 1000 + vi * 100 + ti * 10 + si)
                    estimator.fit(features[a], truth[task][a])
                    scores.append(f1_score(truth[task][b], estimator.predict(features[b]), average="micro"))
                view_scores[view_name][task] = float(np.mean(scores))
        selected_view = max(views, key=lambda name: (min(view_scores[name].values()), np.mean(list(view_scores[name].values()))))
        features = views[selected_view]
        detail = {"fold": fold, "selected_view": selected_view, "view_inner_micro_f1": view_scores, "tasks": {}}
        for ti, task in enumerate(TASKS):
            candidates = []
            for hi, (head_name, kind, c_value, class_weight) in enumerate(HEADS):
                scores = []
                for si, (a, b) in enumerate(splits[task]):
                    a, b = train[a], train[b]
                    estimator = model(kind, c_value, class_weight, 103000 + fold * 1000 + ti * 100 + hi * 10 + si)
                    estimator.fit(features[a], truth[task][a])
                    scores.append(f1_score(truth[task][b], estimator.predict(features[b]), average="micro"))
                candidates.append({"name": head_name, "kind": kind, "C": c_value, "class_weight": class_weight, "inner_micro_f1": float(np.mean(scores))})
            chosen = max(candidates, key=lambda item: item["inner_micro_f1"])
            estimator = model(chosen["kind"], chosen["C"], chosen["class_weight"], 104000 + fold * 10 + ti)
            estimator.fit(features[train], truth[task][train])
            predictions[task][test] = estimator.predict(features[test])
            outer = float(f1_score(truth[task][test], predictions[task][test], average="micro"))
            detail["tasks"][task] = {"selected_head": chosen, "head_candidates": candidates, "outer_micro_f1": outer}
            print(f"fold={fold} view={selected_view} task={task} head={chosen['name']} outer={outer:.6f}", flush=True)
        details.append(detail)

    fields = ["sample_id", "fold"] + [field for task in TASKS for field in (task + "_truth", task + "_pred")]
    with (OUT / "predictions.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for index, sample_id in enumerate(ids):
            row = {"sample_id": sample_id, "fold": int(folds[index])}
            for task in TASKS:
                row[task + "_truth"] = names[task][truth[task][index]]
                row[task + "_pred"] = names[task][predictions[task][index]]
            writer.writerow(row)
    micro = {task: float(f1_score(truth[task], predictions[task], average="micro")) for task in TASKS}
    macro = {task: float(f1_score(truth[task], predictions[task], average="macro")) for task in TASKS}
    result = {
        "schema": "tempo-micro-e08-v1", "status": "complete",
        "model_contract": "one nested-selected frozen embedding view with three classification heads",
        "micro_f1": micro, "macro_f1_diagnostic": macro,
        "minimum_micro_f1": min(micro.values()), "all_tasks_at_least_0_70": min(micro.values()) >= 0.70,
        "fold_details": details, "dataset_sha256": sha(DATA),
        "feature_sha256": {str(path.relative_to(ROOT)): sha(path) for path in (E15, E22, BGE, CLIP)},
        "seconds": time.time() - started, "predictions_sha256": sha(OUT / "predictions.csv"),
    }
    (OUT / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({key: result[key] for key in ("micro_f1", "macro_f1_diagnostic", "minimum_micro_f1", "all_tasks_at_least_0_70", "seconds")}, indent=2))


if __name__ == "__main__":
    main()
