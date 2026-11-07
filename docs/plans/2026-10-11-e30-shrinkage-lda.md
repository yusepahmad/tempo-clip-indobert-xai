# E30 shrinkage LDA pada fitur PCA training-only

**Tanggal:** 2026-10-11
**Status:** done

## Tujuan
Menguji classifier generatif pooledcovariance dengan shrinkage yang belum dicoba, menuju Task2 Macro-F1 minimal0,70. E29boosting0,4848337232 belummengungguli E14best0,5662691391. Tidak menjamin kenaikan.

## Ruang Lingkup
- Tambah `DEMO_XAI_745_FULL/01_notebook/e30_shrinkage_lda.py`, `_verify.py`, `_checks.py`; output `04_hasil_eksperimen/e30_shrinkage_lda/`, recovery root, mirrorserver, plan/changelog.
- Reuse immutable `e29_pca_boosting.BlockPCA` dan auditedinputloader (source7eea9c1ec7f491353f1f64408eb258e7782b1fe49200872f3d8c14cf192cbeb8): base3072+E22caption_context1024. Gate E29finalverified740<0,70/source/current8manifest. Tidak memakai OOFsupervised sebagai fitur atau E28incomplete.
- Tidakmengubah activeE28/E12, source/cacheE29, dataset/label/baseline atau modelproduksi. CPU4process perprocess1thread, existing sklearn1.7.2; tanpa API/GPU/download/dependencybaru.

## Langkah
1. Pipeline BlockPCA semantic/caption_fusion32/64 samaE29trainingonly(StandardScaler/L2/PCA randomseed42/QR/iter4). Classifier LinearDiscriminantAnalysis solverlsqr/store_covarianceTrue.
2. Grid32: mode2 x PCAcomponents2 x shrinkage[0,01;0,1;0,5;auto] x priors[trainingfrequencies(None);uniform7]. PriorsNone dipelajari hanya training yangdipakai; uniform fixed1/7. Semua classmeans/covariance/PCAfit training-only; tidak ada earlystopping.
3. Inner3Task2/outer5originalbaseline seed42, meanMacroF1firstargmax, rawGridSearchCV n_jobs4; simpan32x3scores/selectedinner3/refitmetadata(mean/scaler/PCA/classmeans/covariance/coefficient/priorhashes/trainingprobability), IDs/indices/prediksi740/protocolsource. Singlelock danimmutablecheckpoints.
4. Compile/hashserverlocal; synthetic140 endpoints repeatedfit/heldoutisolation/priortrainingcounts/finiteprobability, serial-vs-joblib4 fixedparameterinner3. Gate missingpinnedloader/prior/source sebelumoutput. Actualfold1worstfixedparameter benchmark tanpa targettestF1. Full hanya setelah bukti persiapan/currentrootfeaturepins lolos.
5. Full32grid sekali dan auditorchained mengulang semuaselectedinner/refit/PCA/LDAmetadata/probability/prediction/score. Rootcopy8hash/currentinput/source/baseline740/32gridfirstargmax/manual7classF1 wajibsebelum hasilfinal. Fullgrid tidak diulang auditor.

## Risiko & Asumsi
- Asumsi pooledGaussian/lineardecision bisa tidak cocok; PCA bisa membuang sinyal. Priorsuniform tidak dipilih dari outertest. Repeatedexperimentselection bias tetap, OOF bukanexternalholdout.
- Reuse sourceE29 frozen haruscocokhash; perubahanbaru hanyaE30. Jika reproduksi exactgagal, diagnosis tanpa mengurangiketelitian atau mengubahgrid setelah melihatoutertest.

## Verifikasi
AuditedE14/E22features/IDs/source, originalCSV dan baseline740 tetap. Syntheticisolation/priors/parity, actualruntime, currentprior/sourcegates; finalselectedfitreproduction dan manualMacroF1. E30 tidak memakai migrasi atau respons E28.

## Referensi
- https://scikit-learn.org/1.6/modules/generated/sklearn.discriminant_analysis.LinearDiscriminantAnalysis.html — shrinkage hanya lsqr/eigen, priorsNone memakai proporsi training; signature aktual sklearn1.7.2 server diverifikasi sebelum full.

## Koreksi pemeriksa prior sebelum full
- Smokeawal gagal sebelum report/fulloutput pada assertion prior. Readonly sourceaktual LDA.fit sklearn1.7.2 membuktikan learnedpriors=`counts.astype(X.dtype)/float(n_training)`; uniform juga castX.dtype. PCAfloat32 menghasilkan priorsfloat32, expectedawalfloat64 berbeda maksimum1,27724e-8 pada syntheticcounts, sedangkan castdtype cocok exact.
- Ubah hanya expectedprior pemeriksa metadata mengikuti formula/dtype sourceaktual, lalu wajib **array_equal**, bukan melonggarkan toleransi. Simpan loggagal terpisah dan ulang seluruhsmoke. Model/grid/input/split tidak berubah; belum trainingfull/API.

