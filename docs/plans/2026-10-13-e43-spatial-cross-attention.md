# E43 — Spatial CLIP tokens dan text-conditioned attention

**Tanggal:** 2026-10-13
**Status:** done

## Tujuan
Meningkatkan dekoding metafora melalui informasi wilayah gambar yang hilang pada global pooling. Tetap CLIP–IndoBERT joint3task,740sampul asli dan target semuaMacroF1≥0,70.

## Ruang Lingkup
- Source `01_notebook/e43_spatial_attention/`, fitur/hasil/recovery E43, status/changelog.
- Ekstraksi label-free CPU server memakai pinned CLIP-L14 E36, full/crop sama. Patchtokens16×16 dipool rata-rata menjadi4×4, diproyeksikan dengan CLIP visual.proj ke768 dan L2normalize;32regionaltokens per sampul.
- Tidak mengubah E36–E42 source/hasil, data/label/fold atau delivery.

## Langkah
1. Ekstrak32regionaltokens dan periksa globalfeatures full/crop seluruh740 identik E36 tolerance2e-5. SimpanSHA source/model/data/images,layout/tokenprojection; audit independent sampledforward sebelum training.
2. Implementasi shared text-conditioned regionattention, sharedfusion3heads dengan positivejointloss. Konfigurasi/epoch/grid ditetapkan di plan sebelum fitting; nested5outer×2inner dan maxminimumtaskmeanF1. IndoBERT asli, tanpa Qwen/E5/BGE/rationale.
3. Checks attention simplex/heldout/datahash/gradients/determinism sebelum fit; CPU bila memadai, GPU hanya kuotagratis setelah smoke+resourcegates.
4. Canonical740OOF/checkpoint/auditsroot/manualF1; deliverybaru/XAI faithful/cleaninstall tetap gates terpisah sebelum final release.

## Risiko & Asumsi
Patchfeatures belum tentu lebih baik dan spatialpool bisa mengurangi detail. Attentionweights bukan otomatis explanationfaithful. Perlu graph reconstruction dan perturbation sebelum XAIrelease. Tidak mengubah data atau label untuk memenuhi target. RepeatedCV bukan independent holdout.

## Verifikasi
740globalparity/order/imageSHA, pinnedweights,32×768finite/unitnorm; independent sampledforward. Training/protokol ditambahkan sebelumfit. Semua3targetboolean bersama dan provenance/checkpoint audit.

## Progres awal
Ekstraksi CPU tmux `tempo-e43-regions` aktif di server. Log pertama REGIONS16/740 setelah28detik; parity/shape assertions lulus pada batch tersebut. Auditor independen6sample sudah tersedia, belum dijalankan hingga cache lengkap. Model training belum dibuat/fit, sehingga belum ada skor E43.

## Protokol training ditetapkan sebelum fit
- Input: globalCLIPfull/crop1536 + frozenIndoBERTmean/CLS768 + regionalCLIP32×768. Head kontrol tanpaattention(mean,hidden256,loss1:1:1);8kandidat attention: hidden128/256 × teksmean/CLS × loss1:1:1/1:2:2. Total9config.
- Shared attention: query dari teks, keys dari region, dim64 scaled-dot-product softmax32region; valuesdim128. Learned32×64position embeddings. Attendedvalue digabung globalvisual×2+teks lalu sharedMLP/ReLU/drop0,4 dan3heads. Attentionshared antar3task.
- Semua120epochs AdamWlr0,001/weightdecay0,001, seed42, training-only inverse-frequency classweights. Tidak menambah supervised labels/inputs.
- Nested5×2 baseline folds; pilih maxminimumacross-taskmeaninnerF1, tieconfigawal. Resetsetiapfit. Full GPU FP32 (TF32off), canonical CPUFP32checkpoint740OOF; jika perbedaanpred dilaporkan tanpa memilihprecisionbyquality.
- Smoke sebelumfull, requirefreequota≥2jam/pay-to-scalefalse/nootheractivejobs. Fullinternalguard3600GPUdetik,CLI2100s; tidak retrylivejob. Source/config/inputhashes/splits/checkpoints disimpan.

Progres berikutnya: ekstraksi112/740 pada135,4detik tanpaassertionfailure. `model.py`/`checks.py` tersedia dan serverchecks lulus:9config, balancedselection/ties, attention simplex/shared3taskgradients, heldoutisolation, determinism dancheckpointparity. Belum training model pada data740; worker/evaluator GPU masih disiapkan.

Progres worker: `prepare.py` memaketkan hanya fitur/data teraudit dengansource/inputSHA; `worker.py` smoke/fullGPUFP32 nested9config×5outer×2inner, split/search/checkpoint/protocol/OOF3task danresourceguard dibuat. Semua source syntaxlulus dan disinkronkanserver. Worker belumdijalankan; auditor hasil/launcher masihpersiapan. Ekstraksi224/740 pada258,2detik tanpaassertfailure.

Auditor `verify_result.py` dan root evaluator tersedia; semua source syntaxlulus. Uji sintetis root lulus validfixture serta menolak false target/wrongTask3metric/modifiedOOF/inputSHA. Verifier menghitung ulang pemilihan9config independently dan canonical740CPUFP32; belum dijalankan terhadap model. Ekstraksi320/740 pada355,6detik tanpaassertfailure.

## Otomasi audit setelah ekstraksi
`finalize_features.py` memantau handle tmux spesifik `tempo-e43-regions`; setelah handle terminal wajib completedmanifest, lalu run independentfeatureaudit dan preparepackage secara sequential/check=True. Tidak restart ekstraksi atau meluncurkan GPU. `build_launchers.py` membuat privateoffline launchers dari sourcebytes+packageSHA. Tahap upload/smoke/full tetap resourcegatesbaru.

Ekstraksi740selesai808,92detik CPU; globalE36paritymaxabs0,0. Independentfeatureaudit lulus all740imageSHA/unitnorm/source/featurehash dan6sampleforward (max4,92e-6). Package ready, disalinlokal dan seluruhpackagefileSHA diperiksa builder. Privateoffline smoke/full launchers dibuat. Uploadprivate dataset sedangberjalan; quota6,34h/pay-to-scalefalse/E42COMPLETE diperiksa.

Private dataset `yusepmuhamadzazuli/tempo-e43-spatial-features-20261013` uploadberhasil dan statusready. Smoke launcher dikirim timeout300s/T4; full belummulai.

Smoke `tempo-e43-spatial-smoke` versi1 pushberhasil, status resmiRUNNING. Belumsmokeresult/skorE43; nofull/duplicatejob.

Smoke resmiCOMPLETE/passed8,78detik worker,2TeslaT4; query/key/value/position/shared/all3heads updates positif, source/packageSHA cocok. Kuota6,33jam/pay-to-scalefalse diperiksa. Full dikirim timeout2100s/internal3600GPUdetik.

Full `tempo-e43-spatial-full` versi1 berhasilpush dan resmiRUNNING. Tidakada hasilqualityE43; checkpointCPUFP32/rootaudit menunggu outputfull.

## Hasil akhir
Full COMPLETE74,63detikworkerGPU; serveraudit9configselection/split/checkpoint/input/source dan740CPUFP32 serta rootmanualF1/hash lulus. Canonical Task1 0,46730067691718935; Task2 0,42458340094039876; Task3 0,36745921609882026. GPU/CPU pred differences0/0/0. Selected[6,0,0,6,1],attention3/5fold. Minimumtask turun dariE42 0,39556ke0,36746; tidakdipromosikan. Targetsemua0,70belum. Regionalfeatures tersimpan untuk pengujian model lanjut; attentionweights belumfaithfulXAI.
