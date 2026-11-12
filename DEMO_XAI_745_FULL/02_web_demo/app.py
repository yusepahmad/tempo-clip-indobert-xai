#!/usr/bin/env python3
"""Serve E42 checkpoints by default; explicit legacy backends remain available.
Inference and XAI share the active E42 fold(s); production never trains E42.
"""

from __future__ import annotations

import io
import json
import os
import re
import time
import uuid
import hashlib
import threading
import shutil
import traceback
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from flask import Flask, jsonify, request, send_file, send_from_directory, Response
from PIL import Image
from werkzeug.exceptions import HTTPException, RequestEntityTooLarge

from label_display import nama_task, tampil
from explanation_evidence import explain, ringkas
from class_catalog import catalog
from xai_core import (DEFINISI_DOMAIN, TASKS, XAIEngine, heatmap_overlay,
                      susun_kesimpulan, susun_penjelasan)
from batch_jobs import (AntreanPenuh, BatchJobs, JobTidakDitemukan,
                        saring_path)

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
# Folder cache/job dapat dialihkan lewat variabel lingkungan (dipakai test agar
# tidak menyentuh _cache/_jobs milik server yang sedang hidup).
CACHE = Path(os.environ.get("TEMPO_CACHE_DIR") or HERE / "_cache")
JOBS_DIR = Path(os.environ.get("TEMPO_JOBS_DIR") or HERE / "_jobs")
CACHE.mkdir(exist_ok=True)

# ---------------------------------------------------------------- batas input
# Audit backend 6 Okt (docs/plans/2026-10-06-audit-bug-kode.md, B2/B3).
#
# Gambar: PNG 147 byte berdimensi 1x16000 membuat praproses CLIP memakan
# +3,3 GB RAM. Dimensi dan rasio dicek dari header sebelum piksel didekode;
# gambar yang lolos diperkecil ke sisi terpanjang 2000 px sebelum disimpan.
# Gambar dataset (mode dataset) tidak melewati jalur ini.
Image.MAX_IMAGE_PIXELS = 40_000_000
# Batas dicek sendiri di baca_gambar (pesan ramah); peringatan bawaan PIL hanya
# mengotori log. Gambar > 2x batas tetap ditolak PIL saat dibuka.
warnings.simplefilter("ignore", Image.DecompressionBombWarning)
SISI_MAKS = 8000
RASIO_MAKS = 5.0
SISI_SIMPAN = 2000
# Teks: atribusi occlusion butuh ~0,14 detik per kata sambil memegang kunci
# model, jadi panjang judul dibatasi. Judul dataset terpanjang 129 karakter,
# teks pendukung terpanjang 370 karakter.
BATAS_HEADLINE = 300
BATAS_SUPPORTING = 2000
# Unggahan: satu sampul tidak perlu lebih dari 25 MB; batch boleh lebih besar.
BATAS_UNGGAH = 25 * 1024 * 1024
BATAS_UNGGAH_BATCH = 200 * 1024 * 1024
# Job batch yang berjalan + antre. Satu worker; job ketiga ditolak (429).
MAKS_JOB_AKTIF = 2

# Setiap analisis menyimpan sampai empat berkas PNG (peta terpadu + tiga peta
# per task) ditambah salinan gambar unggahan, semuanya bernama
# <awalan>_<analysis_id>... Pembersihan dilakukan per analisis (semua berkas
# satu analysis_id sekaligus), bukan per berkas, supaya hasil yang masih
# terbuka tidak kehilangan sebagian petanya.
BATAS_CACHE_ANALISIS = 150
UMUR_CACHE_DETIK = 2 * 3600
_KUNCI_CACHE = re.compile(r"^(?:cam|upload|ocr)_([0-9a-f]{32})")


def bersihkan_cache(batas: int = BATAS_CACHE_ANALISIS, umur: float = UMUR_CACHE_DETIK,
                    sekarang: float | None = None) -> None:
    """Hapus analisis lama dari folder cache.

    Sebuah analisis dihapus bila berumur > `umur` detik atau berada di luar
    `batas` analisis terbaru. Kegagalan menghapus (berkas sedang dibuka
    peramban, hal yang lazim di Windows) diabaikan — cache hanya sementara,
    dan gagal menghapus tidak boleh menggagalkan analisis.
    """
    sekarang = time.time() if sekarang is None else sekarang
    kelompok: dict[str, list] = {}
    try:
        for p in CACHE.glob("*.png"):
            m = _KUNCI_CACHE.match(p.name)
            kunci = m.group(1) if m else p.name
            try:
                mtime = p.stat().st_mtime
            except OSError:
                continue
            g = kelompok.setdefault(kunci, [0.0, []])
            g[0] = max(g[0], mtime)
            g[1].append(p)
    except OSError:
        return
    urut = sorted(kelompok.values(), key=lambda g: g[0], reverse=True)
    for rank, (mtime, berkas) in enumerate(urut):
        if rank < batas and sekarang - mtime <= umur:
            continue
        for p in berkas:
            try:
                p.unlink()
            except OSError:
                pass


class InputTidakSah(ValueError):
    """Masukan pengguna ditolak; dikirim sebagai JSON {"error": pesan}."""

    def __init__(self, pesan: str, kode: int = 400):
        super().__init__(pesan)
        self.kode = kode


def _teks(nilai) -> str:
    """Teks dataset: NaN/None menjadi string kosong (bukan "nan")."""
    if nilai is None:
        return ""
    try:
        if pd.isna(nilai):
            return ""
    except (TypeError, ValueError):
        pass
    return str(nilai)


