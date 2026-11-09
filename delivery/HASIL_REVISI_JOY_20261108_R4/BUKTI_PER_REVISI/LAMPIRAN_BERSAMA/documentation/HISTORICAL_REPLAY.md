# Pemulihan prediksi baseline

RII_FROZEN_MTL_WEIGHTED mereplikasi120 epoch full-batch, seed42, shared256/ReLU/dropout0.4, AdamW1e-3/wd1e-4, class weights training-only, CLIP-B32+IndoBERT CLS beku, dan lima fold yang sama. Prediksi ketiga task identik terhadap kolom baseline E42 pada seluruh740 sampel (0perbedaan). Image-only dan text-only juga menghasilkan metrik historis yang sama, kini dengan prediksi mentah lengkap. Single-task/tanpa weighting/headline-only/rich128 adalah kontrol baru yang diberi nama terpisah, bukan angka historis yang ditulis ulang. Text-only supporting sebenarnya sudah ada pada extractor lama; headline-only ditambahkan sebagai kontras input yang jelas.

Keluarga ini adalah ablation baseline CLIP-B32 beku, bukan ablasi E42 yang memiliki CLIP-L14 dan tail teks trainable. Ablasi E42-family baru berada pada RII_TAIL_*. Semua sumber/seed/fold/OOF dipertahankan.
