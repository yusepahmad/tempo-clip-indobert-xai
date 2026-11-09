# Pemahaman Paket DEMO_XAI_745_FULL + Revisi 15 Sep

**Tanggal:** 2026-09-22
**Status:** dokumen pemahaman (belum ada perubahan kode)

## 1. Ringkasan sistem

Demo XAI untuk dekoding metafora sampul Majalah Tempo. Pipeline:

1. **Fitur**: CLIP ViT-B-32 (`laion2b_s34b_b79k`) untuk gambar + IndoBERT
   (`indobenchmark/indobert-base-p1`, token CLS) untuk teks
   `headline [SEP] supporting`. Keduanya L2-normalized, digabung → 1280 dim
   (512 img + 768 txt). Cache: `03_data/fitur_clip_indobert_740.npz`.
2. **Model**: head MTL kecil — `Linear(1280→256) + ReLU + Dropout(0.4)`
   bersama, lalu 3 head linear per task. Encoder dibekukan. AdamW lr=1e-3,
   wd=1e-4, 120 epoch full-batch, class-weighted CrossEntropy, seed 42.
3. **Evaluasi**: stratified 5-fold CV (stratifikasi pakai Task 1).
4. **XAI**: Grad-CAM adaptasi ViT + atribusi kata occlusion + penjelasan
   naratif berlabel asal.

### Tiga task

| Task | Isi | Kelas |
|---|---|---|
| task1_issue | Isu utama | 10 |
| task2_domain_sumber | Domain sumber metafora | 7 |
| task3_primary_entity_type | Tipe entitas sasaran | 8 |

### Hasil (740 sampul, fusion MTL)

| Task | Accuracy | Macro-F1 | Baseline F1 |
|---|---|---|---|
| Task 1 | 0,455 | 0,438 | 0,036 |
| Task 2 | 0,320 | 0,320 | 0,064 |
| Task 3 | 0,355 | 0,276 | 0,075 |

Recall per kelas Task 2 terendah: KONSUMSI_TRANSAKSI 0,214 dan
MESIN_INFRASTRUKTUR 0,220 (padahal kelas terbesar, 214 sampel).
Tertinggi NON_METAFORA 0,651.

### Temuan XAI utama

Dari 25 sampul leave-one-out: zona dominan kepala 22, tengah 2, kaki 1.
Intensitas rata-rata: kepala 0,180 / tengah 0,086 / kaki 0,060.
Model bertumpu pada logo+judul kecil, bukan ilustrasi metaforanya.

## 2. Arsitektur kode

- `01_notebook/extract_features.py` — ekstraksi fitur → .npz
- `01_notebook/run_evaluation.py` — 4 varian model × 5-fold CV → JSON + CSV
- `01_notebook/run_xai_analysis.py` — Grad-CAM, zona, leave-one-out
- `02_web_demo/xai_core.py` — `XAIEngine` (train/predict/gradcam/atribusi_kata),
  `DEFINISI_DOMAIN`, `zona_dominan`, `susun_penjelasan`, `heatmap_overlay`
- `02_web_demo/app.py` — Flask, port 7860. Dua mode: pilih sampul dataset
  (leave-one-out, ada label pembanding) atau unggah gambar (tanpa label)
- `02_web_demo/index.html` — antarmuka 5 bagian

### Catatan teknis Grad-CAM

Hook diambil di `visual.transformer.resblocks[-2]`, bukan blok terakhir:
pada CLIP hanya token CLS dipakai untuk embedding, jadi gradien token patch
di blok terakhir nol. Metode yang dipakai sebenarnya Gradient×Activation per
token (`(a*g).sum(-1).abs()`), bukan Grad-CAM CNN — sudah disebut apa adanya
di komentar kode.

## 3. Revisi dari pembimbing (`docs/references/revision/revision.pdf`, 15 Sep)

PDF 32 halaman Canva; konten nyata hanya halaman 1-7 (hal. 8 meme, 9-32 kosong).

### R1 — OCR otomatis untuk input teks (hal. 2)
User harus mengetik ulang headline saat upload. Diminta terisi otomatis
via OCR. Arahan: "berbasis trm base => hf" (TrOCR / transformer-based dari
HuggingFace), tapi boleh pakai yang lain.

