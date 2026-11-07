#!/usr/bin/env python3
"""Latih + evaluasi MTL (5-fold CV) untuk dataset 740 sampul.

Mereplikasi logika sel 12/14/16/17/19 dari notebook demo versi pilot (189
sampul), diterapkan pada dataset penuh. Menyimpan hasil metrik ke JSON, sama
format dengan hasil_mtl_189_task2domain.json (berkas pilot, tidak disertakan
di paket). Notebook DEMO_XAI_TEMPO.ipynb kini juga memakai dataset 740, dan
hasil skrip ini (Macro-F1 0,438 / 0,320 / 0,276) adalah baseline yang dipakai
aplikasi.
"""
from pathlib import Path
from collections import Counter
import json

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from sklearn.metrics import f1_score, accuracy_score, precision_recall_fscore_support
from sklearn.model_selection import StratifiedKFold

# Path relatif terhadap paket ini (folder induk dari 01_notebook/), agar
# berjalan di mana pun paket ini diletakkan, termasuk di Windows.
PAKET = Path(__file__).resolve().parent.parent
DATA_CSV = PAKET / "03_data" / "DATASET_740_TASK2_DOMAIN.csv"
FEATURES = PAKET / "03_data" / "fitur_clip_indobert_740.npz"
OUT_JSON = PAKET / "04_hasil_eksperimen" / "hasil_mtl_740_task2domain.json"
OUT_RECALL_CSV = PAKET / "04_hasil_eksperimen" / "analisis_recall_per_kelas_740.csv"

SEED = 42
TASKS = {
    "task1_issue": "Task 1 — Isu Utama",
    "task2_domain_sumber": "Task 2 — Domain Sumber Metafora",
    "task3_primary_entity_type": "Task 3 — Tipe Entitas Sasaran",
}

torch.manual_seed(SEED)
np.random.seed(SEED)


class KepalaMTL(nn.Module):
    def __init__(self, dim_masuk, n_kelas, tersembunyi=256, p_drop=0.4):
        super().__init__()
        self.bersama = nn.Sequential(
            nn.Linear(dim_masuk, tersembunyi), nn.ReLU(), nn.Dropout(p_drop)
        )
        self.kepala = nn.ModuleDict({t: nn.Linear(tersembunyi, n) for t, n in n_kelas.items()})

    def forward(self, x):
        h = self.bersama(x)
        return {t: k(h) for t, k in self.kepala.items()}


def evaluasi(fitur, y, n_kelas, n_lipat=5, epoch=120):
    strat = y["task1_issue"]
    cnt = Counter(strat)
    aman = np.array([c if cnt[c] >= n_lipat else -1 for c in strat])
    skf = StratifiedKFold(n_splits=n_lipat, shuffle=True, random_state=SEED)

    tebak = {t: np.zeros(len(strat), dtype=int) for t in TASKS}
    fold_no = 0
    for i_latih, i_uji in skf.split(fitur, aman):
        fold_no += 1
        bobot = {}
        for t in TASKS:
            c = np.bincount(y[t][i_latih], minlength=n_kelas[t]).astype(np.float32)
            w = np.where(c > 0, len(i_latih) / (np.maximum(c, 1) * (c > 0).sum()), 0.0)
            bobot[t] = torch.tensor(w, dtype=torch.float32)

        torch.manual_seed(SEED)
        m = KepalaMTL(fitur.shape[1], n_kelas)
        opt = torch.optim.AdamW(m.parameters(), lr=1e-3, weight_decay=1e-4)
        rugi = {t: nn.CrossEntropyLoss(weight=bobot[t]) for t in TASKS}
        Xt = torch.tensor(fitur[i_latih])
        yt = {t: torch.tensor(y[t][i_latih]) for t in TASKS}
        m.train()
        for _ in range(epoch):
            opt.zero_grad()
            o = m(Xt)
            (sum(rugi[t](o[t], yt[t]) for t in TASKS) / len(TASKS)).backward()
            opt.step()
        m.eval()
        with torch.no_grad():
            o = m(torch.tensor(fitur[i_uji]))
        for t in TASKS:
            tebak[t][i_uji] = o[t].argmax(dim=1).numpy()
        print(f"    fold {fold_no}/{n_lipat} selesai", flush=True)

    hasil = {}
    for t in TASKS:
        hasil[t] = {
            "accuracy": accuracy_score(y[t], tebak[t]),
            "macro_f1": f1_score(y[t], tebak[t], average="macro", zero_division=0),
        }
    return hasil, tebak


def main():
    df = pd.read_csv(DATA_CSV, encoding="utf-8-sig")
    z = np.load(FEATURES)
    X = np.hstack([z["img"], z["txt"]]).astype(np.float32)
    dim_img = z["img"].shape[1]
    print(f"Sampul: {len(df)}  Fitur gabungan: {X.shape[1]} dim")

    peta, y, n_kelas = {}, {}, {}
    for t in TASKS:
        kelas = sorted(df[t].astype(str).unique())
        peta[t] = kelas
        y[t] = df[t].astype(str).map({c: i for i, c in enumerate(kelas)}).to_numpy()
        n_kelas[t] = len(kelas)
        print(f"{t}: {n_kelas[t]} kelas")

    varian = {
        "image-only (CLIP)": X[:, :dim_img],
        "text-only (IndoBERT)": X[:, dim_img:],
        "fusion MTL (CLIP+IndoBERT)": X,
    }

    hasil_semua = {"majority baseline": {}}
    for t in TASKS:
        mayoritas = Counter(y[t]).most_common(1)[0][0]
        tebak_maj = np.full(len(y[t]), mayoritas)
        hasil_semua["majority baseline"][t] = {
            "accuracy": accuracy_score(y[t], tebak_maj),
            "macro_f1": f1_score(y[t], tebak_maj, average="macro", zero_division=0),
        }

    tebakan_fusion = None
    for nama, fitur in varian.items():
        print(f"Evaluasi: {nama}")
        h, tb = evaluasi(fitur, y, n_kelas)
        hasil_semua[nama] = h
        if nama.startswith("fusion"):
            tebakan_fusion = tb

    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(hasil_semua, f, indent=2, ensure_ascii=False)
    print(f"Disimpan: {OUT_JSON}")

    t = "task2_domain_sumber"
    p, r, f1s, dukung = precision_recall_fscore_support(
        y[t], tebakan_fusion[t], average=None, zero_division=0,
        labels=list(range(n_kelas[t]))
    )
    rinci = pd.DataFrame({
        "kelas": peta[t], "jumlah": dukung,
        "recall": np.round(r, 3), "f1": np.round(f1s, 3),
    }).sort_values("jumlah", ascending=False)
    rinci.to_csv(OUT_RECALL_CSV, index=False)
    print(f"Disimpan: {OUT_RECALL_CSV}")
    print(rinci.to_string(index=False))

    print("\n=== RINGKASAN MACRO-F1 ===")
    for nama, h in hasil_semua.items():
        print(f"{nama:30s} T1={h['task1_issue']['macro_f1']:.3f}  "
              f"T2={h['task2_domain_sumber']['macro_f1']:.3f}  "
              f"T3={h['task3_primary_entity_type']['macro_f1']:.3f}")


if __name__ == "__main__":
    main()
