# E41 — Cached frozen front dan fine-tuning tail IndoBERT jointMTL

**Tanggal:** 2026-10-12
**Status:** done

## Tujuan
Mengadaptasi representasi bahasa untuk ketiga task, melampaui frozenhead. Menjaga CLIP-L14full/crop + IndoBERT jointMTL, targetSEMUA3MacroF1≥0,70 dan deployment/XAI yang dapat direkonstruksi.

## Ruang Lingkup
- `DEMO_XAI_745_FULL/01_notebook/e41_cached_tail/`, source/model/cache/audits, output/recoveryE41, privateKaggle dataset/kernel, status/changelog/gates.
- CPU .31: sekali encode pretrainedIndoBERT hingga10layer, cacheh10FP32 berisi740×128×768 denganpaddingzero, attention/poolmask dan frozenCLIP-L14views. Simpan pretrained2tailblock/config/hash. Tidak memakai label dalamekstraksi.
- PrivateKaggle upload hanya cache/data model yang sudah diizinkan, tanpa publikasi. Offlinewheels dari benchmarkexisting; internetfalse runtime, nohostedAPI. GPU hanya kuotagratis (gatequota≥2jam,pay-to-scalefalse,noactiveE36) dan1jobatatime.
- Tidak mengubah dataset/label/fold, benchmarkdeliveryaktif atau hasil sebelumnya.

## Langkah
1. Ekstrak h10 dengan snapshotIndoBERT asli dipinE37. Zero paddedtokens saja; validtokens equivalence diuji melalui forward tail melawan fullencoder serta pooledmeanE37semua740. Simpan data/source/model/featureSHA, masks dansampleorder.
2. Kandidatfixed: 2BERTblocks trainable, frozenCLIPbothviews, shared256/drop0,3 +3heads, visualweight2, taskloss1:2:2. Warmstarthead120epochtraining-only. TailLR2e-5/head3e-4, AdamWdecay0,01, batch32, AMPFP16GPU. Tidak mengubah frozenfrontweights.
3. Nested5outerbaseline×2innerTask2seed123. Untuksetiapinner, epochcandidates[0,2,4,8,12]. Pilih maksimum minimum across-taskmeaninnerMacroF1 tiapepoch; ties epochterawal. Resetpretrainedtail + warmheadoutertraining danrefitepochpilihan, prediksioutertestsekali.
4. CPU preflight memeriksa cache/tail equivalence, joint3head/tailgradient, finites, masks/heldouttraining-only. GPUoffline smoke2steps dahulu; full hanya setelahsmokelulus. CLItimeout900s(full), internalguard1200GPUdetik (alokasi1–2GPUdirekam); smoke300s/internal240GPUdetik. Jangan retry jobyangmasihlive.
5. Simpan5tail/headcheckpoint, protocols/inputhash/splits/epochtrace/740OOF3task, all3targetboolean. Audit cache, nestedselection/source, rootmanualF1, checkpointCPU sampledforward. Siapkan reconstructioncontract: fullimage/text frozenfront original + trainedtail/head; fullXAI/cleanpackage masihgatefinal terpisah.

## Risiko & Asumsi
Cachelowerlayers detached sah karena weights bagianini beku; XAI delivery harus menghubungkan kembali fullgraph untuk inputgradients. Mengubah cachepadding tidak boleh mengubah validtokenforward. Kaggle startup dapat gagal; tidak mengasumsikan timeout/requestedhardware selalu dipatuhi. Reportalokasi/kuota/terminalstatus. Target tidakdijamin; repeatedCVselection limitations dicatat. Label/mapping/rationale tidak menjadi fiturekstraksi.

## Verifikasi
Pinnedmodel/source/datahash,740pooledbaseparity,6sampled full-vs-cachetail tokenforward, paddingmaskfixtures, shared/tail/all3headgradient, training-onlywarmstart/classweights, nesteddisjoint/epochselection, 740OOFmanualF1all3, checkpointpredsampleparityCPU/GPU, privateuploadmanifest dan resourcegates. Goal tidakcomplete sebelumsemua3≥0,70 + semua deliverygateslulus.

## Penetapan presisi evaluasi sebelum GPUrun
- Training/innerselection menggunakanAMPGPU. SkorGPUOOF bersifatprovisional; evaluatorserver merekonstruksi seluruh740OOF memakai checkpointFP32diCPU sebagai presisi canonical delivery, menghitung ketigaMacroF1 dan perbedaannya tanpa memilihpresisi berdasarkan skor. BaselineOOF dari kontrolterverifikasiE33 disertakan besertahash, tidakdirefitGPU.

## Progres 2026-10-13
Cache/preflight server lulus; hash semua file salinan lokal cocok. Dataset privat ready. Kernel `research-account/tempo-e41-cached-tail-smoke` versi 1 berhasil dikirim dengan timeout300s, status resmi RUNNING. CLI kuota6,56jam; pay-to-scale SDK false. Full belum dikirim; menunggu smoke terminal/lulus.

Evaluator canonical `verify_result.py` dan root independen tersedia; syntax evaluator lulus di server. Belum dieksekusi terhadap hasil model. Poll ulang smoke resmi RUNNING; logs/output masih kosong. Tidak ada full/duplikat yang dikirim.

Smoke resmi COMPLETE dan smoke.json passed (4,89detik worker,2TeslaT4). Hash worker/model/cache cocok; seluruh parameter group berubah. Kuota6,55jam dan pay-to-scalefalse diperiksa sebelum full. Launcher full dibuat dari source identik, hanya TEMPO_SMOKE=0.

Full kernel `tempo-e41-cached-tail-full` versi1 berhasil dikirim (timeout900s) dan resmi RUNNING. `check_root_audit.py` lulus fixture sintetis valid serta menolak target palsu, Macro-F1 Task3 salah, dan hash OOF berubah. Ini bukti evaluator, bukan skor model.

## Penguatan audit sebelum hasil full tersedia
Simpan hash input cache dan source dengan path relatif root dalam verification.json; auditor root memeriksa ulang hash input. Uji sintetis juga harus menolak perubahan input. Tambahkan README kontrak rekonstruksi unggahan baru/XAI dan jelaskan yang belum terintegrasi. Full job masih RUNNING; tidak mengubah worker/model yang telah dikirim.

Penguatan audit input selesai; checks sintetis lulus termasuk input SHA palsu. README kontrak delivery dibuat; semua evaluator disinkronkan ke server. Poll terakhir full masih resmi RUNNING, log kosong. Tidak ada job duplikat.

Full resmi COMPLETE;81,35detik worker. GPU AMP provisional Task1 0,494795562; Task2 0,419239880; Task3 0,385321511; targetfalse. Lima checkpoint terunduh dan SHA cocok; sudah disalin ke server, evaluator CPU FP32 seluruh740 sedang berjalan. Ini belum skor canonical.

## Hasil akhir eksperimen
Audit server seluruh740checkpoint forward CPU FP32 dan root stdlib/input/output SHA lulus. Canonical Task1 0,495725624055955; Task2 0,4206737615962957; Task3 0,3856956289281086. GPU/CPU pred differences1/2/1. Target semua0,70 belum tercapai. Delivery tidak dipromosikan; XAI/unggahan kandidat belum terintegrasi.
