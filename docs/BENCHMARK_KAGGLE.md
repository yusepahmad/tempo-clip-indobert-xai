# Benchmark GPU Kaggle

Tanggal: 2026-10-05. Status: benchmark versi 3 berhasil setelah verifikasi nomor HP. Eksperimen penuh belum dijalankan.

## Artefak
- Input private: https://www.kaggle.com/datasets/research-account/tempo-benchmark-20261005
- Kernel private: https://www.kaggle.com/code/research-account/tempo-one-epoch-benchmark
- Script/metadata lokal: `DEMO_XAI_745_FULL/01_notebook/kaggle_benchmark/`.

## Konfigurasi
Satu epoch fold pertama dari split 5-fold seed 42 (592 latih/148 uji), batch 16, full visual CLIP + IndoBERT, AMP float16, AdamW LR 2e-5/weight decay 1e-4, class-weighted loss per task. Tidak memakai gradient checkpointing; T4 diminta via CLI. Jika runtime memiliki dua kartu, kode memakai satu GPU saja. Ini benchmark waktu, bukan evaluasi akhir skripsi.

Paket input awal berisi CSV final, seluruh gambar dan notebook definisi model (~98 MB), tanpa credential/venv. Versi 2 menambahkan bobot pretrained identik dari cache dan wheels Python 3.13 Linux (~1,15 GB total), karena versi 1 gagal DNS saat pip install. Retry versi 2 menggunakan internet false dan HF_HUB_OFFLINE=1. Dataset dibuat private, lisensi Other dengan keterangan hak tetap pada penulis asli. API menolak nama copyright-authors yang tercantum pada dokumentasi. API datasets status memberi 403 tetapi create menerima dataset private dan kernel berhasil dimulai; keterbacaan input dibuktikan lewat job.

Perintah:

```bash
rtk proxy kaggle kernels status research-account/tempo-one-epoch-benchmark
rtk proxy kaggle kernels logs research-account/tempo-one-epoch-benchmark
rtk proxy kaggle kernels output research-account/tempo-one-epoch-benchmark -p DEMO_XAI_745_FULL/04_hasil_eksperimen/kaggle_benchmark
```

Job berjalan server-side, tanpa perlu tab browser/terminal tetap terbuka. Batas job ini 3600 detik; bukan menjalankan 120 epoch atau 5 fold penuh. Output target `benchmark_kaggle.json`: GPU, durasi setup, durasi satu epoch, waktu evaluasi 148 sampul, memory peak, dan ekstrapolasi waktu 600 epoch. Pengukuran setup terpisah dari training. Estimasi belum termasuk checkpoint/variabilitas/kuota per GPU dan hanya sah jika status success.

Plan: [2026-10-05-benchmark-kaggle.md](plans/2026-10-05-benchmark-kaggle.md).

## Hambatan terverifikasi
Kernel diagnostik private `research-account/tempo-gpu-diagnostic` selesai: torch `2.11.0+cpu`, CUDA false, torch CUDA null, tidak ada `/dev/nvidia*` atau `nvidia-smi`. Editor akun menunjukkan GPU T4 x2 disabled dan pesan “Get phone verified” untuk membuka GPU/TPU/internet. Form verifikasi nomor HP telah dibuka tanpa memasukkan nomor atau mengirim SMS. User perlu menyelesaikan verifikasi sendiri, lalu benchmark dapat dikirim ulang. Quota 30 jam tidak membuktikan akses GPU telah aktif.

Script diagnostik: `DEMO_XAI_745_FULL/01_notebook/kaggle_benchmark/diagnostic/`. Hasil di `DEMO_XAI_745_FULL/04_hasil_eksperimen/kaggle_benchmark/gpu_diagnostic.json`. Belum ada epoch yang berjalan; tidak ada estimasi durasi Kaggle yang valid.

## Hasil benchmark versi 3
Kernel COMPLETE dan output status success. Satu Tesla T4 digunakan (dua tersedia), batch 16, tanpa gradient checkpointing. Semua 740 gambar ditemukan; split 592 latih/148 uji. Bobot CLIP dan IndoBERT sama-sama diperbarui, loss/gradien finite.

- Setup: 77,14 detik.
- Training satu epoch/37 langkah: 30,98 detik.
- Evaluasi forward 148 sampul: 5,25 detik (bukan metrik akhir CV).
- Peak allocated: 3,89 GiB; reserved: 4,39 GiB.
- Ekstrapolasi training 600 epoch: 5,16 jam, belum termasuk setup tiap fold, checkpoint, evaluasi tambahan, variasi runtime dan penghitungan kuota. Ini estimasi dari satu epoch, bukan durasi eksperimen yang telah selesai.
- Total kode job: 113,37 detik.

