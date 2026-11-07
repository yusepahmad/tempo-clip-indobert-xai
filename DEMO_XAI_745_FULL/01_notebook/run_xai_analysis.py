#!/usr/bin/env python3
"""Analisis XAI: Grad-CAM + zona dominan pada 25 sampul (leave-one-out),
mereplikasi sel 39 notebook demo, diterapkan pada dataset 740 sampul.

Juga menjalankan uji satu-sampul (leave-one-out) pada 7 sampul contoh,
mereplikasi hasil_uji_satu_gambar.json.
"""
from pathlib import Path
import json

import numpy as np
import pandas as pd
import torch
import torch.nn as nn

# Path relatif terhadap paket ini (folder induk dari 01_notebook/), agar
# berjalan di mana pun paket ini diletakkan, termasuk di Windows.
PKG = Path(__file__).resolve().parent.parent
DATA_CSV = PKG / "03_data" / "DATASET_740_TASK2_DOMAIN.csv"
FEATURES = PKG / "03_data" / "fitur_clip_indobert_740.npz"
DIR_GAMBAR = PKG / "05_gambar"
OUT_ZONA_JSON = PKG / "04_hasil_eksperimen" / "analisis_zona_740.json"
OUT_LOO_JSON = PKG / "04_hasil_eksperimen" / "hasil_uji_satu_gambar_740.json"

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


def latih(X, y, n_kelas, kecualikan=None, epoch=120, lr=1e-3, wd=1e-4):
    torch.manual_seed(SEED)
    idx = np.array([i for i in range(len(X)) if i != kecualikan])
    bobot = {}
    for t in TASKS:
        cnt = np.bincount(y[t][idx], minlength=n_kelas[t]).astype(np.float32)
        w = np.where(cnt > 0, len(idx) / (np.maximum(cnt, 1) * (cnt > 0).sum()), 0.0)
        bobot[t] = torch.tensor(w, dtype=torch.float32)
    model = KepalaMTL(X.shape[1], n_kelas)
    opt = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=wd)
    rugi = {t: nn.CrossEntropyLoss(weight=bobot[t]) for t in TASKS}
    Xt = torch.tensor(X[idx])
    yt = {t: torch.tensor(y[t][idx]) for t in TASKS}
    model.train()
    for _ in range(epoch):
        opt.zero_grad()
        out = model(Xt)
        total = sum(rugi[t](out[t], yt[t]) for t in TASKS) / len(TASKS)
        total.backward()
        opt.step()
    model.eval()
    return model


def grad_cam(jalur_gambar, fitur_teks, task, model, clip_model, preprocess):
    from PIL import Image
    im = preprocess(Image.open(jalur_gambar).convert("RGB")).unsqueeze(0)
    simpan = {}

    def hook_fwd(_m, _i, o):
        simpan["act"] = o

    def hook_bwd(_m, _gi, go):
        simpan["grad"] = go[0]

    blok = clip_model.visual.transformer.resblocks[-2]
    h1 = blok.register_forward_hook(hook_fwd)
    h2 = blok.register_full_backward_hook(hook_bwd)
    try:
        v = clip_model.encode_image(im)
        v = v / v.norm(dim=-1, keepdim=True)
        x = torch.cat([v[0], torch.tensor(fitur_teks)]).reshape(1, -1)
        out = model(x)
        logits = out[task][0]
        k = int(logits.argmax())
        clip_model.zero_grad(set_to_none=True)
        model.zero_grad(set_to_none=True)
        logits[k].backward()
    finally:
        h1.remove()
        h2.remove()

    act = simpan.get("act")
    grad = simpan.get("grad")
    if act is None or grad is None:
        return None, k
    a = act.detach()
    g = grad.detach()
    if a.dim() == 3:
        if a.shape[0] == 1:
            a, g = a[0], g[0]
        elif a.shape[1] == 1:
            a, g = a[:, 0, :], g[:, 0, :]
        else:
            return None, k
    else:
        return None, k
    a = a[1:]
    g = g[1:]
    if float(g.abs().sum()) == 0.0:
        return None, k
    cam = (a * g).sum(dim=-1).abs()
    n = cam.shape[0]
    sisi = int(round(n ** 0.5))
    if sisi * sisi != n:
        return None, k
    cam = cam.reshape(sisi, sisi).float().numpy()
    rentang = float(cam.max() - cam.min())
    cam = (cam - cam.min()) / rentang if rentang > 1e-12 else np.zeros_like(cam)
    return cam, k


