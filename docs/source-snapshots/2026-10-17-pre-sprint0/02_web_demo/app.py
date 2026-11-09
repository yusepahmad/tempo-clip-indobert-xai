#!/usr/bin/env python3
"""Web demo XAI — MTL CLIP-IndoBERT untuk dekoding metafora sampul Tempo.

Jalankan dari folder paket:
    Linux/macOS : ./jalankan_linux.sh
    Windows     : jalankan_windows.bat
atau langsung:
    cd 02_web_demo && ../venv/bin/python app.py
lalu buka http://127.0.0.1:7860

Dua mode:
  1. Pilih sampul dari dataset 740  -> model dilatih tanpa sampul itu
     (leave-one-out), sehingga prediksi jujur dan bisa dibandingkan dengan
     label anotator.
  2. Unggah gambar sampul sendiri   -> tidak ada label pembanding, murni
     melihat apa yang diprediksi model.

Semua angka yang ditampilkan adalah hasil model nyata, bukan ilustrasi.
"""

from __future__ import annotations

import io
import json
import re
import time
import uuid
import hashlib
import threading
import shutil
from functools import wraps
from pathlib import Path

import numpy as np
from flask import Flask, jsonify, request, send_file, send_from_directory, Response

from label_display import nama_task, tampil
from explanation_evidence import explain
from class_catalog import catalog
from xai_core import (DEFINISI_DOMAIN, TASKS, XAIEngine, heatmap_overlay,
                      susun_kesimpulan, susun_penjelasan)

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
CACHE = HERE / "_cache"
CACHE.mkdir(exist_ok=True)

# Setiap analisis menyimpan sampai empat berkas PNG (peta terpadu + tiga peta
# per task) ditambah salinan gambar unggahan. Tanpa pembersihan, folder cache
# tumbuh terus — terasa cepat bila dosen memproses banyak sampul berturut-turut.
BATAS_CACHE = 400


def bersihkan_cache(batas: int = BATAS_CACHE) -> None:
    """Sisakan berkas terbaru saja di folder cache.

    Dipanggil setelah tiap analisis. Kegagalan menghapus (berkas sedang dibuka
    peramban, hal yang lazim di Windows) diabaikan — cache hanya sementara,
    dan gagal menghapus tidak boleh menggagalkan analisis.
    """
    try:
        berkas = sorted(CACHE.glob("*.png"), key=lambda p: p.stat().st_mtime, reverse=True)
    except OSError:
        return
    for p in berkas[batas:]:
        try:
            p.unlink()
        except OSError:
            pass

app = Flask(__name__, static_folder=None)
MODEL_LOCK = threading.RLock()
OCR_LOCK = threading.RLock()
ENG = XAIEngine()
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
            "headline": str(r["headline_verified"]),
            "supporting": "" if str(r.get("supporting_text_verified", "")).lower() in ("nan","none") else str(r.get("supporting_text_verified", "")),
            "domain": str(r["task2_domain_sumber"]),
            # Istilah awam untuk daftar pilihan (revisi 15 Sep, R2).
            "domain_tampil": tampil(str(r["task2_domain_sumber"])),
            "issue": str(r["task1_issue"]),
            "issue_tampil": tampil(str(r["task1_issue"])),
        })
    return jsonify(out)


@app.route("/api/image/<sample_id>")
def image(sample_id):
    # Gambar dalam paket dinamai <sample_id>.<ext> di folder 05_gambar.
    for ext in (".jpg", ".jpeg", ".png", ".webp"):
        p = ROOT / "05_gambar" / f"{sample_id}{ext}"
        if p.exists():
            return send_file(p)
    return "gambar tidak ditemukan", 404


@app.route("/api/unggahan/<token>")
def unggahan(token):
    if not re.fullmatch(r"[A-Za-z0-9_]+", token):
        return "token tidak sah", 400
    p = CACHE / f"{token}_src.png"
    if not p.exists():
        return "tidak ditemukan", 404
    return send_file(p)


@app.route("/api/heatmap/<token>")
def heatmap(token):
    # Token dipakai untuk menyusun nama berkas, jadi dibatasi pada karakter
    # yang memang dihasilkan sendiri (huruf, angka, garis bawah). Tanpa ini
    # token seperti "../../etc/passwd" akan menunjuk ke luar folder cache.
    if not re.fullmatch(r"[A-Za-z0-9_]+", token):
        return "token tidak sah", 400
    p = CACHE / f"{token}.png"
    if not p.exists():
        return "tidak ditemukan", 404
    return send_file(p)


