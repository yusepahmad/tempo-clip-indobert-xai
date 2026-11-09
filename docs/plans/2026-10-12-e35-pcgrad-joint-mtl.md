# E35 — PCGrad pada shared CLIP–IndoBERT MTL

**Tanggal:** 2026-10-12
**Status:** done

## Tujuan
Menguji apakah konflikgradien ketiga task membatasi kenaikanTask2 setelah E33naik0,3530 tetapi Task1turun. Tidak mengklaim konflik telah dibuktikan sebelum diagnosis; target0,70tetapbelum.

## Ruang Lingkup
- `DEMO_XAI_745_FULL/01_notebook/e35_pcgrad_mtl/`, hasil`04_hasil_eksperimen/e35_pcgrad_mtl/`, bukti recovery, plan/changelog.
- CPU1thread .31, fitur CLIP512/IndoBERT768 yang sama, arsitektur shared256/dropout0,4/3head/120epoch.
- Tidak mengubah layanan utama, dataset, label atau penggunaan GPU E34.

## Langkah
1. Bekukan6konfigurasi sebelum outertest: kontrolsumloss (Task2weight1/2, visualweight1), PCGradshared (Task2weight1/2 × visualweight1/2).
2. PCGrad hanya memproyeksikan gradien parameterbersama yang konflik; privatehead memakai gradient jointweightedloss biasa. Seed42; classweights training-only; bobotsemuataskpositif. Catat frekuensikonflik perfit.
3. Nested5outeridentikbaseline×2innerTask2seed123; pilih konfigurasi via innerMacroF1 saja. Kontrolbaseline harus identik metrik historis; simpan OOF3task/checkpoint/split/trace.
4. Uji proyeksi analitik2vektor, nonconflictidentity, determinisme, heldoutisolation dan pembaruanhead/shared. Auditrefitwinner dan metrik740OOF secara independen.
5. Bandingkan dengan E33danbaseline tanpa mempromosikan model otomatis. Catat hasil apaadanya termasuk bila gagalmeningkatkan.

## Risiko & Asumsi
- PCGrad tidak menjamin peningkatan; negative-transfer bukan satu-satunya sumber error.
- Pemilihan berulang dataset yang sama tetap berisiko bias; nestedbukanholdouteksternal.
- Implementasi adalah PCGrad pada sharedparameters dengan privateheads ordinary weightedgradients; bukan klaim salinan identik framework sumber.

## Verifikasi
Sumberalgoritma: https://arxiv.org/abs/2001.06782 dan repositori penulis https://github.com/tianheyu927/PCGrad. Projeksi berlawanan arah menggunakan gradienasli tasklain dan urutan acakseeded; finitegradient, classweights/splittraining-only, baselineparity, selectedrefit dan rootMacroF1stdlib.

## Hasil evaluasi
- Task2 0,3434893436; Task1 0,3958483693; Task3 0,3072914160;196,39detikCPU; selectedconfig5/5/3/3/5. Target0,70belumtercapai. Tidak mempromosikan ke delivery.
- Auditserverlulus; E35selectedinner/outerrefit dan baselineparity direproduksi, rootstdlib/pairedbootstrap juga lulus. E34auditprotokol/output/deltacheckpointlulus; sampledCPUforwardaudit sedang dilakukan.

- E34sampledforwardCPU: seluruh5checkpointdelta direkonstruksi;15heldoutinput×3task(45prediksi) identik dengan GPUAMP. E35rootauditmetric/hash/740OOFdanbootstrap2000 lulus. Target0,70tetapbelum; faseE36 menguji backboneCLIPlebihbesar/cropgeometrik.