### R2 — Rename label kelas di tampilan (hal. 3)
`KONSUMSI_TRANSAKSI` dilingkari merah. Nama kelas teknis harus dipetakan ke
istilah yang mudah dipahami saat **ditampilkan**. Tegas: **jangan ubah
dataset**, hanya display mapping. Contoh yang disebut: "permainan kontes".

### R3 — Paragraf kesimpulan awam di akhir (hal. 4)
Penjelasan dinilai jelas tapi terlalu teknis. Diminta satu paragraf penutup
berbahasa awam yang menjawab: apa pesan tersirat sampul ini. Untuk sementara
bagian teknis tetap ada, kesimpulan ditambah di bawahnya; saat final, user
cukup melihat kesimpulan saja.

**Bug dilaporkan:** badge ungu `GABUNGAN` tidak pernah muncul.

### R4 — Atribusi kata tidak masuk akal (hal. 5-6)
Sampul "GULA-GULA DEMO BURUH": semua kontribusi negatif — GULA-GULA −0,023,
DEMO −0,087, BURUH −0,089. Keberatan pembimbing:
- "GULA-GULA" rendah wajar (tidak ada unsur gula di gambar)
- **"DEMO" fatal**: gambar jelas menunjukkan megafon + kepalan tangan
- "BURUH" justru menurunkan, padahal jelas ada di teks dan gambar

Juga diminta: judul dikaitkan dengan konteks bawah (konteks keyword).

### R5 — Satu heatmap terpadu (hal. 7)
Sampul "CUKAI ABAL-ABAL ROKOK ILEGAL": heatmap task 1/2/3 berbeda-beda.
Boleh berbeda di tampilan teknis, tapi untuk user harus **satu heatmap yang
mencakup semua**. Catatan: tidak ada satu pun yang menangkap asap rokok,
tangan yang memegang rokok, dan sarung tangan golf (task 3 paling dekat tapi
masih kurang).

**Catatan pembimbing:** "Ga harus mingdep selesai semua."

## 4. Temuan verifikasi kode (akar masalah bug)

Diverifikasi langsung di kode, bukan dugaan:

1. **Bug format `+-0.023`** — `xai_core.py:419-420` menulis `+` secara
   hardcode: `f"(kontribusi +{top['kontribusi']:.3f})"`. Saat semua
   kontribusi negatif, tercetak `+-0.023`. Lebih dalam: kata dengan
   kontribusi negatif tetap disebut "paling menopang keputusan" — secara
   logika salah, karena tidak ada kata yang menopang.

2. **`GABUNGAN` tidak muncul** — `xai_core.py:473`, syaratnya
   `catatan and catatan.get("sumber_metafora") and cam is not None`.
   Di `app.py` mode unggahan, `catatan = None`, sehingga blok 5 dilewati.
   Sampul pada screenshot hal. 4 adalah mode unggahan → GABUNGAN memang
   tidak akan pernah muncul di mode itu. Di mode dataset, 83 sampul
   NON_METAFORA punya `task2_source_description` yang jadi string `"nan"`
   (truthy) sehingga lolos syarat secara keliru.

3. **Teks usang dari versi 189** — masih tersisa di paket 740:
   - `index.html:347` — "wajar pada tahap 189 sampul — Macro-F1 Task 2
     domain baru 0,174"
   - `xai_core.py` DEFINISI_DOMAIN: LAINNYA "terdapat 12 sampul"
     (seharusnya 63), NON_METAFORA "16 dari 189 sampul" (seharusnya 83)
   - `app.py:~150` komentar "pakai seluruh 189 sebagai data latih"

4. **`02_BATASAN_TEKNIS.md` tidak ada** — dirujuk dua kali di
   `01_TUTORIAL.md` (Bagian D dan Bagian E) tapi file tidak ada di paket.

5. **`run_xai_analysis.py` docstring tidak sinkron** — menyebut "5 sampul
   contoh", kode memakai 7.

## 5. Yang belum diputuskan

- R4 adalah masalah kualitas model, bukan sekadar bug tampilan. Perlu
  keputusan: perbaiki metode atribusi (occlusion pada IndoBERT CLS mungkin
  terlalu kasar), atau jelaskan sebagai batasan.
- R5 "satu heatmap mencakup semua" perlu definisi: rata-rata 3 task,
  atau heatmap task terpilih saja.
