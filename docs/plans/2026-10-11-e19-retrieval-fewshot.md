# E19 few-shot hosted dengan retrieval training tiap fold

**Tanggal:** 2026-10-11
**Status:** done

## Tujuan
Memberikan contoh kategori dari outer-training kepada VLM hosted untuk membantu domain sumber metafora, dengan evaluasi OOF740 sah menuju0,70. Persiapan berjalan tanpa request API selama E18 aktif.

## Ruang Lingkup
- `DEMO_XAI_745_FULL/01_notebook/e19_fewshot/prepare.py`, hasil `04_hasil_eksperimen/e19_fewshot/` input manifest JSONL/config; plan/changelog/recovery.
- Model awal Gemini3Flash sama E18; belum memulai inference. Sebelum inference tambahkan worker/auditor/budget dan bukti saldo/model/token ke plan.
- Dataset/label asli, E18/E15/E12 aktif tidak diubah. Tidak melatih encoder, tidak memakai anotasi description/mapping.

## Langkah
1. Baca original740 CSV dan frozen BGE-M3 combined740x1024 yang hash/model sudah diverifikasi. Rekonstruksi outer5 baseline Task1 stratified seed42.
2. Untuk setiap outer-test, pilih tepat2 contoh terdekat kosinus per7kelas hanya dari outer-training592, tie indexascending. Query BGE combined tidak memakai targetlabel. Semua contoh14 berbeda dan tidak dari testfold. Tidak ada hyperparameter search dari testlabel.
3. Bangun prompt: codebook/target E12/E15 tetap plus14 contoh teks (E01deskripsi400karakter, sumber/alasan200, headline120), urut kode lalu nearest. Cantumkan kode label training contoh secara eksplisit; ilustrasi hanya gambar target384 nanti. Beri instruksi bahwa contoh adalah training dan target harus dinilai mandiri, jawaban satu kode.
4. Audit setiap740 retrievalID/index/outerfold/trainmembership/classcounts/urutan kosinus, targetlabel permutation invariant pada fungsi querybuilder dengan contoh dibekukan; simpan740 prompt hashes dan trace selected trainingID/label/similarity. Jangan ekspor label target dalam request manifest.
5. Kompilasi dan hash salinan source/input. Belum hitung skor parsial, belum menggunakan kuota. Setelah E18 terminal dan biaya tersedia, tetapkan budget sebelum inference pada plan yang diperbarui.

## Risiko & Asumsi
- Retrieval memakai label hanya milik training; contoh berbasis caption otomatis bisa keliru, label training tetap asli.
- Penggunaan model hosted harus menyisakan kuota harian dan tidak paralel dengan E18 agar audit biaya perrequest terjaga.
- Few-shot bukan jaminan0,70; hasil baru sah setelah all740 dan audit independen. Contoh14 dipilih sebelum melihat skor E18/outertest.

## Verifikasi
Hash originaldata/BGE/source E01 cocok,740 target dan5fold148,14contoh pertarget hanya outertrain dengan2/class, bukti ranking kosinus, prompt invariant terhadap perubahan targetlabel. Hasil persiapan bukan klaim kualitas.

## Hasil persiapan
- Source SHA256 `1b5f53843afc359dbf8c90d6babf99573f63cc16abab38f715bacf691d1b4562`; kompilasi dan hash salinan cocok. Inputs740 SHA256 `66ef704a01a1f47a2f93cf30caa7a269f61e223c2a9cba2beb56bdf8394ad9bb`, panjang prompt12399–13510karakter (mean13095,27).
- Server membuktikan cosine ranking/trainingmembership dan prompt target-permutation invariant. Root memeriksa independen10360 membership/label/code terhadap baseline E14 terverifikasi,740ID/fold/prompt-hash dan dua hash source/input cocok. Bukti `docs/server-recovery/2026-10-11/e19_fewshot/preparation_verification.json` menjelaskan batas cek lokal.
- Tidak ada request API E19 atau skor. Inference menunggu E18 terminal serta budget/protokol worker yang ditetapkan berikutnya.

