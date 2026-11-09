# R30 — Augmentasi dan pemilihan inner

Selesai teknis; menunggu pemeriksaan pembimbing.

Bukti yang diserahkan. Dokumentasi parameter augmentasi, penjelasan pemilihan AUG_SELECTED, dan catatan pemeriksaan 30 contoh back-translation.

- [R30_AUGMENTATION_AUDIT.md](R30_AUGMENTATION_AUDIT.md) — Alasan pemilihan AUG_SELECTED memakai inner fold dan batas perbandingan
- [R30_ABLATION_PARITY.md](R30_ABLATION_PARITY.md) — Alasan pemilihan AUG_SELECTED memakai inner fold dan batas perbandingan
- [R30_protocol.json](R30_protocol.json) — Protokol/status rerun tanpa rotasi yang tersimpan
- [R30_completion.json](R30_completion.json) — Protokol/status rerun tanpa rotasi yang tersimpan
- [launch.py](launch.py) — Worker augmentasi historis sebagai sumber transform dan perbandingan rotasi
- [augmentation_controls.py](augmentation_controls.py) — Source ekstraksi ulang dan pemilihan pipeline inner pada revisi
- [moderate_no_rotation.py](moderate_no_rotation.py) — Fungsi transform aktual pada rerun, hash cocok dengan protocol.json
- [R30_parameter_dan_back_translation.md](R30_parameter_dan_back_translation.md) — Parameter aktual tiap arm dan penjelasan eksplisit tidak berlakunya pemeriksaan back-translation
- [R30_metrik_per_task.csv](R30_metrik_per_task.csv) — Macro-F1 utama, akurasi, precision/recall, kappa, CI dan scope per task
- [R30_uji_berpasangan.csv](R30_uji_berpasangan.csv) — Exact McNemar/Holm untuk akurasi dan CI bootstrap selisih Macro-F1; arah before→after dipertahankan
- [R30_seleksi_inner_per_fold.json](R30_seleksi_inner_per_fold.json) — Keputusan pipeline dan seluruh metadata fold aktual


