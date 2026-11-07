# E26 fitur leksikal caption tanpa reduksi SVD

**Tanggal:** 2026-10-11
**Status:** done

## Tujuan
Menguji informasi objek/frasa caption Gemini E22 secara langsung melalui TF-IDF, karena embedding semantik dapat mengaburkan kata pembeda kelas. Ini berbeda dari E09 yang memakai deskripsi Qwen dan mereduksi fitur leksikal menjadi128komponen SVD. Target tetap Macro-F1 Task2 minimal0,70 pada original OOF740, tanpa klaim jaminan.

## Ruang Lingkup
- Tambah `DEMO_XAI_745_FULL/01_notebook/e26_caption_lexical/{evaluate,verify,prepare_checks}.py`, outputserver `04_hasil_eksperimen/e26_caption_lexical/`, recovery `docs/server-recovery/2026-10-11/e26_caption_lexical/`, plan dan CHANGELOG.
- Gunakan caption E22 image-only yang sudah diaudit740, originalheadline/support, dan frozen baseE14 E5/BGE/CLIP. Tidak menggunakan targetlabel/anotasi manual/domainVLM sebagai input teks; tidak mengubah dataset/label/originalsplit atau source/cache E22.
- Tidak membuat requestAPI/GPU/downloadmodel baru. Persiapan boleh dilakukan saat E22OOF aktif; fullOOF E26 hanya setelah E22terminal dan auditserver/root selesai dengan skor<0,70.

## Langkah
1. Gate originalCSV740/source/feature/caption manifests dengan loader E22 yang dibekukan; reconstruct caption dan caption+headline/support tanpa label. Pin seluruhinput/source/helper dan versi numericalsoftware.
2. Bekukan grid384: view[caption,context], analyzer[word,word_char], lexical_weight[0.5,1,2], semantic_weight[0,1], C[0.1,1,10,100], kernel[linear,rbf], class_weight[None,balanced]. Untuk menghindari duplikasi lexical-only, grid lexical_weight1 saja saat semantic_weight0: jumlah grid menjadi256 (64lexical-only +192fusion). gamma RBF=scale. Word TF-IDF1–2gram/max12000; char_wb3–5gram/max24000; min_df1, sublinear_tfTrue, lowercase default; normalizeL2 setelah word/charunion, tanpaSVD.
3. Fit tigaStandardScaler/L2 base pertraining, weights E5=0.5/BGE=1/CLIP=1; semantic_weight mengalikan semua base. Fit vocabulary/IDF hanya training, bukan global. Outer5 asli/Task1seed42, inner3Task2seed42; seluruh256pilihan dalam innerCV, firstargmax.
4. Cache hanya transform/kernel yang berasal dari training pada innerfold yang sama. Gabungkan sparseTF-IDF dan weightedsemantic; hitung linear/RBF kernel untuk SVCprecomputed. Rawreference SVC linear/RBF pada proyeksi asli dipakai audit setiap selectedinner/refit. Tidak menggunakan OOFprediction eksperimen lain sebagai fitur.
5. Sebelum full: compile/hashserverlocal, synthetic dan actual592/148 fixedparameter parity/projection/scalermetadata/vocabulary/IDF/gamma/rawcachedpred, heldoutisolation serta inputlabelpermutation. Missingcaptiongate/sourcechange menolak; source dibekukan sebelum launch.
6. Setelah E22auditfinal<0,70, satu worker+auditor chained, checkpoint immutable/signature/singlelock. Salin hasil final dan auditroot8hash/all740IDtruthfold/gridargmax/partitions/manual7classF1. Laporkan hasil/batas; jangan memilih hasil intermediate outerfold sebagai final.

## Risiko & Asumsi
- Caption mungkin tidak menyebut objek penting, TF-IDF dapat overfit kata langka. InnerCV dan kelasbalanced adalah bagian protokol; tidak ada garansi0,70.
- Repeatedexperimentselection bias tetap ada; OOF bukan heldout eksternal. Auditor mereproduksi selectedfits, tidak seluruh256grid secara raw.
- Perbedaan floatingpoint sparse/precomputed harus menolak rawprediction mismatch, bukan melonggarkan audit. Source/cache lama tetap immutable.

## Verifikasi
Original740CSV/labels/split hashes, caption/server/rootfeature gates; train-only vocabulary/scalers/IDF, fixedparameterrawparity, heldoutleakfixtures, allselectedinner/refitmetadata/predictions, manualconfusion/perclass/MacroF1 dan rootcopy hashes. Catat seluruh perubahan aktual setelah diterapkan.

