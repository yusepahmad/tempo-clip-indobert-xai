"""One-epoch Kaggle GPU benchmark; not final CV results."""
import gc
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import zipfile

started = time.perf_counter()
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["HF_HUB_OFFLINE"] = "1"
inputs = Path("/kaggle/input")
csv_paths = list(inputs.rglob("DATASET_740_TASK2_DOMAIN.csv"))
if not csv_paths:
    destination = Path("/kaggle/working/input_extracted")
    for archive in inputs.rglob("tempo_benchmark_input.zip"):
        with zipfile.ZipFile(archive) as handle:
            handle.extractall(destination)
    csv_paths = list(destination.rglob("DATASET_740_TASK2_DOMAIN.csv"))
if len(csv_paths) != 1:
    raise RuntimeError(f"Expected exactly one dataset CSV, found {len(csv_paths)}")
root = csv_paths[0].parents[1]
import numpy as np
import pandas as pd
import torch
from collections import Counter
from sklearn.model_selection import StratifiedKFold
from torch.utils.data import DataLoader
if not torch.cuda.is_available():
    raise SystemExit("GPU unavailable: select a GPU runtime")
import torch.distributed as dist
from torch.nn.parallel import DistributedDataParallel
from torch.utils.data.distributed import DistributedSampler
rank = int(os.environ["LOCAL_RANK"])
torch.cuda.set_device(rank)
dist.init_process_group("nccl")
torch.set_num_threads(2)
torch.manual_seed(42)
print("GPU:", torch.cuda.get_device_name(0), "GPU count:", torch.cuda.device_count(), flush=True)
notebook = json.loads((root / "01_notebook/finetune_encoder_colab.ipynb").read_text())
scope = {"torch": torch, "np": np, "pd": pd, "DATA_CSV": csv_paths[0], "DIR_GAMBAR": root / "05_gambar"}
for index in (7, 9, 10, 12):
    source = "".join(notebook["cells"][index]["source"])
    if index == 9:
        source = source.replace('CLIP_PRETRAINED = "laion2b_s34b_b79k"',
                                "CLIP_PRETRAINED = " + repr(str(root / "weights/clip/open_clip_model.safetensors")))
        source = source.replace('INDOBERT = "indobenchmark/indobert-base-p1"',
                                "INDOBERT = " + repr(str(root / "weights/indobert")))
    if index == 12:
        source = source.split("# Uji cepat:")[0]
    exec(compile(source, f"notebook-cell-{index}", "exec"), scope)
df, tasks, y, n_classes = scope["df"], scope["TASKS"], scope["y"], scope["n_kelas"]
df["supporting_text_verified"] = df["supporting_text_verified"].fillna("")
counter = Counter(y["task1_issue"])
strat = np.array([c if counter[c] >= 5 else -1 for c in y["task1_issue"]])
train_indices, test_indices = next(StratifiedKFold(n_splits=5, shuffle=True, random_state=42).split(np.zeros(len(df)), strat))
model = scope["ModelFineTuned"](n_classes)
for name in ("transformer", "token_embedding", "ln_final", "positional_embedding",
             "text_projection", "logit_scale", "logit_bias", "attn_mask"):
    if hasattr(model.clip, name):
        delattr(model.clip, name)
gc.collect()
model = model.cuda().train()
raw_model = model
model = DistributedDataParallel(model, device_ids=[rank], find_unused_parameters=True)
optimizer = torch.optim.AdamW(model.parameters(), lr=2e-5, weight_decay=1e-4, foreach=False)
scaler = torch.amp.GradScaler("cuda", init_scale=1024)
weights = {}
for task in tasks:
    counts = np.bincount(y[task][train_indices], minlength=n_classes[task]).astype(np.float32)
    weights[task] = torch.tensor(np.where(counts > 0,
        len(train_indices) / (np.maximum(counts, 1) * (counts > 0).sum()), 0), device="cuda", dtype=torch.float32)
dataset = scope["SampulDataset"](df, train_indices)
sampler = DistributedSampler(dataset, num_replicas=2, rank=rank, shuffle=True, seed=42)
loader = DataLoader(dataset, batch_size=8, sampler=sampler, num_workers=0)
report = {"purpose": "one epoch fold 1 benchmark, not final CV evaluation", "dataset_rows": len(df),
          "images_verified": len(df), "train_samples": len(train_indices), "test_samples": len(test_indices),
          "gpu": torch.cuda.get_device_name(0), "gpu_count": torch.cuda.device_count(), "gpus_used": 2, "local_rank": rank, "local_batch_size": 8,
          "torch": torch.__version__, "vram_gib": torch.cuda.get_device_properties(0).total_memory / 1024**3,
          "batch_size": 16, "amp": "float16", "gradient_checkpointing": False,
          "trainable_parameters": sum(p.numel() for p in model.parameters() if p.requires_grad),
          "setup_seconds": time.perf_counter() - started, "encoder_weights_updated": {}, "status": "running"}
