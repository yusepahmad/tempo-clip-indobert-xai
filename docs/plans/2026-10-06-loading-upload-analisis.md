# Loading upload dan analisis

**Tanggal:** 2026-10-06
**Status:** done

## Tujuan
Perlihatkan bahwa upload/OCR dan analisis sedang diproses dengan spinner dan pesan yang jelas.

## Ruang Lingkup
`02_web_demo/index.html`, `01_notebook/test_loading_ui.js`, regresi UI, bukti verifikasi, plan/changelog. Backend/model tidak diubah.

## Langkah
1. Tambahkan indikator loading besar pada workspace dan indikator inline saat upload/OCR.
2. Selaraskan tombol, aria-busy dan status OCR/analisis; bersihkan loading pada selesai/gagal/pembatalan/pergantian gambar.
3. Verifikasi loading dan respons usang dengan regresi serta HTTP.

## Risiko & Asumsi
Endpoint tidak mengirim progres tahap internal; spinner bersifat indeterminate, tidak mengarang persentase/tahapan selesai. Respons OCR lama tidak boleh mengakhiri loading gambar baru. Browser visual belum tersedia.

## Verifikasi
Status loading terlihat di DOM, lifecycle dan respons usang lulus, sintaks/HTTP sesuai source.

## Hasil
Overlay/spinner indeterminate dan pesan berbeda untuk OCR/analisis, loading OCR inline, tombol busy dan aria-busy diterapkan. Analisis menunggu OCR selesai; respons OCR usang tidak mematikan loading permintaan baru. Regresi selesai/gagal/respons usang, state/tab/preview, sintaks/DOM/HTTP lulus. Preview visual browser belum tersedia.
