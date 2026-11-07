> Pembaruan Week 3 (2026-10-05): UI/input/XAI dan batch tersedia untuk review baseline. Lihat [panduan dan bukti Week 3](docs/DELIVERY_WEEK_3.md), termasuk cara batch/review/ekspor, diagnosis OCR dan penerimaan yang belum lengkap. Training baru belum diintegrasikan; definisi resmi lengkap belum terverifikasi.

# Tutorial — langkah demi langkah (dataset 740 sampul)

---

## Bagian A — Menjalankan aplikasi web (paling cepat, sudah diuji jalan)

**Syarat: Python 3.10 atau 3.11.** Python 3.12 ke atas belum tentu didukung
PyTorch.

### Linux / macOS

**1. Buat environment terpisah (bila belum ada)**

```bash
python3.10 -m venv venv
```

**2. Pasang pustaka**

```bash
venv/bin/pip install --extra-index-url https://download.pytorch.org/whl/cpu torch torchvision
venv/bin/pip install -r requirements.txt
```

**3. Jalankan**

```bash
cd 02_web_demo
../venv/bin/python app.py
```

Buka http://127.0.0.1:7860 di browser. Model dilatih otomatis saat server
menyala (sekitar 5–10 detik untuk 740 sampul), lalu siap dipakai.

**4. Mematikan**

Tekan Ctrl+C di terminal.

### Windows

**1. Buat environment terpisah (bila belum ada)**

Buka Command Prompt atau PowerShell, lalu jalankan (pastikan `python` yang
terpanggil adalah versi 3.10 atau 3.11 — cek dulu dengan `python --version`,
atau pakai `py -3.10` bila beberapa versi Python terpasang):

```bat
py -3.10 -m venv venv
```

**2. Pasang pustaka**

```bat
venv\Scripts\pip install --extra-index-url https://download.pytorch.org/whl/cpu torch torchvision
venv\Scripts\pip install -r requirements.txt
```

**3. Jalankan**

```bat
cd 02_web_demo
..\venv\Scripts\python app.py
```

Buka http://127.0.0.1:7860 di browser. Model dilatih otomatis saat server
menyala (sekitar 5–10 detik untuk 740 sampul), lalu siap dipakai.

**4. Mematikan**

Tekan Ctrl+C di jendela terminal.

**Catatan Windows:**
- Bila `py` tidak dikenali, gunakan `python` biasa (asalkan versinya 3.10/3.11)
  atau instal peluncur Python dari python.org dengan opsi "py launcher"
  dicentang saat instalasi.
- Bila muncul error terkait "long path" saat memasang PyTorch, aktifkan
  dukungan path panjang di Windows (Group Policy atau registry `LongPathsEnabled`)
  atau pindahkan folder paket ke path yang lebih pendek (misalnya `C:\demo_xai`).
- Antivirus/Windows Defender kadang memperlambat instalasi paket besar seperti
  PyTorch — ini normal, tunggu saja sampai selesai.

---

## Bagian B — Menjalankan ulang eksperimen dari nol

Tiga script di `01_notebook/` mereplikasi seluruh alur pada notebook demo
189 sampul, diterapkan pada dataset 740 sampul. Jalankan berurutan.

Perintah di bawah memakai path gaya Linux/macOS (`venv/bin/python`). Di
Windows, ganti dengan `venv\Scripts\python` (Command Prompt/PowerShell),
misalnya `venv\Scripts\python 01_notebook\extract_features.py`.

**1. Ekstraksi fitur (± 2 menit, CPU)**

```bash
venv/bin/python 01_notebook/extract_features.py
```
```bat
venv\Scripts\python 01_notebook\extract_features.py
```

Memuat CLIP (ViT-B-32, laion2b_s34b_b79k) dan IndoBERT
(indobenchmark/indobert-base-p1), lalu menghitung fitur untuk 740 gambar dan
740 teks headline+pendukung. Hasil disimpan ke
`03_data/fitur_clip_indobert_740.npz`.

**2. Pelatihan + evaluasi 5-fold CV (± 1 menit)**