## Implementasi dan pemeriksaan awal
- Tambah worker `evaluate.py`, raw sparseauditor `verify.py` dengan environmentthread1 sebelum NumPy, serta `prepare_checks.py`. OriginalE22loader/sourceSHA dipin; all742captionmanifesthash dan currentcaptionauditor digate. Cached256grid memakai vocabulary/IDF/scalers training-only tanpaSVD.
- Local/server compile dan tigaSHA cocok: workere5e8fcd4fec00e89b7b9c0bff10699d851f3d5f0062dacf8ee57c84d8a48d3d7, verifier875cc2f5f6490b3d3282c47269009913674dc27e935f037e5fc398d25dcab284, checks7ef74097b49b9308b398ba224a87d4726aae01a8d22feeb9fcf85e503dea33c7.
- Pemeriksaan awal menemukan vocabularyindices NumPyint64 tidak JSONserializable; metadata kini mengubah indeks menjadi Pythonint sebelum hashing. Ini perbaikan pencatatan sebelum fullOOF/sourcefreeze, tidak mengubah tokenization/fit/grid. Checkjob521461/starttime209614960 confirmedR; belum ada preparationreport ataufullOOF.
- GateE22final terpenuhi: workerterminal dan server/rootOOFverified **0,557623259929161**<0,70. Bukti rootE22 tersedia; fullE26 masih menunggu seluruhtesparity/leakage selesai.

## Persiapan verified dan launch OOF
- Checkjob521461 terminal exit0. Dua fixture:12fixedparameter synthetic70(49/21) dan6fixedparameter actual740fold1(592/148) lulus raw sparse/precomputedpredictions, scaler/vocabulary/IDF/gamma serta heldouttrainingtransform/metadata isolation. Lexical-only independen dari perubahansemantic; heldout-onlyword tidak masuk vocabulary. Textbuilder labelpermutation dan missingcaption/sourcechange gates lolos. Bukan rawparity exhaustive256grid; tidak memakai targettestscore untuk memilih optimizer.
- Bukti root `docs/server-recovery/2026-10-11/e26_caption_lexical/preparation.json` SHA2563f650904090158283370467b109b58b3f0dc3b27491983089b5d230b49de1b4d cocok server. Root memeriksa tiga sourcehash, caption/currentmanifest/featureaudit740 dan finalE22rootaudit<0,70. Sources tetap seperti catatan sebelumnya.
- Gate finalE22serverhash, worker/sessionterminal, preparedsource/reporthash dan absentE26output/session diperiksa sebelum launch. WorkerE26 **541222/starttime209630082** confirmedR/exactcmdline, tmux tempo-e26-oof; protocol.json terbentuk, log masih kosong normal. Auditorrawsparse chained setelah worker exit0. Belum skorE26.
- Plan tetap in-progress; best terverifikasi E14 **0,5662691391334344**, target0,70 belum tercapai. Tidak ada requestAPI/GPU tambahan atau perubahan dataset/label.

## Hasil final OOF740
- Worker541222 terminal setelah lima fold lengkap; auditor707767/starttime209740499 terminalsuccess. Seluruhselectedinner3/refit5 raw sparseSVC/vocabulary/IDF/scalermetadata/740predictions cocok. Final Macro-F1 **0,5385617683922208**. Verificationserver SHA256 **2bd34c8fef9c77a576e251ca0b2578f4542a4a4021ff4ccd6f88846179cde040**.
- Rootcopy `docs/server-recovery/2026-10-11/e26_caption_lexical/full_oof/` dan run/auditlogs lengkap. Root8manifest/source/currentreference/helper/caption/featurepins, preparationinputsignature,740originalIDtruthbaselinefold,5disjoint592/148partitions,256gridordering/firstargmax/selectedmeans danmanual7classF1 cocok. Bukti `root_oof_verification.json`.
- Belum mengungguli E14 **0,5662691391334344** atau target0,70. Semua5fold memilih semantic_weight1; tidak memilih hasilindividualfold sebagai final. Fullgrid tidak diulangraw, upstreamencoder sampled12view/sample; captionsemantics danexternalgeneralization tidak tersertifikasi, repeatedexperimentselection bias tetap. Modelbest tetapE14.
- E26 selesai; tujuanthread tetap aktif. Tidak ada API/GPU tambahan atau perubahan originaldata/labels/splits.
