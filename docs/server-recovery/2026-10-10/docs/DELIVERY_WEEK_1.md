# Laporan Minggu 1 — Demo XAI Dekoding Metafora Sampul Tempo

> **Dokumen riwayat: laporan Minggu 1 per 22 September 2026.** Status terbaru: [STATUS_REVISI_20261006.md](STATUS_REVISI_20261006.md) (6 Oktober 2026). Ringkasan koreksi status bertanggal 6 Okt ada tepat di bawah catatan ini.
>
> **Koreksi status 6 Okt** (isi laporan di bawah tidak diubah; path bukti relatif terhadap `04_hasil_eksperimen/revisi_week3/`.)
> - **R1** ("Selesai" di bawah): per 6 Okt berstatus *diterapkan, kualitas terbatas*. Judul tepat 68–78% pada dua set validasi audit OCR 6 Okt untuk versi aplikasi terakhir (cenderung optimistis; 63–72% saat kode dibekukan); sasaran usulan 80% belum tercapai, jadi koreksi manual wajib ([AUDIT_OCR_URUTAN_20261006.md](AUDIT_OCR_URUTAN_20261006.md)).
> - **R5** ("Selesai" di bawah): pada 5 Okt tampilan utama sempat diubah menjadi peta task pilihan, dan audit 6 Okt pagi mencatatnya belum sesuai permintaan dosen. Ditutup lagi 6 Okt: peta utama = peta gabungan tiga task, peta task pilihan tampil sebagai blok terpisah "Bukti task pilihan" (`01_notebook/test_r5_heatmap.js`, `r5_heatmap_verification.json`).
> - **Ganti gambar** (bagian 5, "teks yang diketik pengguna dipertahankan"): sejak 6 Okt gambar baru selalu mengganti judul dan teks pendukung dengan hasil gambar baru; ketikan selama OCR gambar yang sama tetap dilindungi (`browser_smoke_20261006_judul.json`).
> - **Atribusi kata:** occlusion yang disebut di laporan ini diganti LIME sebagai metode baku analisis satuan sejak Minggu 2; occlusion dipakai untuk batch.
> - **Cara menjalankan:** gunakan panduan paket 6 Okt di [../00_BACA_DULU.md](../00_BACA_DULU.md) dan [../MULAI_DARI_SINI.md](../MULAI_DARI_SINI.md). Instalasi bersih paket diuji di Linux; Windows belum diuji.

**Periode:** 22 September 2026
**Deadline keseluruhan:** 12 Oktober 2026
**Status:** Minggu 1 selesai (3 dari 5 revisi tertutup)

**Judul penelitian:** Eksperimen Multi-Task Learning CLIP-IndoBERT Berbasis XAI
untuk Dekoding Metafora Sampul Majalah Tempo

---

## Daftar isi

