# Delivery ZIP untuk Windows

**Tanggal:** 2026-10-17
**Status:** done

## Tujuan
Membuat paket delivery `tempo-final-release-v1-windows.zip` yang siap dipakai di Windows, berdasarkan konten yang sama dengan release Linux yang sudah terverifikasi.

## Ruang Lingkup
- File/modul yang tersentuh:
  - `delivery/final_release_20261017/build_bundle_windows.py` — script build baru
  - `delivery/final_release_20261017/tempo-final-release-v1-windows.zip` — output ZIP
  - `delivery/final_release_20261017/bundle_verification_windows.json` — laporan verifikasi
  - `CHANGELOG.md` — entry baru
- Yang eksplisit TIDAK disentuh:
  - Release Linux yang sudah ada (`tempo-final-release-v1-linux.zip`)
  - Source canonical di `DEMO_XAI_745_FULL/`
  - Dokumentasi sprint lama

## Langkah
1. Buat script `build_bundle_windows.py` yang:
   - Mengambil konten dari `DEMO_XAI_745_FULL/` yang sama (dari delivery/final_release_20261017/)
   - Mengonversi line endings file teks (.py, .md, .txt, .bat, .json, .csv, .html, .js, .css) ke CRLF untuk kompatibilitas Windows
   - Memastikan path separator di ZIP menggunakan forward slash (standar ZIP)
   - Membuat DELIVERY_MANIFEST_WINDOWS.json terpisah
   - Mengeksklusi file Linux-only (jalankan_linux.sh, requirements-lock-linux.txt, requirements-delivery-lock-linux.txt)
   - Security scan: tidak ada credentials/secrets
   - Verifikasi integritas ZIP (CRC + SHA-256)
2. Jalankan build script
3. Verifikasi output ZIP
4. Catat ke CHANGELOG.md

## Risiko & Asumsi
- Konten source identik dengan release Linux, hanya berbeda format line endings dan eksklusi file Linux-only
- File biner (gambar, model) tidak diubah line endings-nya
- setup_windows.bat dan jalankan_windows.bat sudah menggunakan CRLF di source

## Verifikasi
- ZIP CRC check lulus
- SHA-256 konten terverifikasi
- File teks menggunakan CRLF
- Tidak ada file Linux-only dalam paket
- Security scan tidak mendeteksi credentials
