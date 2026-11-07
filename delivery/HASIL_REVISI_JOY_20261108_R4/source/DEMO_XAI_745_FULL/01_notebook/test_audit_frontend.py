"""Regresi perbaikan audit frontend F1, F3, F4, F6–F12 (plan docs/plans/2026-10-06-audit-bug-kode.md).

Browser headless (Playwright/Chromium) terhadap server demo yang sedang hidup:
    TEMPO_DEMO_URL=http://127.0.0.1:7861 venv/bin/python 01_notebook/test_audit_frontend.py
Endpoint berat (/api/ocr, /api/analisis, /api/batch*) SELALU di-mock lewat page.route,
jadi test ini tidak menjalankan model. Hanya halaman, /api/samples, /api/catalog dan
gambar dataset yang diambil dari server. Panggilan berat yang lolos dari mock dicatat
dan menggagalkan test.
"""
import json, os, re, sys, unittest
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE = os.environ.get("TEMPO_DEMO_URL", "http://127.0.0.1:7861")
FOTO = sorted((Path(__file__).resolve().parents[1] / "06_gambar_revisi").glob("*.jpeg"))
PNG = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
XSS = '<img src=x data-xss=1 onerror="window.__xss=(window.__xss||0)+1">'
TASKS = ["task1_issue", "task2_domain_sumber", "task3_primary_entity_type"]


def hasil_palsu(teks=""):
    """Respons /api/analisis minimal; `teks` disisipkan ke setiap field string yang dirender."""
    t = teks
    pred = {k: {"probabilitas": 0.5, "nama_task": k + t, "nama_task_mudah": "Task " + k + t,
                "prediksi": "KELAS_" + k + t, "prediksi_tampil": "Kelas " + k + t,
                "semua": [{"kelas": "A", "prob": 0.5}, {"kelas": "B" + t, "kelas_tampil": "Kelas B" + t, "prob": 0.3}]}
            for k in TASKS}
    return {
        "analysis_id": "id" + t, "snapshot": {"model": "model" + t}, "mode": "dataset (leave-one-out)" + t,
        "task_xai": "Domain sumber" + t, "durasi_detik": 1.0, "headline": "JUDUL" + t, "supporting": "pendukung" + t,
        "prediksi": pred, "gambar_url": PNG, "heatmap_url": PNG, "heatmap_padu_url": PNG,
        "heatmap_per_task": {k: {"url": PNG, "nama_task": "nama " + k + t} for k in TASKS},
        "catatan_anotator": {"sumber_metafora": "sumber" + t, "pemetaan_makna": "makna" + t, "entitas": "entitas" + t},
        "verifikasi": {k: {"cocok": True} for k in TASKS},
        "atribusi_kata": [{"kata": "kata" + t, "kontribusi": 0.2}, {"kata": "lain", "kontribusi": -0.1}],
        "kelas_untuk_atribusi": "K" + t, "kelas_untuk_atribusi_tampil": "Kelas K" + t, "prob_kelas_atribusi": 0.5,
        "metode_atribusi": "occlusion", "evidence": {"x": t},
        "penjelasan": [{"asal": "model", "label": "Label" + t, "teks": "teks" + t}],
        "kesimpulan": {"cek": ["cek" + t]},
        "ringkasan": {"bagian": [{"asal": "model", "teks": "ringkas" + t}, {"asal": "anotator", "teks": "b" + t}],
                      "keyakinan": "tinggi", "tanda": "tanda" + t},
    }


def ocr_ok(headline="JUDUL OCR", kandidat=None, catatan=""):
    return {"tersedia": True, "headline": headline, "pendukung": "pendukung ocr", "keyakinan": 0.9,
            "catatan": catatan, "kandidat_headline": kandidat or [headline, "KANDIDAT DUA"]}


def item_review(i):
    return {"name": f"foto{i}.jpg", "input_file": f"input_{i}.bin", "status": "needs_review",
            "headline": f"OCR {i}", "supporting": "", "ocr": {"kandidat_headline": [f"OCR {i}", f"ALT {i}"]}}


