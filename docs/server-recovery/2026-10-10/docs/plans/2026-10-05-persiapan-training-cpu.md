# Persiapan dan Benchmark Training CPU

**Tanggal:** 2026-10-05
**Status:** done

## Tujuan
Memeriksa pekerjaan terakhir dan kesiapan laptop, menyediakan benchmark full fine-tuning CLIP+IndoBERT di CPU sebelum memilih tempat training penuh.

## Ruang Lingkup
- Tambah `DEMO_XAI_745_FULL/01_notebook/benchmark_finetune_cpu.py` dan `docs/PERSIAPAN_TRAINING_CPU.md`.
- Perbaiki pelepasan model fold dan model preprocessing di `finetune_encoder_colab.ipynb`.
- Hasil terukur `DEMO_XAI_745_FULL/04_hasil_eksperimen/benchmark_finetune_cpu.json`.
- Plan ini dan `CHANGELOG.md` root.
- Tidak mengubah dataset, model aplikasi, skema 5-fold/120 epoch, atau menjalankan training penuh.

## Langkah
1. Audit hardware, dataset, lingkungan Python, dan notebook terakhir.
2. Buat benchmark CPU terbatas yang memakai definisi model notebook dan data nyata, menyimpan pengukuran terpisah dari hasil ilmiah.
3. Lepaskan model yang tidak dibutuhkan di notebook Colab.
4. Jalankan benchmark, dokumentasikan hasil dan perintah penggunaan.
5. Catat perubahan yang sudah diterapkan di changelog.

## Risiko & Asumsi
- Benchmark pendek tidak menjamin durasi training penuh; estimasi hanya ekstrapolasi waktu optimizer step.
- CPU dapat memanaskan laptop; batasi thread, batch, dan jumlah langkah.
- Full fine-tuning kedua encoder tetap keputusan sebelumnya; tidak diganti menjadi encoder beku.
- Bobot pretrained menggunakan cache lokal bila tersedia; hasil benchmark bukan metrik evaluasi.

## Verifikasi
Compile kode notebook/script, cek seluruh 740 gambar dan kolom wajib, lakukan forward/backward/optimizer pada sampul nyata, pastikan gradien kedua encoder, dan periksa hasil pengukuran.

## Hasil Verifikasi
- Compile script dan seluruh sel kode notebook berhasil.
- Semua 740 path gambar ditemukan; 3 forward/backward/optimizer step berhasil dan gradien kedua encoder valid.
- Peak RSS 4,35 GiB; waktu steady step sekitar 1,84 detik, ekstrapolasi training sekitar 182 jam pada batch 1/thread 4.
- Training penuh dan runtime GPU belum diuji.
