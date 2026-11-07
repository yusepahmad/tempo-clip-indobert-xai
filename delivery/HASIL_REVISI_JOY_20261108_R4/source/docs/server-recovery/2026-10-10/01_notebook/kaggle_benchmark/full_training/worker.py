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
dist.init_process_group("nccl", device_id=torch.device("cuda", rank))
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

import hashlib, random, shutil
from sklearn.metrics import accuracy_score, f1_score, precision_recall_fscore_support
smoke = os.environ.get("TEMPO_SMOKE", "0") == "1"
output = Path("/kaggle/working/tempo_smoke" if smoke else "/kaggle/working/tempo_full")
output.mkdir(exist_ok=True)
config = {"schema": 1, "folds": 5, "epochs": 120, "batch": 16, "lr": 2e-5,
          "weight_decay": 1e-4, "seed": 42, "world_size": 2, "smoke": smoke,
          "data_sha256": hashlib.sha256(csv_paths[0].read_bytes()).hexdigest(),
          "notebook_sha256": hashlib.sha256((root/"01_notebook/finetune_encoder_colab.ipynb").read_bytes()).hexdigest()}
checkpoint = output / "latest.pt"
resume = torch.load(checkpoint, map_location="cpu", weights_only=False) if checkpoint.exists() else None
if resume and resume["config"] != config:
    raise RuntimeError("Checkpoint configuration/input mismatch")
if not resume and any(output.glob("fold_*")):
    raise RuntimeError("Existing fold outputs without resume checkpoint")
