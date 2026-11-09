# Implementasi Evaluasi dan Delivery Revisi II

**Tanggal:** 2026-11-01
**Status:** in-progress

## Tujuan
Melaksanakan plan induk Revisi II yang telah diotorisasi, menghasilkan analisis yang dapat direproduksi, melengkapi eksperimen yang memungkinkan, dan paket untuk Joy dengan status bukti setiap revisi yang jujur.

## Ruang Lingkup
- Source baru `DEMO_XAI_745_FULL/01_notebook/revisi_ii/`, hasil baru `DEMO_XAI_745_FULL/04_hasil_eksperimen/revisi_ii/`, `docs/revisi-ii/`, serta delivery baru `delivery/revisi_ii_20261101/`.
- Menyalin dan menormalkan prediksi tersimpan ke paket baru; membaca metadata dan source historis tanpa mengubahnya.
- Subplan induk, dokumentasi canonical yang terkait, dan root changelog diperbarui berdasarkan hasil aktual.
- ZIP lama, label canonical, worker/source berhash, model aktif dan layanan tidak ditimpa. Model web lama disajikan sebagai demo historis terpisah sampai parity model baru dibuktikan.

## Langkah
1. Inventaris file dan isi arsip seluruh workspace yang relevan untuk bukti anotator/penilai, fitur E01 dan asal dataset; baca revisi awal yang ditemukan.
2. Buat evaluator baru, tes kontrak ID/truth/fold/label dan statistik independen. CI Macro-F1 menggunakan 2.000 bootstrap pasangan pengamatan seed tetap; McNemar exact + Holm untuk akurasi. Perubahan macro diuji lewat CI bootstrap selisih berpasangan, bukan McNemar.
3. Reproduksi kelompok 36 nama dari notebook historis (exclude nama `vlm`/`qlora`), dengan peringatan bahwa ini filter nama, bukan audit backbone. Tambahkan seluruh comparator/kontrol/CI-D01 pada tabel lengkap. Deduplicate signature prediksi per ID dan catat alias serta jumlah konfigurasi bukan dihitung sebagai jumlah alias.
4. Audit arsitektur/source untuk membatasi kandidat utama CLIP–IndoBERT MTL; tetapkan berdasarkan mean Macro-F1 antartask dan pengungkapan post-hoc. Pertahankan ranking minimum sebagai audit dokumen saja.
5. Lengkapi CPU rerun baseline/unimodal/single-task dan class-weighting bila fitur/protokol setara tersedia; gunakan direktori baru, kontrak yang dibekukan sebelum hasil, seed, fold dan log waktu. Eksperimen yang belum memenuhi parity diberi label diagnostik, bukan pengganti ablasi model utama.
   Kontrol backbone beku baru memakai satu image768 dan teks IndoBERT mean768,
   head/seed/loss/120epoch identik untuk CLIP-full/SigLIP2/DINOv2. Untuk memenuhi
   penghapusan rotasi, ekstrak ulang SigLIP2 moderate dengan RNG sama dan
   rotasi nol; jalankan A00/A01/A02_no_rotation/A03 sampler dengan35epoch,
   head192 sama, jumlah paparan/update sama dan seleksi pipeline inner2fold
   mean Macro-F1. Ini keluarga controlled baru, bukan penggantian hasil lama.
6. Gunakan status Kaggle read-only untuk mengecek kapasitas/job lama. Job refit E14 sudah COMPLETE saat observasi; bila dikoleksi, verifikasi penuh sebelum dipakai sebagai bukti. Eksperimen GPU baru hanya setelah audit fondasi dan smoke; batas komputasi dan anti-duplikasi tercatat sebelum submission.
   Eksperimen baru RII tail menggunakan source TailMTL E42 yang disalin byte-identik,
   CLIP-L14 full/crop + IndoBERT front beku/two-block tail, fixed LR2e-5/3e-4,
   loss task1/2/3=1:2:2, class weights training-only, inner2fold Task2 seed123,
   kandidat epoch0/2/4/8 dan seleksi mean Macro-F1 antartask. Arm MTL weighted,
   MTL unweighted, tiga model single-task independen, image-only dan text-only
   memakai outer fold canonical yang sama. Ini controlled recipe baru (bukan
   reproduksi grid E42 enam konfigurasi), dilaporkan terpisah dari E42 historis.
   Evaluasi canonical baru GPU FP32 dengan save/reload parity, bukan GPU AMP
   dibanding CPU FP32 sebagai dua hasil alternatif. Smoke <=180 detik; full
   <=3.600 detik wall dengan guard eksplisit, private, existing datasets only.
   Tidak mengirim ulang run ambigu atau menjalankan full sebelum smoke lulus.
   Tambahan input: baseline rich128 terpotong pada736/740 sampel. Siapkan cache
   rich256 dari allowlist input yang sama (tanpa label gold) dan arm E42-family
   headline-only/rich256 terpisah, agar batas token128 tidak menyembunyikan
   hilangnya alasan visual. Cache baru dipublikasikan hanya sebagai dataset
   Kaggle privat untuk eksperimen sendiri, dengan metadata/hash dan ledger;
   gunakan private existing account tanpa pembelian/upgrade.
   Kontrol Qwen zero-shot: jalankan seluruh740 ID untuk tiga task pada input
   basic (citra+judul+supporting) dan rich (tambahan E01), revision8B/NF4 sama
   dengan QLoRA, tanpa LoRA/training. Smoke empat sampel lebih dahulu;
   full wall <=7.200detik, private, protocol/source/input/prediksi hash.
   Zero-shot tidak disebut OOF training. Rerun QLoRA input-basic wajib tetap
   terbuka sampai lima fold selesai dan diverifikasi; kontrol zero-shot saja
   tidak menutup R21.
   QLoRA basic dikontraskan dengan rich E14 pada resep/seed/fold dan epoch
   refit yang sama `[3,1,3,2,3]`, yang berasal dari pilihan inner rich historis
   (bukan outer-test). Tidak menjalankan pencarian epoch basic baru agar
   input menjadi intervensi utama; ini paired input ablation bersyarat pada
   resep yang dipilih pada rich, bukan optimasi independen basic berdasarkan
   Macro-F1. Pelaporan hasil baru tetap Macro-F1/akurasi/kappa. Worker turunan
   menghapus fitur E01 seluruhnya dari basic, mempertahankan source/protokol
   asli, private smoke8 training/4 test sebelum full740. Batas full9jam wall
   (<=18jam-GPU bila dua T4 dialokasikan); cek kuota sebelum submission,
   tanpa pembelian. Durasi historis menunjukkan pekerjaan ini berjam-jam;
   status R21 tetap terbuka sampai collector/verifier740 lulus.
