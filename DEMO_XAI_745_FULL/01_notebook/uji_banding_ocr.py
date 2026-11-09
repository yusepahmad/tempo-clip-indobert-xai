#!/usr/bin/env python3
"""Uji banding OCR untuk pengisian headline otomatis (revisi 15 Sep, R1).

Dosen menyarankan OCR berbasis transformer dari HuggingFace (TrOCR), dengan
catatan "kalo bisa pake yang lain sihlakan". Skrip ini membandingkan kandidat
pada sampul asli, memakai `headline_verified` di dataset sebagai acuan, agar
pemilihan metode punya dasar angka — bukan preferensi.

Kandidat:
  - easyocr    : dirancang untuk teks pada gambar alami (scene text)
  - trocr      : TrOCR (microsoft/trocr-base-printed), sesuai saran dosen

Ukuran yang dipakai:
  - CER  (Character Error Rate)  : makin kecil makin baik
  - WER  (Word Error Rate)       : makin kecil makin baik
  - Rasio kata acuan yang tertangkap

Jalankan:
    venv/bin/python 01_notebook/uji_banding_ocr.py --n 20
"""
from __future__ import annotations

import argparse
import json
import re
import time
from pathlib import Path

import pandas as pd

PAKET = Path(__file__).resolve().parent.parent
DATA_CSV = PAKET / "03_data" / "DATASET_740_TASK2_DOMAIN.csv"
DIR_GAMBAR = PAKET / "05_gambar"
OUT_JSON = PAKET / "04_hasil_eksperimen" / "uji_banding_ocr.json"


# ---------------------------------------------------------------- metrik

def normalisasi(teks: str) -> str:
    """Samakan bentuk sebelum dibandingkan.

    Huruf besar-kecil dan tanda baca tidak dihitung sebagai kesalahan, karena
    yang dinilai adalah apakah kata-katanya tertangkap — bukan ketepatan
    tipografinya.
    """
    teks = (teks or "").upper()
    teks = re.sub(r"[^A-Z0-9\s]", " ", teks)
    return re.sub(r"\s+", " ", teks).strip()


def jarak_edit(a: list, b: list) -> int:
    """Jarak Levenshtein antara dua urutan (karakter atau kata)."""
    if not a:
        return len(b)
    if not b:
        return len(a)
    sebelum = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        kini = [i]
        for j, cb in enumerate(b, 1):
            kini.append(min(
                sebelum[j] + 1,        # hapus
                kini[j - 1] + 1,       # sisip
                sebelum[j - 1] + (ca != cb),  # ganti
            ))
        sebelum = kini
    return sebelum[-1]


def skor(acuan: str, hasil: str) -> dict:
    """Bandingkan hasil OCR terhadap headline acuan.

    CER/WER dibagi panjang TERPANJANG di antara acuan dan hasil, bukan panjang
    acuan saja. Dengan pembagi panjang acuan, keluaran yang jauh lebih panjang
    (OCR membaca seluruh teks sampul, bukan headline saja) selalu menghasilkan
    nilai >= 1 sehingga semua kandidat tampak sama buruk dan tidak dapat
    dibedakan.

    `kata_tertangkap` mengukur berapa banyak kata acuan yang muncul (recall),
    `presisi_kata` berapa banyak kata keluaran yang memang ada di acuan.
    Keduanya perlu: recall tinggi dengan presisi rendah berarti headline
    tertangkap tetapi tenggelam di antara teks lain.
    """
    a, h = normalisasi(acuan), normalisasi(hasil)
    ka, kh = a.split(), h.split()

    cer = jarak_edit(list(a), list(h)) / max(len(a), len(h), 1)
    wer = jarak_edit(ka, kh) / max(len(ka), len(kh), 1)

    recall = sum(1 for w in ka if w in kh) / max(len(ka), 1)
    presisi = sum(1 for w in kh if w in ka) / max(len(kh), 1)
    f1 = (2 * recall * presisi / (recall + presisi)) if (recall + presisi) else 0.0

    return {
        "cer": round(min(cer, 1.0), 3),
        "wer": round(min(wer, 1.0), 3),
        "kata_tertangkap": round(recall, 3),
        "presisi_kata": round(presisi, 3),
        "f1_kata": round(f1, 3),
    }


# ---------------------------------------------------------------- mesin OCR

def buat_easyocr_mentah():
    """Seluruh teks yang terbaca, tanpa pemilihan headline.

    Dipakai sebagai pembanding dasar: menunjukkan bahwa OCR memang menangkap
    teksnya, tetapi tanpa penyaringan hasilnya tidak dapat dipakai untuk
    mengisi kolom headline.
    """
    import easyocr
    pembaca = easyocr.Reader(["id", "en"], gpu=False, verbose=False)

    def jalan(path: Path) -> str:
        potongan = pembaca.readtext(str(path), detail=0, paragraph=False)
        return " ".join(potongan)

    return jalan


def buat_easyocr_headline():
    """EasyOCR + pemilihan headline seperti yang dipakai aplikasi.

    Inilah yang sebenarnya perlu diukur, karena yang masuk ke kolom headline
    adalah keluaran modul ini — bukan teks OCR mentah.
    """
    import sys
    sys.path.insert(0, str(PAKET / "02_web_demo"))
    import ocr_headline

    def jalan(path: Path) -> str:
        return ocr_headline.baca(path).get("headline", "")

    return jalan


