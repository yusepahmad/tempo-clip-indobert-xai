> **Penyesuaian 12 Oktober:** E14 dipertahankan sebagai pembanding historis, bukan model utama tesis. Delivery utama diganti joint CLIP–IndoBERT MTL melalui [plan penyelarasan](2026-10-12-align-delivery-clip-indobert-mtl.md). Hasil audit E14 di bawah tetap merupakan riwayat paket E14.

# Delivery Week 3–4 dengan backend E14 berversi

**Tanggal:** 2026-10-12
**Status:** done

## Tujuan
Atas instruksi user, prioritaskan delivery E2E dengan E14 Task2 Macro-F1 OOF0,5662691391334344, tanpa menunggu0,70. Pisahkan backend/modelmanifest dariUI/batch/ekspor agar kandidat terverifikasi berikutnya bisa mengganti model melalui kontrak yang stabil. Week3 merupakan revisi demo yang sudah ada; Week4 ditetapkan sebagai integrasi E14, pengujianE2E dan paketdelivery, bukan mengulangWeek3.

## Ruang Lingkup
- Snapshot source server6Okt yang lebihbaru daripada source UI lokal, di folder staging baru `delivery/week34_20261012/DEMO_XAI_745_FULL/` (lokal) dan `/home/research-user/workspace/learn/delivery_week34_20261012/DEMO_XAI_745_FULL/` (server). Tidak menimpa source baseline atau service live lama.
- Modul backend/registry/versionedmodel baru, export/audit scripts, integrationtests/E2E, manifest/modelcard/release notes/statusWeek34, paketZIP/checksum. Artefak model di06_models/e14-v1, bukti bertanggal terpisah.
- Plan/rootCHANGELOG serta sinkronisasi salinan ke server project. E32 yang masih berjalan tidak dihentikan atau dipromosikan otomatis.
- Dataset/label asli, hasil eksperimen/OOF lama, dan credentials tidak diubah/disertakan. Tidak menambah providerberbayar/APIrequest atau deployment publik.

## Langkah
1. Inventaris/snapshot source server terbaru dan identifikasi seluruh kontrak input/prediksi/XAI/batch/ekspor. Pertahankan perbaikanWeek3server yang belum ada di source lokal.
2. Siapkan backendE14 terpisah: hashverified3072frozenfeatures, pipelineStandardScaler/L2weighted/SVC; ekspor5modelOOFselectedparams dan scaler+manifest untuk datasetoriginal. Cocokkan semua740prediksi keE14OOF. Artefak fullfit untukdata baru memakai recipe yang dinyatakan, tidak menganggap in-sample sebagai evaluasi baru.
3. Kontrak perprediction menyertakan backend/version/evaluationmode/scorekind; Macro-F1 merupakan metrik OOFTask2, bukan probabilitas sampel atau skor ketigatask. UI/batch/ekspor harus menyatakan model serta sumberpenjelasan yang sesuai.
4. Pilihan jalurunggahan ditanyakan karena E14 memerlukan Qwen-generateddeskripsi/source-reason serta E5/BGEencoding, bukan hanyacheckpoint: (a) phaseddatasetE14+baselineuploads berlabeljelas, atau(b) fullE14upload dari awal denganlatensi/integrasilebihlama. Jangan implementasikan keputusan dependen sebelumjawaban. Sambilmenunggu: snapshot/export/registry/tests/docs yang independen.
5. XAI baselineGradCAM/LIME tidak boleh diklaim menjelaskan prediksiE14. UntukE14dataset, sediakan atribusi input/block yang benar atau keterbatasan eksplisit; jangan memalsukan heatmap/E14probability. JalurXAI/backend bisa diubah tanpa membongkarUI.
6. Sesudah scopeunggahan jelas, integrasikan satuan/dataset/edit/unggah/OCR/batch/review/export/error; jalankan regresi existingWeek3 dan browser desktop/mobile, modelidentity/OOFparity/semua740IDs serta upgrade/rollbacksmoke. Uji cleaninstall platformyang tersedia, catat Windows jika belumdiuji.
7. Paket review/delivery berversi dengan hashmanifest tanpa cache/venv/secrets; tulis actualstatusWeek3/Week4 dan changelog sesudah perubahan. Deliveryready hanya untuk scope yang terbukti, tanpa mengklaim0,70 atau semua3task0,5663.