def baca_gambar(data: bytes) -> Image.Image:
    """Dekode gambar unggahan dengan aman, kembalikan RGB maks SISI_SIMPAN px."""
    if not data:
        raise InputTidakSah("gambar tidak terbaca: berkas kosong")
    try:
        im = Image.open(io.BytesIO(data))  # hanya header; piksel belum didekode
        w, h = im.size
        if w < 1 or h < 1:
            raise InputTidakSah("gambar tidak terbaca: dimensi kosong")
        if max(w, h) > SISI_MAKS:
            raise InputTidakSah(f"gambar terlalu besar ({w}×{h} px); sisi maksimal {SISI_MAKS} px")
        if max(w, h) / min(w, h) > RASIO_MAKS:
            raise InputTidakSah(f"bentuk gambar tidak wajar untuk sampul ({w}×{h} px); "
                                f"perbandingan sisi maksimal {RASIO_MAKS:g}:1")
        if w * h > Image.MAX_IMAGE_PIXELS:
            raise Image.DecompressionBombError("terlalu banyak piksel")
        im.draft("RGB", (SISI_SIMPAN, SISI_SIMPAN))  # JPEG besar: dekode langsung di skala kecil
        im = im.convert("RGB")
    except InputTidakSah:
        raise
    except Image.DecompressionBombError:
        raise InputTidakSah("gambar terlalu besar; maksimal "
                            + f"{Image.MAX_IMAGE_PIXELS:,}".replace(",", ".") + " piksel")
    except Image.UnidentifiedImageError:
        raise InputTidakSah("gambar tidak terbaca: format berkas tidak dikenali")
    except Exception as e:
        raise InputTidakSah(f"gambar tidak terbaca ({type(e).__name__})")
    im.thumbnail((SISI_SIMPAN, SISI_SIMPAN), Image.LANCZOS)
    return im


def _cek_teks(headline: str, supporting: str) -> None:
    if len(headline) > BATAS_HEADLINE:
        raise InputTidakSah(f"headline terlalu panjang ({len(headline)} karakter; maksimal {BATAS_HEADLINE})")
    if len(supporting) > BATAS_SUPPORTING:
        raise InputTidakSah(f"teks pendukung terlalu panjang ({len(supporting)} karakter; maksimal {BATAS_SUPPORTING})")


app = Flask(__name__, static_folder=None)
app.config["MAX_CONTENT_LENGTH"] = BATAS_UNGGAH_BATCH
MODEL_LOCK = threading.RLock()
OCR_LOCK = threading.RLock()
BACKEND_NAME=os.environ.get('TEMPO_BACKEND','e42-tail-grid')
RICH_BACKEND = BACKEND_NAME == 'clip-indobert-tail-rich256'
CHECKPOINT_BACKEND = BACKEND_NAME in ('e42-tail-grid','clip-indobert-tail-rich256')
from micro_e14_engine import MicroE14Engine, E14Unavailable
if BACKEND_NAME == 'micro-e14-qlora':
    ENG = MicroE14Engine()
elif BACKEND_NAME == 'e42-tail-grid':
    from e42_engine import E42Engine
    ENG = E42Engine()
elif RICH_BACKEND:
    from tail_rich_engine import TailRichEngine
    ENG = TailRichEngine()
elif BACKEND_NAME in ('clip-indobert-mtl','baseline'):
    from mtl_engine import MTLDeliveryEngine
    ENG = MTLDeliveryEngine()
else:
    raise ValueError('TEMPO_BACKEND tidak dikenal; pilih e42-tail-grid, clip-indobert-tail-rich256, clip-indobert-mtl, atau micro-e14-qlora')
SAMPLE_IDS = frozenset(str(x) for x in ENG.df["sample_id"])
if BACKEND_NAME == 'micro-e14-qlora':
    print(f"[init] MICRO-E14 ready={ENG.ready}; {ENG.reason}", flush=True)
elif CHECKPOINT_BACKEND:
    print(f'[init] backend={BACKEND_NAME}; version={ENG.manifest["version"]}; {len(ENG.df)} sampul; 5 checkpoint asli terverifikasi; CPU', flush=True)
else:
    print(f"[init] dataset {len(ENG.df)} sampul, dimensi fitur {ENG.X.shape[1]}")
    print("[init] melatih head MTL awal ...")
    ENG.train()
    print("[init] siap.")
_TRAINING_KEY = None

def train_context(exclude=None):
    global _TRAINING_KEY
    if _TRAINING_KEY != exclude:
        ENG.train(exclude_index=exclude)
        _TRAINING_KEY = exclude


def _galat(pesan: str, kode: int = 400):
    return jsonify({"error": pesan}), kode


# ---------------------------------------------------------- error handler JSON
# Frontend selalu memanggil res.json(); halaman HTML bawaan Flask membuatnya
# gagal dengan "Unexpected token '<'".

def _rute_api() -> bool:
    return request.path.startswith("/api/")


@app.errorhandler(RequestEntityTooLarge)
def _terlalu_besar(e):
    batas = request.max_content_length or app.config["MAX_CONTENT_LENGTH"]
    return _galat(f"berkas terlalu besar (maksimal {batas // (1024 * 1024)} MB per permintaan)", 413)


@app.errorhandler(HTTPException)
def _galat_http(e):
    if not _rute_api():
        return e
    pesan = {404: "tidak ditemukan", 405: "metode HTTP tidak didukung"}.get(e.code, e.name.lower())
    return _galat(pesan, e.code)


