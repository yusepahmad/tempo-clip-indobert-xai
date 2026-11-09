# Release QA — Penelitian Lanjutan

**Tanggal:** 2026-10-18  
**Status:** in-progress

## Verifikasi lokal

Perintah:

```text
../venv/bin/python -m unittest test_audit_backend test_audit_frontend
test_batch_error_message test_mtl_delivery test_narasi_ringkasan
test_ocr_urutan -v
```

Hasil backend: 64 test ditemukan; 63 lulus. Satu modul frontend awalnya tidak
dapat diimpor karena Playwright belum tersedia. Setelah Playwright 1.64 dan
Chromium headless dipasang, server dijalankan pada `127.0.0.1:7860` dan seluruh
**13/13 test frontend lulus**. Tidak ada kegagalan assertion backend,
joint-model identity/backpropagation, batch, narasi, urutan OCR, maupun frontend.

## Gate release

| Gate | Status | Bukti |
| --- | --- | --- |
| Backend/regresi Python | Lulus | 63 test non-frontend lulus |
| Frontend Playwright Chromium | Lulus | 13/13 test lulus |
| Macro-F1 ketiga task ≥0,70 | Gagal | E42: 0,5255/0,3956/0,4034 |
| OCR exact match ≥80% | Gagal | 75,00% dan 76,67% pada dua holdout |
| Clean Windows | Menunggu pengguna | Harus dijalankan pada mesin Windows bersih |
| Uji pengguna manusia | Menunggu pengguna | Pengguna menyatakan akan mengujinya |
| Validasi eksternal baru | Tidak tersedia | Dataset dinyatakan tetap; jangan klaim external validation |

Rilis lama tetap dapat digunakan sebagai demonstrasi, tetapi belum boleh
dipromosikan sebagai rilis penelitian yang memenuhi dua target akademik.
