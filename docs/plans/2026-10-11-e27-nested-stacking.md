# E27 stacking cross-fitted lima representasi frozen

**Tanggal:** 2026-10-11
**Status:** done

## Tujuan
Menguji apakah meta-classifier dapat menggabungkan informasi yang saling melengkapi dari semantik, caption, SigLIP2 dan DINOv2 menuju Macro-F1 Task2 minimal0,70. Diagnostik OOF lama menunjukkan DINOv2 benar pada48error E14 tetapi salah pada63prediksi benar E14. Ini hanya alasan meneliti kombinasi, bukan bukti peningkatan atau input yang boleh dipakai meta-model.

## Ruang Lingkup
- Tambah `DEMO_XAI_745_FULL/01_notebook/e27_stacking/{evaluate,verify,prepare_checks}.py`, output `04_hasil_eksperimen/e27_stacking/`, recovery `docs/server-recovery/2026-10-11/e27_stacking/`, plan/changelog.
- Lima base: E14semantic3072 (E5weight0.5/BGE1/CLIP1), caption1024, caption_context1024, SigLIP2image768, DINOv2image768. Semua fitur frozen sudah diaudit; loaderlama/currenthash/manifest/source/modelpins wajib cocok. Tidak memakai OOFpredictions atau modelweights terlatih eksperimen lain sebagai fitur.
- Tidak mengubah data/label/originalsplit/sourcecachelama; tidak memakai anotasi manual sebagai fitur. Tidak API/GPU/download baru. Persiapan boleh saatE26aktif; fullE27 hanya sesudah E26terminal dan server/rootauditfinal<0,70.

## Langkah
1. Muat semua representasi melalui loaderE22/E23/E25 yang dipin sourcehash; buktikan original740IDs/labels/folds/base3072 sama. Gabungkan menjadi6656dim. Pin inputs/revisions/hashes/source/versions.
2. Bekukan lima baseSVC RBF C1/class_weightbalanced/OVRdecision. Gamma E14=0.1, lainnya=scale. Perblok StandardScaler/L2 fit hanya training. Tidak ada basehyperparametersearch atau pemakaianOOFlama.
3. Pada setiap training outer/inner, buat meta-training35dim dari prediksi decisionfunction lima base melalui crossfit3 stratifiedTask2 seed42. Tiaprow diprediksi base yang tidak dilatih pada row tersebut; semua scaler juga hanya foldtraining. Refit base pada seluruh training itu untuk metatest. Data/label outertest tidak pernah membentuk metatrain atau fitbase.
4. Meta StandardScaler+LogisticRegression lbfgs/max_iter5000/random_state42; grid6 C[0.1,1,10] x class_weight[None,balanced]. Pilih firstargmax pada inner3Task2 seed42. Outer5Task1baseline asli. Cache metafeatures hanya dalam trainingpartition yang sama untuk enammetaparameters; tidak reuse antarinner/outer.
5. Rawauditor memakai sklearnStackingClassifier(cv3identik/stack_methoddecision_function) untuk selectedinner3/refit5, serta cross_val_predict independen untuk metatrainhash/coverage. Periksa basefit/scalermetadata, metatrain/testhash, metamodelcoef/intercept/scalers, predictions dan manual7classF1. Tidak mengulang raw seluruhgrid6.
6. Tes synthetic serta actual592/148 fixedmetaparameter parity dengan rawStackingClassifier; heldoutfeature/labelchange tidak mengubah basefits/metatrain; splitcoverage/heldoutisolation; missingfeature/sourcechange gates. Compile/hashserverlocal sebelumlaunch.
7. Setelah gateE26final<0,70 dan rootauditsfitur/persiapan lolos, satu worker+auditor chained. Rootcopy8hash/source/featurepins/740baselineIDs/truth/folds/6gridargmax/5partitions/manualMacroF1. Catat hasil dan batas, targetthread tetap sampai0,70terverifikasi.

## Risiko & Asumsi
- Base sangat berkorelasi dan meta-crossfit vs refit memiliki distribusi berbeda; stacking tidak menjamin peningkatan. Semua skor akhir harus diaudit, bukan oraclecoverage atau skorinner.
- Pemilihan representasi/konfigurasi dari eksperimen terdahulu membawa repeatedexperimentselection bias; OOF bukan externalholdout. Tidak menghilangkan batas itu.
- Indextransformer menyimpan frozenarrayglobal sebagai parameter, tetapi fit hanya indicestraining; invarianttes dan audit harus membuktikan heldout tidak memengaruhi fit. Semua metatrain mesti crossfit ulang di setiapinner, tidak boleh slicingOOFglobal.

## Verifikasi
Inputloader/source/model/CSVhash gates; all740alignment, crossfitcoverage dan disjointness; synthetic/actualrawStackingClassifier parity, heldoutisolation; selectedinner/refitrawmetadata/prediksi; manual7classconfusion/perclass/MacroF1 dan rootcopyallhash. Changelog sesudah perubahan aktual.

