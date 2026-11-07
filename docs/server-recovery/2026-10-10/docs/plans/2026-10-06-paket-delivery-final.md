# Paket Delivery Final Week 3 (Langkah 5)

**Tanggal:** 2026-10-06
**Status:** done (2026-10-06)

Langkah 5 [plan induk](2026-10-06-lanjutan-week3-server.md). User: "siapkan untuk ready delivery dan saya download zip nya".

## Tujuan
ZIP delivery yang cocok dengan source terbaru, terbukti berjalan dari instalasi bersih (Linux), dengan manifest SHA256, dokumen yang sinkron, dan tautan unduh untuk user.

## Ruang Lingkup
1. **Sinkron dokumen** (sub-agent, ditinjau): `docs/STATUS_REVISI_20261006.md`, `TEKS_DELIVERY.md`, `00_BACA_DULU.md`, `MULAI_DARI_SINI.md`, `docs/DELIVERY_WEEK_3.md` — tambah perubahan malam 6 Okt (narasi ringkasan/penjelasan, audit OCR urutan + sampah teks baku, perbaikan unggah berkas sama/judul, audit kode FE/BE/modul, pembatalan analisis, batas sumber daya) dan status paket "delivery revisi Week 3 (baseline)" tanpa klaim seluruh sasaran riset selesai.
2. **Lock dependensi**: `requirements-lock-linux.txt` dari `pip freeze` venv server yang lulus semua test (requirements.txt tetap batas bawah).
3. **Build** `01_notebook/bangun_paket_delivery.py` → `/home/yusep/workspace/learn/dist/TEMPO_XAI_DELIVERY_WEEK3_20261006.zip` (+ `.sha256`), isi folder `DEMO_XAI_745_FULL/`:
   - dikecualikan: `venv/`, `__pycache__/`, `02_web_demo/_cache/`, `02_web_demo/_jobs/`, `.pytest_cache/`, `SERVER_HANDOFF_MANIFEST.json` (manifest handoff lama, tidak lagi cocok), folder screenshot smoke selain run final `browser_smoke_20261006_audit/` (JSON semua run tetap disertakan);
   - ditambahkan: `DELIVERY_MANIFEST.json` (SHA256 + ukuran tiap berkas, daftar pengecualian).
   - Arsip handoff `TEMPO_SERVER_HANDOFF_20261006.zip` tidak ditimpa.
4. **Verifikasi**: CRC ZIP (`testzip`), hash tiap berkas = manifest = source; ekstrak ke folder bersih; venv baru Python 3.10 + `requirements.txt` + verifikasi/browser; jalankan `jalankan_linux.sh` (127.0.0.1:7860); seluruh test Python/JS/frontend, `verify_r5_http.py`, `verify_week3_http.py` (staging) dan smoke browser terhadap salinan bersih.
5. **Unduh**: server HTTP statis sementara (tmux `tempo-unduh`, port 8853, hanya folder `dist/`) + alternatif `scp`; dimatikan setelah user selesai mengunduh.

## Risiko & Asumsi
- Windows clean install tidak dapat diuji di server ini (tidak ada mesin Windows); dicatat sebagai batas.
- Instalasi bersih mengunduh paket pip dan model; butuh internet (tersedia).
- Server unduh terbuka di jaringan selama dibutuhkan; hanya melayani ZIP dan checksum.

## Verifikasi
Lihat langkah 4; hasil dicatat di bagian Hasil.

## Hasil (2026-10-06)
- Dokumen delivery disinkronkan (STATUS, TEKS_DELIVERY, 00_BACA_DULU, MULAI_DARI_SINI, DELIVERY_WEEK_3); `requirements-lock-linux.txt` dibuat dari venv server yang lulus semua test.
- `01_notebook/bangun_paket_delivery.py` → `dist/TEMPO_XAI_DELIVERY_WEEK3_20261006.zip` (±114 MB, 1054 berkas termasuk `DELIVERY_MANIFEST.json`); CRC dan hash isi = manifest = source lulus. Izin eksekusi `jalankan_linux.sh` kini ikut tersimpan (di source dan ZIP handoff lama berkas ini tidak executable).
- **Uji instalasi bersih (Linux):** ZIP diekstrak ke folder baru; venv baru Python 3.10.12 dibuat dengan `uv` (paket sistem `python3.10-venv` tidak ada di server ini; `python3.10 -m venv` standar tetap dipakai di panduan) lalu `pip install` torch CPU + `requirements.txt` + verifikasi + browser — tanpa konflik, versi sama dengan server (torch 2.14.1+cpu, transformers 5.18.0). `./jalankan_linux.sh` menyalakan aplikasi di 127.0.0.1:7860. Di salinan bersih: 70 test Python, 4 JS, 13 frontend, `verify_r5_http.py`, `verify_week3_http.py` (staging) lulus; smoke browser **94/94** (`04_hasil_eksperimen/revisi_week3/browser_smoke_paket_bersih.json`).
- Batas: cache model Hugging Face/EasyOCR di home user server sudah ada sehingga unduhan model pertama tidak teruji ulang; Windows clean install tidak diuji (tidak ada mesin Windows di server).
- ZIP dibangun ulang setelah hasil ini dicatat; berkas kode/test identik dengan ZIP yang diuji (hanya dokumen/bukti yang berbeda — diverifikasi otomatis).
