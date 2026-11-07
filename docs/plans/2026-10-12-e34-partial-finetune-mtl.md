# E34 — Fine-tuning terbatas CLIP–IndoBERT joint MTL

**Tanggal:** 2026-10-12
**Status:** done

## Tujuan
Menguji adaptasi ringan kedua encoder, menghindari mengulang full-finetuning120epoch yang sebelumnya menurunkan Task2 ke0,2461. Tetap satu model CLIP–IndoBERT dengan tiga task dan XAI yang dapat mengalir melalui head/encoder.

## Ruang Lingkup
- `DEMO_XAI_745_FULL/01_notebook/e34_partial_mtl/`: worker, launcher Kaggle private, checks dan audit.
- Hasil/bukti terpisah `04_hasil_eksperimen/e34_partial_mtl/` dan `docs/server-recovery/2026-10-12/e34_partial_mtl/`.
- Kuota aktual CLI12Oktober: GPUtersisa6,71/30jam, refresh17Oktober. Pengguna secara eksplisit mengizinkan hanya Kagglegratis.
- Tidak mengubah layanan7862/dataset/label, tidak memanggil hostedAI/APIberbayar atau membeli kuota.

## Langkah
1. Bekukan resep sebelum E33selesai: CLIPViT-B32/IndoBERTbasep1 asli, shared256/dropout0,4, visualweight2, taskloss1:2:1.
2. Bekukan encoder kecuali2blok terakhir CLIP/IndoBERT dan final visualnorm/projection. Headwarmstart120epoch fitur beku pada subsetlatih saja; differentialLRencoder2e-6/head3e-4, weightdecay1e-4.
3. Outer5fold identik baseline. Innerholdout20%Task2seed123 dari outertrain memilih epoch0..12 berdasarkan Macro-F1Task2. Epoch0 menjadi opsi jika adaptasi merusak. Refit dari pretrained pada seluruhoutertrain selama epochpilihan, lalu prediksioutertest sekali.
4. Uji CPU sintetik logika freeze/jointgradient/splitselection tanpa mengunduh bobot baru. Kaggle P100tunggal, timeout2700detik, maksimal1jobaktif. Smoke2step terlebih dahulu untuk mengukur laju dan numerik; full5fold hanya setelah smoke lulus dan kuota minimal2jam.
5. Simpan checkpointdelta parametertrainable+head, baseweighthashes, split, logepoch dan740OOF. Tidak memakai outerlabels untuk memilih epoch/konfigurasi.
6. Audit hasil dan catatperbandingan semua3task; tidak mempromosikan otomatis sampai XAI/unggahan dan reproduksi teruji.

## Risiko & Asumsi
- Sisa kuota terbatas; timeout45menit/job dan smoke<5menit membatasi penggunaan. Runtimehabis menghasilkan eksperimen parsial tanpa skor CVpenuh.
- Fine-tuning belum tentu menaikkan skor; epoch0dipertimbangkan melalui inner saja.
- Fiturwarmstart diperiksa pada inputbenchmark; bila fiturcache tidak tersedia, ekstraksi encoder beku sekali untuk740input pada GPU sebelum fithead (tanpa labeltest untuk fit).
- Pemilihan berulang korpus sama masih bias; perlu holdout eksternal untuk klaim akhir0,70.

## Verifikasi
CSV/image/baseweighthash, disjointouter/innerindices, classweights/warmstart training-only, masktrainablebenar keduaencoder, semuahead/shared mendapatgradient, finiteAMP/updateencoder nyata, smoke2step dan runtime, prediks740sekali, perclassMacroF1 ketiga task dihitung independen. Tidak ada Qwen/E5/BGE/SVC.

## Progres
- CPU preflight menggunakan model asli: masktrainable/frozenparameter, gradientkeduaencoder, sharedlayer dan ketigahead lulus; finite loss/gradients.
- Smokeprivate `yusepmuhamadzazuli/tempo-e34-partial-mtl-smoke` versi1 dimulai P100tunggal, internetoff, timeout300s. Sumber/wheels/weights memakai datasetKaggle yang sudah tersedia. Belum menjalankanfullsebelumsmokelulus.

## Penyesuaian alokasi GPU sebelum retry
- Smokev1 berhenti sebelumtraining: Kaggle memberikan jumlahCUDAdevice berbeda dari permintaanP100tunggal. Guard bekerja; tidak ada skor atau checkpoint yang dianggap berhasil.
- Retryv2 menerima palingbanyak2GPUgratis yang dialokasikan, merekam nama/jumlah aktual dan mengalikan walltime dengan jumlahGPU dalam guard. Model memakai GPU0; alokasi tambahan tetap dihitung sebagai biaya kuota, bukan disembunyikan.
- Timeoutfull diturunkan1350s (maks45GPUmenit jika2GPU); internalbudget2400GPUdetik. Smoke tetap300s (maks10GPUmenit). Ini menggantikan asumsiP100tunggal45menit pada langkah4, tanpa menambah komitmenberbayar.

- Smokev2 **passed**,2AMPsteps,59,74detik: CLIPprojection dan IndoBERTlastblock berubah4,0047e-6; sharedhead berubah0,0006004; finite loss0,9224. Smoke bukan skorCV. Kuota sebelumfull **6.68jam**, memenuhi gate≥2jam. Full5fold berikutnya diizinkan dengan timeout1350s, guard2400GPUdetik.

## Hasil evaluasi
- Task2 0,3533093282; Task1 0,4062644319; Task3 0,3223234762;373,07detikGPU; epochpilihan11/10/2/7/10. Target0,70belumtercapai. Tidak mempromosikan ke delivery.
- Auditserverlulus; E35selectedinner/outerrefit dan baselineparity direproduksi, rootstdlib/pairedbootstrap juga lulus. E34auditprotokol/output/deltacheckpointlulus; sampledCPUforwardaudit sedang dilakukan.

- E34sampledforwardCPU: seluruh5checkpointdelta direkonstruksi;15heldoutinput×3task(45prediksi) identik dengan GPUAMP. E35rootauditmetric/hash/740OOFdanbootstrap2000 lulus. Target0,70tetapbelum; faseE36 menguji backboneCLIPlebihbesar/cropgeometrik.