Hasil: `DEMO_XAI_745_FULL/04_hasil_eksperimen/kaggle_benchmark/benchmark_kaggle.json`; log: `tempo-one-epoch-benchmark.log`. Hambatan verifikasi di atas adalah riwayat yang sudah terselesaikan. Tidak ada training penuh atau perubahan training Windows dalam benchmark ini.

## Dua T4 dengan DDP
Private kernel `research-account/tempo-dual-gpu-benchmark` versi 1 COMPLETE; dua rank status success. Total batch tetap 16 (8/rank), 592 sampul dibagi tanpa padding, 37 langkah. Weighted CE dinormalisasi memakai jumlah bobot label batch global sebelum DDP averaging. Kedua encoder diperbarui di kedua rank; pemeriksaan finite gradient tetap dilakukan setiap langkah seperti baseline.

| Konfigurasi | Waktu epoch | Estimasi 600 epoch |
| --- | ---: | ---: |
| Satu T4 | 30,98 detik | 5,16 jam |
| Dua T4, DDP | 24,13 detik | 4,02 jam |

Pengurangan waktu 22,13%, speedup 1,28×. Evaluasi forward 148 sampul dibagi kedua rank: 2,14 detik. Peak allocated 4,30 GiB/GPU, reserved 4,78 GiB/GPU (DDP menambah buffer komunikasi). Angka setup/total pada laporan worker tidak mencakup instalasi launcher, sehingga tidak dibandingkan dengan total job baseline. Loss laporan rank merupakan kontribusi lokal berskala world size, rata-rata dua rank adalah loss global. Urutan shuffle berbeda; ini uji throughput, bukan pembuktian kesetaraan metrik akhir.

Hasil dan log: `DEMO_XAI_745_FULL/04_hasil_eksperimen/kaggle_benchmark/dual_gpu/`, termasuk `comparison.json`. Estimasi masih satu epoch, tidak termasuk checkpoint/variasi runtime; penghitungan kuota dua GPU belum diverifikasi. Training penuh belum dimulai. Plan: [benchmark dua GPU](plans/2026-10-05-benchmark-kaggle-dual-gpu.md).

## Verifikasi optimasi dua T4
Kernel private `research-account/tempo-optimization-check` COMPLETE. Paired runtime memakai init/sampler seed sama: baseline 20,46 detik/epoch, kandidat 15,60 detik/epoch (sekitar 24% pengurangan waktu). Baseline kali ini menghitung tensor pemeriksaan finite terlebih dulu sebelum sinkronisasi individual, berbeda dari kode baseline awal 24,13 detik; variasi runtime juga mungkin terjadi. Angka paired adalah perbandingan utama.

Kandidat: fused AdamW, DDP static_graph, pin_memory/nonblocking transfer, dan satu sinkronisasi untuk gabungan seluruh pemeriksaan gradien. Pemeriksaan seluruh gradien tetap setiap langkah. Batch global 16, LR 2e-5, weight decay 1e-4, AMP, split dan arsitektur sama. DDP mencatat parameter yang tidak dipakai: bert.pooler.dense.weight/bias. Static graph mendukung parameter unused yang tetap, tanpa menghapus pooler. Tidak menggunakan worker multiprocessing atau cache preprocessing.

Semua empat laporan rank sukses: kedua encoder diperbarui, 148 sampul evaluasi finite. Loss global baseline/kandidat berbeda <0,001. Ini membuktikan sanity satu epoch, bukan kesetaraan seluruh bobot atau konvergensi 120 epoch. Estimasi 600 epoch kandidat sekitar 2,60 jam training, belum termasuk checkpoint/setup/variasi. Hasil lengkap di `DEMO_XAI_745_FULL/04_hasil_eksperimen/kaggle_benchmark/optimized/comparison.json`.

Rujukan implementasi: [PyTorch DDP static_graph](https://docs.pytorch.org/docs/2.11/generated/torch.nn.parallel.DistributedDataParallel.html) dan [AdamW fused](https://docs.pytorch.org/docs/2.11/generated/torch.optim.AdamW.html). Plan: [verifikasi optimasi](plans/2026-10-05-verifikasi-optimasi-kaggle.md).
