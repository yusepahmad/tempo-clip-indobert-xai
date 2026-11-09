# Keputusan J01 — Auxiliary Hierarki Task 2

J01 menambahkan head biner `NON_METAFORA` versus metafora sebagai auxiliary
loss saat training. Metadata auxiliary tidak digunakan sebagai input maupun
output inference; model final tetap satu graph dengan keluaran Task 2 tujuh
kelas.

| Task | Macro-F1 |
| --- | ---: |
| Task 1 | 0.504971 |
| Task 2 | 0.385758 |
| Task 3 | 0.370704 |
| Minimum | 0.370704 |

Keputusan: **stop J01**. Nilai minimum lebih rendah daripada E42 (`0.395560`)
dan auxiliary hierarchy tidak memperbaiki Task 2. Tidak dilakukan pencarian
tambahan pada outer OOF yang sama.
