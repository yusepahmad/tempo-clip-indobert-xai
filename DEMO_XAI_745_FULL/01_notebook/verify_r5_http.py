"""Verifikasi HTTP R5: peta utama gabungan tiga task + bukti task pilihan.

Jalankan saat server demo hidup:
    TEMPO_DEMO_URL=http://127.0.0.1:7861 venv/bin/python 01_notebook/verify_r5_http.py
Output: 04_hasil_eksperimen/revisi_week3/r5_heatmap_verification.json
(path dihitung dari lokasi script, tidak menimpa bukti lain).
"""
import hashlib, json, os, time
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "04_hasil_eksperimen" / "revisi_week3" / "r5_heatmap_verification.json"
BASE = os.environ.get("TEMPO_DEMO_URL", "http://127.0.0.1:7861")
PNG = b"\x89PNG\r\n\x1a\n"


def png_hash(url):
    r = requests.get(BASE + url, timeout=60)
    assert r.ok and r.content.startswith(PNG), (url, r.status_code)
    return hashlib.sha256(r.content).hexdigest()


def analisis(data, files=None):
    t = time.time()
    r = requests.post(BASE + "/api/analisis", data=data, files=files, timeout=600)
    assert r.ok, r.text[:500]
    d = r.json()
    padu, task = d["heatmap_padu_url"], d["heatmap_url"]
    assert padu and task and padu != task, (padu, task)
    per = d["heatmap_per_task"]
    assert set(per) == {"task1_issue", "task2_domain_sumber", "task3_primary_entity_type"}, per.keys()
    h_padu, h_task = png_hash(padu), png_hash(task)
    h_per = {k: png_hash(v["url"]) for k, v in per.items()}
    assert h_padu != h_task
    # Peta task pilihan = peta per task untuk task yang diminta.
    assert h_task == h_per[d["task_id"]], "heatmap_url bukan peta task pilihan"
    return {"task_id": d["task_id"], "task_xai": d["task_xai"],
            "kelas_untuk_atribusi": d["kelas_untuk_atribusi"],
            "kelas_untuk_atribusi_tampil": d["kelas_untuk_atribusi_tampil"],
            "input_source": d["snapshot"]["input_source"], "metode_atribusi": d["metode_atribusi"],
            "heatmap_padu_sha256": h_padu, "heatmap_task_sha256": h_task,
            "heatmap_per_task_sha256": h_per, "seconds": round(time.time() - t, 1)}


page = requests.get(BASE + "/", timeout=30).text
halaman = {"imgHeatTask": 'id="imgHeatTask"' in page, "renderPetaPanas": "renderPetaPanas(plain)" in page,
           "renderer_lama_hilang": "const utama = d.heatmap_url" not in page}
assert all(halaman.values()), halaman

sample = requests.get(BASE + "/api/samples", timeout=30).json()[0]["sample_id"]
dataset = [analisis({"sample_id": sample, "task": t, "metode_atribusi": "occlusion"})
           for t in ("task1_issue", "task2_domain_sumber", "task3_primary_entity_type")]
# Satu input yang sama -> satu peta gabungan yang sama, apa pun task pilihannya.
padu_sama = len({r["heatmap_padu_sha256"] for r in dataset}) == 1
task_beda = len({r["heatmap_task_sha256"] for r in dataset}) == 3

foto = ROOT / "06_gambar_revisi" / "WhatsApp Image 2026-09-29 at 04.33.42.jpeg"
with open(foto, "rb") as f:
    unggahan = analisis({"task": "task2_domain_sumber", "headline": "GULA-GULA DEMO BURUH",
                         "supporting": "", "metode_atribusi": "occlusion"},
                        files={"gambar": (foto.name, f, "image/jpeg")})

hasil = {"tanggal": time.strftime("%Y-%m-%d %H:%M:%S"), "server": BASE,
         "plan": "docs/plans/2026-10-06-r5-peta-gabungan-dan-changelog.md",
         "halaman": halaman, "sample_id": sample, "dataset_per_task": dataset,
         "peta_gabungan_identik_antar_task": padu_sama, "peta_task_berbeda_antar_task": task_beda,
         "unggahan_foto_dosen": {"file": foto.name, **unggahan},
         "batas": ["HTTP + hash PNG, bukan review visual browser",
                   "occlusion dipakai demi waktu; R5 tidak bergantung metode atribusi kata",
                   "kelas unggahan bukan ground truth tervalidasi"]}
assert padu_sama and task_beda, hasil
hasil["status"] = "success"
OUT.write_text(json.dumps(hasil, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({k: hasil[k] for k in ("status", "halaman", "peta_gabungan_identik_antar_task",
                                        "peta_task_berbeda_antar_task")}, ensure_ascii=False))
print("R5 HTTP VERIFIED ->", OUT.relative_to(ROOT))