## Persiapan current dan fulllaunch
- Currentworker **a8275d868dbee02e56eda500f115d76efe1ca25258d091b7870526b61318d048**, auditor **046b6079bae565baa25a73d070e33f6174f1425434390862f78ada6f4dc36868**, checks **ee7e5dea02f15676cc9c6a7ad599c69daef44efe2dfab7d30f84ce9de186a8c8** compile/hashserverroot cocok. Initialfailedprior log tetapdisimpan sebagai `e30_prior_dtype_failure.log`; exactdtype formula lalu seluruhsmoke ulangterminalexit0. Tidak ada toleranceweakening.
- Synthetic140 duaendpoints/repeatfit/PCA/LDAarray/probability/imbalancedtrainingpriors/uniform/heldoutisolation/semanticcaptionindependence lolos. Serial vsjoblib4 all6inner scores/bestparams/metadata persis. Missingfinalprior gate menolak sebelumoutput. Actual592/148fixedauto/64caption smoke0,29465s tanpa targettestF1; budgetserial520fitx1,5 sekitar230s, bukan jaminanwallclock.
- Root `e30_preparation.json` SHA256 **33f249d4cb6a66e388e1cae581e127543517c82d31ee0abf1b2204caf5191f65**, `root_preparation_verification.json`: current3sources/pinnedE29loader/referenceprotocol danE29finalroot740/priorhash cocok.
- Setelahabsenceoutput/session/activeworkerchecker dancurrentpreparation/sourcehash gates, fullworker **1586795/starttime210318132** confirmedR/exactcmdline, tmux **tempo-e30-lda**; raw32grid4process perprocess1thread, auditorchained exit0. Logs `04_hasil_eksperimen/e30_run.log`/`e30_audit.log`. Tidak requestAPI/GPU/download tambahan; belum skorOOF final. E28tetapberjalan.

## Auditor root final — sebelum implementasi
- Tambahkan `01_notebook/e30_shrinkage_lda_root_verify.py`, adaptasi stdlib auditorE29 untuk nestedreference E29/E14/E22, exactgrid32 dan LDAmeans/covariance/coefficient/prior/probabilityhashes (tanpa metadatafixediterationpohon). Semua740originalbaseline/8manifest/firstargmax/manualF1 tetapwajib. Tidak mengubah workerauditor yang selesai.
- Root memeriksa format/sum prior dan fixeduniform; seluruh learnedprior/fitstats direproduksi auditorserver. Selftest firsttie/manualF1/invalid/missingfullgate, lalu auditactualcopy. Outputexclusive setelah seluruhassertions; nofit/API. Batas ini dicatat eksplisit.

## Hasil final dan batas
- Fullworker1586795 selesai5fold/terminal. Auditorchained selesai semua selectedinner3/refit5 exact scaler/PCA/learnedprior/LDAmeans/covariance/coefficient/trainingprobability metadata dan740predictions; OOF VERIFIED. Worker/grid tidak diubah setelahlaunch.
- Rootauditor `e30_shrinkage_lda_root_verify.py` SHA256 **f44b37fdd71e477ae22245a10e85d4cf8208227e73503f12f1b3a52750389714**. Selftest32grid/firsttie/manual7classF1/4invalidscores/missingfullgate lolos. Adaptasinama preparationfile semula masihE29 menyebabkan missingfile saatrootaudit; dikoreksi ke e30_preparation.json sebelumreport, tidak mengubah bukti/score/assertion.
- Root `full_oof/` dan `root_oof_verification.json` verified8hash/currentworker/auditor/helper/immutableE29inputreference/E14/E22sourcefeatures/currentpreparation, original740CSV/IDs/truth/baselinefold, disjoint592/148coveronce, exact32grid/firstargmax/PCAtraincounts/LDAarrayhashes/priorformat dan manual7classconfusion/F1.
- **Macro-F1 =0,558038581543254**, serververificationSHA256 **28f3a4938be36f52b2930d7c3e031852b3108819c9e675c29a764c17d79e79e4**. Belum mengungguli E14best0,5662691391334344 atau mencapai0,70. Modelproduksi/dataset/label tidak diubah.
- EksperimenE30 selesai; tujuanutama tetapaktif danE28berlanjut. Fullgrid tidakdiulang auditor, root tidakfitmodel, learnedprior direproduksi server; upstreamencoderreproduction sampled danrepeatedexperimentselection bias/noexternalholdout tetap.
