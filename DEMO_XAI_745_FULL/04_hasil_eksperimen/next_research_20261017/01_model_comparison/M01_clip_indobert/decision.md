# Keputusan M01 — Frozen CLIP-L14 + IndoBERT Shared MLP

M01 adalah kontrol arsitektur joint sederhana dengan tiga head, dinilai memakai
outer fold E42 yang sama dan pemilihan konfigurasi melalui inner 3-fold.

| Task | Macro-F1 |
| --- | ---: |
| Task 1 | 0.442571 |
| Task 2 | 0.359185 |
| Task 3 | 0.358120 |
| Minimum | 0.358120 |

Keputusan: **stop M01**. Minimum Macro-F1 lebih rendah daripada E42
(0.395560), sehingga M01 tidak dipromosikan ke augmentation. Hasil ini
menunjukkan bahwa penyederhanaan head pada fitur beku tidak menyelesaikan
negative transfer. Kandidat berikutnya harus menguji representasi visual lain
(M02/M03), bukan menambah pencarian hyperparameter M01 pada OOF yang sama.
