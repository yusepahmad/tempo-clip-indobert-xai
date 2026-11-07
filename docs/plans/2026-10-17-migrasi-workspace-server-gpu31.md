# Migrasi Workspace ke Server GPU .31

**Tanggal:** 2026-10-17
**Status:** in-progress

## Tujuan
Memindahkan seluruh project dari komputer lokal ke
`yusep@10.12.1.31:/home/yusep/workspace/learn` tanpa kehilangan file,
termasuk file tersembunyi dan artefak eksperimen.

## Ruang Lingkup
- Sumber: `/home/yusep/Desktop/Freelance/TA-1-sekripsi-tempo-joy-eau-dia-final/`.
- Tujuan: `yusep@10.12.1.31:/home/yusep/workspace/learn/`.
- Seluruh isi project termasuk `.claude`, source, data, model, dokumentasi,
  delivery, dan environment yang berada di dalam project.
- Tidak menimpa data tujuan yang tidak berasal dari project ini.

## Langkah
1. Periksa koneksi, isi tujuan, kapasitas disk, dan ukuran sumber.
2. Catat fingerprint jumlah file/byte dan checksum artefak penting.
3. Salin seluruh isi ke direktori staging di server menggunakan transfer yang
   dapat dilanjutkan dan mempertahankan metadata.
4. Verifikasi jumlah file, ukuran, serta checksum sumber dan staging.
5. Jika tujuan kosong, jadikan staging sebagai `/home/yusep/workspace/learn`;
   jika tidak kosong, hentikan sebelum merge/overwrite.
6. Catat migrasi pada changelog di salinan server.
7. Hapus sumber lokal hanya setelah verifikasi penuh; bila penghapusan lokal
   tidak aman atau terputus, laporkan bahwa operasi baru berupa salinan.

## Risiko & Asumsi
- Transfer berukuran besar dapat terputus; gunakan mekanisme resumable.
- Environment Python dapat berisi symlink/path absolut dan mungkin perlu dibuat
  ulang di server walaupun seluruh file dipindahkan.
- Server harus memiliki ruang disk dan izin tulis yang cukup.
- Kata “pindahkan” berarti sumber lokal boleh dihapus setelah salinan server
  terbukti lengkap.

## Verifikasi
- Seluruh path relatif sumber terdapat pada tujuan.
- Jumlah file, total byte reguler, dan checksum manifest sama.
- Artefak penting OCR/model/dokumentasi dapat dibaca di server.
- Sumber lokal baru dihapus setelah seluruh pemeriksaan lulus.
