# Laporan Final OCR

Laporan ini hanya merangkum acceptance set yang sudah dibuka. Tidak ada parameter selector yang dituning dari holdout tersebut.

| Set | N | Exact | CER | Token-F1 | P50 | P95 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| holdout_1 | 80 | 60/80 (75.00%) | 0.2492 | 0.8458 | 1.996s | 8.114s |
| holdout_2 | 90 | 69/90 (76.67%) | 0.0812 | 0.8663 | 2.372s | 8.690s |
| independent | 60 | 43/60 (71.67%) | 0.1635 | 0.8373 | 2.116s | 7.916s |

## Keputusan

- Gate exact match ≥80% **belum lulus** pada dua holdout utama (75,00% dan 76,67%).
- Holdout yang sudah dibuka tidak boleh digunakan lagi untuk memilih aturan selector.
- Acceptance baru yang sah memerlukan gambar prospektif yang belum pernah dipakai. Dengan data yang dinyatakan tetap, pengujian itu belum tersedia.
- Pengujian manusia dan clean-Windows tetap merupakan acceptance eksternal yang harus dilakukan pengguna.
