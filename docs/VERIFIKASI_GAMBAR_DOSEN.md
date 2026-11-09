# Verifikasi tiga gambar asli dosen

Tanggal: 2026-10-05. User mengidentifikasi tiga file root sebagai gambar pemberian dosen. Headline acuan ditranskripsi visual oleh agen; bukan validasi label kelas dari dosen.

| File | Acuan headline | OCR aktual | Tepat | Detik |
|---|---|---|---|---:|
| WhatsApp Image 2026-09-29 at 04.33.42.jpeg | GULA-GULA DEMO BURUH | GULA-GULA DEMO BURUH | Ya | 20.61 |
| WhatsApp Image 2026-09-29 at 05.29.27.jpeg | WASWAS RUPIAH | VJJASWAS RUPIAH | Tidak | 4.13 |
| WhatsApp Image 2026-09-29 at 05.31.04.jpeg | CUKAI ABAL-ABAL ROKOK ILEGAL | CUKAI ABAL-ABAL ROKOK ILEGAL | Ya | 13.13 |

Dua dari tiga headline tepat. CUKAI ABAL-ABAL ROKOK ILEGAL tergabung benar tanpa logo TEMPO; ini bukti gambar nyata menggantikan fixture sintetis untuk kasus tersebut. WASWAS perlu dikoreksi manual dari VJJASWAS. Tidak ada perbaikan ejaan yang dipaksakan hanya agar cocok acuan.

File GULA-GULA dan WASWAS memiliki judul yang cocok dengan korpus masing-masing TMP-70CF6BDC6E3D dan TMP-EDC96202A038, tetapi SHA256 ketiga file WhatsApp tidak cocok dengan image_sha256 dataset. Kesamaan tema/judul tidak berarti file identik atau otomatis mempunyai label/anotasi dataset.

Output blok OCR, koordinat, skor, kandidat, hash dan dimensi disimpan di `DEMO_XAI_745_FULL/04_hasil_eksperimen/revisi_week3/gambar_dosen/`. Latensi GULA pertama termasuk pemuatan engine; tiga contoh bukan benchmark representatif. Teks pendukung masih memerlukan pemeriksaan; hasil ini menguji OCR/pemilihan headline, bukan keakuratan klasifikasi/XAI unggahan asli.

Ulang uji dengan `DEMO_XAI_745_FULL/venv/bin/python DEMO_XAI_745_FULL/01_notebook/verify_gambar_dosen.py` dari root; jangan mengubah file asli.
