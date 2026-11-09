# Parameter augmentasi dan catatan pemeriksaan

| Arm baru | Brightness | Contrast | JPEG quality | Noise Gaussian σ | Rotasi | Sampling |
|---|---|---|---|---|---|---|
| A00 clean | tidak diubah | tidak diubah | tidak direkompresi augmentasi | 0 | 0 | n training draws |
| A01 light | Uniform(0.92,1.08) | Uniform(0.92,1.08) | integer 88–96 | 1.5 | 0 | n draws, 50% clean/50% fixed augmentation |
| A02 moderate no rotation | Uniform(0.85,1.15) | Uniform(0.85,1.15) | integer 78–90 | 3.0 | 0; draw RNG lama tetap dikonsumsi | n draws, 50% clean/50% fixed augmentation |
| A03 light sampler | sama dengan light | sama dengan light | sama dengan light | 1.5 | 0 | replacement n draws, joint inverse-sqrt sampler |

Seluruh arm baru 35 epoch, batch 32, head 192/LN/GELU/dropout0.25 dan optimizer sama; validation/test bersih. Tidak ada geometric crop pada transform augmentasi. Resize/preprocessing encoder dibedakan dari augmentasi. Worker lama moderate memakai rotasi ±2 derajat; file moderate_no_rotation.py adalah fungsi aktual setelah rotasi dinolkan, dengan hash cocok protokol.

Pemilihan pipeline memakai mean Macro-F1 pada dua inner folds, bukan skor outer tertinggi. Karena itu AUG_SELECTED boleh lebih rendah dari A01 pada outer. Mengganti pemenang setelah melihat outer akan menggunakan test untuk seleksi. Rerun juga menyamakan jumlah update/paparan; selisih lama versus baru bukan efek rotasi tunggal.

## Status permintaan 30 contoh back-translation
**Tidak berlaku pada pipeline yang dijalankan: back-translation tidak digunakan.** Tidak ada 30 hasil back-translation untuk dinilai. Source/protokol disertakan supaya keputusan ini dapat diperiksa. Tidak dibuat terjemahan baru dan tidak diklaim sebagai 30 pemeriksaan manusia historis. Jika back-translation ditambahkan pada versi berikutnya, audit manusia harus dilakukan sebelum hasilnya dipakai.
