# Audit OCR: Urutan Kata Headline dan Teks Pendukung

**Tanggal:** 2026-10-06
**Status:** done (2026-10-06, termasuk lanjutan)

## Tujuan
User melihat hasil OCR "salah penataan kata". Audit ini memisahkan dua jenis kesalahan — **salah baca** (huruf/kata keliru, ranah EasyOCR) dan **salah urut/penggabungan** (kata benar tetapi urutan atau pengelompokan salah, ranah `ocr_headline.py`) — mengukurnya pada set yang tidak dipakai menyetel selector, lalu memperbaiki penyusunan urutan bila terbukti menjadi sumber kesalahan.

## Dugaan awal dari membaca kode (`02_web_demo/ocr_headline.py`)
1. Baris headline diurutkan `(atas, kiri)`: kotak kata pada satu baris visual dengan `atas` berbeda beberapa piksel dapat tertukar urutan kiri-kanannya.
2. Teks pendukung diurutkan `atas` saja: teks dari kolom/kotak berbeda (teaser kiri dan kanan) saling menyelip, dan kata dalam satu baris tidak diurutkan kiri-kanan.
3. Penggabungan baris headline memakai kedekatan vertikal tanpa memperhatikan kolom.

## Ruang Lingkup
- Baru `01_notebook/audit_ocr_urutan.py`: jalankan EasyOCR (mesin produksi) sekali per gambar, **simpan blok mentah** ke cache bukti, lalu evaluasi selector lama vs kandidat baru secara offline pada blok yang sama.
- Set data:
  - **Dev:** 30 sampul diagnosis lama (`ocr_diagnosis.json`, blok sudah tersimpan) — boleh dipakai merancang perbaikan.
  - **Uji:** 100 sampul acak lain (seed 42, di luar 30 dev) — hanya untuk pengukuran; tidak dipakai menyetel.
  - Tiga foto dosen (`06_gambar_revisi/`) dicatat terpisah (tanpa ground truth pendukung).
- Kebenaran: `headline_verified`, `supporting_text_verified` dari dataset (tidak diubah).
- Metrik (normalisasi huruf besar/spasi/tanda baca ringan):
  - headline: exact, CER, **bag-of-words sama tetapi urutan beda** (indikator salah urut), word recall;
  - pendukung: word recall/precision terhadap kebenaran, **urutan** = Kendall tau / LCS rasio atas kata yang cocok;
  - kategori kesalahan per sampel: tepat, salah urut, salah baca, salah pilih blok (headline mengambil teks lain), kosong.
- Kandidat perbaikan (bila audit menunjukkan salah urut nyata): pengelompokan baris berdasarkan tumpang-tindih vertikal (pusat y dalam toleransi relatif tinggi huruf), urut baris atas→bawah dan kata kiri→kanan; untuk pendukung, pengelompokan kolom/kotak sederhana sebelum pengurutan baris.
- Output: `04_hasil_eksperimen/revisi_week3/ocr_audit_urutan_20261006.json` (+ cache blok `ocr_audit_blok_20261006.json`) dan laporan `docs/AUDIT_OCR_URUTAN_20261006.md`.
- Bila perbaikan diterapkan: `02_web_demo/ocr_headline.py` + regresi baru; restart `tempo-ui` (bind 0.0.0.0).
- TIDAK: mengganti mesin OCR, mengubah dataset/label, menaikkan angka dengan menyetel di set uji.

## Langkah
1. Tulis dan jalankan skrip audit (OCR 100 + replay 30 dev + 3 foto dosen), ukur selector produksi.
2. Klasifikasikan kesalahan; tunjukkan contoh nyata salah urut.
3. Rancang perbaikan pada set dev; ukur di set uji tanpa penyetelan ulang. Terapkan hanya bila set uji membaik dan tidak ada regresi exact headline.
4. Regresi, smoke browser terdampak (OCR), dokumen (laporan audit, BATASAN/STATUS OCR), CHANGELOG.

## Perubahan di tengah jalan (dicatat sebelum dilanjutkan)
- Pemeriksaan per sampel pada set uji menemukan tiga pola kesalahan nyata yang belum terlihat di dev: potongan paragraf rata kiri-kanan terlempar (tinggi baris diambil dari blok kecil), logo "TEMPO" salah baca (TFMPO/TEMPQ/TEMFO/TEMPC/TRMPO) terpilih sebagai judul, dan kolom bercelah sempit tergabung sebaris. Ketiganya diperbaiki, sehingga **set uji tidak lagi independen**.
- Karena itu ditambah **set validasi 60 sampul acak (seed 7) di luar dev dan uji** yang dibuka hanya setelah rancangan dibekukan; angka utama laporan berasal dari set ini. Angka set uji tetap dilaporkan dengan label "terkontaminasi".
- Konvensi transkripsi pendukung anotator campuran (deck lebih dulu vs teaser lebih dulu); urutan antar-kelompok mengikuti deck lebih dulu (dev + alasan teks pendukung dipotong 500 karakter untuk model). Skor urutan dilaporkan dengan catatan ini.

