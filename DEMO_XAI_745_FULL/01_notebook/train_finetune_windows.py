"""Local full fine-tuning: 5 folds, 120 epochs, GPU microbatch 1.

--smoke-test executes only one effective batch, never writes CV results.
"""
import argparse
from collections import Counter
import gc
import json
import os
from pathlib import Path
import time


def setup(root, weights):
    import torch
    import pandas as pd
    import numpy as np
    torch.set_num_threads(4)
    notebook = json.loads((root / "01_notebook/finetune_encoder_colab.ipynb").read_text())
    scope = {"torch": torch, "np": np, "pd": pd,
             "DATA_CSV": root / "03_data/DATASET_740_TASK2_DOMAIN.csv",
             "DIR_GAMBAR": root / "05_gambar"}
    for index in (7, 9, 10, 12):
        source = "".join(notebook["cells"][index]["source"])
        if index == 9:
            source = source.replace('CLIP_PRETRAINED = "laion2b_s34b_b79k"',
                                    "CLIP_PRETRAINED = " + repr(str(weights / "clip/open_clip_model.safetensors")))
            source = source.replace('INDOBERT = "indobenchmark/indobert-base-p1"',
                                    "INDOBERT = " + repr(str(weights / "indobert")))
        if index == 12:
            source = source.split("# Uji cepat:")[0]
        exec(compile(source, f"notebook-cell-{index}", "exec"), scope)
    scope["df"]["supporting_text_verified"] = scope["df"]["supporting_text_verified"].fillna("")
    return scope


