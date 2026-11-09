# SALINAN BEKU ocr_headline.py sebelum audit urutan 2026-10-06 — hanya untuk pembanding di audit_ocr_urutan.py. Jangan dipakai aplikasi.
#!/usr/bin/env python3
"""Pembacaan teks sampul otomatis untuk mengisi kolom headline (revisi R1).

Dosen mencatat: "user masih harus ngeinput ulang tuh teks, nah disaranin kalo
bisa itu kesalin otomatis karena user ga bakalan punya waktu buat ngetik
ulang". Modul ini membaca teks dari gambar sampul lalu menebak mana yang
merupakan headline.

Catatan penting soal peran OCR di sini:
hasil OCR **tidak** dipakai sebagai kebenaran. Ia hanya mengisi kolom di
antarmuka, dan pengguna tetap dapat menyuntingnya sebelum analisis dijalankan.
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
    hasil = []
    for kotak, teks, yakin in pembaca.readtext(str(path), detail=1, paragraph=False):
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
_ABAIKAN = re.compile(
    r"^(TEMPO|ENAK\s+DIBACA.*|MAJALAH\s+BERITA.*|RP\s*[\d.,]+|"
    r"EDISI.*|ISSN.*|WWW\..*|H\.?\s*\d+|\d+\s*[-–]\s*\d+.*|"
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


def _layak(blok: dict, tinggi_gambar: float = 0.0) -> bool:
    t = blok["teks"].strip()
    if len(t) < 3:
        return False
    if _ABAIKAN.match(t) or _LOGO_PASTI.match(t):
        return False

    # Pola logo yang longgar hanya berlaku di bagian atas sampul, agar kata
    # Indonesia yang sah ("MOMEN", "NONTON") tidak ikut terbuang bila muncul
    # sebagai headline di bagian bawah.
    if tinggi_gambar > 0:
        relatif = blok["atas"] / tinggi_gambar
        if relatif < _BATAS_ATAS_RELATIF and _LOGO_ATAS.match(t):
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
        elif hasil.endswith(("-", "‐", "‑")):
            hasil += teks
        else:
            hasil += " " + teks
    return hasil.strip()


def baca(path: Path, maks_baris: int = 4) -> dict:
    """Baca teks sampul dan tebak headline-nya.

    Mengembalikan dict berisi:
      tersedia  : bool
      headline  : tebakan headline (string kosong bila gagal)
      pendukung : teks lain yang terbaca, sebagai calon teks pendukung
      semua     : seluruh blok teks terbaca, urut dari atas
      catatan   : keterangan bila ada yang perlu disampaikan ke pengguna

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


def pilih_headline(blok, tinggi_gambar=0.0, maks_baris=4):
    """Pure selector: extraction scores are not headline correctness probabilities."""
    kandidat = [b for b in blok if _layak(b, tinggi_gambar)]
    if not kandidat:
        semua = [b["teks"] for b in sorted(blok, key=lambda b: b["atas"])]
        return {"tersedia": True, "headline": "", "pendukung": " ".join(semua),
                "semua": semua,
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
    ambang_tinggi = utama["tinggi"] * 0.62
    jangkauan = max(utama["tinggi"] * 3.5, tinggi_gambar * 0.10 if tinggi_gambar else 0)

    baris_headline = [
        b for b in kandidat
        if b["tinggi"] >= ambang_tinggi and abs(b["atas"] - utama["atas"]) <= jangkauan
    ]
    baris_headline.sort(key=lambda b: (b["atas"], b["kiri"]))
    baris_headline = baris_headline[:maks_baris]
    if utama not in baris_headline:
        baris_headline = [utama]

    headline = _rangkai(b["teks"] for b in baris_headline)

    dipakai = {id(b) for b in baris_headline}
    sisa = [b for b in kandidat if id(b) not in dipakai]
    sisa.sort(key=lambda b: b["atas"])
    pendukung = _rangkai(b["teks"] for b in sisa)

    yakin_rata = sum(b["yakin"] for b in baris_headline) / len(baris_headline)
    catatan = ""
    if yakin_rata < 0.5:
        catatan = ("Keyakinan pembacaan rendah — periksa dan perbaiki teks "
                   "sebelum menganalisis.")

    return {
        "tersedia": True,
        "headline": headline,
        "pendukung": pendukung[:500],
        "semua": [b["teks"] for b in sorted(blok, key=lambda b: b["atas"])],
        "keyakinan": round(yakin_rata, 3),
        "skor_ocr": round(yakin_rata, 3),
        "status_headline": "perlu_pemeriksaan",
        "blok_mentah": blok,
        "kandidat_headline": [headline] + list(dict.fromkeys(b["teks"] for b in sorted(kandidat,key=skor_blok,reverse=True) if b not in baris_headline)),
        "alasan_selector": "Ukuran, posisi, panjang dan skor pembacaan; bukan peluang headline benar.",
        "catatan": catatan,
    }
