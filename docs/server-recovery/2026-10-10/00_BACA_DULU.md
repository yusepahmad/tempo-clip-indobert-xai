# Demo XAI — Dekoding Metafora Sampul Majalah Tempo (740 Sampul)

Gambaran paket · per 6 Oktober 2026

> **Status:** **paket delivery revisi Week 3** dengan **model baseline**
> (`TEMPO_XAI_DELIVERY_WEEK3_20261006.zip`). Paket ini diuji dari instalasi
> bersih di Linux, lihat `docs/plans/2026-10-06-paket-delivery-final.md`.
> Beberapa hal masih terbuka: instalasi bersih Windows, browser selain
> Chromium, uji pengguna manusia, sasaran OCR 80%, eksperimen E01/E02,
> integrasi checkpoint fine-tuning, dan autentikasi server. Status terbaru
> per revisi ada di [`docs/STATUS_REVISI_20261006.md`](docs/STATUS_REVISI_20261006.md).

---

## Apa sistem ini

Diberi sebuah sampul Majalah Tempo (gambar + judul utama + teks pendukung),
sistem memprediksi tiga hal, lalu **menjelaskan dasar keputusannya** (XAI):

| Task | Pertanyaan | Kelas |
|---|---|---|
| Task 1 | Topik/isu utama sampul | 10 |
| Task 2 | Ranah (domain sumber) metafora | 7 |
| Task 3 | Tipe entitas/pihak yang disorot | 8 |

Total 25 kelas. Definisi, kriteria, dan contoh tiap kelas memakai **codebook
operasional** yang disusun atas instruksi user (bukan codebook resmi; tidak
menunggu codebook resmi).

Dataset: **740 sampul (dataset final)**. Model demo: **baseline** — CLIP
ViT-B/32 + IndoBERT beku + head Multi-Task Learning.

Penjelasan yang ditampilkan:
- **Bukti gambar** — peta panas area gambar yang berpengaruh.
- **Bukti kata** — atribusi kata judul (LIME baku di analisis satuan,
  occlusion sebagai pilihan cepat di batch).
- **Ringkasan** (tab Prediksi) — ringkasan awam tiga task sekaligus (isu,
  pihak yang disorot, kiasan), dengan tingkat keyakinan dan perbandingan
  dengan label anotator untuk sampul dataset.
- **Penjelasan** (tab Penjelasan) — alasan untuk task pilihan, dalam bagian
  "Mengapa <kelas>?", "Arti kelas ini", "Catatan anotator" (hanya milik task
  itu) dan "Yang perlu dicek".

Ringkasan dan penjelasan dirangkai dari bukti dengan templat (bukan LLM) dan
diberi penanda asal MODEL / ANOTATOR / CODEBOOK / GABUNGAN.

---

## Hasil model (baseline, dipakai demo)

Macro-F1, 5-fold cross-validation pada 740 sampul:

| Task | Macro-F1 baseline |
|---|---|
| Task 1 — isu utama | **0,438** |
| Task 2 — domain sumber metafora | **0,320** (0,3197) |
| Task 3 — tipe entitas | **0,276** |

**Catatan fine-tuning Kaggle.** Full fine-tuning kedua encoder di Kaggle
sudah selesai (COMPLETE) dengan hasil 0,5139 / 0,2461 / 0,3699. Task 1 dan
Task 3 naik, tetapi **Task 2 — fokus demo — turun**, sehingga **baseline tetap
dipakai**. Checkpoint fine-tuning belum diunduh/diintegrasikan ke aplikasi.
Rincian: [`docs/HASIL_FULL_TRAINING_KAGGLE.md`](docs/HASIL_FULL_TRAINING_KAGGLE.md).

### Riwayat singkat: dibanding demo 189 sampul

| Hal | Demo 189 sampul (lama) | Dataset final 740 sampul |
|---|---|---|
| Macro-F1 Task 1 | 0,316 | 0,438 |
| Macro-F1 Task 2 | 0,191 | 0,320 |
| Macro-F1 Task 3 | 0,213 | 0,276 |
| Zona dominan Grad-CAM (25 sampul) | kepala sampul 19/25 | kepala sampul 22/25 |

### Temuan penting: model bertumpu pada kepala sampul

Analisis zona pada 25 sampul (leave-one-out) menunjukkan model **lebih
bertumpu pada kepala sampul (logo dan judul kecil) daripada ilustrasi
metaforanya**:

| Zona | Intensitas rata-rata | Dominan pada |
|---|---|---|
| Kepala sampul | 0,180 | 22 dari 25 sampul |
| Bagian tengah (ilustrasi) | 0,086 | 2 sampul |
| Kaki sampul | 0,060 | 1 sampul |

Artinya prediksi yang benar belum tentu benar karena alasan yang benar.
Temuan ini dilaporkan apa adanya sebagai batasan (sumber:
`04_hasil_eksperimen/analisis_zona_740.json`).