1. [Untuk pembaca baru — apa ini sebenarnya](#1-untuk-pembaca-baru)
2. [Cara menjalankan (Windows & Linux)](#2-cara-menjalankan)
3. [Revisi dosen dan status penyelesaiannya](#3-revisi-dosen)
4. [Yang dikerjakan Minggu 1, rinci](#4-yang-dikerjakan-minggu-1)
5. [Bug yang ditemukan dan diperbaiki](#5-bug-yang-ditemukan)
6. [Bukti dan angka](#6-bukti-dan-angka)
7. [Rancangan Minggu 2 dan 3](#7-rancangan-minggu-2-dan-3)
8. [Batasan yang harus diketahui](#8-batasan)
9. [Keputusan yang sudah diambil](#9-keputusan-yang-sudah-diambil)
10. [Berkas penting](#10-berkas-penting)

---

## 1. Untuk pembaca baru

### Apa yang dilakukan sistem ini

Diberi sebuah sampul Majalah Tempo, sistem memprediksi tiga hal sekaligus,
lalu **menjelaskan dasar keputusannya**.

| Task | Pertanyaan yang dijawab | Jumlah kelas |
|---|---|---|
| Task 1 | Isu apa yang dibahas sampul ini? | 10 |
| Task 2 | Kiasan dari ranah apa yang dipakai? | 7 |
| Task 3 | Siapa yang dikritik? | 8 |

Bagian **XAI** (*Explainable AI*) itulah inti penelitiannya: sistem tidak
hanya menebak, tetapi menunjukkan area gambar mana dan kata mana yang
memengaruhi keputusannya.

### Cara kerjanya

```
Sampul  ──┬─→ CLIP (gambar)    ─→ 512 angka ─┐
          │                                   ├─→ digabung (1280) ─→ MTL Head ─┬─→ Task 1
          └─→ IndoBERT (teks)  ─→ 768 angka ─┘                                 ├─→ Task 2
                                                                               └─→ Task 3
                                          │
                                          └─→ XAI: Grad-CAM + atribusi kata
```

- **CLIP** dan **IndoBERT** hanya dipakai untuk mengubah gambar dan teks jadi
  angka. Keduanya **dibekukan** — tidak ikut dilatih.
- Yang dilatih hanya **MTL Head**: jaringan kecil `1280 → 256 → 3 keluaran`.
- **Multi-Task Learning** berarti ketiga task berbagi satu lapisan tengah,
  sehingga saling membantu meski datanya terbatas.

### Dua mode pemakaian

| | Pilih dari dataset | Unggah gambar sendiri |
|---|---|---|
| Asal gambar | 740 sampul yang sudah dianotasi | Sampul apa pun |
| Cara melatih | *Leave-one-out* — sampul uji dikeluarkan dari data latih | Seluruh 740 sampul |
| Ada jawaban benar? | Ya, bisa dibandingkan | Tidak |
| Kegunaan | Menguji kejujuran model | Memproses sampul baru |

*Leave-one-out* penting: model belum pernah melihat sampul yang sedang diuji,
jadi prediksinya jujur, bukan hafalan.

---

## 2. Cara menjalankan

### Syarat

- **Python 3.10 atau 3.11** — versi 3.12 ke atas **tidak bisa**, PyTorch belum
  mendukungnya
- RAM minimal 8 GB (disarankan 16 GB)
- Ruang kosong ±4 GB (model yang diunduh ±1,5 GB)
- Internet saat pertama kali dijalankan

### Windows — cara termudah

1. **Pasang Python 3.10** dari
   <https://www.python.org/downloads/release/python-31011/>

   Saat memasang, **centang dua opsi ini**:
   - `Add Python to PATH`
   - `py launcher`

2. **Klik dua kali `setup_windows.bat`** — cukup sekali.
   Skrip ini mencari Python yang tepat, membuat folder `venv`, dan memasang
   semua pustaka. Perlu 10–30 menit tergantung kecepatan internet.

3. **Klik dua kali `jalankan_windows.bat`**

4. Tunggu sampai muncul `Running on http://127.0.0.1:7860`, lalu buka alamat
   itu di peramban.

> **Saat pertama kali dijalankan**, aplikasi mengunduh model CLIP, IndoBERT,
> dan EasyOCR (±1,5 GB). Ini hanya sekali; setelahnya dibaca dari cache.
> Jangan tutup jendela saat proses unduh berlangsung.

**Mematikan:** tekan `Ctrl+C` di jendela hitam, atau tutup jendelanya.

### Windows — cara manual

Bila skrip `.bat` gagal, jalankan dari Command Prompt di folder paket:

```bat
py -3.10 -m venv venv
venv\Scripts\python -m pip install --upgrade pip
venv\Scripts\pip install --extra-index-url https://download.pytorch.org/whl/cpu torch torchvision
venv\Scripts\pip install -r requirements.txt

cd 02_web_demo
..\venv\Scripts\python app.py
```

### Linux / macOS

```bash
python3.10 -m venv venv
venv/bin/pip install --upgrade pip
venv/bin/pip install --extra-index-url https://download.pytorch.org/whl/cpu torch torchvision
venv/bin/pip install -r requirements.txt

./jalankan_linux.sh
```

### Bila ada masalah

| Gejala | Penyebab & solusi |
|---|---|
| `py bukan perintah yang dikenali` | Python belum terpasang, atau `py launcher` tidak dicentang. Pasang ulang Python 3.10 |
| `Python 3.10/3.11 tidak ditemukan` | Versi Python salah. Cek dengan `python --version` |
| Galat *"long path"* saat memasang | Pindahkan folder ke path pendek, misal `C:\demo_xai`, lalu ulangi |
| Pemasangan sangat lambat | Antivirus memindai paket besar. Normal, tunggu saja |
| `Address already in use` / port dipakai | Server lain masih jalan. Tutup jendela lamanya |
| Peta panas tidak muncul | Gradien bernilai nol pada sampul itu. Lihat `02_BATASAN_TEKNIS.md` bagian 1 |
| Analisis terasa lambat (10–40 detik) | Wajar. Model dilatih ulang tiap analisis mode dataset |

---

## 3. Revisi dosen

Dosen memberi lima butir revisi pada 15 September (`revision.pdf`, 32 halaman
— isi nyatanya halaman 1–7).

| Kode | Permintaan | Status |
|---|---|---|
| **R1** | Teks sampul terisi otomatis, user tidak mengetik ulang | **Selesai** |
| **R2** | Nama kelas ditampilkan dengan istilah mudah dipahami | **Selesai** |
| **R3** | Paragraf kesimpulan berbahasa awam di akhir | Minggu 2 |
| **R4** | Atribusi kata tidak masuk akal (LIME) | Minggu 2 |
| **R5** | Satu peta panas terpadu, bukan tiga terpisah | **Selesai** |

Catatan dosen: *"Ga harus mingdep selesai semua."*

### Kutipan asli dan tafsirannya

**R1** — *"user masih harus ngeinput ulang tuh teks, nah disaranin kalo bisa
itu kesalin otomatis karena user ga bakalan punya waktu buat ngetik ulang"*,
dengan arahan *"pake ocr => berbasis trm base => hf"* dan izin
*"kalo bisa pake yang lain sihlakan"*.

**R2** — Dosen melingkari merah tulisan `KONSUMSI_TRANSAKSI` di layar, lalu
menulis *"semua nama kelas jangan kaku jadi bisa di ganti atau rename
**(bukan di dataset)** saat di tampilkan dengan istilah lebih mudah di
pahami"*. Penegasan "bukan di dataset" dipatuhi: dataset tidak disentuh sama
sekali.

**R3** — *"Penjelasanya jelas which is good tapi terlalu teknikal buat user,
jadi di minta suatu kesimpulan akhir di mana hanya ada paragraf dan mudah di
pahami user apa yang sebenarnya pesan tersirat yang coba di sampaikan oleh
sampul itu"*. Dosen juga melaporkan badge ungu `GABUNGAN` tidak pernah muncul.

**R4** — Pada sampul "GULA-GULA DEMO BURUH", semua kata bernilai negatif.
Dosen menilai *"Yang fatal demo, padahal gambar jelas menunjukan aksi demo"*.

**R5** — *"Heatmap dari task 1, 2 dan 3 dapat di lihat berbeda-beda, gpp kalo
teknikal namun pas ke user nanti di minta hanya satu dan sama dan itu harus
mencakup semua"*.

---

## 4. Yang dikerjakan Minggu 1

### R1 — Pembacaan teks sampul otomatis

**Masalah:** Untuk setiap sampul, pengguna harus mengetik ulang judul dan
teks pendukung. Untuk ratusan sampul, itu tidak masuk akal.

**Yang dibangun:** modul `02_web_demo/ocr_headline.py`. Begitu berkas gambar
dipilih, teks dibaca otomatis dan mengisi kedua kolom — tetap bisa disunting.

**Mengapa EasyOCR, bukan TrOCR seperti saran dosen:**

Dilakukan uji banding pada 20 sampul asli, memakai kolom `headline_verified`
sebagai jawaban benar (skrip: `01_notebook/uji_banding_ocr.py`).

| Pendekatan | F1 | Presisi | Keterangan |
|---|---|---|---|
| OCR mentah (semua teks) | 0,204 | 0,119 | Judul tertangkap, tapi tenggelam di antara teks lain |
| + pemilihan judul | 0,684 | 0,717 | Memilih blok teks terbesar |
| + penyaringan logo | 0,804 | 0,824 | Logo TEMPO tidak lagi terpilih |
| **+ skor gabungan** | **0,895** | **0,960** | **Dipakai sekarang** |

Hasil akhir: **14 dari 20 sampul terbaca sempurna, 0 gagal total.**

**Alasan metodologis** (lebih kuat daripada angka): TrOCR dirancang untuk
**satu baris teks**, bukan gambar dengan banyak blok teks tersebar. Ia tidak
memberi informasi posisi dan ukuran huruf — padahal justru informasi itulah
yang dipakai membedakan judul dari teks lain, dan yang menaikkan F1 dari
0,204 ke 0,895.

Dosen mengizinkan alternatif. Rincian lengkap: `docs/2026-09-22-keputusan-ocr.md`.

### R2 — Istilah yang mudah dipahami

**Yang dibangun:** `02_web_demo/label_display.py` memetakan seluruh 25 nama
kelas teknis ke istilah Indonesia yang wajar.

| Sebelum | Sesudah |
|---|---|
| `KONSUMSI_TRANSAKSI` | Konsumsi & Transaksi |
| `corruption_and_bribery` | Korupsi & Suap |
| `judiciary_or_law_enforcement` | Peradilan & Penegak Hukum |
| `multiple_or_other` | Beberapa Pihak / Lainnya |

**Dataset tidak diubah sama sekali** — tetap 740 baris, 15 kolom, 7 kelas
Task 2, sesuai penegasan dosen. Nama teknis tetap ditampilkan kecil di bawah
istilah awam, supaya masih bisa dicocokkan dengan tabel hasil eksperimen.

Bila suatu saat ada kelas baru yang belum terdaftar, sistem tidak error —
nama teknisnya dirapikan otomatis.

### R5 — Peta panas terpadu

**Masalah:** Tiap task menghasilkan peta panas sendiri, jadi pengguna melihat
tiga gambar berbeda dan bingung mana yang benar.

**Yang dibangun:** fungsi `gradcam_terpadu()` di `xai_core.py`. Ketiga peta
dirata-ratakan setelah masing-masing dinormalisasi — normalisasi penting agar
tidak ada task yang mendominasi hanya karena gradiennya kebetulan besar.

Tampilan sekarang: **satu peta gabungan** sebagai gambar utama, dan tiga peta
per task disembunyikan di panel lipat *"Lihat peta panas per task (tampilan
teknis)"*. Sesuai permintaan dosen: teknis boleh ada, tapi pengguna cukup
melihat satu.

### Dokumen yang dilengkapi

`02_BATASAN_TEKNIS.md` dirujuk dua kali di tutorial tetapi **tidak ada** di
paket. Sekarang ditulis, berisi sembilan bagian: metode Grad-CAM yang dipakai,
batasan atribusi kata, temuan model bertumpu pada logo, performa per kelas,
sifat penjelasan naratif, perbedaan dua mode, batasan dataset,
reproduksibilitas, dan daftar yang belum dikerjakan.

---

## 5. Bug yang ditemukan

Sebagian ditemukan saat menelusuri revisi, sebagian saat uji coba.

### Dilaporkan dosen

| Bug | Penyebab | Perbaikan |
|---|---|---|
| Angka tertulis `+-0.023` | Tanda `+` ditulis permanen di kode | Format tanda otomatis |
| Kata bernilai negatif disebut "paling menopang" | Logika tidak memeriksa tanda | Bila semua negatif, dinyatakan terus terang tidak ada kata yang menopang |
| Badge `GABUNGAN` tidak pernah muncul | Mode unggahan mengirim catatan kosong, blok dilewati | Blok tetap tampil, isinya menyesuaikan |

### Ditemukan saat pemeriksaan kode

| Bug | Dampak |
|---|---|
| 83 sampul NON_METAFORA punya nilai kosong terbaca sebagai teks `"nan"` | Sampul tanpa metafora seolah punya catatan anotator |
| Antarmuka masih menampilkan angka dataset lama (189 sampul, F1 0,174) di 5 tempat | Pembaca melihat angka yang salah |
| Celah keamanan path traversal pada dua alamat | Berkas di luar folder cache bisa diakses |

### Ditemukan saat uji coba pengguna

**Judul terbaca "TEN" pada sampul "ANCANG-ANCANG JOKOWI".** Yang terambil
ternyata sisa logo TEMPO — huruf M dan P tertutup kepala pada foto. Empat
cacat sekaligus: pola penyaringan logo terlalu kaku, pemilihan hanya memakai
tinggi teks, keyakinan OCR tidak dipakai, dan posisi diabaikan. Diperbaiki
dengan skor gabungan (tinggi × posisi × keyakinan × penalti panjang).

**Sistem tetap menampilkan "43,4%" untuk judul yang rusak.** Ini yang paling
serius: angka yang tampak meyakinkan di atas masukan yang salah lebih
menyesatkan daripada tidak ada angka. Sekarang muncul peringatan bila judul
kurang dari dua kata.

**Mengganti gambar tidak memperbarui teks.** Kolom hanya diisi bila kosong,
sehingga teks dari gambar sebelumnya tertinggal. Sekarang sistem membedakan
teks hasil OCR (boleh ditimpa) dari teks yang diketik pengguna (dipertahankan).
Ditemukan pula tiga cacat serupa: teks lama tertinggal saat OCR gagal, jawaban
OCR terlambat menimpa hasil yang lebih baru, dan berpindah tab meninggalkan
sisa unggahan.

### Ditemukan saat menyiapkan versi Windows

**Folder cache tidak pernah dibersihkan.** Tiap analisis menyimpan sampai
empat berkas PNG; memproses ratusan sampul akan menumpuk ratusan megabita.
Sekarang hanya 400 berkas terbaru yang disimpan.

**Dokumen merujuk path yang tidak ada** (`../../demo_xai/venv/bin/python`).
Pembaca baru akan gagal di langkah pertama.

---

## 6. Bukti dan angka

### Performa model (tidak berubah Minggu 1)

Hasil *5-fold cross-validation* pada 740 sampul:

| Task | Akurasi | Macro-F1 | Baseline |
|---|---|---|---|
| Isu utama | 0,455 | 0,438 | 0,036 |
| Domain kiasan | 0,320 | 0,320 | 0,064 |
| Sasaran kritik | 0,355 | 0,276 | 0,075 |

Semua jauh di atas baseline — model memang mempelajari sesuatu. Tetapi
Macro-F1 0,28–0,44 **belum layak dipakai sebagai alat putus**.

### Temuan XAI terpenting

Dari 25 sampul yang dianalisis:

| Zona sampul | Intensitas rata-rata | Dominan pada |
|---|---|---|
| Kepala (logo, judul kecil) | 0,180 | **22 dari 25** |
| Tengah (ilustrasi) | 0,086 | 2 dari 25 |
| Kaki (judul besar, barcode) | 0,060 | 1 dari 25 |

**Model lebih bertumpu pada logo dan teks tercetak daripada ilustrasi
metaforanya.** Prediksi yang benar belum tentu karena alasan yang benar.

Temuan ini konsisten dengan versi dataset sebelumnya (189 sampul: 19 dari 25)
dan **menguat** setelah data bertambah hampir empat kali lipat — jadi bukan
akibat data kecil.

Justru inilah yang membuat XAI berharga: tanpa peta panas, kelemahan ini tidak
akan terlihat dari angka akurasi saja.

### Verifikasi yang dijalankan

| Yang diuji | Hasil |
|---|---|
| Server menyala, memuat 740 sampul | Berhasil |
| Mode dataset (leave-one-out) | 5 blok penjelasan lengkap |
| Mode unggahan | Badge `GABUNGAN` muncul — sebelumnya tidak pernah |
| Sampul NON_METAFORA | Blok anotator benar tidak muncul, teks `"nan"` tidak bocor |
| Peta panas terpadu + 3 per task | Keempat berkas dihasilkan dan tersaji |
| Penjagaan path traversal | Tiga upaya ditolak |
| Logika OCR saat ganti gambar | 6 skenario diuji, semua lolos |
| Pembersihan cache | 465 berkas → 400 |

---

## 7. Rancangan Minggu 2 dan 3

### Minggu 2 (29 September – 5 Oktober)

Bagian paling berisiko sengaja ditaruh di tengah, bukan di akhir, supaya masih
ada waktu penyangga.

**Hari 8–11 — R4: LIME sungguhan**

Masalah yang dilaporkan dosen: pada sampul "GULA-GULA DEMO BURUH", semua kata
bernilai negatif (GULA-GULA −0,023, DEMO −0,087, BURUH −0,089). Dosen menilai
fatal karena gambar jelas menunjukkan aksi demo.

Metode sekarang adalah *occlusion* sederhana — hapus satu kata, ukur
perubahan. Akan diganti LIME dengan model *surrogate*, yang juga menutup celah
antara diagram rancangan (menjanjikan LIME) dan implementasi.

**Titik keputusan di hari 11:** bila LIME tidak memperbaiki, beralih ke
rencana cadangan — laporkan sebagai batasan dengan bukti dua metode sudah
diuji. Untuk skripsi berbasis XAI, itu hasil yang sah.

**Hari 12–14 — R3: paragraf kesimpulan awam**

Menjawab permintaan dosen: paragraf yang menjelaskan *konteks* sampul dalam
bahasa awam.

Strateginya **merangkai, bukan menggenerasi** — sama seperti penjelasan yang
sudah ada. Empat bagian:

| Bagian | Sumber |
|---|---|
| Apa yang dibicarakan | Task 1 + judul |
| Siapa yang disorot | Task 3 |
| Cara menyampaikannya | Task 2 + definisi codebook |
| Seberapa kuat dasarnya | Probabilitas + kata dominan + zona |

Untuk sampul dataset, bagian ketiga diganti catatan anotator yang jauh lebih
kaya, dan diberi label ANOTATOR.

### Minggu 3 (6–12 Oktober)

**Hari 15–17 — pemrosesan banyak sampul sekaligus**

Dosen berencana mengirim seluruh sampul. Akan dibuat mode unggah banyak berkas
plus ekspor hasil (CSV/JSON) agar bisa ditelaah luring.

Catatan metodologis penting: mode batch **tidak memakai leave-one-out**. Mode
dataset sekarang melatih ulang model untuk tiap sampul — untuk 740 sampul
berarti 740 kali pelatihan, tidak masuk akal. Batch akan memakai satu model
terlatih penuh. Perbedaan ini harus ditulis jujur karena hasilnya tidak
sebanding langsung dengan angka leave-one-out.

**Hari 18–19 — pengujian menyeluruh**, termasuk kasus batas: OCR gagal, gambar
rusak, judul kosong, peta panas tidak terbentuk.

**Hari 20–21 — dokumentasi akhir**, termasuk bagian Batasan dan pemetaan tiap
revisi ke implementasinya sebagai bukti.

---

## 8. Batasan

Ditulis terus terang karena menyembunyikannya akan lebih merugikan saat sidang.

### Model masih sering meleset

Macro-F1 Task 2 = 0,320 berarti **sekitar 2 dari 3 tebakan domain kiasan
meleset**. Sistem ini alat bantu analisis, bukan alat putus.

### Model bertumpu pada logo, bukan ilustrasi

22 dari 25 sampul. Belum diperbaiki — perbaikannya butuh memotong area logo
lalu melatih ulang, yang mengubah semua angka di skripsi. Diputuskan untuk
dilaporkan sebagai temuan.

### "Grad-CAM" di sini bukan Grad-CAM CNN

Pada CLIP ViT, hanya token CLS yang dipakai untuk embedding akhir, sehingga
gradien token patch di blok terakhir bernilai nol dan rumus Grad-CAM asli
menghasilkan peta kosong. Yang dipakai adalah *Gradient × Activation* pada
blok kedua dari belakang. Harus disebut apa adanya di laporan.

### OCR tidak sempurna

5 dari 20 sampul judulnya terpotong sebagian (contoh: "PERANG BUBAT DI TANAH
JAWA" terbaca "PERANG BUBAT"). Huruf hias tebal masih sulit. Karena itu kolom
teks selalu dapat disunting, dan antarmuka menyatakan hal ini.

### Penjelasan kaku

Tidak ada teks yang dihasilkan model bahasa — setiap kalimat dirangkai dari
komponen yang asalnya dapat ditunjuk. Konsekuensinya penjelasan mengikuti
pola tetap dan tidak menyesuaikan keunikan tiap sampul.

### Anotasi satu orang

Tidak ada pengukuran kesepakatan antar-anotator, sehingga konsistensi label
tidak terukur.

---

## 9. Keputusan yang sudah diambil

Diputuskan 22 September 2026, mengunci ruang lingkup tiga minggu:

| Isu | Keputusan | Alasan |
|---|---|---|
| Arsitektur model | **Tidak diubah** | Mengubahnya berarti melatih ulang dan semua angka skripsi berubah. Fokus ke lapisan output yang memang diminta dosen |
| Atribusi teks (R4) | **LIME sungguhan** | Menutup celah antara diagram dan implementasi |
| Temuan fokus-logo | **Dilaporkan jujur** | Justru memperkuat argumen mengapa XAI diperlukan |
| Bentuk output | **Batch dan satuan** | Sesuai rencana dosen mengirim banyak sampul |
| Paragraf konteks (R3) | **Tanpa LLM** | Ketiga task tetap memprediksi sampul baru, jadi bahannya ada. Memakai LLM akan membatalkan klaim "tidak ada teks dari model bahasa" dan membuat batch 740 sampul makan 4–12 jam |

### Selisih dengan diagram rancangan

Diagram arsitektur menjanjikan beberapa hal yang **belum** ada di implementasi:

| Di diagram | Kenyataan |
|---|---|
| Task 1 = *Critique Category Classification* | Task 1 = klasifikasi isu, 10 kelas |
| Aliran bertingkat antar-task | Tiga keluaran paralel |
| LIME | *Occlusion* sederhana (akan diperbaiki Minggu 2) |
| *Synthesized Macro-Label* | Belum ada (akan dibuat Minggu 2) |

Dua yang pertama tidak dikejar dalam tiga minggu — masuk bagian Batasan
sebagai rencana lanjutan. Bila ditanya saat sidang, jawabannya sudah tertulis.

---

## 10. Berkas penting

### Untuk menjalankan

| Berkas | Isi |
|---|---|
| `setup_windows.bat` | Setup otomatis Windows, sekali jalan |
| `jalankan_windows.bat` | Menjalankan aplikasi di Windows |
| `jalankan_linux.sh` | Menjalankan aplikasi di Linux/macOS |
| `requirements.txt` | Daftar pustaka |

### Untuk memahami

| Berkas | Isi |
|---|---|
| `00_BACA_DULU.md` | Gambaran umum paket |
| `01_TUTORIAL.md` | Panduan langkah demi langkah |
| `02_BATASAN_TEKNIS.md` | Batasan teknis, 9 bagian |
| `docs/DELIVERY_WEEK_1.md` | Dokumen ini |
| `docs/2026-09-22-keputusan-ocr.md` | Dasar pemilihan OCR |
| `docs/plans/2026-09-22-timeline-3-minggu.md` | Rencana tiga minggu |
| `CHANGELOG.md` | Seluruh perubahan |

### Kode

| Berkas | Isi |
|---|---|
| `02_web_demo/app.py` | Server web, 7 alamat API |
| `02_web_demo/xai_core.py` | Mesin prediksi, Grad-CAM, atribusi kata |
| `02_web_demo/ocr_headline.py` | Pembacaan judul otomatis |
| `02_web_demo/label_display.py` | Pemetaan istilah awam |
| `02_web_demo/index.html` | Antarmuka |
| `01_notebook/extract_features.py` | Ekstraksi fitur CLIP + IndoBERT |
| `01_notebook/run_evaluation.py` | Pelatihan + evaluasi |
| `01_notebook/run_xai_analysis.py` | Analisis Grad-CAM dan zona |
| `01_notebook/uji_banding_ocr.py` | Uji banding OCR |

### Data dan hasil

| Berkas | Isi |
|---|---|
| `03_data/DATASET_740_TASK2_DOMAIN.csv` | 740 sampul, 15 kolom — **jangan diubah** |
| `03_data/fitur_clip_indobert_740.npz` | Cache fitur |
| `04_hasil_eksperimen/hasil_mtl_740_task2domain.json` | Metrik tiga task |
| `04_hasil_eksperimen/analisis_zona_740.json` | Analisis zona peta panas |
| `04_hasil_eksperimen/uji_banding_ocr.json` | Hasil uji banding OCR |
| `05_gambar/` | 740 gambar sampul |

---

## Ringkasan satu paragraf

Minggu 1 menutup tiga dari lima revisi dosen: pembacaan teks sampul otomatis
(F1 0,895 setelah tiga tahap perbaikan), penggantian nama kelas teknis dengan
istilah yang mudah dipahami tanpa menyentuh dataset, dan penyatuan tiga peta
panas menjadi satu. Selain itu diperbaiki sembilan cacat — tiga dilaporkan
dosen, sisanya ditemukan saat pemeriksaan kode dan uji coba, termasuk satu
yang cukup serius: sistem menampilkan angka meyakinkan meski teks masukannya
rusak. Paket kini dapat dijalankan di Windows lewat dua kali klik. Tersisa R4
(LIME) dan R3 (paragraf kesimpulan) untuk Minggu 2, serta pemrosesan banyak
sampul untuk Minggu 3.