7. Buat paket anotasi ganda acak150 dan audit kelas penampung60, rubrik/protokol XAI lima penilai, beserta importer yang menolak jawaban kosong/model sebagai bukti manusia. Jalankan perhitungan agreement hanya dari penilaian manusia nyata yang tersedia.
   XAI E42 memakai checkpoint outer fold untuk delapan ID acak seed20261101,
   encoder CLIP-L14 berhash, attention rollout Abnar–Zuidema (class-agnostic,
   tidak disebut Grad-CAM), LIME teks dengan visual tetap, dan uji deletion
   top20% versus random pada skor kelas model yang sama. Nilai ini eksploratif
   delapan sampel, bukan penilaian lima manusia atau faithfulness seluruh740.
   Peta real/kontrol random disiapkan dalam paket teracak dengan kunci privat
   koordinator, bukan melabelkan kontrol sebagai penjelasan model nyata.
8. Buat tiga notebook baru, tabel/grafik, tanggapan 28 revisi, narasi metode/hasil/keterbatasan/etika, referensi primer dan paket reproduksi dengan dependency terkunci.
9. Uji Run all dan validator dari ekstraksi dan environment terpisah, browser HTML offline, checksum/CRC/manifest; catat Colab/Windows sesuai pengujian aktual. Buat paket mudah diteruskan dengan daftar pekerjaan manusia/komputasi yang masih terbuka, tanpa label semua revisi selesai bila belum ada bukti.

## Risiko & Asumsi
- Tidak ditemukan bukti dua anotator atau lima penilai dari nama file awal; pencarian isi/arsip tetap dilakukan sebelum menyimpulkan.
- Generator E01 membaca CSV berlabel ke proses, tetapi prompt hanya mengambil gambar/judul/supporting/codebook. Ini tidak memenuhi tuntutan literal CSV label tidak pernah diakses; bedakan process isolation dari tidak mengalirnya gold ke prompt.
- Pembanding SigLIP/DINO dan metode stacking tidak memenuhi identitas model utama; input VLM-derived harus diberi konteks terpisah.
- E42 memakai tail IndoBERT trainable dan class weights; E48 LinearSVC bukan ablation head-only yang setara. Tidak menamai rerun frozen baseline sebagai ablation E42.
- Hasil manusia tidak dapat diciptakan; bila tidak ada, paket berisi instrumen/sampel dan status menunggu manusia. Pengiriman ke Joy tidak dilakukan otomatis; user meminta delivery kepada user untuk diteruskan.

## Verifikasi
- Semua28 nomor terpetakan, setiap status Selesai memiliki bukti serta uji; status lain menyebut kebutuhan tersisa.
- Skor canonical dihitung ulang dari prediksi asli dan sejalan dengan penghitungan independen; kelas/ID/split tidak dimutasi.
- Seed/bootstrap, batas sumber daya dan kontrak eksperimen tersimpan sebelum output training baru.
- Tiga notebook Run all tanpa training tersembunyi dan tanpa absolute workspace path; seluruh input paket berhash dan valid setelah ekstraksi.
- Source/data/hasil/ZIP lama tidak ditimpa. Changelog dicatat setelah perubahan nyata selesai.

## Catatan eksekusi lanjutan
- Smoke QLoRA basic v2 gagal sebelum training karena definisi CrossEntropyLoss terhapus saat derivasi; seluruh source/protokol/log gagal diarsipkan. Perbaikan definisi loss dan smoke versi berikutnya diperlukan sebelum full.
- User mengizinkan upload kandidat B01 dan tiga notebook ke Colab. Percobaan upload tertahan izin file URL ekstensi; menunggu pengguna mengaktifkan izin, tanpa mengubah akses browser diam-diam.
- Lampiran model E42 dibuat terpisah dari ZIP analisis: lima checkpoint, cache front/tail, 740 citra, source/manifest pin dan replay CPU yang hanya menulis laporan QA baru. Uji replay 740 prediksi dilakukan dari ekstraksi lampiran; tidak menjalankan ulang grid historis atau mengubah hasil lama. Bobot pretrained publik tidak dibundel; pin/hash dan langkah unduh dicantumkan untuk regenerasi XAI.
