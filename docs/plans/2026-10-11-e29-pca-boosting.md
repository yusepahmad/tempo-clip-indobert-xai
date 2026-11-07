# E29 PCA training-only dan histogram gradient boosting

**Tanggal:** 2026-10-11
**Status:** done

## Tujuan
Menguji keluarga classifier pohon boosting yang belum ada pada eksperimen E01–E28 untuk mengejar Macro-F1 Task2 minimal0,70. E14 terbaik0,5662691391334344; SVC/MLP/stacking belum mencapai target. Tidak menjamin kenaikan.

## Ruang Lingkup
- Tambah `DEMO_XAI_745_FULL/01_notebook/e29_pca_boosting.py`, `e29_pca_boosting_verify.py`, `e29_pca_boosting_checks.py`; output `04_hasil_eksperimen/e29_pca_boosting/`, recovery root, mirrorserver, plan/changelog.
- Input E14base3072 serta E22caption_context1024 yang sudah diaudit. Tidak menggunakan respons E28 yang belum lengkap, supervised OOF sebagai fitur, annotations, label baru atau model produksi. E28/E12 tetap berjalan tanpa perubahan.
- CPU singlethread, sklearn1.7.2 yang sudah terpasang; tanpa API/GPU/download/dependency baru. Dapat berjalan bersamaan dengan penantian inference E28.

## Langkah
1. Gate originalCSV/E14 source/feature/protocol melalui e16.inputs, E22feature manifest/source/snapshot dan740IDs melalui E22loader yang dipin. Rootcopy E22featureaudit harus cocok sebelum full. Pin helper/loader/hash/model/features/source/versions dan priorE27verified<0,70.
2. Transform training-only perblok StandardScaler/L2 kemudian PCA32/64, randomized seed42/iterated_power4/power_iteration_normalizerQR/whitenFalse. Mode semantic memakai blok E51536/BGE1024/CLIP512, mode caption_fusion menambahkan caption_context1024. Tidak ada learnedfit pada outertest/innervalidation; PCA selalu fit ulang pada training yang sedang digunakan.
3. HistGradientBoostingClassifier learning_rate0,1, min_samples_leaf10, max_bins63, early_stoppingFalse, seed42. Grid mode2 x components2 x max_leaf_nodes[7,15] x l2_regularization[1,10] x max_iter[100,300] x class_weight[None,balanced] =64. Balancedweights dari labeltraining saja. Fixediterations dipilih inner; tidak earlystop menggunakan heldouttest.
4. Nested inner3Task2/outer5Task1baseline seed42, meanMacroF1firstargmax. Raw sklearnPipeline/GridSearchCV(n_jobs4,error_score=raise), masing-masing proses singlethread, simpan64x3scores/fold, selectedinner3fit metadata/scaler/PCA/treefieldhashes/classweights, refit dan740prediksi. Satu lock/sourceprotocolimmutable/checkpoints; tidak resume saat source/protocol berubah.
5. Compile/hashserverlocal, synthetic140float32 untuk mode/parameterendpoint/repeatfit/heldoutinvariance/PCAfit/classbalance/fixediterations/finiteprobability. Actualfold1 parameter termahal untuk runtime dan finitepredict, tanpa menghitung targettestF1. Gate missingfeature/prior/sourcechange sebelumoutput; benchmark membuktikan kelayakan CPU sebelum full.
6. Jalankan full64grid dan auditor chained sekali. Auditor mengulang seluruh selectedinner3/refit5/scaler/PCA/treehash/740prediksi/manual7classF1; fullgrid tidak diulang. Root8filehash/source/data/features/baseline740/64gridfirstargmax/manualF1 wajib sebelumklaim hasil.

## Risiko & Asumsi
- PCA mungkin membuang sinyal kelas langka; pohon pada embedding bisa lebih buruk daripada SVC. Representasi/kompleksitas dipilih dari innertraining saja.
- Dataset740 kecil; eksperimen berulang menambah selectionbias. OOF bukan externalholdout. Target tetapbelum sampai terbukti minimal0,70.
- PCA/tree reproducibility memakai singlethread sebelum importnumpy. Treehash hanya field arrays, bukan structuredpadding. Jika metadata tidak reproduce, diagnosis tanpa melonggarkanassertion.
- Runtimefull bergantung PCA/boosting. Jika smoke menunjukkan tidaklayak, revisi plan sebelum perubahan grid; tidak memilih grid memakai outertestquality.

## Verifikasi
Current source/model/CSV/feature/ID hashes, repeatfit/heldoutisolation/fixediterations/finiteprobability, inner/outerdisjoint, originalbaselinefolds, selectedfitreproduction, all740predictions dan manual confusion/perclass/MacroF1. Catat batas dan bukti aktual di changelog.

## Referensi
- https://scikit-learn.org/1.7/modules/generated/sklearn.ensemble.HistGradientBoostingClassifier.html — class_weightbalanced memakai label yang diberikan pada fit; early_stoppingFalse menjaga fixediteration.