def buat_trocr():
    """TrOCR — pendekatan yang disarankan dosen ("berbasis trm base => hf").

    Catatan pemuatan: `TrOCRProcessor.from_pretrained` gagal pada
    transformers 5.x ("Couldn't instantiate the backend tokenizer"), meski
    sentencepiece sudah terpasang. Karena itu komponennya dimuat terpisah —
    image processor dari checkpoint TrOCR, tokenizer dari `roberta-base`
    (TrOCR memang memakai tokenizer RoBERTa untuk dekodernya). Hasilnya
    setara, dan kegagalan pustaka tidak dihitung sebagai kegagalan metode.
    """
    import torch
    from transformers import (AutoImageProcessor, AutoTokenizer,
                              VisionEncoderDecoderModel)
    from PIL import Image

    nama = "microsoft/trocr-base-printed"
    gambar_proc = AutoImageProcessor.from_pretrained(nama)
    tok = AutoTokenizer.from_pretrained("roberta-base")
    model = VisionEncoderDecoderModel.from_pretrained(nama)
    model.eval()

    def jalan(path: Path) -> str:
        # TrOCR dirancang untuk SATU baris teks. Sampul majalah memuat banyak
        # blok teks, sehingga seluruh gambar diumpankan apa adanya — inilah
        # keterbatasan yang justru ingin diukur.
        im = Image.open(path).convert("RGB")
        piksel = gambar_proc(images=im, return_tensors="pt").pixel_values
        with torch.no_grad():
            ids = model.generate(piksel, max_new_tokens=64)
        return tok.batch_decode(ids, skip_special_tokens=True)[0]

    return jalan


MESIN = {
    "easyocr_mentah": buat_easyocr_mentah,
    "easyocr_headline": buat_easyocr_headline,
    "trocr": buat_trocr,
}


# ---------------------------------------------------------------- utama

def cari_gambar(sid: str):
    for ext in (".jpg", ".jpeg", ".png", ".webp"):
        p = DIR_GAMBAR / f"{sid}{ext}"
        if p.exists():
            return p
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=20, help="jumlah sampul yang diuji")
    ap.add_argument("--mesin", nargs="*", default=list(MESIN),
                    help=f"pilih dari: {', '.join(MESIN)}")
    args = ap.parse_args()

    df = pd.read_csv(DATA_CSV, encoding="utf-8-sig")
    # Ambil merata dari seluruh dataset, bukan 20 baris pertama, agar tidak
    # terkonsentrasi pada satu periode terbitan.
    langkah = max(1, len(df) // args.n)
    contoh = df.iloc[::langkah].head(args.n)
    print(f"Menguji {len(contoh)} sampul dari {len(df)} (tiap ke-{langkah}).\n")

    hasil = {}
    for nama in args.mesin:
        if nama not in MESIN:
            print(f"[lewati] mesin tidak dikenal: {nama}")
            continue

        print(f"=== {nama} ===", flush=True)
        try:
            t0 = time.time()
            jalan = MESIN[nama]()
            print(f"  model siap ({time.time()-t0:.0f}s)", flush=True)
        except Exception as e:
            print(f"  GAGAL dimuat: {type(e).__name__}: {e}\n")
            hasil[nama] = {"error": f"{type(e).__name__}: {e}"}
            continue

        rinci, durasi = [], []
        for _, r in contoh.iterrows():
            path = cari_gambar(r["sample_id"])
            if path is None:
                continue
            acuan = str(r["headline_verified"])
            t1 = time.time()
            try:
                keluar = jalan(path)
            except Exception as e:
                keluar = ""
                print(f"  [{r['sample_id']}] error: {type(e).__name__}")
            dt = time.time() - t1
            durasi.append(dt)

            s = skor(acuan, keluar)
            rinci.append({
                "sample_id": r["sample_id"],
                "acuan": acuan,
                "hasil_ocr": keluar[:300],
                **s,
                "detik": round(dt, 2),
            })
            print(f"  {r['sample_id']}  CER {s['cer']:.2f}  WER {s['wer']:.2f}  "
                  f"R {s['kata_tertangkap']:.2f} P {s['presisi_kata']:.2f} "
                  f"F1 {s['f1_kata']:.2f}  {dt:.1f}s", flush=True)

        if rinci:
            n = len(rinci)
            hasil[nama] = {
                "n": n,
                "cer_rata2": round(sum(x["cer"] for x in rinci) / n, 3),
                "wer_rata2": round(sum(x["wer"] for x in rinci) / n, 3),
                "kata_tertangkap_rata2": round(
                    sum(x["kata_tertangkap"] for x in rinci) / n, 3),
                "presisi_kata_rata2": round(
                    sum(x["presisi_kata"] for x in rinci) / n, 3),
                "f1_kata_rata2": round(sum(x["f1_kata"] for x in rinci) / n, 3),
                "detik_rata2": round(sum(durasi) / len(durasi), 2),
                "rinci": rinci,
            }
            h = hasil[nama]
            print(f"  --> CER {h['cer_rata2']}  WER {h['wer_rata2']}  "
                  f"recall {h['kata_tertangkap_rata2']}  "
                  f"presisi {h['presisi_kata_rata2']}  "
                  f"F1 {h['f1_kata_rata2']}  {h['detik_rata2']}s/sampul\n")

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(hasil, f, indent=2, ensure_ascii=False)
    print(f"Disimpan: {OUT_JSON}")

    sah = {k: v for k, v in hasil.items() if "error" not in v}
    if len(sah) > 1:
        menang = max(sah, key=lambda k: sah[k]["f1_kata_rata2"])
        print(f"\nF1 kata tertinggi: {menang}")


if __name__ == "__main__":
    main()
