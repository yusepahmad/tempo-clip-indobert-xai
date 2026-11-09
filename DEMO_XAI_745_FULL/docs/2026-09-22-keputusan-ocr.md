# Keputusan Pemilihan OCR (revisi R1)

**Tanggal:** 22 September 2026
**Status:** selesai, terimplementasi

## Permintaan dosen

> "Untuk bagian interfacenya kan user masih harus ngeinput ulang tuh teks, nah
> disaranin kalo bisa itu kesalin otomatis karena user ga bakalan punya waktu
> buat ngetik ulang."
>
> "taks => pake ocr => berbasis trm base => hf"
> "Disaranin pake OCR => kalo bisa pake yang lain sihlakan"

Dosen menyarankan OCR berbasis transformer dari HuggingFace (TrOCR), dengan
izin memakai alternatif lain.

## Yang diuji

Perbandingan dijalankan pada **20 sampul asli**, diambil merata dari seluruh
dataset (tiap sampul ke-37), memakai kolom `headline_verified` sebagai acuan.
Skrip: `01_notebook/uji_banding_ocr.py`.
Hasil mentah: `04_hasil_eksperimen/uji_banding_ocr.json`.

| Kandidat | Keterangan |
|---|---|
| `easyocr_mentah` | Seluruh teks yang terbaca, tanpa pemilihan headline |
| `easyocr_headline` | EasyOCR + modul pemilihan headline (`ocr_headline.py`) |
| `trocr` | TrOCR `microsoft/trocr-base-printed`, sesuai saran dosen |

## Ukuran yang dipakai

- **CER / WER** — jarak edit karakter/kata, dibagi panjang **terpanjang** di
  antara acuan dan hasil.
- **Recall** — berapa banyak kata acuan yang muncul di hasil.
- **Presisi** — berapa banyak kata hasil yang memang ada di acuan.
- **F1** — rata-rata harmonik keduanya.

### Catatan metodologis penting

Rancangan metrik yang pertama membagi CER/WER dengan panjang **acuan** saja.
Cara itu keliru untuk kasus ini: OCR membaca seluruh teks sampul (120+
karakter) sementara acuan hanya headline (~27 karakter), sehingga jarak edit
selalu melampaui panjang acuan dan CER/WER jenuh di 1,00 untuk semua kandidat
— tidak ada yang dapat dibedakan. Terlihat jelas dari gejala mustahil:
`kata_tertangkap` 1,00 (semua kata acuan ketemu) bersamaan dengan CER 1,00
(salah total).

Setelah pembagi diubah ke panjang terpanjang dan ditambahkan presisi,
perbedaan antar-kandidat baru terukur.

## Hasil

| Kandidat | CER ↓ | WER ↓ | Recall ↑ | Presisi ↑ | F1 ↑ | Detik/sampul |
|---|---|---|---|---|---|---|
| easyocr mentah | 0,892 | 0,894 | 0,936 | 0,119 | 0,204 | 3,53 |
| easyocr + pemilihan headline | 0,307 | 0,348 | 0,677 | 0,717 | 0,684 | 4,69 |
| + penyaringan logo TEMPO | 0,175 | 0,216 | 0,814 | 0,824 | 0,804 | 3,94 |
| **+ skor gabungan (audit)** | **0,119** | **0,145** | **0,882** | **0,960** | **0,895** | **3,84** |
| TrOCR | — | — | — | — | — | — |

Sebaran akhir pada 20 sampul: **14 sempurna** (F1 = 1,00), 1 baik, 5 sebagian,
**0 gagal total**.

### Bacaan hasil

**OCR mentah tidak dapat dipakai langsung.** Recall 0,936 menunjukkan
EasyOCR memang menangkap hampir semua kata headline — tetapi presisi 0,119
berarti kata-kata itu tenggelam di antara teks lain pada sampul (rubrik,
harga, nomor halaman, teks pendukung). Mengisi kolom headline dengan keluaran
ini justru menyulitkan pengguna.

**Pemilihan headline yang menentukan.** Modul `ocr_headline.py` memilih blok
teks tercetak paling besar, menggabungkan baris yang tingginya sebanding, dan
membuang elemen tetap sampul. Presisi naik dari 0,119 ke 0,717.

