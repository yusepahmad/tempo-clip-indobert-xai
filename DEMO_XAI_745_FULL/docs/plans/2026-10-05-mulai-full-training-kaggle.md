# Mulai Full Training Kaggle
**Tanggal:** 2026-10-05
**Status:** done
## Tujuan
Menjalankan full training yang telah diminta user: dua T4, 5 fold × 120 epoch.
## Ruang Lingkup
- Submit kernel private tempo-full-training versi pertama; runner yang sudah diuji tidak diubah.
- docs/TRAINING_KAGGLE.md, bukti peluncuran/status, CHANGELOG.md.
- Tidak mengubah dataset atau training Windows.
## Langkah
1. Cek quota dan pastikan tidak meluncurkan job duplikat.
2. Push launcher full dengan GPU T4 dan timeout6jam.
3. Verifikasi status server dan log awal bila tersedia; dokumentasikan link serta cara pantau.
## Risiko & Asumsi
- Estimasi2,6jam belum termasuk checkpoint/evaluasi; timeout6jam.
- Job server-side; log CLI mungkin baru tersedia setelah selesai. Status RUNNING saja tidak membuktikan epoch telah dimulai.
- Pemulihan hanya dari checkpoint yang berhasil tersedia sebagai output.
## Verifikasi
API push sukses, kernel private, konfigurasi full (smoke false), status server aktual; jangan mengklaim selesai sebelum hasil CV lengkap.

## Hasil
Quota29,82jam; full launcher smokefalse/fresh start diperiksa. Push versi1 sukses, server RUNNING. Log epoch belum tersedia; job belum selesai. Bukti status dan link disimpan; task peluncuran selesai, hasil eksperimen menunggu job.
