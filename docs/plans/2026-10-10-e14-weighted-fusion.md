# E14 fusi berbobot E5, BGE-M3 dan CLIP

**Tanggal:** 2026-10-10
**Status:** done

## Tujuan
Menguji informasi yang saling melengkapi dari dua encoder teks dan gambar setelah E13 mencapai nested0,5477/kandidat tetap0,5549. Target tetap Macro-F1 OOF Task2 minimal0,70.

## Ruang Lingkup
- `DEMO_XAI_745_FULL/01_notebook/e14_weighted_fusion.py`, auditor terpisah `01_notebook/e14_weighted_fusion_verify.py`, hasil `04_hasil_eksperimen/e14_weighted_fusion/`, salinan learn/recovery, plan/changelog.
- Fitur beku terverifikasi E06 description+source_reason (1536), E13 combined (1024), CLIP asli (512). Data/label/produksi tidak berubah; tidak memakai fitur dari prediksi OOF supervised, deskripsi/mapping anotator atau memindahkan bobot model ke server.
- Satu CPU/BLAS1, tidak memakai GPU atau mengubah/menghentikan pemantau E12.
- Pemantau terpisah `01_notebook/monitor_e14.py` dan status/log `04_hasil_eksperimen/e14_monitor/`; tidak mengubah worker aktif.

## Langkah
1. Validasi hash dataset/NPZ/ID dan referensi E13 yang sudah diaudit. Split outer baseline5 seed42, inner3 stratified Task2 seed42, identik E13.
2. Transformer pipeline fit StandardScaler terpisah per blok hanya pada data training yang sedang dipakai; L2-normalize setiap blok, lalu gabungkan berbobot. BGE weight1, E5 weight[0,0.5,1,2], CLIP weight[0,0.5,1,2].
3. Grid inner-CV RBF-SVC C[1,10,100], gamma[scale,0.1,1], class_weight[None,balanced], seluruh bobot ikut dipilih inner. Refit outer-training lalu prediksi outer-test sekali. Catat grid score, params, split dan740 OOF weighted-family.
4. Kandidat kontrol lima keluarga E13 memakai artefak fit yang sudah selesai dengan split/inner seed/data sama, tanpa retraining atau melatih meta-model dari OOF. Per outerfold pilih keluarga terbaik dari lima kontrol dan weighted-family hanya berdasarkan inner-score yang sebanding. Simpan740 nested OOF dan provenance/hash referensi.
5. Lock satu instance, checkpoint tiapfold dengan signature source/protokol/hash/split; resume hanya jika cocok. Audit seluruh ID/fold/label, pemilihan bobot/keluarga dan skor manual, hash salinan sebelum klaim.
6. Auditor terpisah menunggu semua740 output lengkap, menghitung ulang inner-CV hanya untuk parameter terpilih, lalu refit outer-training dan mereproduksi prediksi tiapfold. Bandingkan checkpoint/routing kontrol dan hitung ulang TP/FP/FN; tidak mengulang seluruh pencarian grid atau mengubah worker aktif.
7. Jalankan satu pemantau dengan lock dan identitas PID/starttime worker. Poll45s; setelah worker terminal dan seluruh artefak lengkap, jalankan auditor sekali, simpan status exit/hash. Worker hilang tanpa output, PID dipakai ulang, atau audit gagal menghasilkan needs_root_audit; tidak restart training. Log pemantau/auditor berada di folder terpisah agar manifest output E14 tidak berubah ketika audit menulis log.

## Risiko & Asumsi
- Fusi bisa menambah noise atau overfit; family/weights tidak dipilih berdasarkan outer-test. Riset berulang tetap memiliki bias pemilihan antar eksperimen.
- Normalisasi perblok berbeda dari E13; lima keluarga E13 dipertahankan sebagai kontrol terpisah. Perbandingan inner menggunakan split/metric identik.
- Grid288kombinasi perfold dapat memerlukan CPU beberapa menit hingga jam; tidak mengurangi protokol atau mengulang proses hidup karena log sementara kosong.