Distribusi kelas Task 2 pada 740 sampul: MESIN_INFRASTRUKTUR 214,
PERMAINAN_KONTES 106, BENCANA_JERAT 100, HEWAN_TUBUH 90, KONSUMSI_TRANSAKSI 84,
NON_METAFORA 83, LAINNYA 63.

---

## Isi paket

```
MULAI_DARI_SINI.md           pintu masuk: cara menjalankan + urutan baca
00_BACA_DULU.md              dokumen ini (gambaran paket)
01_TUTORIAL.md               panduan langkah demi langkah memakai UI
02_BATASAN_TEKNIS.md         batasan yang perlu diketahui sebelum menyimpulkan
TEKS_DELIVERY.md             draf pesan serah terima
CHANGELOG.md                 catatan seluruh perubahan
AGENTS.md                    aturan kerja proyek (plan + changelog)
DELIVERY_MANIFEST.json       SHA256 dan ukuran tiap berkas paket (cek integritas)

jalankan_linux.sh            menjalankan aplikasi di Linux/macOS
jalankan_windows.bat         menjalankan aplikasi di Windows
setup_windows.bat            setup otomatis Windows (sekali jalan)
requirements.txt             pustaka aplikasi (batas bawah versi)
requirements-lock-linux.txt  versi pustaka persis yang terbukti lulus semua
                             test di server Linux (Python 3.10, CPU)
requirements-verification.txt   tambahan untuk regresi HTML5/HTTP
requirements-browser.txt     tambahan untuk smoke browser (Playwright)
requirements-training-windows.lock.txt   lock environment training Windows

01_notebook/
   DEMO_XAI_TEMPO.ipynb      notebook metodologi baseline (dataset 740; teks dimutakhirkan 6 Okt — lihat blok "Pembaruan 6 Oktober" di sel pertama)
   extract_features.py, run_evaluation.py, run_xai_analysis.py
                             ekstraksi fitur, 5-fold CV, Grad-CAM + zona
   test_ui_html5.py, test_week3_regressions.py,
   test_week3_training_audit.py, test_batch_error_message.py,
   test_narasi_ringkasan.py, test_ocr_urutan.py, test_audit_backend.py
                             regresi Python
   test_audit_frontend.py    regresi frontend (Playwright, endpoint berat di-mock)
   test_loading_ui.js, test_week3_state.js,
   test_workspace_ui.js, test_r5_heatmap.js
                             regresi JavaScript (Node)
   verify_r5_http.py, verify_week3_http.py, verify_scale740.py,
   verify_gambar_dosen.py, smoke_browser_week3.py
                             verifikasi HTTP / skala 740 / foto dosen / browser
   audit_ocr_urutan.py, evaluate_ocr_week3.py, compare_selector_week3.py,
   compare_decoder_week3.py, audit_finetuned_week3.py, kaggle_benchmark/, ...
                             audit/evaluasi OCR, audit fine-tuning, benchmark

02_web_demo/
   app.py                    server web (Flask)
   xai_core.py               mesin prediksi dan XAI
   index.html                antarmuka
   batch_jobs.py             antrean batch, ekspor CSV/JSON, lanjut/ulang
   class_catalog.py          katalog 25 kelas
   codebook_operasional.json codebook operasional 25 kelas
   explanation_evidence.py   ringkasan dan penjelasan berbasis bukti (templat)
   label_display.py          label ramah pengguna
   ocr_headline.py           OCR, pemilihan judul, urutan baca teks pendukung

03_data/
   DATASET_740_TASK2_DOMAIN.csv       dataset 740 sampul
   fitur_clip_indobert_740.npz        cache fitur CLIP + IndoBERT

04_hasil_eksperimen/
   hasil_mtl_740_task2domain.json     metrik baseline Task 1/2/3 (5-fold CV)
   analisis_recall_per_kelas_740.csv  recall & F1 per kelas Task 2
   analisis_zona_740.json             zona dominan Grad-CAM (25 sampul)
   hasil_uji_satu_gambar_740.json     uji leave-one-out 7 sampul contoh
   revisi_week3/                      bukti verifikasi Week 3 (server baseline,
                                      R5, smoke browser, OCR, batch, skala 740, ...)
   finetuned_kaggle/                  log + metrik audit full fine-tuning Kaggle
   ...                                benchmark & smoke training lainnya

05_gambar/                   740 gambar sampul (<sample_id>.jpg/.jpeg/.webp)
06_gambar_revisi/            tiga foto sampul dari dosen (uji unggahan/OCR)

docs/                        laporan Week 1–3, codebook, audit, status, plans/
```

Folder `venv/` dibuat di komputer masing-masing dan tidak disertakan dalam
paket. Cache/job lokal (`02_web_demo/_cache/`, `_jobs/`) juga tidak disertakan.
`DELIVERY_MANIFEST.json` mencantumkan SHA256 tiap berkas sehingga isi paket
dapat dicocokkan setelah diekstrak.

