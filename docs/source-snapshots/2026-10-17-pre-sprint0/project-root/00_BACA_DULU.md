> Pembaruan Week 3 (2026-10-05): UI/input/XAI dan batch tersedia untuk review baseline. Lihat [panduan dan bukti Week 3](docs/DELIVERY_WEEK_3.md), termasuk cara batch/review/ekspor, diagnosis OCR dan penerimaan yang belum lengkap. Training baru belum diintegrasikan; definisi resmi lengkap belum terverifikasi.

# Demo XAI — Dekoding Metafora Sampul Majalah Tempo (Dataset Penuh, 740 Sampul)

Paket lengkap: notebook, script eksperimen, aplikasi web, dataset, hasil
eksperimen, dan 740 gambar sampul.

Tanggal: 15 September 2026

---

## Baca ini lebih dulu

**Ini hasil menjalankan pipeline yang sama dengan demo 189 sampul
sebelumnya, kali ini pada dataset penuh (740 dari 745 sampul eligible).**

| Hal | Demo 189 sampul (lama) | Dataset 740 sampul (ini) |
|---|---|---|
| Jumlah data | 189 dari target 745 | **740 dari 745** |
| Macro-F1 Task 1 (isu utama) | 0,316 | **0,438** |
| Macro-F1 Task 2 (domain sumber) | 0,191 | **0,320** |
| Macro-F1 Task 3 (tipe entitas) | 0,213 | **0,276** |
| Zona dominan Grad-CAM (25 sampul) | kepala sampul 19/25 | kepala sampul 22/25 |

Semua angka adalah hasil model nyata, dihitung langsung dari dataset ini.
Tidak ada yang diilustrasikan atau dikarang.

---

## Isi paket

```
00_BACA_DULU.md              dokumen ini
01_TUTORIAL.md               panduan langkah demi langkah (sama seperti demo 189)

01_notebook/
   DEMO_XAI_TEMPO.ipynb      notebook asli (referensi metodologi, dibuat untuk 189 sampul)
   extract_features.py       script ekstraksi fitur CLIP+IndoBERT untuk 740 sampul
   run_evaluation.py         script pelatihan MTL + 5-fold CV untuk 740 sampul
   run_xai_analysis.py       script Grad-CAM, zona dominan, uji leave-one-out

02_web_demo/
   app.py                    server web (Flask), sudah diarahkan ke dataset 740
   xai_core.py               mesin prediksi dan XAI
   index.html                antarmuka

03_data/
   DATASET_740_TASK2_DOMAIN.csv       dataset 740 sampul + task2_domain_sumber
   fitur_clip_indobert_740.npz        cache fitur, agar tidak perlu ekstraksi ulang

04_hasil_eksperimen/
   hasil_mtl_740_task2domain.json     metrik Task 1/2/3 (5-fold CV, 4 varian model)
   analisis_recall_per_kelas_740.csv  recall & F1 per kelas Task 2
   analisis_zona_740.json             zona dominan Grad-CAM pada 25 sampul (leave-one-out)
   hasil_uji_satu_gambar_740.json     uji leave-one-out pada 7 sampul contoh

05_gambar/
   740 berkas sampul, dinamai <sample_id>.jpg/.jpeg/.webp
```

---

## Cara tercepat mencoba

**Aplikasi web (disarankan — sudah diuji jalan end-to-end)**

**Windows** — klik dua kali `setup_windows.bat` (sekali saja), lalu
`jalankan_windows.bat`.

**Linux / macOS**

```bash
python3.10 -m venv venv
venv/bin/pip install --extra-index-url https://download.pytorch.org/whl/cpu torch torchvision
venv/bin/pip install -r requirements.txt
./jalankan_linux.sh
```

Buka http://127.0.0.1:7860 di browser. Sudah diverifikasi: memuat 740 sampul,
prediksi tiga task, Grad-CAM, atribusi kata, dan penjelasan naratif semuanya
berjalan dengan benar pada dataset penuh ini.

**Menjalankan ulang eksperimen dari nol**

```bash
venv/bin/python 01_notebook/extract_features.py   # ~2 menit, hasilkan .npz
venv/bin/python 01_notebook/run_evaluation.py      # ~1 menit, 5-fold CV
venv/bin/python 01_notebook/run_xai_analysis.py    # ~1 menit, Grad-CAM + zona

# Windows: ganti "venv/bin/python" menjadi "venv\Scripts\python" 
```

Detail lengkap ada di `01_TUTORIAL.md`.

---

## Tiga task yang diprediksi

| Task | Isi | Kelas |
|---|---|---|
| Task 1 | Isu utama sampul | 10 |
| Task 2 | Domain sumber metafora | 7 |
| Task 3 | Tipe entitas sasaran | 8 |

Distribusi kelas Task 2 pada dataset 740 sampul:

| Domain | Jumlah |
|---|---|
| MESIN_INFRASTRUKTUR | 214 |
| PERMAINAN_KONTES | 106 |
| BENCANA_JERAT | 100 |
| HEWAN_TUBUH | 90 |
| KONSUMSI_TRANSAKSI | 84 |
| NON_METAFORA | 83 |
| LAINNYA | 63 |

Tidak ada kelas dengan jumlah sampel terlalu sedikit untuk 5-fold CV (kelas
terkecil, LAINNYA, tetap punya 63 sampul).

---

## Temuan yang paling penting dari paket ini

Analisis 25 sampul (leave-one-out) menunjukkan model **masih lebih bertumpu
pada zona kepala sampul (logo dan judul kecil) daripada ilustrasi
metaforanya** — temuan ini konsisten dengan demo 189 sampul, bahkan setelah
data bertambah hampir 4 kali lipat:

| Zona | Intensitas rata-rata | Dominan pada |
|---|---|---|
| Kepala sampul | 0,180 | 22 dari 25 sampul |
| Bagian tengah (ilustrasi) | 0,086 | 2 sampul |
| Kaki sampul | 0,060 | 1 sampul |

Artinya prediksi yang benar belum tentu karena alasan yang benar — dan
kelemahan ini tetap ada meskipun jumlah data meningkat signifikan. Ini
memperkuat rekomendasi tindak lanjut yang sudah dicatat di demo sebelumnya:
memangkas area logo/judul kecil sebelum encoding, lalu menguji apakah fokus
model bergeser ke ilustrasi.
