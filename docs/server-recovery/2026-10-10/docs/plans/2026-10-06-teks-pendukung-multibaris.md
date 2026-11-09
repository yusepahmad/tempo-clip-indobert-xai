# Teks pendukung multibaris

**Tanggal:** 2026-10-06
**Status:** done

## Tujuan
Memudahkan pembacaan teks pendukung panjang sesuai arahan user: textarea beberapa baris dan scroll vertikal bila diperlukan.

## Ruang Lingkup
`02_web_demo/index.html`, plan dan changelog root/paket. Backend/model tidak diubah.

## Langkah
1. Ganti input teks pendukung dataset/unggahan dengan textarea yang lebih tinggi dan dapat diperbesar.
2. Izinkan halaman analisis menggulir vertikal; pertahankan tab hasil dan panel terpisah.
3. Verifikasi ID/value/handler tetap kompatibel, sintaks/regresi dan HTTP.

## Risiko & Asumsi
Scroll ke bawah kini diizinkan sesuai koreksi user. Kolom tidak memotong teks dan tetap memakai ID lama.

## Verifikasi
Textarea dua mode, label/ID tetap, regresi JS dan respons HTTP lulus.

## Hasil
Teks pendukung dua mode menjadi textarea 5 baris, tinggi minimal 125px, dapat diperbesar vertikal. Scroll halaman vertikal diizinkan; tab tetap tersedia. Pemeriksaan textarea/ID/HTTP/sintaks serta regresi loading/state/navigasi lulus. Visual browser belum tersedia.
