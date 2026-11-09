# E32 gambar penuh dan crop ilustrasi SigLIP2

**Tanggal:** 2026-10-12
**Status:** done

## Tujuan
Uji kandidat kedua yang diotorisasi: fitur gambar penuh ditambah view area ilustrasi. Diagnosis42kasus menunjukkan potensi konflik objek/topik/relasi; bukan bukti sebab atau label salah. Target utama0,70, bestE14 0,5662691391334344; E31adapter0,4748302905 tidakpromote.

## Ruang Lingkup
- Source baru `DEMO_XAI_745_FULL/01_notebook/e32_crop/` (extract/verify_features/evaluate/verify/root_audit/checks); output server e32_crop/e32_oof dan preparation/log terpisah; recovery `docs/server-recovery/2026-10-12/e32_crop/`.
- Plan/changelog serta salinan server project. Reuse immutable E23 official SigLIP2 model snapshot dan fullimagefeatures, E14semantic features.
- Tidak mengubah gambar mentah, label/dataset asli, source/cache E23, demo, dependency atau credentials. CPU offline; tanpa API/GPU/download.

## Langkah
1. Bekukan ROI semua gambar RGB sama: bbox(floor0,05W,floor0,12H,floor0,95W,floor0,93H), lalu processor resmi SigLIP2 384. Bukan deteksi objek; area ini dapat memotong informasi, sehingga fullimage tetap tersedia.
2. Loader model offline3snapshotfiles persis E23 audited modelgoogle/siglip2-base-patch16-384 revisionf775b65a79762255128c981547af89addcfe0f88. Verifikasi hashes/modelfrozen/finiteunit/syntheticrepeat/batch equivalence, smoke4gambaraktual. Perkirakan biaya740encoderforward+audit; gatekonservatif <1jam sebelum full.
3. Ekstraksi740crop batch4CPU8threads sekali, allimage/ROI/pixelhash dicatat; auditor server reconstruct740input serta6sampledforwardindices0,1,37,123,369,739. Rootcopyaudit source/snapshot/manifest/CSV/all740originalimagehash/ROI/NPZfloat32finiteunit768/IDs sebelum OOF.
4. Nestedouter5 baseline/inner3 seed42 menggunakan training-only StandardScaler/L2 tiapblock. Grid64: E5weight0,5/2; fullSigLIPweight0/1; cropSigLIPweight0/1; C1/10; gamma0,1/scale; classweightNone/balanced. BGE1/CLIP1 tetap. Semua kombinasi dibekukan sebelum OOF; firstargmaxinner saja.
5. Syntheticrepeat/heldout/zero-weightcrop-isolation/missingfeaturegate/actualsmoke tanpa outerqualityscore. Root/source/preparation verified sebelumlaunchOOF sekali. Auditor reproduksi selectedinner/refit/scaler/pred; rootaudit original740fold/grid64/manualF1.
6. Catat actualhasil dan limit; tidakexpandgrid jika buruk, tidakpromote sebelumfinalaudit. Tetapaktifkan goal utama terpisah jika<0,70.

## Risiko & Asumsi
- ROIgeometrik tidak menemukan objek otomatis, tetapmemuat sebagianheadline dan dapat memotongdetail. Cropweight0 sebagai kontrol; fullimage tersedia.
- DiagnosisOOF dipakai memilihkeluargakandidat, repeatedselectionbias/noexternalholdout tetap. Labeloriginal dipertahankan dan annotationtext tidak menjadi fitur.
- Hasil baik tidak dijamin; menggunakan encoder baru bukanfine-tuningencoder.
- Root tidak mengulangprocessor/encoder; hanya6forwarddireproduksiserver, seluruhinputhash diperiksa.

## Verifikasi
Frozen source/model/prep/root/serverhash; invarianceallannotations, all740originalimages+ROI+pixel serverreconstruct, float32finiteunit768, determinism/runtimegates. Nested740ID/truth/fold identikE14,64gridfirstargmax dan selectedfitsreproduced, manual7classMacroF1/rootmanifest. Changelog setelah perubahan nyata.