## Hasil smoke awal dan revisi paralel sebelum full
- Source awal workerccc1ca82043ace688ee00e6c5a62c4706d4016295446de6a69561aa8f830a4c9/auditor8bc0c01658e48104b193cbb8e21abc12a30eb6af4c25080516ca1c5e78e7a706/checksd8ac19ba28ce08adf49cc37217cde2aa40117e75925468f75e8125ab683cbc52 compile/hash cocok. Preparationterminalexit0; syntheticrepeat/PCA/treefield/probability/weight/heldoutisolation/fixediterations danactual740gate lolos, expensivefit12,16045s tanpa testF1. Report awal disimpan immutable, belum trainingfull.
- Proyeksi konservatif serial sekitar5jam. Sebelum full ubah hanya schedulingGridSearchCV ke **n_jobs4**, setiap proses tetapenvsinglethread sebelum NumPy. Grid64/algoritma/split/tuning/data tetap. Tambahkan uji serial-vs-joblib4 dengan tiga fixedparameter pada syntheticinner3; allsplit scores, bestparams, scaler/PCA/tree/probabilitymetadata harus persis. Jika gagal, diagnosis sebelumlaunch. Auditor tetapserial.
- Simpan initialpreparation terpisah, reportcurrent baru memin currentworker/checkssource dan scheduling. Hitung anggaran dengan **1000fit** (960grid +5refit +15worker selectedinner +20auditor), bukan label985fit pada reportawal; margin1,5x tetap. Bukan pemotongan grid untuk menurunkan compute.

## Persiapan current dan peluncuran full
- Currentworker **7eea9c1ec7f491353f1f64408eb258e7782b1fe49200872f3d8c14cf192cbeb8**, auditor **8bc0c01658e48104b193cbb8e21abc12a30eb6af4c25080516ca1c5e78e7a706**, checks **a780714d4377fe102d38704733a0761b7e49b4835dc89eb8400004166bd2901c**. Compile/hashlocalserver cocok; currentscheduling4process perprocess1thread.
- Currentpreparation terminalexit0: syntheticendpoints/repeat/PCA/treefield/probability/heldoutisolation/imbalancedweights/fixediterations/missingloadergate lolos. Serial vsjoblib4 seluruh9inner scores, bestparams danselectedfitmetadata persis. Worstfixedactualfit11,9153s; serial1000fitx1,5 sekitar17873s, scheduling4 mengurangi waktu grid tetapi bukan jaminan durasiwallclock. Tidak menghitung outertestF1 pada smoke.
- Root `e29_preparation.json` SHA256 **db20eff7c38e442c88bb4f395bf05c3ea4288449aaa122413ca3017ce8a73aaa** serta `root_preparation_verification.json` memeriksa3sources/helper/E14protocol/currentE27verification danE22embeddingverification/meta cocok fullfeaturecopy auditedroot. Initialreport tetap `e29_initial_preparation.json`; tidak dipakai sebagai currentgate.
- Setelahcurrentpreparation/sourcehash, absenceoutput/session/activecheckerworker diperiksa, fullworker **1310755/starttime210145433** confirmedR/exactcmdline, tmux **tempo-e29-boosting**. RawGridSearchCV64grid/n_jobs4, auditorchained setelahexit0. Log `04_hasil_eksperimen/e29_run.log`/`e29_audit.log`. Tidak ada requestAPI/GPU/download tambahan. Belum fullOOF/skor. E28 tetapaktif.

## Auditor salinan final root — sebelum implementasi
- Tambahkan `01_notebook/e29_pca_boosting_root_verify.py`, stdlib, untuk langkah6: delapanmanifest/source/helper/currentpreparation dan E14/E22featurepins, all740originalCSV/IDs/truth/baselinefolds, partisi592/148coveronce, exact64grid/firstargmax, selectedmetadataPCA/traincounts/fixediterations/class/modelhashes dan manual7classconfusion/F1. Tidak mengubah activeworker/auditor/source/data/grid.
- Reportroot ditulis exclusive setelah fullserververified lengkap. Missingfullgate menolak tanpa report. Uji firsttie/manualF1/invalidscore dan grid64ordering vs actualsklearnserver; root tidak melakukan fitulang. Auditorserver tetap mereproduksi semua selectedinner/refit/PCA/tree/prediksi.

## Persiapan auditor salinan root selesai
- Source `e29_pca_boosting_root_verify.py` SHA256 **039fbabae2e2fd8f4fcfe9288898b24c63ba972b84b0b07015b4c70e8d7934d1**, local/server compile/hash cocok. All64ordering dibanding actualsklearn ParameterGrid sama; actualcompletedfold1 metadata PCA/training394,395,395/refit592/fixediterations/modelhashformats diterima.
- Firsttie/manualperfect-or-wrong7classF1/4invalidscores/missingfullgate lolos tanpa reportfinal. Bukti `docs/server-recovery/2026-10-11/e29_pca_boosting/root_oof_auditor_preparation.json`. Ini persiapan; fullOOF/score belum terverifikasi. Activeworker/auditor tetapimmutable.

## Hasil final dan batas
- Worker1310755 selesai5fold dan terminal; auditor1497604/starttime210263513 selesai semua selectedinner3/refit5 secara exact (scalers/PCA/treefieldhash/probability/weights/fixediterations/740predictions). Log OOF VERIFIED dan reportserververified740 tersedia. Tidak ada perubahan source/grid setelahlaunch.
- Root `full_oof/` dan `root_oof_verification.json` memeriksa8copiedhash/currentworker/auditor/helper/E14/E22/pinnedpreparation, semua740originalCSV/ID/truth/baselinefold, lima disjoint592/148coveronce, exact64grid/firstargmax/traincountsPCA/classmetadata dan manual7classconfusion/perclassF1.
- **Macro-F1 =0,48483372322994545**, serververification SHA256 **523d2b9aa775d92c64839f0b76124b4eba5d3d40bd5f4fdd97d38d6609edb5df**. Tidak mengungguli E14best0,5662691391334344 atau target0,70. Dataset/label/baseline/produksimodel tidak diubah; semua fold memilih300iterations dari innertraining.
- Eksperimen E29 selesai, target utama tetapaktif. Full64grid tidak diulang auditor; root tidak melakukan modelfit, upstreamencoderreproduction sampled, repeatedexperimentselection bias dan tiadanya externalholdout tetap. E28 masihberjalan dan dilanjutkan sesuai planE28.
