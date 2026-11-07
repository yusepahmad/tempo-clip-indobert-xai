"""Test perbaikan audit backend 6 Okt (B1–B16, docs/plans/2026-10-06-audit-bug-kode.md).

Mengimpor app.py (memuat dataset dan melatih head MTL; beberapa test menjalankan
analisis nyata dengan CLIP/IndoBERT di CPU, ~10–20 detik per analisis).
Folder cache/job dialihkan ke folder sementara lewat TEMPO_CACHE_DIR /
TEMPO_JOBS_DIR, sehingga _cache/_jobs milik server yang hidup tidak disentuh.

Jalankan: cd 01_notebook && ../venv/bin/python -m unittest test_audit_backend -v
"""
import io, json, os, re, socket, subprocess, sys, tempfile, textwrap, threading, time, unittest
from pathlib import Path

DEMO = Path(__file__).resolve().parents[1] / "02_web_demo"
sys.path.insert(0, str(DEMO))
_TMP = tempfile.TemporaryDirectory(prefix="tempo_audit_be_")
os.environ["TEMPO_CACHE_DIR"] = str(Path(_TMP.name) / "cache")
os.environ["TEMPO_JOBS_DIR"] = str(Path(_TMP.name) / "jobs")
Path(os.environ["TEMPO_CACHE_DIR"]).mkdir()

import numpy as np
from PIL import Image
import app as A
import ocr_headline
from batch_jobs import AntreanPenuh, BatchJobs, JobTidakDitemukan, pesan_gagal

GAMBAR = DEMO.parent / "05_gambar"
SAMPLE_SUPPORTING_NAN = "TMP-DB65F6B7A1E4"   # supporting_text_verified NaN
SAMPLE_CATATAN_NAN = "TMP-4650B47F4E32"      # task2_source_description/mapping_note NaN


def png(w, h, warna="white"):
    buf = io.BytesIO(); Image.new("RGB", (w, h), warna).save(buf, "PNG"); return buf.getvalue()


def tunggu(jobs, id, batas=60):
    t = time.time()
    while id in jobs.active and time.time() - t < batas:
        time.sleep(.02)


def sisi(p):
    with Image.open(p) as im:
        return im.size


def tanpa_path_server(teks):
    return "/home/" not in teks and str(DEMO) not in teks and _TMP.name not in teks


