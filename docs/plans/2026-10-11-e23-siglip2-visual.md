# E23 fitur visual frozen SigLIP2 di CPU

**Tanggal:** 2026-10-11
**Status:** done

## Tujuan
Menguji sumber fitur visual berbeda dari CLIP asli untuk meningkatkan Task2 Macro-F1 menuju0,70. Ekstraksi image-only dapat berjalan di CPU sambil E22 menghasilkan caption, tanpa menambah pemakaian API/GPU atau menunggu skor E22.

## Ruang Lingkup
- Tahap awal `DEMO_XAI_745_FULL/01_notebook/e23_siglip2/{extract,verify_features}.py`, output `04_hasil_eksperimen/e23_siglip2/`, cache `.cache/e23_hf/`, recovery/plan/changelog.
- Dataset/label/gambar asli, E22 worker/cache dan trainingE12 tidak diubah. Tidak memakai caption/anotasi/context/kode kelas sebagai input encoder.
- Evaluator supervised akan dibekukan sebelum implementasi setelah fitur verified; semua hyperparameter hanya innertraining, outer5baseline740 asli7kelas. Tidak mengklaim skor dari fitur/smoke.

## Langkah
1. Pin official google/siglip2-base-patch16-384 revisionf775b65a79762255128c981547af89addcfe0f88; safetensorsSHAed72c0ace85020ae610fc817c2538b9cae5a477b012a50859c60af5b3ad30857. Sumber https://huggingface.co/google/siglip2-base-patch16-384 dan metadata HfApi resmi diperiksa. Download config/preprocessor/weights saja, verifikasiLFSsha dan pin semua snapshotfiles.
2. CPUFP32 delapanthread batch4, AutoImageProcessor(use_fast=False) konfigurasi resmi384, frozen AutoModel trust_remote_code=False/use_safetensors=True/local_files_only. Transformers5.18 mengembalikan BaseModelOutputWithPooling pada get_image_features: gunakan pooler_output laluL2, bukan logits/labelprompt.
3. Smoke empat gambar sintetis netral:768dimfinite/unit/frozen/repeatability/single-vs-batch tolerance1e-5. Kompilasi/inputlabelpermutation/gatehash sebelum full, tanpa score target.
4. OriginalCSV740hash/IDs/imagepaths dipin. Builder hanyaID/imagepath, invariant terhadap seluruhfieldlain termasuklabel/anotasi/headline. Untuk semua740 simpan hashsourceimage danprocessor pixel_values/dimensi, inferimage-only dan simpanNPZ740x768 +sampleIDs/meta/model/source/runtimehashes. Singlelock/protocol immutable, jangan menimpa feature yang ada.
5. Auditor memeriksa all740inputaudit/ID/source/pixelhash/shape/finiteness/norm serta metadata; reproduksi6indeks tetap[0,1,37,123,369,739] pada frozenmodel tolerance1e-5. Batas sampling dinyatakan; tidak mengulang seluruh740forward. Copy/hash/root audit sebelum evaluasi.

## Risiko & Asumsi
- Representasi pretraining berbeda belum tentu memperbaiki domain metafora. Tidak ada jaminan0,70; repeatedexperimentbias tetap.
- Download publik dan CPU tidak menggunakan payment/provider inference. Cache terisolasi tanpa upgrade dependency. Beban8thread dari88CPU, memori1TiB tersedia.
- Processor memakai resize resmi; tidak melakukan crop manual/augmentation/label-dependent selection. Gambar/dataset tetap asli.

## Verifikasi
Officialrevision/weightSHA/snapshot hashes, originalCSV740 sourcehash, inputbuilder label/context invariance, synthetictensor checks, all740source/pixel audit, sampled6reproduction, rootcopy hashes/IDalign. Tidak ada kualitasTask2 sebelumOOF740 terverifikasi.

