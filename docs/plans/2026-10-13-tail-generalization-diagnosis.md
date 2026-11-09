# Diagnosis train versus held-out tail MTL

**Tanggal:** 2026-10-13
**Status:** done

## Tujuan
Mengukur gap train/outer-test dari checkpoint E42 sebelum menambah kompleksitas model. Menghindari grid tanpa diagnosis untuk target semua3task0,70.

## Ruang Lingkup
- Utility `01_notebook/tail_graph_audit/generalization.py` dan hasildiagnosisE42/changelog.
- InferenceCPU saja, tanpa retraining/pemilihan ulang checkpoint/config, tanpa mengganti data/label/E44livejob/delivery.

## Langkah
1. Verifikasi canonicalauditpassed, source/cache/checkpointSHA, splitprovenance.
2. Forward semua740sample setiap5checkpointCPUFP32; prediksi outertest wajib identik canonicalOOF.
3. Hitung train/test Macro-F1 dan confidence pertask/perfold serta meanfold gap. Training score bukan OOF dan bukan hasil kualitas generalisasi.
4. Catat keterbatasan diagnosis repeatedcorpus; gunakan sebagai evidence rancangan berikutnya, bukan memilih ulang E42.

## Risiko & Asumsi
Train/test gap dapat dipengaruhi samplecount/kelaslangka; tidak membuktikan sebab. Tidak mengklaim trainF1 sebagai benchmark atau mengubah reportedOOF.

## Verifikasi
Checkpoint/input/source SHA,5fold disjoint740samplecoverage, canonicalheldoutpredparity,3task metrics finite/range. Data/fit/weights tidakdiubah.

## Hasil
Audit inference5×740CPUFP32 lulus, heldoutpredsidentikcanonicalOOF. Mean fold train-minus-heldout Macro-F1 gap: Task1 0,427854927; Task2 0,603535574; Task3 0,579623754. TrainMacroF1sekitar0,90–1,00. Evidence kuat gap generalisasi; bukan bukti sebab tunggal/noisylabels. Prioritas regularisasi/augmentasi model setelah E44, bukan memperbesar kapasitas tanpa evidence. File `04_hasil_eksperimen/e42_tail_grid/generalization_diagnosis.json`.
