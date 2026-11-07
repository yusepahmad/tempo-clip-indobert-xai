#!/usr/bin/env python3
"""MICRO-E11: nested hierarchical Task-3 head over the E10 multimodal stack."""
import csv
import hashlib
import json
import time
from pathlib import Path

import numpy as np
from sklearn.metrics import f1_score
from sklearn.model_selection import StratifiedKFold

import run_micro_e10_nested_vlm_stacking as e10

ROOT = e10.ROOT
PROJECT = e10.PROJECT
OUT = PROJECT / "04_hasil_eksperimen/next_research_20261017/06_micro_f1/MICRO_E11_hierarchical_task3"
E10_PRED = PROJECT / "04_hasil_eksperimen/next_research_20261017/06_micro_f1/MICRO_E10_nested_vlm_stacking/predictions.csv"
TASK3 = "task3_primary_entity_type"
CANDIDATES = ("lr0.03", "lr0.1", "lr1.0", "extra")
THRESHOLDS = tuple(np.arange(0.25, 0.751, 0.05).round(2))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def positive_probability(estimator, values):
    probabilities = estimator.predict_proba(values)
    column = int(np.where(np.asarray(estimator.classes_) == 1)[0][0])
    return probabilities[:, column]


def main():
    started = time.time()
    OUT.mkdir(parents=True, exist_ok=True)
    rows, fold_rows, e10_rows = read(e10.DATA), read(e10.FOLDS), read(E10_PRED)
    ids = np.asarray([row["sample_id"] for row in rows])
    assert ids.tolist() == [row["sample_id"] for row in fold_rows] == [row["sample_id"] for row in e10_rows]
    classic, siglip, e15, e22, bge, clip = (np.load(path, allow_pickle=False) for path in (e10.CLASSIC, e10.SIGLIP, e10.E15, e10.E22, e10.BGE, e10.CLIP))
    views = {
        "classic": np.hstack((e10.l2(classic["visual"]), e10.l2(siglip["image"]), e10.l2(classic["base_mean"]))),
        "qwen_bge": np.hstack((e10.l2(e15["last_token"]), e10.l2(bge["combined"]))),
        "caption_bge": np.hstack((e10.l2(e22["caption_context"]), e10.l2(bge["combined"]), e10.l2(clip["img"]))),
    }
    folds = np.asarray([int(row["fold"]) for row in fold_rows])
    tasks = e10.TASKS
    names = {task: sorted({row[task] for row in rows}) for task in tasks}
    counts = {task: len(names[task]) for task in tasks}
    truth = {task: np.asarray([{name: i for i, name in enumerate(names[task])}[row[task]] for row in rows]) for task in tasks}
    individual = names[TASK3].index("individual")
    output_task3 = np.full(740, -1, dtype=int)
    details = []

    for fold in range(1, 6):
        train, test = np.where(folds != fold)[0], np.where(folds == fold)[0]
        z_train_parts, z_test_parts = [], []
        for ti, task in enumerate(tasks):
            splits = list(StratifiedKFold(3, shuffle=True, random_state=111000 + fold * 10 + ti).split(train, truth[task][train]))
            for vi, (view_name, features) in enumerate(views.items()):
                cross = np.zeros((len(train), counts[task]), dtype=np.float32)
                for si, (a, b) in enumerate(splits):
                    estimator = e10.base_model(view_name, 112000 + fold * 1000 + ti * 100 + vi * 10 + si)
                    estimator.fit(features[train[a]], truth[task][train[a]])
                    cross[b] = e10.scores(estimator, features[train[b]], counts[task])
                estimator = e10.base_model(view_name, 113000 + fold * 100 + ti * 10 + vi)
                estimator.fit(features[train], truth[task][train])
                z_train_parts.append(cross)
                z_test_parts.append(e10.scores(estimator, features[test], counts[task]))
        z_train, z_test = np.hstack(z_train_parts), np.hstack(z_test_parts)
        y = truth[TASK3][train]
        binary = (y == individual).astype(int)
        splits = list(StratifiedKFold(3, shuffle=True, random_state=121000 + fold).split(train, y))
        binary_oof, non_oof = {}, {}
        for ci, candidate in enumerate(CANDIDATES):
            p_individual = np.zeros(len(train), dtype=np.float32)
            p_non = np.zeros((len(train), counts[TASK3]), dtype=np.float32)
            for si, (a, b) in enumerate(splits):
                binary_model = e10.meta_model(candidate, 122000 + fold * 1000 + ci * 10 + si)
                binary_model.fit(z_train[a], binary[a])
                p_individual[b] = positive_probability(binary_model, z_train[b])
                non_rows = a[y[a] != individual]
                non_model = e10.meta_model(candidate, 123000 + fold * 1000 + ci * 10 + si)
                non_model.fit(z_train[non_rows], y[non_rows])
                p_non[b] = e10.scores(non_model, z_train[b], counts[TASK3])
            p_non[:, individual] = -1.0
            binary_oof[candidate] = p_individual
            non_oof[candidate] = p_non.argmax(axis=1)
        evaluated = []
        for binary_name in CANDIDATES:
            for non_name in CANDIDATES:
                for threshold in THRESHOLDS:
                    predicted = non_oof[non_name].copy()
                    predicted[binary_oof[binary_name] >= threshold] = individual
                    evaluated.append({
                        "binary": binary_name, "non_individual": non_name, "threshold": float(threshold),
                        "inner_micro_f1": float(f1_score(y, predicted, average="micro")),
                    })
        selected = max(evaluated, key=lambda item: item["inner_micro_f1"])
        binary_model = e10.meta_model(selected["binary"], 124000 + fold)
        binary_model.fit(z_train, binary)
        non_rows = np.where(y != individual)[0]
        non_model = e10.meta_model(selected["non_individual"], 125000 + fold)
        non_model.fit(z_train[non_rows], y[non_rows])
        p_individual = positive_probability(binary_model, z_test)
        p_non = e10.scores(non_model, z_test, counts[TASK3])
        p_non[:, individual] = -1.0
        predicted = p_non.argmax(axis=1)
        predicted[p_individual >= selected["threshold"]] = individual
        output_task3[test] = predicted
        outer = float(f1_score(truth[TASK3][test], predicted, average="micro"))
        details.append({"fold": fold, "selected": selected, "outer_micro_f1": outer})
        print(f"fold={fold} binary={selected['binary']} non={selected['non_individual']} threshold={selected['threshold']:.2f} outer={outer:.6f}", flush=True)

    fields = ["sample_id", "fold"] + [field for task in tasks for field in (task + "_truth", task + "_pred")]
    with (OUT / "predictions.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for index, sample_id in enumerate(ids):
            row = {"sample_id": sample_id, "fold": int(folds[index])}
            for task in tasks:
                row[task + "_truth"] = e10_rows[index][task + "_truth"]
                row[task + "_pred"] = names[task][output_task3[index]] if task == TASK3 else e10_rows[index][task + "_pred"]
            writer.writerow(row)
    micro = {}
    macro = {}
    predictions = read(OUT / "predictions.csv")
    for task in tasks:
        actual = np.asarray([row[task + "_truth"] for row in predictions])
        predicted = np.asarray([row[task + "_pred"] for row in predictions])
        micro[task] = float(f1_score(actual, predicted, average="micro"))
        macro[task] = float(f1_score(actual, predicted, average="macro"))
    result = {
        "schema": "tempo-micro-e11-v1", "status": "complete",
        "model_contract": "E10 nested multimodal stack with a nested hierarchical Task-3 head",
        "task1_task2_source": str(E10_PRED.relative_to(ROOT)),
        "task3_leakage_control": "binary/non-individual models and threshold selected using outer-training cross-fit only",
        "micro_f1": micro, "macro_f1_diagnostic": macro,
        "minimum_micro_f1": min(micro.values()), "all_tasks_at_least_0_70": min(micro.values()) >= 0.70,
        "fold_details": details, "e10_predictions_sha256": sha(E10_PRED),
        "seconds": time.time() - started, "predictions_sha256": sha(OUT / "predictions.csv"),
    }
    (OUT / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({key: result[key] for key in ("micro_f1", "macro_f1_diagnostic", "minimum_micro_f1", "all_tasks_at_least_0_70", "seconds")}, indent=2))


if __name__ == "__main__":
    main()
