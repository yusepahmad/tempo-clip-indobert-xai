# Pemutakhiran Teks Notebook Metodologi

**Tanggal:** 2026-10-06
**Status:** done (2026-10-06)

## Tujuan
User menanyakan mengapa `01_notebook/DEMO_XAI_TEMPO.ipynb` masih bertanggal 29 September 2026. Tanggal itu sesuai isi terakhir notebook, tetapi teksnya tertinggal dari aplikasi: atribusi kata disebut "occlusion, bukan LIME penuh" (aplikasi memakai LIME baku sejak 28 Sep), definisi domain disebut dari "173 catatan" (sisa pilot; dataset final 657 catatan), dan tidak ada catatan perubahan 5–6 Okt (peta gabungan R5, narasi ringkasan/penjelasan, OCR, fine-tuning Kaggle).

## Ruang Lingkup
- Hanya sel markdown 0, 27, 42 notebook (JSON diedit langsung, sel kode dan output tidak diubah, notebook tidak dijalankan ulang): tanggal pemutakhiran 6 Okt + blok "Pembaruan 6 Oktober 2026" (beda notebook vs aplikasi), "173" → "657", daftar "belum dikerjakan" diselaraskan.
- `00_BACA_DULU.md`, `01_TUTORIAL.md` (baris rujukan notebook), CHANGELOG; ZIP delivery dibangun ulang, diverifikasi hanya dokumen/notebook yang berbeda dari ZIP yang lulus uji bersih.
- TIDAK: kode notebook, angka eksperimen.

## Verifikasi
- Notebook tetap JSON valid (nbformat), jumlah sel/output kode tidak berubah; ZIP baru: CRC + manifest lulus; beda dengan ZIP teruji hanya berkas dokumen/notebook.

## Hasil (2026-10-06)
- Sel 0: "Tanggal pemutakhiran: 6 Oktober 2026 (isi metodologi dan angka sejak 29 September 2026)", baris tabel atribusi kata diselaraskan, blok baru "Pembaruan 6 Oktober 2026 — beda notebook ini dengan aplikasi". Sel 27: "173" → "657 catatan" (diverifikasi dari dataset). Sel 42: daftar "belum dikerjakan" diselaraskan (LIME di notebook, integrasi checkpoint).
- 43 sel tetap; sel kode dan output identik; `nbformat.validate` lulus (peringatan id sel sudah ada sebelumnya).
- `00_BACA_DULU.md` dan `01_TUTORIAL.md` merujuk pemutakhiran ini; ZIP delivery dibangun ulang.