class AuditFrontend(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pw = sync_playwright().start()
        cls.browser = cls.pw.chromium.launch()

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.pw.stop()

    def setUp(self):
        self.lolos = []      # panggilan berat yang tidak di-mock
        self.dialogs = []
        self.ctx = None

    def tearDown(self):
        if self.ctx:
            self.ctx.close()
        self.assertEqual(self.lolos, [], "endpoint berat terpanggil tanpa mock")

    def buka(self, width=1280, height=900, hash_="", mobile=False):
        self.ctx = self.browser.new_context(viewport={"width": width, "height": height},
                                            is_mobile=mobile, has_touch=mobile)
        for pola in ("**/api/ocr", "**/api/analisis", "**/api/batch", "**/api/batch/**"):
            self.ctx.route(pola, lambda r: (self.lolos.append(r.request.url), r.abort()))
        page = self.ctx.new_page()
        page.on("dialog", lambda d: (self.dialogs.append(d.message), d.accept()))
        return page

    def muat(self, page, hash_=""):
        page.goto(BASE + "/" + hash_)
        page.wait_for_function("document.getElementById('sample').options.length>1")

    def tunggu_siap(self, page):
        page.wait_for_function("document.getElementById('workspace').dataset.state!=='ocr'")

    def unggah(self, page, ocr):
        page.route("**/api/ocr", lambda r: r.fulfill(**ocr) if "status" in ocr else r.fulfill(json=ocr))
        page.click("#tabUnggah")
        page.set_input_files("#gambar", str(FOTO[0]))
        self.tunggu_siap(page)

    # ---------------- F1: XSS ----------------
    def test_f1_pesan_ocr_di_escape(self):
        page = self.buka(); self.muat(page)
        self.unggah(page, ocr_ok(catatan="Sebagian baris judul terbaca (" + XSS + ") — periksa ejaannya."))
        self.assertEqual(page.locator("#statusOcr [data-xss]").count(), 0)
        self.assertIn("<img src=x", page.inner_text("#statusOcr"))
        page.unroute("**/api/ocr")
        page.route("**/api/ocr", lambda r: r.fulfill(status=400, json={"tersedia": False, "error": "gagal " + XSS}))
        page.set_input_files("#gambar", str(FOTO[1])); self.tunggu_siap(page)
        self.assertEqual(page.locator("#statusOcr [data-xss]").count(), 0)
        self.assertIn("gagal <img", page.inner_text("#statusOcr"))
        page.unroute("**/api/ocr")
        page.route("**/api/ocr", lambda r: r.fulfill(json={"tersedia": True, "headline": "", "catatan": XSS}))
        page.set_input_files("#gambar", str(FOTO[2])); self.tunggu_siap(page)
        self.assertEqual(page.locator("#statusOcr [data-xss]").count(), 0)
        page.wait_for_timeout(200)
        self.assertIsNone(page.evaluate("window.__xss"))

    def test_f1_hasil_analisis_di_escape(self):
        page = self.buka(); self.muat(page)
        page.route("**/api/analisis", lambda r: r.fulfill(json=hasil_palsu(XSS)))
        page.click("#jalan"); page.wait_for_selector("#hasil", state="visible")
        for tab in ("ringkasan", "visual", "teks", "sumber", "verifikasi"):
            page.click(f"#result-tab-{tab}")
        page.eval_on_selector("#bandingHeat", "d=>d.open=true")
        page.wait_for_timeout(300)
        self.assertEqual(page.locator("#hasil [data-xss]").count(), 0)
        self.assertIsNone(page.evaluate("window.__xss"))
        for sel in ("#ringkas", "#tabelPred", "#kataBox", "#verif", "#verifVisual", "#narasi", "#simpulTeks"):
            self.assertIn("<img src=x", page.inner_text(sel), sel)

    def test_f1_batch_di_escape_dan_url_peta_aman(self):
        page = self.buka()
        job = {"id": "jobx", "status": "complete", "progress": {"total": 2}, "items": [
            {"name": "nama" + XSS, "status": "failed", "error": "err" + XSS},
            {"name": "ok", "status": "success", "result": {"kesimpulan": {"paragraf": "par" + XSS},
                                                          "heatmap_padu_url": "javascript:window.__xss=1"}}]}
        page.route("**/api/batch/jobx", lambda r: r.fulfill(json=job))
        page.add_init_script("localStorage.setItem('tempoBatchId','jobx')")
        self.muat(page, "#batch")
        page.wait_for_function("document.querySelectorAll('#batchResults details').length===2")
        page.eval_on_selector_all("#batchResults details", "ds=>ds.forEach(d=>d.open=true)")
        self.assertEqual(page.locator("#batch [data-xss]").count(), 0)
        self.assertEqual(page.locator("#batchResults a[href^='javascript']").count(), 0)
        self.assertIsNone(page.evaluate("window.__xss"))

    # ---------------- F3: render ulang batch ----------------
    def test_f3_ketikan_dan_details_dipertahankan_tombol_dikunci(self):
        page = self.buka()
        st = {"status": "needs_review", "review": []}
        ditahan = []

        def get(r):
            r.fulfill(json={"id": "job1", "status": st["status"], "progress": {"total": 3},
                            "items": [item_review(0), item_review(1),
                                      {"name": "TMP-A", "status": "success", "result": {"kesimpulan": {"paragraf": "A"}}}]})

        def review(r):
            st["review"].append(r.request.url); ditahan.append(r)
        page.route("**/api/batch/job1", get)
        page.route("**/api/batch/job1/review/*", review)
        page.route("**/api/batch/job1/input/*", lambda r: r.fulfill(status=404, body=""))
        page.add_init_script("localStorage.setItem('tempoBatchId','job1')")
        self.muat(page, "#batch")
        page.wait_for_function("document.querySelectorAll('#batchResults details').length===3")
        det = page.locator("#batchResults > details")
        det.nth(0).locator("summary").click(); det.nth(1).locator("summary").click(); det.nth(2).locator("summary").click()
        page.fill("input[aria-label='Headline final foto1.jpg']", "KOREKSI ITEM 1")
        page.fill("input[aria-label='Teks pendukung final foto1.jpg']", "pendukung 1")
        tombol = det.nth(0).locator("button")
        tombol.click()
        page.wait_for_timeout(200)
        self.assertTrue(tombol.is_disabled()); self.assertIn("Mengirim", tombol.inner_text())
        tombol.click(force=True); page.wait_for_timeout(200)
        self.assertEqual(len(st["review"]), 1, "konfirmasi ganda terkirim")
        ditahan[0].fulfill(status=202, json={"id": "job1"})
        page.wait_for_timeout(600)
        self.assertEqual(page.input_value("input[aria-label='Headline final foto1.jpg']"), "KOREKSI ITEM 1")
        self.assertEqual(page.input_value("input[aria-label='Teks pendukung final foto1.jpg']"), "pendukung 1")
        self.assertEqual(page.eval_on_selector_all("#batchResults > details", "d=>d.map(x=>x.open)"), [True, True, True])
        # Polling saat running: details yang terbuka tidak menutup sendiri.
        st["status"] = "running"; page.evaluate("pollBatch()"); page.wait_for_timeout(3600)
        self.assertEqual(page.eval_on_selector_all("#batchResults > details", "d=>d.map(x=>x.open)"), [True, True, True])
        self.assertTrue(page.is_disabled("input[aria-label='Headline final foto1.jpg']"))
        self.assertEqual(page.input_value("input[aria-label='Headline final foto1.jpg']"), "KOREKSI ITEM 1")
        st["status"] = "complete"; page.wait_for_timeout(3500)

    # ---------------- F4: polling dengan backoff ----------------
    def test_f4_polling_jalan_lagi_setelah_error(self):
        page = self.buka()
        st = {"n": 0}

        def get(r):
            st["n"] += 1
            if st["n"] == 2:
                r.fulfill(status=502, body="<html>Bad gateway</html>", content_type="text/html"); return
            r.fulfill(json={"id": "job2", "status": "running" if st["n"] < 4 else "complete",
                            "progress": {"total": 1}, "items": [{"name": "TMP-A", "status": "running"}]})
        page.route("**/api/batch/job2", get)
        page.add_init_script("localStorage.setItem('tempoBatchId','job2')")
        self.muat(page, "#batch")
        page.wait_for_function("/tidak dapat dihubungi/.test(document.getElementById('batchStatus').textContent)", timeout=8000)
        teks = page.inner_text("#batchStatus")
        self.assertIn("Mencoba lagi", teks); self.assertNotIn("Unexpected token", teks)
        page.wait_for_function("/— complete —/.test(document.getElementById('batchStatus').textContent)", timeout=15000)
        self.assertEqual(st["n"], 4)
        page.wait_for_timeout(3500)
        self.assertEqual(st["n"], 4, "polling harus berhenti setelah complete")

    # ---------------- F6 ----------------
    def test_f6_klik_tab_aktif_tidak_membuang_hasil(self):
        page = self.buka(); self.muat(page)
        page.route("**/api/analisis", lambda r: r.fulfill(json=hasil_palsu()))
        page.click("#jalan"); page.wait_for_selector("#hasil", state="visible")
        page.click("#tabData")
        self.assertTrue(page.is_visible("#hasil"))
        self.assertEqual(page.eval_on_selector("#workspace", "e=>e.dataset.state"), "results")
        page.click("#tabUnggah")
        self.assertTrue(page.is_hidden("#hasil"), "pindah mode tetap membatalkan hasil")

    # ---------------- F7 ----------------
    def test_f7_kandidat_ocr_dibersihkan_dan_bisa_dipilih_ulang(self):
        page = self.buka(); self.muat(page)
        self.unggah(page, ocr_ok("WASWAS RUPIAH", ["WASWAS RUPIAH", "KANDIDAT LAMA"]))
        page.select_option("#ocrCandidates", "KANDIDAT LAMA")
        self.assertEqual(page.input_value("#headline"), "KANDIDAT LAMA")
        self.assertEqual(page.input_value("#ocrCandidates"), "")
        page.fill("#headline", "sunting manual")
        page.select_option("#ocrCandidates", "KANDIDAT LAMA")
        self.assertEqual(page.input_value("#headline"), "KANDIDAT LAMA")
        page.click("#tabData"); page.click("#tabUnggah")
        self.assertEqual(page.eval_on_selector_all("#ocrCandidates option", "o=>o.map(x=>x.value)"), [""])

    # ---------------- F8 ----------------
    def test_f8_batch_id_usang_dihapus(self):
        page = self.buka()
        page.route("**/api/batch/deadbeef00", lambda r: r.fulfill(status=404, json={"error": "job tidak ditemukan"}))
        page.add_init_script("if(!sessionStorage.getItem('sekali')){sessionStorage.setItem('sekali','1');localStorage.setItem('tempoBatchId','deadbeef00');}")
        self.muat(page, "#batch")
        page.wait_for_function("/tidak ada di server/.test(document.getElementById('batchStatus').textContent)")
        self.assertIsNone(page.evaluate("localStorage.getItem('tempoBatchId')"))
        self.assertTrue(page.is_disabled("#batchResume"))
        page.reload(); page.wait_for_timeout(600)
        self.assertEqual(page.inner_text("#batchStatus"), "")

    # ---------------- F9 ----------------
    def test_f9_mulai_batch_dikunci(self):
        page = self.buka()
        posts, ditahan, st = [], [], {"status": "running"}

        def batch(r):
            if r.request.method == "POST":
                posts.append(r.request.post_data_buffer); ditahan.append(r)
            else:
                r.fulfill(json={"id": "job3", "status": st["status"], "progress": {"total": 1},
                                "items": [{"name": "TMP-A", "status": st["status"]}]})
        page.route("**/api/batch", batch)
        page.route("**/api/batch/job3", batch)
        self.muat(page, "#batch")
        page.fill("#batchIds", "TMP-A")
        page.set_input_files("#batchFiles", str(FOTO[0]))
        page.click("#batchStart")
        page.wait_for_timeout(200)
        self.assertTrue(page.is_disabled("#batchStart"))
        page.click("#batchStart", force=True); page.wait_for_timeout(200)
        self.assertEqual(len(posts), 1, "dobel klik membuat dua job")
        ditahan[0].fulfill(status=202, json={"id": "job3"})
        page.wait_for_function("/— running —/.test(document.getElementById('batchStatus').textContent)")
        for sel in ("#batchStart", "#batchIds", "#batchFiles", "#batchMethod", "#batchTask", "#batchAddCurrent", "#batchResume"):
            self.assertTrue(page.is_disabled(sel), sel)
        self.assertEqual(page.eval_on_selector("#batchFiles", "e=>e.files.length"), 0)
        st["status"] = "complete"
        page.wait_for_function("/— complete —/.test(document.getElementById('batchStatus').textContent)", timeout=8000)
        for sel in ("#batchStart", "#batchIds", "#batchFiles", "#batchMethod", "#batchTask", "#batchResume"):
            self.assertFalse(page.is_disabled(sel), sel)

    # ---------------- F10 ----------------
    def test_f10_mobile_gulir_ke_overlay_dan_hasil(self):
        page = self.buka(390, 844, mobile=True); self.muat(page)
        ditahan = []
        page.route("**/api/analisis", lambda r: ditahan.append(r))
        page.click("#jalan"); page.wait_for_timeout(900)
        kartu = page.evaluate("()=>{const r=document.querySelector('.processing-card').getBoundingClientRect();return [r.top,r.bottom,innerHeight]}")
        self.assertTrue(0 <= kartu[0] and kartu[1] <= kartu[2], f"kartu loading di luar layar: {kartu}")
        panjang = hasil_palsu()
        panjang["penjelasan"] = [{"asal": "model", "label": f"Blok {i}", "teks": "teks panjang " * 40} for i in range(12)]
        ditahan[0].fulfill(json=panjang); page.wait_for_selector("#hasil", state="visible"); page.wait_for_timeout(900)
        pos = page.evaluate("()=>[document.getElementById('hasil').getBoundingClientRect().top,document.querySelector('header').getBoundingClientRect().bottom,innerHeight]")
        self.assertTrue(pos[1] - 1 <= pos[0] < pos[2] / 2, f"hasil tidak terlihat: {pos}")
        page.click("#result-tab-sumber"); page.evaluate("window.scrollBy(0,600)"); page.wait_for_timeout(300)
        hdr, tabs = page.evaluate("()=>[document.querySelector('header').getBoundingClientRect().bottom,document.querySelector('.result-tabs').getBoundingClientRect().top]")
        self.assertAlmostEqual(tabs, hdr, delta=1.5)

    def test_f10_desktop_tidak_auto_scroll(self):
        page = self.buka(1280, 600); self.muat(page)
        page.route("**/api/analisis", lambda r: r.fulfill(json=hasil_palsu()))
        page.click("#jalan"); page.wait_for_selector("#hasil", state="visible"); page.wait_for_timeout(600)
        self.assertEqual(page.evaluate("scrollY"), 0)

    # ---------------- F11 ----------------
    def test_f11_task_batch_dan_id_tanpa_duplikat(self):
        page = self.buka(); self.muat(page)
        posts = []
        page.route("**/api/batch", lambda r: (posts.append(r.request.post_data or ""), r.fulfill(status=400, json={"error": "uji"})))
        page.select_option("#task", "task1_issue")
        sample = page.input_value("#sample")
        page.evaluate("location.hash='#batch'")
        self.assertTrue(page.is_visible("#batchTask"))
        self.assertEqual(page.input_value("#batchTask"), "task1_issue")
        page.click("#batchAddCurrent"); page.click("#batchAddCurrent")
        self.assertEqual(page.input_value("#batchIds"), sample)
        page.select_option("#batchTask", "task3_primary_entity_type")
        page.click("#batchStart"); page.wait_for_function("document.getElementById('batchStatus').textContent==='uji'")
        self.assertIn("task3_primary_entity_type", posts[0])
        self.assertEqual(json.loads(re.search(r'name="sample_ids"\r\n\r\n(.*?)\r\n', posts[0]).group(1)), [sample])

    # ---------------- F12 ----------------
    def test_f12_respons_bukan_json_dan_error_json(self):
        page = self.buka(); self.muat(page)
        page.route("**/api/analisis", lambda r: r.fulfill(status=413, body="<html>Too large</html>", content_type="text/html"))
        page.click("#jalan"); page.wait_for_function("document.getElementById('workspace').dataset.state==='ready' && !document.getElementById('jalan').disabled")
        page.wait_for_timeout(200)
        self.assertTrue(self.dialogs and "terlalu besar" in self.dialogs[-1], self.dialogs)
        self.assertNotIn("Unexpected token", self.dialogs[-1])
        page.unroute("**/api/analisis")
        page.route("**/api/analisis", lambda r: r.fulfill(status=429, json={"error": "Server sibuk, antrean penuh."}))
        page.click("#jalan"); page.wait_for_timeout(500)
        self.assertEqual(self.dialogs[-1], "Gagal: Server sibuk, antrean penuh.")
        self.unggah(page, {"status": 502, "body": "<html>Bad gateway</html>", "content_type": "text/html"})
        st = page.inner_text("#statusOcr")
        self.assertIn("tidak dapat dihubungi", st); self.assertNotIn("Unexpected token", st)
        self.assertFalse(page.is_disabled("#jalan"))
        page.route("**/api/batch", lambda r: r.fulfill(status=413, body="<html>x</html>", content_type="text/html"))
        page.evaluate("location.hash='#batch'"); page.fill("#batchIds", "TMP-A"); page.click("#batchStart")
        page.wait_for_function("/terlalu besar/.test(document.getElementById('batchStatus').textContent)")
        self.assertFalse(page.is_disabled("#batchStart"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
