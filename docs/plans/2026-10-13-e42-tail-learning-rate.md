# E42 — Nested tuning tail learning rate dan loss

**Tanggal:** 2026-10-13
**Status:** done

## Tujuan
Meningkatkan ketiga task bersama menuju Macro-F1 0,70 melalui adaptasi IndoBERT yang lebih tepat, memakai cache E41 teraudit.

## Ruang Lingkup
- Source baru `DEMO_XAI_745_FULL/01_notebook/e42_tail_grid/`, hasil/recovery E42, private Kaggle kernels, status dan changelog.
- Tidak mengubah source/hasil E41, 740 data/label, outer folds atau delivery aktif.

## Langkah
1. Enam konfigurasi tetap: encoder LR [2e-6,2e-5,1e-4] × loss [1:1:1,1:2:2]; head LR3e-4. Epoch [0,2,4,8,12,24]. Semua memakai dua tail blok dan shared3head E41.
2. Inner2fold pada masing-masing outer5fold. Pilih config/epoch dengan maksimum minimum across-task mean inner Macro-F1; ties urutan config lalu epoch. Reset pretrained tail dan training-only warmhead untuk setiap fit. Tidak memilih berdasarkan outer test.
3. Smoke sebelum full; cache/source hash dan GPU gratis/pay-to-scale/activejob diperiksa. Full budget internal3600GPUdetik dan timeout2100s; no duplicate live job.
4. Audit source/splits/selection dan seluruh740checkpoint CPU FP32 canonical, root stdlib metrics/hash. Skor GPU provisional. Simpan semua trace dan checkpoint.
5. Catat hasil, keterbatasan repeatedCV, dan lanjutkan delivery hanya jika semua quality/XAI/newupload/clean gates terbukti.

## Risiko & Asumsi
Grid dapat overfit inner folds dan tidak menjamin0,70. High LR bisa tidak stabil; finitechecks wajib dan partial CV tidak diterima. Eksperimen memakai kuota gratis saja. Full XAI harus reconnect encoder graph, cachegradient saja belum cukup.

## Verifikasi
Config count/selection tie fixture, reset/positive3loss/gradient checks; smoke allparameter updates; SHA source/cache/checkpoint, fold provenance dan heldout isolation, CPU FP32 all740 forward/manualF1 dan target semua task. Delivery belum diganti.

## Progres
Source/launchers disiapkan dan syntax lulus. Preflight CPU server lulus, termasuk6config/selection tie, cacheSHA/reconstruction/heldout invariance/joint gradients. Bukti `docs/server-recovery/2026-10-13/e42_tail_grid_preflight.json`. Kuota6,51jam, pay-to-scalefalse, E41full COMPLETE. E42smoke versi1 push berhasil, resmi RUNNING. Full belum dikirim; auditor nestedconfig belum dibuat.

Auditor E42 dibuat: memeriksa semua6config×2inner traces, menghitung ulang selection secara independen dan forward seluruh740CPUFP32; root auditor/hash fixtures disiapkan. README mencatat kontrak dan batasan. Full belum dikirim; smoke terakhir RUNNING.

Smoke COMPLETE/passed5,21detik worker; tail/shared/all3head updates positif, sourceSHA cocok,2T4. Auditor root sintetis lulus. Kuota6,49jam/pay-to-scalefalse diperiksa; full dikirim timeout2100s/internal3600GPUdetik.

## Diagnosis E41 saat E42 masih live
Read-only klasifikasi740OOF menunjukkan Task3 legislature F1=0,1429 (19sampel), political_party0,2400 (30), government0,3333 (108); individual0,6992 (315). Task2 KONSUMSI_TRANSAKSI0,2360 (84),27sampel diprediksi MESIN_INFRASTRUKTUR. Ini diagnosis eksploratif untuk desain berikutnya; tidak mengubah config/source/job E42 dan bukan klaim independent holdout.

## Hasil akhir
Full COMPLETE,483,17detik worker. Audit server seluruh6candidate traces×2inner×5outer, checkpointSHA dan740CPUFP32forward serta root manualMacroF1/input/output SHA lulus. Task1 0,5254826236457082; Task2 0,3955604325695003; Task3 0,40339840958144335. GPU/CPU pred differences0/0/0. Selectedconfigs[5,5,5,3,4],epochs[12,12,2,8,8]. Min task0,39556 naik dariE41 0,38570 tetapi Task2 turun. Semua0,70 belum; delivery tidak dipromosikan.
