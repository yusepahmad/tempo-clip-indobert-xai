# E25 fitur visual frozen DINOv2

**Tanggal:** 2026-10-11
**Status:** done

## Tujuan
Menguji representasi visual self-supervised DINOv2 yang berbeda dari CLIP/SigLIP2 untuk Task2 menuju Macro-F1 OOF0,70. Berjalan CPU sambil menunggu E22, tanpa menggunakan label/context untuk encoder dan tanpa API/GPU.

## Ruang Lingkup
- Tambahkan `DEMO_XAI_745_FULL/01_notebook/e25_dinov2/{extract,verify_features}.py`, output `04_hasil_eksperimen/e25_dinov2/`, cache `.cache/e25_hf/`, recovery/plan/changelog/mirrorserver.
- Evaluator supervised dipersiapkan sesudah fitur/server/rootverified: image-only dan fusi E14+768, nestedgrid378 sama seperti E23; detailimplementasi dibekukan sebelum ditulis. Tidak mengubah E22sources/cache/proses, E12monitor, dataset/label/images asli atau modelproduksi.

## Langkah
1. Pin official `facebook/dinov2-base` revisionf9e44c814b77203eaa57a6bdbbd535f21ede1415 dan safetensorsSHAd73036b56966966d07975d696bde331762f37297e2f095de8cea0040c3aa0841; HfApi metadata resmi dibaca. Snapshotconfig/preprocessor/safetensors saja; cache terpisah tanpa upgrade dependency.
2. Frozen AutoModel FP32 CPU8threads batch4, trust_remote_codeFalse/localfiles/safetensors. Processor AutoImageProcessor(use_fast=False) resmi: shortestedge256/center_crop224, normalisasiImageNet; tidak memodifikasi filegambar. Ambil normalized last_hidden_state CLS768, bukanclassificationlogits.
3. Sebelumfull smoke4synthetic finite/unit/frozen/repeat/single-vs-batch1e-5, source/compile/hash, originalCSV740gate dan image-onlybuilderinvariant semua nonID/imagefields. Modelcard/dokumentasi resmi diperiksa.
4. SourceCSV hash/IDs/images dipin; simpan all740 sourceimage/pixelhashes/NPZfloat32unit768/meta/runtime/model/sourcehash. Singlelock/protocolimmutable, rejectexistingfeatures. Full dimulai setelahsmoke otomatis lolos, bukan berdasarkan targetscore.
5. Auditor independently reconstruct all740source/pixelhash, checkfinite/unit/ID/modelpins; reproducefixed6indices[0,1,37,123,369,739]1e-5. Rootcopy/hash/all740ID/NPYtensor audit sebelumOOF. Samplinglimit dinyatakan.

## Risiko & Asumsi
- Pretraininggambar tidak menjamin domainmetafora lebihbaik. Officialcenter_crop224 bisa menghilangkan bagianpinggir; dicatat sebagai keterbatasan, bukan dipilih berdasarkantestscore. Fitur hanya gambar, tidakprompt/kelas/context/annotasi.
- CPU8 dari88thread dan bobot346MB tersedia; tidak memakai paid inference/GPU/API. Semua inputtraining classifiers nanti tetaptrainingonly dengan outer5baseline dan inner3Task2.
- Repeatedexperimentselectionbias tetap; target0,70 belum tercapai. Tidak menurunkan protokol E12 atau menghentikan E22.

## Verifikasi
Compile/hash/modelrevision/LFS/snapshot, smoke/frozen/no-labelbuilder, all740image/pixel/ID/float32norm, sampled6forward, rootcopiedmanifest/IDs/numerics. Belum kualitasTask2 sebelumOOF740valid.

## Referensi
- https://huggingface.co/facebook/dinov2-base
- https://huggingface.co/docs/transformers/model_doc/dinov2

## Persiapan/launch awal
- Extractsourcec32e3a34fc428284aca8ec7e972f1525c54a42a84b5ec33e14c3f73995967341; auditorfeature69d17c74571ccf72e25d77b65962bc93f87ac64e6e6562141fa816e82aa12559. Compile/hashlocalserver, all740originalimageinputs/nonID/imagefieldsinvariance dan badCSVhashgate lolos. Output belumada sebelumlaunch.
- Worker2347426/starttime208228214 aktif tmuxtempo-e25-features, downloadmodel/preparation lalu full hanya sesudahsmoke4synthetic diworker lolos; auditorchainedexit0. Pada observasi awal preparation masihpending, belumfitur/OOF/skor. E22 tetaplive630/740.