## Risiko & Asumsi
- `supporting_text_verified` adalah transkripsi anotator yang mungkin hanya memuat sebagian teks sampul; precision pendukung rendah bukan otomatis kesalahan. Fokus pada recall dan urutan kata yang cocok.
- EasyOCR di CPU ±3–10 detik per gambar; 100 gambar ±10–15 menit, dijalankan terpisah dari server (thread dibatasi).
- Salah baca huruf tidak diperbaiki oleh penyusunan urutan; dilaporkan apa adanya.

## Verifikasi
- Angka sebelum/sesudah pada set uji yang sama (blok sama), bukan set dev.
- Contoh sebelum/sesudah untuk foto dosen dan beberapa sampul.
- Regresi lama `test_week3_regressions.py` (selector) tetap lulus.

## Hasil (2026-10-06)
- Laporan: `docs/AUDIT_OCR_URUTAN_20261006.md`; bukti `ocr_audit_urutan_20261006.json`, blok `ocr_audit_blok_20261006.json`.
- Akar masalah: teks pendukung diurutkan menurut posisi atas saja (teaser antarkolom menyelip); judul terpotong karena baris lanjutan berkeyakinan rendah dibuang; logo salah baca terpilih sebagai judul. Tidak ditemukan kata judul yang tertukar.
- Validasi independen 60: pendukung urutan sempurna 13→35/56, skor urutan 0,768→0,877, judul tepat 41→43 (5 naik, 3 turun), salah pilih blok 12→8. 13 penurunan urutan seluruhnya karena konvensi deck. Tiga regresi judul dicatat, tidak diperbaiki agar validasi tetap independen.
- Kode: `ocr_headline.py` (urutan baca berbasis tata letak, sambung judul berantai, filter logo mirip TEMPO dan tagline berjarak). Salinan beku sebelum audit `01_notebook/ocr_selector_baseline_20261006.py`. Regresi baru `test_ocr_urutan.py` (8, gagal semua terhadap selector lama) + seluruh regresi lama lulus; smoke `browser_smoke_20261006_ocr.json` 83/83. Server `tempo-ui` direstart (0.0.0.0:7861).

## Lanjutan: tiga regresi judul (atas permintaan user)
- **Akar masalah:** (1) kicker kecil berkeyakinan sangat rendah di bawah logo ("5uth!", "Sutl:", tinggi 0,70× judul) tersambung lewat jalur baris lanjutan; (2) pada judul berleading rapat, baris di tengah rentang grup ("KUBU") tidak tersambung karena aturan hanya memeriksa tepi atas/bawah grup.
- **Perbaikan:** blok berkeyakinan < 0,30 hanya boleh tersambung bila tingginya ≥ 0,85× judul utama; blok yang berada di dalam rentang vertikal grup dan sekolom ikut tersambung. Regresi ditambah di `test_ocr_urutan.py`.
- **Verifikasi:** set validasi pertama kini terkontaminasi; dibuat **set validasi kedua 60 sampul (seed 11) di luar dev/uji/validasi**, dibuka setelah kode dibekukan. Dilaporkan: selector awal (baseline) vs versi audit pertama vs versi lanjutan pada blok yang sama. Diterima bila tidak memburuk dibanding versi audit pertama di validasi kedua.

### Hasil lanjutan (2026-10-06)
- Poin 1 (kicker kecil, ambang 0,85×) dan 2 (baris tengah grup) memperbaiki ketiga regresi; validasi kedua (beku): judul 38/60 = versi audit pertama, 0 regresi dibanding sebelum audit.
- Setelah validasi kedua dibuka (terkontaminasi, dicatat): syarat sebaris = bersebelahan, batas baris judul 6. Uji ambang ukuran 0,55 **dibatalkan** (3 regresi). Hasil akhir validasi kedua: judul 39/60, CER 0,260→0,290 karena deck terserap pada judul yang sudah salah — trade-off dilaporkan di `docs/AUDIT_OCR_URUTAN_20261006.md`.
- Regresi `test_ocr_urutan.py` 12 test + seluruh regresi lama lulus; smoke `browser_smoke_20261006_ocr2.json` 83/83; server `tempo-ui` direstart (0.0.0.0:7861).
- **Keputusan user (2026-10-06):** batas baris judul 6 dipertahankan meski CER judul naik pada judul yang sudah salah pilih blok.
