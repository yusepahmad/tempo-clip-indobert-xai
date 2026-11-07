# E40 — MMoE CLIP–IndoBERT untuk target ketiga task

**Tanggal:** 2026-10-12
**Status:** done

## Tujuan
Mengejar Macro-F1≥0,70 untuk KETIGA task, bukan hanyaTask2. Menguji shared experts dan task-specific gating untuk perbedaan kebutuhan ketiga task. Hasil sebelumnya belum memenuhi target; tidak menyatakan goal selesai.

## Ruang Lingkup
- `DEMO_XAI_745_FULL/01_notebook/e40_balanced_mmoe/`, output/recovery, status/changelog dan `docs/GOAL_DELIVERY_GATES.md`.
- Reuse fitur CLIP-L14 full/crop dan IndoBERTCLS/mean dari E36/E37, CPU .31, tanpa download/GPU/API baru.
- Tetap740sampul/labelasli dan foldbaseline. Tidak mengubah delivery aktif atau menghapus eksperimen lama.

## Langkah
1. Grid26 sebelumouter: baselineB32CLS; sharedL14both+mean control; 2text(CLS/mean)×2expertcounts(2/4)×2hidden(64/128)×3lossweights(1:1:1;1:2:2;1:1:2). MMoEdrop0,3;visualweight2;120epoch. Semuaexperts dipakai bersama; gate danhead per task; semua losses positif.
2. Nested5outerbaseline×2innerTask2seed123. Pilih maksimum nilai minimum dari meaninnerMacroF1 tiap task; ties pertama. Simpan inner per-task scores, semuaOOF3task, checkpoint/grid/sourcehash/splits.
3. Uji kontrolbaseline, determinisme, heldoutisolation, sharedexpert mendapatgradient dari setiap task, gate simplex/finite, checkpoint roundtrip dan inputgradient untuk XAI.
4. Audit selectedinner/outerrefit/740OOF dan hitungmanualMacroF1independen. Targetreached hanya jika ketigaMacroF1≥0,70. Evaluasi tradeoff tiap task.
5. Buat kontrak artefak kandidat dan daftar gate final delivery: input baru, XAI faithful, cleaninstall, E2E, manifest/hash dan dokumentasi reproducible. Tidak mempromosikan kandidat otomatis sebelum gate selesai.

## Risiko & Asumsi
740sampul sedikit untukMoE; dropout/hiddenkecil diuji, bukan jaminan0,70. Repeatedselectionkorpus sama tetap eksploratif. Tidak mengubah label atau memakai rationale/mapping/labeltest. Pernyataan "tidak ada batasan" tidak dipakai untuk membeli layanan tanpa anggaran eksplisit; default tetap Kagglegratis dan data740 yang disetujui.

## Verifikasi
Referensi primer https://research.google/pubs/modeling-task-relationships-in-multi-task-learning-with-multi-gate-mixture-of-experts/. Baselineexact, source/data/featureaudit hashes, disjointnestedindices, minimum meaninnerF1 terhitung ulang, selectedmodel/state/OOF parity, all3manualF1, XAIinputgradients/checkpointroundtrip. Completion goal membutuhkan semua3task≥0,70 DAN semua gatedelivery terverifikasi.

## Progres
- Checks26configs/exactbaseline/balancedselection/sharedexpertgradientseachtask/gatesimplex/heldout/determinisme/XAIinputgradient/checkpointparity lulus. NestedfitCPU .31 dimulai melalui `tempo-e40-balanced`; auditorchained setelahfitsukses.
- Goalcompletiongates dan kontrak checkpoint/model kandidat ditulis; fullimage/text XAI runtime/unggahan/cleanpackage belum diklaim selesai. KaggleE36 kini tidakditemukanAPI dan kuota kembali6,56jam; tidak diluncurkanulang.

## Hasil terverifikasi (2026-10-13)
Server audit dan root stdlib audit lulus: Task1 0,461670380; Task2 0,418296539; Task3 0,373591441. Target ketiganya belum tercapai. Hasil terpisah; delivery tidak dipromosikan.
