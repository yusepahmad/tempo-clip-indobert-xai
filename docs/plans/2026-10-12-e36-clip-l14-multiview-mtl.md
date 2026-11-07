# E36 — CLIP ViT-L/14 dan crop ilustrasi dalam joint IndoBERT MTL

**Tanggal:** 2026-10-12
**Status:** done

## Tujuan
Menguji batas fiturvisual setelah E33/E34 bertahan sekitar0,353 dan E35PCGrad0,343. Tetap keluarga CLIP + IndoBERT joint3task, tanpa VLMgeneratif/SVC. BackboneCLIP lebihbesar dan crop geometrik merupakan ablasi yang harus dilaporkan eksplisit.

## Ruang Lingkup
- `DEMO_XAI_745_FULL/01_notebook/e36_clip_l14/`, hasil/recoveryE36, plan/changelog.
- Modelpublik `laion/CLIP-ViT-L-14-laion2B-s32B-b82K`, revisioncommit/LFSsha dipin sebelumrun. Download≤3GB publicweights perhost (cacheKaggle untuk ekstraksi dan cacheCPUserver untuk reproduksi) (bukan hostedinference) dan frozenfeature extraction Kagglegratis.
- Tidak mengubah dataset/label, BERTcache asal, baseline, demo7862atau arsip.

## Langkah
1. Pin officialmodelrevision/LFSdigest/config; ekstrak740fullimage dan cropfixed [0,0.20,1,0.94] melaluiCLIP-L14 yang sama. Tidak memakai label/anotasi/rationale untuk memilihcrop.
2. Kaggleprivate, internet hanya untuk downloadweights publik, maksimum2GPUalokasi, timeout600s, guard900GPUdetik. Cekkuota≥2jam dan tidakadajobE34aktif sebelumlaunch.
3. PadukanL14full768/crop768/dua-view1536 dengan IndoBERT768 asal. Grid25: baselineB32kontrol +3view×Task2weight[1,2]×dropout[0,2;0,4]×visualweight[1,2]. Shared256 dan3heads jointloss120epoch.
4. Nested5outeridentikbaseline×2innerTask2seed123, pilihfamily/hyperparams melaluiinner saja. Catat3task740OOF, checkpoint,hash,splits,trace dan baselineparity.
5. Reproduksi6featureforward padaCPU dengan weights yang sama, auditnorm/hash/sampleorder/crop, selectednestedrefit dan rootMacroF1.
6. Jika gagalnaikbermakna, lanjutkan diagnosisdata/representasi dengan bukti; target0,70tidakdiklaim otomatis. IntegrasiXAI L14/multiview adalah scope berikutnya jika kandidatlayak; aplikasiutama belumdiganti.

## Risiko & Asumsi
- Backbonebesar/crop tidak menjaminperbaikan; metafora memerlukan konteks dan labelkonsisten.
- Data historis25XAI menunjukkan22/25peta dominan kepala sampul; crop menguji hipotesis perhatianilustrasi, bukan bukti croplebihbaik.
- Cumulativeselectionbias tetap ada walau nested; perluholdoutbaru untukklaimfinal.
- Labelkonteks/metaphor_mapping tidak boleh masukfitur, labeltest tidak boleh memilihview/crop/grid.

## Verifikasi
Modelcardprimary https://huggingface.co/laion/CLIP-ViT-L-14-laion2B-s32B-b82K. Commit/LFS/SHA/imagehash, finiteunitnorm740×2, cropROI seragam, CPUrepro6, disjointindices/controlbaselineparity, selectedrefitpredictionparity3task, rootstdlibF1. Semua resource hanya kuotagratis dan downloadpublik.

## Progres
- Modelpinned revision1627032197142fbe2a7cfec626f4ced3ae60d07a; fileopen_clip_pytorch_model.safetensors1.710.517.748byte, SHA2567d129ed747e0ed53e82dfcc140382b51be66b56e6a9bdc3258afd2846e3bb019.
- E34terminalCOMPLETE sebelumlaunch; kuota6,56jam memenuhi gate. FeaturejobprivateT4dikirim dengan timeout600s; labeltidak digunakan ekstraksi.

- CPUmodelcacheL14download/pinnedLFS hash lulus;25config/fourview/determinisme/heldoutisolation/visualtextgradientrouting checks lulus. GPUserveextractor belumdigunakan untukfitsebelum norm/hash/order dan CPUreproduksi6lulus.

- Keputusan pengguna: batas penelitian tetap 740 sampul; hanya optimasi model, tanpa penambahan sampul atau perubahan label.

