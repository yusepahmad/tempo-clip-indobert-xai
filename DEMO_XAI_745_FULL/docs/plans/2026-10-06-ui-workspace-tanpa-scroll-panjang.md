# Workspace UI tanpa scroll halaman panjang

**Tanggal:** 2026-10-06
**Status:** done

## Tujuan
Memusatkan penggunaan dalam satu workspace layar desktop; hasil diakses melalui tab, batch/panduan lewat navigasi tampilan.

## Ruang Lingkup
`02_web_demo/index.html`, `01_notebook/test_workspace_ui.js`, bukti verifikasi UI, plan dan changelog root/paket. Backend/model/data dan ZIP review lama tidak diubah.

## Langkah
1. Ubah Analisis/Batch/Panduan menjadi tampilan bergantian, dengan navigasi hash dan status aktif.
2. Kelompokkan hasil ke tab Ringkasan/Visual/Teks/Sumber/Verifikasi; hilangkan auto-scroll hasil.
3. Batasi workspace ke tinggi viewport desktop, kecilkan preview/form dan sediakan overflow lokal untuk konten panjang. Layar kecil tetap adaptif tanpa memotong akses.
4. Verifikasi ID/control tetap, tab/navigasi/keyboard/state, sintaks dan endpoint; catat keterbatasan preview browser.

## Risiko & Asumsi
Konten panjang tetap memerlukan scroll di dalam panel; tidak boleh dipotong. Desktop memakai workspace tetap, layar ponsel tidak dipaksa memenuhi layout desktop. Browser CUA belum tersedia pada sesi sebelumnya; verifikasi visual hanya diklaim bila tersedia.

## Verifikasi
Seluruh ID/handler lama utuh, tepat satu view dan tab aktif, atribut aksesibilitas sesuai, auto-scroll dihapus, regresi JS dan HTTP lulus.

## Hasil
Tiga view navigasi dan lima tab hasil diterapkan. Desktop memakai tinggi viewport dengan overflow lokal bila detail panjang; mobile tetap adaptif. Preview/form dipadatkan, tabel ringkasan tiga kolom, anotator tersedia pada tab Verifikasi. Scroll otomatis hasil dihapus. Uji navigasi hash/tab/keyboard/fokus, regresi state/respons lama, sintaks, 63 ID unik dan HTTP lulus. Review visual browser belum dijalankan karena akses browser tidak tersedia.
