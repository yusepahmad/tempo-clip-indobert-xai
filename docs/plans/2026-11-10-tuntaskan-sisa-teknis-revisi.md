# Tuntaskan Sisa Teknis Revisi

**Tanggal:** 2026-11-10
**Status:** done

## Tujuan
Menyelesaikan seluruh pekerjaan revisi yang dapat dilakukan secara teknis tanpa menggantikan anotasi, penilaian, keputusan metodologis, atau bukti historis manusia.

## Ruang Lingkup
- Memeriksa status live R21 Qwen citra+judul literal pada Kaggle/server `.31`; mengoleksi dan memvalidasi hasil hanya jika job benar-benar complete.
- Mengaudit dan menjalankan verifikasi teknis paket R32 yang dapat dilakukan di lingkungan tersedia, tanpa mengklaim kelulusan Colab asli bila tidak dijalankan di Colab.
- Memvalidasi integritas dan kelengkapan template/paket R22, R23/R6, R31, dan R34/R9 untuk handoff manusia.
- Memperbarui status, tracker, dokumentasi, dan changelog hanya berdasarkan bukti aktual.
- Tidak mengisi skor/anotasi manusia, tidak membuat timestamp/riwayat korpus, dan tidak mengambil keputusan pembimbing.

## Langkah
1. Audit source manager/collector R21, credential yang tersedia, status job Kaggle, dan artefak pada server `.31`.
2. Jika R21 complete, tarik hasil, jalankan collector/validasi ID-fold-probabilitas, dan regenerasi keluaran terkait; jika belum, dokumentasikan status live dan blocker aktual tanpa resubmit duplikat.
3. Audit pasangan notebook/ZIP R32 dan jalankan validasi lokal yang relevan; pisahkan bukti lokal dari bukti Colab asli.
4. Verifikasi ZIP manusia, manifest, checksum, jumlah item, kolom kosong, dan pemisahan kunci kontrol.
5. Susun laporan status teknis akhir dan daftar pekerjaan yang tetap menunggu manusia.
6. Jalankan tes/verifikasi proporsional, catat perubahan di `CHANGELOG.md`, lalu perbarui status plan.

## Risiko & Asumsi
- Akses Kaggle mungkin hanya tersedia pada server `.31`; job lama tidak boleh disubmit ulang tanpa bukti gagal.
- Driver GPU server `.31` sebelumnya tidak tersedia, tetapi koleksi hasil Kaggle tidak memerlukan GPU lokal.
- Bukti Linux/server tidak boleh dinamai bukti `colab_verified=true`.
- Paket R4 bersifat immutable; keluaran baru dibuat sebagai addendum/status baru, bukan menimpa snapshot R4.

## Verifikasi
- Status Kaggle diperoleh dari pengamatan live atau dinyatakan tidak dapat diakses dengan bukti command/log.
- Hasil R21, bila dikoleksi, lulus pemeriksaan 740 ID, lima fold, truth, probabilitas, dan provenance.
- Paket R32 dan paket manusia lulus checksum/struktur/jumlah item yang diharapkan.
- Tidak ada kolom manusia yang diisi otomatis dan tidak ada status revisi dinaikkan tanpa bukti.

## Hasil
- R21 literal berhasil dikoleksi dari job Kaggle `COMPLETE` dan lulus collector 740 ID/lima fold/probabilitas/audit prompt; empat tes source R21 lulus.
- Addendum terpisah dibuat pada `delivery/ADDENDUM_R21_LITERAL_20261110/` dengan prediksi, hasil, metrik, provenance, dan manifest; R4 tidak ditimpa.
- Delapan ZIP manusia lulus CRC/checksum; ZIP R32 lulus CRC dan notebook lulus schema/compile.
- Validator R4 lulus 2.431 hash, 234 metrik, 78 sumber, dan 28 baris revisi; status manusia/Colab tidak dinaikkan.
