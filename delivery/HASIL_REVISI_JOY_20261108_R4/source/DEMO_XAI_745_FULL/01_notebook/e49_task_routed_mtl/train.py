#!/usr/bin/env python3
"""E49 Training Script: Nested Cross-Validation with Task-Routed MMoE Joint Model."""
import csv
import hashlib
import json
import time
from collections import Counter
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
from sklearn.metrics import f1_score
from sklearn.model_selection import StratifiedKFold
import torch
from torch import nn
import torch.nn.functional as F

from model import TaskRoutedMMoE, E49Config, TASKS, compute_effective_class_weights

ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = ROOT / "03_data/DATASET_740_TASK2_DOMAIN.csv"
CACHE_PATH = ROOT / "04_hasil_eksperimen/e41_cached_tail/cache/front_cache.npz"
E42_OOF = ROOT / "04_hasil_eksperimen/e42_tail_grid/oof.csv"
OUT_DIR = ROOT / "04_hasil_eksperimen/e49_task_routed_mtl"

def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()

def read_csv(p: Path) -> List[Dict[str, str]]:
    with p.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def set_seed(seed: int = 49):
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

# Define Candidate Configurations for Inner Search
CANDIDATES = [
    # cfg 0: Balanced baseline MMoE
    E49Config(num_experts=3, expert_hidden=160, tower_dim=80, dropout=0.2, visual_scale=1.5, text_scale=1.0,
              lr=1e-3, weight_decay=1e-4, epochs=45, loss_weights=(1.0, 1.5, 1.5), class_weight_power=0.5, label_smoothing=0.05),
    # cfg 1: Higher visual scale, 4 experts
    E49Config(num_experts=4, expert_hidden=192, tower_dim=96, dropout=0.25, visual_scale=2.0, text_scale=1.0,
              lr=1e-3, weight_decay=1e-4, epochs=45, loss_weights=(1.0, 1.5, 1.5), class_weight_power=0.5, label_smoothing=0.05),
    # cfg 2: Equal loss weights, moderate power
    E49Config(num_experts=4, expert_hidden=192, tower_dim=96, dropout=0.2, visual_scale=1.5, text_scale=1.0,
              lr=8e-4, weight_decay=2e-4, epochs=45, loss_weights=(1.0, 1.0, 1.0), class_weight_power=0.4, label_smoothing=0.05),
    # cfg 3: Higher Task 2/3 focus, 4 experts
    E49Config(num_experts=4, expert_hidden=192, tower_dim=96, dropout=0.2, visual_scale=1.8, text_scale=1.0,
              lr=1e-3, weight_decay=1e-4, epochs=45, loss_weights=(1.0, 2.0, 2.0), class_weight_power=0.5, label_smoothing=0.08),
    # cfg 4: Compact MMoE, lower lr
    E49Config(num_experts=3, expert_hidden=128, tower_dim=64, dropout=0.15, visual_scale=1.5, text_scale=1.0,
              lr=6e-4, weight_decay=1e-4, epochs=45, loss_weights=(1.0, 1.5, 1.5), class_weight_power=0.45, label_smoothing=0.05),
]

def train_one_model(
    v_train: torch.Tensor,
    t_train: torch.Tensor,
    y_train: Dict[str, torch.Tensor],
    num_classes: Dict[str, int],
    cfg: E49Config,
    epochs: int,
    device: torch.device
) -> TaskRoutedMMoE:
    set_seed(cfg.seed)
    model = TaskRoutedMMoE(num_classes, cfg).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=cfg.lr, weight_decay=cfg.weight_decay)

    # Class-weighted loss
    loss_fns = {}
    for task in TASKS:
        weights = compute_effective_class_weights(y_train[task].cpu().numpy(), num_classes[task], power=cfg.class_weight_power).to(device)
        loss_fns[task] = nn.CrossEntropyLoss(weight=weights, label_smoothing=cfg.label_smoothing)

    n_samples = len(v_train)
    bsz = cfg.batch_size

    model.train()
    for ep in range(epochs):
        perm = torch.randperm(n_samples)
        for i in range(0, n_samples, bsz):
            idx = perm[i:i + bsz]
            batch_v = v_train[idx].to(device)
            batch_t = t_train[idx].to(device)

            optimizer.zero_grad()
            logits = model(batch_v, batch_t)

            loss = sum(
                w * loss_fns[task](logits[task], y_train[task][idx].to(device))
                for task, w in zip(TASKS, cfg.loss_weights)
            ) / sum(cfg.loss_weights)

            loss.backward()
            optimizer.step()

    model.eval()
    return model

