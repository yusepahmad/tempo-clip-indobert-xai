# E24 MLP pada fitur semantik dan visual frozen

**Tanggal:** 2026-10-11
**Status:** done

## Tujuan
Menguji supervised nonlinear head atas E14frozen3072dim, berbeda dari SVC serta E02MLP TF-IDF/SVD. Target utama tetap Macro-F1 Task2 minimal0,70; tidak menjamin kenaikan.

## Ruang Lingkup
- `DEMO_XAI_745_FULL/01_notebook/e24_semantic_mlp.py`, `e24_semantic_mlp_verify.py`, output `04_hasil_eksperimen/e24_semantic_mlp/`, recovery, plan/changelog dan mirrorserver.
- Tidak mengubah dataset/label/inputembedding/modelproduksi/E22worker/cache/E12. CPU singlethread tanpa API/GPU.

## Langkah
1. Gate E14 input/audit/hashes melalui helper e16_hierarchical.inputs; E51536+BGE1024+CLIP512. StandardScaler dan L2 setiap blok training-only; CLIP/BGEweight1, E5weight[0,5;2].
2. MLPClassifier sklearn1.7.2 yang sudah terpasang: hidden64/ReLU/Adam, seed42, fullbatch, LR0,003, early_stoppingFalse, tol0 dan n_iter_no_change>max_iter agar fixed epochs[50;150]. Alpha[0,01;1], balance[False;True] sampleweight dari hitungan training saja. Total16grid, inner3Task2seed42 pilih meanMacroF1firstargmax; outer5 baseline592/148740asli.
3. Simpan grid16x3score, bestindex/params, selectedinner3 metadata/scaler/modelweights/loss/n_iter, refit metadata dan prediksi/IDs/split. Singlelock/protocol/sourceimmutable. Semua classes harus7, finite loss/weights/probabilities.
4. Compile/hash lalu synthetic70 tes repeatfit/predict/metadata, labelcountweight, fixedepoch, heldoutfitisolation dan gateinput. Actualbase fold1 satu parameter tanpa menghitung targetscore untuk benchmark runtime. Full dimulai hanya sesudah smoke lolos dan estimasi CPU layak.
5. Auditor mereproduksi semua selectedinner3/refit5 weights/scalers/scores/all740pred dan gridordering/firstargmax/manual7classF1. Fullgrid tidak diulang. Rootcopy/hash/split/score sebelum klaim kualitas.

## Risiko & Asumsi
- Sampel740 kecil dibandingdimensi3072, overfit mungkin. Regularisasi/epoch/weights dipilih inner, bukan outertest. Repeatedexperiment selection bias tetap.
- MLP stochastic diatur seed42/singlethread; apabila reproduksi metadata/prediksi gagal, jangan klaim valid sampai penyebab diaudit. ConvergenceWarning fixedepoch dicatat sebagai expected, finite checks tetap wajib.
- FitScaler melibatkan seluruhtraining yang memang digunakan untukoptimisasi; tidak ada earlystoppingholdoutinternal. Tidak memakai OOFprediksi supervised sebagai fitur atau anotasi manual.

## Verifikasi
Hash/data/feature/sourcegate, sklearnversion1.7.2, synthetic dan actualsmoke, fixedepoch, deterministicrepeat, training-only transformations/weights, nestedpartition/gridfirstargmax, rawselectedfit reproduction, rootmanualF1.

## Referensi
- https://scikit-learn.org/stable/modules/generated/sklearn.neural_network.MLPClassifier.html ; dukungan sample_weight dikonfirmasi langsung pada signature versi1.7.2 server.

## Persiapan dan keputusan full
- Sourceworker5979315a8a82577a1dd71ebf3fcbd988ff46951d3a9e7cf0a1556dab84daaef3 dan auditor5f3c3a705dc0b09b4a8d1c857d98412b85fbaba45d078bde3489667747254a28 compile/hashserverlocal cocok.
- Synthetic70float32: parameter pertama/terakhir grid lolos deterministic repeatedfit/modelweight/scaler/loss metadata/prediksi, fixed50/150epoch dan heldoutperturbationfitisolation. Separate imbalanced38training memeriksa sampleweightdigest dari labeltraining. Inputgate real E14/data/features/source/audit lolos.
- Actualbasefold1 train592/test148, parameter pertama fixed, smoke finite/predlabels lolos tanpa menghitung targettestF1. Waktu0,8432s untuk50epoch; estimasi konservatif seluruh240innerfit dianggap150epoch sekitar607s, plus refit/audit. CPU singlethread layak; lanjut full16grid tanpa API/GPU.

- Full worker2161689/starttime208126258 aktif tmuxtempo-e24-mlp dengan auditor chained exit0. Source/output terpisah; belum skorOOF. Bukti preparation `docs/server-recovery/2026-10-11/e24_semantic_mlp/preparation.json`. E22worker1649962/guardian1755879/dispatcher1762420 masih live, terakhir476/740caption.

## Koreksi audit singlethread — sebelum perubahan
- Full worker selesai lima fold; auditor awal gagal equality selectedmodelmetadata. Diagnosis readonly menemukan auditor mengimpor NumPy sebelum env singlethread worker, sehingga satu OpenBLASpool64thread. Prediksi/innerF1 sama tetapi loss beda maksimum8,4612e-8 dan hashweights berbeda. Dengan threadpool_limits(1), fold1 seluruhselectedinner3 metadata/loss/hashweights/score persis sama.
- Tambahkan auditor terpisah `e24_semantic_mlp_verify_singlethread.py`: env OMP/OPENBLAS/MKL_NUM_THREADS=1 sebelum importNumPy/sklearn; semua assertion lama tetap. Sourceworker/checkpoints/output/grid16/dataset/label tidak diubah. Auditorawal/log dipertahankan sebagai bukti. Jalankan hanya auditor baru, bukan trainingulang/fullgrid atau pengurangan ketelitian audit.
- Verifikasi compile/hash lokalserver lalu seluruhselectedinner/refit5 harus exactmetadata/hashweights/scaler/predscore. Jika gagal, lanjutdiagnosis tanpa klaim skor. Rootaudit memeriksa hash auditor baru setelah complete.

## Hasil final dan batas
- Auditor singlethread691b6ed1d20ee991c394abfb1056f731de9d19a2bfd82c2b47250262148e3694 selesai exit0; semua selectedinner3/refit5 scaler/modelweight/loss metadata, inner scores dan740prediksi cocok exact. Worker asli/data/grid16 tidak berubah. Auditorawal/log dipertahankan; masalah import-thread diperbaiki pada auditor terpisah, bukan dengan melonggarkan equality.
- Rootcopy memeriksa delapanhash, current worker/auditor/helper/fusion sources, semua740ID/truth/fold dibanding baseline, lima partisi592/148, gridordering/firstargmax/selectedauditmean, fixedepoch/finite loss dan manual confusion/perclassF1.
- Macro-F1 **0,5358067460479774**. VerificationserverSHA9f6b033e5f995f3db00b558929eaa6628395778a10780027acb2a8f7bc4dd2bc; bukti `docs/server-recovery/2026-10-11/e24_semantic_mlp/root_verification.json` dan `full_oof/`.
- Semua fold memilih50epoch dari innertraining. Di bawah E14fixed0,5662691391334344; modelbest tidak diganti, tujuan utama0,70 masih aktif. Auditor tidak mengulang fullgrid; repeated experiment selection bias tetap. E22 masih live dan independen.
