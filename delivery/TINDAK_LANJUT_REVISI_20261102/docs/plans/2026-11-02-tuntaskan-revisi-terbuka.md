# Tindak Lanjut Sembilan Revisi Terbuka

**Tanggal:** 2026-11-02
**Status:** in-progress

## Tujuan
Mengerjakan bagian teknis yang masih memungkinkan sekarang, memeriksa peluang selesai pada 2 November 2026 WIB, dan memberi estimasi berbasis log serta daftar kebutuhan manusia yang belum tersedia.

## Ruang Lingkup
- Source dan pengujian baru/terkait pada `DEMO_XAI_745_FULL/01_notebook/revisi_ii/` untuk R21, penguatan input provenance R22, import/validasi bukti manusia dan uji reproduksi R32.
- Bukti/job baru pada `DEMO_XAI_745_FULL/04_hasil_eksperimen/revisi_ii/`, catatan tindak lanjut pada `docs/revisi-ii/`, serta paket tambahan berversi `delivery/TINDAK_LANJUT_REVISI_20261102/`.
- Plan ini dan `CHANGELOG.md`; R3_FULL beserta ZIP-nya dipertahankan.
- Tidak mengganti anotator/penilai dengan AI, membuat riwayat/timestamp historis, mengubah label, atau menyatakan butir selesai tanpa bukti.

## Langkah
1. Cocokkan sembilan status terbuka dengan permintaan PDF asli, sumber/log terakhir, dan informasi pengguna (belum punya dokumen Agustus maupun hasil anotator/penilai).
2. Periksa status smoke/full QLoRA basic dan kapasitas/kuota melalui akses tersedia. Hitung perkiraan dari waktu per epoch/inferensi yang benar-benar tercatat; ajukan full hanya setelah smoke/hash/kontrak dan anggaran komputasi terverifikasi sesuai plan induk, privat, tanpa pembelian dan tanpa duplikasi.
3. Perkuat R22 dengan ekspor input allowlist tanpa label dan kontrak generator versi baru yang gagal bila label/kolom terlarang masuk. Bukti ini tidak diberlakukan surut terhadap runtime historis.
4. Siapkan jalur uji Colab yang mengeluarkan laporan nyata serta perhitungan agreement/adjudikasi yang siap digunakan ketika manusia mengisi data; uji lokal menggunakan fixture/hasil paket yang sesuai, tanpa mengisi rating manusia.
5. Bangun paket tindak lanjut berisi source, bukti hasil aktual, instrumen/panduan dan matriks estimasi/tanggung jawab. Koleksi hasil eksperimen bila selesai dalam sesi; bila masih berjalan, catat status dan estimasi bersyarat.
6. Verifikasi artefak baru, isolasi data, kontrak ID/label/fold, status runtime, checksum paket; catat perubahan aktual ke changelog.

## Risiko & Asumsi
- Sembilan ID terdiri dari kebutuhan bertumpang tindih: R23/R6 serta R34/R9.
- Pengguna mengonfirmasi belum punya dokumen Agustus, dua set anotasi, atau lima hasil penilai. Penghitungan agreement menunggu data nyata.
- Sisa waktu hari ini dihitung memakai Asia/Jakarta; durasi training tergantung antrean, GPU dan kuota. Estimasi bukan janji hasil/mutu model.
- Job full mengikuti batas plan induk 9 jam wall / maksimum 18 jam-GPU bila dua T4. Tidak ada pembelian/upgrade; ketidakjelasan kuota harus diselesaikan sebelum submission.
- Browser/Colab harus benar-benar bisa diakses untuk mengklaim Run all Colab. Kelulusan Linux tidak menutup bukti Colab.
- Timestamp asli E01 dan isolasi runtime historis tidak dapat direkonstruksi dari salinan recovery; provenance baru diberi versi/tanggal baru.