@torch.no_grad()
def predict_model(
    model: TaskRoutedMMoE,
    v_test: torch.Tensor,
    t_test: torch.Tensor,
    device: torch.device
) -> Dict[str, np.ndarray]:
    model.eval()
    v_test = v_test.to(device)
    t_test = t_test.to(device)
    logits = model(v_test, t_test)
    preds = {}
    for task in TASKS:
        preds[task] = torch.argmax(logits[task], dim=-1).cpu().numpy()
    return preds

def evaluate_predictions(y_true: Dict[str, np.ndarray], y_pred: Dict[str, np.ndarray], num_classes: Dict[str, int]) -> Dict[str, float]:
    scores = {}
    for task in TASKS:
        scores[task] = float(f1_score(y_true[task], y_pred[task], labels=list(range(num_classes[task])), average="macro", zero_division=0))
    scores["min"] = min(scores[t] for t in TASKS)
    scores["mean"] = float(np.mean([scores[t] for t in TASKS]))
    return scores

def main():
    start_time = time.time()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    device = torch.device("cpu")

    rows = read_csv(DATA_PATH)
    e42_rows = read_csv(E42_OOF)
    cache = np.load(CACHE_PATH)

    assert len(rows) == 740
    assert len(e42_rows) == 740
    sample_ids = [r["sample_id"] for r in rows]
    assert sample_ids == cache["sample_ids"].tolist()
    assert sample_ids == [r["sample_id"] for r in e42_rows]

    # Labels and encodings
    label_encoders = {}
    num_classes = {}
    y_encoded = {}
    for task in TASKS:
        unique_labels = sorted({r[task] for r in rows})
        label_encoders[task] = unique_labels
        num_classes[task] = len(unique_labels)
        enc = {label: i for i, label in enumerate(unique_labels)}
        y_encoded[task] = np.array([enc[r[task]] for r in rows], dtype=np.int64)

    # Features
    v_features = torch.tensor(cache["visual"], dtype=torch.float32)
    t_features = torch.tensor(cache["base_mean"], dtype=torch.float32)

    # Outer fold assignments from E42
    outer_folds = np.array([int(r["fold"]) for r in e42_rows])
    assert set(outer_folds) == {1, 2, 3, 4, 5}

    print(f"=== Starting E49 Nested Cross-Validation (5 Outer Folds) ===")
    oof_predictions = {task: np.full(740, -1, dtype=np.int64) for task in TASKS}
    fold_details = []

    for fold in range(1, 6):
        fold_start = time.time()
        train_idx = np.where(outer_folds != fold)[0]
        test_idx = np.where(outer_folds == fold)[0]

        print(f"\n--- Outer Fold {fold}/5: {len(train_idx)} train, {len(test_idx)} test ---")

        # Inner 3-fold split on train_idx, stratified by Task 2
        inner_strat = y_encoded["task2_domain_sumber"][train_idx]
        skf = StratifiedKFold(n_splits=3, shuffle=True, random_state=4900 + fold)
        inner_splits = list(skf.split(train_idx, inner_strat))

        best_candidate_idx = 0
        best_objective = -1.0
        best_candidate_metrics = None

        # Search across CANDIDATES on inner folds
        for c_idx, cfg in enumerate(CANDIDATES):
            inner_scores = []
            for in_tr_local, in_val_local in inner_splits:
                in_tr = train_idx[in_tr_local]
                in_val = train_idx[in_val_local]

                in_v_tr, in_t_tr = v_features[in_tr], t_features[in_tr]
                in_y_tr = {task: torch.tensor(y_encoded[task][in_tr]) for task in TASKS}

                in_v_val, in_t_val = v_features[in_val], t_features[in_val]
                in_y_val = {task: y_encoded[task][in_val] for task in TASKS}

                # Train model on inner train
                inner_model = train_one_model(
                    in_v_tr, in_t_tr, in_y_tr, num_classes, cfg, epochs=cfg.epochs, device=device
                )
                val_preds = predict_model(inner_model, in_v_val, in_t_val, device)
                eval_metrics = evaluate_predictions(in_y_val, val_preds, num_classes)
                inner_scores.append(eval_metrics)

            mean_min = float(np.mean([s["min"] for s in inner_scores]))
            mean_mean = float(np.mean([s["mean"] for s in inner_scores]))
            mean_task1 = float(np.mean([s["task1_issue"] for s in inner_scores]))
            mean_task2 = float(np.mean([s["task2_domain_sumber"] for s in inner_scores]))
            mean_task3 = float(np.mean([s["task3_primary_entity_type"] for s in inner_scores]))

            print(f"  Candidate {c_idx}: inner min={mean_min:.4f}, mean={mean_mean:.4f} (T1:{mean_task1:.4f}, T2:{mean_task2:.4f}, T3:{mean_task3:.4f})")

            # Selection rule: maximize min(T1, T2, T3), tie-break by mean
            if (mean_min > best_objective) or (np.isclose(mean_min, best_objective) and mean_mean > best_candidate_metrics["mean"]):
                best_objective = mean_min
                best_candidate_idx = c_idx
                best_candidate_metrics = {
                    "min": mean_min, "mean": mean_mean,
                    "task1": mean_task1, "task2": mean_task2, "task3": mean_task3
                }

        selected_cfg = CANDIDATES[best_candidate_idx]
        print(f"  => Selected Candidate {best_candidate_idx} with inner min {best_objective:.4f}")

        # Retrain on full train_idx with selected config
        outer_v_tr, outer_t_tr = v_features[train_idx], t_features[train_idx]
        outer_y_tr = {task: torch.tensor(y_encoded[task][train_idx]) for task in TASKS}

        outer_model = train_one_model(
            outer_v_tr, outer_t_tr, outer_y_tr, num_classes, selected_cfg, epochs=selected_cfg.epochs, device=device
        )

        # Predict on outer test fold
        outer_v_te, outer_t_te = v_features[test_idx], t_features[test_idx]
        outer_preds = predict_model(outer_model, outer_v_te, outer_t_te, device)

        for task in TASKS:
            oof_predictions[task][test_idx] = outer_preds[task]

        # Calculate outer fold score
        outer_true = {task: y_encoded[task][test_idx] for task in TASKS}
        outer_metrics = evaluate_predictions(outer_true, outer_preds, num_classes)
        print(f"  Outer Fold {fold} Result: min={outer_metrics['min']:.4f}, mean={outer_metrics['mean']:.4f}")
        print(f"    T1: {outer_metrics['task1_issue']:.4f}, T2: {outer_metrics['task2_domain_sumber']:.4f}, T3: {outer_metrics['task3_primary_entity_type']:.4f}")
        print(f"    Elapsed: {time.time() - fold_start:.1f}s")

        fold_details.append({
            "fold": fold,
            "selected_candidate_idx": best_candidate_idx,
            "inner_metrics": best_candidate_metrics,
            "outer_metrics": outer_metrics,
            "train_size": len(train_idx),
            "test_size": len(test_idx)
        })

    # Verify all 740 predictions are filled
    for task in TASKS:
        assert (oof_predictions[task] >= 0).all(), f"Unfilled predictions in {task}"

    # Overall 740 OOF Evaluation
    oof_true = {task: y_encoded[task] for task in TASKS}
    overall_scores = evaluate_predictions(oof_true, oof_predictions, num_classes)
    total_elapsed = time.time() - start_time

    print(f"\n=======================================================")
    print(f"=== E49 OVERALL 740 SAMPLES OOF RESULTS ===")
    print(f"Task 1 (Issue) Macro-F1:       {overall_scores['task1_issue']:.4f}")
    print(f"Task 2 (Domain) Macro-F1:      {overall_scores['task2_domain_sumber']:.4f}")
    print(f"Task 3 (Entity) Macro-F1:      {overall_scores['task3_primary_entity_type']:.4f}")
    print(f"Minimum across tasks:          {overall_scores['min']:.4f}")
    print(f"Mean across tasks:             {overall_scores['mean']:.4f}")
    print(f"Total training time:           {total_elapsed:.1f}s")
    print(f"=======================================================")

    # Write OOF CSV
    oof_csv_path = OUT_DIR / "oof.csv"
    with oof_csv_path.open("w", encoding="utf-8", newline="") as f:
        fieldnames = ["sample_id", "fold"]
        for task in TASKS:
            fieldnames.extend([f"{task}_truth", f"{task}_pred"])
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for i in range(740):
            row_dict = {
                "sample_id": sample_ids[i],
                "fold": str(outer_folds[i])
            }
            for task in TASKS:
                row_dict[f"{task}_truth"] = label_encoders[task][y_encoded[task][i]]
                row_dict[f"{task}_pred"] = label_encoders[task][oof_predictions[task][i]]
            writer.writerow(row_dict)

    # Write result.json
    result_json_path = OUT_DIR / "result.json"
    result_data = {
        "experiment": "E49_task_routed_mmoe_mtl",
        "date": "2026-10-17",
        "dataset_sha256": sha256_file(DATA_PATH),
        "cache_sha256": sha256_file(CACHE_PATH),
        "e42_oof_sha256": sha256_file(E42_OOF),
        "oof_csv_sha256": sha256_file(oof_csv_path),
        "overall_scores": overall_scores,
        "fold_details": fold_details,
        "total_seconds": total_elapsed,
        "contract": {
            "joint_model": True,
            "single_graph": True,
            "tasks": list(TASKS),
            "samples": 740,
            "protocol": "5-fold outer nested CV on exact E42 splits"
        }
    }
    with result_json_path.open("w", encoding="utf-8") as f:
        json.dump(result_data, f, indent=2, sort_keys=True)

    print(f"\nArtifacts successfully saved to {OUT_DIR}")

if __name__ == "__main__":
    main()
