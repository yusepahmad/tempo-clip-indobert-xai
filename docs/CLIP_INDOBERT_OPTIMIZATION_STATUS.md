# Status optimasi CLIP–IndoBERT MTL

Tanggal: 2026-10-13. Target **SEMUA ketiga task Macro-F1 ≥0,70 pada kandidat joint MTL yang sama: belum tercapai**. E40 terbaru terverifikasi: Task1 0,461670380; Task2 0,418296539; Task3 0,373591441. E41 selesai dan audit server/root lulus: Task1 0,495725624; Task2 0,420673762; Task3 0,385695629. E42 selesai/audit server+root lulus: Task1 0,525482624; Task2 0,395560433; Task3 0,403398410. Best per-task lintas eksperimen tidak boleh digabung untuk mengklaim satu model lulus.

## Batas penelitian
Tetap740sampul dan label asli sesuai keputusan pengguna. Semua kandidat memakai encoder keluargaCLIP–IndoBERT, sharednetwork dan tiga head yang dilatih bersama dengan loss positif untuk ketiga task. Qwen/E5/BGE/SVC dan anotasi mapping/rationale tidak menjadi input kandidat ini. Kaggle hanya kuota gratis; pemeriksaan API menunjukkan pay-to-scale tidak aktif. E39 hanya memakai CPU dan fitur cache.

## Hasil terverifikasi
| Eksperimen | Task1 Macro-F1 | Task2 Macro-F1 | Task3 Macro-F1 | Perubahan |
|---|---:|---:|---:|---|
| Baseline |0,438032|0,319726|0,276352|Frozen CLIPB32–IndoBERT jointMTL|
| E33 |0,395052|0,353018|0,319647|Optimasi24konfigurasi head/loss|
| E34 |0,406264|0,353309|0,322323|Fine-tuning2blok terakhir keduaencoder|
| E35 |0,395848|0,343489|0,307291|PCGrad sharedgradient|
| E36 |0,417758|0,431522|0,345496|CLIP-L14full/crop + IndoBERTCLS|
| E37 |0,485113|0,369245|0,344326|CLIPB32 + IndoBERTtokenmean/last4mean|
| E38 |0,483509|0,405497|0,374651|CLIP-L14full/crop + IndoBERTtokenpooling|
| E39 |0,430360|**0,434757**|0,336619|Training-only centering/standardisasi permodalitas|
| E40 |0,461670|0,418297|0,373591|Shared MMoE, pemilihan minimum mean inner F1 tiga task|
| E41 |0,495726|0,420674|0,385696|Fine-tuning dua blok IndoBERT, canonical CPU FP32|
| E42 |0,525483|0,395560|0,403398|Nested6config tailLR/loss, canonical CPU FP32|
| E43 |0,467301|0,424583|0,367459|Text-conditioned regionalattention frozenencoders|

