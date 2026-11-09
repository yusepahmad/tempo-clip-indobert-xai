# E45 joint fused feature mixup

Enamconfig: alpha0/.2/.4 × warmheadwd1e-4/.01. Warmhead120epochs dan tailtraining sama-sama mixup pada fusedvisualtextfeatures dengan satu pairing/lambda untuk ketiga task. Tidak mengubah740data/labeltersimpan. Mixedloss=lambdaweightedCE(y)+(1-lambda)weightedCE(y_perm). Alpha0identity; inference tanpaaugmentasi. TailLR1e-4/head3e-4/taskweights1:2:2/epochs0,2,4,8,12,24.

Smoke memakai configterakhir(alpha.4,warmwd.01) agar GPU benar-benar menguji mixupaktif. Full nested5×2 maxminimumtaskmeaninnerF1/tiesconfigepochawal; outertesttidakmemilihconfig. Seedreset setiapfit, classweightstrainingonly. CPUpreflight alpha0loss/gradientparity/endpoints, heldoutwarmheadinvariance denganmixupaktif, jointtail/shared/3headgradients dan cachepinned lulus.

Launchers privateoffline menggunakan datasetcacheE41 yangsama. GPU hanya setelahE44terminal/audit, quota≥2h/pay-to-scalefalse/noactivejob; smoke sebelumfull. TrainingAMPprovisional; CPUFP32all740checkpointOOFcanonical dan rootmanualF1/source/input/outputhashaudit.

Adaptasi featuremixup mengacu https://arxiv.org/abs/1710.09412 ; manfaatTempo belumdibuktikan. FullgraphXAI/newupload/productionrefit/cleaninstall masihgates terpisah; deliverytidakdiganti otomatis. RepeatedCVlimitations tetap.