## Fitur lengkap dan scope evaluasi — sebelum implementasi
- Extractor2347426/auditor2372626 terminalsuccess, all740image/pixelhash reconstruits; fixed6forwards maxerror0. NPZSHA5c44a8043a5a1a76bb8f7508ab2d6529a55435f5b5a4fad9e14a021b5fe4eb98.
- Rootmemeriksa5manifest/currentextract/auditor/modelpins, original740CSV/ID/imageaudit, independentNPYUnicode/float32finite/unit768(maxnormerr1,45258e-7), server6forwarderrors. Bukti `docs/server-recovery/2026-10-11/e25_dinov2/root_feature_verification.json`; belumskorTask2.
- Tambahkan evaluate.py(rawpipeline referensi, tidak diluncurkan), evaluate_cached.py dan verify_cached.py. Output `e25_oof_cached/`. ShapeE14base3072+DINO768=3840. Normalisasi StandardScaler/L2 per4blok training-only; image_only18 danfusion360: E5[0,5;2],CLIP[0;1],DINO[0;0,5;1;2;4],C[1;10;100],gamma[scale;0,1;1],classweight[None;balanced], total378.
- Inner3Task2seed42meanMacroF1firstargmax dan outer5baselineoriginal740/7class. Cachefloat64RBF trainingprojection/gamma lintasC/class, sama algoritma E23 yang sudah terbukti; tidak mengurangi grid. Save378x3scores/metadata/indices/IDs/sourcepins. Auditor env1thread sebelumNumPy, memakai rawpipeline untuksemua selectedinner3/refit5/scaler/prediksi dan manualF1; fullgrid tidakdiulang.
- Sebelumlaunchcompile/hash dan actualfold1train592/test148 fixedparamindices[0;17;18;100;200;377]exactprojection/scaler/gamma/rawpredparity/heldouttrainingkernelisolation tanpa targettestscore; imageonlybaseindependence dan zeroDINOcontrol. Gatecurrentfeaturemanifest/model/source. Fullcached hanya sesudahsemuateslolos; rawworker tidak diluncurkan sebagai duplikat.

## Persiapan evaluator dan launch
- Rawreferencesourceb28efd745fd5c0a0e84068ca7a1df364671e89502b2c269982dbdb6d2c1bfe52; cached47aaa313d3aa84666c30dce5c5beaae78544e07b13c6f52cc7ec33bf038ac226; auditor99e9ff3f1ffa89fdf3ec470c64aec32a4d5297ce69fec1158c40005a31d43b35. Compile/hashlocalserver/currentfeaturegate lolos.
- Actualfold1train592/test148 enamparameterfixed[0;17;18;100;200;377]exactprojection/scalermetadata/gamma/rawpredparity/heldouttrainingkernelisolation lolos. Imageonlybaseindependence dan zeroDINOcontrol lolos. Tidak menghitung targettestF1 untuk memilih optimizer; bukan exhaustive rawparity seluruh378grid.
- WorkerOOF2399666/starttime208261011 live tmuxtempo-e25-oof; rawpipelineauditor chained exit0. Rawreferenceworker tidak diluncurkan; belumOOFfinal/skor. E22worker/guardian/dispatcher tetaplive674/740caption.

## Hasil final OOF dan batas
- Cached378grid selesai lima fold, auditor2417291 terminalsuccess. Pipeline raw mereproduksi seluruh selectedinner3/refit5 scaler/score/prediksi,740OOF dan manual7classF1. Rawreference tidak diluncurkan sebagai duplikat.
- Root memeriksa8copiedhash/currentcached/reference/verifier/helperpins, featureverification/meta pins yang sudahrootverified, semua740ID/truth/baselinefold, lima592/148partitions, gridordering/firstargmax/selectedauditmean serta manualconfusion/perclassF1. Bukti `docs/server-recovery/2026-10-11/e25_dinov2/root_oof_verification.json` dan full_oof.
- Macro-F1 **0,5381659817436221** (rootmanual0,538165981743622; beda floatingpoint<1e-12). SerververificationSHA0cf356c1c8a9790be4ef550ac2b7f002ec403c3ce8f22fe87dcb04ded17eb917. Di bawah E14fixed0,5662691391334344; targetutama0,70 belumtercapai dan tetapaktif.
- Keterbatasan: fullgrid tidak diulang auditor, fiturforward hanya6sampel, officialcenter_crop224 bisa menghilangkanpinggir, repeatedexperimentselectionbias tetap. Tidak mengganti bestmodel atau mengubahdataset/label.
