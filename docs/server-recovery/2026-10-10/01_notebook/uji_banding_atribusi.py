#!/usr/bin/env python3
"""Uji banding metode atribusi kata: occlusion vs LIME (revisi 15 Sep, R4).

Dosen melaporkan pada sampul "GULA-GULA DEMO BURUH" seluruh kata bernilai
negatif, termasuk "DEMO" yang jelas tergambar. Diagram rancangan penelitian
menyebut LIME, sedangkan yang terpasang selama ini occlusion sederhana.

Skrip ini membandingkan keduanya pada sampul dataset — tempat gambar dan
teksnya benar-benar cocok — supaya pemilihan metode punya dasar angka.

Yang diukur:
  - berapa sampul yang SELURUH katanya bernilai negatif (gejala yang
    dikeluhkan dosen);
  - kesepakatan urutan kata antar-metode (korelasi peringkat Spearman);
  - stabilitas LIME bila dijalankan ulang (LIME berbasis sampling acak,
    occlusion deterministik);
  - waktu per sampul.

Jalankan:
    venv/bin/python 01_notebook/uji_banding_atribusi.py --n 25

Catatan 6 Okt: skrip ini memakai 200 varian LIME secara baku (--sampel-lime),
sedangkan aplikasi memakai 120 varian (xai_core.atribusi_kata_lime). Hasilnya
menjadi dasar LIME sebagai metode analisis satu sampul; batch memakai occlusion.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

PAKET = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PAKET / "02_web_demo"))

OUT_JSON = PAKET / "04_hasil_eksperimen" / "uji_banding_atribusi.json"
DIR_GAMBAR = PAKET / "05_gambar"
TASK = "task2_domain_sumber"


def cari_gambar(sid: str):
    for ext in (".jpg", ".jpeg", ".png", ".webp"):
        p = DIR_GAMBAR / f"{sid}{ext}"
        if p.exists():
            return p
    return None


def spearman(a: list[float], b: list[float]) -> float:
    """Korelasi peringkat antara dua daftar skor.

    Dipakai untuk melihat apakah kedua metode sepakat soal URUTAN kata,
    terlepas dari besaran angkanya yang memang tidak sebanding.
    """
    n = len(a)
    if n < 2:
        return float("nan")

    def peringkat(x):
        urut = sorted(range(n), key=lambda i: x[i])
        r = [0.0] * n
        i = 0
        while i < n:
            j = i
            while j + 1 < n and x[urut[j + 1]] == x[urut[i]]:
                j += 1
            rata = (i + j) / 2 + 1
            for k in range(i, j + 1):
                r[urut[k]] = rata
            i = j + 1
        return r

    ra, rb = peringkat(a), peringkat(b)
    ma, mb = sum(ra) / n, sum(rb) / n
    pemb = sum((x - ma) * (y - mb) for x, y in zip(ra, rb))
    penyebut = (sum((x - ma) ** 2 for x in ra) * sum((y - mb) ** 2 for y in rb)) ** 0.5
    return pemb / penyebut if penyebut > 1e-12 else float("nan")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=25, help="jumlah sampul yang diuji")
    ap.add_argument("--sampel-lime", type=int, default=200,
                    help="jumlah varian yang dibangkitkan LIME per sampul")
    args = ap.parse_args()

    import xai_core

    eng = xai_core.XAIEngine()
    df = eng.df

    # Ambil merata dari seluruh dataset, bukan baris-baris pertama.
    langkah = max(1, len(df) // args.n)
    pilihan = list(range(0, len(df), langkah))[:args.n]
    print(f"Menguji {len(pilihan)} sampul dari {len(df)} (tiap ke-{langkah}).\n",
          flush=True)

    rinci = []
    for i in pilihan:
        r = df.iloc[i]
        sid = r["sample_id"]
        gambar = cari_gambar(sid)
        if gambar is None:
            continue

        # leave-one-out, sama seperti mode dataset pada aplikasi
        eng.train(exclude_index=i)
        img_feat = eng.X[i, :eng.dim_img]
        headline = str(r["headline_verified"])
        supporting = str(r.get("supporting_text_verified", "") or "")

        t0 = time.time()
        occ, kelas_o, prob_o = eng.atribusi_kata(img_feat, headline, supporting, TASK)
        t_occ = time.time() - t0

        t0 = time.time()
        lim, kelas_l, prob_l = eng.atribusi_kata_lime(
            img_feat, headline, supporting, TASK, n_sampel=args.sampel_lime)
        t_lime = time.time() - t0

        # LIME dijalankan dua kali untuk mengukur stabilitasnya.
        lim2, _, _ = eng.atribusi_kata_lime(
            img_feat, headline, supporting, TASK, n_sampel=args.sampel_lime)

        so = [x["kontribusi"] for x in occ]
        sl = [x["kontribusi"] for x in lim]
        sl2 = [x["kontribusi"] for x in lim2]

        baris = {
            "sample_id": sid,
            "headline": headline,
            "kelas": kelas_o,
            "probabilitas": round(prob_o, 4),
            "n_kata": len(so),
            "occ_positif": sum(1 for v in so if v > 0),
            "lime_positif": sum(1 for v in sl if v > 0),
            "occ_semua_negatif": all(v <= 0 for v in so),
            "lime_semua_negatif": all(v <= 0 for v in sl),
            "sepakat_kata_teratas": (
                max(occ, key=lambda x: x["kontribusi"])["kata"]
                == max(lim, key=lambda x: x["kontribusi"])["kata"]
            ),
            "korelasi_occ_lime": round(spearman(so, sl), 3),
            "stabilitas_lime": round(spearman(sl, sl2), 3),
            "detik_occ": round(t_occ, 2),
            "detik_lime": round(t_lime, 2),
            "occlusion": occ,
            "lime": lim,
        }
        rinci.append(baris)
        print(f"  {sid}  \"{headline[:34]}\"", flush=True)
        print(f"     positif: occ {baris['occ_positif']}/{baris['n_kata']}"
              f"  lime {baris['lime_positif']}/{baris['n_kata']}"
              f"  | korelasi {baris['korelasi_occ_lime']}"
              f"  stabilitas-lime {baris['stabilitas_lime']}"
              f"  | {t_occ:.1f}s vs {t_lime:.1f}s", flush=True)

    if not rinci:
        print("Tidak ada sampul yang dapat diuji.")
        return

    n = len(rinci)
    def rata(kunci):
        nilai = [x[kunci] for x in rinci if not np.isnan(x[kunci])]
        return round(sum(nilai) / len(nilai), 3) if nilai else float("nan")

    ringkas = {
        "n_sampul": n,
        "sampel_lime": args.sampel_lime,
        "occ_semua_negatif": sum(1 for x in rinci if x["occ_semua_negatif"]),
        "lime_semua_negatif": sum(1 for x in rinci if x["lime_semua_negatif"]),
        "sepakat_kata_teratas": sum(1 for x in rinci if x["sepakat_kata_teratas"]),
        "korelasi_occ_lime_rata2": rata("korelasi_occ_lime"),
        "stabilitas_lime_rata2": rata("stabilitas_lime"),
        "detik_occ_rata2": round(sum(x["detik_occ"] for x in rinci) / n, 2),
        "detik_lime_rata2": round(sum(x["detik_lime"] for x in rinci) / n, 2),
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump({"ringkasan": ringkas, "rinci": rinci}, f, indent=2,
                  ensure_ascii=False)

    print("\n=== RINGKASAN ===")
    print(f"  sampul diuji                     : {n}")
    print(f"  semua kata negatif (occlusion)   : {ringkas['occ_semua_negatif']}")
    print(f"  semua kata negatif (LIME)        : {ringkas['lime_semua_negatif']}")
    print(f"  sepakat soal kata teratas        : {ringkas['sepakat_kata_teratas']}/{n}")
    print(f"  korelasi urutan occ-LIME         : {ringkas['korelasi_occ_lime_rata2']}")
    print(f"  stabilitas LIME (ulang 2x)       : {ringkas['stabilitas_lime_rata2']}")
    print(f"  waktu rata-rata                  : occ {ringkas['detik_occ_rata2']}s"
          f"  vs LIME {ringkas['detik_lime_rata2']}s")
    print(f"\nDisimpan: {OUT_JSON}")


if __name__ == "__main__":
    main()