## Risiko & Asumsi
- E14 adalah keluargaSVCfusionTask2, bukan3headMTL checkpoint. ArsitekturdanmetodeXAI berbeda; UIterjaga tetapi backendupgrade bisa membutuhkan encoder danatribusi baru.
- Fitur E5/BGE dariGPUFP16 sebelumnya, liveCPUembedding mungkin berbeda; perlu parity/latencytesting jikafulluploads. OriginalQwen8B liveCPU bisa mahal; tidak menjanjikan waktusama denganbaseline.
- Hashverifiedtrustedjoblibartefacts boleh dimuat hanya setelahmanifestmatch; tidak menerima checkpointupload pengguna.
- Future0,70hanya dipromosikan sesudahvalidOOF+backendcontract/E2Etests; interface stabil mengurangi perubahan aplikasi, tidak menjamin semua modelplug-and-play.
- Packagingpersiapan baru; tidakmengubahserviceport7861 yang berjalan sebelum E2Ebaru lolos. User sudahmengizinkan eksekusi delivery, tidak perlu meminta approvalulang untuk reversiblestaging.

## Verifikasi
Hash source snapshot/localserver/artifact;740OOFexactparity/labels/split; backendversion danscorekind konsisten diAPI/UI/export; dataedit tidak memakai cachedfeaturesusang; XAI attribution menggunakanbackendyang benar; OCR/unggah/batch/error/browser/cleaninstall smoke; manifestCRC/checksum dan upgrade/rollback. Limitriset/OCR/Windows dicatat jujur.

## Keputusan user: full E14 unggahan
- User memilih **E14 wajib untuk unggahanbaru sejakdeliverypertama**, menerima waktuintegrasi/inferensilebihlama. Tidak ada fallbackdiam-diam kebaseline. Task1/3 tetapbaseline; Task2E14.
- Tambahkan persiapan/pengunduhan snapshot publik Qwen3-VL-8B-Instruct revision0c351dd01ed87e9c1b53cbc748cba10e6187ff3b dan multilingual-e5-base revisiond128750597153bb5987e10b1c3493a34e5a4502a jika belumcached; BGE-M3 snapshot E22 tersedia. Verifikasi metadataofficial/LFSsha danfilepins. Ini unduhanbobotpublik+inferensilokalCPU, bukan hostedAIAPI/paidprovider. Modelassets dipisah dan setupmanifest mencatat kebutuhan disk/unduhan; tidak memasukkan credential.
- Livepipeline mempertahankan promptA/promptB E01,maxside1024,greedy220/260tokens, E5queryprefix/maskedmeanL2512, BGECLS/L21024; CPUFP32 berbedaGPUFP16 asal, drift danlatensi harusdiukur/dilaporkan. Cachekey imageSHA+headline+support+pipelineversion, label/catatanmanual tidak digunakan.
- XAI Task2 memakai backendE14: RBFdecisionfunction yang direkonstruksi/diperiksa keSVC untuk gradien komponenCLIP; captionsemanticsdibekukan saatatribusiCLIP dan keterbatasan ditampilkan. Atribusiteks memproses BGEcontext baru dengan source-reason tetap, tidakmengklaim regenerasiQwen untuk tiapperturbasi. Explanationpipeline/version ditandai jelas.

## Penyesuaian XAI sebelum implementasi
- Untuk mempercepat integrasi dan menghindari gradienSVCmulticlass yang keliru, Task2 memakai **occlusion gambar pada49region gambar asli, hanya komponenCLIP berubah; deskripsi/source-reason tetap**, langsung mengukur perubahan skordecisionE14. Task1/3 tetapgradientCLIPbaseline; peta gabungan berlabel metodecampuran. Jangan menyebut Task2GradCAM atau atribusi keseluruhanQwen.
- LIME/occlusionteks Task2 memakai variasijudul padaBGEcombined dengan deskripsi/source-reasonQwen tetap. Modeloutputs tetapSVC; relative-decision-softmax ditandai skorrelatif, bukanprobabilitasterkalibrasi. UI/narasi/ekspor disesuaikan agar tidakmemalsukan keyakinan.

