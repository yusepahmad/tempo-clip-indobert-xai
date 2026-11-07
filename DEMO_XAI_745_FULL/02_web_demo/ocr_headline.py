#!/usr/bin/env python3
"""Pembacaan teks sampul otomatis untuk mengisi kolom headline (revisi R1).

Dosen mencatat: "user masih harus ngeinput ulang tuh teks, nah disaranin kalo
bisa itu kesalin otomatis karena user ga bakalan punya waktu buat ngetik
ulang". Modul ini membaca teks dari gambar sampul lalu menebak mana yang
merupakan headline.

Catatan penting soal peran OCR di sini:
hasil OCR **tidak** dipakai sebagai kebenaran. Ia hanya mengisi kolom di
antarmuka, dan pengguna tetap dapat menyuntingnya sebelum analisis dijalankan.
(Di antarmuka, memilih gambar baru mengganti isi kolom dengan hasil gambar
baru; pada batch, teks OCR menunggu konfirmasi pengguna.)
OCR pada sampul majalah tidak pernah sempurna — teks bertumpuk di atas
ilustrasi, memakai huruf hias, dan tercetak miring.

Pemilihan mesin didasarkan pada `01_notebook/uji_banding_ocr.py`, yang
membandingkan kandidat pada sampul asli memakai `headline_verified` sebagai
acuan. Hasilnya tersimpan di `04_hasil_eksperimen/uji_banding_ocr.json`.

Mesin dimuat lambat (saat pertama dipakai) supaya server tetap cepat menyala
bila fitur ini tidak dipakai.
"""

from __future__ import annotations

import re
from pathlib import Path

# Mesin yang dipakai. Diubah di satu tempat ini bila hasil uji banding
# menunjukkan kandidat lain lebih baik.
MESIN_DEFAULT = "easyocr"

_pembaca = None
_mesin_aktif = None
_alasan_gagal = None


# ------------------------------------------------------------------ mesin

def _muat_easyocr():
    import easyocr
    # Bahasa Indonesia dan Inggris sekaligus: sampul Tempo memuat keduanya
    # (mis. "TEMPO", "INVESTIGASI", nama asing).
    return easyocr.Reader(["id", "en"], gpu=False, verbose=False)


def _baca_easyocr(pembaca, path: Path) -> list[dict]:
    """Kembalikan blok teks beserta tinggi dan keyakinannya."""
    def baca(**opsi):
        return pembaca.readtext(str(path), detail=1, paragraph=False, **opsi)

    mentah = baca()
    # Huruf display yang sangat besar kadang runtuh menjadi fragmen dua huruf
    # berkeyakinan rendah (contoh development: "GO" terbaca "co"). Upscaling
    # seluruh koleksi memperlambat OCR, jadi second-pass hanya untuk pola ini.
    from PIL import Image
    tinggi_gambar = Image.open(path).height
    pemicu = [(kotak, teks, yakin) for kotak, teks, yakin in mentah
              if 1 <= len(re.sub(r"[^A-Za-z]", "", str(teks))) <= 2
              and 0.12 <= float(yakin) < 0.35
              and max(t[1] for t in kotak) - min(t[1] for t in kotak) >= 0.08 * tinggi_gambar]
    if pemicu:
        import numpy as np
        gambar = Image.open(path).convert("RGB")
        for kotak_pemicu, _, _ in pemicu:
            py0, py1 = min(t[1] for t in kotak_pemicu), max(t[1] for t in kotak_pemicu)
            ph = py1 - py0
            terkait = []
            for item in mentah:
                kotak = item[0]
                y0, y1 = min(t[1] for t in kotak), max(t[1] for t in kotak)
                h = y1 - y0
                if h >= 0.7 * ph and min(y1, py1) - max(y0, py0) >= 0.5 * min(h, ph):
                    terkait.append(item)
            xs = [t[0] for item in terkait for t in item[0]]
            ys = [t[1] for item in terkait for t in item[0]]
            pad = max(8, int(0.12 * ph))
            x0, y0 = max(0, int(min(xs)) - pad), max(0, int(min(ys)) - pad)
            x1, y1 = min(gambar.width, int(max(xs)) + pad), min(gambar.height, int(max(ys)) + pad)
            ulang = pembaca.readtext(np.array(gambar.crop((x0, y0, x1, y1))), detail=1,
                                     paragraph=False, mag_ratio=1.5,
                                     allowlist="ABCDEFGHIJKLMNOPQRSTUVWXYZ -")
            if ulang:
                mentah = [item for item in mentah if item not in terkait]
                mentah.extend(([[float(x) + x0, float(y) + y0] for x, y in kotak], teks, yakin)
                              for kotak, teks, yakin in ulang)

    hasil = []
    for kotak, teks, yakin in mentah:
        ys = [titik[1] for titik in kotak]
        xs = [titik[0] for titik in kotak]
        hasil.append({
            "teks": str(teks).strip(),
            "tinggi": float(max(ys) - min(ys)),
            "atas": float(min(ys)),
            "kiri": float(min(xs)),
            "kanan": float(max(xs)), "bawah": float(max(ys)), "kotak": [[float(x),float(y)] for x,y in kotak],
            "yakin": float(yakin),
        })
    return hasil