def zona_dominan(cam):
    n = cam.shape[0]
    batas_atas = max(1, n // 3)
    batas_bawah = n - max(1, n // 3)
    zona = {
        "kepala sampul (logo dan judul kecil)": float(cam[:batas_atas].mean()),
        "bagian tengah (umumnya ilustrasi)": float(cam[batas_atas:batas_bawah].mean()),
        "kaki sampul (headline besar dan barcode)": float(cam[batas_bawah:].mean()),
    }
    urut = sorted(zona.items(), key=lambda kv: -kv[1])
    return urut[0][0], urut[0][1], zona


def find_image(sid):
    for ext in (".jpg", ".jpeg", ".png", ".webp"):
        p = DIR_GAMBAR / f"{sid}{ext}"
        if p.exists():
            return p
    return None


def main():
    df = pd.read_csv(DATA_CSV, encoding="utf-8-sig")
    z = np.load(FEATURES)
    X = np.hstack([z["img"], z["txt"]]).astype(np.float32)
    dim_img = z["img"].shape[1]

    peta, y, n_kelas = {}, {}, {}
    for t in TASKS:
        kelas = sorted(df[t].astype(str).unique())
        peta[t] = kelas
        y[t] = df[t].astype(str).map({c: i for i, c in enumerate(kelas)}).to_numpy()
        n_kelas[t] = len(kelas)

    import open_clip
    print("Memuat CLIP untuk Grad-CAM ...", flush=True)
    clip_model, _, preprocess = open_clip.create_model_and_transforms(
        "ViT-B-32", pretrained="laion2b_s34b_b79k"
    )
    clip_model.eval()

    # ---------- Analisis zona pada 25 sampul pertama (leave-one-out) ----------
    print("Menghitung zona dominan pada 25 sampul pertama (leave-one-out).", flush=True)
    zona_rekap = {"kepala": 0, "tengah": 0, "kaki": 0}
    nilai_zona = {"kepala": [], "tengah": [], "kaki": []}
    detail = []

    for sid in df["sample_id"].head(25):
        i = int(df.index[df.sample_id == sid][0])
        jalur = find_image(sid)
        if jalur is None:
            continue
        m = latih(X, y, n_kelas, kecualikan=i)
        cam, _ = grad_cam(jalur, X[i, dim_img:], "task2_domain_sumber", m, clip_model, preprocess)
        if cam is None:
            continue
        nama, nilai, semua = zona_dominan(cam)
        kunci = "kepala" if "kepala" in nama else ("tengah" if "tengah" in nama else "kaki")
        zona_rekap[kunci] += 1
        for k, v in semua.items():
            kk = "kepala" if "kepala" in k else ("tengah" if "tengah" in k else "kaki")
            nilai_zona[kk].append(v)
        detail.append({"sample_id": sid, "zona_dominan": kunci, "nilai": nilai})
        print(f"  {sid}: zona dominan = {kunci} ({nilai:.3f})", flush=True)

    ringkasan_intensitas = {k: (float(np.mean(v)) if v else None) for k, v in nilai_zona.items()}
    hasil_zona = {
        "n_sampul_dianalisis": len(detail),
        "zona_dominan_count": zona_rekap,
        "intensitas_rata_rata": ringkasan_intensitas,
        "detail": detail,
    }
    with open(OUT_ZONA_JSON, "w", encoding="utf-8") as f:
        json.dump(hasil_zona, f, indent=2, ensure_ascii=False)
    print(f"Disimpan: {OUT_ZONA_JSON}")

    # ---------- Uji leave-one-out pada 7 sampul pertama dari tiap domain unik ----------
    print("\nMenjalankan uji leave-one-out pada sampul contoh (satu per domain unik).", flush=True)
    terpilih, sudah = [], set()
    for _, r in df.iterrows():
        d = r["task2_domain_sumber"]
        if d not in sudah:
            terpilih.append(r["sample_id"])
            sudah.add(d)
        if len(terpilih) >= 7:
            break

    rekap_loo = []
    for sid in terpilih:
        i = int(df.index[df.sample_id == sid][0])
        row = df.iloc[i]
        m = latih(X, y, n_kelas, kecualikan=i)
        with torch.no_grad():
            out = m(torch.tensor(X[i].reshape(1, -1)))
        prediksi = {}
        cocok_total = 0
        for t in TASKS:
            prob = torch.softmax(out[t][0], dim=0).numpy()
            urut = prob.argsort()[::-1]
            pred_label = peta[t][int(urut[0])]
            asli = str(row[t])
            cocok = pred_label == asli
            cocok_total += int(cocok)
            prediksi[t] = {
                "prediksi": pred_label,
                "probabilitas": float(prob[urut[0]]),
                "anotator": asli,
                "cocok": cocok,
            }
        rekap_loo.append({
            "sample_id": sid,
            "headline": str(row["headline_verified"]),
            "prediksi": prediksi,
            "skor_cocok": f"{cocok_total} dari {len(TASKS)}",
        })
        print(f"  {sid}: {cocok_total}/{len(TASKS)} cocok", flush=True)

    with open(OUT_LOO_JSON, "w", encoding="utf-8") as f:
        json.dump(rekap_loo, f, indent=2, ensure_ascii=False)
    print(f"Disimpan: {OUT_LOO_JSON}")

    print("\n=== RINGKASAN ZONA ===")
    print(zona_rekap)
    print(ringkasan_intensitas)


if __name__ == "__main__":
    main()
