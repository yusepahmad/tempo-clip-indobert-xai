#!/usr/bin/env python3
"""MICRO-E06: leakage-safe nested three-head classifier over VLM text views."""
import csv
import hashlib
import json
import time
from pathlib import Path

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import f1_score
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import FeatureUnion, make_pipeline
from sklearn.svm import LinearSVC


ROOT = Path(__file__).resolve().parents[3]
PROJECT = ROOT / "DEMO_XAI_745_FULL"
DATA = PROJECT / "03_data/DATASET_740_TASK2_DOMAIN.csv"
FOLDS = PROJECT / "04_hasil_eksperimen/e42_tail_grid/oof.csv"
DESC = ROOT / "docs/server-recovery/2026-10-10/e01-full-terbaru/e01_vlm/deskripsi.jsonl"
ZERO = ROOT / "docs/server-recovery/2026-10-10/e01-full-terbaru/e01_vlm/zeroshot.jsonl"
CAPTION_DIR = ROOT / "docs/server-recovery/2026-10-11/e22_caption/full_caption_cache/records"
OUT = PROJECT / "04_hasil_eksperimen/next_research_20261017/06_micro_f1/MICRO_E06_vlm_text"
TASKS = ("task1_issue", "task2_domain_sumber", "task3_primary_entity_type")
VIEWS = ("base", "base_desc", "base_caption", "base_desc_caption", "base_zero", "all_vlm")
HEADS = (
    ("c025", 0.25, None),
    ("c05", 0.5, None),
    ("c1", 1.0, None),
    ("c05_balanced", 0.5, "balanced"),
)


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def read_jsonl(path):
    return {row["sample_id"]: row for row in map(json.loads, path.read_text().splitlines())}


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def classifier(c=0.5, class_weight=None, seed=0):
    word = TfidfVectorizer(
        ngram_range=(1, 2), min_df=2, max_df=0.995, max_features=25000,
        sublinear_tf=True, strip_accents="unicode",
    )
    char = TfidfVectorizer(
        analyzer="char_wb", ngram_range=(3, 5), min_df=2,
        max_features=35000, sublinear_tf=True,
    )
    return make_pipeline(
        FeatureUnion((("word", word), ("char", char))),
        LinearSVC(C=c, class_weight=class_weight, random_state=seed),
    )