_MESIN = {
    "easyocr": (_muat_easyocr, _baca_easyocr),
}


def tersedia() -> bool:
    """Apakah OCR dapat dipakai pada lingkungan ini."""
    return _siapkan() is not None


def mesin_aktif() -> str | None:
    _siapkan()
    return _mesin_aktif


def alasan_gagal() -> str | None:
    """Penjelasan singkat bila OCR tidak tersedia, untuk ditampilkan apa adanya."""
    _siapkan()
    return _alasan_gagal


def _siapkan():
    """Muat mesin OCR sekali saja. Kembalikan None bila tidak tersedia."""
    global _pembaca, _mesin_aktif, _alasan_gagal
    if _pembaca is not None or _alasan_gagal is not None:
        return _pembaca

    muat, _ = _MESIN.get(MESIN_DEFAULT, (None, None))
    if muat is None:
        _alasan_gagal = f"mesin '{MESIN_DEFAULT}' tidak dikenal"
        return None

    try:
        _pembaca = muat()
        _mesin_aktif = MESIN_DEFAULT
    except ImportError as e:
        _alasan_gagal = (f"pustaka OCR belum terpasang ({e.name}). "
                         f"Pasang dengan: venv/bin/pip install {MESIN_DEFAULT}")
    except Exception as e:
        _alasan_gagal = f"{type(e).__name__}: {e}"
    return _pembaca


# ------------------------------------------------------- pemilihan headline

# Teks tetap yang selalu ada di sampul Tempo tetapi bukan headline.
_BULAN = r"(?:JANUARI|FEBRUARI|MARET|APRIL|MEI|JUNI|JULI|AGUSTUS|SEPTEMBER|OKTOBER|NOVEMBER|DESEMBER)"
_ABAIKAN = re.compile(
    r"^(TEMPO|ENAK\s+DIBACA.*|MAJALAH\s+BERITA.*|RP\s*[\d.,]+|"
    # "EDISI 3-9 SEPTEMBER 2012" dibuang; "EDISI KHUSUS … THAMRIN" tidak (audit 6 Okt).
    r"EDISI\b[\s\d.,:/–-]*(?:" + _BULAN + r"[\s\d.,:/–-]*)*|"
    r"ISSN.*|WWW\..*|H\.?\s*\d+|"
    # Rentang tanggal ("10-16", "22-28 JANUARI 2018"); rentang tahun "1903-1962" tetap.
    r"\d{1,2}\s*[-–]\s*\d{1,2}(?:\s+" + _BULAN + r".*)?|\d+\s*[-–]\s*\d+\s+" + _BULAN + r".*|"
    r"INVESTIGASI|LAPORAN\s+UTAMA|WAWANCARA|OPINI|SELINGAN)$",
    re.IGNORECASE,
)

# Logo "TEMPO" dicetak sangat besar, sehingga hampir selalu menjadi blok
# tertinggi pada sampul. OCR kerap membacanya tidak utuh, dan bentuk rusaknya
# tidak terduga karena logo sering tertutup objek foto: pada sampul
# "ANCANG-ANCANG JOKOWI" huruf M dan P tertutup kepala, sehingga terbaca
# "TEN". Pola yang menuntut awalan "TEM" tidak menangkap kasus itu.
#
# Karena itu dipakai dua lapis. `_LOGO_PASTI` menangkap bentuk yang tidak
# mungkin merupakan kata Indonesia, dan berlaku di mana pun pada sampul.
_LOGO_PASTI = re.compile(
    r"^[^A-Z0-9]*(TEMP[O0]\s*[0-9]*|TEMP|TEM[O0]|TEM|TEN|TE)[^A-Z0-9]*$",
    re.IGNORECASE,
)

# `_LOGO_ATAS` jauh lebih longgar — potongan pendek yang tersusun dari
# huruf-huruf pembentuk "TEMPO" — tetapi HANYA diterapkan pada bagian atas
# sampul, tempat logo berada. Tanpa pembatasan posisi, pola ini ikut membuang
# kata Indonesia yang sah seperti "MOMEN", "NONTON", atau "TEMPE" bila muncul
# sebagai headline.
_LOGO_ATAS = re.compile(r"^[^A-Z0-9]*[TEMPON0]{2,6}[^A-Z0-9]*$", re.IGNORECASE)

