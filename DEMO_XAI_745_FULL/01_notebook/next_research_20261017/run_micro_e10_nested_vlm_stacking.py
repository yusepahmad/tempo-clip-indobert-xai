#!/usr/bin/env python3
"""MICRO-E10: leakage-safe nested stacking of classic and frozen VLM views."""
import csv
import hashlib
import json
import time
from pathlib import Path

import numpy as np
from sklearn.ensemble import ExtraTreesClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

ROOT = Path(__file__).resolve().parents[3]
PROJECT = ROOT / "DEMO_XAI_745_FULL"
DATA = PROJECT / "03_data/DATASET_740_TASK2_DOMAIN.csv"
FOLDS = PROJECT / "04_hasil_eksperimen/e42_tail_grid/oof.csv"
CLASSIC = PROJECT / "04_hasil_eksperimen/e41_cached_tail/cache/front_cache.npz"
SIGLIP = PROJECT / "04_hasil_eksperimen/next_research_20261017/01_model_comparison/M02_siglip2_indobert/features.npz"
E15 = ROOT / "docs/server-recovery/2026-10-11/e15_vlm_features/embeddings.npz"
E22 = ROOT / "docs/server-recovery/2026-10-11/e22_caption/full_embeddings/embeddings.npz"
BGE = ROOT / "docs/server-recovery/2026-10-10/e13_bge_m3/e13_bge_m3/embeddings.npz"
CLIP = PROJECT / "03_data/fitur_clip_indobert_740.npz"
OUT = PROJECT / "04_hasil_eksperimen/next_research_20261017/06_micro_f1/MICRO_E10_nested_vlm_stacking"
TASKS = ("task1_issue", "task2_domain_sumber", "task3_primary_entity_type")