@app.route("/api/ocr", methods=["POST"])
def ocr():
    """Baca teks sampul untuk mengisi kolom headline (revisi 15 Sep, R1).

    Dipanggil segera setelah pengguna memilih berkas, sebelum menekan
    "Analisis". Hasilnya hanya mengisi kolom — pengguna tetap dapat
    menyuntingnya. Kegagalan OCR dilaporkan apa adanya dan tidak pernah
    menggagalkan proses unggah.
    """
    upload = request.files.get("gambar")
    if upload is None:
        return jsonify({"error": "tidak ada gambar"}), 400

    import ocr_headline

    token = f"ocr_{int(time.time()*1000)}"
    path = CACHE / f"{token}_src.png"
    try:
        from PIL import Image
        Image.open(io.BytesIO(upload.read())).convert("RGB").save(path)
    except Exception as e:
        return jsonify({"error": f"gambar tidak terbaca: {type(e).__name__}"}), 400

    with OCR_LOCK:
        hasil = ocr_headline.baca(path)
    try:
        path.unlink()  # berkas sementara, gambar asli diunggah ulang saat analisis
    except OSError:
        pass

    hasil["mesin"] = ocr_headline.mesin_aktif()
    return jsonify(hasil)


@app.route("/api/catalog")
def get_catalog():
    return jsonify(catalog(ENG, DEFINISI_DOMAIN))


@app.route("/api/analisis", methods=["POST"])
def analisis():
    with MODEL_LOCK:
        return analyse_core()