# Bagian atas sampul memuat logo, kicker rubrik, dan nomor halaman — bukan
# headline. Headline Tempo hampir selalu berada di bawah pertengahan sampul.
# Ambang ini longgar (0,28) supaya sampul dengan tata letak tidak lazim tetap
# tertangani; blok di atasnya tidak dibuang, hanya tidak diistimewakan
# sebagai kandidat headline.
_BATAS_ATAS_RELATIF = 0.28
# Baris kedua judul sering sengaja dicetak lebih kecil (mis. THOHIR/STORY,
# ISLAM/JALAN DAMAI). Kedekatan vertikal dan overlap kolom tetap wajib, jadi
# rasio ini dapat lebih longgar daripada filter kandidat utama.
_RASIO_TINGGI_LANJUTAN = 0.38
_RASIO_TINGGI_INTI = 0.62
_LOGO_DI_DALAM = re.compile(r"T\s*E\s*M\s*P\s*[O0]", re.IGNORECASE)
# Huruf tunggal berjarak, mis. tagline "E N A K  D I B A C A  D A N  P E R L U".
_HURUF_BERJARAK = re.compile(r"(?:\S\s+){2,}\S")


# Teks baku sampul yang kerap salah dibaca (audit 6 Okt, plan
# 2026-10-06-ocr-sampah-teks-baku). Semua aturan berlaku pada BLOK UTUH, bukan
# potongan kalimat, agar "Investigasi: …" atau "Rp 36 miliar" di tengah teaser
# tetap utuh.
_FOOTER = re.compile(r"T[E3][MN][PF][O0]C[O0]|MAJALAHTEM")          # majalah.tempo.co
_RUBRIK = ("INVESTIGASI", "LAPORANUTAMA", "WAWANCARA", "SELINGAN")
_HARGA_ISSN = re.compile(r"^(RP|IS[SN][NM]?|SN)\W{0,2}[\dO]", re.IGNORECASE)
_NOMINAL = re.compile(r"MILIAR|TRILIUN|JUTA|RIBU", re.IGNORECASE)   # teaser "Rp 179,56 miliar" bukan harga sampul


def _jarak_edit(a: str, b: str) -> int:
    prev = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        cur = [i]
        for j, y in enumerate(b, 1):
            cur.append(min(cur[-1] + 1, prev[j] + 1, prev[j - 1] + (x != y)))
        prev = cur
    return prev[-1]


def _sampah_baku(blok: dict, tinggi_gambar: float = 0.0) -> bool:
    t = blok["teks"].strip()
    rapat = re.sub(r"[^A-Za-z0-9]", "", t).upper()
    yakin = blok.get("yakin", 1.0)
    if _FOOTER.search(rapat):
        return True
    if len(rapat) <= 20 and ("MINGGUAN" in rapat or _jarak_edit(rapat, "MINGGUAN") <= 1):
        return True
    huruf = re.sub(r"[^A-Z]", "", rapat)
    # Selisih ketat agar kata sah tidak terbuang ("SERANGAN"≈SELINGAN, "INVESTASI"≈INVESTIGASI).
    if any(abs(len(huruf) - len(r)) <= 1 and _jarak_edit(huruf, r) <= (2 if len(r) >= 11 else 1)
           for r in _RUBRIK):
        return True
    # Variasi pembacaan banner rubrik yang rusak ("INVES ACAS]", "OUTLOOK EKONOMI", dll)
    if "INVESTASI" not in rapat and re.search(r"^(?:INVES|INVE5|1NVES)[A-Z0-9\s\]\[]{0,8}$", rapat):
        return True
    if re.search(r"^(?:OUTLOOK|UUTLOOK)(?:\s*(?:EKONOMI|POLITIK|HUKUM|BISNIS))?(?:\s*\d{4})?$", t, re.IGNORECASE):
        return True
    if re.search(r"^(?:LAPORAN\s+KHUSUS|EDISI\s+KHUSUS|LAPORAN\s+UTAMA)$", t, re.IGNORECASE):
        return True
    if len(t) <= 16 and yakin < 0.75 and _HARGA_ISSN.match(t) and not _NOMINAL.search(t):
        return True
    # Potongan acak satu kata campuran huruf+angka ("7uizo", "Doo10", "XI7Va").
    if (" " not in t and len(t) <= 8 and yakin < 0.75 and re.search(r"\d", t)
            and len(re.findall(r"[A-Za-z]", t)) >= 2 and not re.search(r"[-.]", t)):
        return True
    # Pecahan logo raksasa di area logo ("APO", "TEA", "TEI", "IMAD"; 4–10% teratas).
    # Dibatasi < 15% dan hanya pecahan logo yang dikenal; kata independen seperti "GIE" tetap aman.
    _PECAHAN_LOGO = {"APO", "TEA", "TEI", "IMAD", "EMPO", "TEM", "MPO", "TEN", "TE"}
    if (tinggi_gambar > 0 and blok["atas"] / tinggi_gambar < 0.15
            and blok.get("tinggi", 0) >= 0.08 * tinggi_gambar
            and (huruf in _PECAHAN_LOGO or (len(huruf) <= 4 and all(c in "TEMPON0" for c in huruf)))):
        return True
    return False


