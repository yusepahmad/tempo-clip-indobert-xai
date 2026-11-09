# E38 — Joint MTL CLIP-L14 dan pooling token IndoBERT

**Tanggal:** 2026-10-12
**Status:** done

## Tujuan
Menguji kombinasi representasi visualE36 dan teksE37 tanpa GPU/ekstraksibaru. E37terverifikasi0,3692; target0,70belum.

## Ruang Lingkup
- `DEMO_XAI_745_FULL/01_notebook/e38_l14_token/`, output/recoveryE38, ringkasanstatus/changelog.
- Reuse fiturE36/E37 hanya setelahkeduanya lulusfeatureaudit. CPU .31.
- Dataset/label740,baseline/delivery,metrikhasilE36/E37 tidakdiubah. TanpaVLM/SVC/API.

## Langkah
1. Tetapkan25konfigurasi sebelumouter: baselineB32CLScontrol +3visual(full/crop/both)L14×2textpool(mean/last4)×Task2weight[1,2]×visualweight[1,2]. Shared256drop0,4/120epoch joint3head.
2. Uji routingsemuaview/determinisme/heldout dan gatefeaturehash/order/audit.
3. Nested5outerbaseline×2innerTask2seed123; selectedinner-only, simpan3task740OOF/checkpoint/split/trace.
4. Auditselectedinner/outerrefit/baselineparity danrootmanualF1. Laporkanketigatask, tidakmempromosikanautomatis.

## Risiko & Asumsi
Kombinasibelumtentumembaik. Repeatedexperimentselectionkorpus sama membatasigeneralisasi; target0,70tidakbolehdipalsukan/diperolehdengangantilabel. Cropgeometrik/teksasli tidakmemakaimappinglabel.

## Verifikasi
Hash/order/unitnorminputterverifikasi, disjointnestedindices,baselineexact,refitpredictionsparity,740manualF1, semua3headjointgradients. SeluruhfitCPUserver,tidakadabiayaAPI.

## Progres
- Checks25configs/sevenviewpairs/determinisme/heldout/routing/jointgradients lulus. Menunggu featureauditE36 sebelumfit.

- FeatureauditE36 selesai: seluruh740imageSHA/order/unitnorm/pinnedweights/source lulus,12CPUforwardcocok. Nestedfit25config berjalanCPU; source/grid dibekukan sebelumouter.

## Hasil akhir
{
  "task1_issue": {
    "macro_f1": 0.4835092774370205,
    "accuracy": 0.5067567567567568
  },
  "task2_domain_sumber": {
    "macro_f1": 0.4054966017319787,
    "accuracy": 0.4283783783783784
  },
  "task3_primary_entity_type": {
    "macro_f1": 0.37465096761044686,
    "accuracy": 0.46621621621621623
  }
}

Baseline parity identik; audit server selectedinner/outerrefit dan semua740OOF ketiga task lulus. Root stdlib hash/manualMacroF1 lulus. Target0,70belum tercapai. Tidak dipromosikan ke aplikasi.
