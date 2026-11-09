# Fix: Unggah Ulang Gambar Tidak Mengganti Gambar

**Tanggal:** 2026-10-06
**Status:** done (2026-10-06)

## Tujuan
User melaporkan "pas upload engga ganti image". Reproduksi Playwright (desktop & mobile):
- Lulus: unggah A → analisis → unggah B; dataset → unggah → dataset → unggah; ganti gambar saat analisis berjalan.
- **Gagal:** memilih **berkas yang sama** lagi (mis. setelah analisis, atau berkas yang disunting lalu disimpan ulang dengan nama/lokasi sama) — browser tidak memicu `change` karena nilai input tidak berubah, sehingga OCR, pratinjau dan pembatalan hasil lama tidak terjadi.

## Ruang Lingkup
- `02_web_demo/index.html`:
  - berkas aktif disimpan di `gambar._berkas`; setelah dibaca, `input.value=''` agar pemilihan berikutnya (termasuk berkas sama) selalu memicu `change`; batal memilih tidak menghapus berkas aktif;
  - label baru `#namaBerkas` ("Gambar aktif: <nama>") karena input tampak kosong setelah dikosongkan;
  - `analisis()` dan `updateGuidedPreview()` memakai `gambar._berkas` (fallback `files[0]`); `pilihTab('data')` mengosongkan `_berkas` dan label.
- Regresi: tambahan di `01_notebook/test_loading_ui.js`/baru bila perlu; uji Playwright skenario berkas sama; smoke browser.
- TIDAK: backend, batch (input terpisah), OCR.

## Risiko & Asumsi
- Bila skenario user berbeda dari berkas sama, perbaikan ini tidak menutupnya — tanyakan user setelah rilis.
- Test JS lama memakai DOM tiruan; properti `_berkas` pada stub bernilai undefined sehingga jatuh ke `files`.

## Verifikasi
- Playwright: pilih A → analisis → pilih A lagi → OCR berjalan, hasil lama hilang, analisis baru memakai berkas aktif; pilih B; batal tidak menghapus.
- Semua regresi JS/Python + smoke browser lulus.

## Hasil (2026-10-06)
- `index.html`: berkas aktif di `gambar._berkas`, input dikosongkan setelah dibaca, label `#namaBerkas`; `analisis()`, `bacaOtomatis()` dan `updateGuidedPreview()` memakai berkas aktif; mode Dataset mengosongkan berkas aktif.
- Playwright: memilih berkas yang sama lagi kini menjalankan OCR ulang, menyembunyikan hasil lama dan analisis baru memakai berkas aktif; ganti ke berkas lain dan pindah mode tetap benar.
- Smoke `browser_smoke_20261006_unggah.json` **93/93** (skenario baru `scenario_berkas_sama`, 10 cek); 4 test JS + 6 test Python lulus. Tidak perlu restart server (halaman dibaca dari disk).
