# Verifikasi tiga gambar asli dosen

> **Dokumen riwayat per 5 Oktober 2026** (tabel di bawah adalah hasil 5 Okt di mesin asal). Status terbaru: [STATUS_REVISI_20261006.md](STATUS_REVISI_20261006.md) (6 Oktober 2026). Hasil OCR foto dosen per 6 Okt di server ada di bagian "Pembaruan 6 Oktober 2026".

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

## Pembaruan 6 Oktober 2026

Tabel dan paragraf di atas adalah hasil 5 Okt di mesin asal dan tidak diubah. Per 6 Okt, ketiga foto disalin ke `06_gambar_revisi/` di paket dan diuji ulang di server `10.12.1.31`. Path bukti relatif terhadap `04_hasil_eksperimen/revisi_week3/`.

| File | Acuan headline | OCR server 6 Okt (4 thread) | Audit OCR 6 Okt (8 thread) | Tepat |
|---|---|---|---|---|
| WhatsApp Image 2026-09-29 at 04.33.42.jpeg | GULA-GULA DEMO BURUH | GULA-GULA DEMO BURUH | GULA-GULA DEMO BURUH | Ya |
| WhatsApp Image 2026-09-29 at 05.29.27.jpeg | WASWAS RUPIAH | VJASWAS RUPIAH | VJJASWAS RUPIAH | Tidak |
| WhatsApp Image 2026-09-29 at 05.31.04.jpeg | CUKAI ABAL-ABAL ROKOK ILEGAL | CUKAI ABAL-ABAL ROKOK ILEGAL | CUKAI ABAL-ABAL ROKOK ILEGAL | Ya |

- **Judul:** tetap 2/3 tepat. Salah baca WASWAS berasal dari EasyOCR dan berbeda menurut lingkungan: `VJASWAS` di server (4 thread, versi pustaka lebih baru), `VJJASWAS` di mesin asal (tabel 5 Okt) dan pada audit OCR yang memakai 8 thread. Koreksi manual tetap perlu. Bukti server: `server_baseline_20261006.json` (`ocr_foto_dosen`) dan smoke browser final `browser_smoke_20261006_audit.json` (94/94; WASWAS dikoreksi manual sebelum analisis). Bukti 8 thread: `ocr_audit_urutan_20261006.json`, kunci `dosen`.
- **Teks pendukung:** kini disusun menurut tata letak (baris, lalu kolom/paragraf, dengan deck di bawah judul lebih dulu), dan sampah teks baku ("TEMPOCOIMINGGUAN", "TEMPOCO/MINGGUAN", "INVES AGASI", "SN: Olze") dibuang. Contoh hasil smoke final untuk GULA-GULA: "Presiden Prabowo menunjuk ketua konfederasi buruh Jumhur Hidayat menjadi Menteri Lingkungan Hidup. Grogi meredam May Day. H.26; Uji Bukti Mendakwa Nadiem Makarim H.63; Lintang Pukang 3 Juta Rumah H.72". Bukti tanpa sampah: `supporting_final` pada `browser_smoke_20261006_audit.json` dan [plan sampah teks baku](plans/2026-10-06-ocr-sampah-teks-baku.md). Entri `dosen` kolom `produksi` di `ocr_audit_urutan_20261006.json` (dihitung ulang 6 Okt malam, blok OCR 8 thread) juga sudah tanpa sampah tersebut; kolom `baseline`/`audit1` adalah pembanding beku sebelum filter. Uji ulang dari paket: `venv/bin/python 01_notebook/verify_gambar_dosen.py <folder_keluaran>` (kini membaca `06_gambar_revisi/`).
- **R4 pada foto dosen:** smoke browser Task 2 (LIME, judul final): GULA-GULA → Permainan & Kontes, dengan ketiga kata GULA-GULA/DEMO/BURUH bernilai negatif saat teks pendukung terisi hasil OCR. Kelas unggahan tetap tidak divalidasi; lihat R4 di [STATUS_REVISI_20261006.md](STATUS_REVISI_20261006.md).
- **Ulang uji (6 Okt malam):** `verify_gambar_dosen.py` kini membaca foto dari `06_gambar_revisi/` (jatuh ke folder induk hanya untuk tata letak mesin asal) dan menerima folder keluaran sebagai argumen agar bukti 5 Okt di `revisi_week3/gambar_dosen/` tidak tertimpa. Dijalankan dari paket 6 Okt malam: GULA-GULA dan CUKAI tepat, WASWAS `VJJASWAS RUPIAH`.