## Scope evaluator, sebelum implementasi
- Tambahkan `e23_siglip2/evaluate.py`, `verify_oof.py`, output `04_hasil_eksperimen/e23_oof/`. Tidak mengubah E22sources. Evaluator menggunakan format checkpoint/audit E22 sebagai pola, dengan input3072original+768SigLIP2=3840.
- Nestedjointsearch modeimage_only (StandardScaler+L2 image768) dan fusion (StandardScaler+L2 terpisah E51536/BGE1024/CLIP512/Siglip768 trainingonly). Imageonly C[1;10;100]*gamma[scale;0,1;1]*classweight[None;balanced]=18. Fusi E5weight[0,5;2]*CLIPweight[0;1]*Siglipweight[0;0,5;1;2;4]*C3*gamma3*classweight2=360. Total378. Siglipweight0 kontrol, imageonly dapat menguji tanpa semua fitur lama. Semuaweights/hyperparameters/mode dipilih inner3Task2seed42, meanMacroF1firstargmax; outer5baselineTask1seed42 original740 tujuhkelas.
- Gatefeatureverified740/currentextract+auditor/meta/snapshot/dataset/helper sourcehash sebelum output/training. Simpan378x3innergrid/order/argmax/scalerselectedinner3/refit/prediksi/indices/IDs; auditor reproduksiselectedinner/refits/all740/manualconfusionF1, fullgrid tidak diulang. Singlelock/protocolcheckpointimmutable.
- Tes compile/hash/syntheticheldoutfitisolation/imageonlybaseindependence/controlweight0/missingfeaturegate sebelumlaunch. Fullfit hanya sesudahfeaturesserververified dan rootcopy/hash/inputalign; tidak menunggu skor E22 karena fitur/imageonly frozen independen, tidak menggunakanlabel/OOF supervised lain sebagai fitur.

## Hasil awal ekstraksi
- Extractsource52ea5fbb6d2291e7aaed5aa3e62cfee5be082f15443600229c6561f390242947; auditorfeature69d17c74571ccf72e25d77b65962bc93f87ac64e6e6562141fa816e82aa12559, compile/hashserverlocal/original740/imageonlypermutation/missingsourcegate lolos.
- WorkerCPU1861210 aktif tmux tempo-e23-features, auditor chained setelahexit0. Tidak memakaiAPI/GPU; belumfeaturefinal/skor. E22worker tetap aktif198/740, tidak dimodifikasi.

## Hasil persiapan model/evaluator
- Smoke4synthetic frozenpooler768 finite/unit/repeat/single-vs-batch lolos. Snapshotmodel officialrevision/weightsha cocok. Salinan preparation hashcaa2cfd295334a8ad96501799cee323c167f819f5b5d28219fdb435531a342c3 cocok server; rootsource/revision/weightchecked. Bukti `docs/server-recovery/2026-10-11/e23_siglip2/preparation.json`; qualityscoreNone.
- Evaluatorsourcede41e071e4dbdbad4cea998bf8ae4816866562e33e1da5f489eefa5b0881ef9c; auditorOOF6de4400a53691d2dd749096dde7ff0d0c8d3d23a84c8a1505803f6aa67baea11. Compile/hashserverlocal cocok. Synthetic70(56train14heldout) checks378grid/heldoutfitisolation/imageonlybaseindependence/weight0control/predict/missingfeaturegate lolos.
- Worker1861210 masih live, terakhir log200/740fitur; auditor feature akan berjalan setelahexit0. FullOOF belumdimulai. E22worker1649962 juga live220/740caption; tidak memakai API/GPU tambahan E23.

## Audit fitur lengkap dan launch OOF
- Extractor1861210 dan auditor1916343 terminal exit0; server verified740x768, all740image/pixelhash direkonstruksi. Six predeclared forwarderrors maksimum2,68221e-7<1e-5. NPZSHAd5fa8a7d4da34923b110041a146a33d818e361e76c1fea7413c675c3c0261a35.
- Root memeriksa5copiedhashes/source/modelrevision/weightSHA, originalCSV/NPZ/all740auditID/imagenames; NPYfloat32shape/finiteness/norm dibaca independen tanpa pickle, maxnormerror1,44831e-7. Sampelreproductionserver diperiksa, bukanmengulang seluruh740forward. Bukti `docs/server-recovery/2026-10-11/e23_siglip2/root_feature_verification.json` dan full_features. SerververificationSHAec69508ef61c5aeb74351d838576fc968e969204898b24b6a0132b517339dc10.
- Semua gate launch OOF terpenuhi, worker1938743 aktif tmux tempo-e23-oof, auditorOOF chained exit0. Grid378/source/pipeline tidak berubah. Belum skorOOFfinal; source/output/selectedinner/refit/rootmanualaudit wajib sebelum klaim kualitas. E22caption1649962 tetap live274/740.

