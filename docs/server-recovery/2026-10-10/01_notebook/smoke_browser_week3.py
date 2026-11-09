"""Smoke UI browser headless (Chromium) untuk demo Week 3, desktop dan mobile.

Jalankan saat server demo hidup (lihat docs/HANDOFF_SERVER.md):
    TEMPO_DEMO_URL=http://127.0.0.1:7861 venv/bin/python 01_notebook/smoke_browser_week3.py
Dependensi: requirements-browser.txt.
Output: 04_hasil_eksperimen/revisi_week3/browser_smoke_<tanggal>/ (screenshot, ekspor)
        dan browser_smoke_<tanggal>.json (checklist). Bukan uji pengguna manusia.
"""
import json, os, sys, time, traceback
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
BASE = os.environ.get("TEMPO_DEMO_URL", "http://127.0.0.1:7861")
TAG = os.environ.get("SMOKE_TAG", time.strftime("%Y%m%d"))
OUT = ROOT / "04_hasil_eksperimen" / "revisi_week3" / f"browser_smoke_{TAG}"
REPORT = OUT.with_suffix(".json")
FOTO = sorted((ROOT / "06_gambar_revisi").glob("*.jpeg"))
REF = {"04.33.42": "GULA-GULA DEMO BURUH", "05.29.27": "WASWAS RUPIAH",
       "05.31.04": "CUKAI ABAL-ABAL ROKOK ILEGAL"}  # acuan visual agen, bukan ground truth
LONG = "\n".join(f"Baris {i}: teks pendukung panjang untuk memeriksa textarea multibaris, "
                 f"kalimat ini sengaja dibuat cukup panjang agar membungkus." for i in range(1, 10))
ANALISIS_MS, OCR_MS = 300_000, 180_000

checks, runs, events = [], [], []


def check(view, name, ok, detail=None):
    checks.append({"viewport": view, "check": name, "ok": bool(ok), "detail": detail})
    print(("PASS" if ok else "FAIL"), view, name, "" if detail is None else detail, flush=True)


def shot(page, view, name, full=False):
    p = OUT / f"{view}_{name}.png"
    page.screenshot(path=str(p), full_page=full)
    return p.name


def state(page):
    return page.eval_on_selector("#workspace", "e=>e.dataset.state")


def img_loaded(page, sel):
    return page.eval_on_selector(sel, "e=>e.complete && e.naturalWidth>0 && getComputedStyle(e).display!=='none'")


def wait_ready(page, timeout=OCR_MS):
    page.wait_for_function("document.getElementById('workspace').dataset.state!=='ocr'", timeout=timeout)


def run_analysis(page, view, label):
    """Klik Analisis, cek loading terlihat sejak awal, tunggu hasil. Kembalikan JSON respons."""
    with page.expect_response(lambda r: r.url.endswith("/api/analisis"), timeout=ANALISIS_MS) as resp:
        page.click("#jalan")
        page.wait_for_selector("#processingOverlay:not([hidden])", timeout=3000)
        check(view, f"{label}: overlay loading tampil saat request", True)
        check(view, f"{label}: tombol busy", page.is_disabled("#jalan")
              and "Menganalisis" in page.inner_text("#jalan"), page.inner_text("#jalan"))
    d = resp.value.json()
    page.wait_for_selector("#hasil", state="visible", timeout=30_000)
    page.wait_for_selector("#processingOverlay", state="hidden", timeout=30_000)
    check(view, f"{label}: hasil tampil, loading bersih", state(page) == "results" and not page.is_disabled("#jalan"))
    return d


def open_tab(page, name):
    page.click(f"#result-tab-{name}")
    page.wait_for_selector(f"#result-panel-{name}", state="visible")
    page.wait_for_timeout(400)  # tunggu transisi warna tab (.15s) selesai sebelum screenshot


def check_visual(page, view, label, d):
    open_tab(page, "visual")
    page.wait_for_function("['imgHeat','imgHeatTask'].every(i=>{const e=document.getElementById(i);return e.complete&&e.naturalWidth>0})", timeout=30_000)
    heat, task = page.get_attribute("#imgHeat", "src"), page.get_attribute("#imgHeatTask", "src")
    check(view, f"{label}: R5 peta utama = gabungan", heat == d["heatmap_padu_url"] and img_loaded(page, "#imgHeat"), heat)
    check(view, f"{label}: R5 bukti task pilihan terpisah", task == d["heatmap_url"] and task != heat and img_loaded(page, "#imgHeatTask"), task)
    judul = page.inner_text("#judulHeatTask")
    check(view, f"{label}: R5 judul task/kelas", d["task_xai"] in judul and d["kelas_untuk_atribusi_tampil"] in judul, judul)
    check(view, f"{label}: R5 caption gabungan", "gabungan tiga task" in page.inner_text("#capHeat"))


