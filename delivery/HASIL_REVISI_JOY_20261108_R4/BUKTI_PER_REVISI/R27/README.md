# R27 — MTL versus single-task dan loss aktual

Selesai teknis; menunggu pemeriksaan pembimbing.

Bukti yang diserahkan. Tabel perbandingan MTL versus single-task per task, dan potongan kode fungsi Joint Loss yang sebenarnya dijalankan.

- [R27_metrik_per_task.csv](R27_metrik_per_task.csv) — Macro-F1 utama, akurasi, precision/recall, kappa, CI dan scope per task
- [R27_uji_berpasangan.csv](R27_uji_berpasangan.csv) — Exact McNemar/Holm untuk akurasi dan CI bootstrap selisih Macro-F1; arah before→after dipertahankan
- [R27_ABLATION_PARITY.md](R27_ABLATION_PARITY.md) — Kontrak shared MTL versus tiga model independen dan definisi loss
- [R27_R18_ARSITEKTUR_JOINT_LOSS.md](R27_R18_ARSITEKTUR_JOINT_LOSS.md) — Kontrak shared MTL versus tiga model independen dan definisi loss
- [worker.py](worker.py) — Source worker E42 historis lengkap, tidak ditulis ulang sebagai training baru
- [tail_ablation_worker.py](tail_ablation_worker.py) — Source controlled rerun MTL/single-task yang benar-benar menghasilkan prediksi baru
- [R27_joint_loss_yang_dijalankan.py.txt](R27_joint_loss_yang_dijalankan.py.txt) — Potongan fungsi epoch/Joint Loss aktual