## Verifikasi
Kompilasi; transform fit hanya innertrain melalui Pipeline/GridSearchCV; hash/ID/finite input. Checkpoint lima outerfold, inner score/params, kontrol referencehash cocok, setiap output740unik tepat baselinefold/label; hitung ulang Macro-F1 dan routing keluarga secara independen.

## Implementasi dan verifikasi awal
- Worker selesai dan dikompilasi; SCP ditunggu sampai selesai sebelum launch. Aktif di server`.31`, tmux `tempo-e14`, PID2652448, satu CPU/BLAS1.
- Pemeriksaan signature/protocol/lock aktual lolos; worker SHA02588b6fcd4bdbe21be4b17e9d60dcfcdebfbf0b97246056a88b4804febfb6e5. Hash dataset/E5/BGE/CLIP/reference-verification cocok dan input740x3072 finite/ID exact sebelum search dimulai.
- Grid288kombinasi perfold, inner3. Belum ada OOF lengkap atau klaim skor baru. E12 fold1/2 dan pemantau tetap aktif; tidak memakai tambahan GPU.
- Checkpoint fold1 selesai dalam498,16s. Inner memilih weighted-family0,5556961, di atas kontrol inner tertinggi0,5473870; C1/gamma0,1/balanced/E5weight0,5/CLIPweight1. Ini skor inner pemilihan model, bukan skor OOF lengkap atau bukti target0,70.
- Auditor terpisah selesai dibuat dan dikompilasi; SHA256 lokal/server identik `f86265f3248a7dd33099116bdb10eb5c111d1ed31913a67c0ee26bdaea8b2c1a`. Audit hasil aktual menunggu kedua artefak740 OOF lengkap. Fold2 worker selesai503,05s, proses melanjutkan fold3; tidak ada klaim skor OOF baru.
- Pemantau audit aktif di tmux `tempo-e14-monitor`, PID2901954, mengadopsi worker2652448/startticks200677587. Kompilasi/source SHA256 lokal-server `d27394d38f93f56a38e81c63d52ffd0b0a07cc176234c93f41b91f88cf4c99d7` cocok. State aktual watching; audit belum dijalankan karena worker masih aktif. Fold3 selesai495,77s dan memilih kontrol description_reason via inner; fold4 sedang dihitung.

## Hasil akhir
- Kelima fold selesai (498,16/503,05/495,77/499,60/502,81s). OOF keluarga fusi berbobot **0,5662691391334344** menjadi kandidat tetap terbaik; nested pemilihan enam keluarga **0,550917426557633**. Keduanya di bawah0,70 dan tidak dipertukarkan dalam pelaporan.
- Routing inner: weighted/weighted/description_reason/weighted/semantic_visual. Fusi memakai C1/balanced semua fold, gamma0,1 pada fold1–4 dan scale fold5; bobot E5 0,5/0,5/2/2/1, CLIP1/1/1/1/0,5.
- Auditor aktual selesai: inner-CV parameter terpilih dihitung ulang, refit outer-training mereproduksi seluruh740 prediksi, routing kontrol dan TP/FP/FN/confusion matrix cocok. Tidak mengulang keseluruhan grid. Pemantau berakhir `verified_ready_for_root_copy_audit`.
- Bukti `docs/server-recovery/2026-10-10/e14_weighted_fusion/verification.json`, SHA256 `3bcb7e4e22cb744c41d088e643dfac936796bde2248df14ca22878fa26df40db`. Sebelas hash salinan cocok; penghitungan stdlib terpisah di lokal mengonfirmasi kedua Macro-F1 dan148 sampel/fold. Log audit/state disalin terpisah di `e14_monitor/`.
- E12 masih berjalan; E15 tetap disiapkan untuk slot GPU berikutnya. Dataset/label/produksi tidak berubah. Goal keseluruhan masih aktif karena target belum tercapai.