def main():
    started = time.time()
    OUT.mkdir(parents=True, exist_ok=True)
    rows = read_csv(DATA)
    fold_rows = read_csv(FOLDS)
    ids = [row["sample_id"] for row in rows]
    assert ids == [row["sample_id"] for row in fold_rows]
    desc = read_jsonl(DESC)
    zero = read_jsonl(ZERO)
    captions = {}
    for path in CAPTION_DIR.glob("*.json"):
        row = json.loads(path.read_text())
        if row.get("usable", True):
            captions[row["sample_id"]] = row.get("caption", "")
    assert set(ids) == set(desc) == set(zero) == set(captions)

    texts = {view: [] for view in VIEWS}
    for row in rows:
        sid = row["sample_id"]
        base = f"HEADLINE: {row['headline_verified']} SUPPORTING: {row['supporting_text_verified']}"
        visual = desc[sid]["deskripsi"]
        caption = captions[sid]
        # Deliberately exclude zero[sid]['domain'], which is a direct pseudo-label.
        reasoning = f"SUMBER VISUAL: {zero[sid].get('sumber_visual', '')} ALASAN: {zero[sid].get('alasan', '')}"
        values = {
            "base": base,
            "base_desc": f"{base} DESKRIPSI: {visual}",
            "base_caption": f"{base} CAPTION: {caption}",
            "base_desc_caption": f"{base} DESKRIPSI: {visual} CAPTION: {caption}",
            "base_zero": f"{base} {reasoning}",
            "all_vlm": f"{base} DESKRIPSI: {visual} CAPTION: {caption} {reasoning}",
        }
        for view, value in values.items():
            texts[view].append(value)
    texts = {key: np.asarray(value) for key, value in texts.items()}
    folds = np.asarray([int(row["fold"]) for row in fold_rows])
    label_names = {task: sorted({row[task] for row in rows}) for task in TASKS}
    truth = {
        task: np.asarray([{name: i for i, name in enumerate(label_names[task])}[row[task]] for row in rows])
        for task in TASKS
    }
    predictions = {task: np.full(len(rows), -1, dtype=int) for task in TASKS}
    fold_details = []

    for fold in range(1, 6):
        train = np.where(folds != fold)[0]
        test = np.where(folds == fold)[0]
        splits = {
            task: list(StratifiedKFold(3, shuffle=True, random_state=96000 + fold * 10 + ti).split(train, truth[task][train]))
            for ti, task in enumerate(TASKS)
        }
        view_scores = {}
        for vi, view in enumerate(VIEWS):
            view_scores[view] = {}
            for ti, task in enumerate(TASKS):
                scores = []
                for si, (inner_train, inner_valid) in enumerate(splits[task]):
                    a, b = train[inner_train], train[inner_valid]
                    model = classifier(seed=96100 + fold * 1000 + vi * 100 + ti * 10 + si)
                    model.fit(texts[view][a], truth[task][a])
                    scores.append(f1_score(truth[task][b], model.predict(texts[view][b]), average="micro"))
                view_scores[view][task] = float(np.mean(scores))
        selected_view = max(
            VIEWS,
            key=lambda view: (min(view_scores[view].values()), np.mean(list(view_scores[view].values()))),
        )
        detail = {"fold": fold, "selected_view": selected_view, "view_inner_micro_f1": view_scores, "tasks": {}}
        for ti, task in enumerate(TASKS):
            candidates = []
            for hi, (name, c_value, class_weight) in enumerate(HEADS):
                scores = []
                for si, (inner_train, inner_valid) in enumerate(splits[task]):
                    a, b = train[inner_train], train[inner_valid]
                    model = classifier(c_value, class_weight, 97000 + fold * 1000 + ti * 100 + hi * 10 + si)
                    model.fit(texts[selected_view][a], truth[task][a])
                    scores.append(f1_score(truth[task][b], model.predict(texts[selected_view][b]), average="micro"))
                candidates.append({"name": name, "C": c_value, "class_weight": class_weight, "inner_micro_f1": float(np.mean(scores))})
            chosen = max(candidates, key=lambda item: item["inner_micro_f1"])
            model = classifier(chosen["C"], chosen["class_weight"], 98000 + fold * 10 + ti)
            model.fit(texts[selected_view][train], truth[task][train])
            predictions[task][test] = model.predict(texts[selected_view][test])
            outer = float(f1_score(truth[task][test], predictions[task][test], average="micro"))
            detail["tasks"][task] = {"selected_head": chosen, "head_candidates": candidates, "outer_micro_f1": outer}
            print(f"fold={fold} view={selected_view} task={task} head={chosen['name']} outer={outer:.6f}", flush=True)
        fold_details.append(detail)

    assert all(np.all(predictions[task] >= 0) for task in TASKS)
    fields = ["sample_id", "fold"] + [field for task in TASKS for field in (task + "_truth", task + "_pred")]
    with (OUT / "predictions.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for i, sid in enumerate(ids):
            result_row = {"sample_id": sid, "fold": int(folds[i])}
            for task in TASKS:
                result_row[task + "_truth"] = label_names[task][truth[task][i]]
                result_row[task + "_pred"] = label_names[task][predictions[task][i]]
            writer.writerow(result_row)
    micro = {task: float(f1_score(truth[task], predictions[task], average="micro")) for task in TASKS}
    macro = {task: float(f1_score(truth[task], predictions[task], average="macro")) for task in TASKS}
    result = {
        "schema": "tempo-micro-e06-v1",
        "status": "complete",
        "model_contract": "one selected VLM text view per outer fold with three LinearSVC task heads",
        "selection": "view maximizes minimum inner micro-F1 across three tasks; each head tuned in inner CV",
        "excluded_inputs": ["task2_domain pseudo-label", "task2_source_description", "task2_mapping_note", "task3_primary_entity"],
        "micro_f1": micro,
        "macro_f1_diagnostic": macro,
        "minimum_micro_f1": min(micro.values()),
        "all_tasks_at_least_0_70": min(micro.values()) >= 0.70,
        "fold_details": fold_details,
        "source_sha256": {str(path.relative_to(ROOT)): sha256(path) for path in (DATA, FOLDS, DESC, ZERO)},
        "caption_records": len(captions),
        "seconds": time.time() - started,
        "predictions_sha256": sha256(OUT / "predictions.csv"),
    }
    (OUT / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({key: result[key] for key in ("micro_f1", "macro_f1_diagnostic", "minimum_micro_f1", "all_tasks_at_least_0_70", "seconds")}, indent=2))


if __name__ == "__main__":
    main()