## Persiapan selesai, fullOOF belum diluncurkan
- Implementasi worker `evaluate.py`, auditor `verify.py`, fixture `prepare_checks.py` ditambahkan. Threadenv1 sebelum numericalimports. SignatureBASES dinormalisasiJSON agar checkpoint/protocol dapat dibandingkan tanpa mismatch tuple/list.
- Local/server compile dan sourcehash cocok: worker **ed2641cb870fe1f4d0b12fbf6c99934ea6457bdae928cf3d638d05c7af86352a**, auditor **6d88fa1d5b5f7b80d6fa814b1118378ac2c8d589bbfeb053775d78a6add5ced3**, checks **54c0efbc88f64d1e78959346265bb7acd7e5529b55511d4a98016058efb583d8**.
- Tes selesai exit0: synthetic70(49/21) dan actual740fold1(592/148), masing-masingmetaparameterindices0/5. RawStackingClassifier serta independentsklearncross_val_predict cocok exactpredictions dan seluruhbasefit/scaler/gamma/support/dual/intercept, meta35train/testhash, crossfitcoverageindices danmetaStandardScaler/coef/intercept/iterations. Bukan rawparity exhaustive6grid, tidak memakai targettestscore untuk memilihoptimizer.
- Mengubah features danlabel heldout tidak mengubah basefit/metatrain35 atau metamodel; crossfit3 menutup pooltraining sekali dan semua fit/prediksi excludesheldout. Missingfeature/sourcechange gates menolak.
- Bukti `docs/server-recovery/2026-10-11/e27_stacking/preparation.json` SHA256 **ca335185fd00d667a19ea9ee18e95d8dc22be08556497b80d3661e220aafdd28**. Rootsource/inputsignature/helper/threefeatureverification/meta pins cocok terhadap salinan yang sudahdiauditroot. StatuslegacyE23features_verified diperiksa sesuai report aslinya beserta verificationSHA, bukan diubah.
- E26worker541222/starttime209630082 masih confirmedR, empatfold selesai, belum finalOOF/audit. FullE27 tetap menunggu finalE26server/root<0,70 dan worker/sessionterminal. Belum ada fullE27score, tidak ada API/GPU tambahan, bestE14 tetap0,5662691391334344.

## FullOOF diluncurkan setelah E26finalaudit
- E26worker541222/auditor707767/sessiontempo-e26-oof terminal; finalserver/rootOOFverified **0,5385617683922208**<0,70. RootE26verificationhash dan allcopiedsource/inputpins cocok.
- Sebelum launch: preparationreporthashca335185fd00d667a19ea9ee18e95d8dc22be08556497b80d3661e220aafdd28, current3sourcehash, finalE26verification2bd34c8fef9c77a576e251ca0b2578f4542a4a4021ff4ccd6f88846179cde040, terminalPID/session dan absentE27output/session digate.
- Satu workerE27 **752476/starttime209768367** confirmedR/exactcmdline, tmux tempo-e27-oof, rawStackingClassifier/cross_val_predict auditor chained setelah exit0. Output `04_hasil_eksperimen/e27_stacking/`, run/auditlogs terpisah. Tidak ada API/GPU tambahan/sourcechange/datachange.
- Belum ada skorE27; bestE14 tetap0,5662691391334344 dan target0,70 belum tercapai. Plan in-progress sampai finalOOF danserver/rootaudit selesai.

## Hasil final OOF740
- Worker752476 terminal sesudah lima fold; auditor762917/starttime209776400 terminalsuccess. Seluruhselectedinner3/refit5 rawStackingClassifier danindependentcross_val_predict, basefit/scalers/metatrain35/test/metamodelmetadata serta740predictions cocok. Final Macro-F1 **0,4952155713517192**; serververification SHA256 **6dd4b7b9cc8b4504d8fb6ae9d157eee33d1085f113c96a52f9dfdf30ae52e9fa**.
- Rootcopy `docs/server-recovery/2026-10-11/e27_stacking/full_oof/` dan run/auditlogs lengkap. Root8hash/source/helper/threefeaturepins/preparationinputsignature, all740baselineIDtruthfolds,5disjoint592/148partitions,6gridordering/firstargmax/selectedmeans dan manual7classF1 cocok **0,4952155713517191** (<1e-12 dari server).
- Root juga memeriksa seluruhselectedinner/refitcrossfitpartitions: semua trainingpool excludesoutertest; tiga validationpartitions menutup pool sekali, selectedinnerheldout menutupoutertraining sekali; lima basefitmetadata percache. Bukti `root_oof_verification.json`. Auditorroot inline pertama memiliki typo nama keyoof_sha256 saat transformtemplate; diperbaiki sebelum laporanverified ditulis, tidak mengubah worker/grid/data atau melonggarkan assertion.
- Stacking ini belum mengungguli E14 **0,5662691391334344** atau target0,70; best tetapE14. Fullgrid6 tidak diulangraw, upstreamencoderforwards sampled, repeatedexperimentselection bias dannoexternalholdout tetap. Tujuanthread masih aktif.
