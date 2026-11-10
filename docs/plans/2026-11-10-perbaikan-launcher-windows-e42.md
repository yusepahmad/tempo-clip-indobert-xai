# Perbaikan Launcher Windows E42

**Tanggal:** 2026-11-10
**Status:** done

## Tujuan
Memastikan alur setup dan launcher Windows memakai backend E42 secara default, memeriksa kelengkapan aset E42 sebelum server dimulai, dan memberikan pesan kegagalan yang jelas.

## Ruang Lingkup
- `DEMO_XAI_745_FULL/jalankan_windows.bat`
- `DEMO_XAI_745_FULL/setup_windows.bat`
- `DEMO_XAI_745_FULL/01_notebook/check_delivery.py`
- Dokumentasi penggunaan Windows yang terkait langsung
- `CHANGELOG.md`
- Tidak mengubah bobot model, hasil eksperimen, atau pipeline pelatihan E42.

## Langkah
1. Audit kontrak launcher, setup, dependency lock, dan pemeriksaan delivery saat ini.
2. Ubah launcher agar E42 menjadi backend default dan kegagalan preflight terlihat jelas.
3. Ubah setup agar memakai dependency lock web dan menjalankan preflight E42.
4. Ubah pemeriksaan delivery agar memvalidasi aset serta replay prediksi E42.
5. Selaraskan dokumentasi Windows.
6. Jalankan pemeriksaan statis batch, preflight Python, dan pengujian serving E42.
7. Catat hasil aktual di changelog dan push ke Git.

## Risiko & Asumsi
- Lingkungan saat ini Linux dan tidak menyediakan kernel/VM Windows, sehingga file `.bat` tidak dapat dieksekusi secara native di sini.
- Validasi dilakukan melalui kontrak statis launcher dan eksekusi nyata komponen Python yang dipanggil launcher.
- Unduhan backbone tersemat pada eksekusi pertama tetap membutuhkan internet dan ruang disk beberapa GB.

## Verifikasi
- Launcher menunjuk `e42-tail-grid` secara default dan semua path yang dirujuk tersedia.
- Setup memakai `02_web_demo/requirements-web-lock.txt`.
- `check_delivery.py` berhasil memuat lima fold E42 dan mereplay 740 prediksi sesuai OOF kanonik.
- Tes serving E42 lulus dan scan identitas tetap bersih.

## Hasil
- Kontrak statis kedua file batch lulus, termasuk path berpetik, penanganan error, backend default, dependency lock, dan semua target file.
- Preflight aktual menghasilkan `5 checkpoints, 740/740 canonical OOF predictions match`.
- Dua tes `test_e42_serving.py` lulus dalam 13,242 detik.
- Eksekusi native `.bat` belum diklaim karena lingkungan verifikasi bukan Windows.