@app.errorhandler(Exception)
def _galat_server(e):
    print(f"[galat] {request.method} {request.path}:\n{traceback.format_exc()}", flush=True)
    if not _rute_api():
        return "Terjadi kesalahan di server", 500
    return _galat("terjadi kesalahan di server; lihat log server", 500)


@app.errorhandler(E14Unavailable)
def _e14_unavailable(e):
    # Explicit 503, never fallback to the old model or saved OOF predictions.
    return _galat(str(e), 503)


# --------------------------------------------------------------------------


@app.route("/")
def index():
    return send_from_directory(HERE, "index.html")


@app.route("/api/samples")
def samples():
    out = []
    for _, r in ENG.df.iterrows():
        out.append({
            "sample_id": r["sample_id"],
            "headline": _teks(r["headline_verified"]),
            "supporting": _teks(r.get("supporting_text_verified")),
            "rich": {k:ENG.rich_inputs[str(r["sample_id"])][k] for k in ("description","source_visual","reason")} if RICH_BACKEND else {},
            "domain": str(r["task2_domain_sumber"]),
            # Istilah awam untuk daftar pilihan (revisi 15 Sep, R2).
            "domain_tampil": tampil(str(r["task2_domain_sumber"])),
            "issue": str(r["task1_issue"]),
            "issue_tampil": tampil(str(r["task1_issue"])),
        })
    return jsonify(out)


def _gambar_dataset(sample_id: str) -> Path | None:
    # Hanya sample_id yang ada di dataset: mencegah "..\" (Windows) dan
    # karakter aneh lain ikut menyusun path.
    if sample_id not in SAMPLE_IDS:
        return None
    for ext in (".jpg", ".jpeg", ".png", ".webp"):
        p = ROOT / "05_gambar" / f"{sample_id}{ext}"
        if p.exists():
            return p
    return None


@app.route("/api/image/<sample_id>")
def image(sample_id):
    # Gambar dalam paket dinamai <sample_id>.<ext> di folder 05_gambar.
    p = _gambar_dataset(sample_id)
    if p is None:
        return _galat("gambar tidak ditemukan", 404)
    return send_file(p)


@app.route("/api/unggahan/<token>")
def unggahan(token):
    if not re.fullmatch(r"[A-Za-z0-9_]+", token):
        return _galat("token tidak sah", 400)
    p = CACHE / f"{token}_src.png"
    if not p.exists():
        return _galat("tidak ditemukan", 404)
    return send_file(p)


@app.route("/api/heatmap/<token>")
def heatmap(token):
    # Token dipakai untuk menyusun nama berkas, jadi dibatasi pada karakter
    # yang memang dihasilkan sendiri (huruf, angka, garis bawah). Tanpa ini
    # token seperti "../../etc/passwd" akan menunjuk ke luar folder cache.
    if not re.fullmatch(r"[A-Za-z0-9_]+", token):
        return _galat("token tidak sah", 400)
    p = CACHE / f"{token}.png"
    if not p.exists():
        return _galat("tidak ditemukan", 404)
    return send_file(p)


def _saring_ocr(hasil: dict) -> dict:
    """`catatan` OCR bisa memuat pesan exception berisi path server."""
    if isinstance(hasil.get("catatan"), str):
        hasil["catatan"] = saring_path(hasil["catatan"])
    return hasil


@app.route("/api/ocr", methods=["POST"])
def ocr():
    """Baca teks sampul untuk mengisi kolom headline (revisi 15 Sep, R1).

    Dipanggil segera setelah pengguna memilih berkas, sebelum menekan
    "Analisis". Hasilnya hanya mengisi kolom — pengguna tetap dapat
    menyuntingnya. Kegagalan OCR dilaporkan apa adanya dan tidak pernah
    menggagalkan proses unggah.
    """
    request.max_content_length = BATAS_UNGGAH
    upload = request.files.get("gambar")
    if upload is None:
        return _galat("tidak ada gambar")
    try:
        gambar = baca_gambar(upload.read())
    except InputTidakSah as e:
        return _galat(str(e), e.kode)

    import ocr_headline

    path = CACHE / f"ocr_{uuid.uuid4().hex}_src.png"
    gambar.save(path)
    try:
        with OCR_LOCK:
            hasil = ocr_headline.baca(path)
    finally:
        try:
            path.unlink()  # berkas sementara, gambar asli diunggah ulang saat analisis
        except OSError:
            pass

    hasil["mesin"] = ocr_headline.mesin_aktif()
    return jsonify(_saring_ocr(hasil))


@app.route('/api/models')
def get_models():
    description = ENG.description()
    if BACKEND_NAME in ('clip-indobert-mtl','baseline'):
        state_path = ROOT/'04_hasil_eksperimen/next_research_20261017/07_micro_e14_deployment/job_state.json'
        if state_path.exists():
            state = json.loads(state_path.read_text())
            description['micro_e14_deployment'] = dict(status=state['status'], observed_at=state['observed_at'],
                note='Last observed Kaggle job status, not live inference readiness; baseline remains active')
    return jsonify(description)


@app.route("/api/catalog")
def get_catalog():
    return jsonify(catalog(ENG, DEFINISI_DOMAIN))


