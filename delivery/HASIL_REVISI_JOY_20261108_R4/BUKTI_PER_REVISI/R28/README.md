# R28 — Prediksi baseline/unimodal

Selesai teknis; menunggu pemeriksaan pembimbing.

Bukti yang diserahkan. Empat berkas predictions.csv untuk ablasi unimodal, dan tabel uji McNemar multimodal versus unimodal.

- [01_majority/predictions.csv](01_majority/predictions.csv) — Satu dari empat prediksi canonical baseline; 740 ID × tiga task, model=MAJORITY_TRAIN_FOLD
- [02_image_only/predictions.csv](02_image_only/predictions.csv) — Satu dari empat prediksi canonical baseline; 740 ID × tiga task, model=RII_FROZEN_IMAGE_ONLY
- [03_text_supporting/predictions.csv](03_text_supporting/predictions.csv) — Satu dari empat prediksi canonical baseline; 740 ID × tiga task, model=RII_FROZEN_TEXT_SUPPORTING
- [04_multimodal/predictions.csv](04_multimodal/predictions.csv) — Satu dari empat prediksi canonical baseline; 740 ID × tiga task, model=RII_FROZEN_MTL_WEIGHTED
- [kontrol_tail_tambahan/01_multimodal/predictions.csv](kontrol_tail_tambahan/01_multimodal/predictions.csv) — Kontrol E42-family pada resep baru yang diberi label terpisah; model=RII_TAIL_MTL_WEIGHTED
- [kontrol_tail_tambahan/02_image_only/predictions.csv](kontrol_tail_tambahan/02_image_only/predictions.csv) — Kontrol E42-family pada resep baru yang diberi label terpisah; model=RII_TAIL_IMAGE_ONLY
- [kontrol_tail_tambahan/03_text_supporting/predictions.csv](kontrol_tail_tambahan/03_text_supporting/predictions.csv) — Kontrol E42-family pada resep baru yang diberi label terpisah; model=RII_TAIL_TEXT_SUPPORTING
- [kontrol_tail_tambahan/04_majority/predictions.csv](kontrol_tail_tambahan/04_majority/predictions.csv) — Kontrol E42-family pada resep baru yang diberi label terpisah; model=MAJORITY_TRAIN_FOLD
- [model_utama_historis/predictions.csv](model_utama_historis/predictions.csv) — Referensi OOF model utama historis E42; bukan hasil ablation resep baru
- [R28_metrik_per_task.csv](R28_metrik_per_task.csv) — Macro-F1 utama, akurasi, precision/recall, kappa, CI dan scope per task
- [R28_uji_berpasangan.csv](R28_uji_berpasangan.csv) — Exact McNemar/Holm untuk akurasi dan CI bootstrap selisih Macro-F1; arah before→after dipertahankan
- [R28_HISTORICAL_REPLAY.md](R28_HISTORICAL_REPLAY.md) — Baseline direplay identik; keluarga frozen dan E42-tail tidak disamakan
- [R28_ABLATION_PARITY.md](R28_ABLATION_PARITY.md) — Baseline direplay identik; keluarga frozen dan E42-tail tidak disamakan


