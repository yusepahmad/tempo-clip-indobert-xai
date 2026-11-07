# E44 focal tail MTL

Lima konfigurasi: weighted CE gamma0/power1 control, focal gamma1/2 × classpower0,5/1. Tail LR1e-4, head3e-4, taskweights1:2:2 dan epoch0/2/4/8/12/24. Warmhead120epochs E41 weightedCE tetap; positivejoint3loss dan sharedtail/head. Cache pinnedE41 dipakai ulang.

Rumus focal memakai unweighted CE untuk pt, kemudian alpha training-only di luar focal; gamma0loss dan gradients harus identik weightedCE. Absentclassweight0. Original paper: https://arxiv.org/abs/1708.02002 ; manfaat padaTempo belumdiasumsikan.

Nested5×2 memilih config/epoch maxminimumacross-taskmeaninnerF1; ties config/epochawal. Outertest tidak memilih. GPUAMP scores provisional, canonicalCPUFP32 seluruh740 checkpointforward. `verify_cache.py`, `verify_result.py`, `root_verify.py`, `check_root_audit.py` mengikuti E42, dengan5config dan focalchecks.

GPU hanya kuotagratis/privateoffline dataset E41, smoke sebelumfull dannoactivejob. Resourceguard/timeouttersimpan pada protocol. Kontrak fullgraphXAI/unggahanbaru mengikuti E41README; tidak mengganti delivery sampai gates kualitas/XAI/cleaninstallterbukti. RepeatedCV tetap limitation.
