# E42 nested tail grid

Menggunakan cache frozen-front/CLIP E41 yang sudah teraudit. Model tetap joint CLIP–IndoBERT dengan dua tail blok trainable, shared head dan tiga task losses positif.

Enam kandidat encoder LR [2e-6,2e-5,1e-4] × task loss [1:1:1,1:2:2], epoch [0,2,4,8,12,24]. Semua kandidat memakai outertraining yang sama dan dua inner folds. Pemilihan memaksimalkan minimum mean inner Macro-F1 ketiga task; ties config pertama lalu epoch pertama. Model direset sebelum setiap fit. Tidak memilih config memakai outer test.

GPU AMP OOF provisional. Setelah kernel full COMPLETE:

```sh
python verify_result.py ../e41_cached_tail/cache E42_GPU_OUTPUT
python root_verify.py E42_GPU_OUTPUT
```

Gunakan path cache aktual, bukan contoh relatif bila menjalankan dari folder lain. Evaluator memeriksa semua enam candidate traces/splits, memilih ulang config/epoch secara independen, memeriksa SHA checkpoint, lalu merekonstruksi seluruh740OOF CPU FP32 sebagai presisi canonical yang ditetapkan sebelum hasil tersedia. Pelatihan GPU tidak direproduksi penuh; trace audit bersifat struktural. Root auditor memakai stdlib untuk Macro-F1 dan input/output hashes.

Kontrak full encoder/unggahan baru/XAI mengikuti [E41 README](../e41_cached_tail/README.md). Pilihan config dapat berbeda antarouterfold; config produksi dan epoch harus dipilih training-only sebelum refit seluruh740. Checkpoint CV bukan otomatis production release. Target semua task≥0,70, XAI fullgraph, unggahan baru, clean install dan QA belum terbukti oleh smoke.

Tidak mengubah data/label/outerfold atau delivery aktif. Kaggle hanya kuota gratis. Laporkan keterbatasan repeated experiment selection pada korpus740 yang sama.
