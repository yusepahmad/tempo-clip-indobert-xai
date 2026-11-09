"""Bangun folder kernel Kaggle E01 (full/ dan smoke/) dari 01_notebook/e01_vlm.py.

Kernel script Kaggle hanya mengunggah code_file, jadi tiap folder berisi salinan
utuh e01_vlm.py yang hanya berbeda pada LIMIT dan BATAS_MENIT.
Plan: docs/plans/2026-10-08-e01-vlm-dua-tahap-kaggle.md

    venv/bin/python 01_notebook/kaggle_e01/siapkan_kernel.py
"""
import json
import pathlib
import re

DI_SINI = pathlib.Path(__file__).resolve().parent
SUMBER = DI_SINI.parent / "e01_vlm.py"
DATASET = "research-account/tempo-benchmark-20261005"
KERNEL = {
    "full": {"id": "research-account/tempo-e01-vlm", "title": "Tempo E01 VLM", "limit": 0, "batas_menit": 600},
    "smoke": {"id": "research-account/tempo-e01-vlm-smoke", "title": "Tempo E01 VLM Smoke", "limit": 12, "batas_menit": 40},
}

teks = SUMBER.read_text()
for nama, k in KERNEL.items():
    folder = DI_SINI / nama
    folder.mkdir(exist_ok=True)
    salinan, n = re.subn(r"^LIMIT = .*$", f"LIMIT = {k['limit']}  # diatur siapkan_kernel.py ({nama})",
                         teks, count=1, flags=re.M)
    assert n == 1, "Baris LIMIT tidak ditemukan di e01_vlm.py"
    salinan, n = re.subn(r"^BATAS_MENIT = .*$", f"BATAS_MENIT = {k['batas_menit']}  # diatur siapkan_kernel.py ({nama})",
                         salinan, count=1, flags=re.M)
    assert n == 1, "Baris BATAS_MENIT tidak ditemukan di e01_vlm.py"
    (folder / "e01_vlm.py").write_text(salinan)
    (folder / "kernel-metadata.json").write_text(json.dumps({
        "id": k["id"], "title": k["title"], "code_file": "e01_vlm.py",
        "language": "python", "kernel_type": "script", "is_private": True,
        "enable_gpu": True, "enable_internet": True,
        "dataset_sources": [DATASET], "competition_sources": [],
        "kernel_sources": [], "model_sources": [],
    }, indent=2) + "\n")
    print(f"{folder.relative_to(DI_SINI.parents[1])}: LIMIT={k['limit']}, BATAS_MENIT={k['batas_menit']}, id={k['id']}")