def siapkan_masukan(form: dict, gambar_bytes: bytes | None, batch: bool = False) -> dict:
    """Validasi masukan analisis TANPA memegang kunci model.

    Dipakai oleh /api/analisis dan worker batch. Melempar InputTidakSah.
    `form` berisi string; kunci yang tidak ada berarti "tidak dikirim"
    (berbeda dengan string kosong untuk headline mode dataset).
    """
    task = (form.get("task") or "task2_domain_sumber").strip()
    if task not in TASKS:
        raise InputTidakSah("task tidak sah")

    metode = (form.get("metode_atribusi") or "").strip().lower() or ("occlusion" if batch else "lime")
    if metode not in ("lime", "occlusion"):
        raise InputTidakSah("metode_atribusi tidak sah (pilih lime atau occlusion)")

    m = {"task": task, "metode": metode, "batch": batch}
    sample_id = (form.get("sample_id") or "").strip()
    if sample_id:
        row = ENG.df[ENG.df["sample_id"] == sample_id]
        if row.empty:
            raise InputTidakSah("sample_id tidak ditemukan")
        img_path = _gambar_dataset(sample_id)
        if img_path is None:
            raise InputTidakSah(f"gambar tidak ditemukan: {sample_id}", 404)
        r = row.iloc[0]
        headline_asli = _teks(r["headline_verified"])
        supporting_asli = _teks(r.get("supporting_text_verified"))
        headline = form["headline"].strip() if form.get("headline") is not None else headline_asli
        supporting = form["supporting"].strip() if form.get("supporting") is not None else supporting_asli
        if not headline:
            raise InputTidakSah("headline wajib diisi")
        _cek_teks(headline, supporting)
        m.update(mode="dataset", sample_id=sample_id, i=int(row.index[0]), row=r, img_path=img_path,
                 headline=headline, supporting=supporting,
                 teks_berubah=(headline != headline_asli or supporting != supporting_asli))
    elif gambar_bytes is not None:
        headline = (form.get("headline") or "").strip()
        supporting = (form.get("supporting") or "").strip()
        if not headline:
            raise InputTidakSah("headline wajib diisi untuk gambar unggahan")
        _cek_teks(headline, supporting)
        m.update(mode="unggahan", gambar=baca_gambar(gambar_bytes), headline=headline, supporting=supporting)
    else:
        raise InputTidakSah("pilih sampul dataset atau unggah gambar")
    if RICH_BACKEND:
        defaults = ENG.rich_inputs[m["sample_id"]] if m["mode"] == "dataset" else {}
        fields = {k:str(form[k] if k in form else defaults.get(k, "")).strip()
                  for k in ("description", "source_visual", "reason")}
        if any(len(v)>3000 for v in fields.values()):
            raise InputTidakSah("Keterangan visual maksimal 3000 karakter per kolom")
        if any(not v for v in fields.values()):
            raise InputTidakSah("Lengkapi deskripsi gambar, objek/perumpamaan visual dan alasan visual untuk model rich")
        m["rich_fields"] = fields
    return m


# Pembatalan analisis (audit F2): klien membatalkan analisis yang sudah tidak
# relevan (judul/task/gambar diganti). Tanpa ini server tetap menghitung sampai
# selesai sementara analisis baru menunggu MODEL_LOCK — dua kali lebih lama.
_REQ_ID = re.compile(r"^[0-9a-f]{8,64}$")
_DIBATALKAN: dict[str, float] = {}
_DIBATALKAN_LOCK = threading.Lock()


class Dibatalkan(Exception):
    pass


def _cek_batal(req_id: str | None) -> None:
    if req_id:
        with _DIBATALKAN_LOCK:
            if req_id in _DIBATALKAN:
                raise Dibatalkan()


@app.route("/api/analisis/batal", methods=["POST"])
def batal_analisis():
    req_id = (request.form.get("req_id") or "").strip().lower()
    if not _REQ_ID.match(req_id):
        return _galat("req_id tidak sah")
    sekarang = time.time()
    with _DIBATALKAN_LOCK:
        for k in [k for k, t in _DIBATALKAN.items() if sekarang - t > 600]:
            del _DIBATALKAN[k]
        if len(_DIBATALKAN) < 5000:
            _DIBATALKAN[req_id] = sekarang
    return jsonify({"dibatalkan": req_id})


@app.route("/api/analisis", methods=["POST"])
def analisis():
    # Body dibaca dan divalidasi SEBELUM mengunci model: klien yang mengirim
    # unggahan dengan lambat tidak boleh membekukan engine (audit B1).
    request.max_content_length = BATAS_UNGGAH
    form = request.form.to_dict()
    upload = request.files.get("gambar")
    req_id = (form.get("req_id") or "").strip().lower()
    try:
        masukan = siapkan_masukan(form, upload.read() if upload is not None else None)
        masukan["req_id"] = req_id if _REQ_ID.match(req_id) else None
        with MODEL_LOCK:
            _cek_batal(masukan["req_id"])   # dibatalkan saat masih antre: lewati
            return jsonify(analyse_core(masukan))
    except InputTidakSah as e:
        return _galat(str(e), e.kode)
    except Dibatalkan:
        return _galat("analisis dibatalkan oleh pengguna", 409)


_CATATAN_IN_SAMPLE = ("Catatan: hasil batch dataset memakai model yang ikut dilatih dengan sampul ini "
                      "(in-sample), jadi kecocokan dengan label anotator bukan ukuran akurasi.")