stop_epoch = int(os.environ.get("TEMPO_STOP_EPOCH", "2")) if smoke else 120
splits = list(StratifiedKFold(n_splits=5, shuffle=True, random_state=42).split(np.zeros(len(df)), strat))
start_fold = resume["fold"] if resume else 1
records = []
for fold, (train_indices, test_indices) in enumerate(splits, 1):
    if fold < start_fold or (output/f"fold_{fold}_metrics.json").exists():
        continue
    if smoke and fold != 1:
        break
    random.seed(42); np.random.seed(42); torch.manual_seed(42)
    raw = scope["ModelFineTuned"](n_classes)
    for name in ("transformer", "token_embedding", "ln_final", "positional_embedding", "text_projection", "logit_scale", "logit_bias", "attn_mask"):
        if hasattr(raw.clip, name): delattr(raw.clip, name)
    raw.cuda()
    model = DistributedDataParallel(raw, device_ids=[rank], static_graph=True)
    optimizer = torch.optim.AdamW(model.parameters(), lr=2e-5, weight_decay=1e-4, foreach=False, fused=True)
    scaler = torch.amp.GradScaler("cuda", init_scale=1024)
    start_epoch = 0
    if resume and resume["fold"] == fold:
        raw.load_state_dict(resume["model"])
        optimizer.load_state_dict(resume["optimizer"])
        scaler.load_state_dict(resume["scaler"])
        start_epoch = resume["epoch"]
        state = resume["rng"][rank]
        random.setstate(state["python"]); np.random.set_state(state["numpy"])
        torch.set_rng_state(state["cpu"]); torch.cuda.set_rng_state(state["cuda"], rank)
        if rank == 0: print(f"RESUMED fold={fold} completed_epoch={start_epoch}", flush=True)
    resume = None
    weights = {}
    for t in tasks:
        counts = np.bincount(y[t][train_indices], minlength=n_classes[t]).astype(np.float32)
        weights[t] = torch.tensor(np.where(counts > 0, len(train_indices)/(np.maximum(counts,1)*(counts>0).sum()),0), device="cuda", dtype=torch.float32)
    dataset = scope["SampulDataset"](df, train_indices)
    sampler = DistributedSampler(dataset, num_replicas=2, rank=rank, shuffle=True, seed=42)
    loader = DataLoader(dataset, batch_size=8, sampler=sampler, num_workers=0, pin_memory=True)
    for epoch in range(start_epoch, stop_epoch):
        sampler.set_epoch(epoch)
        model.train(); dist.barrier(); torch.cuda.synchronize()
        begin = time.perf_counter(); total_loss = torch.zeros((), device="cuda"); updates=0
        encoder_changed = {}
        for step, (images, ids, mask, labels) in enumerate(loader, 1):
            if smoke and step > 2: break
            optimizer.zero_grad(set_to_none=True)
            labels = {t:v.cuda(non_blocking=True) for t,v in labels.items()}
            with torch.autocast("cuda", dtype=torch.float16):
                logits = model(images.cuda(non_blocking=True), ids.cuda(non_blocking=True), mask.cuda(non_blocking=True))
                denom = torch.stack([weights[t][labels[t]].sum() for t in tasks]); dist.all_reduce(denom)
                loss = sum(torch.nn.functional.cross_entropy(logits[t],labels[t],weight=weights[t],reduction="sum")*2/denom[i] for i,t in enumerate(tasks))/len(tasks)
            if not torch.isfinite(loss).item(): raise RuntimeError("Nonfinite loss")
            scaler.scale(loss).backward(); scaler.unscale_(optimizer)
            if not torch.stack([torch.isfinite(p.grad).all() for p in model.parameters() if p.grad is not None]).all().item():
                raise RuntimeError("Nonfinite gradient")
            probes={}
            if step == 1:
                for name, enc in (("clip",raw.clip.visual),("bert",raw.bert)):
                    p=next(p for p in enc.parameters() if p.grad is not None and p.grad.abs().sum().item()>0)
                    index=p.grad.abs().flatten().argmax().item();probes[name]=(p,index,p.detach().flatten()[index].item())
            scaler.step(optimizer);scaler.update()
            if probes:
                encoder_changed={name:p.detach().flatten()[index].item()!=before for name,(p,index,before) in probes.items()}
                if not all(encoder_changed.values()): raise RuntimeError("Encoder did not update")
            total_loss+=loss.detach();updates+=1
        dist.all_reduce(total_loss);torch.cuda.synchronize();dist.barrier()
        record={"fold":fold,"epoch":epoch+1,"loss":total_loss.item()/(2*updates),"seconds":time.perf_counter()-begin,"updates":updates,"encoder_updated":encoder_changed,"smoke":smoke}
        records.append(record)
        if rank==0:
            print(json.dumps(record),flush=True)
            with (output/"training_history.jsonl").open("a") as f: f.write(json.dumps(record)+"\n")
        if smoke or (epoch+1)%5==0 or epoch+1==120:
            state={"python":random.getstate(),"numpy":np.random.get_state(),"cpu":torch.get_rng_state(),"cuda":torch.cuda.get_rng_state(rank)}
            rng=[None,None];dist.all_gather_object(rng,state)
            if rank==0:
                payload={"config":config,"fold":fold,"epoch":epoch+1,"model":raw.state_dict(),"optimizer":optimizer.state_dict(),"scaler":scaler.state_dict(),"rng":rng,"classes":scope["peta"]}
                torch.save(payload,output/"latest.pt.tmp");os.replace(output/"latest.pt.tmp",checkpoint)
                (output/"progress.json").write_text(json.dumps({"fold":fold,"completed_epoch":epoch+1,"config":config},indent=2))
                del payload
            dist.barrier()
    # Smoke phase 1 stops before final evaluation, leaving checkpoint for phase 2.
    if smoke and stop_epoch==1:
        if rank==0: (output/"smoke_phase1.json").write_text(json.dumps({"checkpoint_saved":checkpoint.exists(),"completed_epoch":1}))
        del model,raw,optimizer,scaler;gc.collect();torch.cuda.empty_cache();break
    optimizer.zero_grad(set_to_none=True);raw.eval()
    local_indices=test_indices[rank::2];pred={t:[] for t in tasks}
    with torch.no_grad():
        for images,ids,mask,labels in DataLoader(scope["SampulDataset"](df,local_indices),batch_size=8,num_workers=0,pin_memory=True):
            with torch.autocast("cuda",dtype=torch.float16):
                logits=raw(images.cuda(non_blocking=True),ids.cuda(non_blocking=True),mask.cuda(non_blocking=True))
            if not all(torch.isfinite(v).all().item() for v in logits.values()):raise RuntimeError("Nonfinite evaluation")
            for t in tasks:pred[t].extend(logits[t].argmax(1).cpu().tolist())
    parts=[None,None];dist.all_gather_object(parts,{"indices":local_indices,"pred":pred})
    if rank==0:
        indices=np.concatenate([x["indices"] for x in parts]);preds={t:np.concatenate([x["pred"][t] for x in parts]) for t in tasks}
        assert len(indices)==148 and len(set(indices))==148
        metrics={t:{"accuracy":float(accuracy_score(y[t][indices],preds[t])),"macro_f1":float(f1_score(y[t][indices],preds[t],average="macro",zero_division=0))} for t in tasks}
        torch.save({"state_dict":raw.state_dict(),"classes":scope["peta"],"fold":fold,"unused_clip_text_tower_removed":True,"config":config},output/f"fold_{fold}.pt.tmp")
        os.replace(output/f"fold_{fold}.pt.tmp",output/f"fold_{fold}.pt")
        np.savez(output/f"fold_{fold}_predictions.npz",indices=indices,**preds)
        (output/f"fold_{fold}_metrics.json").write_text(json.dumps({"fold":fold,"metrics":metrics,"smoke":smoke},indent=2))
        if smoke:
            (output/"smoke_result.json").write_text(json.dumps({"status":"success","resumed_from_epoch":start_epoch,"completed_epoch":stop_epoch,"evaluated_samples":len(indices),"records":records,"purpose":"checkpoint/resume verification only, not CV results"},indent=2))
    dist.barrier()
    del model,raw,optimizer,scaler,weights,logits;gc.collect();torch.cuda.empty_cache()
if rank==0 and not smoke and all((output/f"fold_{f}_metrics.json").exists() for f in range(1,6)):
    predictions={t:np.full(len(df),-1,dtype=int) for t in tasks};fold_metrics=[];seen=[]
    for f in range(1,6):
        z=np.load(output/f"fold_{f}_predictions.npz");seen.extend(z["indices"].tolist())
        for t in tasks:predictions[t][z["indices"]]=z[t]
        fold_metrics.append(json.loads((output/f"fold_{f}_metrics.json").read_text()))
    assert len(seen)==740 and len(set(seen))==740
    metrics={t:{"accuracy":float(accuracy_score(y[t],predictions[t])),"macro_f1":float(f1_score(y[t],predictions[t],average="macro",zero_division=0))} for t in tasks}
    np.savez(output/"oof_predictions.npz",**predictions)
    (output/"hasil_mtl_740_finetuned.json").write_text(json.dumps({"status":"complete","config":config,"hasil":metrics,"fold_metrics":fold_metrics,"classes":scope["peta"]},indent=2))
    t="task2_domain_sumber"
    _,recall,f1,support=precision_recall_fscore_support(y[t],predictions[t],labels=list(range(n_classes[t])),zero_division=0)
    pd.DataFrame({"kelas":scope["peta"][t],"jumlah":support,"recall":recall,"f1":f1}).to_csv(output/"analisis_recall_per_kelas_740_finetuned.csv",index=False)
dist.barrier();dist.destroy_process_group()
