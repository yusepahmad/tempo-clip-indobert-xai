# Perbaikan struktur textarea HTML

**Tanggal:** 2026-10-06
**Status:** done

## Tujuan
Memulihkan panel input/preview/hasil setelah konversi input menjadi textarea menghasilkan tag self-closing yang tidak valid di browser.

## Ruang Lingkup
`02_web_demo/index.html`, `01_notebook/test_ui_html5.py`, parser html5lib pada venv untuk verifikasi, pemeriksaan parsing HTML5, plan/changelog root/paket. Model/data tidak diubah.

## Langkah
1. Ganti textarea self-closing dengan pasangan tag pembuka/penutup eksplisit.
2. Periksa struktur menggunakan parser HTML5 sesuai perilaku browser, termasuk pemisahan Batch/Panduan dan posisi workspace.
3. Jalankan regresi UI/sintaks/HTTP dan catat hasil.

## Risiko & Asumsi
Parser HTML biasa sebelumnya menerima bentuk self-closing; HTML5 memperlakukan textarea sebagai elemen teks, sehingga kontrol berikutnya bisa tertelan. Validasi harus memakai aturan HTML5.

## Verifikasi
Tiga textarea memiliki penutup eksplisit, seluruh ID tetap ditemukan parser HTML5, Batch bukan anak input, workspace/script tetap utuh, regresi dan HTTP lulus.

## Hasil
Dua textarea self-closing diganti penutup eksplisit. Empat uji HTML5 lulus, termasuk fixture bentuk rusak yang kehilangan workspace. Input/task/tombol/workspace dan Batch/Panduan kembali terpisah. Regresi loading/state/navigasi, sintaks dan HTML HTTP lulus. html5lib 1.1 dipasang pada venv sebagai alat verifikasi, bukan perubahan runtime model. Visual browser belum tersedia.