def page_basics(page, view):
    check(view, "tanpa scroll horizontal",
          page.evaluate("document.documentElement.scrollWidth<=window.innerWidth+1"),
          page.evaluate("[document.documentElement.scrollWidth, window.innerWidth]"))


def scenario_initial(page, view):
    page.goto(BASE + "/#analisis")
    page.wait_for_function("document.getElementById('sample').options.length>700", timeout=60_000)
    page.wait_for_function("!!document.getElementById('previewData').getAttribute('src')")
    check(view, "workspace tampil dan bukan di dalam textarea (regresi textarea)",
          page.is_visible("#workspace") and page.evaluate("!document.getElementById('workspace').closest('textarea')"))
    check(view, "tepat 3 textarea", page.evaluate("document.querySelectorAll('textarea').length") == 3)
    teks = page.evaluate("document.body.innerText")
    check(view, "petunjuk tidak memakai arah kiri/kanan (benar di desktop dan mobile)",
          "panel kiri" not in teks and "sebelah kanan" not in teks)
    check(view, "batch/panduan tersembunyi di view analisis", page.is_hidden("#batch") and page.is_hidden("#panduan"))
    page_basics(page, view)
    shot(page, view, "01_awal", full=True)


def scenario_dataset(page, view):
    page.select_option("#task", "task2_domain_sumber")
    d = run_analysis(page, view, "dataset")
    runs.append({"viewport": view, "skenario": "dataset", "sample_id": d["snapshot"]["sample_id"],
                 "task_id": d["task_id"], "headline": d["headline"], "metode": d["metode_atribusi"],
                 "kelas": d["kelas_untuk_atribusi"], "detik_server": d.get("durasi_detik")})
    for i, tab in enumerate(["ringkasan", "visual", "teks", "sumber", "verifikasi"], 2):
        if tab == "visual":
            check_visual(page, view, "dataset", d)
        else:
            open_tab(page, tab)
        page.locator(f"#result-panel-{tab}").scroll_into_view_if_needed()
        shot(page, view, f"{i:02d}_dataset_{tab}", full=(view == "mobile"))
    check(view, "kata atribusi tampil", page.evaluate("document.getElementById('kataBox').innerText.trim().length>0"))
    page_basics(page, view)


def scenario_keyboard(page, view):
    page.focus("#result-tab-ringkasan")
    seq = [("ArrowRight", "visual"), ("End", "verifikasi"), ("Home", "ringkasan"), ("ArrowLeft", "verifikasi")]
    ok = True
    for key, want in seq:
        page.keyboard.press(key)
        got = page.evaluate("document.activeElement.dataset.resultTab")
        ok &= got == want and page.is_visible(f"#result-panel-{want}")
    check(view, "keyboard tab hasil (Arrow/Home/End)", ok)


def scenario_race(page, view):
    page.select_option("#task", "task1_issue")
    page.click("#jalan")
    page.wait_for_selector("#processingOverlay:not([hidden])", timeout=3000)
    try:
        page.select_option("#task", "task3_primary_entity_type", timeout=3000)
        reachable = True
    except Exception as e:
        reachable = False
        check(view, "race: task dapat diganti saat analisis", False, repr(e)[:200])
    if reachable:
        page.wait_for_timeout(1500)
        check(view, "race: ganti task membatalkan hasil lama",
              page.is_hidden("#hasil") and state(page) == "ready" and not page.is_disabled("#jalan"), state(page))
        d = run_analysis(page, view, "race-ulang")
        check(view, "race: hasil baru sesuai task baru",
              d["task_id"] == "task3_primary_entity_type" and d["task_xai"] in page.inner_text("#ringkas"))


def scenario_failure(page, view):
    start = len(events)
    try:
        _failure(page, view)
    finally:
        for e in events[start:]:
            e["expected"] = "uji kegagalan disengaja (route abort/500)"