def _bukan_teks_sampul(blok: dict, tinggi_gambar: float = 0.0) -> bool:
    """Logo, tagline berjarak, dan teks baku sampul — bukan headline/pendukung."""
    t = blok["teks"].strip()
    if _ABAIKAN.match(t) or _LOGO_PASTI.match(t):
        return True
    if _HURUF_BERJARAK.fullmatch(t) and all(len(w) == 1 for w in t.split()):
        return True
    if _sampah_baku(blok, tinggi_gambar):
        return True
    if tinggi_gambar > 0 and blok["atas"] / tinggi_gambar < _BATAS_ATAS_RELATIF:
        if _LOGO_ATAS.match(t):
            return True
        if blok.get("tinggi", 0) >= 0.08 * tinggi_gambar:
            if _LOGO_DI_DALAM.search(t) or _mirip_tempo(t):
                return True
    return False


def _mirip_tempo(teks: str) -> bool:
    """Logo yang salah terbaca: TFMPO, TEMPQ, TEMFO, TEMPC, TRMPO (selisih ≤ 2 huruf)."""
    huruf = re.sub(r"[^A-Za-z0-9]", "", teks).upper()
    if not 4 <= len(huruf) <= 7:
        return False
    prev = list(range(6))
    for i, x in enumerate(huruf, 1):
        cur = [i]
        for j, y in enumerate("TEMPO", 1):
            cur.append(min(cur[-1] + 1, prev[j] + 1, prev[j - 1] + (x != y)))
        prev = cur
    return prev[-1] <= 2


def _layak(blok: dict, tinggi_gambar: float = 0.0) -> bool:
    t = blok["teks"].strip()
    if len(t) < 3:
        return False
    # Logo/tagline/teks baku; pola logo longgar hanya di bagian atas sampul agar
    # kata sah ("MOMEN", "NONTON") di bagian bawah tidak ikut terbuang.
    if _bukan_teks_sampul(blok, tinggi_gambar):
        return False

    # Blok dengan keyakinan sangat rendah umumnya adalah tekstur gambar yang
    # salah dikenali sebagai huruf, bukan teks sungguhan.
    if blok.get("yakin", 1.0) < 0.30:
        return False
    # Blok yang hampir seluruhnya angka/tanda baca (barcode, harga, nomor
    # halaman) bukan headline.
    huruf = sum(c.isalpha() for c in t)
    return huruf >= max(3, len(t) * 0.5)


def _rangkai(bagian) -> str:
    """Gabungkan baris headline menjadi satu kalimat.

    Headline yang dicetak beberapa baris kerap dipenggal dengan tanda hubung
    ("ANCANG-" / "ANCANG" / "JOKOWI"). Baris yang berakhir tanda hubung
    disambung tanpa spasi agar terbaca "ANCANG-ANCANG JOKOWI", bukan
    "ANCANG- ANCANG JOKOWI".
    """
    hasil = ""
    for teks in bagian:
        teks = (teks or "").strip()
        if not teks:
            continue
        if not hasil:
            hasil = teks
        elif hasil.endswith(("-", "‐", "‑")) and len(hasil) > 1 and hasil[-2].isalpha():
            hasil += teks  # "ANCANG-" + "ANCANG"
        elif (hasil.endswith((" -", " ‐", " ‑")) and len(hasil) > 2 and hasil[-3].isalpha()
              and teks[:1].isalpha()):
            hasil = hasil[:-2] + "-" + teks  # "GAYA -" + "GAYAAN"; "31 OKTOBER -" + "6 …" tetap berspasi
        else:
            hasil += " " + teks
    return hasil.strip()


