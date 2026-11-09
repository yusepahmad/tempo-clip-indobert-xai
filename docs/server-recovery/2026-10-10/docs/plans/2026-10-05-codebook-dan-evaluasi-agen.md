# Codebook operasional dan evaluasi agen

**Tanggal:** 2026-10-05
**Status:** done

## Tujuan
Menyusun definisi25kelas atas instruksi user, tabel pemeriksaan kasus ambigu/revisi, dan tiga tinjauan agen atas demo.

## Ruang Lingkup
- Codebook baru JSON/Markdown, katalog UI, tabel pemeriksaan, laporan evaluasi agen, delivery dan CHANGELOG.
- Dataset, label, training/bobot tidak diubah. Definisi baru tidak diklaim sebagai codebook asli atau bukti validasi label. Evaluasi agen tidak diklaim sebagai uji manusia.

## Langkah
1. Susun definisi, kriteria masuk dan pembeda untuk25kelas, contoh berbasis anotasi dataset dengan alasan usulan.
2. Integrasikan katalog dan tandai provenance draft operasional.
3. Siapkan tabel kasus untuk headline/teks pendukung, sumber gambar dan keputusan pemeriksaan.
4. Tiga sub-agent meninjau kejelasan/task, alur input/OCR dan bukti/batch; catat metode serta batasnya.
5. Verifikasi cakupan25kelas, hasil tinjauan dan dokumentasikan perubahan.

## Risiko & Asumsi
- User menyatakan codebook resmi tidak ada dan mengizinkan penyusunan definisi. Definisi operasional baru tetap perlu konsistensi dengan anotasi historis.
- Tinjauan agen dapat menemukan masalah tetapi tidak menggantikan pengalaman pengguna nyata.

## Verifikasi
Seluruh25label memiliki definisi/kriteria/pembeda; ID contoh cocok dataset, tiga tinjauan agen dicatat tanpa klaim uji manusia, tabel memuat kasus ambigu dan kolom keputusan.

## Hasil
25kelas dan contoh asli lulus pemeriksaan; katalog API lengkap. Tabel13kasus dan tiga tinjauan agen tersedia. Temuan peta/narasi, klaim zona, skor, reviewbatch/counterkandidat/resume diperbaiki. Regresi Python3test, JavaScript, HTTPtiga task/batch/ekspor dan previewuploadHTTP200 lulus. Dataset/bobot tidak berubah; keputusan semantik ambigu dan penerimaan pengguna manusia tidak diklaim selesai.
