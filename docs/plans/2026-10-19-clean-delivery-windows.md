# Clean Delivery Windows

**Tanggal:** 2026-10-19
**Status:** done

## Tujuan
Membuat satu ZIP Windows terbaru yang ringkas dan jelas untuk penerima.

## Ruang Lingkup
- Runtime web, dataset/fitur, gambar, manifest model, launcher dan setup Windows.
- Panduan singkat dan ringkasan hasil E11/E07 terbaru.
- Builder serta changelog root.
- Riwayat eksperimen, environment, cache, notebook pembanding dan dokumen lama
  dikeluarkan dari ZIP. Sumber workspace dan arsip historis tetap disimpan.

## Langkah
1. Pilih file berdasarkan dependensi runtime.
2. Buat panduan, ringkasan hasil, dan builder allowlist.
3. Bangun ZIP, verifikasi CRC/hash dan pemeriksaan delivery dari hasil ekstrak.
4. Catat hasil dan tutup plan.

## Risiko & Asumsi
- Clean install Windows tetap diuji pengguna.
- Data dan artefak ber-hash dipertahankan byte aslinya; CRLF hanya untuk launcher.
- Model aplikasi aktif berbeda dari kandidat penelitian E11.

## Verifikasi
CRC dan SHA-256 seluruh entry cocok; check_delivery.py lulus dari ekstraksi
paket; tidak ada file training, cache, credential, dan launcher Linux.

Hasil: ZIP 101.022.435 byte, 761 file. CRC, seluruh hash konten dan hash
provenance data runtime lulus. `check_delivery.py` dijalankan dari hasil ekstrak
dan lulus menggunakan environment verifikasi yang tersedia.
