# E47 refinement hubungan antar-task tanpa teacher forcing

**Tanggal:** 2026-10-13
**Status:** done

## Tujuan
Menguji hubungan prediksi ketiga task dalam satu graph differentiable CLIP–IndoBERT joint MTL untuk target semua Macro-F1>=0,70 tanpa GPU.

## Ruang Lingkup
- Source/output baru E47, recovery/status/CHANGELOG.
- Tidak mengubah740label/sampul/cache, eksperimen sebelumnya, jobE44, E45 atau runtime delivery.

## Langkah
1. Frozen CLIPL14full/crop + IndoBERTmean -> shared256/ReLU/drop0,4 -> tiga initialhead. Concatenate sharedfeature dan softmaxprobabilities ketiga task -> refinementMLP(hidden64/128,ReLU,drop0,4) -> tiga residualhead; final=initial+scale*residual.
2. Tidak ada goldlabel, argmaxdetach, teacherforcing atau OOFprediction sebagai fitur. Satu forward sample independen, semua komponen menerima jointloss.
3. Delapanconfig: baselineasli, L14controlno-refinement, 2hidden x 3scale[0,25;0,5;1]. Refinement wd0,001; controlwd0,0001; positive taskweights1:2:2 kecualibaseline1:1:1. Seed42,120epoch,lr0,001.
4. Limaouterfoldbaselineidentik,2innerTask2seed123. Pilihmaxminimumacross-taskmeaninnerF1, tiesfirst. Preflightbaselineexact, heldoutlabels/featuresinvariance, determinism, cross-taskgradientdanallshared/refinement/3headupdates.
5. CPUfit, selectedinner/outerrefit/hash/all740OOFserveraudit, rootmanualF1. Catatactualresulttanpapromosiotomatis.

## Risiko & Asumsi
Hipotesis desain ini belum terbukti; korelasi task dapat memperkuat kesalahan dan menambahoverfitting. RepeatedCV bukanholdouteksternal. Tidakmenjamin0,70; goldlabels hanya loss training.

## Verifikasi
Preflighttraining-only/baseline/gradients; protocol8configs/splits/selection/checkpoints/reproduced740OOF/rootmetrics. XAI/deliverygates tetap belumotomatislulus.

## Progres
Source syntax dan preflight CPU server lulus baselineexact, label/featureheldoutinvariance, determinism, shared/refinement/3headgradients dan cross-taskgradient. NestedfitCPU dimulai; belumskorfinal.

## Hasil final
Training231,72055detikCPU; selected[5,6,7,1,7], refinement4/5fold. Auditserver selectedinner/outerrefit/baseline/740OOF dan rootstdlib/hashpassed. MacroF1 Task1=0,4564508755957856; Task2=0,42484872807321133; Task3=0,37594748717414106. Tidak mengungguliE41/E42 secara keseluruhan; tidakpromosidelivery. Semua0,70belumtercapai.
