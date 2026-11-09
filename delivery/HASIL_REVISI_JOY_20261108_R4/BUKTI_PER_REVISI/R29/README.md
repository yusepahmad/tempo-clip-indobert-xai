# R29 — Backbone dan SigLIP2

Selesai teknis; menunggu pemeriksaan pembimbing.

Bukti yang diserahkan. Tabel ablasi backbone per task dengan uji McNemar, dan pernyataan varian CLIP yang dipakai model utama.

- [R29_metrik_per_task.csv](R29_metrik_per_task.csv) — Macro-F1 utama, akurasi, precision/recall, kappa, CI dan scope per task
- [R29_uji_berpasangan.csv](R29_uji_berpasangan.csv) — Exact McNemar/Holm untuk akurasi dan CI bootstrap selisih Macro-F1; arah before→after dipertahankan
- [R29_ABLATION_PARITY.md](R29_ABLATION_PARITY.md) — Varian CLIP ViT-L14 utama dan perbedaan parity antar keluarga
- [R29_MAIN_MODEL_DECISION.md](R29_MAIN_MODEL_DECISION.md) — Varian CLIP ViT-L14 utama dan perbedaan parity antar keluarga
- [train_backbone_controls.py](train_backbone_controls.py) — Source kontrol backbone dengan dimensi head/input yang setara