E39 paling tinggi pada Task2 (0,434757), naik tipis dari E36 (0,431522) dan memulihkan Task1 ke0,430360 (E36:0,417758) walau tetap di bawah baseline0,438032; Task3 turun sedikit ke0,336619. E38 meningkatkan semua task dan merupakan pembanding dengan hasil lebih seimbang. Belum ada pergantian aplikasi delivery (http://10.12.1.31:7862); integrasi XAI dan unggahan baru untuk kandidat memerlukan verifikasi tersendiri.

## Protokol dan bukti
Lima outerfold identik baseline. Hyperparameter/epoch dipilih hanya dari outertraining: E33/E35/E36/E37/E38 menggunakan2innerfold; E34 innerholdout20%. Seluruh740prediksiOOF untukketigatask tersedia; baseline direproduksi identik. Auditor server mereproduksi selectedinnerfit, outerrefit dan OOF; auditor root menghitung Macro-F1 secara independen memakai stdlib dan memeriksa hash salinan.

E34 audit forward CPU mereproduksi45prediksi dari15heldoutinput, bukan rerun training GPU penuh. E36 featureaudit memeriksa SHA740gambar, pinnedweights, source/data/order/unitnorm dan12vectorforward. EkstraksiCPU8thread selesai778,69detik. CPU dipilih sebelumfit karena jobKaggle belum memberi hasil; hasil antarjalur tidak dicampur. E37 mereproduksiCLS seluruh740 terhadapcachebaseline dan12sampledpoolforward.

Bootstrap E36−baseline: eksploratif95%interval[0,07305;0,15033]. Pemilihan eksperimen berulang pada korpus yang sama dan overlap trainingfold membatasi interpretasi; hasil bukan holdout eksternal atau jaminan0,70.

Bukti lokal: `docs/server-recovery/2026-10-12/`; E36 lengkap di `e36_clip_l14/final/`, E38 di `e38_l14_token/`, E37 di `e37_token_pool/`. Salinan kerja numerik: `DEMO_XAI_745_FULL/04_hasil_eksperimen/`. Server sumber: `/home/yusep/workspace/learn/DEMO_XAI_745_FULL/`.

## Status akhir batch
E39 selesai10konfigurasi nested5×2,285,63detikCPU. Auditselectedinner/outerrefit/bufferstatistiktrain/740OOF dan rootmanualF1/hash lulus. Best0,4347570621, hanya0,0032355295 di atasE36; tanpa centering terpilih4/5fold, sehingga belum bukti normalisasi memberi manfaat konsisten. Target0,70belum tercapai. Tidak ada fitCPU yang masih berjalan pada batchE33–E39.

## Status E40/E41 dan Kaggle
E40 selesai 26 konfigurasi nested5×2, 850,67detik CPU; audit server serta root independen lulus. Seluruh task naik dari baseline, tetapi tidak ada yang mencapai0,70. Delivery belum diganti.

E41 cache frozen10blok pertama IndoBERT + CLIP-L14full/crop lulus audit740sample dan preflight gradient. Smoke GPU COMPLETE/passed (2TeslaT4,4,89detik worker). Full `yusepmuhamadzazuli/tempo-e41-cached-tail-full` versi1 COMPLETE;81,35detik worker. Semua checkpoint/source/cache SHA dan split/epoch selection lulus audit. Forward CPU FP32 seluruh740 dan manualF1 root lulus. Perbedaan prediksiGPU/CPU1/2/1. Timeout900s dan guard1200GPUdetik; tidak menjalankan duplikat. Training memakai AMP; hasil canonical akan direkonstruksi CPU FP32 seluruh740OOF sebelum klaim kualitas. Integrasi fullgraph XAI/unggahan baru belum dikerjakan untuk kandidat.

Kuota CLI terbaru6,51jam tersisa; pay-to-scale false diperiksa sebelum fullrun. E36 lama kini tidak ditemukan, tidak direlaunch; hasilnya tetap berasal dari jalur CPU teraudit. Bukti smoke: `docs/server-recovery/2026-10-13/e41_smoke/`. Resource status adalah snapshot, bukan janji sisa kuota.

## Plan
- [E33](plans/2026-10-12-e33-joint-mtl-optimization.md)
- [E34](plans/2026-10-12-e34-partial-finetune-mtl.md)
- [E35](plans/2026-10-12-e35-pcgrad-joint-mtl.md)
- [E36](plans/2026-10-12-e36-clip-l14-multiview-mtl.md)
- [E37](plans/2026-10-12-e37-indobert-token-pooling.md)
- [E38](plans/2026-10-12-e38-l14-token-fusion.md)
- [E39](plans/2026-10-12-e39-train-only-feature-normalization.md)

- [E40](plans/2026-10-12-e40-balanced-mmoe-mtl.md)
- [E41](plans/2026-10-12-e41-cached-tail-indobert.md)

## E42 hasil akhir
Selesai483,17detik workerGPU. Audit checkpoint/6configselection/740CPUFP32 serta root manualF1/hash lulus; prediksiGPU/CPU identik. Minimum task naik dari0,385696 ke0,395560, namun Task2 turun dariE41. Semua task≥0,70 belum; delivery tetap. [Plan E42](plans/2026-10-13-e42-tail-learning-rate.md).

## E43 spatial attention sedang berjalan
Ekstraksi740×32×768regionCLIP selesai808,92detikCPU; globalE36paritymaxabs0,0. Independentfeatureaudit allimageSHA/unitnorm +6sampleforward lulus. SmokeGPU COMPLETE/passed8,78detik,2T4, attention/shared/3head updates positif dan source/packageSHA cocok. Full `tempo-e43-spatial-full` versi1 resmiRUNNING. BelumskorE43; delivery tetap. Kuota snapshot6,33jam/pay-to-scale disabled. [Plan E43](plans/2026-10-13-e43-spatial-cross-attention.md).

## Hasil akhir E43
E43 COMPLETE/auditserver+rootlulus: **0,467300677 / 0,424583401 / 0,367459216**. CPU/GPU740prediksi identik; attention3/5fold,dua kontroltanpaattention. Minimumtask lebih rendah dariE42, tidakdipromosikan. Full74,63detikworkerGPU. Targetsemua0,70belum. Bagian E43 RUNNING diatas adalah riwayat, sudahdigantikan hasilakhirini.

## E44 sedang berjalan
WeightedCE/focalgamma1/2×classpower0,5/1:5config nested5×2. CPUloss/gradientparity/cache/heldout/selectionchecks serta rootsyntheticchecks lulus. GPUgamma0smoke COMPLETE/passed5,30detik; full `tempo-e44-focal-tail-full` versi1 RUNNING. BelumskorE44; dataset740/deliverytetap. Snapshotkuota6,29jam/pay-to-scalefalse. [Plan E44](plans/2026-10-13-e44-focal-tail.md).

## Gangguan akses Kaggle terbaru
2026-10-13 sekitar03:24WIB: list/kuota meminta autentikasi ulang dan status E44/E43 tidak dapat diakses. E44 terakhir teramati RUNNING sekitar03:23WIB; status terkini belum diketahui, bukan dianggap gagal/selesai. Recovery88257 belum mengunduh/audit; E45 belum diluncurkan.

## Akses Kaggle pulih
Refresh token akses melalui SDK resmi berhasil; status E44 kembali RUNNING. Gangguan autentikasi sebelumnya teratasi tanpa login ulang/token di chat. E45 tetap belum diluncurkan.

## E46 CPU hasil akhir
Label smoothing/weight decay tujuhconfig nested5x2 selesai178,57detikCPU, auditserver+rootlulus740OOF. MacroF1 **0,457459409 / 0,417845517 / 0,353358005**; selected[3,3,3,3,1], smoothing0,1 terpilih4/5fold. BelummengungguliE41/E42; tidakpromosidelivery. E44 masih dipantau session18517; user mengonfirmasi logtrainingbertambah. [Plan E46](plans/2026-10-13-e46-label-smoothing.md).

## E47 CPU hasil akhir
Joint task-probability refinement delapanconfig nested5x2 selesai231,72detikCPU, auditserver/rootlulus740OOF. MacroF1 **0,456450876 / 0,424848728 / 0,375947487**; refinement4/5fold. Minimum0,375947belum mengungguliE41/E42; tidakpromosi. [Plan E47](plans/2026-10-13-e47-task-relations.md).

## E44 hasil akhir — menggantikan status RUNNING/insiden sebelumnya
COMPLETE; auditserver/rootpassed740CPUFP32. MacroF1 **0,525529885 / 0,393685820 / 0,403833268**. Seluruhfold memilihkontrolweightedCE, bukanfocal. Minimum0,393686lebih rendah dariE42; tidakpromosi. Worker398,03s. Kuotaterbaru6,16jam/pay-to-scalefalse; snapshotlama telahberubah. E45siap smoke setelahresourcegate. [Plan E44](plans/2026-10-13-e44-focal-tail.md).
