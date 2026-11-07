# MICRO-E13 — Hasil Pilot Joint QLoRA

**Kaggle:** version 1, COMPLETE.
**Epoch terpilih:** 3 dari 6, maksimum minimum Micro-F1 validation, mean sebagai
tie-breaker. Durasi worker 13.238,79 detik (sekitar 3 jam 41 menit).

| Task | Kontrol | E13 epoch 3 | Selisih poin persentase |
| --- | ---: | ---: | ---: |
| Task 1 | 55,46% | 72,27% | +16,81 |
| Task 2 | 49,58% | 58,82% | +9,24 |
| Task 3 | 55,46% | 68,07% | +12,61 |
| Minimum | 49,58% | 58,82% | +9,24 |

## Keputusan

Lulus gate praktis pilot yang dibekukan sebelum hasil diambil: minimum naik
setidaknya 3 poin dan tidak ada task turun lebih dari 3 poin. Pipeline layak
dievaluasi lebih lanjut dengan prosedur outer-fold training yang dikunci.

Ketiga skor berasal dari satu adapter dan satu epoch yang sama. Skor maksimum
per-task dari epoch berbeda tidak digabung menjadi klaim model.

Ini adalah hasil inner-validation 119 sampel, dipakai memilih epoch, dengan
473 sampel inner-training. Outer-test 148 sampel belum dievaluasi. Target
Micro-F1 0,70 untuk masing-masing task pada 740 OOF belum terbukti.

Task 2 tetap menjadi bottleneck. Perlu evaluasi OOF untuk mengukur generalisasi
sebelum mengganti kandidat/model aplikasi. Macro-F1 validation epoch terpilih:
`0,6299 / 0,5151 / 0,5348`.

## Verifikasi dan artefak

CSV validation cocok dengan result/log, 119 ID unik dan split kontrol sama;
label, hash source/prediksi, pemilihan epoch dan metrik diverifikasi lokal.
Metrik/prediksi/log sudah disimpan. Unduhan checkpoint besar tertunda karena
transfer tidak bergerak; checkpoint tetap tersedia di output Kaggle.
