#!/usr/bin/env python3
"""M01: nested-CV frozen CLIP-L14 + IndoBERT shared MLP, three joint heads."""
from __future__ import annotations

import csv, hashlib, json, random, time
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
import torch
from sklearn.metrics import f1_score
from sklearn.model_selection import StratifiedKFold
from torch import nn
import torch.nn.functional as F

ROOT = Path(__file__).resolve().parents[3]
P = ROOT / "DEMO_XAI_745_FULL"
DATA = P / "03_data/DATASET_740_TASK2_DOMAIN.csv"
CACHE = P / "04_hasil_eksperimen/e41_cached_tail/cache/front_cache.npz"
E42 = P / "04_hasil_eksperimen/e42_tail_grid/oof.csv"
PROTOCOL = P / "04_hasil_eksperimen/next_research_20261017/frozen_protocol.json"
OUT = P / "04_hasil_eksperimen/next_research_20261017/01_model_comparison/M01_clip_indobert"
TASKS = ("task1_issue", "task2_domain_sumber", "task3_primary_entity_type")

@dataclass(frozen=True)
class Config:
    hidden: int
    dropout: float
    lr: float
    weight_decay: float
    class_weight_power: float
    label_smoothing: float
    epochs: int = 35
    batch_size: int = 32

CONFIGS = [
    Config(128, .20, 1e-3, 1e-4, .0, .0),
    Config(192, .25, 8e-4, 2e-4, .5, .05),
    Config(256, .30, 6e-4, 3e-4, .5, .05),
]

class SharedMLP(nn.Module):
    def __init__(self, classes, cfg):
        super().__init__()
        self.shared = nn.Sequential(nn.Linear(2304, cfg.hidden), nn.LayerNorm(cfg.hidden), nn.GELU(), nn.Dropout(cfg.dropout))
        self.heads = nn.ModuleDict({t: nn.Linear(cfg.hidden, classes[t]) for t in TASKS})
    def forward(self, visual, text):
        x = torch.cat([F.normalize(visual.float(), dim=-1), F.normalize(text.float(), dim=-1)], dim=-1)
        z = self.shared(x)
        return {t: self.heads[t](z) for t in TASKS}

def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as f: return list(csv.DictReader(f))

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def seed_all(seed):
    random.seed(seed); np.random.seed(seed); torch.manual_seed(seed)

def weights(y, n, power):
    counts = np.bincount(y, minlength=n).astype(np.float32)
    if power == 0: return torch.ones(n)
    value = (len(y) / (n * counts)) ** power
    return torch.tensor(value / value.mean(), dtype=torch.float32)

def fit(v, t, ys, classes, cfg, seed):
    seed_all(seed); model = SharedMLP(classes, cfg)
    opt = torch.optim.AdamW(model.parameters(), lr=cfg.lr, weight_decay=cfg.weight_decay)
    losses = {task: nn.CrossEntropyLoss(weight=weights(ys[task].numpy(), classes[task], cfg.class_weight_power), label_smoothing=cfg.label_smoothing) for task in TASKS}
    model.train()
    for _ in range(cfg.epochs):
        for idx in torch.randperm(len(v)).split(cfg.batch_size):
            opt.zero_grad(); logits = model(v[idx], t[idx])
            loss = sum(losses[task](logits[task], ys[task][idx]) for task in TASKS) / 3
            loss.backward(); opt.step()
    return model.eval()

@torch.no_grad()
def predict(model, v, t): return {task: model(v, t)[task].argmax(1).numpy() for task in TASKS}

def score(truth, pred, classes):
    values = {task: float(f1_score(truth[task], pred[task], labels=range(classes[task]), average="macro", zero_division=0)) for task in TASKS}
    return {**values, "min": min(values.values()), "mean": float(np.mean(list(values.values())))}

def main():
    started = time.time(); OUT.mkdir(parents=True, exist_ok=True)
    rows, folds_rows = read_csv(DATA), read_csv(E42); cache = np.load(CACHE)
    ids = [r["sample_id"] for r in rows]
    assert ids == cache["sample_ids"].tolist() == [r["sample_id"] for r in folds_rows]
    protocol = json.loads(PROTOCOL.read_text())
    assert protocol["dataset"]["sha256"] == sha(DATA)
    labels, encoded, classes = {}, {}, {}
    for task in TASKS:
        labels[task] = sorted({r[task] for r in rows}); classes[task] = len(labels[task]); enc = {x:i for i,x in enumerate(labels[task])}
        encoded[task] = np.array([enc[r[task]] for r in rows])
    v, t = torch.tensor(cache["visual"], dtype=torch.float32), torch.tensor(cache["base_mean"], dtype=torch.float32)
    folds = np.array([int(r["fold"]) for r in folds_rows]); oof = {task: np.full(len(rows), -1) for task in TASKS}; details=[]
    for fold in range(1, 6):
        train, test = np.where(folds != fold)[0], np.where(folds == fold)[0]
        inner = StratifiedKFold(3, shuffle=True, random_state=10100 + fold)
        candidates=[]
        for ci, cfg in enumerate(CONFIGS):
            ss=[]
            for si,(a,b) in enumerate(inner.split(train, encoded["task2_domain_sumber"][train])):
                tr, va = train[a], train[b]
                m=fit(v[tr],t[tr],{x:torch.tensor(encoded[x][tr]) for x in TASKS},classes,cfg,101000+fold*100+ci*10+si)
                ss.append(score({x:encoded[x][va] for x in TASKS},predict(m,v[va],t[va]),classes))
            candidates.append({"config":ci,"min":float(np.mean([x["min"] for x in ss])),"mean":float(np.mean([x["mean"] for x in ss]))})
        chosen=max(candidates,key=lambda x:(x["min"],x["mean"])); cfg=CONFIGS[chosen["config"]]
        m=fit(v[train],t[train],{x:torch.tensor(encoded[x][train]) for x in TASKS},classes,cfg,202000+fold)
        pred=predict(m,v[test],t[test])
        for task in TASKS: oof[task][test]=pred[task]
        details.append({"fold":fold,"selected":chosen,"config":asdict(cfg),"outer":score({x:encoded[x][test] for x in TASKS},pred,classes)})
        print(f"fold={fold} selected={chosen['config']} outer_min={details[-1]['outer']['min']:.4f}", flush=True)
    overall=score(encoded,oof,classes)
    with (OUT/"oof.csv").open("w",newline="") as f:
        fields=["sample_id","fold"]+[z for task in TASKS for z in (task+"_truth",task+"_pred")]; w=csv.DictWriter(f,fieldnames=fields); w.writeheader()
        for i,sid in enumerate(ids):
            row={"sample_id":sid,"fold":int(folds[i])}
            for task in TASKS: row[task+"_truth"]=labels[task][encoded[task][i]]; row[task+"_pred"]=labels[task][int(oof[task][i])]
            w.writerow(row)
    result={"schema":"tempo-m01-shared-mlp-v1","status":"complete","joint_model":True,"dataset_sha256":sha(DATA),"cache_sha256":sha(CACHE),"protocol_sha256":sha(PROTOCOL),"overall_scores":overall,"fold_details":details,"seconds":time.time()-started}
    result["oof_sha256"]=sha(OUT/"oof.csv"); (OUT/"result.json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(overall,indent=2))

if __name__ == "__main__": main()