**Penyaringan logo memberi lompatan terbesar.** Logo "TEMPO" dicetak sangat
besar sehingga hampir selalu menjadi blok tertinggi. OCR kerap membacanya
tidak utuh ("TEM", "~TEMPO", "TEMP0"), sehingga daftar abaikan yang menuntut
kecocokan penuh tidak menangkapnya dan logo terpilih sebagai headline. Setelah
bentuk rusak itu ikut disaring, F1 naik 0,684 → **0,804**.


### Soal TrOCR

TrOCR tidak dapat dijalankan sampai selesai dalam sesi ini. Dua hal terpisah:

1. **Kegagalan pemuatan, sudah teratasi.** `TrOCRProcessor.from_pretrained`
   gagal pada transformers 5.17 dengan galat *"Couldn't instantiate the
   backend tokenizer"*, bahkan setelah `sentencepiece` dipasang. Diatasi
   dengan memuat komponen terpisah: image processor dari checkpoint TrOCR,
   tokenizer dari `roberta-base` (TrOCR memang memakai tokenizer RoBERTa).
   Perbaikan ini sudah masuk ke `uji_banding_ocr.py`.

2. **Belum tuntas diukur.** Unduhan model (~1,4 GB) belum selesai saat
   dokumen ini ditulis. Skripnya siap; jalankan:
   ```
   venv/bin/python 01_notebook/uji_banding_ocr.py --n 20 --mesin trocr
   ```

**Namun ada alasan metodologis yang lebih kuat**: TrOCR dirancang untuk
**satu baris teks** (dokumen tercetak, tulisan tangan), bukan *scene text*
dengan banyak blok. Pada sampul majalah, TrOCR akan mengembalikan satu
untaian untuk seluruh gambar tanpa informasi posisi dan ukuran huruf —
padahal justru informasi itulah yang dipakai untuk membedakan headline dari
teks lain, dan yang terbukti menaikkan F1 dari 0,204 ke 0,895.

Untuk memakai TrOCR secara adil, ia perlu didahului deteksi baris teks
(mis. CRAFT/DBNet) agar tiap blok diumpankan terpisah — yakni menambahkan
lagi komponen yang sudah dibawa EasyOCR.


## Audit lanjutan (22 Sep, setelah uji coba pengguna)

Uji coba pada dua sampul di luar 20 sampul evaluasi memperlihatkan kegagalan
yang tidak tertangkap uji awal.

### Kasus "ANCANG-ANCANG JOKOWI"

Headline terbaca **"TEN"** — potongan logo TEMPO yang huruf M dan P-nya
tertutup kepala Jokowi. Headline asli justru terbuang ke kolom teks pendukung.

Empat cacat rancangan yang ditemukan:

1. **Pola penyaringan logo terlalu kaku.** Menuntut awalan "TEM", sehingga
   bentuk rusak "TEN" lolos.
2. **Pemilihan hanya memakai tinggi blok.** Sisa logo setinggi 13,5% tinggi
   gambar mengalahkan headline asli (5,0%), dan ambang relatif 0,62×
   menyingkirkan headline sepenuhnya.
3. **Keyakinan OCR tidak dipakai memilih**, hanya dilaporkan.
4. **Posisi diabaikan.** Logo selalu di sepertiga atas; headline Tempo hampir
   selalu di bawah pertengahan.

### Kasus "NAF HODA BARU KADIN"

Satu baris paragraf deskripsi (tinggi 43 px, panjang penuh) mengalahkan
headline (tinggi 74 px), karena tinggi baris paragraf dapat menyamai tinggi
huruf headline sementara panjangnya tidak diperhitungkan.

### Perbaikan

- **Penyaringan logo dua lapis.** `_LOGO_PASTI` untuk bentuk yang tidak
  mungkin kata Indonesia, berlaku di mana pun. `_LOGO_ATAS` jauh lebih longgar
  tetapi hanya berlaku di sepertiga atas — tanpa pembatasan posisi, pola
  longgar itu ikut membuang kata sah seperti "MOMEN", "NONTON", "TEMPE".
