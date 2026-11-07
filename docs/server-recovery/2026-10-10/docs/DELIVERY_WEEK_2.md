# Laporan Minggu 2 — Demo XAI Dekoding Metafora Sampul Tempo

> **Dokumen riwayat: laporan Minggu 2 per 28 September 2026.** Status terbaru: [STATUS_REVISI_20261006.md](STATUS_REVISI_20261006.md) (6 Oktober 2026). Ringkasan koreksi status bertanggal 6 Okt ada tepat di bawah catatan ini.
>
> **Koreksi status 6 Okt** (isi laporan di bawah tidak diubah; path bukti relatif terhadap `04_hasil_eksperimen/revisi_week3/`.)
> - **"Kelima revisi dosen tertutup"** tidak lagi menjadi status terkini. Per 6 Okt: R1 *diterapkan, kualitas terbatas* (judul tepat 68–78% pada dua set validasi audit OCR 6 Okt untuk versi aplikasi terakhir (cenderung optimistis; 63–72% saat kode dibekukan), sasaran usulan 80% belum tercapai); R2 diterapkan; R3 diterapkan dan narasinya ditulis ulang 6 Okt (ringkasan tiga task di tab Prediksi, penjelasan task pilihan di tab Penjelasan, tetap tanpa LLM); R4 diterapkan, tetapi polanya masih bisa muncul tergantung input; R5 sempat menyimpang pada 5 Okt (peta utama mengikuti task pilihan) dan ditutup lagi 6 Okt dengan peta gabungan tiga task sebagai peta utama.
> - **"Kasus spesifik R4 belum dapat diuji ulang"**: foto asli dosen tersedia sejak 5 Okt ([VERIFIKASI_GAMBAR_DOSEN.md](VERIFIKASI_GAMBAR_DOSEN.md)). Audit 6 Okt pagi (judul manual, teks pendukung kosong) memberi DEMO positif (`audit_gula_original_lime.json`); smoke browser dengan teks pendukung hasil OCR memberi ketiga kata GULA-GULA nilai negatif (`browser_smoke_20261006_audit.json`). Kelas unggahan tidak divalidasi.
> - Analisis satuan tetap memakai LIME (120 varian) dan batch memakai occlusion. Fine-tuning Kaggle tidak dipakai di demo karena Task 2 turun; model tetap baseline.

**Periode:** 28 September 2026
**Deadline keseluruhan:** 12 Oktober 2026
**Status:** Minggu 2 selesai — **kelima revisi dosen tertutup**

**Judul penelitian:** Eksperimen Multi-Task Learning CLIP-IndoBERT Berbasis XAI
untuk Dekoding Metafora Sampul Majalah Tempo

---

## Ringkasan satu paragraf

Minggu 2 menutup dua revisi terakhir. **R4** — atribusi kata yang dinilai
fatal oleh dosen — dijawab dengan memasang LIME sungguhan berdampingan dengan
occlusion, lalu membandingkan keduanya pada 25 sampul: LIME lebih jarang
menghasilkan gejala "seluruh kata negatif" (1/25 vs 2/25), keduanya sepakat
soal kata terpenting pada 22 dari 25 sampul, tetapi LIME 21 kali lebih lambat.
**R3** — paragraf kesimpulan berbahasa awam — dibangun dengan cara merangkai,
bukan menggenerasi, sehingga setiap pernyataannya tetap dapat ditelusuri ke
bagian teknis. Satu hal yang harus disampaikan terus terang: kasus spesifik
yang dilaporkan dosen tidak dapat diuji ulang karena sampulnya bukan bagian
dari korpus 740.

---

## Status seluruh revisi

| Kode | Permintaan | Selesai |
|---|---|---|
| R1 | Teks sampul terisi otomatis | Minggu 1 |
| R2 | Nama kelas pakai istilah mudah dipahami | Minggu 1 |
| R5 | Satu peta panas terpadu | Minggu 1 |
| **R3** | **Paragraf kesimpulan berbahasa awam** | **Minggu 2** |
| **R4** | **Atribusi kata yang masuk akal (LIME)** | **Minggu 2** |