## Scope lanjutan: worker dan auditor
- Tambahkan `verify_inputs.py`, `run.py`, `verify.py` di folder E19. Inference tetap belum dimulai sampai E18 terminal, strict740 dan parsernya terverifikasi, keduanya di bawah0,70, saldo resmi minimal6,10USD dan token valid. Perubahan scope ini ditulis sebelum membuat kode.
- Model/prompt/example14 tetap yang sudah dibekukan. Max output4096token untuk memberi ruang reasoning, gambar target384 PNG, tanpa temperature/tools/grounding. Parser eksplisit E18 yang sudah dibekukan digunakan, hasil strict tetap ikut dicatat.
- Budget6USD dan reserve0,05USD perrequest, min saldo0,10USD, satu worker dengan fcntl dan persistent marker. Cache complete tidak diulang; marker uncertain/http error memerlukan audit manual. Quota setiaprequest sebelum/sesudah harus cocok usagecost, source/input/hash protocol invariant.
- Auditor input independen merekonstruksi740ranking/outertrain/examplelabels/prompt/gambar sebelum inference; target labels hanya dipakai untuk contoh training dan evaluasi akhir. Auditor output membutuhkan all740, merekonstruksi parsing/biaya/baselinefold dan F1manual vs sklearn. Root perlu copy/hash/cek F1 sebelum klaim.
- Token boleh diperbarui resmi di luar repo tanpa mencetak/copy key, tidak mengubah model/prompt. Jangan upgrade dependency CLI/runtime aktif.

## Hasil kesiapan worker/auditor
- Auditor input independen selesai:740ranking/prompt/gambar direkonstruksi,10360contoh training dicek. Source verifier `1f155f0b91ce7a035c7a9815943c45b85821701db8277d23fa0e37055f41f18b`; bukti `docs/server-recovery/2026-10-11/e19_fewshot/input_verification.json`.
- Worker `193e8662f90484ea920c70f1af1e6b4c0adf9ee38a209e574b718d812a0c7e16`, auditor output `70285a0cabefaa5b454f73e0386d3bb82bdc1d6605a36dff07ae0ebcf9428d63`. Kompilasi dan source hashes salinan server cocok. Gate inference menolak E18 yang belum verified tanpa membuat runconfig/records; gate kualitas menolak keluaran missing tanpa membuat metrics.
- E19 inference belum dimulai; tidak ada biaya/skor. Tetap menunggu E18 terminal/audited, pemeriksaan root dan saldo.

## Pembekuan decodingv2 sebelum training/inference
Sebelum E19/E20 dijalankan, gunakan parser `e18_hosted/parse_v2.py` yang telah lolos22kasus format tanpa targetlabels. E18 strict/v1 tetap dipertahankan. E19 harus menunggu hasil strict/v1/v2 lengkap terverifikasi dan semuanya di bawah0,70 sebelum inference; source/parser/evaluator/OoFhash dipin. E20 memakai kategori zero-shot parsed_v2 saja; tidak memilih parser dari skor heldout. Source E19/E20 diganti sebelum menghasilkan runconfig/checkpoint, lalu gate/kompilasi/hash diverifikasi lagi. Proses E18/watch tetap.

## Verifikasi source setelah decodingv2
- `e19_fewshot/run.py` SHA256 `5228b42750bfdd2d91106b906fc1a7e2b64556d2473c61b6381e7acfd5628c7f`.
- `e19_fewshot/verify.py` SHA256 `38e970beb147fdb86ce75001805aacd6c126e61fb89b2c33b4f5f1199ea40258`.
Kompilasi/hash server cocok; gate E19/E20 tetap menolak E18 belumverified tanpa inference/training/output. Belum ada runconfig/checkpoint/skor baru.