dist.barrier()
torch.cuda.synchronize()
torch.cuda.reset_peak_memory_stats()
epoch_started = time.perf_counter()
loss_sum = 0.0
try:
    for step, (images, ids, mask, labels) in enumerate(loader, 1):
        optimizer.zero_grad(set_to_none=True)
        with torch.autocast("cuda", dtype=torch.float16):
            outputs = model(images.cuda(), ids.cuda(), mask.cuda())
            denominators = torch.stack([weights[t][labels[t].cuda()].sum() for t in tasks])
            dist.all_reduce(denominators)
            loss = sum(torch.nn.functional.cross_entropy(outputs[t], labels[t].cuda(), weight=weights[t], reduction="sum")
                       * 2 / denominators[i] for i, t in enumerate(tasks)) / len(tasks)
        if not torch.isfinite(loss).item():
            raise RuntimeError("Nonfinite loss")
        scaler.scale(loss).backward()
        scaler.unscale_(optimizer)
        if not all(torch.isfinite(p.grad).all().item() for p in model.parameters() if p.grad is not None):
            raise RuntimeError("Nonfinite gradients")
        probes = {}
        if step == 1:
            for name, encoder in (("clip", raw_model.clip.visual), ("bert", raw_model.bert)):
                p = next(p for p in encoder.parameters() if p.grad is not None and p.grad.abs().sum().item() > 0)
                index = p.grad.abs().flatten().argmax().item()
                probes[name] = (p, index, p.detach().flatten()[index].item())
        scaler.step(optimizer)
        scaler.update()
        if step == 1:
            report["encoder_weights_updated"] = {name: p.detach().flatten()[index].item() != before
                for name, (p, index, before) in probes.items()}
            if not all(report["encoder_weights_updated"].values()):
                raise RuntimeError("Encoder weights did not change")
        loss_sum += loss.item()
        if step == 1 or step % 5 == 0:
            print(f"Training step {step}/{len(loader)}, loss={loss.item():.4f}", flush=True)
        del outputs, loss
    torch.cuda.synchronize()
    dist.barrier()
    report["epoch_train_seconds"] = time.perf_counter() - epoch_started
    report["mean_training_loss"] = loss_sum / len(loader)
    optimizer.zero_grad(set_to_none=True)
    raw_model.eval()
    evaluation_started = time.perf_counter()
    tested = 0
    with torch.no_grad():
        for images, ids, mask, labels in DataLoader(scope["SampulDataset"](df, test_indices[rank::2]), batch_size=8, num_workers=0):
            with torch.autocast("cuda", dtype=torch.float16):
                outputs = raw_model(images.cuda(), ids.cuda(), mask.cuda())
            assert all(torch.isfinite(v).all().item() for v in outputs.values())
            tested += len(images)
            del outputs
    torch.cuda.synchronize()
    report["fold_evaluation_seconds"] = time.perf_counter() - evaluation_started
    count = torch.tensor(tested, device="cuda")
    dist.all_reduce(count)
    report["evaluated_samples"] = count.item()
    elapsed = torch.tensor(report["fold_evaluation_seconds"], device="cuda")
    dist.all_reduce(elapsed, op=dist.ReduceOp.MAX)
    report["fold_evaluation_seconds"] = elapsed.item()
    report["estimated_train_hours_5fold_120epochs"] = report["epoch_train_seconds"] * 600 / 3600
    report["status"] = "success"
except Exception as error:
    report["status"] = "failed"
    report["error"] = repr(error)
    raise
finally:
    report["peak_allocated_gib"] = torch.cuda.max_memory_allocated() / 1024**3
    report["peak_reserved_gib"] = torch.cuda.max_memory_reserved() / 1024**3
    report["total_job_seconds"] = time.perf_counter() - started
    report["caveat"] = "First epoch extrapolation excludes later setup, checkpoints, dataset upload, quota accounting and runtime variation. Two GPUs DDP; global weighted CE denominator; first epoch only."
    Path(f"/kaggle/working/benchmark_dual_rank{rank}.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2), flush=True)

dist.destroy_process_group()