def analyse_core(batch=False):
    t0 = time.time()
    analysis_id = uuid.uuid4().hex
    task_xai = request.form.get("task", "task2_domain_sumber")
    if task_xai not in TASKS:
        return jsonify({"error":"task tidak sah"}),400

    sample_id = request.form.get("sample_id", "").strip()
    upload = request.files.get("gambar")

    if sample_id:
        row = ENG.df[ENG.df["sample_id"] == sample_id]
        if row.empty:
            return jsonify({"error": "sample_id tidak ditemukan"}), 400
        i = int(row.index[0])
        r = row.iloc[0]
        img_path = None
        for ext in (".jpg", ".jpeg", ".png", ".webp"):
            kandidat = ROOT / "05_gambar" / f"{sample_id}{ext}"
            if kandidat.exists():
                img_path = kandidat
                break
        if img_path is None:
            return jsonify({"error": f"gambar tidak ditemukan: {sample_id}"}), 404
        headline = str(r["headline_verified"])
        supporting = str(r.get("supporting_text_verified", "") or "")

        # leave-one-out: sampul uji tidak ikut dilatih
        train_context(None if batch else i)
        img_feat = ENG.X[i, :ENG.dim_img]
        txt_feat = ENG.X[i, ENG.dim_img:]
        vec = ENG.X[i]

        label_asli = {t: str(r[t]) for t in TASKS}
        catatan = {
            "sumber_metafora": str(r.get("task2_source_description", "") or ""),
            "pemetaan_makna": str(r.get("task2_mapping_note", "") or ""),
            "entitas": str(r.get("task3_primary_entity", "") or ""),
        }
        mode = "dataset batch (eksplorasi, in-sample)" if batch else "dataset (leave-one-out)"
        final_headline = request.form.get("headline", headline).strip()
        final_supporting = request.form.get("supporting", supporting).strip()
        if not final_headline:
            return jsonify({"error":"headline wajib diisi"}),400
        if final_headline != headline or final_supporting != supporting:
            headline, supporting = final_headline, final_supporting
            img_feat, txt_feat = ENG.features_for(img_path, headline, supporting)
            vec = np.concatenate([img_feat, txt_feat])
        gambar_url = f"/api/image/{sample_id}"
    elif upload is not None:
        headline = request.form.get("headline", "").strip()
        supporting = request.form.get("supporting", "").strip()
        if not headline:
            return jsonify({"error": "headline wajib diisi untuk gambar unggahan"}), 400
        up_token = f"upload_{uuid.uuid4().hex}"
        img_path = CACHE / f"{up_token}_src.png"
        from PIL import Image
        try:
            Image.open(io.BytesIO(upload.read())).convert("RGB").save(img_path)
        except Exception:
            return jsonify({"error":"gambar tidak terbaca"}),400

        train_context()  # pakai seluruh 740 sampul sebagai data latih
        img_feat, txt_feat = ENG.features_for(img_path, headline, supporting)
        vec = np.concatenate([img_feat, txt_feat])
        label_asli = None
        catatan = None
        mode = "unggahan (tanpa label pembanding)"
        gambar_url = f"/api/unggahan/{up_token}"
    else:
        return jsonify({"error": "pilih sampul dataset atau unggah gambar"}), 400

    pred = ENG.predict_vector(vec)

    # Grad-CAM
    #
    # Revisi 15 Sep (R5): peta panas per task tetap dihitung untuk tampilan
    # teknis, tetapi yang ditonjolkan ke pembaca adalah satu peta terpadu yang
    # mencakup ketiga task.
    token = f"cam_{analysis_id}"
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
    # karena LIME ~21x lebih lambat (17,7 detik vs 0,83 detik per sampul).
    # Untuk pemrosesan banyak sampul sekaligus, occlusion jauh lebih masuk akal.
    metode = request.form.get("metode_atribusi", "occlusion" if batch else "lime").strip().lower()
    if metode not in ("lime", "occlusion"):
        metode = "lime"

    if metode == "lime":
        try:
            kata, kelas_kata, prob_kata = ENG.atribusi_kata_lime(
                img_feat, headline, supporting, task_xai)
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
    # Peta yang dinarasikan adalah peta terpadu, karena itu yang dilihat
    # pembaca; bila peta terpadu gagal dihitung, jatuh kembali ke peta task.
    cam_untuk_narasi = cam

    # Paragraf kesimpulan berbahasa awam (revisi 15 Sep, R3). Ditaruh di bawah
    # penjelasan teknis, sesuai permintaan dosen: "untuk sementara biar saja
    # begitu tapi tambah penjelasan di akhir di bawahnya".
    from xai_core import zona_dominan
    operational=json.loads((HERE/"codebook_operasional.json").read_text(encoding='utf-8'))
    current_definitions={label:entry["definition"] for label,entry in operational.items()}
    kesimpulan = explain(pred, task_xai, kata, catatan, cam, headline, current_definitions, zona_dominan)
    # Narrative and conclusion now share task-bound evidence; no cross-task claims.
    penjelasan = [{"label":"Penjelasan task pilihan", "asal":kesimpulan["asal"].lower(), "teks":kesimpulan["paragraf"]}]

    snapshot = {"analysis_id":analysis_id,"sample_id":sample_id or None,
                "image_sha256":hashlib.sha256(img_path.read_bytes()).hexdigest(),
                "headline":headline,"supporting":supporting,"task_id":task_xai,
                "class_id":kelas_kata,"model":"baseline frozen CLIP/IndoBERT + runtime MTL head",
                "protocol":mode,"input_source":"dataset" if sample_id else "upload"}
    hasil = {
        "analysis_id":analysis_id,"snapshot":snapshot,"task_id":task_xai,
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
    return jsonify(hasil)


# One processing core, serial engine access, independent persisted batch output.
def batch_runner(job,item,folder):
    from werkzeug.datastructures import FileStorage
    data={"task":job["task"],"metode_atribusi":job["method"]}
    handle=None
    if item.get("sample_id"):
        data["sample_id"]=item["sample_id"]
    else:
        path=folder/item["input_file"]
        from PIL import Image
        with Image.open(path) as image:image.verify()
        if not item.get("reviewed"):
            import ocr_headline
            with OCR_LOCK:ocr=ocr_headline.baca(path)
            # Automatic text is offered for review, never silently treated as verified.
            return {"status":"needs_review","ocr":ocr,"headline":ocr.get("headline",""),"supporting":ocr.get("pendukung","")}
        handle=path.open("rb")
        data.update(gambar=FileStorage(handle,filename=item["name"]),headline=item["headline"],supporting=item.get("supporting",""))
    try:
        with app.test_request_context("/api/analisis",method="POST",data=data):
            with MODEL_LOCK:response=app.make_response(analyse_core(batch=True))
        result=response.get_json()
        if response.status_code!=200:raise ValueError(result.get("error","analisis gagal"))
        assets=folder/"assets";assets.mkdir(exist_ok=True)
        def preserve(url):
            if not url:return url
            if url.startswith("/api/heatmap/"):
                name=url.rsplit("/",1)[1]+".png";source=CACHE/name
            elif url.startswith("/api/unggahan/"):
                name=url.rsplit("/",1)[1]+"_src.png";source=CACHE/name
            else:return url
            shutil.copy2(source,assets/name)
            return f"/api/batch/{job['id']}/assets/{name}"
        for key in ("heatmap_url","heatmap_padu_url","gambar_url"):result[key]=preserve(result.get(key))
        for v in result["heatmap_per_task"].values():v["url"]=preserve(v["url"])
        return {"status":"success","result":result}
    finally:
        if handle:handle.close()

from batch_jobs import BatchJobs
JOBS=BatchJobs(HERE/"_jobs",batch_runner)
app.config["MAX_CONTENT_LENGTH"]=200*1024*1024

@app.route("/api/batch",methods=["POST"])
def batch_create():
    task=request.form.get("task","task2_domain_sumber")
    if task not in TASKS:return jsonify(error="task tidak sah"),400
    try:ids=json.loads(request.form.get("sample_ids","[]"))
    except ValueError:return jsonify(error="sample_ids harus JSON list"),400
    if not isinstance(ids,list) or not all(isinstance(x,str) for x in ids):return jsonify(error="sample_ids harus list string"),400
    files=request.files.getlist("gambar")
    if not 0<len(ids)+len(files)<=740:return jsonify(error="Pilih 1–740 sampul"),400
    method=request.form.get("metode_atribusi","occlusion")
    if method not in ("lime","occlusion"):return jsonify(error="metode tidak sah"),400
    items=[{"name":x,"sample_id":x,"status":"queued"} for x in ids]
    job=JOBS.create(items,task,method);folder=JOBS.root/job["id"]
    for index,f in enumerate(files):
        name=f"input_{index}.bin";f.save(folder/name)
        job["items"].append({"name":f.filename,"input_file":name,"status":"queued"})
    JOBS.save(job);JOBS.start(job["id"])
    return jsonify(id=job["id"]),202

@app.route("/api/batch/<id>")
def batch_status(id):
    try:
        with JOBS.lock:j=JOBS.get(id)
    except (OSError,ValueError):return jsonify(error="job tidak ditemukan"),404
    counts={k:sum(x["status"]==k for x in j["items"]) for k in ("queued","running","success","failed","needs_review")}
    j["progress"]={"total":len(j["items"]),**counts};return jsonify(j)

@app.route("/api/batch/<id>/review/<int:index>",methods=["POST"])
def batch_review(id,index):
    try:JOBS.review(id,index,request.form.get("headline",""),request.form.get("supporting",""))
    except (ValueError,OSError,IndexError) as e:return jsonify(error=str(e)),400
    return jsonify(id=id),202

@app.route("/api/batch/<id>/resume",methods=["POST"])
def batch_resume(id):
    try:JOBS.resume(id)
    except (ValueError,OSError) as e:return jsonify(error=str(e)),400
    return jsonify(id=id),202

@app.route("/api/batch/<id>/export/<kind>")
def batch_export(id,kind):
    try:
        with JOBS.lock:j=JOBS.get(id)
    except (ValueError,OSError):return jsonify(error="job tidak ditemukan"),404
    if kind=="json":return Response(json.dumps(j,ensure_ascii=False),mimetype="application/json",headers={"Content-Disposition":f"attachment; filename={id}.json"})
    if kind=="csv":return Response(JOBS.export_csv(j),mimetype="text/csv; charset=utf-8",headers={"Content-Disposition":f"attachment; filename={id}.csv"})
    return jsonify(error="format tidak dikenal"),400

@app.route("/api/batch/<id>/assets/<name>")
def batch_asset(id,name):
    if not id.isalnum() or not re.fullmatch(r"[A-Za-z0-9_]+\.png",name):return "tidak ditemukan",404
    return send_from_directory(JOBS.root/id/"assets",name)

@app.route("/api/batch/<id>/input/<int:index>")
def batch_input(id,index):
    try:
        with JOBS.lock:item=JOBS.get(id)["items"][index]
        name=item["input_file"]
        if Path(name).name != name:return "tidak ditemukan",404
        return send_from_directory(JOBS.root/id,name)
    except (ValueError,OSError,IndexError,KeyError):return "tidak ditemukan",404


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=7860, debug=False)
