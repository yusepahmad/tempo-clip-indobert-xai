# Minggu 2 — LIME (R4) dan Paragraf Kesimpulan Awam (R3)

**Tanggal:** 2026-09-28
**Status:** done (28 Sep 2026)
**Deadline keseluruhan:** 12 Oktober 2026 (sisa 14 hari)

## Tujuan

Menutup dua revisi terakhir dari lima butir revisi dosen 15 September:

- **R4** — atribusi kata yang tidak masuk akal pada sampul "GULA-GULA DEMO
  BURUH" (semua kata bernilai negatif; dosen menilai *"Yang fatal demo,
  padahal gambar jelas menunjukan aksi demo"*).
- **R3** — paragraf kesimpulan berbahasa awam yang menjelaskan konteks sampul
  (*"terlalu teknikal buat user, jadi di minta suatu kesimpulan akhir di mana
  hanya ada paragraf dan mudah di pahami user apa yang sebenarnya pesan
  tersirat yang coba di sampaikan oleh sampul itu"*).

Setelah Minggu 2 selesai, kelima revisi tertutup dan Minggu 3 tersisa untuk
mode batch, pengujian, dan dokumentasi.

## Ruang Lingkup

**Disentuh:**
- `02_web_demo/xai_core.py` — metode atribusi baru (LIME) + fungsi penyusun
  paragraf kesimpulan
- `02_web_demo/app.py` — meneruskan hasil metode baru ke antarmuka
- `02_web_demo/index.html` — bagian kesimpulan, penanda metode atribusi
- `01_notebook/uji_banding_atribusi.py` — skrip pembanding LIME vs occlusion (baru)
- `04_hasil_eksperimen/uji_banding_atribusi.json` — hasil pembanding (baru)
- `requirements.txt` — tambah `lime`
- `CHANGELOG.md`, `docs/`

**Tidak disentuh:**
- `03_data/` — dataset tetap 740 baris, 15 kolom (perintah tegas dosen pada R2)
- Arsitektur `MTLHead` — tiga head paralel dipertahankan (keputusan 22 Sep)
- `05_gambar/`
- Metode occlusion lama — **tetap ada** sebagai pembanding, tidak dihapus

## Langkah

### Bagian A — R4: LIME (target hari 1–4)

1. Pasang `lime` di venv, catat ke `requirements.txt`
2. Tambah metode `atribusi_kata_lime()` di `XAIEngine`, berdampingan dengan
   `atribusi_kata()` yang lama
3. Buat `01_notebook/uji_banding_atribusi.py`: bandingkan LIME vs occlusion
   pada kasus uji dosen ("GULA-GULA DEMO BURUH") dan sejumlah sampul dataset
4. Simpan hasil ke `04_hasil_eksperimen/uji_banding_atribusi.json`
5. Putuskan metode mana yang dipakai di antarmuka, berdasarkan angka
6. Sambungkan ke `app.py` dan `index.html`, sebutkan metodenya apa adanya

**Kriteria berhasil:** kata "DEMO" dan "BURUH" tidak lagi bernilai negatif
pada sampul uji, ATAU ada penjelasan berbasis data mengapa tetap begitu.

**Titik keputusan (paling lambat akhir hari 4):** bila LIME tidak memperbaiki,
hentikan dan laporkan sebagai batasan dengan bukti dua metode sudah diuji.
Untuk skripsi berbasis XAI, itu hasil yang sah — jangan memaksakan.

**HASIL (28 Sep):** LIME dipakai sebagai metode baku. Pada 25 sampul, gejala
"seluruh kata negatif" turun dari 2/25 (occlusion) menjadi 1/25 (LIME);
kedua metode sepakat soal kata teratas pada 22/25 dengan korelasi urutan
0,851. LIME 21x lebih lambat (17,68 s vs 0,83 s), sehingga occlusion
dipertahankan untuk pemrosesan banyak sampul.

**Catatan jujur:** kasus spesifik yang dilaporkan dosen tidak dapat diuji
ulang — sampul "GULA-GULA DEMO BURUH" diunggah dosen dan tidak ada di korpus
740. Yang dapat dinyatakan: LIME mengurangi gejala itu secara terukur pada
sampul dataset. Untuk membuktikan kasus itu sendiri, berkasnya perlu diminta.

### Bagian B — R3: paragraf kesimpulan (target hari 5–7)

7. Tambah fungsi `susun_kesimpulan()` di `xai_core.py`, merangkai empat bagian:

   | Bagian | Sumber |
   |---|---|
   | Apa yang dibicarakan | Task 1 + judul |
   | Siapa yang disorot | Task 3 |
   | Cara menyampaikannya | Task 2 + `DEFINISI_DOMAIN` |
   | Seberapa kuat dasarnya | Probabilitas + kata dominan + zona peta panas |

8. Untuk sampul dataset, bagian ketiga diganti catatan anotator
   (`task2_mapping_note`) yang jauh lebih kaya, diberi label ANOTATOR
9. Tampilkan sebagai bagian terpisah di bawah penjelasan teknis, sesuai
   permintaan dosen (*"untuk sementara biar saja begitu tapi tambah penjelasan
   di akhir di bawahnya"*)
10. Uji pada sampul dataset, sampul unggahan, dan sampul NON_METAFORA

### Bagian C — penutup

11. Uji end-to-end lewat HTTP untuk ketiga mode
12. Perbarui `02_BATASAN_TEKNIS.md` bagian 2 (atribusi) dan bagian 9
13. Catat ke `CHANGELOG.md`, perbarui timeline

**HASIL langkah 11 (29 Sep, verifikasi susulan):** ketiga mode diuji langsung
lewat HTTP ke `/api/analisis` pada server yang sedang berjalan
(`02_web_demo/app.py`, port 7860):

| Mode | sample_id / input | HTTP | Catatan |
|---|---|---|---|
| Dataset (leave-one-out) | `TMP-8D0A20A6A066` | 200 | `heatmap_padu_url`, `domain_tampil`, `kesimpulan.paragraf` semua terisi; `verifikasi` berisi label anotator lengkap |
| Unggahan (tanpa label) | gambar sampul + headline manual | 200 | `label_anotator`/`verifikasi` bernilai `None` sesuai desain; `kesimpulan` tetap terisi (`asal: gabungan`, dari codebook) |
| Dataset, sampul NON_METAFORA | `TMP-4650B47F4E32` | 200 | Kasus yang dulu memicu bug `GABUNGAN` (R3): `sumber_metafora` bernilai string `"nan"` kini terdeteksi kosong oleh `_bersih()`, blok `[CODEBOOK]` tampil (bukan `[ANOTATOR]` palsu), badge `[GABUNGAN]` tetap muncul di blok verifikasi |

Tidak ditemukan regresi pada R2 (label tampil), R3 (kesimpulan + badge
GABUNGAN), maupun R5 (heatmap terpadu) di ketiga mode.

## Risiko & Asumsi

| Risiko | Penanganan |
|---|---|
| LIME tidak memperbaiki R4 | Titik keputusan di hari 4; cadangan sudah disiapkan (laporkan sebagai batasan dengan bukti) |
| LIME lambat — butuh ratusan sampel perturbasi per prediksi, tiap sampel memanggil IndoBERT | Ukur dulu. Bila > 30 detik/sampul, turunkan jumlah sampel atau pakai occlusion untuk mode batch |
| Paragraf kesimpulan terdengar meyakinkan padahal Macro-F1 Task 2 hanya 0,320 | Paragraf **wajib** menyatakan ketidakpastiannya; bagian keempat khusus untuk itu |
| Sampul NON_METAFORA (83 buah) tidak punya catatan anotator | Sudah ditangani `_bersih()`; paragraf jatuh ke definisi codebook |

**Asumsi:**
- Keputusan 22 Sep tetap berlaku: tanpa LLM, arsitektur tidak diubah, temuan
  fokus-logo dilaporkan jujur.
- Contoh paragraf di `revision.pdf` hal. 4 diperlakukan sebagai **target**
  (keputusan 22 Sep), meski asal-usulnya belum dikonfirmasi ke dosen.

## Verifikasi

1. Skrip pembanding menghasilkan angka untuk LIME dan occlusion pada kasus
   yang sama, tersimpan di `04_hasil_eksperimen/`
2. Uji HTTP: mode dataset, mode unggahan, dan sampul NON_METAFORA masing-masing
   mengembalikan paragraf kesimpulan yang masuk akal
3. Dataset tetap 740 baris × 15 kolom, tidak berubah
4. Tidak ada regresi: lima blok penjelasan, peta terpadu, dan OCR tetap jalan