## Model dan launch fitur
- Offline snapshot3hash persis E23; synthetic4/repeat/singlebatch dan actual4smoke1,357935s lulus. Konservatif740*1,5 **376,826997s /6,28menit**, di bawah1jam. Rootmodelpreparation/currentbuildersource/3cropboundaryfixtures lolos; model preparation original disimpan sebelumfull.
- Builder source74ac86d0f1a49fd007d090c6215c37f153e35a1b80862a6ff49889d2117a8e46. Launch sekali tmuxtempo-e32-crop, PID3220698/starttime216145466 confirmedR/exactcmdline; auditorverify_features chained exit0, OOF tidak otomatis. Fullbuilder membuatpreparation currentdurasi baru; model/source sama, originalpreparation root tetap dipertahankan.
- Tambah evaluator64grid, auditorselectedfit, syntheticchecks dan rootauditorfeatures/OOF. Rootauditfixturegrid64/firsttie/manualF1/4invalid/missingfull lulus. Belumfullfeature/rootcopy/OOFscore.

## Fitur lengkap dan sebelum OOF
- Ekstraksi740selesai; serveraudit all740image/crop/pixel serta6sampledforwardfiniteunit768 lolos. SerververificationSHA **233d12d9174c3cec4e8d4fff81b0387a3fd41a52b1324b8005acac4a80e99fd1**. Fullcopy `full_features/`, root independent5manifest/model/E23originalpin/cropgeometry/float32unit/IDs lolos, bukti `root_feature_verification.json`. Root geometry memakai server-recordedoriginaldimensions, tidak mengulangprocessor/encoder.
- Auditorroot diperketat memin previousE23rootverifiedfeatureSHAec695 sebelumfullrootaudit; currentSHAbae55da4fceb6846a7ff3efd7b5aec36d5c185c15ab163cc425ac52be085244a. Tidak mengubah builder/workerfit/grid.
- Syntheticrepeat/heldout/zero-cropweight-isolation/missingfeature-beforeoutput lolos. Actual592/148 SVCsmoke1,235167s tanpa outerqualityscore; konservatif980fit*1,5 **30,26menit**, di bawah1jam. FullpreparationSHAd068a0c9ded53048085595da1e95c321bcf6e3c0b7a5c072b1c5caf8ac4d476b, currentworker/verifier/checks/grid64/rootfeaturepin/E14baselineprotocol diperiksaroot.
- Berikutnya launchsekali evaluate.py dan verify.py hanya jika exit0, CPU1thread/1process, terpisah dari fitur terminal. Tolak existingOOF/log/session; capturePID/starttime dan janganretry status tidakpasti. Belum skorbaru.
- Launch tmuxtempo-e32-oof sekali setelahrootfeature/preparationgates; rincianPID dicatat setelah observasi. Runlog e32_oof_run.log dan auditorchained e32_oof_audit.log.
- WorkerOOF **3301911/starttime216188405**, confirmedR/exactcmdline, protocol.json terbentuk; observasi awal0/5fold. BestE14 tetap0,5662691391334344.
- Observasi lanjut:1/5fold selesai180,351254s; selectedinnerC1/balanced/gamma0,1/crop1/E5weight0,5/fullSigLIP0, innerMacroF10,5559268635. Bukan skorouter atau final. Worker3301911/starttime216188405 stateR, CPUtime218s sebandingwall218s, tidakstalled. Remaining4fold+audit tetap berjalan; tidakrestart.

## Hasil final
- E32 selesai5fold, audit server dan salinanroot740 lolos. Macro-F1 **0,5632417944480668**, di bawah E14 **0,5662691391334344**; tidak dipromosikan. Bukti `docs/server-recovery/2026-10-12/e32_crop/root_oof_verification.json`. Tidak ada API AI/GPU untuk tahap ini.