## Progres terverifikasi
- Snapshot888file dari source server terbaru, hash lokal/server cocok. Artefak E14 lima fold + refit all740 diekspor; prediksi740 OOF persis dan Macro-F1 0,5662691391334344.
- Tiga snapshot publik immutable Qwen/E5/BGE sudah diunduh dan hash official LFS cocok (~20,97GB total). BGE revision ini menyediakan `pytorch_model.bin`, bukan safetensors; downloader diperbaiki setelah metadata official diperiksa. Model dimuat melalui transformers/torch terbaru dalam lingkungan server; tidak ada API AI berbayar.
- API dataset tiga task + heatmap/atribusi occlusion lolos. Uji unggahan Qwen CPU sedang berjalan; belum menyatakan delivery ready.

## Kelengkapan snapshot untuk delivery
- Sertakan tiga gambar revisi dosen di `06_gambar_revisi/`, dua notebook historis Week3, dan helper `audit_finetuned_week3.py` yang diperlukan tes lama. Manifest snapshot888file tetap sebagai rekaman snapshot awal; file tambahan dicatat dalam manifest paket final. Notebook historis diberi penunjuk ke kontrak delivery E14, bukan mengubah hasil evaluasi lama.

## Verifikasi integrasi dan environment
- HTTP dataset tiga task, unggahan E14 penuh, pengulangan cache+LIME, OCR, batchunggahan+review, datasetdiedit, pembatalanpre-cancel dan request berikutnya: lulus. Unggahan pertama321,7detik, cache+LIME40,4detik (CPU8threadserverini, bukan jaminanlatensi).
- Audit backend740OOF/manualF1/heldout/tamper sebelumdeserialisasi/routing/cancel lulus. CPUFP32 E5/BGE pada3sampelcosine>0,999996 denganprediksisama; bukan auditsemuaembeddinglive/Qwen.
- 83tesregresi lama lulus setelahbaseURLstagingbenar danfixturesbaseline dilengkapi. Empat tesJS lokal lulus. Dua tescontract versiE14/rollbackbaseline lulus dalamenvironmentLinuxbaru.
- CleaninstallLinux Python3.10.12 denganPyTorchCPU2.14.1,transformers5.18,sklearn1.7.2 berhasil. Hosttidakpunyaensurepip; venv baru dibuat --without-pip, pip environmentlama hanya dipakai sebagaiinstaller --python target (tanpasystem-site-packages). Aplikasi kini berjalan memakaiinterpreterbaru; uji gambar revisi dosen yangSHA-nya tidakada dalam740dataset masihberlangsung.

## Penutupan delivery
- Uji gambar revisi dosen dengan SHA byte tidak terdapat pada740dataset lulus padaenvironmentbaru:378,8detik. Uji ini membuktikanjalurunggahan, bukanholdoutperforma independen.
- Browser finaldesktop/mobile padaenvironmentbaru lulus lima tab hasil, tanpa pageerror/overflow halaman. Browser unggahan nyata→OCR→koreksiteks→E14→LIME→heatmap lulus,37,2detik memakai cache. Banner membaca metrik/version dariAPI, sehingga upgradeE14keluargayangsam tidakmemerlukan editangkadiUI.
- Bukti55URLasset diarsipkan dalam07_delivery_evidence besertamanifest3snapshot,fiturlivecontoh,environmentdanlog. Petunjuk terbaruDELIVERY.md,notebookpemeriksaanE14,launcherdefaultE14,danstatusWeek34 disiapkan. Dokumentasi baseline diberi penunjuk sebagai riwayat.
- ZIPawal lolosCRC/seluruhhash/exclusioncache-venv-secrets. Paket final mencakupplan/changelogpenutupan; bobot20,97GB dipisah denganpinnedsetup/manifest. Defaultserverstagingreviewdi10.12.1.31:7862; tidakmenimpasource/servicebaselineportlama. Windows,produksipublik,ujipenggunamanusia dantarget0,70tidakdiklaimselesai.