def read(path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def l2(values):
    values = np.asarray(values, dtype=np.float32)
    return values / (np.linalg.norm(values, axis=1, keepdims=True) + 1e-8)


def base_model(view, seed):
    if view == "classic":
        return LogisticRegression(C=0.3, solver="liblinear", max_iter=1200, random_state=seed)
    if view == "qwen_bge":
        return make_pipeline(StandardScaler(), LogisticRegression(C=0.01, solver="liblinear", max_iter=3000, random_state=seed))
    return make_pipeline(StandardScaler(), SVC(C=10.0, gamma="scale", kernel="rbf", decision_function_shape="ovr", random_state=seed))


def scores(estimator, values, class_count):
    if hasattr(estimator, "predict_proba"):
        raw = estimator.predict_proba(values)
    else:
        raw = estimator.decision_function(values)
        if raw.ndim == 1:
            raw = np.column_stack((-raw, raw))
        raw = raw - raw.max(axis=1, keepdims=True)
        raw = np.exp(raw)
        raw /= raw.sum(axis=1, keepdims=True)
    output = np.zeros((len(values), class_count), dtype=np.float32)
    output[:, np.asarray(estimator.classes_, dtype=int)] = raw
    return output


def meta_model(name, seed):
    if name.startswith("lr"):
        return LogisticRegression(C=float(name[2:]), solver="liblinear", max_iter=1500, random_state=seed)
    return ExtraTreesClassifier(n_estimators=300, max_features="sqrt", min_samples_leaf=2, n_jobs=-1, random_state=seed)


def main():
    started = time.time()
    OUT.mkdir(parents=True, exist_ok=True)
    rows, fold_rows = read(DATA), read(FOLDS)
    ids = np.asarray([row["sample_id"] for row in rows])
    assert ids.tolist() == [row["sample_id"] for row in fold_rows]
    classic, siglip, e15, e22, bge, clip = (np.load(path, allow_pickle=False) for path in (CLASSIC, SIGLIP, E15, E22, BGE, CLIP))
    assert ids.tolist() == classic["sample_ids"].tolist() == siglip["sample_ids"].tolist()
    assert np.array_equal(ids, e15["sample_id"]) and np.array_equal(ids, e22["sample_id"]) and np.array_equal(ids, bge["sample_id"])
    views = {
        "classic": np.hstack((l2(classic["visual"]), l2(siglip["image"]), l2(classic["base_mean"]))),
        "qwen_bge": np.hstack((l2(e15["last_token"]), l2(bge["combined"]))),
        "caption_bge": np.hstack((l2(e22["caption_context"]), l2(bge["combined"]), l2(clip["img"]))),
    }
    assert all(value.shape[0] == 740 and np.isfinite(value).all() for value in views.values())
    folds = np.asarray([int(row["fold"]) for row in fold_rows])
    names = {task: sorted({row[task] for row in rows}) for task in TASKS}
    class_counts = {task: len(names[task]) for task in TASKS}
    truth = {task: np.asarray([{name: i for i, name in enumerate(names[task])}[row[task]] for row in rows]) for task in TASKS}
    predictions = {task: np.full(740, -1, dtype=int) for task in TASKS}
    details = []
    candidates = ("lr0.03", "lr0.1", "lr1.0", "extra")

    for fold in range(1, 6):
        train, test = np.where(folds != fold)[0], np.where(folds == fold)[0]
        meta_train, meta_test = [], []
        for ti, task in enumerate(TASKS):
            splits = list(StratifiedKFold(3, shuffle=True, random_state=111000 + fold * 10 + ti).split(train, truth[task][train]))
            for vi, (view_name, features) in enumerate(views.items()):
                cross = np.zeros((len(train), class_counts[task]), dtype=np.float32)
                for si, (a, b) in enumerate(splits):
                    estimator = base_model(view_name, 112000 + fold * 1000 + ti * 100 + vi * 10 + si)
                    estimator.fit(features[train[a]], truth[task][train[a]])
                    cross[b] = scores(estimator, features[train[b]], class_counts[task])
                estimator = base_model(view_name, 113000 + fold * 100 + ti * 10 + vi)
                estimator.fit(features[train], truth[task][train])
                meta_train.append(cross)
                meta_test.append(scores(estimator, features[test], class_counts[task]))
        z_train, z_test = np.hstack(meta_train), np.hstack(meta_test)
        detail = {"fold": fold, "meta_dimensions": int(z_train.shape[1]), "tasks": {}}
        for ti, task in enumerate(TASKS):
            splits = list(StratifiedKFold(3, shuffle=True, random_state=114000 + fold * 10 + ti).split(train, truth[task][train]))
            evaluated = []
            for ci, candidate in enumerate(candidates):
                inner = []
                for si, (a, b) in enumerate(splits):
                    estimator = meta_model(candidate, 115000 + fold * 1000 + ti * 100 + ci * 10 + si)
                    estimator.fit(z_train[a], truth[task][train[a]])
                    inner.append(f1_score(truth[task][train[b]], estimator.predict(z_train[b]), average="micro"))
                evaluated.append({"name": candidate, "inner_micro_f1": float(np.mean(inner))})
            selected = max(evaluated, key=lambda item: item["inner_micro_f1"])
            estimator = meta_model(selected["name"], 116000 + fold * 10 + ti)
            estimator.fit(z_train, truth[task][train])
            predictions[task][test] = estimator.predict(z_test)
            outer = float(f1_score(truth[task][test], predictions[task][test], average="micro"))
            detail["tasks"][task] = {"selected": selected, "candidates": evaluated, "outer_micro_f1": outer}
            print(f"fold={fold} task={task} meta={selected['name']} outer={outer:.6f}", flush=True)
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
        "schema": "tempo-micro-e10-v1", "status": "complete",
        "model_contract": "one nested stack over classic/Qwen/BGE/caption/CLIP views with three task heads",
        "leakage_control": "all base cross-fit and refit models use outer-training only",
        "micro_f1": micro, "macro_f1_diagnostic": macro,
        "minimum_micro_f1": min(micro.values()), "all_tasks_at_least_0_70": min(micro.values()) >= 0.70,
        "fold_details": details, "dataset_sha256": sha(DATA),
        "feature_sha256": {str(path.relative_to(ROOT)): sha(path) for path in (CLASSIC, SIGLIP, E15, E22, BGE, CLIP)},
        "seconds": time.time() - started, "predictions_sha256": sha(OUT / "predictions.csv"),
    }
    (OUT / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({key: result[key] for key in ("micro_f1", "macro_f1_diagnostic", "minimum_micro_f1", "all_tasks_at_least_0_70", "seconds")}, indent=2))


if __name__ == "__main__":
    main()