---

## R4 — Atribusi kata dengan LIME

### Masalah yang dilaporkan

Pada sampul "GULA-GULA DEMO BURUH", seluruh kata bernilai negatif:
GULA-GULA −0,023, DEMO −0,087, BURUH −0,089. Dosen menilai ini fatal:

> *"Yang fatal demo, padahal gambar jelas menunjukan aksi demo"*
> *"Buruh kok bisa membuat turun padahal di teks ada di mention buruh"*

Metode yang dipakai saat itu adalah *occlusion* sederhana: hapus satu kata,
ukur perubahan probabilitas. Diagram rancangan penelitian sebenarnya menyebut
**LIME**, jadi ada celah antara rancangan dan implementasi.

### Yang dikerjakan

LIME dipasang **berdampingan** dengan occlusion, bukan menggantikannya,
sehingga keduanya dapat dibandingkan dan occlusion tetap tersedia.

| | LIME | Occlusion |
|---|---|---|
| Cara kerja | Membangkitkan ratusan varian judul, mencocokkan regresi linear berbobot jarak | Menghapus satu kata, ukur perubahan |
| Pengaruh antar-kata | Terhitung | Tidak terhitung |
| Sifat | Sampling acak (diberi `random_state` agar dapat diulang) | Deterministik |

### Hasil uji banding (25 sampul)

Skrip: `01_notebook/uji_banding_atribusi.py`
Hasil mentah: `04_hasil_eksperimen/uji_banding_atribusi.json`

| Ukuran | Occlusion | LIME |
|---|---|---|
| Sampul dengan **seluruh kata negatif** | 2 dari 25 | **1 dari 25** |
| Sepakat soal kata teratas | 22 dari 25 (88%) | |
| Korelasi urutan kata (Spearman) | 0,851 | |
| Stabilitas bila diulang | deterministik | 1,0 |
| Waktu per sampul | **0,83 detik** | 17,68 detik |

### Penyetelan kecepatan

Analisis pertama memakan ~60 detik, terlalu lama untuk dipakai berulang.
Rinciannya: Grad-CAM tiga task 13,3 detik, LIME 200 varian 15,9 detik,
pelatihan ulang 2,6 detik, sisanya overhead.

Jumlah varian LIME diuji pada 5 sampul:

| Varian | Waktu | Korelasi terhadap 200 varian | Kata teratas sama |
|---|---|---|---|
| 200 | 15,9 detik | acuan | acuan |
| 80 | 6,1 detik | 0,960 | 4 dari 5 |

Selisih kualitasnya kecil sementara kecepatannya 2,6 kali lebih baik, jadi
nilai baku ditetapkan **120 varian** — di antara keduanya.

### Keputusan

**LIME dipakai sebagai metode baku**, karena itu yang dijanjikan diagram
penelitian dan karena ia mengurangi gejala yang dikeluhkan.

**Occlusion dipertahankan** dan dapat dipilih lewat parameter
`metode_atribusi`. Alasannya praktis: untuk 740 sampul, selisihnya sekitar
3,6 jam berbanding 10 menit. Untuk mode batch di Minggu 3, occlusion jauh
lebih masuk akal.

Bila LIME gagal karena alasan apa pun, sistem otomatis jatuh ke occlusion —
analisis tidak pernah gagal total. Metode yang benar-benar dipakai
ditampilkan ke pembaca, tidak perlu ditebak.

### Yang harus disampaikan terus terang

**Kasus spesifik dosen belum dapat dibuktikan teratasi.** Sampul "GULA-GULA
DEMO BURUH" adalah gambar yang diunggah dosen sendiri — bukan bagian dari 740
sampul korpus — sehingga berkasnya tidak tersedia untuk diuji ulang.

Uji banding di atas dijalankan pada sampul dataset, tempat gambar dan teksnya
benar-benar cocok. Yang dapat dinyatakan: **LIME mengurangi gejala itu secara
terukur**. Yang tidak dapat dinyatakan: bahwa kasus itu sendiri sudah beres.