def _failure(page, view):
    dialogs = []
    page.on("dialog", lambda dg: (dialogs.append(dg.message), dg.accept()))
    for mode, handler, expect in [
        ("jaringan", lambda r: r.abort(), "Terjadi kesalahan"),
        ("server", lambda r: r.fulfill(status=500, content_type="application/json", body='{"error":"uji kegagalan server"}'), "Gagal: uji kegagalan server")]:
        page.route("**/api/analisis", handler)
        n = len(dialogs)
        page.click("#jalan")
        for _ in range(150):  # tunggu dialog error, bukan state: analisis() sempat 'ready' sebelum request
            if len(dialogs) > n:
                break
            page.wait_for_timeout(100)
        page.wait_for_timeout(300)
        msg = dialogs[n] if len(dialogs) > n else None
        check(view, f"gagal {mode}: pesan error dan loading bersih",
              msg is not None and msg.startswith(expect) and page.is_hidden("#processingOverlay") and not page.is_disabled("#jalan"), msg)
        page.unroute("**/api/analisis")


def upload_and_ocr(page, view, foto, label):
    page.click("#tabUnggah")
    page.set_input_files("#gambar", str(foto))
    seen = False
    try:
        page.wait_for_selector("#processingOverlay:not([hidden])", timeout=2000)
        seen = "membaca teks" in page.inner_text("#processingTitle")
    except Exception:
        pass
    wait_ready(page)
    hl = page.input_value("#headline")
    check(view, f"{label}: OCR selesai, headline terisi", bool(hl), {"overlay_ocr_terlihat": seen, "headline": hl})
    return hl


def scenario_dosen(page, view):
    for foto in FOTO:
        key = foto.stem.split(" at ")[-1]
        page.click("#tabData")  # mulai bersih: pindah mode mengosongkan kolom unggahan
        ocr = upload_and_ocr(page, view, foto, f"dosen {key}")
        status_ocr = page.inner_text("#statusOcr")
        final = ocr
        if ocr != REF[key]:  # alur pengguna: koreksi judul yang salah baca
            page.fill("#headline", REF[key])
            final = REF[key]
        supporting = page.input_value("#supporting")
        page.select_option("#task", "task2_domain_sumber")
        d = run_analysis(page, view, f"dosen {key}")
        check_visual(page, view, f"dosen {key}", d)
        shot(page, view, f"10_dosen_{key.replace('.', '')}_visual")
        open_tab(page, "teks")
        shot(page, view, f"10_dosen_{key.replace('.', '')}_kata")
        runs.append({"viewport": view, "skenario": "foto_dosen", "file": foto.name, "headline_ocr": ocr,
                     "status_ocr": status_ocr,
                     "headline_final": final, "dikoreksi": ocr != final, "supporting_final": supporting,
                     "task_id": d["task_id"], "metode": d["metode_atribusi"], "kelas": d["kelas_untuk_atribusi"],
                     "atribusi_kata": d.get("atribusi_kata"), "detik_server": d.get("durasi_detik")})


def scenario_upload_long(page, view):
    foto = FOTO[0]
    upload_and_ocr(page, view, foto, "unggah")
    page.fill("#supporting", LONG)
    m = page.eval_on_selector("#supporting", "e=>({same:e.value===arguments[0], sh:e.scrollHeight, ch:e.clientHeight, resize:getComputedStyle(e).resize, rows:e.rows})".replace("arguments[0]", json.dumps(LONG)))
    check(view, "teks pendukung panjang utuh, textarea dapat digulir/diperbesar",
          m["same"] and m["sh"] > m["ch"] and m["resize"] != "none", m)
    page.evaluate("window.scrollTo(0, document.scrollingElement.scrollHeight)")
    sc = page.evaluate("({y:window.scrollY, sh:document.scrollingElement.scrollHeight, ih:window.innerHeight})")
    check(view, "halaman dapat digulir vertikal", sc["sh"] <= sc["ih"] or sc["y"] > 0, sc)
    page.locator("#supporting").scroll_into_view_if_needed()
    shot(page, view, "20_unggah_teks_panjang", full=True)
    d = run_analysis(page, view, "unggah")
    sent = d.get("supporting", "")
    # Browser menormalisasi baris baru menjadi CRLF pada multipart/form-data (standar HTML).
    check(view, "unggah: teks pendukung panjang terkirim utuh",
          sent.replace("\r\n", "\n").strip() == LONG.strip(), {"crlf_dari_browser": "\r\n" in sent, "panjang": len(sent)})
    check_visual(page, view, "unggah", d)
    shot(page, view, "21_unggah_hasil_visual", full=True)
    page_basics(page, view)