def baca(path: Path, maks_baris: int = 6) -> dict:
    """Baca teks sampul dan tebak headline-nya.

    Mengembalikan dict berisi:
      tersedia  : bool
      headline  : tebakan headline (string kosong bila gagal)
      pendukung : teks lain yang terbaca, sebagai calon teks pendukung —
                  disusun menurut urutan baca tata letak (audit 6 Okt),
                  teks baku sampul disaring, dipotong 500 karakter
      semua     : seluruh blok teks terbaca, urut dari atas
      catatan   : keterangan bila ada yang perlu disampaikan ke pengguna
    Bila OCR berjalan, `pilih_headline` juga menambahkan antara lain
    `keyakinan` (rata-rata skor pembacaan baris judul, bukan peluang headline
    benar) dan `kandidat_headline` (pilihan judul di antarmuka).

    Tidak pernah melempar exception: kegagalan OCR tidak boleh menggagalkan
    proses unggah.
    """
    pembaca = _siapkan()
    if pembaca is None:
        return {"tersedia": False, "headline": "", "pendukung": "", "semua": [],
                "catatan": _alasan_gagal or "OCR tidak tersedia"}

    try:
        _, baca_fn = _MESIN[_mesin_aktif]
        blok = baca_fn(pembaca, Path(path))
    except Exception as e:
        return {"tersedia": False, "headline": "", "pendukung": "", "semua": [],
                "catatan": f"OCR gagal membaca gambar: {type(e).__name__}: {e}"}

    if not blok:
        return {"tersedia": True, "headline": "", "pendukung": "", "semua": [],
                "catatan": "Tidak ada teks yang terbaca pada gambar ini."}

    try:
        from PIL import Image
        tinggi_gambar = float(Image.open(path).size[1])
    except Exception:
        tinggi_gambar = 0.0

    return pilih_headline(blok, tinggi_gambar, maks_baris)


# ------------------------------------------------------- urutan baca
#
# Audit 6 Okt (docs/AUDIT_OCR_URUTAN_20261006.md): mengurutkan blok hanya
# berdasarkan posisi atas membuat teaser dua kolom saling menyelip
# ("YANG LENYAP DI · MENTERI BARU · MUSEUM BAHARI · DEMI PEMILU"), dan baris
# lanjutan headline berhuruf hias kerap terbuang karena skor pembacaannya
# rendah. Blok kini disusun menjadi baris lalu kelompok (kolom/paragraf).

def _lanjutan_layak(blok: dict, tinggi_gambar: float = 0.0) -> bool:
    """Baris lanjutan headline: boleh berkeyakinan rendah, asal mirip kata."""
    t = blok["teks"].strip()
    # Kata sangat pendek (GO, DI) diterima hanya bila hasil crop ulang sangat
    # yakin dan seluruh huruf kapital; fragmen pendek biasa tetap ditolak.
    pendek_yakin = (len(t) >= 2 and blok.get("yakin", 1.0) >= 0.75
                    and all(not c.isalpha() or c.isupper() for c in t))
    if (len(t) < 4 and not pendek_yakin) or blok.get("yakin", 1.0) < 0.15 or _bukan_teks_sampul(blok, tinggi_gambar):
        return False
    return sum(c.isalpha() for c in t) >= len(t.replace(" ", "")) * 0.6


def _tengah(b):
    return b["atas"] + b["tinggi"] / 2


def _bawah(b):
    return b.get("bawah", b["atas"] + b["tinggi"])


def _kanan(b):
    return b.get("kanan", b["kiri"])


def _tumpang_horizontal(a, b):
    lebar = min(_kanan(a) - a["kiri"], _kanan(b) - b["kiri"])
    tumpang = min(_kanan(a), _kanan(b)) - max(a["kiri"], b["kiri"])
    return tumpang / lebar if lebar > 0 else 1.0  # lebar tak diketahui: jangan menghalangi


def _susun_baris(bloks, celah_maks=1.2):
    """Kelompokkan blok sejajar menjadi baris; kolom berbeda tetap terpisah.

    `celah_maks` (kelipatan tinggi huruf) membatasi jarak horizontal antarblok
    dalam satu baris. EasyOCR sudah menggabungkan kata berdekatan menjadi satu
    blok, jadi celah lebar pada teks kecil hampir selalu batas kolom; huruf
    headline sering berjarak lebar sehingga memakai ambang lebih longgar.
    """
    baris = []
    for b in sorted(bloks, key=lambda x: (_tengah(x), x["kiri"])):
        for r in baris:
            h = min(b["tinggi"], r["tinggi"])
            jarak = max(b["kiri"] - r["kanan"], r["kiri"] - _kanan(b))
            # Kata sebaris bersebelahan; baris bertumpuk saling menimpa secara
            # horizontal (kotak huruf judul besar/miring bisa sangat tinggi
            # sehingga titik tengahnya berdekatan: "OBAT/PENCABUT/NYAWA").
            if (abs(_tengah(b) - r["tengah"]) <= 0.5 * h and jarak <= celah_maks * max(b["tinggi"], r["tinggi"])
                    and not any(_tumpang_horizontal(b, x) >= 0.3 for x in r["blok"])):
                r["blok"].append(b)
                r["kiri"], r["kanan"] = min(r["kiri"], b["kiri"]), max(r["kanan"], _kanan(b))
                r["atas"], r["bawah"] = min(r["atas"], b["atas"]), max(r["bawah"], _bawah(b))
                # Tinggi baris = blok tertinggi: potongan kecil yang terdeteksi
                # buruk ("mampu", 8 px) tidak boleh menentukan ukuran baris.
                r["tinggi"] = max(r["tinggi"], b["tinggi"])
                r["tengah"] = (r["atas"] + r["bawah"]) / 2
                break
        else:
            baris.append({"blok": [b], "kiri": b["kiri"], "kanan": _kanan(b), "atas": b["atas"],
                          "bawah": _bawah(b), "tinggi": b["tinggi"], "tengah": _tengah(b)})
    for r in baris:
        r["blok"].sort(key=lambda x: x["kiri"])
        r["teks"] = _rangkai(x["teks"] for x in r["blok"])
    return sorted(baris, key=lambda r: (r["atas"], r["kiri"]))