class Dasar(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c = A.app.test_client()


class B1KunciModel(unittest.TestCase):
    def test_unggahan_lambat_tidak_memegang_model_lock(self):
        from werkzeug.serving import make_server
        srv = make_server("127.0.0.1", 0, A.app, threaded=True)
        th = threading.Thread(target=srv.serve_forever, daemon=True); th.start()
        s = socket.create_connection(("127.0.0.1", srv.server_port))
        try:
            kepala = (b"--zz\r\nContent-Disposition: form-data; name=\"gambar\"; filename=\"a.png\"\r\n"
                      b"Content-Type: image/png\r\n\r\n")
            s.sendall(b"POST /api/analisis HTTP/1.1\r\nHost: x\r\nContent-Type: multipart/form-data; boundary=zz\r\n"
                      b"Content-Length: 100000\r\n\r\n" + kepala)
            time.sleep(.5)   # request sedang membaca body yang tidak kunjung lengkap
            dapat = A.MODEL_LOCK.acquire(timeout=1.5)
            self.assertTrue(dapat, "MODEL_LOCK dipegang selama body unggahan dibaca")
            A.MODEL_LOCK.release()
        finally:
            s.close(); srv.shutdown()


class B2Gambar(Dasar):
    def test_tolak_dimensi_dan_rasio_ekstrem(self):
        for w, h in [(1, 16000), (16000, 1), (8001, 7000), (100, 501), (7000, 6000)]:
            with self.assertRaises(A.InputTidakSah, msg=(w, h)):
                A.baca_gambar(png(w, h))
        with self.assertRaises(A.InputTidakSah):
            A.baca_gambar(b"")
        with self.assertRaises(A.InputTidakSah):
            A.baca_gambar(b"bukan gambar")
        self.assertEqual(A.baca_gambar(png(100, 500)).size, (100, 500))   # rasio 5:1 tepat masih boleh

    def test_perkecil_ke_2000_dan_gambar_kecil_tidak_berubah(self):
        self.assertEqual(max(A.baca_gambar(png(3000, 4000)).size), 2000)
        semua = sorted(GAMBAR.glob("*.jpg"), key=lambda p: max(sisi(p)))
        for kecil in (semua[0], semua[len(semua) // 2]):   # 600–1200 px: piksel identik
            im = A.baca_gambar(kecil.read_bytes())
            with Image.open(kecil) as f:
                asli = f.convert("RGB")
            self.assertLessEqual(max(asli.size), 2000)
            self.assertEqual(im.size, asli.size)
            self.assertTrue(np.array_equal(np.asarray(im), np.asarray(asli)))

    def test_endpoint_menolak_gambar_ekstrem_dengan_json(self):
        for url in ("/api/analisis", "/api/ocr"):
            for ukuran, pesan in (((1, 16000), "sisi maksimal 8000"), ((1, 4000), "tidak wajar")):
                t = time.time()
                r = self.c.post(url, data={"headline": "JUDUL", "gambar": (io.BytesIO(png(*ukuran)), "a.png")})
                self.assertEqual(r.status_code, 400, url)
                self.assertIn(pesan, r.get_json()["error"])
                self.assertLess(time.time() - t, 3)


class B3Batas(Dasar):
    def test_panjang_teks(self):
        r = self.c.post("/api/analisis", data={"sample_id": SAMPLE_CATATAN_NAN, "headline": "A" * 301})
        self.assertEqual(r.status_code, 400); self.assertIn("headline terlalu panjang", r.get_json()["error"])
        r = self.c.post("/api/analisis", data={"sample_id": SAMPLE_CATATAN_NAN, "supporting": "B" * 2001})
        self.assertEqual(r.status_code, 400); self.assertIn("pendukung terlalu panjang", r.get_json()["error"])
        r = self.c.post("/api/analisis", data={"headline": "A " * 200, "gambar": (io.BytesIO(png(10, 10)), "a.png")})
        self.assertEqual(r.status_code, 400)
        r = self.c.post("/api/batch/" + "a" * 32 + "/review/0", data={"headline": "A" * 301})
        self.assertEqual(r.status_code, 400)

    def test_batas_unggah_per_endpoint(self):
        besar = b"\0" * (A.BATAS_UNGGAH + 1024)
        for url in ("/api/analisis", "/api/ocr"):
            r = self.c.post(url, data={"headline": "X", "gambar": (io.BytesIO(besar), "a.png")})
            self.assertEqual(r.status_code, 413, url)
            self.assertIn("maksimal 25 MB", r.get_json()["error"])
        # batch boleh lebih besar dari batas analisis tunggal; berkas rusak gagal per item
        lama = A.JOBS.runner
        A.JOBS.runner = lambda j, x, f: {"status": "success", "result": {}}
        try:
            r = self.c.post("/api/batch", data={"sample_ids": "[]", "gambar": (io.BytesIO(besar), "besar.bin")})
            self.assertEqual(r.status_code, 202, r.get_data(as_text=True))
            tunggu(A.JOBS, r.get_json()["id"])
        finally:
            A.JOBS.runner = lama

    def test_batas_job_aktif(self):
        lepas = threading.Event()
        lama = A.JOBS.runner
        A.JOBS.runner = lambda j, x, f: (lepas.wait(20), {"status": "success", "result": {}})[1]
        ids = []
        try:
            for _ in range(2):
                r = self.c.post("/api/batch", data={"sample_ids": json.dumps([SAMPLE_CATATAN_NAN])})
                self.assertEqual(r.status_code, 202); ids.append(r.get_json()["id"])
            r = self.c.post("/api/batch", data={"sample_ids": json.dumps([SAMPLE_CATATAN_NAN])})
            self.assertEqual(r.status_code, 429)
            self.assertIn("maksimal 2", r.get_json()["error"])
        finally:
            lepas.set()
            for i in ids: tunggu(A.JOBS, i)
            A.JOBS.runner = lama


class B4Path(Dasar):
    def test_job_tidak_ada_404_tanpa_path(self):
        for metode, url in [("post", "/api/batch/deadbeef/resume"), ("post", "/api/batch/deadbeef/review/0"),
                            ("post", "/api/batch/" + "0" * 32 + "/resume"), ("get", "/api/batch/" + "0" * 32),
                            ("get", "/api/batch/deadbeef/export/csv"), ("get", "/api/batch/deadbeef/assets/a.png"),
                            ("get", "/api/batch/deadbeef/input/0")]:
            r = getattr(self.c, metode)(url, data={"headline": "X"} if metode == "post" else None)
            self.assertEqual(r.status_code, 404, url)
            self.assertEqual(r.get_json()["error"], "job tidak ditemukan", url)
            self.assertTrue(tanpa_path_server(r.get_data(as_text=True)), url)

    def test_review_indeks_di_luar_rentang_404(self):
        j = A.JOBS.create([{"name": "x", "status": "needs_review", "input_file": "input_0.png"}], "task1_issue", "occlusion")
        j["status"] = "needs_review"; A.JOBS.save(j)
        r = self.c.post(f"/api/batch/{j['id']}/review/5", data={"headline": "X"})
        self.assertEqual(r.status_code, 404); self.assertEqual(r.get_json()["error"], "item tidak ditemukan")

    def test_catatan_ocr_disaring(self):
        lama = ocr_headline.baca
        ocr_headline.baca = lambda p: {"tersedia": False, "headline": "", "pendukung": "", "semua": [],
                                       "catatan": f"OCR gagal membaca gambar: FileNotFoundError: '{p}'"}
        try:
            r = self.c.post("/api/ocr", data={"gambar": (io.BytesIO(png(40, 60)), "a.png")})
            self.assertEqual(r.status_code, 200)
            self.assertTrue(tanpa_path_server(r.get_json()["catatan"]), r.get_json()["catatan"])
            with tempfile.TemporaryDirectory() as d:
                (Path(d) / "input_0.bin").write_bytes(png(40, 60))
                hasil = A.batch_runner({"id": "x", "task": "task1_issue", "method": "occlusion"},
                                       {"name": "a.png", "input_file": "input_0.bin", "status": "running"}, Path(d))
                self.assertEqual(hasil["status"], "needs_review")
                self.assertTrue(tanpa_path_server(hasil["ocr"]["catatan"]), hasil["ocr"]["catatan"])
                self.assertNotIn(d, hasil["ocr"]["catatan"])
                # berkas mentah dinormalisasi menjadi PNG tervalidasi
                self.assertEqual(hasil["input_file"], "input_0.png")
                self.assertTrue((Path(d) / "input_0.png").exists())
        finally:
            ocr_headline.baca = lama


class B5NaN(Dasar):
    def test_helper_dan_masukan_dataset(self):
        self.assertEqual(A._teks(float("nan")), ""); self.assertEqual(A._teks(None), ""); self.assertEqual(A._teks("ab"), "ab")
        m = A.siapkan_masukan({"sample_id": SAMPLE_SUPPORTING_NAN}, None, batch=True)
        self.assertEqual(m["supporting"], ""); self.assertFalse(m["teks_berubah"])
        # frontend mengirim "" untuk supporting NaN: fitur pra-hitung tetap dipakai
        r = self.c.get("/api/samples").get_json()
        s = next(x for x in r if x["sample_id"] == SAMPLE_SUPPORTING_NAN)
        m = A.siapkan_masukan({"sample_id": SAMPLE_SUPPORTING_NAN, "headline": s["headline"], "supporting": s["supporting"]}, None)
        self.assertFalse(m["teks_berubah"])

    def test_analisis_dataset_catatan_tanpa_nan(self):
        r = self.c.post("/api/analisis", data={"sample_id": SAMPLE_CATATAN_NAN, "metode_atribusi": "occlusion"})
        self.assertEqual(r.status_code, 200, r.get_data(as_text=True)[:300])
        d = r.get_json()
        self.assertEqual(d["catatan_anotator"]["sumber_metafora"], "")
        self.assertEqual(d["catatan_anotator"]["pemetaan_makna"], "")
        self.assertNotIn("nan", json.dumps(d["catatan_anotator"]).lower())
        self.assertEqual(d["mode"], "dataset (leave-one-out)")
        for k in ("ringkasan", "kesimpulan", "penjelasan", "heatmap_url", "heatmap_padu_url", "heatmap_per_task", "verifikasi"):
            self.assertIn(k, d)
        g = self.c.get(d["heatmap_padu_url"]); self.assertEqual(g.status_code, 200); g.close()


class B6Keluar(unittest.TestCase):
    def test_proses_tidak_menunggu_job_batch(self):
        skrip = textwrap.dedent(f"""
            import sys, time, tempfile; sys.path.insert(0, {str(DEMO)!r})
            from batch_jobs import BatchJobs
            J = BatchJobs(tempfile.mkdtemp(), lambda j, x, f: (time.sleep(3), {{"status": "success"}})[1])
            j = J.create([{{"name": str(i), "status": "queued"}} for i in range(5)], "t", "occlusion"); J.start(j["id"])
            time.sleep(.3)
        """)
        t = time.time(); subprocess.run([sys.executable, "-c", skrip], check=True, timeout=30)
        self.assertLess(time.time() - t, 6, "proses menunggu seluruh job batch (5x3 detik) sebelum keluar")

    def test_restart_menandai_interrupted(self):
        with tempfile.TemporaryDirectory() as d:
            J = BatchJobs(d, lambda *a: {})
            j = J.create([{"name": "a", "status": "running"}], "t", "occlusion"); j["status"] = "running"; J.save(j)
            J2 = BatchJobs(d, lambda *a: {})
            self.assertEqual(J2.get(j["id"])["status"], "interrupted")
            self.assertEqual(J2.get(j["id"])["items"][0]["status"], "queued")
            J.pool.shutdown(); J2.pool.shutdown()


class B7AntreUlang(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory(); self.n = 0
    def tearDown(self):
        self.dir.cleanup()

    def test_resume_membersihkan_error_lama(self):
        def runner(j, x, f):
            self.n += 1
            if self.n == 1: raise RuntimeError("timeout sementara")
            return {"status": "success", "result": {"headline": "H"}}
        J = BatchJobs(self.dir.name, runner)
        j = J.create([{"name": "a", "status": "queued"}], "t", "occlusion"); J.start(j["id"]); tunggu(J, j["id"])
        self.assertEqual(J.get(j["id"])["status"], "failed")
        J.resume(j["id"]); tunggu(J, j["id"])
        x = J.get(j["id"])["items"][0]
        self.assertEqual(x["status"], "success"); self.assertNotIn("error", x)
        self.assertNotIn("timeout", J.export_csv(J.get(j["id"])))
        J.pool.shutdown()

    def test_review_membersihkan_result_lama(self):
        def runner(j, x, f):
            if not x.get("reviewed"): return {"status": "needs_review", "headline": "OCR"}
            raise RuntimeError("gagal kedua")
        J = BatchJobs(self.dir.name, runner)
        j = J.create([{"name": "b", "status": "queued", "input_file": "input_0.png", "result": {"headline": "LAMA"}}], "t", "occlusion")
        J.start(j["id"]); tunggu(J, j["id"])
        J.review(j["id"], 0, "BARU", ""); tunggu(J, j["id"])
        x = J.get(j["id"])["items"][0]
        self.assertEqual(x["status"], "failed"); self.assertNotIn("result", x)
        self.assertNotIn("LAMA", J.export_csv(J.get(j["id"])))
        # unggahan yang gagal boleh ditinjau ulang
        J.review(j["id"], 0, "LAGI", ""); tunggu(J, j["id"])
        J.pool.shutdown()

    def test_review_hanya_untuk_item_yang_perlu(self):
        J = BatchJobs(self.dir.name, lambda *a: {"status": "success", "result": {}})
        j = J.create([{"name": "TMP", "sample_id": "TMP", "status": "success"},
                      {"name": "TMP2", "sample_id": "TMP2", "status": "failed"}], "t", "occlusion")
        for i in (0, 1):
            with self.assertRaisesRegex(ValueError, "tidak perlu ditinjau"):
                J.review(j["id"], i, "KOREKSI", "")
        with self.assertRaises(IndexError):
            J.review(j["id"], 9, "KOREKSI", "")
        with self.assertRaises(JobTidakDitemukan):
            J.review("0" * 32, 0, "KOREKSI", "")
        J.pool.shutdown()

    def test_status_job_queued_saat_resume_dan_review(self):
        lepas = threading.Event()
        J = BatchJobs(self.dir.name, lambda j, x, f: (lepas.wait(10), {"status": "needs_review"} if not x.get("reviewed") else {"status": "success", "result": {}})[1])
        a = J.create([{"name": "a", "status": "queued"}], "t", "occlusion")
        b = J.create([{"name": "b", "status": "failed"}], "t", "occlusion"); jb = J.get(b["id"]); jb["status"] = "interrupted"; J.save(jb)
        c = J.create([{"name": "c", "status": "needs_review", "input_file": "input_0.png"}], "t", "occlusion"); jc = J.get(c["id"]); jc["status"] = "needs_review"; J.save(jc)
        J.start(a["id"]); time.sleep(.1)
        J.resume(b["id"]); self.assertEqual(J.get(b["id"])["status"], "queued")
        J.review(c["id"], 0, "JUDUL", ""); self.assertEqual(J.get(c["id"])["status"], "queued")
        lepas.set()
        for i in (a, b, c): tunggu(J, i["id"])
        J.pool.shutdown()

    def test_kapasitas(self):
        lepas = threading.Event()
        J = BatchJobs(self.dir.name, lambda *a: (lepas.wait(10), {"status": "success", "result": {}})[1], max_aktif=1)
        a = J.create([{"name": "a", "status": "queued"}], "t", "occlusion"); J.start(a["id"])
        b = J.create([{"name": "b", "status": "failed"}], "t", "occlusion")
        with self.assertRaises(AntreanPenuh): J.cek_kapasitas()
        with self.assertRaises(AntreanPenuh): J.resume(b["id"])
        self.assertEqual(J.get(b["id"])["items"][0]["status"], "failed")   # tidak diubah bila ditolak
        lepas.set(); tunggu(J, a["id"]); J.pool.shutdown()


class B8Cache(unittest.TestCase):
    def test_bersihkan_per_analisis(self):
        sekarang = time.time()
        with tempfile.TemporaryDirectory() as d:
            lama_cache = A.CACHE; A.CACHE = Path(d)
            try:
                def buat(hexid, umur, berkas=("cam_{h}.png", "cam_{h}_padu.png", "cam_{h}_task1_issue.png", "upload_{h}_src.png")):
                    for pola in berkas:
                        p = Path(d) / pola.format(h=hexid); p.write_bytes(b"x"); os.utime(p, (sekarang - umur,) * 2)
                ids = [f"{i:032x}" for i in range(6)]
                for i, h in enumerate(ids): buat(h, umur=i * 60)           # 0..5 menit
                os.utime(Path(d) / f"cam_{ids[1]}_padu.png", (sekarang - 3 * 3600,) * 2)  # satu berkas tua dalam grup baru
                tua = f"{99:032x}"; buat(tua, umur=3 * 3600)
                (Path(d) / "ocr_1759700000000_src.png").write_bytes(b"x"); os.utime(Path(d) / "ocr_1759700000000_src.png", (sekarang - 3 * 3600,) * 2)
                A.bersihkan_cache(batas=4, sekarang=sekarang)
                sisa = {p.name for p in Path(d).iterdir()}
                for h in ids[:4]:
                    self.assertEqual(sum(h in n for n in sisa), 4, f"grup {h} harus utuh")
                for h in ids[4:] + [tua]:
                    self.assertFalse(any(h in n for n in sisa), f"grup {h} harus terhapus seluruhnya")
                self.assertNotIn("ocr_1759700000000_src.png", sisa)
            finally:
                A.CACHE = lama_cache


class B9CSV(unittest.TestCase):
    def test_formula(self):
        nama = ["=1+1", "\t=1+1", "\r=1+1", " =HYPERLINK(\"x\")", "＝1+1", "-2+3", "@SUM(A1)", "\tbiasa", "Judul biasa"]
        jj = {"task": "t", "items": [{"name": n, "status": "failed"} for n in nama]}
        import csv
        rows = list(csv.reader(io.StringIO(BatchJobs.export_csv(None, jj))))[1:]
        for n, row in zip(nama, rows):
            if n == "Judul biasa": self.assertEqual(row[0], n)
            else: self.assertTrue(row[0].startswith("'"), repr(row[0]))


class B10Validasi(Dasar):
    def test_sample_id_tak_dikenal_ditolak(self):
        r = self.c.post("/api/batch", data={"sample_ids": json.dumps([SAMPLE_CATATAN_NAN, "TIDAK-ADA", "../../x"])})
        self.assertEqual(r.status_code, 400)
        d = r.get_json(); self.assertIn("TIDAK-ADA", d["error"]); self.assertEqual(d["sample_ids_tidak_dikenal"], ["TIDAK-ADA", "../../x"])

    def test_status_failed_bila_semua_gagal(self):
        with tempfile.TemporaryDirectory() as d:
            def gagal(*a): raise ValueError("x")
            J = BatchJobs(d, gagal)
            j = J.create([{"name": "a", "status": "queued"}, {"name": "b", "status": "queued"}], "t", "occlusion")
            J.start(j["id"]); tunggu(J, j["id"])
            self.assertEqual(J.get(j["id"])["status"], "failed")
            J2 = BatchJobs(Path(d) / "lain", lambda j, x, f: {"status": "success", "result": {}} if x["name"] == "a" else gagal())
            j = J2.create([{"name": "a", "status": "queued"}, {"name": "b", "status": "queued"}], "t", "occlusion")
            J2.start(j["id"]); tunggu(J2, j["id"])
            self.assertEqual(J2.get(j["id"])["status"], "complete")
            J.pool.shutdown(); J2.pool.shutdown()


class B11ErrorJSON(Dasar):
    def test_404_dan_500_json(self):
        r = self.c.get("/api/tidak-ada")
        self.assertEqual(r.status_code, 404); self.assertEqual(r.get_json()["error"], "tidak ditemukan")
        lama = A.catalog
        A.catalog = lambda *a: 1 / 0
        try:
            r = self.c.get("/api/catalog")
            self.assertEqual(r.status_code, 500); self.assertIn("kesalahan di server", r.get_json()["error"])
            self.assertNotIn("ZeroDivision", r.get_data(as_text=True))
        finally:
            A.catalog = lama
        self.assertEqual(self.c.get("/").status_code, 200)


class B12Metode(Dasar):
    def test_metode_tak_sah(self):
        r = self.c.post("/api/analisis", data={"sample_id": SAMPLE_CATATAN_NAN, "metode_atribusi": "foo"})
        self.assertEqual(r.status_code, 400); self.assertIn("metode_atribusi tidak sah", r.get_json()["error"])
        self.assertEqual(A.siapkan_masukan({"sample_id": SAMPLE_CATATAN_NAN, "metode_atribusi": " OCCLUSION "}, None)["metode"], "occlusion")
        self.assertEqual(A.siapkan_masukan({"sample_id": SAMPLE_CATATAN_NAN}, None)["metode"], "lime")
        self.assertEqual(A.siapkan_masukan({"sample_id": SAMPLE_CATATAN_NAN}, None, batch=True)["metode"], "occlusion")


class B13NamaOCR(Dasar):
    def test_nama_berkas_uuid_dan_dihapus(self):
        dilihat = []
        lama = ocr_headline.baca
        ocr_headline.baca = lambda p: (dilihat.append(Path(p)), {"tersedia": True, "headline": "H", "pendukung": "", "semua": [], "catatan": ""})[1]
        try:
            self.assertEqual(self.c.post("/api/ocr", data={"gambar": (io.BytesIO(png(40, 60)), "a.png")}).status_code, 200)
        finally:
            ocr_headline.baca = lama
        self.assertRegex(dilihat[0].name, r"^ocr_[0-9a-f]{32}_src\.png$")
        self.assertFalse(dilihat[0].exists())


class B14InSampleDanAsetBatch(unittest.TestCase):
    def test_ringkasan_batch_dataset(self):
        with tempfile.TemporaryDirectory() as d:
            hasil = A.batch_runner({"id": "f" * 32, "task": "task2_domain_sumber", "method": "occlusion"},
                                   {"name": SAMPLE_CATATAN_NAN, "sample_id": SAMPLE_CATATAN_NAN, "status": "running"}, Path(d))
            r = hasil["result"]
            self.assertEqual(r["mode"], "dataset batch (eksplorasi, in-sample)")
            self.assertIn("bukan ukuran akurasi", r["ringkasan"]["paragraf"])
            self.assertIn("bukan ukuran akurasi", r["ringkasan"]["bagian"][-1]["teks"])
            # aset dipindah ke folder job, tidak tertinggal di cache interaktif
            self.assertTrue(r["heatmap_padu_url"].startswith("/api/batch/"))
            nama = r["heatmap_padu_url"].rsplit("/", 1)[1]
            self.assertTrue((Path(d) / "assets" / nama).exists())
            self.assertFalse((A.CACHE / nama).exists())

    def test_analisis_unggahan_diperkecil(self):
        besar = next(p for p in sorted(GAMBAR.glob("*.jpg")) if max(sisi(p)) > 2000)
        c = A.app.test_client()
        r = c.post("/api/analisis", data={"headline": "JUDUL UJI", "metode_atribusi": "occlusion",
                                          "gambar": (io.BytesIO(besar.read_bytes()), besar.name)})
        self.assertEqual(r.status_code, 200, r.get_data(as_text=True)[:300])
        d = r.get_json()
        self.assertEqual(d["mode"], "unggahan (tanpa label pembanding)")
        self.assertIsNone(d["label_anotator"])
        g = c.get(d["gambar_url"]); self.assertEqual(g.status_code, 200)
        self.assertEqual(max(sisi(io.BytesIO(g.data))), 2000); g.close()
        # berkas unggahan dan peta panas berbagi analysis_id (dibersihkan bersama)
        self.assertIn(d["analysis_id"], d["gambar_url"]); self.assertIn(d["analysis_id"], d["heatmap_padu_url"])


class B16Gambar(Dasar):
    def test_hanya_sample_id_dataset(self):
        self.assertEqual(self.c.get(f"/api/image/{SAMPLE_CATATAN_NAN}").status_code, 200)
        for s in ("..%5c..%5c03_data%5cx", "TIDAK-ADA", "%00"):
            r = self.c.get("/api/image/" + s)
            self.assertEqual(r.status_code, 404, s); self.assertEqual(r.get_json()["error"], "gambar tidak ditemukan")


class PesanGagal(unittest.TestCase):
    def test_input_tidak_sah_tanpa_awalan_tipe(self):
        self.assertEqual(pesan_gagal(A.InputTidakSah("sample_id tidak ditemukan")), "sample_id tidak ditemukan")


class F2Pembatalan(Dasar):
    """Analisis yang dibatalkan klien dilewati server (plan 2026-10-06-audit-bug-kode, F2)."""
    def test_batal_sebelum_dijalankan(self):
        sid = A.ENG.df["sample_id"].iloc[0]
        self.assertEqual(self.c.post("/api/analisis/batal", data={"req_id": "abc12345"}).status_code, 200)
        t = time.time()
        r = self.c.post("/api/analisis", data={"sample_id": sid, "req_id": "abc12345", "metode_atribusi": "occlusion"})
        self.assertEqual(r.status_code, 409)
        self.assertIn("dibatalkan", r.get_json()["error"])
        self.assertLess(time.time() - t, 2.0)

    def test_req_id_tidak_sah(self):
        self.assertEqual(self.c.post("/api/analisis/batal", data={"req_id": "../x"}).status_code, 400)

    def test_tanpa_pembatalan_tetap_jalan(self):
        sid = A.ENG.df["sample_id"].iloc[0]
        r = self.c.post("/api/analisis", data={"sample_id": sid, "req_id": "def67890", "metode_atribusi": "occlusion"})
        self.assertEqual(r.status_code, 200)


if __name__ == "__main__":
    unittest.main()
