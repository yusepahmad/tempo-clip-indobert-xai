"""Full encoder GPU benchmark, batch 1, AMP, checkpointing; no CV results."""
import argparse
import gc
import json
import os
from pathlib import Path
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--steps", type=int, default=3)
    parser.add_argument("--weights", type=Path, required=True)
    args = parser.parse_args()
    if args.steps < 1:
        parser.error("steps must be positive")
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    import torch
    import pandas as pd
    import numpy as np
    from torch.utils.data import DataLoader
    if not torch.cuda.is_available():
        raise SystemExit("CUDA unavailable")
    torch.set_num_threads(4)
    torch.manual_seed(42)
    root = Path(__file__).resolve().parents[1]
    notebook = json.loads((root / "01_notebook/finetune_encoder_colab.ipynb").read_text())
    scope = {"torch": torch, "np": np, "pd": pd,
             "DATA_CSV": root / "03_data/DATASET_740_TASK2_DOMAIN.csv",
             "DIR_GAMBAR": root / "05_gambar"}
    for index in (7, 9, 10, 12):
        source = "".join(notebook["cells"][index]["source"])
        if index == 9:
            source = source.replace('CLIP_PRETRAINED = "laion2b_s34b_b79k"',
                                    "CLIP_PRETRAINED = " + repr(str(args.weights / "clip/open_clip_model.safetensors")))
            source = source.replace('INDOBERT = "indobenchmark/indobert-base-p1"',
                                    "INDOBERT = " + repr(str(args.weights / "indobert")))
        if index == 12:
            source = source.split("# Uji cepat:")[0]
        exec(compile(source, f"notebook-cell-{index}", "exec"), scope)
    df, tasks = scope["df"], scope["TASKS"]
    df["supporting_text_verified"] = df["supporting_text_verified"].fillna("")
    if args.steps > len(df):
        parser.error("steps exceed dataset length")
    model = scope["ModelFineTuned"](scope["n_kelas"])
    # Discard only unused CLIP text tower. Both used encoders remain trainable.
    removed = []
    for name in ("transformer", "token_embedding", "ln_final", "positional_embedding",
                 "text_projection", "logit_scale", "logit_bias", "attn_mask"):
        if hasattr(model.clip, name):
            delattr(model.clip, name)
            removed.append(name)
    model.clip.visual.set_grad_checkpointing(True)
    model.bert.gradient_checkpointing_enable()
    gc.collect()
    model = model.cuda().train()
    optimizer = torch.optim.AdamW(model.parameters(), lr=2e-5, weight_decay=1e-4, foreach=False)
    scaler = torch.amp.GradScaler("cuda", init_scale=1024)
    loader = DataLoader(scope["SampulDataset"](df, np.arange(args.steps)), batch_size=1, num_workers=0)
    loss_fn = torch.nn.CrossEntropyLoss()
    report = {"purpose": "GPU benchmark only, not scientific evaluation", "gpu": torch.cuda.get_device_name(0),
              "torch": torch.__version__, "cuda": torch.version.cuda,
              "vram_gib": torch.cuda.get_device_properties(0).total_memory / 1024**3,
              "dataset_rows": len(df), "images_verified": len(df), "batch_size": 1,
              "amp": "float16", "gradient_checkpointing": True,
              "unused_clip_modules_removed": removed,
              "trainable_parameters": sum(p.numel() for p in model.parameters() if p.requires_grad),
              "step_seconds": [], "loss": [], "encoder_gradients_valid": {},
              "encoder_weights_updated": {}, "status": "running"}
    torch.cuda.reset_peak_memory_stats()
    try:
        for step, (images, ids, mask, labels) in enumerate(loader, 1):
            torch.cuda.synchronize()
            start = time.perf_counter()
            optimizer.zero_grad(set_to_none=True)
            with torch.autocast("cuda", dtype=torch.float16):
                out = model(images.cuda(), ids.cuda(), mask.cuda())
                loss = sum(loss_fn(out[t], labels[t].cuda()) for t in tasks) / len(tasks)
            if not torch.isfinite(loss).item():
                raise RuntimeError("Nonfinite loss")
            scaler.scale(loss).backward()
            scaler.unscale_(optimizer)
            for name in ("clip", "bert"):
                parameters = [p for p in getattr(model, name).parameters() if p.grad is not None]
                report["encoder_gradients_valid"][name] = (
                    all(torch.isfinite(p.grad).all().item() for p in parameters)
                    and any(p.grad.abs().sum().item() > 0 for p in parameters))
            if not all(report["encoder_gradients_valid"].values()):
                raise RuntimeError("Missing or nonfinite encoder gradients")
            if not all(torch.isfinite(p.grad).all().item() for p in model.parameters() if p.grad is not None):
                raise RuntimeError("Nonfinite gradients")
            probes = {}
            for name, encoder in (("clip", model.clip.visual), ("bert", model.bert)):
                parameter = next(p for p in encoder.parameters()
                                 if p.grad is not None and p.grad.abs().sum().item() > 0)
                index = parameter.grad.abs().flatten().argmax().item()
                probes[name] = (parameter, index, parameter.detach().flatten()[index].item())
            scaler.step(optimizer)
            scaler.update()
            report["encoder_weights_updated"] = {
                name: parameter.detach().flatten()[index].item() != before
                for name, (parameter, index, before) in probes.items()}
            if not all(report["encoder_weights_updated"].values()):
                raise RuntimeError("Encoder weights did not change")
            torch.cuda.synchronize()
            duration = time.perf_counter() - start
            report["step_seconds"].append(duration)
            report["loss"].append(loss.item())
            print(f"Step {step}: {duration:.2f}s, loss={loss.item():.4f}", flush=True)
        report["status"] = "success"
    except torch.cuda.OutOfMemoryError as error:
        report["status"] = "out_of_memory"
        report["error"] = str(error)
    except Exception as error:
        report["status"] = "failed"
        report["error"] = repr(error)
        raise
    finally:
        report["peak_allocated_gib"] = torch.cuda.max_memory_allocated() / 1024**3
        report["peak_reserved_gib"] = torch.cuda.max_memory_reserved() / 1024**3
        if report["status"] == "success":
            timings = report["step_seconds"][1:] or report["step_seconds"]
            report["estimated_train_only_hours_5fold_120epochs"] = sum(timings) / len(timings) * 592 * 120 * 5 / 3600
        report["caveat"] = "Short extrapolation, batch 1; excludes heat, data loading, evaluation, saving. No class weighting."
        path = root / "04_hasil_eksperimen/benchmark_finetune_gpu.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps(report, indent=2), flush=True)
    if report["status"] != "success":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