## Scope percepatan kernel, sebelum implementasi
- Tambahkan `e23_siglip2/evaluate_cached.py` dan `verify_cached.py`, output terpisah `04_hasil_eksperimen/e23_oof_cached/`. Source/output referensi lama tetap immutable dan worker1938743 tidak dianggap gagal karena lambat. Versi cached boleh berjalan CPU paralel setelah tesparity; seluruh378grid/normalisasi/split/argmax/SVC RBF tetap, tanpa mengurangi pencarian atau data.
- Fit StandardScaler/L2 semua4blok sekali untuk setiap innertraining, dan outertraining. Bangun proyeksi yang sama per mode/weights, castfloat64 seperti SVCvalidasi, gamma scale dihitung1/(n_features*var(trainingprojection)); gamma0,1/1 tetap. Cache RBF Gram train/train dan test/train per mode/weights/gamma agar C/classweight memakai ulangkernel. Train-only metadata/scalerhash tetap direkam.
- Simpan378x3scores/order/firstargmax/prediksi/indices/sourcepin serta chosenscaler metadata. Auditor cached harus memakai pipelineRBF referensi raw untuk mereproduksi semua selectedinner3/refit5 dan740prediksi, bukan hanya mengulang cached code. Fullgrid tidak diulang dalam audit; transform/kernelparity diuji synthetic dan fixedactualtraining/heldout partitions sebelum full. Perbedaan floatingpoint menjadi risiko: jika selectedrawpred/score mismatch, hentikan klaim dan audit.
- Tests sebelum launch: float64 projection/gamma/RBF terhadap rawpipeline, train-only heldout isolation, synthetic raw/cached predsame untuk kedua mode/gamma/weights/C/classweights, fixed actual fold1 train592/test148 predparity beberapa parameter yang ditentukan tanpa targetscore. Semua label hanya training; tidak menghitung skortarget untuk memilih optimizer.
- Workerreferensi dapat dihentikan sebagai duplikat hanya setelah hasil cached740 dan audit rawpipeline berhasil, atau dibiarkan selesai untuk pembandingan. Jangan restart/menimpa source/protocol lama. Catat statusnya eksplisit; ini optimasi perhitungan, bukan pemulihan timeout.

## Hasil persiapan cached
- Sourcecachedad87b3ef914a0c3b857f0c94432fb4d2723d7efb4b665ccccc79eaf1e00d9ee4, auditorcachedc07366c92520a76a8208acc0d060fbd4d88d7e997e210b60436fbd564f10452c; compile/hashserverlocal cocok.
- Synthetic70float32/56train14test dan actualfold1 train592/test148, enamparameter fixedgridindices[0;17;18;100;200;377] lolos exactprojection, gamma, scaler metadata, raw-vs-cached prediction parity; perubahanheldout tidak mengubahfit/kerneltrain. Targettestscore tidak dihitung/dipakai memilih optimizer. Tidak ada outputcached sebelumtes.
- Cachedworker2016428 aktif tmux tempo-e23-cached, auditor rawpipeline chained exit0. Referensi1938743 tetaplive dan sourcenya tidak berubah; belum ada hasilfinalcached. E22caption1649962 tetaplive345/740.

## Hasil final
- Cached OOF740 selesai dan auditor pipeline raw mereproduksi seluruh selected inner/refit/scaler/prediksi: Macro-F1 **0,5573917002808094**. Root memeriksa delapan hash, source/feature pins, semua ID/truth/fold, partisi592/148, urutan378grid/firstargmax dan menghitung ulang confusion matrix serta F1 tujuh kelas. Bukti `docs/server-recovery/2026-10-11/e23_siglip2/root_oof_verification.json`.
- Worker referensi1938743 dihentikan dengan SIGTERM setelah exact cmdline/source identity diperiksa, karena duplikat hasil cached740 yang sudah diaudit pipeline raw dan root. Fold1/protocol/log/source lama dipertahankan; bukan restart atau kegagalan timeout. Bukti `reference_stop.json`.
- Hasil masih di bawah E14fixed0,5662691391334344 dan target0,70; tujuan eksperimen E23 selesai, tujuan utama tetap aktif. Full grid tidak diulang auditor; reproduksi fitur hanya enam sampel tetap; repeated experiment selection bias tetap.