def new_model(scope):
    model = scope["ModelFineTuned"](scope["n_kelas"])
    for name in ("transformer", "token_embedding", "ln_final", "positional_embedding",
                 "text_projection", "logit_scale", "logit_bias", "attn_mask"):
        if hasattr(model.clip, name):
            delattr(model.clip, name)
    model.clip.visual.set_grad_checkpointing(True)
    model.bert.gradient_checkpointing_enable()
    gc.collect()
    return model.cuda()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--weights", type=Path, required=True)
    parser.add_argument("--smoke-test", action="store_true")
    args = parser.parse_args()
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    import torch
    import numpy as np
    from torch.utils.data import DataLoader
    from sklearn.model_selection import StratifiedKFold
    from sklearn.metrics import accuracy_score, f1_score, precision_recall_fscore_support
    if not torch.cuda.is_available():
        raise SystemExit("CUDA unavailable")
    root = Path(__file__).resolve().parents[1]
    scope = setup(root, args.weights.resolve())
    tasks, df, y, classes = scope["TASKS"], scope["df"], scope["y"], scope["n_kelas"]
    output = root / "04_hasil_eksperimen/finetuned_windows"
    if not args.smoke_test and output.exists() and any(output.iterdir()):
        raise SystemExit(f"Output folder already contains results: {output}; archive them before rerunning")
    output.mkdir(parents=True, exist_ok=True)
    counter = Counter(y["task1_issue"])
    strat = np.array([c if counter[c] >= 5 else -1 for c in y["task1_issue"]])
    splitter = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    predictions = {t: np.full(len(df), -1, dtype=int) for t in tasks}
    fold_metrics = []
    begin = time.perf_counter()
    for fold, (train_indices, test_indices) in enumerate(splitter.split(np.zeros(len(df)), strat), 1):
        torch.manual_seed(42)
        model = new_model(scope).train()
        optimizer = torch.optim.AdamW(model.parameters(), lr=2e-5, weight_decay=1e-4, foreach=False)
        scaler = torch.amp.GradScaler("cuda", init_scale=1024)
        weights = {}
        for t in tasks:
            counts = np.bincount(y[t][train_indices], minlength=classes[t]).astype(np.float32)
            values = np.where(counts > 0, len(train_indices) / (np.maximum(counts, 1) * (counts > 0).sum()), 0)
            weights[t] = torch.tensor(values, dtype=torch.float32, device="cuda")
        loader = DataLoader(scope["SampulDataset"](df, train_indices), batch_size=16,
                            shuffle=True, num_workers=0)
        epochs = 1 if args.smoke_test else 120
        for epoch in range(epochs):
            total_loss, updates = 0.0, 0
            for images, ids, mask, labels in loader:
                optimizer.zero_grad(set_to_none=True)
                labels = {t: v.cuda() for t, v in labels.items()}
                # Weighted CE mean divides by the sum of target class weights.
                # Use the same denominator for ALL microbatches of this group;
                # averaging independently at batch 1 would cancel class weights.
                denominator = {t: weights[t][labels[t]].sum() for t in tasks}
                group_loss = 0.0
                for i in range(len(images)):
                    with torch.autocast("cuda", dtype=torch.float16):
                        logits = model(images[i:i+1].cuda(), ids[i:i+1].cuda(), mask[i:i+1].cuda())
                        loss = sum(torch.nn.functional.cross_entropy(
                            logits[t], labels[t][i:i+1], weight=weights[t], reduction="sum")
                            / denominator[t] for t in tasks) / len(tasks)
                    if not torch.isfinite(loss).item():
                        raise RuntimeError("Nonfinite loss")
                    scaler.scale(loss).backward()
                    group_loss += loss.item()
                    del logits, loss
                scaler.unscale_(optimizer)
                if not all(torch.isfinite(p.grad).all().item() for p in model.parameters() if p.grad is not None):
                    raise RuntimeError("Nonfinite gradients; lower init_scale before restarting")
                probes = {}
                if args.smoke_test:
                    for name, encoder in (("clip", model.clip.visual), ("bert", model.bert)):
                        parameter = next(p for p in encoder.parameters() if p.grad is not None
                                         and p.grad.abs().sum().item() > 0)
                        index = parameter.grad.abs().flatten().argmax().item()
                        probes[name] = (parameter, index, parameter.detach().flatten()[index].item())
                scaler.step(optimizer)
                scaler.update()
                updates += 1
                total_loss += group_loss
                if args.smoke_test:
                    torch.cuda.synchronize()
                    changed = {name: parameter.detach().flatten()[index].item() != before
                               for name, (parameter, index, before) in probes.items()}
                    if not all(changed.values()):
                        raise RuntimeError("Encoder weights did not change")
                    report = {"purpose": "one effective training batch, not CV evaluation",
                              "effective_batch_size": len(images), "microbatch_size": 1,
                              "weighted_loss": group_loss, "encoder_weights_updated": changed,
                              "seconds_including_setup": time.perf_counter() - begin,
                              "peak_allocated_gib": torch.cuda.max_memory_allocated() / 1024**3}
                    (output.parent / "smoke_training_windows.json").write_text(json.dumps(report, indent=2) + "\n")
                    print(json.dumps(report, indent=2), flush=True)
                    return
            print(f"Fold {fold}/5 epoch {epoch+1}/120 loss={total_loss/updates:.4f}", flush=True)
        optimizer.zero_grad(set_to_none=True)
        del optimizer, scaler
        model.eval()
        test_loader = DataLoader(scope["SampulDataset"](df, test_indices), batch_size=1, num_workers=0)
        fold_predictions = {t: [] for t in tasks}
        with torch.no_grad():
            for images, ids, mask, labels in test_loader:
                with torch.autocast("cuda", dtype=torch.float16):
                    logits = model(images.cuda(), ids.cuda(), mask.cuda())
                for t in tasks:
                    fold_predictions[t].extend(logits[t].argmax(1).cpu().tolist())
        metrics = {}
        for t in tasks:
            predictions[t][test_indices] = fold_predictions[t]
            metrics[t] = {"accuracy": accuracy_score(y[t][test_indices], fold_predictions[t]),
                          "macro_f1": f1_score(y[t][test_indices], fold_predictions[t], average="macro", zero_division=0)}
        fold_metrics.append({"fold": fold, "metrics": metrics})
        # Save only completed folds, no mid-fold checkpoints.
        model.cpu()
        torch.save({"state_dict": model.state_dict(), "classes": scope["peta"],
                    "unused_clip_text_tower_removed": True, "fold": fold}, output / f"fold_{fold}.pt")
        (output / f"fold_{fold}_metrics.json").write_text(json.dumps(fold_metrics[-1], indent=2) + "\n")
        np.savez(output / f"fold_{fold}_predictions.npz", indices=test_indices, **fold_predictions)
        del model, weights, logits
        gc.collect()
        torch.cuda.empty_cache()
    results = {t: {"accuracy": accuracy_score(y[t], predictions[t]),
                   "macro_f1": f1_score(y[t], predictions[t], average="macro", zero_division=0)} for t in tasks}
    report = {"metode": "full visual CLIP + IndoBERT, 5-fold CV, 120 epochs/fold",
              "hyperparameter": {"batch_size": 16, "microbatch_size": 1, "amp": "float16",
                                 "gradient_checkpointing": True, "epochs": 120, "lr": 2e-5,
                                 "weight_decay": 1e-4, "seed": 42},
              "hasil": results, "fold_metrics": fold_metrics, "classes": scope["peta"]}
    (output / "hasil_mtl_740_finetuned.json").write_text(json.dumps(report, indent=2) + "\n")
    t = "task2_domain_sumber"
    _, recall, f1, support = precision_recall_fscore_support(y[t], predictions[t],
                             labels=list(range(classes[t])), zero_division=0)
    scope["pd"].DataFrame({"kelas": scope["peta"][t], "jumlah": support, "recall": recall, "f1": f1}).to_csv(
        output / "analisis_recall_per_kelas_740_finetuned.csv", index=False)
    print(json.dumps(report, indent=2), flush=True)


if __name__ == "__main__":
    main()
