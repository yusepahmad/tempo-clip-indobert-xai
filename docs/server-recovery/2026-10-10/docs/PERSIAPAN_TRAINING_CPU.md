# Persiapan Training CLIP + IndoBERT

> **Dokumen riwayat per 5 Oktober 2026.** Status terbaru: [STATUS_REVISI_20261006.md](STATUS_REVISI_20261006.md) (6 Oktober 2026). Jalur Colab/CPU di bawah tidak dipakai untuk training penuh. Training penuh dijalankan di Kaggle dua T4 dan selesai 5 Okt ([HASIL_FULL_TRAINING_KAGGLE.md](HASIL_FULL_TRAINING_KAGGLE.md)); karena Task 2 turun, aplikasi tetap memakai baseline encoder beku.

Tanggal pemeriksaan: 2026-10-05.

## Pekerjaan terakhir
Plan 29 September dan notebook `DEMO_XAI_745_FULL/01_notebook/finetune_encoder_colab.ipynb` menyiapkan full fine-tuning CLIP ViT-B/32 + IndoBERT + head MTL, bukan IndoBERT saja. Dataset 740 sampul, 5-fold CV, 120 epoch/fold. Model aplikasi tetap encoder beku; baseline Macro-F1 Task 2 sekitar 0,320. Belum ditemukan hasil fine-tuning penuh di folder hasil. Folder kerja ini tidak memiliki metadata Git, sehingga pekerjaan terakhir ditelusuri dari plan, changelog, notebook, dan artefak, bukan riwayat commit.

## Laptop dan hasil pengujian
- Ryzen 7 7730U, 8 core/16 thread; grafis Radeon terintegrasi.
- RAM OS 22 GiB; saat audit tersedia sekitar 8,5 GiB. Ruang disk sekitar 195 GiB.
- Environment `DEMO_XAI_745_FULL/venv`: PyTorch 2.14.0+cpu, Transformers 5.17.0, CUDA tidak tersedia.
- Seluruh 740 path gambar terverifikasi; bobot pretrained bisa dimuat dari cache lokal.
- Uji nyata 3 optimizer step, batch 1, 4 thread: 8,27 / 1,76 / 1,92 detik. Gradien CLIP dan IndoBERT valid; optimizer berhasil memperbarui bobot.
- Peak RSS proses sekitar 4,35 GiB, bukan pemakaian seluruh sistem.
- Ekstrapolasi dua langkah terakhir untuk 5 fold × 120 epoch: sekitar 182 jam (7,6 hari) waktu komputasi training. Ini perkiraan sangat kasar pada batch 1/thread 4, belum termasuk loading data, evaluasi, penyimpanan, dan perlambatan CPU karena panas. Batch 16 di notebook GPU tidak diukur dan angka ini bukan prediksi durasi GPU.

## Menjalankan ulang benchmark lokal
Dari root project:

```bash
rtk proxy DEMO_XAI_745_FULL/venv/bin/python DEMO_XAI_745_FULL/01_notebook/benchmark_finetune_cpu.py --steps 3 --batch-size 1 --threads 4
```

Hasil ditulis ke `DEMO_XAI_745_FULL/04_hasil_eksperimen/benchmark_finetune_cpu.json`. Script memakai definisi encoder/head dari notebook, mengecek semua gambar, dan hanya melatih beberapa sampul. Tidak menjalankan CV dan tidak mengganti model aplikasi. Loss tanpa class weighting digunakan hanya untuk menguji komputasi; hasil ini bukan metrik skripsi. Mode offline aktif secara default karena bobot sudah tersedia di mesin ini; pada mesin baru bobot perlu diunduh dahulu (atau set `HF_HUB_OFFLINE=0`).

## Training penuh
CPU terbukti bisa menjalankan full fine-tuning, tetapi untuk eksperimen lengkap jalur GPU yang sudah disiapkan lebih praktis. Tidak mengubah keputusan metodologi menjadi partial fine-tuning.

1. Buka notebook `finetune_encoder_colab.ipynb` di Colab dan pilih runtime GPU yang tersedia. Notebook memeriksa CUDA sebelum training.
2. Unggah `03_data/DATASET_740_TASK2_DOMAIN.csv`, seluruh `05_gambar/`, dan baseline `04_hasil_eksperimen/hasil_mtl_740_task2domain.json` ke folder `MyDrive/DEMO_XAI_745_FULL/` sesuai struktur lokal.
3. Jalankan sel berurutan. Ketersediaan dan memori GPU perlu diperiksa saat runtime; batch 16 belum diuji pada GPU di sesi ini.
4. Salin hasil JSON, recall CSV, dan bobot fold ke folder hasil lokal setelah training. Evaluasi hasil sebelum mengubah model aplikasi.

Notebook kini melepaskan model preprocessing dan model fold setelah disimpan, agar tidak menumpuk model di memori. Keputusan sebelumnya tentang tidak menyimpan checkpoint di tengah fold tetap berlaku; fold yang terputus perlu diulang. Training penuh belum dijalankan oleh persiapan ini.

Plan: [2026-10-05-persiapan-training-cpu.md](plans/2026-10-05-persiapan-training-cpu.md).
