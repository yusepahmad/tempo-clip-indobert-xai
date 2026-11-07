# Peningkatan Selector OCR dan Evaluasi Holdout 2

**Tanggal:** 2026-10-17  
**Status:** done  

## Tujuan
Meningkatkan akurasi *exact match* OCR headline dari 75,0% (60/80 sampel) pada holdout 1 agar dapat melampaui gate wajib minimal **80%** pada holdout final 2 (90 sampel beku), dengan menangani pola kesalahan teridentifikasi:
1. Tercampurnya banner rubrik majalah (misalnya `INVESTIGASI`, `OUTLOOK EKONOMI`, `LAPORAN KHUSUS`) ke dalam teks headline.
2. Terputusnya baris headline bertingkat (misalnya judul multi-baris yang baris atas/bawahnya tertinggal).
3. Tertariknya teks subheadline/teaser berhuruf kecil ke dalam headline utama.

## Ruang Lingkup
- **File/modul yang dibuat dan disentuh:**
  - `docs/plans/2026-10-17-peningkatan-selector-ocr-holdout2.md` (dokumen plan ini)
  - `DEMO_XAI_745_FULL/02_web_demo/ocr_headline.py` (penyempurnaan selector, filtering rubrik banner, perbaikan penyatuan baris headline vertikal)
  - `DEMO_XAI_745_FULL/01_notebook/test_ocr_urutan.py` (penambahan regression fixture untuk kasus yang diperbaiki)
  - `DEMO_XAI_745_FULL/01_notebook/evaluate_ocr_second_holdout.py` (script evaluator read-once untuk holdout 2)
  - `DEMO_XAI_745_FULL/04_hasil_eksperimen/revisi_week3/ocr_second_holdout/results.json` (hasil raw dan metrik evaluasi holdout 2)
  - `CHANGELOG.md` dan `docs/SPRINT_ROADMAP.md` setelah selesai.
- **Yang eksplisit TIDAK disentuh:**
  - `manifest_frozen.json` dan `manifest_frozen.sha256` pada holdout 2 (ground truth holdout tidak diubah).
  - Arsip holdout 1 di `ocr_final_holdout/results.json` (arsip tetap dipertahankan).
  - Dataset `03_data/DATASET_740_TASK2_DOMAIN.csv`.

## Langkah
1. Tulis plan ke `docs/plans/2026-10-17-peningkatan-selector-ocr-holdout2.md`.
2. Evaluasi fungsi selector pada `DEMO_XAI_745_FULL/02_web_demo/ocr_headline.py`:
   - Tambahkan rule pembersihan banner rubrik majalah Tempo yang umum muncul di atas/di awal judul tanpa mengorbankan kata judul asli.
   - Perbaiki heuristik penggabungan baris headline agar menangkap baris judul kapital yang posisinya bersambung vertikal dengan font proporsional.
   - Filter subheadline berbasis perbandingan rasio tinggi bounding box terhadap judul utama.
3. Jalankan suite test OCR (`test_ocr_urutan.py`) untuk memastikan tidak terjadi regresi pada kasus yang sebelumnya sudah benar.
4. Buat script evaluator `evaluate_ocr_second_holdout.py` yang memvalidasi hash manifest holdout 2 sebelum inferensi.
5. Jalankan evaluasi tepat satu kali pada holdout 2 (90 sampel) dan simpan hasil audit ke `ocr_second_holdout/results.json`.
6. Evaluasi kelulusan gate (target $\ge 80\%$, yaitu minimal 72/90 sampel benar).
7. Catat perubahan dan hasil evaluasi ke `CHANGELOG.md`.

## Risiko & Asumsi
- Evaluasi holdout 2 mencakup 90 sampel (10 sampel per kelas untuk 9 kelas Task 1; kelas `other_issue` telah habis pada set sebelumnya).
- Inferensi OCR murni berbasis gambar dan visual layout, tanpa ada akses atau lookup terhadap ground truth.

## Verifikasi
- Unit test OCR lulus tanpa regresi.
- Evaluasi holdout 2 menghasilkan file `results.json` yang memuat `exact_accuracy`, daftar prediksi, denominator 90 sampel, dan status kelulusan gate 80%.