---

## Cara tercepat mencoba

Langkah lengkap (termasuk persiapan Python) ada di
[`MULAI_DARI_SINI.md`](MULAI_DARI_SINI.md).

- **Linux/macOS:** buat venv dan pasang `requirements.txt` (atau
  `requirements-lock-linux.txt` untuk versi persis yang sudah diuji), lalu
  `./jalankan_linux.sh`.
- **Windows:** `setup_windows.bat` (sekali), lalu `jalankan_windows.bat`.

Buka **http://127.0.0.1:7860** di browser.

> Paket ini diuji dari instalasi bersih di Linux, lihat
> `docs/plans/2026-10-06-paket-delivery-final.md`. Instalasi bersih di Windows
> belum diuji.

### Ringkas fitur UI terbaru

- **Navigasi Analisis / Batch / Panduan.**
- **Tiga langkah** di panel "Mulai di sini" (mode Dataset / Unggah gambar):
  1. pilih sampul dari dataset atau gambar dari laptop,
  2. periksa judul utama (dan teks pendukung, boleh kosong, boleh multibaris),
  3. pilih penjelasan yang ingin dilihat — Ranah metafora (Task 2, baku),
     Topik utama (Task 1), atau Pihak yang disorot (Task 3) — lalu
     **Analisis sampul**. Panel "Sampul pilihan" menampilkan preview.
- **OCR + koreksi:** gambar unggahan dibaca otomatis, lalu muncul "Pilihan
  judul hasil pembacaan otomatis". Teks pendukung disusun menurut tata letak
  sampul, dan teks baku sampul yang salah terbaca dibuang. Dengan versi
  aplikasi terakhir, judul tepat 68–78% pada dua set validasi 60 sampul
  (cenderung optimistis karena kedua set ikut dipakai saat perbaikan; angka
  saat kode dibekukan 63–72%). Sasaran usulan 80% belum tercapai, jadi hasil
  OCR **wajib diperiksa** dan dikoreksi manual.
- **Ganti gambar:** gambar baru (atau berkas yang sama dipilih lagi) selalu
  dibaca ulang dan mengganti judul/teks pendukung. Ketikan selama pembacaan
  berjalan tidak ditimpa. Nama berkas tampil sebagai "Gambar aktif: …".
- **Loading:** overlay "Sedang menganalisis sampul". Mengganti input/task saat
  proses berjalan membatalkan hasil lama, dan pembatalan itu juga dikirim ke
  server.
- **Batas masukan:** judul ≤300 karakter, teks pendukung ≤2000, unggahan
  analisis/OCR ≤25 MB, gambar dengan sisi >8000 px, rasio >5:1 atau lebih
  dari 40 MP ditolak, gambar besar diperkecil ke sisi terpanjang 2000 px,
  paling banyak 2 job batch aktif/antre. Pesan galat dikirim sebagai JSON.
- **Lima tab hasil:** Prediksi, Bukti gambar, Bukti kata, Penjelasan,
  Bandingkan label.
- **Bukti gambar:** **peta gabungan tiga task** sebagai peta utama (sama untuk
  semua pilihan task), lalu blok **"Bukti task pilihan"** berisi peta task yang
  menjadi dasar penjelasan. Peta per task tersedia di tampilan teknis.
- **Batch:** ID dataset dan/atau gambar unggahan, pilihan task dan metode
  atribusi di view Batch (Occlusion bawaan, LIME opsional), ekspor CSV/JSON,
  lanjut/ulang item gagal.
  Status `failed` muncul bila semua item gagal. Batch dataset bersifat
  in-sample, jadi bukan metrik akurasi.

LIME butuh sekitar 15–20 detik per analisis di CPU server.

### Menjalankan ulang eksperimen baseline

```bash
venv/bin/python 01_notebook/extract_features.py   # fitur CLIP + IndoBERT (.npz)
venv/bin/python 01_notebook/run_evaluation.py      # MTL + 5-fold CV
venv/bin/python 01_notebook/run_xai_analysis.py    # Grad-CAM + zona dominan
# Windows: ganti "venv/bin/python" menjadi "venv\Scripts\python"
```

---

## Baca selanjutnya

| Berkas | Isi |
|---|---|
| [`MULAI_DARI_SINI.md`](MULAI_DARI_SINI.md) | Cara menjalankan dan urutan baca |
| [`01_TUTORIAL.md`](01_TUTORIAL.md) | Panduan memakai UI langkah demi langkah |
| [`docs/STATUS_REVISI_20261006.md`](docs/STATUS_REVISI_20261006.md) | Status terbaru R1–R5 dan T01–T12 |
| [`02_BATASAN_TEKNIS.md`](02_BATASAN_TEKNIS.md) | Batasan teknis — baca sebelum menyimpulkan apa pun |