def analyse_core(m: dict) -> dict:
    """Jalankan analisis untuk masukan tervalidasi. Pemanggil memegang MODEL_LOCK."""
    if BACKEND_NAME == 'micro-e14-qlora':
        return analyse_e14(m)
    t0 = time.time()
    analysis_id = uuid.uuid4().hex
    task_xai = m["task"]
    batch = m["batch"]
    headline, supporting = m["headline"], m["supporting"]

    if m["mode"] == "dataset":
        sample_id, i, r, img_path = m["sample_id"], m["i"], m["row"], m["img_path"]
        # leave-one-out: sampul uji tidak ikut dilatih
        if CHECKPOINT_BACKEND:
            img_feat, txt_feat, vec = ENG.prepare_analysis(img_path, headline, supporting, sample_id,
                m.get("rich_fields"), cancel=lambda: _cek_batal(m.get('req_id')))
        else:
            train_context(None if batch else i)
            img_feat = ENG.X[i, :ENG.dim_img]
            txt_feat = ENG.X[i, ENG.dim_img:]
            vec = ENG.X[i]

        label_asli = {t: str(r[t]) for t in TASKS}
        catatan = {
            "sumber_metafora": _teks(r.get("task2_source_description")),
            "pemetaan_makna": _teks(r.get("task2_mapping_note")),
            "entitas": _teks(r.get("task3_primary_entity")),
        }
        mode = "dataset batch (eksplorasi, in-sample)" if batch else "dataset (leave-one-out)"
        if m["teks_berubah"] and not CHECKPOINT_BACKEND:
            img_feat, txt_feat = ENG.features_for(img_path, headline, supporting)
            vec = np.concatenate([img_feat, txt_feat])
        gambar_url = f"/api/image/{sample_id}"
    else:
        sample_id = ""
        # Token unggahan memakai analysis_id yang sama dengan peta panasnya,
        # sehingga pembersihan cache menghapus keduanya bersamaan.
        up_token = f"upload_{analysis_id}"
        img_path = CACHE / f"{up_token}_src.png"
        m["gambar"].save(img_path)

        if CHECKPOINT_BACKEND:
            img_feat, txt_feat, vec = ENG.prepare_analysis(img_path, headline, supporting, fields=m.get("rich_fields"),
                cancel=lambda: _cek_batal(m.get('req_id')))
        else:
            train_context()  # pakai seluruh 740 sampul sebagai data latih
            img_feat, txt_feat = ENG.features_for(img_path, headline, supporting)
            vec = np.concatenate([img_feat, txt_feat])
        label_asli = None
        catatan = None
        mode = "unggahan (tanpa label pembanding)"
        gambar_url = f"/api/unggahan/{up_token}"

    if CHECKPOINT_BACKEND:
        mode = ENG._context['protocol']
    if hasattr(ENG, 'set_context'):
        ENG.set_context(img_path, headline, supporting, img_feat, sample_id or None, batch,
                        cancel=lambda: _cek_batal(m.get('req_id')))
    pred = ENG.predict_vector(vec)
    # Grad-CAM
    #
    # Revisi 15 Sep (R5): peta panas per task tetap dihitung untuk tampilan
    # teknis, tetapi yang ditonjolkan ke pembaca adalah satu peta terpadu yang
    # mencakup ketiga task (peta utama tab Bukti gambar). Peta task pilihan
    # (`heatmap_url`) tampil terpisah dan menjadi dasar narasi/zona task itu.
    token = f"cam_{analysis_id}"
    _cek_batal(m.get("req_id"))
    cam_padu, cam_per_task = ENG.gradcam_terpadu(img_path, txt_feat)
    cam = cam_per_task.get(task_xai)

    heat_url = None
    if cam is not None:
        heatmap_overlay(img_path, cam, CACHE / f"{token}.png")
        heat_url = f"/api/heatmap/{token}"

    # peta terpadu (yang ditampilkan ke pembaca)
    heat_padu_url = None
    if cam_padu is not None:
        heatmap_overlay(img_path, cam_padu, CACHE / f"{token}_padu.png")
        heat_padu_url = f"/api/heatmap/{token}_padu"

    # peta per task, untuk ditelusuri bila pembaca ingin membandingkan
    heat_task_url = {}
    for t, c in cam_per_task.items():
        heatmap_overlay(img_path, c, CACHE / f"{token}_{t}.png")
        heat_task_url[t] = {
            "url": f"/api/heatmap/{token}_{t}",
            "nama_task": nama_task(t),
        }

    # atribusi kata (revisi 15 Sep, R4)
    #
    # LIME dipakai sebagai metode utama: diagram rancangan penelitian memang
    # menyebut LIME, dan pada uji 25 sampul ia lebih jarang menghasilkan
    # "semua kata negatif" — gejala yang dikeluhkan dosen (1/25 vs 2/25).
    # Rinciannya di 04_hasil_eksperimen/uji_banding_atribusi.json.
    #
    # Occlusion tetap tersedia dan dapat dipilih lewat parameter `metode`,
    # karena LIME ~21x lebih lambat (17,7 detik vs 0,83 detik per sampul pada
    # uji banding dengan 200 varian; aplikasi kini memakai 120 varian).
    # Untuk pemrosesan banyak sampul sekaligus, occlusion jauh lebih masuk akal,
    # sehingga batch memakai occlusion secara baku (lihat siapkan_masukan).
    metode = m["metode"]
    # Titik periksa sebelum atribusi kata (tahap terlama, terutama LIME).
    _cek_batal(m.get("req_id"))

    if metode == "lime":
        try:
            kata, kelas_kata, prob_kata = ENG.atribusi_kata_lime(
                img_feat, headline, supporting, task_xai)
        except Dibatalkan:
            raise
        except Exception as e:
            # Kegagalan LIME (mis. pustaka tidak terpasang) tidak boleh
            # menggagalkan analisis — jatuh kembali ke occlusion.
            print(f"[peringatan] LIME gagal ({type(e).__name__}: {e}), "
                  f"memakai occlusion.", flush=True)
            metode = "occlusion"

    if metode == "occlusion":
        kata, kelas_kata, prob_kata = ENG.atribusi_kata(
            img_feat, headline, supporting, task_xai)

    # penjelasan naratif: dirangkai dari komponen yang asalnya jelas,
    # tidak ada teks yang dihasilkan model bahasa.
    # Narasi dan zona memakai peta task pilihan (`cam`), bukan peta gabungan:
    # klaim penjelasan harus terikat pada task/kelas yang dijelaskan (R5).
    #
    # Sejak 6 Okt narasi disusun explanation_evidence.py: `explain()` untuk
    # tab Penjelasan (task pilihan) dan `ringkas()` untuk kartu "Ringkasan
    # interpretasi" di tab Prediksi (ketiga task) — keduanya memenuhi
    # permintaan R3 (revisi 15 Sep) akan paragraf berbahasa awam.
    # susun_penjelasan/susun_kesimpulan di xai_core masih diimpor tetapi
    # tidak dipakai di sini lagi.
    from xai_core import zona_dominan
    operational=json.loads((HERE/"codebook_operasional.json").read_text(encoding='utf-8'))
    current_definitions={label:entry["definition"] for label,entry in operational.items()}
    kesimpulan = explain(pred, task_xai, kata, catatan, cam, headline, current_definitions, zona_dominan, label=label_asli)
    # Tab Penjelasan: blok alasan untuk task pilihan (tanpa klaim lintas task).
    penjelasan = [{"label":x["label"], "asal":x["asal"].lower(), "teks":x["teks"]} for x in kesimpulan["blok"]]
    # Tab Prediksi: ringkasan awam ketiga task, terpisah dari penjelasan.
    ringkasan = ringkas(pred, headline, label=label_asli, catatan=catatan)
    if batch and label_asli and not CHECKPOINT_BACKEND:
        # Batch dataset memakai model in-sample (audit B14): kecocokan dengan
        # anotator di sini tidak boleh dibaca sebagai akurasi.
        batch_note = _CATATAN_IN_SAMPLE
        bagian_anotator = [b for b in ringkasan["bagian"] if b["asal"] == "ANOTATOR"]
        if bagian_anotator:
            bagian_anotator[-1]["teks"] += " " + batch_note
        else:
            ringkasan["bagian"].append({"asal": "ANOTATOR", "teks": batch_note})
        ringkasan["paragraf"] = " ".join(b["teks"] for b in ringkasan["bagian"])

    model_info = {t: {k:p.get(k) for k in ('backend','model_version','score_kind','score_label','evaluation_mode','evaluation')}
                  for t,p in pred.items()}
    xai_info = ENG.xai_contract(task_xai) if hasattr(ENG, 'xai_contract') else {'model_version':'baseline-mtl-v1'}
    snapshot = {"analysis_id":analysis_id,"sample_id":sample_id or None,
                "image_sha256":hashlib.sha256(img_path.read_bytes()).hexdigest(),
                "headline":headline,"supporting":supporting,"task_id":task_xai,
                "class_id":kelas_kata,"model":pred[task_xai].get("model_version","baseline-mtl-v1"),"models":model_info,"xai":xai_info,
                "protocol":mode,"input_source":"dataset" if sample_id else "upload",
                "rich_fields":m.get("rich_fields", {})}
    hasil = {
        "analysis_id":analysis_id,"snapshot":snapshot,"task_id":task_xai,"models":model_info,"xai":xai_info,
        "evidence":kesimpulan["bukti"],"supporting":supporting,
        "mode": mode,
        "task_xai": nama_task(task_xai),
        "task_xai_teknis": TASKS[task_xai],
        "headline": headline,
        "prediksi": pred,
        "label_anotator": label_asli,
        "catatan_anotator": catatan,
        "heatmap_url": heat_url,
        # Peta terpadu ketiga task — inilah yang ditampilkan ke pembaca (R5).
        "heatmap_padu_url": heat_padu_url,
        "heatmap_per_task": heat_task_url,
        "atribusi_kata": kata,
        "kelas_untuk_atribusi": kelas_kata,
        "metode_atribusi": metode,
        "kelas_untuk_atribusi_tampil": tampil(kelas_kata),
        "prob_kelas_atribusi": prob_kata,
        "gambar_url": gambar_url,
        "penjelasan": penjelasan,
        "kesimpulan": kesimpulan,
        "ringkasan": ringkasan,
        "durasi_detik": round(time.time() - t0, 1),
    }

    bersihkan_cache()
    if label_asli:
        hasil["verifikasi"] = {
            t: {
                "prediksi": pred[t]["prediksi"],
                "prediksi_tampil": tampil(pred[t]["prediksi"]),
                "anotator": label_asli[t],
                # Istilah awam untuk label anotator (revisi 15 Sep, R2).
                "anotator_tampil": tampil(label_asli[t]),
                "cocok": pred[t]["prediksi"] == label_asli[t],
            }
            for t in TASKS
        }
    return hasil


