"""Repeat OCR on the three lecturer files in the project root.

References are agent visual transcriptions, not verified class annotations.
Run from project root with package venv. Originals are never modified.

Catatan 6 Okt: foto dibaca dari `06_gambar_revisi/` di paket delivery (jatuh
ke folder induk paket bila salinan tidak ada — tata letak mesin asal 5 Okt).
Keluaran baku `revisi_week3/gambar_dosen/` (bukti 5 Okt) TERTIMPA; berikan folder
lain sebagai argumen pertama untuk uji ulang tanpa menimpa:
    venv/bin/python 01_notebook/verify_gambar_dosen.py /tmp/gambar_dosen_ulang
"""
import hashlib
import json
import re
import sys
import time
from pathlib import Path

import torch
from PIL import Image

torch.set_num_threads(4)
package = Path(__file__).resolve().parents[1]
project = package.parent
sys.path.insert(0, str(package / "02_web_demo"))
from ocr_headline import baca

out = Path(sys.argv[1]) if len(sys.argv) > 1 else package / "04_hasil_eksperimen/revisi_week3/gambar_dosen"
out.mkdir(parents=True, exist_ok=True)
cases = [("04.33.42", "GULA-GULA DEMO BURUH"), ("05.29.27", "WASWAS RUPIAH"), ("05.31.04", "CUKAI ABAL-ABAL ROKOK ILEGAL")]
records = []
for stamp, reference in cases:
    nama = f"WhatsApp Image 2026-09-29 at {stamp}.jpeg"
    file = package / "06_gambar_revisi" / nama
    if not file.exists():
        file = project / nama
    start = time.perf_counter()
    ocr = baca(file)
    elapsed = time.perf_counter() - start
    with Image.open(file) as image:
        dimensions = list(image.size)
    normalize = lambda s: re.sub(r"\s+", " ", s.strip()).upper()
    result = {"file": file.name, "sha256": hashlib.sha256(file.read_bytes()).hexdigest(), "dimensions": dimensions, "headline_reference_agent_visual": reference, "reference_source": "Transkripsi visual agen dari file yang ditunjuk user sebagai gambar dosen; bukan label kelas atau validasi dosen", "ocr": ocr, "headline_exact": normalize(ocr["headline"]) == normalize(reference), "seconds": elapsed}
    records.append(result)
    (out / f"{stamp}.json").write_text(json.dumps(result, ensure_ascii=False, indent=2))
    print(file.name, result["headline_exact"], ocr["headline"], flush=True)
(out / "summary.json").write_text(json.dumps(records, ensure_ascii=False, indent=2))
