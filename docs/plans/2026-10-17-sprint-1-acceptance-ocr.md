# Sprint 1 — Acceptance Aplikasi dan OCR

**Tanggal:** 2026-10-17
**Status:** in-progress

## Tujuan
Membuat evaluasi OCR yang dapat diaudit dan tidak memakai ulang set diagnosis,
memisahkan kualitas headline dari teks pendukung, serta menyiapkan acceptance
aplikasi yang membedakan bukti lokal dari validasi eksternal.

## Ruang Lingkup
- Membekukan sampel evaluasi OCR independen dari 740 sampul sebelum menjalankan
  OCR, dengan mengecualikan seluruh sampel evaluasi/diagnosis terdahulu.
- Menjalankan OCR produksi pada set beku dan menghitung metrik headline.
- Mengevaluasi teks pendukung hanya bila tersedia ground truth yang sah; bila
  tidak, mencatatnya sebagai gap data dan tidak membuat label sendiri.
- Menyusun paket review keputusan manusia untuk kasus ambigu dan gambar dosen.
- Menjalankan regresi aplikasi yang relevan setelah evaluasi.
- Menilai kesiapan clean install Windows, uji pengguna manusia, dan browser
  selain Chromium berdasarkan bukti yang tersedia tanpa mengklaim pengujian
  yang tidak dilakukan.
- Tidak mengubah dataset, ground truth, selector OCR produksi, atau model untuk
  mengejar angka acceptance pada set evaluasi.

## Langkah
1. Audit skema dataset, manifest OCR lama, dan seluruh ID yang pernah digunakan
   untuk diagnosis/tuning.
2. Buat aturan sampling deterministik dan manifest set independen yang hanya
   memuat ID/ground truth sebelum OCR dijalankan.
3. Jalankan OCR produksi pada set beku, simpan raw output, versi/config, durasi,
   dan hash input.
4. Hitung exact match serta metrik token/karakter untuk headline; pisahkan
   evaluasi supporting text berdasarkan ketersediaan ground truth.
5. Susun tabel kasus gagal untuk keputusan manusia tanpa mengubah label.
6. Jalankan regresi terkait dan dokumentasikan gate eksternal.
7. Perbarui roadmap, changelog, dan status plan sesuai hasil aktual.
8. Gunakan gabungan diagnosis lama 30 sampel dan development 60 sampel untuk
   menguji perbaikan selector secara offline dari blok OCR tersimpan; ukur
   regresi serta perbaikan exact match sebelum kandidat dikunci.
9. Setelah kandidat dikunci, jalankan tepat satu kali pada holdout final 80
   sampel dan nyatakan gate lulus hanya bila sedikitnya 64 headline cocok.

## Risiko & Asumsi
- EasyOCR dapat membutuhkan unduhan/cache model dan waktu CPU yang cukup lama.
- Kolom supporting text mungkin bukan transkripsi visual lengkap dan tidak sah
  sebagai ground truth OCR; kondisi ini harus dilaporkan apa adanya.
- Mesin Windows dan peserta manusia mungkin tidak tersedia pada workspace ini.
- Set disebut independen hanya terhadap diagnosis/tuning OCR yang teridentifikasi
  di workspace, bukan external dataset di luar 740 sampul.
- Pelonggaran penggabungan baris dapat menarik teaser ke headline; perubahan
  hanya diterima bila evaluasi 90 sampel development menunjukkan peningkatan
  bersih dan kasus regresinya diaudit.

## Keputusan Pengguna 17 Oktober 2026

Target **OCR headline exact match minimal 80% wajib tercapai**. Karena hasil
set 60 sampel sudah dilihat sebelum keputusan ini dan akan dipakai untuk
diagnosis, set tersebut direklasifikasi menjadi development set. Holdout final
baru wajib dibekukan sebelum perubahan selector berikutnya dan tidak boleh
dijalankan sampai kandidat OCR ditetapkan dari development data.

Audit kapasitas setelah mengecualikan 90 sampel pengembangan menemukan kelas
`other_issue` hanya menyisakan 8 sampel. Agar evaluasi tetap seimbang tanpa
menggunakan ulang data pengembangan, holdout final ditetapkan menjadi 80 sampel
(8 sampel × 10 kelas Task 1). Gate 80% berarti minimal 64 dari 80 headline
harus exact match.

## Verifikasi
- Manifest set evaluasi dibuat sebelum output OCR dan memiliki hash stabil.
- Tidak ada overlap dengan ID diagnosis/tuning terdahulu.
- Metrik dapat dihitung ulang dari raw prediction dan ground truth.
- Tidak ada perubahan pada ground truth atau selector produksi selama evaluasi.
- Gate yang tidak dapat diuji ditandai pending dengan kebutuhan yang konkret.

## Hasil Iterasi Kandidat 2

- Kandidat selector dikunci pada SHA-256
  `94bb5c5ef5fd38ae7480d51f435e6c80264e150f04fdfe8f03327747a21435db`.
- Development: 48/60 exact match (80,0%); 16/16 regresi unit OCR lulus.
- Holdout final: 60/80 exact match (75,0%), di bawah syarat 64/80.
- Kesimpulan: gate OCR belum lulus; plan tetap `in-progress`. Hasil holdout
  pertama dipertahankan dan tidak boleh ditimpa.