def analyse_e14(m: dict) -> dict:
    """Same presentation schema, but no fabricated CLIP/IndoBERT explanation."""
    t0 = time.time()
    if m['mode'] != 'dataset':
        raise E14Unavailable('Unggahan baru belum didukung MICRO-E14: fitur visual E01 belum tersedia. Gunakan dataset atau backend baseline secara eksplisit.')
    task, sample_id = m['task'], m['sample_id']
    pred = ENG.predict_image(m['img_path'], m['headline'], m['supporting'], sample_id,
                             cancel=lambda:_cek_batal(m.get('req_id')))
    selected = pred[task]
    analysis_id = uuid.uuid4().hex
    mode = 'dataset deployment refit seluruh 740; in-sample, bukan OOF/leave-one-out'
    limitation = ('XAI visual dan atribusi kata MICRO-E14 belum diimplementasikan. '
                  'Tidak menampilkan peta CLIP atau atribusi IndoBERT. '
                  'Kecocokan sampul dataset ini bukan benchmark karena ikut dilatih. '
                  'Angka CV historis bukan evaluasi checkpoint deployment.')
    if m['teks_berubah']:
        limitation += ' Teks diedit; konteks visual E01 tetap historis. Kombinasi input ini belum dievaluasi.'
    xai = dict(model_version=selected['model_version'], task=task, available=False,
               visual_method=None, text_method=None, limitation=limitation)
    label = {t:str(m['row'][t]) for t in TASKS}
    parts = [dict(asal='MODEL', teks='Prediksi model: '+ '; '.join(nama_task(t)+': '+tampil(pred[t]['prediksi']) for t in TASKS)+'.'),
             dict(asal='METODE', teks=limitation)]
    summary = dict(bagian=parts, paragraf=' '.join(p['teks'] for p in parts),
                   keyakinan='belum dikalibrasi', tanda='Eksplorasi in-sample — bukan hasil OOF')
    models = {t:{k:p.get(k) for k in ('backend','model_version','score_kind','score_label','evaluation_mode','evaluation')} for t,p in pred.items()}
    evidence = dict(model_version=selected['model_version'], prompt_sha256={t:p['prompt_sha256'] for t,p in pred.items()},
                    attribution='Not Implemented', input='image + verified text + frozen label-free E01 visual context; annotation labels NOT passed to model')
    snapshot = dict(analysis_id=analysis_id, sample_id=sample_id, image_sha256=hashlib.sha256(m['img_path'].read_bytes()).hexdigest(),
                    headline=m['headline'], supporting=m['supporting'], task_id=task, class_id=selected['prediksi'],
                    model=selected['model_version'], models=models, xai=xai, protocol=mode, input_source='dataset')
    return dict(analysis_id=analysis_id, snapshot=snapshot, task_id=task, models=models, xai=xai, evidence=evidence,
                mode=mode, headline=m['headline'], supporting=m['supporting'], prediksi=pred, label_anotator=label,
                catatan_anotator=None, task_xai=nama_task(task), task_xai_teknis=TASKS[task],
                heatmap_url=None, heatmap_padu_url=None, heatmap_per_task={}, atribusi_kata=[], metode_atribusi='unavailable',
                kelas_untuk_atribusi=selected['prediksi'], kelas_untuk_atribusi_tampil=tampil(selected['prediksi']),
                prob_kelas_atribusi=selected['probabilitas'], gambar_url=f'/api/image/{sample_id}',
                penjelasan=[dict(label='Batasan MICRO-E14', asal='metode', teks=limitation)],
                kesimpulan=dict(paragraf=summary['paragraf'], blok=[], bukti=evidence), ringkasan=summary,
                verifikasi={t:dict(prediksi=pred[t]['prediksi'], prediksi_tampil=tampil(pred[t]['prediksi']),
                                  anotator=label[t], anotator_tampil=tampil(label[t]), cocok=pred[t]['prediksi']==label[t]) for t in TASKS},
                durasi_detik=round(time.time()-t0,1))


