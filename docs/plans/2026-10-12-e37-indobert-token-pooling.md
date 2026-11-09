# E37 — Pooling token IndoBERT dalam joint CLIP MTL

**Tanggal:** 2026-10-12
**Status:** done

## Tujuan
Menguji apakah agregasi token teks memberi representasi lebih berguna daripada CLS asli, tanpa mengganti keluarga CLIP–IndoBERT dan tanpa menambah740sampul.

## Ruang Lingkup
- `DEMO_XAI_745_FULL/01_notebook/e37_token_pool/`, hasil `04_hasil_eksperimen/e37_token_pool/`, recovery, ringkasan status dan changelog.
- CPU .31, weights IndoBERT asli dari cache lokal; tidak ada GPU/API/downloadbaru.
- Tidak mengubah label, fold, data, E36 yang berjalan atau aplikasi delivery/XAI.

## Langkah
1. Ekstrak maskedmean layerterakhir dan rata-rata4layerterakhir token nonpadding/nonspecial dengan input asli headline [SEP] supporting, max128. Simpan fitur768tiapview, model/tokenizer/source/datahash dan urutan sampel. CLSdireproduksi terhadapfiturcachesemua740 sebelumfit.
2. Grid17dipatok: baselineCLScontrol +2pool×Task2weight[1,2]×drop[0,2;0,4]×visualweight[1,2], joint3headshared256/120epoch. Gambar CLIPB32asli dipertahankan untukmengisolasi perubahanteks.
3. Nested5outerbaseline×2innerTask2seed123, selectedinner-only. SimpanOOF3task/checkpoint/split/trace/baselineparity.
4. Uji maskpadding/special, heldoutisolation/determinisme/gradientsemuahead; auditselectedinner/refit/OOF dan hitungF1stdlibindependen. Dokumentasikantradeofftanpapromosiautomatis.

## Risiko & Asumsi
Poolingbelumtentulebihbaik; teksmengandungkontekspolitikbukanvisualmetafora. Repeatedselectionkorpus sama membatasiklaimgeneralisasi. Tidak memakai source_description/annotator/mapping atau labeluntukekstraksi. Target0,70hanyadiklaimjikaaktualvalid.

## Verifikasi
Localmodelhashes,740CLSparity,unitnorm/finite/order, tokenmaskanalitik,baselineexact,disjointnested, refitparity740prediksi3task,manualMacroF1. Data/label740tetap, resourceCPUtanpabiayaAPI.

## Progres
- Checks17configs/maskpadding-special/determinisme/heldout/gradientrouting lulus. PipelineCPU .31 dimulai melalui tmux `tempo-e37-token-pool`: extract → featureaudit → nestedfit → selectedrefitaudit; tahap berikutnya hanya setelah tahap sebelumnya sukses.

- Ekstraksi740selesai60,66detikCPU; CLSseluruh740cocokcachebaseline. Auditor model/source/datahash,mask/norm/order dan12sampledpoolforward lulus. Nestedfit sudah berjalan setelah gate ini.

- Selesai5fold: Task1MacroF1=0,48511260538451273;Task2=0,3692446110998054;Task3=0,34432550371463444. Selectedconfigs10/8/8/7/8. Baselineparityexact; auditselectedinner/outerrefit/740OOF lulus. Rootstdlibhash/manualF1 lulus; deltaTask2vsbaseline+0,04951847, intervalbootstrapeksploratif[0,01947;0,07899]. Target0,70belum; aplikasi belum diganti.
