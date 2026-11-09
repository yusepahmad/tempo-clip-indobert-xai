# Persiapan Training GTX 1650 Windows

**Tanggal:** 2026-10-05
**Status:** done

## Tujuan
Menyiapkan lingkungan Windows terisolasi, menyalin dataset/project yang dibutuhkan, dan mengukur full fine-tuning pada GPU 4 GiB.

## Ruang Lingkup
- Windows `C:\Users\User\tempo-training-20261005`: Python lokal jika diperlukan, venv, salinan project, bobot pretrained, benchmark/output.
- Tambah script `DEMO_XAI_745_FULL/01_notebook/benchmark_finetune_gpu.py`, panduan `docs/PERSIAPAN_TRAINING_GPU_WINDOWS.md`, hasil benchmark lokal bila tersedia.
- Snapshot versi paket `DEMO_XAI_745_FULL/requirements-training-windows.lock.txt` dan hasil benchmark JSON lokal.
- Runner lokal `DEMO_XAI_745_FULL/01_notebook/train_finetune_windows.py` dan output uji singkat terpisah.
- Plan ini dan CHANGELOG.md.
- Tidak menimpa instalasi Python lama, dataset asli, model aplikasi, atau menjalankan eksperimen penuh sebelum benchmark.

## Langkah
1. Periksa interpreter, ruang disk, RAM, GPU dan dependensi Windows.
2. Siapkan Python dan venv terisolasi; pasang PyTorch CUDA dari index resmi beserta dependensi encoder.
3. Salin notebook, 740 gambar, CSV, baseline dan bobot cache yang diperlukan.
4. Benchmark optimizer step batch 1 dengan AMP dan gradient checkpointing; tetap latih visual CLIP dan IndoBERT penuh. Text tower CLIP yang tidak dipakai tidak perlu tinggal di GPU.
5. Catat penggunaan VRAM, gradien kedua encoder, durasi, keterbatasan dan perintah menjalankan ulang.
6. Setelah benchmark sukses, buat runner lokal 5-fold/120 epoch, effective batch 16 melalui gradient accumulation; pertahankan normalisasi class-weighted loss per effective batch. Uji satu optimizer step memakai 16 microbatch, bukan training penuh.
7. Dokumentasikan serta catat perubahan setelah diterapkan.

## Risiko & Asumsi
- VRAM 4 GiB mungkin tidak cukup untuk bobot, gradien, optimizer state dan aktivasi, bahkan dengan penghematan memori; laporkan hasil nyata tanpa mengubahnya menjadi head-only training.
- Download dependensi butuh jaringan; gunakan bobot lokal bila memungkinkan.
- Python lama tampak tidak lengkap; gunakan instalasi di folder task jika tidak ditemukan interpreter yang valid.
- Benchmark pendek bukan hasil evaluasi skripsi atau jaminan training 120 epoch stabil.

## Verifikasi
Login key SSH, torch CUDA tensor operation, 740 gambar terbaca, loss finite dan gradien kedua encoder valid, minimal 3 optimizer step atau bukti OOM jelas. Pastikan artefak baseline tidak ditimpa.

## Hasil Verifikasi
- Python 3.11.9 dan venv terisolasi berhasil dibuat; PyTorch 2.7.0+cu118 dan torchvision 0.22.0+cu118 terpasang dari index resmi.
- CUDA tensor operation berhasil; dependensi encoder terpasang dan versi paket disimpan.
- Paket dataset/notebook/baseline/bobot pretrained berhasil disalin dan diekstrak di Windows.
- 740 gambar terverifikasi; 3 forward/backward/optimizer step berhasil. Gradien finite dan probe bobot kedua encoder berubah.
- Peak allocated 3,47 GiB, reserved 3,77 GiB; 2 langkah terakhir rata-rata 1,93 detik/sampul.
- Training penuh belum dijalankan; tidak mengubah metodologi atau model aplikasi. Runner lokal kini disiapkan setelah benchmark sukses; eksperimen penuh tetap belum dijalankan.

- Runner 5-fold/120 epoch disiapkan dan smoke test effective batch 16 berhasil, peak allocated 3,47 GiB; bobot kedua encoder berubah. Normalisasi loss/gradien weighted microbatch diverifikasi cocok dengan batch penuh pada kelas tidak seimbang.
