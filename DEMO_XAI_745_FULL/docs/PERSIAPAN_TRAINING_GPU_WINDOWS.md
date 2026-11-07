# Persiapan Training GPU Windows

Tanggal: 2026-10-05. Status: setup dan benchmark selesai.

## Lokasi Windows
`C:\Users\User\tempo-training-20261005`

- Python 3.11.9 lokal: `python\python.exe`.
- Interpreter environment: `venv\Scripts\python.exe`.
- Salinan project: `DEMO_XAI_745_FULL`.
- Bobot lokal: `weights\clip\open_clip_model.safetensors` dan `weights\indobert`.

Python dipasang tanpa mengubah PATH atau mengganti instalasi sebelumnya. PyTorch menggunakan wheel CUDA 11.8 resmi (torch 2.7.0, torchvision 0.22.0), bukan toolkit CUDA sistem. Panduan instalasi resmi: https://pytorch.org/get-started/locally/ . Driver yang terdeteksi 610.47; operasi tensor CUDA nyata berhasil pada GTX 1650 Max-Q.

## Hardware
GTX 1650 VRAM 4096 MiB, RAM sekitar 15,7 GiB, ruang kosong C sekitar 110 GiB. Saat audit GPU terpakai 467 MiB oleh aplikasi desktop. Full training CLIP+IndoBERT jauh lebih besar daripada training IndoBERT saja.

## Benchmark
Script mengikuti definisi encoder dan head notebook Colab, memverifikasi 740 gambar, lalu menjalankan 3 optimizer step pada data nyata. Batch 1, token maksimum 128, AMP float16, gradient checkpointing kedua encoder, AdamW foreach=False. Text tower CLIP yang tidak digunakan untuk encode_image dilepas dari GPU; seluruh parameter visual CLIP dan IndoBERT tetap terbuka. Ini tidak mengubah eksperimen menjadi encoder beku.

Di PowerShell:

```powershell
Set-Location C:\Users\User\tempo-training-20261005
.\venv\Scripts\python.exe .\DEMO_XAI_745_FULL\01_notebook\benchmark_finetune_gpu.py --weights .\weights --steps 3
```

Output terpisah: `DEMO_XAI_745_FULL\04_hasil_eksperimen\benchmark_finetune_gpu.json`. Tidak menimpa hasil baseline atau model aplikasi. Loss benchmark tidak menggunakan class weighting dan tidak bisa dianggap metrik ilmiah. Estimasi durasi pendek tidak mencakup evaluasi, penyimpanan, loading data, atau panas sustained.

## Hasil benchmark nyata
- Seluruh 740 gambar ditemukan; 3 langkah training selesai tanpa OOM.
- 212.624.921 parameter trainable setelah bagian CLIP yang tidak terpakai dilepas.
- Gradien kedua encoder finite dan nonzero; probe bobot visual CLIP serta IndoBERT terbukti berubah pada setiap langkah optimizer.
- Durasi langkah: 2,88 / 2,01 / 1,86 detik; dua langkah terakhir rata-rata 1,93 detik.
- Peak allocated 3,47 GiB; peak reserved 3,77 GiB dari VRAM 4 GiB. Ini statistik allocator PyTorch, bukan total VRAM semua aplikasi. Margin kecil; batch lebih besar belum diuji.
- Ekstrapolasi batch 1 tanpa gradient accumulation: 5 fold × 120 epoch sekitar 191 jam (8 hari), belum termasuk evaluasi/penyimpanan/data loading dan panas. Ini benchmark pendek, bukan prediksi yang pasti.
- Uji GPU ini tidak menunjukkan keuntungan waktu yang jelas dibanding benchmark CPU sebelumnya (~1,84 detik/sampul). Konfigurasi, checkpointing, AMP dan pemeriksaan gradien berbeda sehingga bukan perbandingan performa terkontrol.
- Snapshot paket tersedia di `DEMO_XAI_745_FULL/requirements-training-windows.lock.txt`. Untuk rekonstruksi, install torch/torchvision dari index CUDA 11.8 resmi dahulu, kemudian gunakan lock file dengan `--extra-index-url https://download.pytorch.org/whl/cu118`.

## Runner training penuh yang siap dijalankan
`train_finetune_windows.py` mempertahankan 5-fold CV, 120 epoch/fold, seed 42, class weighting per fold/task, LR 2e-5, weight decay 1e-4 dan head yang sama. Batch fisik 1 dikumpulkan menjadi effective batch 16. Normalisasi weighted CE memakai jumlah bobot target pada seluruh batch efektif (bukan rata-rata terpisah setiap microbatch, yang menghilangkan class weighting pada batch 1).

Uji `--smoke-test` berhasil pada 16 sampul dan satu optimizer step: weighted loss 2,1182, peak allocated 3,47 GiB, probe bobot kedua encoder berubah. Durasi 12,26 detik termasuk pembuatan model setelah dataset disiapkan. Formula loss dan gradien microbatch juga dibandingkan dengan weighted CE batch penuh pada contoh kelas tidak seimbang dan cocok. Uji ini bukan CV atau hasil ilmiah.

Menjalankan ulang uji singkat di PowerShell:

```powershell
Set-Location C:\Users\User\tempo-training-20261005
.\venv\Scripts\python.exe -u .\DEMO_XAI_745_FULL\01_notebook\train_finetune_windows.py --weights .\weights --smoke-test
```

Menjalankan seluruh eksperimen:

```powershell
Set-Location C:\Users\User\tempo-training-20261005
.\venv\Scripts\python.exe -u .\DEMO_XAI_745_FULL\01_notebook\train_finetune_windows.py --weights .\weights | Tee-Object -FilePath .\training.log
```

Jalankan dari terminal Windows lokal, sambungkan charger dan atur agar laptop tidak sleep selama training. Tidak perlu mempertahankan koneksi SSH untuk perintah yang dimulai di terminal lokal ini.

Output disimpan di `DEMO_XAI_745_FULL\04_hasil_eksperimen\finetuned_windows`: bobot dan metrik serta prediksi setiap fold selesai, lalu JSON hasil keseluruhan dan recall CSV setelah lima fold selesai. Tidak ada checkpoint di tengah fold, sesuai keputusan sebelumnya. Folder hasil yang sudah berisi file akan ditolak agar hasil tidak tertimpa; uji singkat hanya membuat JSON terpisah. Runner tidak otomatis melanjutkan fold setelah interupsi.

Checkpoint berisi state_dict, peta kelas, dan penanda text tower CLIP yang dilepas; tidak bisa langsung dimuat secara strict ke model notebook asli yang masih menyertakan text tower. Integrasi ke aplikasi belum dilakukan dan harus menyesuaikan loader setelah evaluasi hasil.

Gradient accumulation/AMP/checkpointing tetap full fine-tuning encoder yang dipakai, tetapi tidak identik secara numerik dengan notebook GPU batch 16. Runner membersihkan 8 nilai NaN pada supporting text di memori tanpa mengubah CSV; notebook lama mengubah NaN menjadi string "nan". Perbedaan ini harus dicatat saat membandingkan eksperimen. Benchmark batch 1 di atas menggunakan optimizer setiap sampul; runner menggunakannya setiap 16 sampul, sehingga ekstrapolasi 191 jam bukan prediksi runner ini. Ukur waktu epoch nyata untuk estimasi durasi penuh.

Training penuh belum dijalankan oleh sesi persiapan ini; hasil skripsi dan model aplikasi tetap baseline sebelumnya.

Plan: [2026-10-05-training-gtx1650-windows.md](plans/2026-10-05-training-gtx1650-windows.md).
