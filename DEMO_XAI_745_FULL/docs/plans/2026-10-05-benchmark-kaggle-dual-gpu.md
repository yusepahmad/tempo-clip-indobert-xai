# Benchmark Dua GPU Kaggle
**Tanggal:** 2026-10-05
**Status:** done
## Tujuan
Bandingkan satu epoch DDP dua T4 dengan baseline satu T4 30,98 detik.
## Ruang Lingkup
- Subfolder kaggle_benchmark/dual_gpu, output benchmark, docs/BENCHMARK_KAGGLE.md dan CHANGELOG.md.
- Tidak menjalankan training penuh atau mengubah training Windows.
## Langkah
1. Buat worker DDP dua proses, batch 8/GPU, total 16, split dan hyperparameter sama.
2. Normalisasi weighted CE terhadap batch global; verifikasi kedua encoder diperbarui dan GPU/rank aktif.
3. Jalankan private kernel satu epoch maksimum 1 jam; unduh hasil dan bandingkan.
## Risiko & Asumsi
- Komunikasi antar T4 bisa lebih mahal daripada peningkatan compute; tidak menjanjikan percepatan.
- DistributedSampler menjaga 592 sampul tanpa padding; urutan shuffle berbeda dari baseline, hasil waktu bukan kesetaraan numerik.
## Verifikasi
Syntax, dua rank aktif, 37 optimizer step, total 592 sampul, finite gradient dan encoder update; durasi diukur dengan sinkronisasi kedua rank.

## Hasil
Kernel versi 1 COMPLETE, kedua rank sukses dengan pembaruan kedua encoder. Epoch 24,13 detik dibanding 30,98 detik baseline (22,13% lebih singkat); estimasi 600 epoch 4,02 jam. Output kedua rank, log, worker aktual dan comparison.json diunduh. Tidak menjalankan eksperimen penuh.