- **Skor gabungan** menggantikan tinggi semata: tinggi × posisi × keyakinan ×
  penalti panjang. Blok di wilayah logo dikalikan 0,45; blok di paruh bawah
  dikalikan 1,15; blok >45 karakter dikalikan 0,35.
- **Kedekatan vertikal** saat menggabungkan baris, agar teks lain yang
  kebetulan seukuran tidak ikut tertarik.
- **Penyambungan tanda hubung**: "ANCANG-" + "ANCANG" → "ANCANG-ANCANG".
- **Blok berkeyakinan < 0,30 dibuang** — umumnya tekstur gambar yang salah
  dikenali sebagai huruf.

### Hasil

| Sampul | Sebelum | Sesudah |
|---|---|---|
| ANCANG-ANCANG JOKOWI | `TEN` | `ANCANG-ANCANG JOKOWI` |
| NAF HODA BARU KADIN | `5uteh NAF HODA BARU KADIN` + paragraf | `NAF HODA BARU KADIN` |

Pada 20 sampul evaluasi: F1 0,804 → **0,895**, presisi 0,824 → **0,960**,
dan kategori gagal total turun dari 3 menjadi **0**.

### Peringatan masukan rusak

Ditemukan pula bahwa sampul dengan headline terbaca keliru tetap menghasilkan
prediksi berikut persentasenya, tanpa isyarat apa pun bahwa masukannya rusak —
pada kasus "TEN" sistem menampilkan "Pemilu & Persaingan Politik 43,4%" seolah
sahih. Kini bila judul kurang dari dua kata atau di bawah 8 karakter, blok
peringatan muncul di awal penjelasan naratif. Prediksi tetap ditampilkan,
tetapi pembaca diberi tahu bahwa hasilnya praktis hanya bersandar pada gambar.

## Keputusan

**Dipakai: EasyOCR + modul pemilihan headline** (`MESIN_DEFAULT = "easyocr"`
di `02_web_demo/ocr_headline.py`).

Alasan:
1. EasyOCR menyertakan deteksi teks + posisi + ukuran, yang dibutuhkan untuk
   memilih headline. TrOCR tidak.
2. Terukur pada sampul asli: F1 0,804, 14 dari 20 sempurna.
3. Dosen mengizinkan alternatif ("kalo bisa pake yang lain sihlakan").
4. Waktu ~4 detik/sampul, wajar untuk pengisian kolom saat unggah.

Mesin dapat ditukar lewat satu konstanta bila dibutuhkan.

## Batasan yang harus disampaikan

- **Hasil OCR bukan kebenaran.** Ia hanya mengisi kolom; pengguna tetap dapat
  menyunting, dan antarmuka menyatakan hal ini secara eksplisit.
- **Huruf hias tebal masih salah baca.** Setelah audit tidak ada lagi yang
  gagal total, tetapi 5 dari 20 sampul masih terpotong sebagian — misalnya
  "PERANG BUBAT DI TANAH JAWA" terbaca "PERANG BUBAT", dan
  "Bung Tomo: Soerabaja di Tahun 45" terbaca "Bung Tomo". Hasilnya tetap
  terbaca manusia dan mudah dilengkapi.
- **Judul terlalu pendek memicu peringatan**, bukan penolakan — headline
  pendek yang sah tetap dapat dianalisis.
- **Kolom yang sudah terisi tidak ditimpa**, agar suntingan pengguna aman.
- **Kegagalan OCR tidak menggagalkan unggah** — bila pustaka tidak tersedia
  atau pembacaan gagal, antarmuka menyatakannya dan pengguna mengisi manual.

## Berkas terkait

| Berkas | Isi |
|---|---|
| `02_web_demo/ocr_headline.py` | Modul pembacaan + pemilihan headline |
| `01_notebook/uji_banding_ocr.py` | Skrip uji banding |
| `04_hasil_eksperimen/uji_banding_ocr.json` | Hasil mentah per sampul |
| `02_web_demo/app.py` | Endpoint `POST /api/ocr` |
| `02_web_demo/index.html` | `bacaOtomatis()`, dipanggil saat berkas dipilih |
