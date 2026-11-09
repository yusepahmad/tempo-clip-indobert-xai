# Keputusan Penutupan R22, R23/R6, dan R31

**Tanggal keputusan:** 10 November 2026  
**Keputusan:** selesai dengan pendekatan konservatif; snapshot R4 dan seluruh label kanonik dipertahankan.

## R22 — provenance deskripsi

Review manusia lengkap pada 20 contoh menemukan 0/20 `sumber_visual` yang memuat kode Task 2. Pipeline baru juga membatasi input ke allowlist tanpa label dan menyimpan generator, prompt, model, serta hash. R22 ditutup sebagai verifikasi kepatuhan pipeline dan audit sampel.

Batas klaim: bukti ini tidak menciptakan timestamp atau isolasi proses historis yang memang tidak tersedia. Naskah harus menyatakan verifikasi prospektif dan audit manusia, bukan mengklaim rekonstruksi runtime lama.

## R23/R6 — kesepakatan antaranotator dan riwayat korpus

Dua anotator independen telah mengisi 150 sampel. Cohen's kappa Task 1/2/3 adalah 0,5721/0,9498/0,9430 dengan 56/6/7 disagreement. Seluruh disagreement dipertahankan pada tabel audit.

Keputusan adjudikasi konservatif: label kanonik dataset tetap menjadi label final untuk semua item disagreement. Tidak ada label anotator A/B yang menimpa gold. Alasan umum penyusutan korpus telah tercatat sebagai kualitas citra buruk; daftar eksklusi historis per ID tidak tersedia dan dinyatakan sebagai keterbatasan, bukan direka. Dengan dua anotasi, kappa, tabel disagreement, keputusan adjudikasi, dan pernyataan keterbatasan tersebut, R23/R6 ditutup.

## R31 — audit kelas penampung

Audit 60/60 lengkap menghasilkan 41 usulan perubahan: 26/30 untuk Task 2 `LAINNYA` dan 15/30 untuk Task 3 `multiple_or_other`. Keputusan konservatif: usulan disimpan sebagai analisis sensitivitas/rekomendasi codebook mendatang dan tidak diterapkan pada gold versi penelitian ini.

Karena gold/codebook tidak diubah, eksperimen utama tidak perlu dijalankan ulang. Pelaporan tetap memisahkan Task 2 domain sumber dari deteksi metafora. R31 ditutup sebagai audit sensitivitas tanpa relabeling.

## Integritas

- Anotasi mentah, gold, prediksi, model, metrik, dan snapshot R4 tidak diubah.
- Bukti numerik tersedia di `delivery/ADDENDUM_HASIL_MANUSIA_20261110/`.
- Setelah keputusan ini, revisi yang masih terbuka hanya R8, R32, dan R34/R9.