def scenario_ocr_race(page, view):
    page.click("#tabUnggah")
    page.set_input_files("#gambar", str(FOTO[1]))
    page.wait_for_timeout(200)
    page.set_input_files("#gambar", str(FOTO[2]))
    wait_ready(page)
    page.wait_for_timeout(8000)  # beri waktu respons OCR lama tiba
    hl = page.input_value("#headline")
    check(view, "race OCR: respons gambar lama tidak menimpa gambar baru", hl.startswith("CUKAI"), hl)


def scenario_edit_preserved(page, view):
    """Gambar baru mengganti judul (termasuk yang disunting); ketikan selama OCR gambar itu dilindungi."""
    page.click("#tabData")
    upload_and_ocr(page, view, FOTO[0], "suntingan")
    page.fill("#headline", "JUDUL SUNTINGAN PENGGUNA")
    page.set_input_files("#gambar", str(FOTO[2]))
    wait_ready(page)
    hl, msg = page.input_value("#headline"), page.inner_text("#statusOcr")
    check(view, "ganti gambar: judul suntingan lama diganti hasil gambar baru",
          hl.startswith("CUKAI") and "diganti" in msg, {"headline": hl, "status": msg})
    shot(page, view, "15_judul_diganti_gambar_baru")
    page.set_input_files("#gambar", str(FOTO[0]))
    page.fill("#headline", "KETIK SAAT OCR")
    wait_ready(page)
    check(view, "ketikan selama OCR gambar yang sama tidak ditimpa", page.input_value("#headline") == "KETIK SAAT OCR",
          page.input_value("#headline"))
    page.click("#tabData")


def scenario_berkas_sama(page, view):
    """Memilih berkas yang sama lagi harus memicu OCR dan membatalkan hasil lama."""
    page.click("#tabData")
    upload_and_ocr(page, view, FOTO[0], "berkas sama")
    run_analysis(page, view, "berkas sama")
    lama = page.get_attribute("#imgAsli", "src")
    with page.expect_response(lambda r: r.url.endswith("/api/ocr"), timeout=OCR_MS):
        page.set_input_files("#gambar", str(FOTO[0]))
    check(view, "berkas sama dipilih lagi: hasil lama disembunyikan, OCR jalan ulang",
          page.is_hidden("#hasil") and page.input_value("#gambar") == "", page.inner_text("#namaBerkas"))
    wait_ready(page)
    d = run_analysis(page, view, "berkas sama ulang")
    check(view, "berkas sama: analisis baru memakai berkas aktif", page.get_attribute("#imgAsli", "src") != lama
          and "Gambar aktif" in page.inner_text("#namaBerkas"), d["gambar_url"])
    shot(page, view, "16_berkas_sama")
    page.click("#tabData")
    check(view, "pindah ke dataset mengosongkan berkas aktif", page.inner_text("#namaBerkas") == "")


def scenario_batch(page, view, request):
    page.goto(BASE + "/#batch")
    page.wait_for_selector("#batch", state="visible")
    sample = page.evaluate("daftar[1].sample_id")
    page.fill("#batchIds", sample)
    page.set_input_files("#batchFiles", files=[{"name": "rusak.png", "mimeType": "image/png", "buffer": b"bukan gambar"}])
    page.select_option("#batchMethod", "occlusion")
    page.click("#batchStart")
    page.wait_for_function("/— (complete|needs_review|interrupted|failed) —/.test(document.getElementById('batchStatus').textContent)", timeout=ANALISIS_MS)
    status = page.inner_text("#batchStatus")
    items = page.eval_on_selector_all("#batchResults > details > summary", "es=>es.map(e=>e.textContent)")
    check(view, "batch selesai: 1 berhasil + gambar rusak gagal",
          any(s.endswith("— success") for s in items) and any(s.endswith("— failed") for s in items), {"status": status[:200], "items": items})
    for fmt in ("csv", "json"):
        href = page.get_attribute(f"#batchStatus a[href$='/export/{fmt}']", "href")
        r = request.get(BASE + href)
        (OUT / f"batch_export.{fmt}").write_bytes(r.body())
        check(view, f"batch ekspor {fmt.upper()}", r.ok and len(r.body()) > 50, len(r.body()))
    page.eval_on_selector_all("#batchResults > details", "ds=>ds.forEach(d=>d.open=true)")
    gagal = page.locator("#batchResults > details", has_text="rusak.png").inner_text()
    check(view, "batch: pesan gagal tanpa path server", "gambar tidak terbaca" in gagal.lower() and "/home/" not in gagal
          and "_jobs" not in gagal, gagal[-120:])
    link = page.locator("#batchResults a", has_text="peta gabungan").first
    r = request.get(BASE + link.get_attribute("href"))
    check(view, "batch tautan peta gabungan PNG", r.ok and r.body()[:8] == b"\x89PNG\r\n\x1a\n")
    shot(page, view, "30_batch", full=True)