Ada juga temuan yang tidak diduga: gejala "seluruh kata negatif" ternyata
**bukan pola umum** — hanya 2 dari 25 sampul. Saat dicoba dengan gambar lain
ditambah judul "GULA-GULA DEMO BURUH", occlusion justru menghasilkan seluruh
nilai positif. Ini memperkuat dugaan bahwa gejala itu muncul dari kombinasi
gambar-dan-teks tertentu, bukan dari metodenya semata.

**Saran:** minta berkas sampul tersebut dari dosen agar dapat diuji langsung.

---

## R3 — Paragraf kesimpulan berbahasa awam

### Permintaan dosen

> *"Penjelasanya jelas which is good tapi terlalu teknikal buat user, jadi di
> minta suatu kesimpulan akhir di mana hanya ada paragraf dan mudah di pahami
> user apa yang sebenarnya pesan tersirat yang coba di sampaikan oleh sampul
> itu"*
>
> *"untuk sementara biar saja begitu tapi tambah penjelasan di akhir di
> bawahnya, entar kalo udah final yang di tampilkan ke user cukup penjelasan
> akhir"*

### Cara kerjanya

Paragraf **dirangkai**, bukan dihasilkan model bahasa — sama seperti
penjelasan naratif yang sudah ada. Empat bagian:

| Bagian | Sumber |
|---|---|
| Apa yang dibicarakan | Task 1 + judul sampul |
| Siapa yang disorot | Task 3 (+ nama entitas bila ada) |
| Cara menyampaikannya | Catatan anotator bila ada, jika tidak definisi codebook |
| Seberapa kuat dasarnya | Probabilitas + kata dominan + zona peta panas |

Untuk sampul dataset, bagian ketiga memakai catatan anotator yang jauh lebih
kaya dan spesifik. Untuk sampul unggahan, ia jatuh ke frasa domain.

### Contoh keluaran

**Sampul dataset, dasar konsisten:**

> Sampul berjudul "AKBAR TERPOJOK SIAPA SENANG" ini dibaca model sebagai
> pembicaraan tentang hukum & peradilan. Pihak yang disorot adalah Akbar
> Tanjung (termasuk kelompok perorangan). Kritiknya disampaikan lewat sudut
> ruang dan posisi fisik terjepit: Posisi di sudut menggambarkan tekanan
> politik dan hukum yang menyudutkan Akbar. Kata yang paling menentukan
> pembacaan ini adalah "AKBAR". Kata pada judul dan area gambar yang disorot
> model sejalan dengan pembacaan di atas.

**Sampul dengan dasar lemah:**

> […] Perlu dicatat: keyakinan model atas jenis kiasan hanya 34%; tidak ada
> satu pun kata pada judul yang menopang pembacaan ini; bagian gambar yang
> paling memengaruhi keputusan adalah area logo dan teks tercetak, bukan
> ilustrasinya. Karena itu kesimpulan di atas sebaiknya diperiksa ulang oleh
> pembaca, bukan diterima begitu saja.

### Prinsip yang dipegang

**Paragraf menyatakan keraguannya, bukan menyembunyikannya.** Macro-F1 Task 2
hanya 0,320 — sekitar 2 dari 3 tebakan domain meleset. Paragraf yang terdengar
lancar dan pasti justru berbahaya: pembaca akan menganggap model "memahami"
sampul. Karena itu ada penanda tetap di kartu: **"dasar pembacaan konsisten"**
atau **"perlu diperiksa ulang"**.

### Batas yang nyata

Untuk sampul di luar dataset, paragraf hanya dapat menyebut **jenis** kiasan
("perumpamaan mesin, alat, atau bangunan"), bukan makna spesifiknya seperti
"hidung panjang = Pinokio = kebohongan". Makna spesifik berasal dari anotasi
manusia yang hanya tersedia untuk 657 sampul korpus.

Keputusan **tanpa LLM** (22 September) dipertahankan. Alasannya: LLM tidak
menambah pengetahuan tentang sampul — ia hanya memperluwes bahasa — sementara
memakainya membatalkan klaim "tidak ada teks yang dihasilkan model bahasa"
yang menjadi kekuatan paket ini, dan membuat pemrosesan 740 sampul memakan
4–12 jam.

