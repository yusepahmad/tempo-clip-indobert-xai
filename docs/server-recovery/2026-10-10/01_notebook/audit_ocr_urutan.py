"""Audit OCR: salah urut vs salah baca (plan docs/plans/2026-10-06-audit-ocr-urutan-kata.md).

  venv/bin/python 01_notebook/audit_ocr_urutan.py ocr      # jalankan EasyOCR, simpan blok (sekali)
  venv/bin/python 01_notebook/audit_ocr_urutan.py evaluasi # bandingkan selector pada blok yang sama

Set dev = 30 sampul diagnosis lama (dipakai merancang); set uji = 100 sampul acak lain
(seed 42, hanya untuk pengukuran); foto dosen dicatat terpisah.
"""
import csv, importlib.util, json, random, re, sys, time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "02_web_demo"))
OUT = ROOT / "04_hasil_eksperimen" / "revisi_week3"
CACHE = OUT / "ocr_audit_blok_20261006.json"
REPORT = OUT / "ocr_audit_urutan_20261006.json"
DOSEN_REF = {"04.33.42": "GULA-GULA DEMO BURUH", "05.29.27": "WASWAS RUPIAH",
             "05.31.04": "CUKAI ABAL-ABAL ROKOK ILEGAL"}  # acuan visual agen, bukan ground truth

rows = {r["sample_id"]: r for r in csv.DictReader((ROOT / "03_data/DATASET_740_TASK2_DOMAIN.csv").open(encoding="utf-8-sig"))}
diag = json.loads((OUT / "ocr_diagnosis.json").read_text(encoding="utf-8"))["results"]
DEV = [x["sample_id"] for x in diag]
UJI = random.Random(42).sample(sorted(set(rows) - set(DEV)), 100)
# Validasi: dibuka hanya setelah rancangan dibekukan (set uji terkontaminasi oleh perbaikan).
VALIDASI = random.Random(7).sample(sorted(set(rows) - set(DEV) - set(UJI)), 60)
# Validasi kedua: dibuka setelah perbaikan lanjutan dibekukan (validasi pertama ikut terkontaminasi).
VALIDASI2 = random.Random(11).sample(sorted(set(rows) - set(DEV) - set(UJI) - set(VALIDASI)), 60)


def gambar(sid):
    return next(ROOT / "05_gambar" / (sid + e) for e in (".jpg", ".jpeg", ".png", ".webp")
                if (ROOT / "05_gambar" / (sid + e)).exists())


def tinggi(path):
    from PIL import Image
    return float(Image.open(path).size[1])


def jalankan_ocr_validasi(nama="validasi", ids=None):
    import torch
    torch.set_num_threads(8)
    import ocr_headline as oh
    pembaca = oh._siapkan()
    cache = json.loads(CACHE.read_text(encoding="utf-8"))
    ids = VALIDASI if ids is None else ids
    cache[nama] = {}
    for i, sid in enumerate(ids, 1):
        t = time.perf_counter()
        path = gambar(sid)
        blok = oh._baca_easyocr(pembaca, path)
        cache[nama][sid] = {"blok": blok, "tinggi": tinggi(path), "detik": round(time.perf_counter() - t, 2)}
        print(f"{i}/{len(ids)} {nama} {sid} {len(blok)} blok", flush=True)
    CACHE.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")


def jalankan_ocr():
    import torch
    torch.set_num_threads(8)
    import ocr_headline as oh
    pembaca = oh._siapkan()
    cache = {"catatan": "Blok EasyOCR mentah (mesin produksi, paragraph=False).", "dev": {}, "uji": {}, "dosen": {}}
    for x in diag:  # dev: blok sudah tersimpan dari diagnosis lama
        cache["dev"][x["sample_id"]] = {"blok": x["ocr"]["blok_mentah"], "tinggi": tinggi(gambar(x["sample_id"]))}
    targets = [("uji", sid, gambar(sid)) for sid in UJI]
    targets += [("dosen", p.stem.split(" at ")[-1], p) for p in sorted((ROOT / "06_gambar_revisi").glob("*.jpeg"))]
    for i, (subset, key, path) in enumerate(targets, 1):
        t = time.perf_counter()
        blok = oh._baca_easyocr(pembaca, path)
        cache[subset][key] = {"blok": blok, "tinggi": tinggi(path), "detik": round(time.perf_counter() - t, 2)}
        print(f"{i}/{len(targets)} {subset} {key} {len(blok)} blok {cache[subset][key]['detik']}s", flush=True)
    CACHE.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")


# ---------- metrik ----------
def kata(s):
    s = (s or "").upper().replace("’", "'").replace("‐", "-").replace("‑", "-").replace("–", "-")
    return re.findall(r"[0-9A-ZÀ-ÖØ-Ý]+(?:[-'][0-9A-ZÀ-ÖØ-Ý]+)*", s)


def lcs(a, b):
    prev = [0] * (len(b) + 1)
    for x in a:
        cur = [0]
        for j, y in enumerate(b, 1):
            cur.append(prev[j - 1] + 1 if x == y else max(prev[j], cur[-1]))
        prev = cur
    return prev[-1]


def edit(a, b):
    prev = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        cur = [i]
        for j, y in enumerate(b, 1):
            cur.append(min(cur[-1] + 1, prev[j] + 1, prev[j - 1] + (x != y)))
        prev = cur
    return prev[-1]


