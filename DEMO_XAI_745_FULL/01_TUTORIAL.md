> Acuan delivery terbaru: [DELIVERY.md](DELIVERY.md). Dokumen ini memuat konteks historis; identitas model utama sekarang CLIP–IndoBERT MTL tiga task.

> Catatan 2026-10-06: tutorial ini disesuaikan dengan tampilan aplikasi terbaru
> (paket delivery revisi Week 3, model baseline). Status revisi terbaru ada di
> [docs/STATUS_REVISI_20261006.md](docs/STATUS_REVISI_20261006.md); bukti
> Week 3 ada di [docs/DELIVERY_WEEK_3.md](docs/DELIVERY_WEEK_3.md).

# Tutorial — langkah demi langkah (dataset 740 sampul)

---

## Bagian A — Menjalankan aplikasi web (paling cepat, sudah diuji jalan)

**Syarat: Python 3.10 atau 3.11.** Python 3.12 ke atas belum tentu didukung
PyTorch.

**Cara singkat:** setelah environment dan pustaka terpasang (langkah 1–2 di
bawah), aplikasi bisa dinyalakan dengan launcher di folder paket:
`./jalankan_linux.sh` (Linux/macOS) atau klik dua kali `jalankan_windows.bat`
(Windows). Keduanya membuka server di http://127.0.0.1:7860. Langkah 3 di
bawah adalah cara manual yang setara.

**Pertama kali dijalankan**, aplikasi mengunduh model CLIP, IndoBERT, dan
EasyOCR dari internet. Ini hanya terjadi sekali; pastikan koneksi internet dan
ruang disk cukup, dan jangan tutup terminal selama unduhan berjalan.

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

