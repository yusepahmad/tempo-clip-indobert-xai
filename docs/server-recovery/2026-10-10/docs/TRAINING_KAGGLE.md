# Full Training Dua T4 di Kaggle

> **Dokumen riwayat per 5 Oktober 2026.** Status terbaru: [STATUS_REVISI_20261006.md](STATUS_REVISI_20261006.md) (6 Oktober 2026). Bagian "Peluncuran penuh 2026-10-05" (status RUNNING, belum ada metrik) sudah usang: training COMPLETE, lihat [HASIL_FULL_TRAINING_KAGGLE.md](HASIL_FULL_TRAINING_KAGGLE.md). Fine-tuning tidak dipakai di demo karena Task 2 turun; aplikasi tetap baseline.

Status 2026-10-05: full training versi1 **COMPLETE**; audit lima fold/600epoch dan740prediksiOOF lulus. Macro-F1 Task1/2/3=0,5139/0,2461/0,3699. Task2 menurun dibanding baseline, sehingga demo tetap baseline. Lihat [hasil dan batas audit](HASIL_FULL_TRAINING_KAGGLE.md). Smoke test versi2 sebelumnya berhasil resume epoch1→2; smoke bukan metrik final.

## Konfigurasi
CLIP visual + IndoBERT penuh, 740 sampul, 5-fold StratifiedKFold seed42, 120 epoch/fold. Batch global16 (8/T4), LR2e-5, weight decay1e-4, AMP float16, fused AdamW dan DDP static graph. Pemeriksaan seluruh gradien finite setiap langkah. Sampler set_epoch menjaga shuffle berubah per epoch. Evaluasi dilakukan setelah epoch120; checkpoint setiap5epoch dan akhir fold. Tidak ada early stopping atau pemilihan model berdasarkan test fold.

## Mulai training penuh
Dari root project (perintah ini memulai training, belum dijalankan dalam persiapan):

```bash
rtk proxy kaggle kernels push -p DEMO_XAI_745_FULL/01_notebook/kaggle_benchmark/full_training --accelerator NvidiaTeslaT4 --timeout 21600
rtk proxy kaggle kernels status yusepmuhamadzazuli/tempo-full-training
rtk proxy kaggle kernels logs yusepmuhamadzazuli/tempo-full-training
rtk proxy kaggle kernels output yusepmuhamadzazuli/tempo-full-training -p DEMO_XAI_745_FULL/04_hasil_eksperimen/finetuned_kaggle
```

Job berjalan server-side; browser/terminal tidak perlu terbuka. Logs CLI mungkin baru tersedia setelah job selesai. Pastikan tidak ada session GPU lain dan quota cukup. Benchmark estimasi2,6jam hanya compute; checkpoint besar menambah waktu. Batasjob6jam bukan jaminan selesai.

## Output
Di /kaggle/working/tempo_full/: latest.pt (model, optimizer, scaler, RNG Python/NumPy/CPU/CUDA tiaprank, epoch/fold/config), progress.json, training_history.jsonl; fold_1.pt sampai fold_5.pt, metrik/prediksi tiapfold; oof_predictions.npz, hasil_mtl_740_finetuned.json dan analisis_recall_per_kelas_740_finetuned.csv setelah kelimafold selesai. Model dan latest checkpoint berukuran beberapa GB total. Model fold berupa state_dict tanpa CLIP text tower, kompatibel pola runner Windows; jangan memuat checkpoint tak tepercaya karena resume menggunakan torch.load weights_only=False.

## Resume
1. Unduh output job yang sudah tersedia; simpan seluruh folder tempo_full (latest.pt DAN model/metrics/prediksi fold yang selesai) sebagai dataset Kaggle PRIVATE. Token/kredensial tidak perlu diunggah.
2. Tambahkan slug dataset checkpoint ke dataset_sources pada kernel-metadata.json. Pada launch_full.py isi RESUME_SOURCE dengan path dataset/folder yang memuat latest.pt di /kaggle/input.
3. Jalankan push kembali. Launcher menyalin input ke tempo_full yang writable. Worker memvalidasi config, SHA256 CSV/notebook, memuat model/optimizer/scaler serta RNG tiaprank, lalu melanjutkan epoch berikutnya. Fold yang selesai dilewati; data completed fold dipakai untuk OOF final.

latest.pt ditulis lewat temporaryfile dan atomic replace, checkpoint sebelumnya dipertahankan sampai file baru selesai. Bila terputus, maksimal5epoch sejak checkpoint terakhir perlu diulang, ASALKAN checkpoint/output dapat diambil dari Kaggle. Crash/timeout platform tidak dijamin menyimpan output; checkpoint pada /kaggle/working bukan backup eksternal otomatis. Resume lintas runtime juga tidak menjamin hasil bit-identik. Hapus/arsip output sebelumnya hanya setelah hasil tersimpan.

## Uji aman
Kernel tempo-full-training-smoke terpisah: dua optimizerstep pada epoch1, simpan checkpoint, restart torchrun, resume epoch2 dua step, evaluasi148sampul. Output tempo_smoke; tidak dianggap metrik CV skripsi. Metadata smoke disediakan terpisah agar tidak memulai full training saat pengujian.

Plan: [persiapan full training](plans/2026-10-05-full-training-kaggle.md).

Hasil verifikasi: `DEMO_XAI_745_FULL/04_hasil_eksperimen/kaggle_full_smoke/tempo_smoke/smoke_result.json`. Log restart di direktori induknya. Smoke memakai2langkah/epoch, bukan seluruh epoch; ini menguji save/load/resume/evaluasi, bukan kualitas akhir. File model/checkpoint smoke tersimpan pada output kernel private; unduhan lokal dibatasi JSON/NPZ/log agar tidak mengunduh bobot beberapaGB yang bukan hasil akhir.

## Peluncuran penuh 2026-10-05
Kernel private versi1: https://www.kaggle.com/code/yusepmuhamadzazuli/tempo-full-training . Push sukses, status RUNNING, timeout21600detik. Quota sebelum submit29,82jam. Epoch belum diverifikasi karena log awal belum tersedia. Bukti peluncuran: `DEMO_XAI_745_FULL/04_hasil_eksperimen/finetuned_kaggle/launch_status.json`. Output akhir harus diunduh dan diperiksa setelah COMPLETE; belum ada metrik full training. Plan: [mulai full training](plans/2026-10-05-mulai-full-training-kaggle.md).