def _susun_kelompok(baris):
    """Baris bertumpuk dengan ukuran huruf mirip menjadi satu kelompok (kolom/paragraf)."""
    kelompok = []
    for r in baris:
        for k in kelompok:
            akhir = k["baris"][-1]
            celah = r["atas"] - akhir["bawah"]
            mirip = 0.6 <= r["tinggi"] / max(akhir["tinggi"], 1e-6) <= 1.6
            if mirip and -0.5 * r["tinggi"] <= celah <= 1.2 * max(r["tinggi"], akhir["tinggi"]) \
                    and _tumpang_horizontal(r, akhir) >= 0.3:
                k["baris"].append(r)
                k["kiri"], k["kanan"] = min(k["kiri"], r["kiri"]), max(k["kanan"], r["kanan"])
                break
        else:
            kelompok.append({"baris": [r], "kiri": r["kiri"], "kanan": r["kanan"], "atas": r["atas"],
                             "tinggi": r["tinggi"]})
    # Paragraf rata kiri-kanan berspasi lebar kerap dipecah EasyOCR menjadi
    # beberapa blok; potongan yang tertinggal sebagai kelompok satu baris
    # dikembalikan ke baris sejajar bila letaknya di dalam rentang kolom itu.
    for k in [k for k in kelompok if len(k["baris"]) == 1]:
        r = k["baris"][0]
        for lain in kelompok:
            if lain is k or len(lain["baris"]) < 2:
                continue
            h = r["tinggi"]
            if lain["kiri"] - h <= r["kiri"] and _kanan(r) <= lain["kanan"] + h:
                tujuan = next((x for x in lain["baris"]
                               if abs(x["tengah"] - r["tengah"]) <= 0.5 * min(h, x["tinggi"])), None)
                if tujuan:
                    tujuan["blok"] = sorted(tujuan["blok"] + r["blok"], key=lambda x: x["kiri"])
                    tujuan["teks"] = _rangkai(x["teks"] for x in tujuan["blok"])
                    tujuan["kiri"], tujuan["kanan"] = min(tujuan["kiri"], r["kiri"]), max(tujuan["kanan"], r["kanan"])
                    k["baris"] = []
                    break
    kelompok = [k for k in kelompok if k["baris"]]
    for k in kelompok:
        k["bawah"] = k["baris"][-1]["bawah"]
        k["teks"] = _rangkai(r["teks"] for r in k["baris"])
    return kelompok


def _urutan_baca(kelompok, headline_bawah=None, tinggi_gambar=0.0):
    """Deck tepat di bawah headline lebih dulu, lalu atas→bawah dan kiri→kanan per pita."""
    sisa = sorted(kelompok, key=lambda k: k["atas"])
    hasil = []
    if headline_bawah is not None:
        batas = 0.15 * tinggi_gambar if tinggi_gambar else float("inf")
        bawah = [k for k in sisa if -k["tinggi"] <= k["atas"] - headline_bawah <= batas]
        if bawah:
            deck = min(bawah, key=lambda k: k["atas"] - headline_bawah)
            hasil.append(deck)
            sisa.remove(deck)
    while sisa:
        awal = sisa[0]
        pita = [k for k in sisa if k["atas"] - awal["atas"] <= awal["tinggi"]]
        pita.sort(key=lambda k: k["kiri"])
        hasil.extend(pita)
        sisa = [k for k in sisa if k not in pita]
    return hasil


def _gabung_kelompok(kelompok) -> str:
    hasil = ""
    for t in (k["teks"].strip().rstrip(";") for k in kelompok if k["teks"].strip()):
        if not hasil:
            hasil = t
        else:  # tanpa ".;" / "?;" ganda
            hasil += (" " if hasil.endswith((".", "?", "!", ":")) else "; ") + t
    return hasil