Untuk versi pustaka persis yang lulus semua test di server Linux, pakai
`requirements-lock-linux.txt` (perintahnya ada di `MULAI_DARI_SINI.md`).

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
venv\Scripts\python -m pip install -r 02_web_demo\requirements-web-lock.txt
```

**3. Jalankan**

```bat
jalankan_windows.bat
```

Buka http://127.0.0.1:7860 di browser. Launcher memeriksa lima checkpoint dan
mereplay 740 prediksi E42 sebelum server dimulai. Cara termudah adalah menjalankan
`setup_windows.bat` sekali, lalu klik dua kali `jalankan_windows.bat`.

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

## Bagian B — Memakai aplikasi

Aplikasi ini adalah prototipe penelitian dengan model **E42** (CLIP-L14 +
IndoBERT + tail multi-task lima outer-fold). Hasilnya membantu pemeriksaan,
bukan keputusan akhir.

### B.1 Navigasi

Di bagian atas ada tiga menu:

| Menu | Isi |
|---|---|
| **Analisis** | Menganalisis satu sampul dan melihat prediksi beserta buktinya |
| **Batch** | Menganalisis banyak sampul sekaligus, lalu mengekspor hasilnya |
| **Panduan** | Arti tiga task, katalog kelas, dan keterangan model baseline |

### B.2 Analisis satu sampul

Isi panel **"Mulai di sini"** dari atas ke bawah. Gambar yang dipilih tampil
di panel **"Sampul pilihan"** sebagai pratinjau.

Pertama, pilih mode di panel "Mulai di sini":

- **Dataset** — memakai salah satu dari 740 sampul yang sudah dianotasi.
  Sampul yang dipilih dikeluarkan dari data latih (*leave-one-out*), jadi
  model belum pernah melihatnya, dan prediksinya bisa dibandingkan dengan
  label anotator.
- **Unggah gambar** — memakai gambar sampul sendiri. Model dilatih pada
  seluruh 740 sampul. Tidak ada label pembanding untuk gambar unggahan.

Lalu ikuti tiga langkah:

1. **"1. Pilih sampul dari dataset"** (mode Dataset) atau **"1. Pilih gambar
   dari laptop"** (mode Unggah gambar).
2. **"2. Periksa judul utama"** — samakan isi kolom dengan judul besar pada
   sampul. Klik kolom untuk memperbaiki. Teks inilah yang dibaca model, jadi
   langkah ini penting.
   Di bawahnya ada kolom **"Teks pendukung (boleh kosong)"**: kotak lima baris
   yang bisa diperbesar. Teks panjang dan beberapa baris boleh dimasukkan.
3. **"3. Pilih penjelasan yang ingin dilihat"** — pilih satu dari:
   - **Ranah metafora (Task 2)** — pilihan bawaan
   - **Topik utama (Task 1)**
   - **Pihak yang disorot (Task 3)**

   Pilihan ini menentukan task mana yang dijelaskan secara rinci (bukti kata,
   bukti task pilihan, dan penjelasan). Prediksi tetap dibuat untuk ketiga
   task.

Terakhir, klik **Analisis sampul**.

**Batas masukan:** judul paling panjang 300 karakter dan teks pendukung 2000
karakter. Gambar unggahan paling besar 25 MB; gambar dengan sisi lebih dari
8000 px, rasio sisi lebih dari 5:1, atau lebih dari 40 megapiksel ditolak.
Gambar besar diperkecil ke sisi terpanjang 2000 px sebelum diproses.

### B.3 Pembacaan teks otomatis (OCR) pada gambar unggahan

Begitu gambar unggahan dipilih, aplikasi langsung membaca teks pada gambar.
Selama proses ini muncul tulisan **"Sedang membaca teks gambar"**. Hasilnya
mengisi kolom judul utama dan teks pendukung.

Pembacaan otomatis **tidak selalu tepat** (lihat Bagian F). Karena itu:

- Periksa kolom judul utama dan perbaiki langsung bila ada huruf yang salah.
- Bila muncul daftar **"Pilihan judul hasil pembacaan otomatis"**, kamu bisa
  memilih kandidat lain yang lebih cocok dengan judul di sampul, lalu tetap
  memeriksanya.
- Bila tidak ada teks yang menyerupai judul, isi judul secara manual.
- Bila kamu mengganti gambar, judul dan teks pendukung **diganti** dengan hasil
  pembacaan gambar baru — termasuk teks yang sudah kamu sunting untuk gambar
  sebelumnya. Teks yang kamu ketik selama pembacaan gambar baru berjalan tidak
  ditimpa. Memilih berkas yang sama lagi juga memicu pembacaan ulang. Nama
  gambar yang sedang dipakai tampil di bawah tombol pilih berkas sebagai
  **"Gambar aktif: …"**.

### B.4 Saat analisis berjalan

Selama analisis, muncul layar **"Sedang menganalisis sampul"** dan tombol
berubah menjadi **"Menganalisis…"**. Hasil tampil otomatis setelah selesai.

Analisis satu sampul memakai LIME untuk atribusi kata, sekitar **15–20 detik
per analisis di CPU server** uji. Di komputer lain waktunya bisa berbeda.

Bila kamu mengganti sampul, teks, atau pilihan penjelasan saat analisis masih
berjalan, analisis lama dibatalkan dan hasilnya tidak ditampilkan. Pembatalan
juga dikirim ke server, sehingga analisis baru tidak perlu menunggu analisis
lama selesai. Klik **Analisis sampul** lagi untuk input yang baru.

### B.5 Membaca lima tab hasil

| Tab | Yang dibaca |
|---|---|
| **Prediksi** | Kelas yang dipilih model untuk ketiga task, lalu **ringkasan interpretasi** berbahasa awam: isu, pihak yang disorot, jenis kiasan, tingkat keyakinan, dan (untuk sampul dataset) perbedaan dengan anotator. Ringkasan dirangkai dari prediksi dan catatan anotator — bukan ditulis model bahasa |
| **Bukti gambar** | Sampul asli berdampingan dengan peta panas. Area merah lebih berpengaruh pada prediksi. Ini bukan deteksi objek |
| **Bukti kata** | Kata yang mendukung atau melemahkan prediksi untuk task yang kamu pilih di langkah 3 |
| **Penjelasan** | Alasan untuk task pilihan: "Mengapa <kelas>?" (kata dan area gambar yang paling berpengaruh), "Arti kelas ini", "Catatan anotator" bila ada, lalu daftar **"Yang perlu dicek"**. Tiap blok diberi penanda asal **MODEL**, **ANOTATOR**, **CODEBOOK**, atau **GABUNGAN** |
| **Bandingkan label** | Untuk sampul dataset: prediksi dibandingkan dengan label anotator. Gambar unggahan tidak punya label pembanding |

Tab bisa dipindah dengan klik, atau dengan tombol panah, Home, dan End di
papan ketik.

**Tab Bukti gambar berisi dua jenis peta — bedakan keduanya:**

1. **Peta gabungan tiga task** (peta utama, di atas). Peta ini adalah
   rata-rata peta ketiga task yang sudah dinormalisasi. Hasilnya **sama**,
   apa pun penjelasan yang kamu pilih di langkah 3. Gunanya untuk melihat
   area gambar yang secara umum memengaruhi ketiga prediksi.
   Peta gabungan **bukan** dasar atribusi kata atau paragraf penjelasan.
2. **"Bukti task pilihan: <task> — kelas <kelas>"** (blok terpisah di
   bawahnya). Peta ini khusus untuk task yang kamu pilih di langkah 3, dan
   inilah yang menjadi dasar penjelasan serta analisis zona.

Peta per task untuk ketiga task tetap tersedia di bagian **"Lihat peta panas
per task (tampilan teknis)"**.

### B.6 Batch: banyak sampul sekaligus

Buka menu **Batch**, lalu **"Buka pengaturan batch"**.

1. Isi **"ID dataset, dipisahkan koma (opsional)"** — atau klik **"Tambahkan
   sampul pilihan"** untuk memasukkan sampul dataset yang sedang dipilih di
   menu Analisis — dan/atau pilih berkas di **"Gambar unggahan (opsional)"**.
2. Pilih **"Metode atribusi batch"**: **Occlusion (lebih cepat)**, pilihan
   bawaan, atau **LIME (lebih lambat)**.
   Lalu pilih **"Penjelasan (task) untuk batch"**. Awalnya pilihan ini
   mengikuti pilihan penjelasan (langkah 3) di menu Analisis, sampai kamu
   mengubahnya sendiri di view Batch.
3. Klik **Mulai batch**.
4. Gambar unggahan dibaca OCR lalu **menunggu konfirmasi**. Untuk setiap item
   unggahan, periksa dan perbaiki judul (serta teks pendukung), lalu klik
   **"Konfirmasi teks dan analisis"**.
5. Setelah item selesai, gunakan tautan **Unduh CSV** (ringkasan) atau
   **Unduh JSON** (hasil dan bukti lengkap). Tiap item yang berhasil juga
   punya tautan **"Buka peta gabungan tiga task"**.
6. Bila server sempat dimatikan atau ada item gagal, klik **"Lanjutkan job
   terakhir / ulang item gagal"**. Item yang sudah berhasil dipertahankan.
   Bila semua item gagal, status job menjadi `failed`.

Paling banyak 2 job batch boleh berjalan/antre sekaligus; job ketiga ditolak
sampai salah satunya selesai.

**Penting:** batch untuk sampul dataset memakai model yang dilatih pada
seluruh korpus, jadi hasilnya eksplorasi **in-sample** — bukan
*leave-one-out* dan **bukan metrik akurasi**. Jangan membandingkannya dengan
hasil analisis satu sampul sebagai ukuran ketepatan model.

### B.7 Panduan

Menu **Panduan** berisi arti tiga task dan **katalog 25 kelas** (10 kelas
isu untuk Task 1, 7 domain sumber metafora untuk Task 2, 8 tipe entitas untuk
Task 3), lengkap dengan definisinya. Definisi ini berasal dari codebook
operasional yang disusun untuk proyek ini atas instruksi pengguna; label tetap
berasal dari dataset. Di menu yang sama ada keterangan model baseline dan
hasil evaluasinya.

---

## Bagian C — Menjalankan ulang eksperimen dari nol

Tiga script di `01_notebook/` mereplikasi alur notebook demo pada dataset 740
sampul. Jalankan berurutan.

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

## Bagian D — Notebook (referensi metodologi)

`01_notebook/DEMO_XAI_TEMPO.ipynb` menjalankan alur yang sama dengan tiga
script di Bagian C, sel demi sel, lengkap dengan penjelasan. Sejak
29 September 2026 notebook ini sudah diarahkan ke dataset 740 sampul
(`DATASET_740_TASK2_DOMAIN.csv` dan `fitur_clip_indobert_740.npz`), jadi
tidak perlu mengubah path. Jalankan ekstraksi fitur (Bagian C langkah 1)
lebih dulu bila berkas fitur belum ada. Teks notebook dimutakhirkan 6 Oktober 2026: sel
pertama memuat blok "Pembaruan 6 Oktober" yang menjelaskan beda notebook
(referensi metodologi baseline, atribusi occlusion) dengan aplikasi (LIME baku,
peta gabungan tiga task, ringkasan/penjelasan baru, OCR).

Notebook berguna untuk pembaca yang ingin menelusuri metodologi langkah demi
langkah; untuk menjalankan ulang eksperimen, tiga script di Bagian C sudah
cukup.

---

## Bagian E — Cara membaca hasilnya

Setiap analisis satu sampul menampilkan lima tab (rincian di Bagian B.5):

1. **Prediksi** — kelas tiga task dan ringkasan awam ketiganya.
2. **Bukti gambar** — peta gabungan tiga task sebagai peta utama, lalu blok
   "Bukti task pilihan" untuk task yang dipilih. Yang menjadi dasar
   penjelasan dan analisis zona adalah peta task pilihan, bukan peta
   gabungan.
3. **Bukti kata** — kata yang mendukung atau melemahkan prediksi (LIME pada
   analisis satu sampul; di batch bisa memakai occlusion yang lebih cepat).
4. **Penjelasan** — alasan untuk task pilihan, dirangkai dari bukti (bukan
   model bahasa), dengan penanda asal dan daftar "Yang perlu dicek".
5. **Bandingkan label** — perbandingan dengan label anotator (hanya untuk
   sampul dataset).

Batasan yang perlu diketahui sebelum menyimpulkan apa pun ada di
`02_BATASAN_TEKNIS.md`.

---

## Bagian F — Bila menemui masalah

**"Berkas tidak ditemukan"**
Pastikan struktur folder tidak dipindah — `xai_core.py` memakai path relatif
terhadap lokasi paket.

**PyTorch gagal dipasang**
Periksa versi Python. Harus 3.10 atau 3.11.

**Unduhan model gagal atau lambat**
CLIP, IndoBERT, dan EasyOCR diunduh dari internet saat pertama kali dipakai
(sekitar 1,5 GB total). Setelah terunduh, model tersimpan di cache (CLIP dan
IndoBERT di `~/.cache/huggingface`) dan tidak diunduh ulang.

**Judul hasil pembacaan otomatis salah**
Ini wajar. Pembacaan otomatis (OCR) pada sampul majalah terbatas. Dengan
versi aplikasi terakhir, judul terbaca tepat 68–78% pada dua set validasi 60
sampul (angka ini cenderung optimistis karena kedua set ikut dipakai saat
perbaikan; angka saat kode dibekukan 63–72%, lihat
`docs/AUDIT_OCR_URUTAN_20261006.md`). Pada tiga foto sampul dari dosen, 2 dari
3 judul tepat (judul WASWAS, misalnya, terbaca `VJASWAS RUPIAH` di server
uji). Sasaran 80% masih usulan dan belum tercapai. Selalu periksa kolom judul utama, perbaiki secara manual
atau pilih kandidat lain dari daftar "Pilihan judul hasil pembacaan
otomatis", lalu baru klik **Analisis sampul**.

**Peta panas tidak muncul**
Bila fungsi Grad-CAM mengembalikan `None`, berarti gradien bernilai nol.
Penjelasannya ada pada `02_BATASAN_TEKNIS.md` bagian 1.
