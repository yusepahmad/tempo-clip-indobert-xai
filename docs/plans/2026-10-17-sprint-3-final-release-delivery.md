# Sprint 3 — Final Release & Delivery Application

**Tanggal:** 2026-10-17  
**Status:** done  

## Tujuan
Membangun paket rilis final aplikasi (`final_release_20261017`) dari source canonical `DEMO_XAI_745_FULL/` yang siap digunakan dan didistribusikan dalam bentuk arsip ZIP portabel, lengkap dengan manifest integritas file SHA-256, panduan pengguna, dokumentasi batasan masalah ilmiah, dan laporan verifikasi release.

## Ruang Lingkup
- **File/modul yang dibuat dan disentuh:**
  - `docs/plans/2026-10-17-sprint-3-final-release-delivery.md` (dokumen plan ini)
  - `delivery/final_release_20261017/` (direktori rilis baru)
  - `delivery/final_release_20261017/build_bundle.py` (script build deterministik dan pemindaian keamanan)
  - `delivery/final_release_20261017/tempo-final-release-v1-linux.zip` (arsip rilis utama)
  - `delivery/final_release_20261017/tempo-final-release-v1-linux.zip.sha256` (checksum arsip)
  - `delivery/final_release_20261017/bundle_verification.json` (laporan audit integritas paket)
  - `docs/SPRINT_ROADMAP.md` (pembaruan status sprint dan roadmap)
  - `CHANGELOG.md` (pencatatan entri rilis final)
- **Yang eksplisit TIDAK disentuh:**
  - Snapshot rilis historis di `delivery/week34_clip_indobert_20261012/` dan `delivery/archive/` (tetap immutable).
  - Dataset `03_data/DATASET_740_TASK2_DOMAIN.csv` dan seluruh file citra sampul di `05_gambar/`.

## Langkah
1. Tulis plan ke `docs/plans/2026-10-17-sprint-3-final-release-delivery.md`.
2. Jalankan test regresi menyeluruh pada source canonical `DEMO_XAI_745_FULL/`:
   - Unit tests OCR (`test_ocr_urutan.py`)
   - Backend API & Batch tests (`test_audit_backend.py`)
   - JavaScript R5 heatmap & UI state tests (`test_r5_heatmap.js`, `test_loading_ui.js`)
   - Pemeriksaan delivery model (`check_delivery.py`)
3. Buat folder release baru di `delivery/final_release_20261017/`.
4. Siapkan script packaging otomatis `delivery/final_release_20261017/build_bundle.py`:
   - Memfilter seluruh cache lokal (`__pycache__`, `.cache`, `_cache`, `_jobs`, `_semantic_cache`, `.git`, `venv`).
   - Melakukan security scan untuk memastikan tidak ada token/credential/kunci privat (`AIza`, `hf_`, `sk-`, `.env`, `.pem`, `.key`).
   - Membuat `DELIVERY_MANIFEST.json` berisi SHA-256 dari seluruh file yang dimasukkan ke paket.
   - Mengompresi file ke dalam ZIP deterministik berstempel waktu seragam.
   - Melakukan pengujian integritas arsip ZIP (`testzip()`) dan verifikasi ulang kecocokan SHA-256 setiap file di dalam ZIP.
5. Jalankan `build_bundle.py` untuk mengemas dan memvalidasi `tempo-final-release-v1-linux.zip`.
6. Sinkronkan dokumen status di `docs/SPRINT_ROADMAP.md` dan catat rilis pada `CHANGELOG.md`.

## Risiko & Asumsi
- Lingkungan `venv/` tidak disertakan di dalam ZIP untuk menjaga ukuran file tetap bersih dan portabel; pengguna menjalankan instalasi dependensi menggunakan `requirements.txt` atau launcher yang disediakan.
- Bobot model publik (CLIP, IndoBERT, EasyOCR) diunduh otomatis pada runtime pertama kali bila belum tersedia di cache lokal mesin target.
- Batasan masalah dan gap target akademis terdokumentasi secara transparan di dalam dokumen rilis dan panduan pengguna.

## Verifikasi
- Semua test regresi lokal berstatus lulus.
- Pemindaian kredensial mengonfirmasi nol secret leakage.
- Uji integritas ZIP `testzip()` menghasilkan `None` (tidak ada error).
- Seluruh checksum SHA-256 file di dalam ZIP 100% cocok dengan manifest.