---

## Bug yang diperbaiki

| Bug | Dampak |
|---|---|
| `str.lower()` merusak akronim | "Ekonomi, Bisnis & BUMN" tercetak "ekonomi, bisnis & bumn" di paragraf kesimpulan |

## Permintaan lain yang ikut ditutup

Pada halaman 5 revisi, dosen juga meminta judul dikaitkan dengan konteks di
bawahnya (*"JUdul kaitkan dengan konteks bawah => Konteks Key word"*).
Paragraf kesimpulan kini menyandingkan kata kunci langsung dengan isu yang
diprediksi — bukan sekadar menyebut kata mana yang paling berpengaruh — dan
menyebut pula kata yang justru menarik ke arah berbeda bila pengaruhnya
cukup berarti.

---

## Verifikasi

| Yang diuji | Hasil |
|---|---|
| Fungsi korelasi Spearman | 5 kasus batas, semua benar |
| Paragraf kesimpulan — sampul dataset | Memakai catatan anotator, label ANOTATOR |
| Paragraf kesimpulan — sampul unggahan | Jatuh ke frasa domain |
| Paragraf kesimpulan — NON_METAFORA | Menyatakan "tidak memakai perumpamaan", `"nan"` tidak bocor |
| Paragraf kesimpulan — semua kata negatif | Menyatakan tiga keraguannya |
| Uji banding LIME vs occlusion | 25 sampul, hasil tersimpan |
| Sintaks JS dan Python | Bersih |

---

## Rancangan Minggu 3 (6–12 Oktober)

**Hari 15–17 — pemrosesan banyak sampul sekaligus.** Dosen berencana mengirim
seluruh sampul. Mode batch memakai **occlusion**, bukan LIME (selisih 10 menit
vs 3,6 jam), dan **tidak memakai leave-one-out** — melatih ulang model untuk
tiap sampul berarti 740 kali pelatihan. Perbedaan ini harus ditulis jujur:
hasil batch tidak sebanding langsung dengan angka leave-one-out.

**Hari 18–19 — pengujian menyeluruh**, termasuk kasus batas.

**Hari 20–21 — dokumentasi akhir**, termasuk pemetaan tiap revisi ke
implementasinya sebagai bukti.

---

## Batasan yang masih berlaku

Selengkapnya di `02_BATASAN_TEKNIS.md`. Yang terpenting:

- **Model masih sering meleset** — Macro-F1 Task 2 = 0,320.
- **Model bertumpu pada logo, bukan ilustrasi** — 22 dari 25 sampul. Dilaporkan
  sebagai temuan, bukan diperbaiki.
- **"Grad-CAM" di sini bukan Grad-CAM CNN** — yang dipakai Gradient × Activation
  pada blok kedua dari belakang.
- **OCR tidak sempurna** — 5 dari 20 sampul judulnya terpotong sebagian.
- **LIME berbasis sampling** — 200 varian, jadi hasilnya perkiraan.
- **Kasus spesifik R4 belum dapat diuji ulang** — berkas sampulnya tidak ada.

---

## Berkas yang berubah Minggu 2

| Berkas | Perubahan |
|---|---|
| `02_web_demo/xai_core.py` | `atribusi_kata_lime()`, `susun_kesimpulan()`, `_huruf_kecil_aman()`, `_prob_banyak_teks()` |
| `02_web_demo/app.py` | LIME sebagai metode baku + fallback, kesimpulan diteruskan |
| `02_web_demo/index.html` | Kartu kesimpulan, keterangan metode atribusi |
| `01_notebook/uji_banding_atribusi.py` | Baru — pembanding LIME vs occlusion |
| `04_hasil_eksperimen/uji_banding_atribusi.json` | Baru — hasil 25 sampul |
| `02_BATASAN_TEKNIS.md` | Bagian 2 ditulis ulang, bagian 5 dan 9 diperbarui |
| `requirements.txt` | `lime>=0.2` |
| `CHANGELOG.md` | Seluruh perubahan Minggu 2 |
