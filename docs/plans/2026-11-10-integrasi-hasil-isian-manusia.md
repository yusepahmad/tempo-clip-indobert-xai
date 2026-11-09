# Integrasi Hasil Isian Manusia

**Tanggal:** 2026-11-10
**Status:** done

## Tujuan
Memvalidasi hasil manusia pada `HASIL_ISIAN/`, menghitung agreement dan ringkasan yang sah, lalu mengintegrasikan bukti R22, R23/R6, R31, dan R34/R9 ke addendum revisi tanpa mengubah snapshot R4.

## Ruang Lingkup
- R22 review manusia 20 contoh.
- R23/R6 dua anotasi independen dan Cohen’s kappa per task.
- R31 adjudikasi 60 sampul dan ringkasan subgroup/usulan label.
- R34/R9 lima penilai XAI, validasi 48 skor per penilai, ICC/agreement dan perbandingan kontrol.
- Addendum hasil manusia, tracker/status, changelog, dan push GitHub setelah verifikasi.
- Tidak mengubah template asli, gold, checkpoint, prediksi model, atau paket R4 immutable.

## Langkah
1. Ekstrak ZIP ke working directory terpisah dan inventarisasi file, manifest, ID, header, serta checksum.
2. Cocokkan setiap isian terhadap template canonical: jumlah item, urutan/ID, kode kelas, rater ID, dimensi, rentang nilai, dan kelengkapan.
3. Hitung Cohen’s kappa R23 per task serta tabel disagreement tanpa menimpa anotasi mentah.
4. Ringkas R22 dan R31 berdasarkan isian aktual, termasuk item bermasalah/label usulan.
5. Hitung ICC dan statistik XAI per dimensi/metode/kontrol; pertahankan blind-key dan batas interpretasi.
6. Buat addendum hasil manusia dengan salinan input, keluaran analisis, provenance, dan manifest.
7. Perbarui tracker/status/changelog hanya untuk butir yang benar-benar memenuhi kriteria.
8. Jalankan verifikasi akhir dan push commit fast-forward ke GitHub.

## Risiko & Asumsi
- Nama “sudah dikerjakan” belum dianggap bukti lengkap sebelum seluruh kontrak CSV lulus.
- Identitas pribadi/registrasi tetap privat dan tidak dipush bila mengandung PII; keluaran publik memakai kode rater.
- Agreement rendah tetap dilaporkan apa adanya dan tidak diubah menjadi status berhasil secara substantif.
- Bukti Colab R32 dan dokumen Agustus R8 berada di luar empat kelompok yang ditemukan dan tetap terbuka kecuali ditemukan bukti tambahan.

## Verifikasi
- Semua input manusia lolos validasi jumlah, ID, header, kode, dan rentang.
- Perhitungan agreement dapat direproduksi dari salinan input yang diarsipkan.
- Tidak ada kolom kosong wajib atau skor/anotasi yang dibuat agent.
- Addendum memiliki manifest SHA-256 dan R4 tetap lulus validator.

## Hasil
- R22 20/20, R23 dua anotator × 150, dan R31 60/60 lulus kontrak template/ID/header/kode/rentang/kelengkapan.
- Cohen’s κ R23 Task 1/2/3 adalah 0,5721/0,9498/0,9430; disagreement mentah dipertahankan terpisah.
- R31 menghasilkan 41/60 usulan perubahan label; gold tidak diubah otomatis.
- R34/R9 gagal syarat independensi: seluruh skor dan alasan lima rater identik; ICC sengaja tidak dilaporkan dan revisi tetap terbuka.
- Reproduksi output identik pada run kedua, lima tes `human_agreement` lulus, manifest addendum lulus, dan validator R4 tetap lulus 2.431 hash.
- Push GitHub ditunda sampai hasil R34 independen diperbaiki atau user meminta audit parsial ini dipublikasikan.
