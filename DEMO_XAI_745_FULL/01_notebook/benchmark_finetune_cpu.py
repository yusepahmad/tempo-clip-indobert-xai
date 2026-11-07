"""Benchmark terbatas; bukan runner evaluasi 5-fold atau hasil skripsi."""
import argparse
import json
import math
import os
from pathlib import Path
import resource
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--steps", type=int, default=3)
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if min(args.steps, args.batch_size, args.threads) < 1:
        parser.error("steps, batch-size, threads harus positif")
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
    import torch
    import numpy as np
    import pandas as pd
    from torch.utils.data import DataLoader
    torch.set_num_threads(args.threads)
    torch.manual_seed(42)
    root = Path(__file__).resolve().parents[1]
    notebook = json.loads((root / "01_notebook/finetune_encoder_colab.ipynb").read_text())
    # Definisi tetap mengikuti notebook eksperimen; setup Colab/CV tidak dieksekusi.
    scope = {"torch": torch, "np": np, "pd": pd,
             "DATA_CSV": root / "03_data/DATASET_740_TASK2_DOMAIN.csv",
             "DIR_GAMBAR": root / "05_gambar"}
    for index in (7, 9, 10, 12):
        source = "".join(notebook["cells"][index]["source"])
        if index == 12:
            source = source.split("# Uji cepat:")[0]
        exec(compile(source, f"notebook-cell-{index}", "exec"), scope)
    tasks, df = scope["TASKS"], scope["df"]
    if args.steps * args.batch_size > len(df):
        parser.error("jumlah sampul benchmark melebihi dataset")
    # Bersihkan NaN pada salinan benchmark, tanpa mengubah dataset sumber.
    df["supporting_text_verified"] = df["supporting_text_verified"].fillna("")
    model = scope["ModelFineTuned"](scope["n_kelas"]).cpu().train()
    optimizer = torch.optim.AdamW(model.parameters(), lr=2e-5, weight_decay=1e-4)
    dataset = scope["SampulDataset"](df, np.arange(args.steps * args.batch_size))
    loader = DataLoader(dataset, batch_size=args.batch_size, num_workers=0)
    loss_fn = torch.nn.CrossEntropyLoss()
    durations, losses = [], []
    gradient_ok = {}
    for step, (images, ids, mask, labels) in enumerate(loader, 1):
        start = time.perf_counter()
        optimizer.zero_grad(set_to_none=True)
        out = model(images, ids, mask)
        loss = sum(loss_fn(out[t], labels[t]) for t in tasks) / len(tasks)
        if not torch.isfinite(loss):
            raise RuntimeError("Loss tidak finite")
        loss.backward()
        for name in ("clip", "bert"):
            gradient_ok[name] = any(p.grad is not None and torch.isfinite(p.grad).all().item()
                                   and p.grad.abs().sum().item() > 0
                                   for p in getattr(model, name).parameters())
        if not all(gradient_ok.values()):
            raise RuntimeError("Gradien encoder tidak valid")
        optimizer.step()
        durations.append(time.perf_counter() - start)
        losses.append(loss.item())
        print(f"Step {step}: {durations[-1]:.2f}s, loss={losses[-1]:.4f}", flush=True)
    steady = sum(durations[1:] or durations) / len(durations[1:] or durations)
    report = {
        "purpose": "benchmark CPU, bukan hasil evaluasi ilmiah",
        "cpu": next((line.split(":", 1)[1].strip() for line in Path("/proc/cpuinfo").read_text().splitlines() if line.startswith("model name")), "unknown"),
        "torch": torch.__version__, "cuda_available": torch.cuda.is_available(),
        "dataset_rows": len(df), "images_verified": len(df),
        "threads": args.threads, "batch_size": args.batch_size,
        "step_seconds": durations, "loss": losses, "encoder_gradients_valid": gradient_ok,
        "peak_process_rss_gib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024**2,
        "estimated_train_only_hours_5fold_120epochs": steady * math.ceil(len(df) * 0.8 / args.batch_size) * 120 * 5 / 3600,
        "caveat": "Ekstrapolasi batch/thread ini; tidak mencakup loading data, evaluasi, saving, panas CPU atau batch GPU 16. Loss tanpa class weighting hanya untuk benchmark."
    }
    output = args.output or root / "04_hasil_eksperimen/benchmark_finetune_cpu.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(report, indent=2, ensure_ascii=False), flush=True)
    print(f"Disimpan: {output}")


if __name__ == "__main__":
    main()
