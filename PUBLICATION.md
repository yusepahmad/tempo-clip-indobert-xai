# Client delivery

Repository ini merupakan ekspor source dan hasil analisis yang telah disanitasi untuk client.

## Isi

- Source penelitian dan web demo.
- Dataset kerja, fold, prediksi, metrik, notebook, dan bukti revisi yang diizinkan.
- Paket analisis utama beserta manifest SHA-256 yang dibangun ulang setelah sanitasi.
- Addendum R21 dan hasil manusia yang sudah divalidasi.

## Sanitasi

Ekspor tidak memuat nama pribadi, username akun pribadi, alamat email pribadi, path home personal asli, credential, token, kunci kontrol, cache environment, atau identitas partisipan. Metadata job eksternal memakai placeholder netral. Riwayat Git client menggunakan author netral dan tidak mempertahankan commit lama.

## Verifikasi

Gunakan instruksi pada `README.md`. Laporan sanitasi tersedia pada `SANITIZATION_REPORT.md`. Manifest paket utama berada di `delivery/HASIL_REVISI_JOY_20261108_R4/MANIFEST_SHA256.json`.

Nilai penelitian dan kesimpulan ilmiah dipertahankan. Sanitasi hanya mengubah metadata identitas, path operasional, URL akun, dan dokumentasi distribusi.