def nilai_headline(truth, pred):
    t, p = kata(truth), kata(pred)
    cocok = sum((Counter(t) & Counter(p)).values())
    recall = cocok / max(len(t), 1)
    urut = lcs(t, p) / cocok if cocok else None
    if not p:
        kategori = "kosong"
    elif t == p:
        kategori = "tepat"
    elif Counter(t) == Counter(p):
        kategori = "salah_urut"
    elif recall < .5:
        kategori = "salah_pilih_blok"
    elif urut is not None and urut < 1:
        kategori = "salah_urut_dan_baca"
    else:
        kategori = "salah_baca_atau_tidak_lengkap"
    return {"kategori": kategori, "exact": t == p, "word_recall": round(recall, 3),
            "urutan_lcs": None if urut is None else round(urut, 3),
            "cer": round(edit(" ".join(t), " ".join(p)) / max(len(" ".join(t)), 1), 3)}


def nilai_pendukung(truth, pred):
    t, p = kata(truth), kata(pred)
    cocok = sum((Counter(t) & Counter(p)).values())
    return {"truth_kata": len(t), "word_recall": round(cocok / len(t), 3) if t else None,
            "urutan_lcs": round(lcs(t, p) / cocok, 3) if cocok >= 2 else None}


def muat_selector(path, nama):
    spec = importlib.util.spec_from_file_location(nama, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m.pilih_headline


def ringkas(items, kunci):
    hs = [x[kunci]["headline"] for x in items]
    ps = [x[kunci]["pendukung"] for x in items if x[kunci]["pendukung"]["urutan_lcs"] is not None]
    rec = [x[kunci]["pendukung"]["word_recall"] for x in items if x[kunci]["pendukung"]["word_recall"] is not None]
    return {"n": len(items), "headline_exact": sum(h["exact"] for h in hs),
            "headline_kategori": dict(Counter(h["kategori"] for h in hs)),
            "headline_cer_rata": round(sum(h["cer"] for h in hs) / len(hs), 4),
            "pendukung_word_recall_rata": round(sum(rec) / len(rec), 3) if rec else None,
            "pendukung_urutan_lcs_rata": round(sum(p["urutan_lcs"] for p in ps) / len(ps), 3) if ps else None,
            "pendukung_urutan_sempurna": sum(p["urutan_lcs"] == 1 for p in ps),
            "pendukung_n_dinilai_urutan": len(ps)}


def evaluasi():
    cache = json.loads(CACHE.read_text(encoding="utf-8"))
    selectors = {"baseline": muat_selector(ROOT / "01_notebook/ocr_selector_baseline_20261006.py", "ocr_baseline"),
                 "audit1": muat_selector(ROOT / "01_notebook/ocr_selector_audit1_20261006.py", "ocr_audit1"),
                 "produksi": muat_selector(ROOT / "02_web_demo/ocr_headline.py", "ocr_produksi")}
    hasil = {}
    subsets = [s for s in ("dev", "uji", "validasi", "validasi2") if s in cache]
    for subset in subsets:
        items = []
        for sid, c in cache[subset].items():
            r = rows[sid]
            item = {"sample_id": sid, "headline_truth": r["headline_verified"],
                    "pendukung_truth": r["supporting_text_verified"]}
            for nama, fn in selectors.items():
                o = fn(c["blok"], c["tinggi"])
                item[nama] = {"headline_ocr": o["headline"], "pendukung_ocr": o["pendukung"],
                              "headline": nilai_headline(r["headline_verified"], o["headline"]),
                              "pendukung": nilai_pendukung(r["supporting_text_verified"], o["pendukung"])}
            items.append(item)
        hasil[subset] = {"ringkasan": {n: ringkas(items, n) for n in selectors}, "items": items}
    dosen = {}
    for key, c in cache["dosen"].items():
        dosen[key] = {}
        for n, fn in selectors.items():
            o = fn(c["blok"], c["tinggi"])
            dosen[key][n] = {"headline_ocr": o["headline"], "pendukung_ocr": o["pendukung"],
                             "headline": nilai_headline(DOSEN_REF[key], o["headline"])}
    REPORT.write_text(json.dumps({"tanggal": time.strftime("%Y-%m-%d %H:%M:%S"),
                                  "plan": "docs/plans/2026-10-06-audit-ocr-urutan-kata.md",
                                  "set": {"dev": "30 diagnosis lama (dipakai merancang)",
                                          "uji": "100 acak seed 42 di luar dev; TERKONTAMINASI — pola kesalahannya dipakai memperbaiki selector",
                                          "validasi": "60 acak seed 7 di luar dev dan uji; angka utama audit pertama; TERKONTAMINASI oleh perbaikan lanjutan",
                                          "validasi2": "60 acak seed 11 di luar dev/uji/validasi; dibuka setelah perbaikan lanjutan dibekukan (angka utama lanjutan)"},
                                  "selector": {"baseline": "sebelum audit", "audit1": "audit urutan pertama", "produksi": "versi aplikasi saat ini"},
                                  "kebenaran": "headline_verified / supporting_text_verified dataset; foto dosen: acuan visual agen",
                                  **hasil, "dosen": dosen}, ensure_ascii=False, indent=2), encoding="utf-8")
    for subset in subsets:
        for n, s in hasil[subset]["ringkasan"].items():
            print(subset, n, json.dumps(s, ensure_ascii=False))
    for key, v in dosen.items():
        print("dosen", key, {n: v[n]["headline_ocr"] for n in v})


if __name__ == "__main__":
    {"ocr": jalankan_ocr, "ocr_validasi": jalankan_ocr_validasi,
     "ocr_validasi2": lambda: jalankan_ocr_validasi("validasi2", VALIDASI2), "evaluasi": evaluasi}[sys.argv[1]]()