## Kontrak tujuh kelas valid
Sebelum inference, auditor final akan menerapkan fallback majority outer-training yang dibekukan sebelum skor hosted diketahui, menyimpan rawINVALID terpisah dan finalprediction tujuhkelas. Gate E19 memakai tiga skor valid E18, bukan skor diagnostik abstention. Detail plan: `2026-10-11-valid-seven-class-decoding.md`. Worker/source guard/hash kembali diperbarui sebelum runconfig dibuat.

Source E19 setelah kontrak tujuhkelas valid: worker `86f7801e5cf87de3600fb12be7db689398ebf27a72109d3218eb13fec584211a`, auditor `ec4eec85d32b73b32ecdcfe8557eb342a113605b3b9ffce9016957e240eb17a1`. Kompilasi/hash/gate incomplete lolos; belum ada inference.

## Gerbang full siap
- E18 terminal dan seluruh740 cache/final tiga decoding lolos audit server serta root. Final strict0,2521309018/v1=0,3646079161/v2=0,3794801487, semua di bawah0,70. Saldo resmi daily7.2309465USD/monthly97.2309465USD, cukup budget6USD+reserve saldo.
- Source worker/auditor/inputverifier lokal-server cocok hash final di atas; belum ada run_config/records. Token resmi baru expiry03:33:18UTC valid, secret tetap600; tidak ada inferensi E18 aktif. E20 berjalan CPU dan tidak memakai API.
- Launch E19 satu worker tmux dengan auditor chained hanya exit0; tidak restart karena log kosong saat check_inputs. Penjaga akses mengikuti PID/starttime baru setelah lock bebas. Batas6USD/protokol/retrieval/parserv2 tetap, tidak ada keputusan dari skor heldout untuk mengubah prompt.
- Worker2469787/starttime205778375 aktif tmux tempo-e19, auditor chained verify.py; respons pertama complete/kodeA/cost0.003621USD lolos quota guard. Penjagaakses2473061 mengikuti worker asli, lock akses bebas karena E18 terminal. Pemeriksaan berikutnya5/740 cost0.0253205USD; belum ada skor kualitas E19.

## Audit final dan recovery salinan
- Recovery clean expiry661/740 telah selesai sesuai `2026-10-11-e19-access-recovery.md`; worker1400094 melanjutkan hanya request baru, source/prompt/runconfig tetap.
- Setelah terminal/all740/verification server selesai, salin output lengkap tanpa secret ke recovery lokal. Periksa seluruh hash manifest, source pins dan740 ID/truth/fold terhadap E14, parsing strict/v2 dari rawresponse, fallback mayoritas dari592outertraining per fold secara independen, biaya perrequest/quota/cumulativebudget dan manual7kelasF1. Simpan root_verification.json. Tidak mengulang inference; jika audit belum selesai jangan klaim skor final terverifikasi.

## Hasil final terverifikasi
- Seluruh740 respons lengkap; worker/penjagaakses/auditor terminal. Server audit reconstruct740ranking/prompt/gambar dan quota selesai.
- Root memeriksa745hash manifest/current sourcepins,740originalID/truth/fold,10360trainingmembership/code, seluruh raw strict/v2 parsing, fallback mayoritas592training secara independen, biaya/quota740 dan confusion/F1manual.
- Final Macro-F1=0,4507245053076869; strict dengan fallback=0,36239666423795497. RawINVALIDv2=20, dipertahankan dalam trace; finalprediksi7kelas semuanya. Cost=4,064538USD kuota Kaggle gratis, di bawah budget6USD. Bukti `docs/server-recovery/2026-10-11/e19_fewshot/root_verification.json` dan full_cache.
- Belum mengungguli E14fixed0,5662691391 atau mencapai0,70. Inference tidak diulang; audit root tidak mengulang ranking/gambar yang sudah direkonstruksi auditor server. Bias pemilihan eksperimen berulang tetap dilaporkan. E22 menyiapkan fitur caption gambar tanpa kategori sebagai strategi berikutnya.
