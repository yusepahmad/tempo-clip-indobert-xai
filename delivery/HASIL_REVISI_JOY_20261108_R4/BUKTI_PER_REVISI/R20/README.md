# R20 — Diagnosis Task3 dan weighting

Selesai teknis; menunggu pemeriksaan pembimbing.

Bukti yang diserahkan. Dua confusion matrix, tabel distribusi prediksi versus gold, angka entropi, dan tabel hasil sebelum dan sesudah class weighting.

- [R20_confusion_BASELINE_CLIP_INDoBERT.png](R20_confusion_BASELINE_CLIP_INDoBERT.png) — Confusion matrix Task 3 untuk diagnosis baseline/E11 dan pembanding model utama E42
- [R20_confusion_BASELINE_CLIP_INDoBERT.csv](R20_confusion_BASELINE_CLIP_INDoBERT.csv) — Confusion matrix Task 3 untuk diagnosis baseline/E11 dan pembanding model utama E42
- [R20_confusion_MICRO_E11_hierarchical_task3.png](R20_confusion_MICRO_E11_hierarchical_task3.png) — Confusion matrix Task 3 untuk diagnosis baseline/E11 dan pembanding model utama E42
- [R20_confusion_MICRO_E11_hierarchical_task3.csv](R20_confusion_MICRO_E11_hierarchical_task3.csv) — Confusion matrix Task 3 untuk diagnosis baseline/E11 dan pembanding model utama E42
- [R20_confusion_e42_tail_grid.png](R20_confusion_e42_tail_grid.png) — Confusion matrix Task 3 untuk diagnosis baseline/E11 dan pembanding model utama E42
- [R20_confusion_e42_tail_grid.csv](R20_confusion_e42_tail_grid.csv) — Confusion matrix Task 3 untuk diagnosis baseline/E11 dan pembanding model utama E42
- [R20_distribusi_gold_prediksi_task3.csv](R20_distribusi_gold_prediksi_task3.csv) — Jumlah/proporsi gold versus prediksi
- [R20_entropi_task3.csv](R20_entropi_task3.csv) — Entropi dan proporsi kelas mayoritas
- [R20_perbandingan_class_weighting.csv](R20_perbandingan_class_weighting.csv) — Macro-F1 utama, akurasi, precision/recall, kappa, CI dan scope per task
- [R20_uji_berpasangan.csv](R20_uji_berpasangan.csv) — Exact McNemar/Holm untuk akurasi dan CI bootstrap selisih Macro-F1; arah before→after dipertahankan
- [R20_ABLATION_PARITY.md](R20_ABLATION_PARITY.md) — Batas parity: frozen dan tail adalah dua keluarga kontrol terpisah
- [R20_confusion_MICRO_E14_joint_qlora_oof.png](R20_confusion_MICRO_E14_joint_qlora_oof.png) — Confusion matrix Task 3 pembanding E14 QLoRA; melengkapi baseline, E11 dan E42.
- [R20_confusion_MICRO_E14_joint_qlora_oof.csv](R20_confusion_MICRO_E14_joint_qlora_oof.csv) — Confusion matrix Task 3 pembanding E14 QLoRA; melengkapi baseline, E11 dan E42.

Versi FULL menampilkan empat confusion matrix: baseline, E11, E42, dan pembanding E14 tambahan. Distribusi/entropi semua empat model juga tersedia di notebook 02 dan analysis/.
