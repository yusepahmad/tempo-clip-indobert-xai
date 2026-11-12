# E42 Production Launcher Fix & Source Code Documentation

**Tanggal:** 2026-11-13
**Status:** done

## Tujuan
Memperbaiki default Linux/Gunicorn ke backend e42-tail-grid versi e42-tail-grid-v1 dan menghasilkan referensi HTML implementasi aktual beserta screenshot source yang dapat diverifikasi.

## Masalah & Akar Penyebab Awal
Folder utama lokal masih snapshot demo Oktober: launcher Linux/Windows memilih baseline dan file serving E42 yang disebut pengguna belum ada. GitHub HEAD teramati e0a977ece2f77ae95325fd164ca0d58a148ec5d8. Perlu audit source mutakhir sebelum memilih perubahan minimal.

## Ruang Lingkup
- Salinan audit terisolasi repository GitHub di work/e42-production; serving E42 yang diperlukan di DEMO_XAI_745_FULL/02_web_demo, launcher Linux/Windows, dependensi/deployment aktif, serta pengujian regresi.
- docs/e42_source_code_documentation.html, docs/e42_source_assets/, generator dokumentasi, catatan verifikasi/deployment, plan ini dan CHANGELOG.md root.
- Tidak mengubah checkpoint, melatih model, metrik ilmiah, eksperimen historis, atau paket delivery immutable. Tidak melakukan deployment/push tanpa permintaan.

## Langkah
1. Audit source GitHub terisolasi, aturan turunannya, model/manifest, startup, inferensi, XAI, training dan dependensi; tentukan sinkronisasi minimal ke folder kerja utama dan catat di plan.
2. Perbaiki default launcher dan identitas/fail-fast asset E42; pertahankan override eksplisit, thread, offline, satu worker/model sesuai implementasi.
3. Tambah regresi default/override, versi, asset invalid, tanpa training. Jalankan checker dan smoke inference/XAI dengan aset aktual bila tersedia.
4. Buat HTML dengan overview, tabel mapping CLIP/IndoBERT/preprocess/fusion/shared/head/forward, joint weighted CE/config/backprop, XAI aktual versus legacy, serving, screenshot PNG ber-highlight dengan file/baris dan link commit GitHub. Gunakan source lokal dengan hash yang cocok commit untuk link tetap; tandai perubahan lokal.
5. Verifikasi screenshot, link/source, HTML lokal dan tes. Catat hasil nyata serta blocker hardware/dependensi/asset, perbarui deployment, changelog setelah implementasi, lalu laporkan daftar file dan hasil.

## Risiko & Asumsi
- Source utama lokal tertinggal; jangan menimpa perubahan lokal tanpa pembandingan. Salinan audit memisahkan provenance GitHub dari data lokal.
- Model/cache bisa besar atau tidak tersedia; unduhan model pertama harus dinyatakan, tidak ada fallback/training otomatis.
- Runtime CPU dapat lambat; tes stub tidak dianggap bukti integrasi. Checkpoint tidak diganti.
- Source GitHub diakses read-only. Belum ada bukti VPS deployment.

## Verifikasi
Static syntax shell/Python, regresi launcher dan fail-fast, check_delivery.py, test_e42_serving.py, hash manifest/checkpoint, startup Linux/Gunicorn dengan backend/version teramati, frontend/health/metadata/predict tiga task/XAI, inspeksi PNG/HTML dan semua referensi source. Laporkan tiap perintah dan hasil/blocker aktual.

## Deliverables & Kriteria Penerimaan
Default Linux/Gunicorn/Windows konsisten E42 dengan override; runtime versi terverifikasi tanpa retraining/fallback; error asset jelas; HTML source akurat beserta aset relatif, link commit dan nomor baris; tes tersedia dieksekusi; deployment serta changelog root merujuk plan. Jika integrasi tak dapat berjalan, jelaskan batas bukti secara eksplisit.

## Keputusan Investigasi
- Source audit dibekukan pada commit e0a977ece2f77ae95325fd164ca0d58a148ec5d8. Dataset dan OOF lokal identik source audit; tidak diubah.
- Sinkronisasi minimum: app.py/index.html, tambah e42_engine.py, tail_rich_engine.py (base class E42), gunicorn_conf.py, serve_tail.py, requirements-web-lock.txt, test_e42_serving.py; sinkron check_delivery.py dan Windows launcher. Tambah source training e42_tail_grid dan aset E42 yang belum ada, byte-identik commit. File lama disalin ke work/e42-before/ untuk pemulihan dan daftar perubahan dicatat.
- Patch launcher di source audit dan folder utama identik; tambah tes regresi, log identitas dan validasi manifest. Gunicorn tetap satu worker/empat thread, tidak preload/checker proses tambahan. Linux checker hanya saat memilih E42; override eksplisit tetap masuk app.
- Ketidaksesuaian source teramati: training max 128 token, serving inherited max 256 token; dokumentasikan tanpa mengganti protokol penelitian. XAI web menggunakan absolute gradient × activation dan LIME/occlusion, bukan rollout historis.

## Hasil Akhir
- Folder utama kini memuat source/aset E42 yang sebelumnya hilang, dengan backup file lama dan provenance sync. Checkpoint baru ditambahkan byte-identik source; dataset/OOF dan metrik tidak diubah.
- Default Linux/Gunicorn/Windows E42; override dipertahankan. Manifest backend/version dan daftar aset wajib divalidasi, log startup mencetak identitas.
- 11 regresi lulus, replay 740/740 lulus pada tiga task, HTTP Linux/Gunicorn dataset+upload+XAI lulus offline, default LIME lulus, missing-assets/unknown-backend gagal terlihat tanpa fallback/training.
- HTML memuat 28 screenshot verbatim, source hashes, range commit tetap dan range file lokal. 10 URL GitHub unik HTTP 200. Chromium desktop/mobile lulus setelah tabel diberi overflow container.
- Deployment guide/verification report/file inventory dan changelog root selesai. Salinan review GitHub di work/e42-production dicerminkan agar diff dapat ditinjau; tidak commit/push.
- Batas bukti: native Windows, VPS deployment, clean install lock, OCR preparation dan load benchmark belum dijalankan. Input128 training/cache vs256 serving serta label kontrak text_method=occlusion walau metode LIME tersedia dicatat tanpa mengubah protokol.

## File Tambahan yang Tersentuh
`DEMO_XAI_745_FULL/{DELIVERY.md,MULAI_DARI_SINI.md}`, `scripts/{e42_runtime_smoke.py,build_e42_source_documentation.py}`, `docs/{e42_production_deployment.md,e42_production_verification.md}`, `qa/e42-production/`, tes launcher/engine, source/assets yang tercantum pada `qa/e42-production/changed-files.json`. Runtime venv ditambah Gunicorn 27.0.0 untuk pengujian; snapshot lock upstream tidak diklaim lulus instalasi bersih.
