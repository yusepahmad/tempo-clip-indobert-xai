# E21 fusi kernel semantik dan leksikal sparse

**Tanggal:** 2026-10-11
**Status:** done

## Tujuan
Menguji kontribusi leksikal tanpa kompresi SVD pada fitur frozen terbaik untuk target Task2 Macro-F1 minimal0,70. E09 memakai SVD128 dan E17 tidak memakai fitur leksikal; E21 menguji kombinasi yang berbeda tanpa API/GPU.

## Ruang Lingkup
- `DEMO_XAI_745_FULL/01_notebook/e21_sparse_kernel.py` dan `e21_sparse_kernel_verify.py`, hasil/recovery E21, plan/changelog.
- Tidak mengubah dataset/label, E19/E20 aktif, atau menggunakan prediksi supervised OOF sebagai fitur.

## Langkah
1. Pin helper input E16/E14 dan seluruh sumber E5/BGE/CLIP/E01 asli. Teks hanya deskripsi/sumber/alasan E01 dan headline/support asli, tanpa annotation/mapping label. Cocokkan740 IDs dan baseline folds.
2. Pada setiap inner/outer-training: fit StandardScaler perblok numerik lalu L2; fit TF-IDF word1–2/char3–5 min_df2, cap12000/24000 dan L2 gabungan tanpa SVD. Heldout hanya transform. Precompute squared distances/linear lexical Gram per split, bukan fit global.
3. Kernel PSD positif `(RBF_semantik + lambda * cosine_TFIDF)/(1+lambda)`. E5weight[0,5;2], CLIPweight[0,5;1], BGE1, gamma[0,1;1], lambda[0;0,25;1;4], C[1;10;100], classweightNone/balanced=192grid. Lambda0 kontrol tanpa lexical.
4. Inner3 Task2 seed42 memilih meanF1/argmax pertama; outer5 Task1 baseline seed42 menghasilkan OOF740. Simpan seluruh grid/inner scores, indeks training/test, fit metadata, sumber/hash, checkpoint immutable dan output tujuhkelas.
5. Auditor mereproduksi inner3 terpilih/refit5, metadata scaler/vocab/idf training, gridorder/argmax, prediksi740 dan manual7x7/F1. Tidak mengulang seluruh grid. Audit salinan root wajib sebelum klaim.
6. Kompilasi/hash server dan uji sintetis split/scaler/vocab/idf/heldout-transform invariance, kernel simetris/PSD/kontrollambda0, predict/192grid. Full baru dijalankan sesudah E20 terminal+verified di bawah0,70; persiapan tidak memulai training/API.

## Risiko & Asumsi
- Leksikal bisa overfit; innerfit vocabulary/idf wajib tanpa heldout. Semua fitur teacher frozen input-only; tidak memakai annotationdeskripsi manusia.
- Precompute hanya transform tanpa labels dari current training split; grid memakai innerlabels, outerlabels hanya evaluasi. Kernel dipakai SVCprecomputed secara konsisten train-train/test-train.
- Evaluasi berulang menyebabkan selection bias; tidak menjamin0,70. Data/label/fold tetap dan tidak mengklaim full grid/inference direproduksi.

## Verifikasi
Asli source/data/hash; seluruh740 sample dan5x148 heldout (592training),3inner folds training-only,192grid, sparseTFIDF tanpaSVD, metadata/prediksi/F1/manualscore. Semua hasil aktual dicatat sesudah implementasi/audit.

## Persiapan terverifikasi dan gerbang full
- Worker SHA256d1e9330e8f62cce1431b2affdd74e99858fe08ea447a0fabb8cca57c8f32e20f; auditor afc0eb7c8496afb3292cffbe229256b33fc7ed576aa096536a4a108f15c1c5e0 lokal/server cocok, compile lolos.
- Uji sintetis70 sampel: heldoutnumeric/text perturbation tidak mengubah metadata/trainkernels; trainingperturbation mengubah fit; kernel simetris/PSD, kontrollambda0 tidak bergantung lexical, shape/predict14 dan192grid lolos. Fixture terisolasi menolak E20missing dan target>=0,70 tanpa training.
- E20 selesai ketika tes gate berjalan; asumsi missing awal tes tidak berlaku, bukan kegagalan implementasi. Tes ulang fixture dan load real740 sumber/folds lolos, belum membuat direktori hasil E21. Bukti server `04_hasil_eksperimen/e21_preparation.json`.
- E20 telah diaudit server dan root:0,5617121910, source/results/manualF1 cocok, proses terminal. Kondisi launch full terpenuhi; jalankan satuCPU worker dan auditor chained tanpa API/GPU. Tidak mengubah grid setelah melihat outertest E21.
- Worker1423858 aktif di tmux tempo-e21; auditor chained setelah exit0. Salinan preparation/sourcepins diperiksa lokal di `docs/server-recovery/2026-10-11/e21_sparse_kernel/e21_preparation.json`. Belum ada klaim skor E21; trainingaktual dimulai sesudah snapshot preparation yang menyatakan false.
- Worker dan auditor kini terminal, server menghasilkan verification verified740 dengan Macro-F1 0,551761622460454. Langkah berikut: salin sembilan berkas hasil tanpa kredensial, verifikasi delapan hash manifest/source pins, seluruh ID/truth/fold terhadap E14, routing train/test/argmax grid, dan hitung manual confusion/F1. Simpan root_verification.json; tidak mengulang seluruh grid atau inference. Setelah cocok, tandai done dan catat changelog/sinkronkan dokumentasi server.
- Audit root selesai:8 hash manifest/current worker+auditor+helper pins cocok;740 ID/truth/baselinefold dan5partisi592/148/prediksi,192grid firstargmax/choseninner cocok. Manual7kelas Macro-F1=0,551761622460454. Bukti `docs/server-recovery/2026-10-11/e21_sparse_kernel/root_verification.json`. Fold1–3 memilih lexical_weight0, fold4–5 memilih0,25. Belum mengungguli E14fixed0,5662691391 dan target0,70. Fullgrid tidak diulang; risiko selectionbias eksperimen berulang tetap berlaku.