## Penyesuaian jalur ekstraksi (sebelum implementasi)
- Karena antrean Kaggle belum menghasilkan log/artefak setelah sekitar 15 menit, siapkan `cpu_extract.py` sebagai pemanggil extractor yang sama (FP32, dua thread, crop/pin identik). Boleh dijalankan di CPU .31 bila Kaggle tetap belum tersedia setelah 20 menit atau gagal. Tidak mengubah `extract.py` yang sudah dikirim.
- Output CPU dipisah di `04_hasil_eksperimen/e36_clip_l14_cpu_fallback/`. Jika kedua ekstraksi selesai, gunakan hasil Kaggle bila lengkap dan lolos audit, selain itu CPU lengkap/lulus audit; keputusan tidak memakai label/metrik. Simpan asal dan manifest, jangan gabungkan baris antarjalur.
- Tidak meluncurkan ulang GPU. CPU dapat tumpang tindih sementara dengan antrean GPU; pembatas waktu GPU lama tetap berlaku. Audit forward CPU dan nestedCV tetap wajib sebelum klaim skor.

- Ruang lingkup dokumentasi: `docs/CLIP_INDOBERT_OPTIMIZATION_STATUS.md` merangkum E33–E36, batas 740 sampul dan bukti terverifikasi; disinkronkan ke workspace server bersama plan/changelog.

- CPUfallback diluncurkan .31 melalui tmux `tempo-e36-cpu-extract` setelah20menit tanpaoutputKaggle; log `e36_cpu_extract.log`. Dataset/label tetap740.

- Pengukuran CPU aktual dua thread lebih lambat daripada benchmark delapan thread. Fallback boleh direstart sebelum fitur lengkap, dengan `cpu_extract_impl.py` salinan extractor yang hanya mengganti jumlah thread2→8. GPU `extract.py` dipertahankan byte-identik; auditor menerima hash sumber GPU atau hash CPU yang terbukti berbeda hanya pada pengaturan thread. Hasil tidak dicampur.

- Fallback8thread selesai740full+crop778,69detik, tanpaGPU. Kaggle tetapRUNNING/nooutput; CPU dipilih sebelumfitnested dan tanpa metriklabel, asal disimpan`extraction_origin.json`. Auditforward12vector sedangdijalankan.

- FeatureauditE36 selesai: seluruh740imageSHA/order/unitnorm/pinnedweights/source lulus,12CPUforwardcocok. Nestedfit25config berjalanCPU; source/grid dibekukan sebelumouter.

## Hasil akhir
{
  "task1_issue": {
    "macro_f1": 0.4177581099841574,
    "accuracy": 0.4472972972972973
  },
  "task2_domain_sumber": {
    "macro_f1": 0.4315215326436391,
    "accuracy": 0.4554054054054054
  },
  "task3_primary_entity_type": {
    "macro_f1": 0.34549634020026876,
    "accuracy": 0.4635135135135135
  }
}

Baseline parity identik; audit server selectedinner/outerrefit dan semua740OOF ketiga task lulus. Root stdlib hash/manualMacroF1 lulus. Target0,70belum tercapai. Tidak dipromosikan ke aplikasi.

## Kendala sesi Kaggle
- Sesudah hasilCPU selesai, API masih melaporkan jobGPU RUNNING tanpa output/log; runtime melebihi timeout600s yang diminta. Streamlogs500; kuotaused akun terusbertambah (belum bisa atribusikan seluruhdelta kejobini).
- SDK resmi memiliki cancelberdasarkan kernel_session_id, tetapi status/pull/output tidak memberi IDsession; browserCUA tidaktersedia. Tidak menebakID, tidakmenghapuskernel atau meluncurkan ulang. Meminta pengguna konfirmasi sesiaktif/ID agar penghentianbisa dilakukan.
- Pemeriksaan09:54UTC: kuotaGPUtersisa5,6267jam; pay-to-scale false. Modelhasil tetap menggunakanCPU yangsudahdiaudit, tidak tergantungjobini.
- Recheck10:50UTC: hanyaE36 yang RUNNING (E34/E15/E12/E13 danlainnya COMPLETE), jadi penurunan kuota dapat diatribusikan keE36. KuotaGPU25,31jam terpakai /4,69jam tersisa (refresh2026-10-17). Log tetap kosong. Endpoint cancel `/api/v1/kernels/cancel-session/{id}` terkonfirmasi di SDK, tetapisessionid tidak diekspos oleh status/output/list; penghentian tetap menunggu konfirmasi/id pengguna.
- Keputusan pengguna: dibatalkan manual melalui web UI Kaggle (Notebooks → Running → stop session). Hasil eksperimen tidak terpengaruh karena memakai fiturCPU teraudit; verifikasi status→COMPLETE/CANCELLED dan kuota berhenti bertambah dilakukan setelah pengguna menghentikan.
- Stop dari web UI gagal; pengguna menghapus paksa (delete) kernel `tempo-e36-clip-l14-features`. Verifikasi12:09UTC: kernel hilang dari daftar, sesi berhenti, dan kuota turun/rekonsiliasi dari26,57jam ke23,44jam terpakai (sisa6,56jam; sebelumnya3,4jam). timeUsed stabil pada dua sampel berjarak50detik (84377,5s identik). Kebocoran kuota berhenti; tidak ada job GPU lain yang aktif.