# One processing core, serial engine access, independent persisted batch output.
def _normalisasi_input_batch(item, folder) -> Path:
    """Validasi & perkecil berkas unggahan batch sekali; simpan sebagai PNG.

    Berkas mentah (input_N.bin) diganti input_N.png yang sudah lolos batas
    dimensi/rasio dan berukuran maks SISI_SIMPAN px.
    """
    path = folder / item["input_file"]
    if path.suffix == ".png" and path.name.startswith("input_"):
        return path
    gambar = baca_gambar(path.read_bytes())  # InputTidakSah -> item "failed" dengan pesan ramah
    norm = path.with_suffix(".png")
    gambar.save(norm)
    item["input_file"] = norm.name
    try:
        path.unlink()
    except OSError:
        pass
    return norm


def batch_runner(job,item,folder):
    form={"task":job["task"],"metode_atribusi":job["method"]}
    gambar_bytes=None
    extra={}
    if item.get("sample_id"):
        form["sample_id"]=item["sample_id"]
    else:
        path=_normalisasi_input_batch(item,folder)
        extra["input_file"]=item["input_file"]
        if not item.get("reviewed"):
            import ocr_headline
            with OCR_LOCK:ocr=_saring_ocr(ocr_headline.baca(path))
            # Automatic text is offered for review, never silently treated as verified.
            return {"status":"needs_review","ocr":ocr,"headline":ocr.get("headline",""),"supporting":ocr.get("pendukung",""),**extra}
        gambar_bytes=path.read_bytes()
        form.update(headline=item["headline"],supporting=item.get("supporting",""))
    masukan=siapkan_masukan(form,gambar_bytes,batch=True)  # InputTidakSah -> item "failed"
    with MODEL_LOCK:result=analyse_core(masukan)
    assets=folder/"assets";assets.mkdir(exist_ok=True)
    def preserve(url):
        if not url:return url
        if url.startswith("/api/heatmap/"):
            name=url.rsplit("/",1)[1]+".png";source=CACHE/name
        elif url.startswith("/api/unggahan/"):
            name=url.rsplit("/",1)[1]+"_src.png";source=CACHE/name
        else:return url
        # Dipindah, bukan disalin: aset batch tidak ikut memenuhi cache
        # interaktif dan tidak hilang saat cache dibersihkan.
        shutil.move(str(source),str(assets/name))
        return f"/api/batch/{job['id']}/assets/{name}"
    for key in ("heatmap_url","heatmap_padu_url","gambar_url"):result[key]=preserve(result.get(key))
    for v in result["heatmap_per_task"].values():v["url"]=preserve(v["url"])
    return {"status":"success","result":result,**extra}

