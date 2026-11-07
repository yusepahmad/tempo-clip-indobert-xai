# Laporan Optimasi Joint Multitask

## Diagnostik negative transfer

| Eksperimen | Task 1 | Task 2 | Task 3 | Minimum | Keputusan |
| --- | ---: | ---: | ---: | ---: | --- |
| E42 joint baseline | 0.5255 | 0.3956 | 0.4034 | 0.3956 | Baseline terbaik |
| E48 single-task diagnostic | 0.4861 | 0.4185 | 0.3883 | 0.3883 | Diagnostik saja |
| E49 task-routed MMoE | 0.4949 | 0.3977 | 0.3695 | 0.3695 | Stop |
| M01 shared MLP | 0.4426 | 0.3592 | 0.3581 | 0.3581 | Stop |
| M04 SigLIP2 adapters | 0.5038 | 0.4222 | 0.3805 | 0.3805 | Stop |
| J01 Task-2 auxiliary | 0.5050 | 0.3858 | 0.3707 | 0.3707 | Stop |

E48 menunjukkan Task 2 single-task sedikit lebih baik daripada E42 joint,
tetapi Task 1 dan Task 3 tidak membaik. E49 membuktikan routing MMoE tidak
mengubah gap tersebut menjadi kenaikan minimum. J01 juga tidak mendukung
hipotesis hierarchical auxiliary.

## Keputusan

- E42 tetap kandidat joint terkunci sementara.
- Weighted CE, label smoothing, focal loss, task-relations, MMoE, shared MLP,
  dan auxiliary hierarchy sudah diuji; tidak ada yang melewati E42 menurut
  minimum Macro-F1.
- M02/M03, M04, dan augmentation sudah dinilai; tidak ada yang mengalahkan E42
  menurut minimum Macro-F1.
- Target tiga task ≥0,70 belum tercapai dan tidak diturunkan.