```bash
venv/bin/python 01_notebook/run_evaluation.py
```
```bat
venv\Scripts\python 01_notebook\run_evaluation.py
```

Melatih 4 varian model (majority baseline, image-only, text-only, fusion MTL)
untuk ketiga task, evaluasi dengan stratified 5-fold cross-validation
(stratifikasi memakai Task 1). Hasil disimpan ke
`04_hasil_eksperimen/hasil_mtl_740_task2domain.json` dan
`analisis_recall_per_kelas_740.csv`.

**3. Analisis XAI: Grad-CAM + zona dominan (± 1 menit)**

```bash
venv/bin/python 01_notebook/run_xai_analysis.py
```
```bat
venv\Scripts\python 01_notebook\run_xai_analysis.py
```

Menghitung Grad-CAM (adaptasi ViT) untuk 25 sampul pertama secara
leave-one-out (model dilatih ulang tanpa sampul yang diuji), menentukan zona
mana yang paling memengaruhi keputusan, lalu menjalankan uji leave-one-out
pada 7 sampul contoh (satu per domain Task 2 yang unik). Hasil disimpan ke
`04_hasil_eksperimen/analisis_zona_740.json` dan
`hasil_uji_satu_gambar_740.json`.

**Catatan:** ketiga script memakai path Python absolut yang ditulis untuk
struktur folder paket ini (lihat variabel `ROOT` di awal tiap script) —
berjalan sama di Windows maupun Linux/macOS selama struktur folder tidak
diubah. Ketiganya juga memakai `torch.manual_seed(42)` di titik yang sama
persis dengan notebook asli, sehingga hasil deterministik dan dapat
direproduksi.

---

## Bagian C — Notebook asli (referensi metodologi)

`01_notebook/DEMO_XAI_TEMPO.ipynb` adalah notebook asli yang dipakai untuk
dataset 189 sampul. Notebook ini **tidak dijalankan ulang untuk 740 sampul**
karena alasan waktu — logikanya sudah direplikasi persis di tiga script
Python pada Bagian B (fungsi `latih`, `grad_cam`, `zona_dominan`, dan
parameter pelatihan identik). Notebook tetap berguna sebagai dokumentasi
metodologi langkah-demi-langkah dan untuk pembaca yang ingin menelusuri alur
sel demi sel pada dataset 189 sampul yang lebih kecil.

Bila ingin menjalankan notebook pada dataset 740 sampul, ubah pada bagian
konfigurasi path:

```python
DATA_CSV = AKAR / "03_data" / "DATASET_740_TASK2_DOMAIN.csv"
FITUR_NPZ = AKAR / "03_data" / "fitur_clip_indobert_740.npz"
```

Sisanya berjalan tanpa perubahan karena skema kolom identik dengan dataset
189 sampul.

---

## Bagian D — Cara membaca hasilnya

Sama seperti demo 189 sampul: setiap analisis menghasilkan empat bagian
(prediksi tiga task, Grad-CAM, kontribusi kata, penjelasan naratif berlabel
asal MODEL/ANOTATOR/CODEBOOK/GABUNGAN). Rincian cara membaca ada di
`02_BATASAN_TEKNIS.md`.

---

## Bagian E — Bila menemui masalah

**"Berkas tidak ditemukan"**
Pastikan struktur folder tidak dipindah — `xai_core.py` memakai path relatif
terhadap lokasi paket.

**PyTorch gagal dipasang**
Periksa versi Python. Harus 3.10 atau 3.11.

**Unduhan model gagal atau lambat**
CLIP dan IndoBERT diunduh dari internet saat pertama kali dipakai (sekitar
1,5 GB total). Setelah terunduh, tersimpan di cache Hugging Face
(`~/.cache/huggingface`) dan tidak diunduh ulang.

**Peta panas tidak muncul**
Bila fungsi Grad-CAM mengembalikan `None`, berarti gradien bernilai nol.
Penjelasannya ada pada `02_BATASAN_TEKNIS.md` bagian 1.