def _potong(teks: str, n: int = 500) -> str:
    """Potong di batas kata, bukan di tengah kata."""
    if len(teks) <= n:
        return teks
    bagian = teks[:n]
    return bagian.rsplit(" ", 1)[0] if " " in bagian else bagian


def pilih_headline(blok, tinggi_gambar=0.0, maks_baris=6):
    """Pure selector: extraction scores are not headline correctness probabilities."""
    # Normalisasi masukan agar blok tidak lengkap tidak membuat crash (audit 6 Okt).
    tinggi_gambar = float(tinggi_gambar or 0.0)
    blok = [dict(b, teks=str(b.get("teks") or ""),
                 yakin=float(b["yakin"]) if b.get("yakin") is not None else 1.0)
            for b in blok if str(b.get("teks") or "").strip()]
    kandidat = [b for b in blok if _layak(b, tinggi_gambar)]
    if not kandidat:
        semua = [b["teks"] for b in sorted(blok, key=lambda b: b["atas"])]
        bersih = [b for b in blok if not _bukan_teks_sampul(b, tinggi_gambar)]
        pendukung = _gabung_kelompok(_urutan_baca(_susun_kelompok(_susun_baris(bersih, celah_maks=0.6)),
                                                  None, tinggi_gambar))
        return {"tersedia": True, "headline": "", "pendukung": _potong(pendukung),
                "semua": semua, "keyakinan": None, "skor_ocr": None,
                "status_headline": "perlu_pemeriksaan", "blok_mentah": blok, "kandidat_headline": [],
                "alasan_selector": "Tidak ada blok yang menyerupai headline.",
                "catatan": "Teks terbaca, tetapi tidak ada yang menyerupai headline."}

    # Headline dipilih dengan skor gabungan, bukan tinggi semata.
    #
    # Memakai tinggi saja gagal pada sampul yang logonya tertutup objek foto:
    # pada "ANCANG-ANCANG JOKOWI" sisa logo terbaca "TEN" setinggi 13,5% tinggi
    # gambar — hampir tiga kali headline aslinya (5,0%) — sehingga headline
    # yang benar tersingkir seluruhnya oleh ambang relatif.
    #
    # Tiga faktor yang dipakai:
    #   tinggi     : headline memang teks terbesar (bobot terbesar)
    #   posisi     : headline Tempo hampir selalu di bawah pertengahan sampul
    #   keyakinan  : blok yang dibaca ragu-ragu jarang merupakan headline
    #   panjang    : headline itu ringkas; paragraf deskripsi panjang meski
    #                tinggi barisnya bisa menyamai huruf headline
    def skor_blok(b: dict) -> float:
        s = b["tinggi"]
        if tinggi_gambar > 0:
            relatif = b["atas"] / tinggi_gambar
            # Turunkan blok di bagian atas (wilayah logo dan kicker rubrik),
            # naikkan sedikit blok di paruh bawah.
            if relatif < _BATAS_ATAS_RELATIF:
                s *= 0.45
            elif relatif > 0.5:
                s *= 1.15

        # Blok panjang hampir pasti paragraf pendukung, bukan headline. Tanpa
        # penalti ini, satu baris paragraf selebar sampul dapat mengalahkan
        # headline yang hurufnya jauh lebih besar, karena tinggi baris
        # keduanya kebetulan mirip.
        n = len(b["teks"])
        if n > 45:
            s *= 0.35
        elif n > 28:
            s *= 0.65

        return s * (0.6 + 0.4 * b.get("yakin", 1.0))

    utama = max(kandidat, key=skor_blok)

    # Headline kerap terpecah beberapa baris ("ANCANG-" / "ANCANG" / "JOKOWI").
    # Baris lain digabung bila tingginya sebanding DAN letaknya berdekatan
    # secara vertikal dengan baris utama — kedekatan mencegah teks lain yang
    # kebetulan seukuran ikut tertarik.
    # Sambung berantai: blok seukuran yang menempel di atas/bawah (atau di
    # sebelah pada baris yang sama) dan sekolom dengan headline. Baris
    # lanjutan berhuruf hias boleh berkeyakinan rendah (`_lanjutan_layak`).
    ambang_tinggi = utama["tinggi"] * _RASIO_TINGGI_INTI
    # Blok berkeyakinan rendah hanya diterima bila seukuran judul: kicker kecil
    # di bawah logo ("5uth!", 0,70× tinggi judul) tidak boleh ikut tersambung.
    kolam = [b for b in blok if b is not utama and b["tinggi"] >= ambang_tinggi
             and (_layak(b, tinggi_gambar)
                  or (_lanjutan_layak(b, tinggi_gambar) and b["tinggi"] >= 0.85 * utama["tinggi"]))]
    grup = [utama]
    berubah = True
    while berubah and len(grup) < maks_baris * 2:
        berubah = False
        atas, bawah = min(b["atas"] for b in grup), max(_bawah(b) for b in grup)
        kiri, kanan = min(b["kiri"] for b in grup), max(_kanan(b) for b in grup)
        rentang = {"kiri": kiri, "kanan": kanan}
        for b in list(kolam):
            dekat = (-0.5 * b["tinggi"] <= b["atas"] - bawah <= 0.8 * utama["tinggi"]
                     or -0.5 * b["tinggi"] <= atas - _bawah(b) <= 0.8 * utama["tinggi"]
                     # baris di tengah rentang grup (leading rapat: "KORUPSI/BANsOS/KUBU/BANTENG")
                     or (b["atas"] >= atas - 0.5 * b["tinggi"] and _bawah(b) <= bawah + 0.5 * b["tinggi"]))
            sebaris = any(abs(_tengah(b) - _tengah(g)) <= 0.5 * min(b["tinggi"], g["tinggi"])
                          and max(b["kiri"] - _kanan(g), g["kiri"] - _kanan(b)) <= 1.5 * g["tinggi"] for g in grup)
            if sebaris or (dekat and _tumpang_horizontal(b, rentang) >= 0.3):
                grup.append(b); kolam.remove(b); berubah = True

    # Subjudul yang merupakan bagian headline kadang jauh lebih kecil daripada
    # kata utama. Tambahkan hanya blok kapital yang menempel LANGSUNG pada inti;
    # jangan iteratif, agar paragraf deck tidak ikut terseret sebagai rantai.
    satelit = []
    for b in blok:
        huruf = [c for c in b["teks"] if c.isalpha()]
        rasio = b["tinggi"] / max(utama["tinggi"], 1e-6)
        kapital = huruf and all(c.isupper() for c in huruf)
        if b in grup or not (_RASIO_TINGGI_LANJUTAN <= rasio < 0.59):
            continue
        if not kapital or len(b["teks"]) > 28 or not _layak(b, tinggi_gambar):
            continue
        # Filter deck liputan/subheadline investigasi yang bukan bagian judul
        if re.search(r"PENELUSURAN\s+TEMPO|LAPORAN\s+TEMPO|INVESTIGASI\s+TEMPO", b["teks"], re.IGNORECASE):
            continue
        for g in grup:
            dekat = (-0.35 * b["tinggi"] <= b["atas"] - _bawah(g) <= 0.45 * utama["tinggi"]
                     or -0.35 * b["tinggi"] <= g["atas"] - _bawah(b) <= 0.45 * utama["tinggi"])
            if dekat and _tumpang_horizontal(b, g) >= 0.3:
                satelit.append(b)
                break
    grup.extend(satelit)
    baris_hl = _susun_baris(grup)[:maks_baris]
    baris_headline = [b for r in baris_hl for b in r["blok"]]
    if utama not in baris_headline:
        baris_hl, baris_headline = _susun_baris([utama]), [utama]

    headline = _rangkai(r["teks"] for r in baris_hl)
    ragu = [b["teks"] for b in baris_headline if b.get("yakin", 1.0) < 0.30]

    dipakai = {id(b) for b in baris_headline}
    sisa = [b for b in kandidat if id(b) not in dipakai]
    kelompok = _susun_kelompok(_susun_baris(sisa, celah_maks=0.6))
    pendukung = _gabung_kelompok(_urutan_baca(kelompok, max(_bawah(b) for b in baris_headline), tinggi_gambar))

    yakin_rata = sum(b["yakin"] for b in baris_headline) / len(baris_headline)
    catatan = ""
    if yakin_rata < 0.5:
        catatan = ("Keyakinan pembacaan rendah — periksa dan perbaiki teks "
                   "sebelum menganalisis.")
    if ragu:
        catatan = (catatan + " " if catatan else "") + (
            "Sebagian baris judul terbaca dengan keyakinan rendah (" + ", ".join(ragu)
            + ") — periksa ejaannya.")

    return {
        "tersedia": True,
        "headline": headline,
        "pendukung": _potong(pendukung),
        "semua": [b["teks"] for b in sorted(blok, key=lambda b: b["atas"])],
        "keyakinan": round(yakin_rata, 3),
        "skor_ocr": round(yakin_rata, 3),
        "status_headline": "perlu_pemeriksaan",
        "blok_mentah": blok,
        "kandidat_headline": [headline] + list(dict.fromkeys(b["teks"] for b in sorted(kandidat,key=skor_blok,reverse=True) if b not in baris_headline)),
        "alasan_selector": "Ukuran, posisi, panjang dan skor pembacaan; bukan peluang headline benar.",
        "catatan": catatan,
    }
