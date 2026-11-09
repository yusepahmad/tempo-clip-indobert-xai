# Persiapan Full Training Kaggle
**Tanggal:** 2026-10-05
**Status:** done
## Tujuan
Runner dua T4 untuk 5-fold/120 epoch, batch global 16, dengan checkpoint/resume dan hasil CV yang dapat diunduh.
## Ruang Lingkup
- kaggle_benchmark/full_training: worker, launcher, metadata private.
- docs/TRAINING_KAGGLE.md, output smoke, CHANGELOG.md.
- Tidak menjalankan full training, mengubah dataset, atau menghentikan Windows.
## Langkah
1. Implementasikan DDP static graph/fused optimizer yang telah diuji, split seed42, AMP, weighted CE global.
2. Checkpoint atomic tiap 5 epoch dan akhir fold (model, optimizer, scaler, RNG tiap rank, fold/epoch/config); simpan model, prediksi, metrik tiap fold dan OOF final.
3. Resume dari output lokal yang disalin dari dataset checkpoint private; validasi config dan fingerprint input, output terpisah smoke.
4. Uji Kaggle singkat: 2 langkah epoch1, restart dari checkpoint, epoch2 dan evaluasi; smoke tidak dianggap CV penuh.
5. Dokumentasikan cara mulai, status, unduh dan resume; catat hasil nyata.
## Risiko & Asumsi
- Job terputus dapat kehilangan epoch sejak checkpoint terakhir; hasil session gagal belum tentu tersedia dari Kaggle.
- Resume memerlukan checkpoint yang berhasil diunduh/disimpan sebagai input; tidak menjamin pemulihan crash server.
- Lima model + optimizer checkpoint memerlukan beberapa GB output; kuota/storage dipantau oleh user.
- Benchmark 2,6 jam belum termasuk I/O checkpoint; verifikasi smoke bukan kualitas model akhir.
## Verifikasi
Syntax, dua rank aktif, encoder update, checkpoint load optimizer/scaler/RNG, epoch resume benar, fold prediksi 148 dan file metrik, output smoke terpisah dari full.

## Progres
Smoke versi1 gagal float64 class weights; diperbaiki explicit torch.float32 sesuai benchmark, diuji ulang sebelum dinyatakan siap.

## Hasil
Smoke versi2 COMPLETE: checkpoint epoch1 disimpan, torchrun baru memuat model/optimizer/scaler/RNG dan melanjutkan epoch2. Kedua encoder diperbarui, prediksi/metrik148sampul tersimpan. JSON/NPZ/log diunduh dan diverifikasi; model/checkpoint smoke tetap pada output private Kaggle. Full launcher syntax valid, konfigurasi5fold/120epoch dan output terpisah; full belum dimulai.
