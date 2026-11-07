# Delivery Update Windows 19 Oktober 2026

**Tanggal:** 2026-10-19
**Status:** done

## Tujuan
Membuat full release v2 Windows yang siap diserahkan dari snapshot terbaru 19
Oktober 2026, termasuk hasil dan kesimpulan MICRO-E07.

## Ruang Lingkup
- Source aplikasi, data delivery, kode eksperimen, hasil tervalidasi E02–E11,
  serta artefak smoke E07.
- Derived embeddings yang diperlukan untuk reproduksi eksperimen terbaru.
- `setup_windows.bat`, `jalankan_windows.bat`, dokumentasi, manifest, laporan
  verifikasi, dan checksum ZIP.
- Konversi seluruh file teks yang didukung ke CRLF.
- Tidak menyertakan skrip/lock Linux-only, `venv`, cache, job sementara,
  credential, ZIP lama, atau bytecode.

## Langkah
1. Buat builder Windows deterministik dari snapshot release v2.
2. Jalankan security scan dan konversi CRLF in-memory.
3. Bangun ZIP Windows dengan ZIP64.
4. Verifikasi CRC, hash setiap entry, file wajib Windows, dan ketiadaan file
   Linux-only.
5. Catat hasil aktual ke changelog dan tutup plan.

## Risiko & Asumsi
- Paket belum dapat membuktikan clean install pada mesin Windows dari host
  Linux; skrip Windows yang sama dengan delivery tervalidasi sebelumnya tetap
  disertakan.
- Model publik tidak dibundel dan diunduh saat setup/launch pertama.
- MICRO-E07 tetap diagnostic smoke 24 sampel dan bukan model delivery aktif.

## Verifikasi
- Checksum SHA-256 ZIP cocok.
- `ZipFile.testzip()` dan `unzip -t` tidak menemukan kerusakan.
- Semua hash entry cocok dengan manifest Windows.
- File teks sampel memakai CRLF; file Linux-only tidak ada; `.bat` utama ada.
