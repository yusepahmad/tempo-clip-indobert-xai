# E45 — Joint feature mixup dan warmhead regularisasi

**Tanggal:** 2026-10-13
**Status:** in-progress

## Tujuan
Menguji regularisasi untuk gaptrain-heldout E42 yang besar, tetap740sampul asli dan CLIP–IndoBERT shared3task. Semua3MacroF1≥0,70 dan delivery/XAI gates tetaptarget.

## Ruang Lingkup
- Source baru `01_notebook/e45_feature_mixup/`, hasil/recovery, status/changelog. CacheE41dipakaiulang.
- Tidak mengubah data/labeltersimpan, E44livejob, source/hasil sebelumnya atau delivery. Mixup hanya augmentasi representasi training, bukan penambahan sampulberlabel.

## Langkah
1. Enamconfig: mixupalpha[0;.2;.4] × warmheadweightdecay[1e-4,0,01]. Beta(alpha,alpha); alpha0identitas. Satu pairing/lambda yang sama untuk seluruhrepresentasifused dan semua3task, hanya trainingindices.
2. Warmhead120epoch mixup pada fused frozenfeatures; kemudian tail last2block + sharedhead training, mixup sesudah fusedfeatures sebelum sharedhead, gradients tetap mencapai tail. Loss lambda*weightedCE(y)+(1-lambda)*weightedCE(y_permuted), taskweights1:2:2. Classweights training-only dan tetap asli.
3. TailLR1e-4/head3e-4/wd0,01/drop0,3,batch32,epoch[0,2,4,8,12,24],seed42. Nested5×2 maxminimumacross-taskmeaninnerF1; tiesconfig/epochawal. Resetsetiapfit; nooutertestselection.
4. Checks alpha0loss/gradient parity, lambda0/1 endpoints, allmodality/taskpairing, heldouttraininginvariance, deterministicwarmhead, jointtail/shared/3headgradient. Tidak melakukan fitmodelpenuh sebelumE44selesai diaudit.
5. GPUgratis smoke sebelumfull,resourcegates≥2jam/pay-to-scalefalse/noactivejobs,timeout2100s/internal3600GPUdetik. GPUAMPprovisional; canonicalCPUFP32all740checkpointOOF, nested/source/hash/rootaudit.

## Risiko & Asumsi
Mixedrepresentasi belumtentu validsemantik untuk metafora, sehingga efek harusdibuktikan. Mixup awalnyaaugmentasi convexinput/target; implementasiini pada fusedfeatures, bukan rawimage/text. Tidak menjamin0,70; repeatedCVlimitations tetap.

## Verifikasi
Loss/gradientendpoints, alpha0CEparity, training-only/determinism/gradient, pinnedcache/source/data/checkpoints/splits/configselection,740canonicalOOFmanualMacroF1all3. Reference https://arxiv.org/abs/1710.09412. Deliveryclean/XAI/newuploads belum otomatislulus.

## Progres persiapan
Model/worker6config/evaluators tersedia dansyntaxlulus; CPUpreflight lulus alpha0loss/gradientparity, lambdaendpoints, mixedfeaturegradients, cache/tailreconstruction danheldoutwarmheadinvariance denganmixupalpha0,2 aktif. Jointtail/shared/3headgradients melalui mixup lulus. Rootsyntheticrejectchecks lulus. TidakadaGPU/fullfitE45; E44masihRUNNING. Launcherbelumdibuat.

Launcherprivateoffline smoke/full dibuat dansyntaxlulus. Smoke dipinconfigterakhir alpha0,4/warmwd0,01 agarGPU menguji augmentasiaktif; fullprotocoldefault tidakberubah. Source/README disinkronserver. TidakadajobE45diluncurkan; masihmenunggu E44selesai/audit.

## Progres eksekusi
E44COMPLETE/auditedpassed. ResourcegateCLI6,16jamgratis dan pay-to-scalefalse. Smoke `tempo-e45-feature-mixup-smoke` version1 berhasilpush timeout300s/T4; full belumdijalankan. Smokeconfigalpha0,4/warmwd0,01 menguji mixupaktif.
