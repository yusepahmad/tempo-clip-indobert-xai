#!/usr/bin/env python3
"""Ekstraksi fitur CLIP (visual) + IndoBERT (teks) untuk dataset 740 sampul.

Menghasilkan fitur_clip_indobert_740.npz dengan array 'img' dan 'txt',
urutan baris sama dengan CSV dataset (setelah filter eligibility).
"""
from pathlib import Path
import sys
import time

import numpy as np
import pandas as pd
import torch
from PIL import Image

# Path relatif terhadap paket ini (folder induk dari 01_notebook/), agar
# berjalan di mana pun paket ini diletakkan, termasuk di Windows.
PAKET = Path(__file__).resolve().parent.parent
DATA_CSV = PAKET / "03_data" / "DATASET_740_TASK2_DOMAIN.csv"
IMG_DIR = PAKET / "05_gambar"
OUT_NPZ = PAKET / "03_data" / "fitur_clip_indobert_740.npz"

CLIP_MODEL = "ViT-B-32"
CLIP_PRETRAINED = "laion2b_s34b_b79k"
INDOBERT = "indobenchmark/indobert-base-p1"

torch.manual_seed(42)
np.random.seed(42)


def main():
    df = pd.read_csv(DATA_CSV, encoding="utf-8-sig")
    print(f"Total baris: {len(df)}", flush=True)

    import open_clip
    from transformers import AutoModel, AutoTokenizer

    print("Memuat CLIP ...", flush=True)
    clip_model, _, preprocess = open_clip.create_model_and_transforms(
        CLIP_MODEL, pretrained=CLIP_PRETRAINED
    )
    clip_model.eval()

    print("Memuat IndoBERT ...", flush=True)
    tok = AutoTokenizer.from_pretrained(INDOBERT)
    bert = AutoModel.from_pretrained(INDOBERT)
    bert.eval()

    img_feats = []
    txt_feats = []
    t0 = time.time()
    n = len(df)
    with torch.no_grad():
        for i, row in df.iterrows():
            img_path = IMG_DIR / Path(row["image_path"]).name
            im = Image.open(img_path).convert("RGB")
            im_t = preprocess(im).unsqueeze(0)
            v = clip_model.encode_image(im_t)
            v = v / v.norm(dim=-1, keepdim=True)
            img_feats.append(v.squeeze(0).numpy().astype(np.float32))

            headline = str(row["headline_verified"]) if pd.notna(row["headline_verified"]) else ""
            supporting = str(row["supporting_text_verified"]) if pd.notna(row["supporting_text_verified"]) else ""
            text = f"{headline} [SEP] {supporting}".strip()
            enc = tok(text, return_tensors="pt", truncation=True, max_length=128, padding="max_length")
            h = bert(**enc).last_hidden_state[:, 0, :]
            h = h / h.norm(dim=-1, keepdim=True)
            txt_feats.append(h.squeeze(0).numpy().astype(np.float32))

            if (i + 1) % 25 == 0 or (i + 1) == n:
                elapsed = time.time() - t0
                rate = (i + 1) / elapsed
                eta = (n - (i + 1)) / rate if rate > 0 else 0
                print(f"  {i+1}/{n}  ({elapsed:.0f}s elapsed, ETA {eta:.0f}s)", flush=True)

    img_arr = np.stack(img_feats)
    txt_arr = np.stack(txt_feats)
    print(f"img shape: {img_arr.shape}, txt shape: {txt_arr.shape}")
    np.savez(OUT_NPZ, img=img_arr, txt=txt_arr)
    print(f"Disimpan: {OUT_NPZ}")


if __name__ == "__main__":
    main()