JOBS=BatchJobs(JOBS_DIR,batch_runner,max_aktif=MAKS_JOB_AKTIF)


def _job_atau_404(id):
    try:
        with JOBS.lock:return JOBS.get(id)
    except JobTidakDitemukan:
        return None


@app.route("/api/batch",methods=["POST"])
def batch_create():
    task=request.form.get("task","task2_domain_sumber")
    if task not in TASKS:return _galat("task tidak sah")
    try:ids=json.loads(request.form.get("sample_ids","[]"))
    except ValueError:return _galat("sample_ids harus JSON list")
    if not isinstance(ids,list) or not all(isinstance(x,str) for x in ids):return _galat("sample_ids harus list string")
    ids=[x.strip() for x in ids]
    files=request.files.getlist("gambar")
    if RICH_BACKEND and files:
        return _galat("Model rich memerlukan keterangan visual per gambar. Gunakan unggah satu gambar; batch dataset tetap tersedia.",422)
    if not 0<len(ids)+len(files)<=740:return _galat("Pilih 1–740 sampul")
    tak_dikenal=[x for x in dict.fromkeys(ids) if x not in SAMPLE_IDS]
    if tak_dikenal:
        contoh=", ".join(tak_dikenal[:10])+(f" (+{len(tak_dikenal)-10} lagi)" if len(tak_dikenal)>10 else "")
        return jsonify(error=f"sample_id tidak dikenal: {contoh}",sample_ids_tidak_dikenal=tak_dikenal),400
    method=request.form.get("metode_atribusi","occlusion")
    if method not in ("lime","occlusion"):return _galat("metode tidak sah")
    with JOBS.lock:
        try:JOBS.cek_kapasitas()
        except AntreanPenuh as e:return _galat(str(e),429)
        items=[{"name":x,"sample_id":x,"status":"queued"} for x in ids]
        job=JOBS.create(items,task,method);folder=JOBS.root/job["id"]
        for index,f in enumerate(files):
            name=f"input_{index}.bin";f.save(folder/name)
            job["items"].append({"name":f.filename or f"berkas_{index+1}","input_file":name,"status":"queued"})
        JOBS.save(job);JOBS.start(job["id"])
    return jsonify(id=job["id"]),202

@app.route("/api/batch/<id>")
def batch_status(id):
    j=_job_atau_404(id)
    if j is None:return _galat("job tidak ditemukan",404)
    counts={k:sum(x["status"]==k for x in j["items"]) for k in ("queued","running","success","failed","needs_review")}
    j["progress"]={"total":len(j["items"]),**counts};return jsonify(j)

@app.route("/api/batch/<id>/review/<int:index>",methods=["POST"])
def batch_review(id,index):
    headline=request.form.get("headline","");supporting=request.form.get("supporting","")
    try:_cek_teks(headline.strip(),supporting)
    except InputTidakSah as e:return _galat(str(e),e.kode)
    try:JOBS.review(id,index,headline,supporting)
    except JobTidakDitemukan:return _galat("job tidak ditemukan",404)
    except IndexError:return _galat("item tidak ditemukan",404)
    except AntreanPenuh as e:return _galat(str(e),429)
    except ValueError as e:return _galat(str(e))
    return jsonify(id=id),202

@app.route("/api/batch/<id>/resume",methods=["POST"])
def batch_resume(id):
    try:JOBS.resume(id)
    except JobTidakDitemukan:return _galat("job tidak ditemukan",404)
    except AntreanPenuh as e:return _galat(str(e),429)
    return jsonify(id=id),202

@app.route("/api/batch/<id>/export/<kind>")
def batch_export(id,kind):
    j=_job_atau_404(id)
    if j is None:return _galat("job tidak ditemukan",404)
    if kind=="json":return Response(json.dumps(j,ensure_ascii=False),mimetype="application/json",headers={"Content-Disposition":f"attachment; filename={id}.json"})
    if kind=="csv":return Response(JOBS.export_csv(j),mimetype="text/csv; charset=utf-8",headers={"Content-Disposition":f"attachment; filename={id}.csv"})
    return _galat("format tidak dikenal")

@app.route("/api/batch/<id>/assets/<name>")
def batch_asset(id,name):
    if _job_atau_404(id) is None:return _galat("job tidak ditemukan",404)
    if not re.fullmatch(r"[A-Za-z0-9_]+\.png",name):return _galat("tidak ditemukan",404)
    return send_from_directory(JOBS.root/id/"assets",name)

@app.route("/api/batch/<id>/input/<int:index>")
def batch_input(id,index):
    j=_job_atau_404(id)
    if j is None:return _galat("job tidak ditemukan",404)
    try:name=j["items"][index]["input_file"]
    except (IndexError,KeyError):return _galat("tidak ditemukan",404)
    if Path(name).name != name:return _galat("tidak ditemukan",404)
    return send_from_directory(JOBS.root/id,name)


if __name__ == "__main__":
    app.run(host=os.environ.get("TEMPO_HOST","127.0.0.1"), port=int(os.environ.get("TEMPO_PORT","7860")), debug=False)