## Verifikasi
- Daftar seluruh sembilan ID menyebut apa yang sudah tersedia, pekerjaan tersisa, estimasi, dependensi dan siapa yang mengerjakan.
- Eksperimen GPU memiliki ledger anti-duplikasi, source/protocol hash, guard waktu dan pemeriksaan smoke yang lulus sebelum full; hasil tidak dipromosikan dari empat sampel menjadi 740.
- Input provenance baru hanya empat field input yang diizinkan, tepat 740 ID unik, gambar berhash dan tanpa label dalam manifest input.
- Instrumen manusia tetap kosong; kalkulator menolak data kosong/model yang menyamar sebagai penilaian manusia.
- Hasil Colab tetap Not Evaluated kecuali ada laporan runtime Colab nyata. Paket baru dan ZIP lama tetap terjaga.

## Hasil aktual pada sesi ini
- Sembilan ID dikonfirmasi tetap terbuka; pengguna belum mempunyai dokumen Agustus, anotasi ganda atau lima hasil penilai. Matriks estimasi mengelompokkan sembilan ID menjadi tujuh pekerjaan karena R23/R6 dan R34/R9 beririsan.
- R21: kuota GPU diperiksa melalui CLI, tersisa 28,18 jam. Smoke v3 COMPLETE/verified, source cocok `88a80feafa508a260c7f03c3c2660ee5e2a59acc77dc04fceb9d5ac000ee5e4a`. Full privat v1 berhasil dikirim, status RUNNING pada 2 November sore WIB. Batas 9 jam wall/18 jam-GPU dipertahankan; tidak ada pembelian atau submission ganda.
- Estimasi awal R21 5–9 jam sejak mulai berdasarkan 19,33 detik/8 contoh training smoke, 592 contoh × total 12 fold-epoch, ditambah load/preprocessing/inferensi. Kolektor berbatas 10 jam memantau setiap lima menit, tanpa resubmit, dan hanya memublikasikan hasil sesudah COMPLETE serta verifikasi 740 ID/fold/truth/probabilitas/split/input-audit/hash. Hasil akan ditulis ke `delivery/R21_HASIL_FULL_20261102/` bila lulus; belum tersedia saat snapshot.
- Tabel R21 dua dimensi dan zero-shot disiapkan: 18 baris, 15 berangka aktual dan 3 QLoRA basic tetap Not Evaluated. CI kappa bootstrap 2.000 disertakan; perbedaan basic128/rich256 dan resep inner rich dijelaskan, bukan diklaim efek input murni.
- R22: 740 input empat kolom allowlist, 742 file berhash, generator asli dan wrapper/probe pembatas baca disiapkan. Uji proses Python memblokir CSV gold asli. Tidak menjalankan pembangkitan fitur baru, tidak mengubah fitur lama, dan tidak mengklaim sandbox OS maupun isolasi/timestamp runtime historis.
- R32: paket analisis portabel 212.288.063 byte dan COLAB_RUN_ALL.ipynb dibuat. Ekstraksi pada venv baru (66 dependensi) lulus Run all tiga notebook, 1.791 hash, 231 metrik dan audit 162 bukti. Colab tetap Not Evaluated karena inventaris browser kosong.
- Paket manusia delapan ZIP diverifikasi checksum/CRC, tanpa kunci privat dan tanpa isian manusia. Kalkulator XAI diperkuat untuk menolak item/rater/dimensi hilang dan skor Likert pecahan bila memakai expected-template.
- Enam tes tindak lanjut dan lima tes agreement lulus. Fixture publikasi menggunakan comparator historis hanya di direktori temporer pengujian, tidak menjadi hasil training penelitian.
- Paket tindak lanjut, laporan QA, source dan estimasi disiapkan pada `delivery/TINDAK_LANJUT_REVISI_20261102/`. R3_FULL tidak diubah. Plan tetap in-progress karena job R21 dan kebutuhan bukti eksternal belum selesai.