def scenario_panduan(page, view):
    page.goto(BASE + "/#panduan")
    page.wait_for_function("document.querySelectorAll('#catalog h3').length===3", timeout=30_000)
    n = page.evaluate("document.querySelectorAll('#catalog details').length")
    check(view, "panduan: katalog 3 task / 25 kelas", n == 25, n)
    page.evaluate("document.querySelector('#panduan details').open=true")
    shot(page, view, "40_panduan", full=True)


VIEWPORTS = {
    "desktop": dict(viewport={"width": 1440, "height": 900}),
    "mobile": dict(viewport={"width": 390, "height": 844}, device_scale_factor=2, is_mobile=True, has_touch=True),
}
PLAN = {
    "desktop": [scenario_initial, scenario_dataset, scenario_keyboard, scenario_race, scenario_failure,
                scenario_dosen, scenario_edit_preserved, scenario_berkas_sama, scenario_batch, scenario_panduan],
    "mobile": [scenario_initial, scenario_dataset, scenario_upload_long, scenario_ocr_race, scenario_panduan],
}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for view, opts in VIEWPORTS.items():
            ctx = browser.new_context(**opts, accept_downloads=True)
            page = ctx.new_page()
            page.set_default_timeout(30_000)
            page.on("console", lambda m, v=view: m.type == "error" and events.append({"viewport": v, "console": m.text}))
            page.on("pageerror", lambda e, v=view: events.append({"viewport": v, "pageerror": str(e)}))
            page.on("response", lambda r, v=view: r.status >= 400 and events.append({"viewport": v, "http": r.status, "url": r.url}))
            for sc in PLAN[view]:
                try:
                    if sc is scenario_batch:
                        sc(page, view, ctx.request)
                    else:
                        sc(page, view)
                except Exception as e:
                    check(view, f"{sc.__name__}: selesai tanpa exception", False, traceback.format_exc()[-800:])
                    try:
                        shot(page, view, f"error_{sc.__name__}", full=True)
                    except Exception:
                        pass
            ctx.close()
        browser.close()
    # 500 sengaja (uji kegagalan server) tidak dihitung sebagai error.
    unexpected = [e for e in events if not e.get("expected")]
    check("semua", "tanpa error konsol/halaman/HTTP tak terduga", not unexpected, unexpected[:10])
    ok = all(c["ok"] for c in checks)
    REPORT.write_text(json.dumps({
        "status": "success" if ok else "failed", "tanggal": time.strftime("%Y-%m-%d %H:%M:%S"),
        "server": BASE, "browser": "Chromium headless (Playwright 1.63.0, build 1243)",
        "viewport": {k: v["viewport"] for k, v in VIEWPORTS.items()},
        "plan": "docs/plans/2026-10-06-smoke-browser-ui.md", "durasi_detik": round(time.time() - t0, 1),
        "lulus": sum(c["ok"] for c in checks), "total": len(checks), "checks": checks,
        "input_dan_hasil": runs, "events": events, "screenshots": sorted(x.name for x in OUT.glob("*.png")),
        "batas": ["Chromium headless di Linux; bukan Firefox/Safari/Windows dan bukan uji pengguna manusia",
                  "Acuan headline foto dosen adalah transkripsi visual agen, bukan ground truth",
                  "Kelas hasil unggahan tidak divalidasi; ini uji alur dan render"]},
        ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{sum(c['ok'] for c in checks)}/{len(checks)} cek lulus -> {REPORT.relative_to(ROOT)}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
