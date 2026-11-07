> Pembaruan Week 3 (2026-10-05): UI/input/XAI dan batch tersedia untuk review baseline. Lihat [panduan dan bukti Week 3](docs/DELIVERY_WEEK_3.md), termasuk cara batch/review/ekspor, diagnosis OCR dan penerimaan yang belum lengkap. Training baru belum diintegrasikan; definisi resmi lengkap belum terverifikasi.

# Batasan Teknis — Demo XAI Dekoding Metafora Sampul Tempo

Dokumen ini menjelaskan apa yang **tidak** dilakukan sistem ini, dan di mana
hasilnya harus dibaca dengan hati-hati. Ditulis terpisah supaya setiap klaim
pada demo dapat ditelusuri batasannya.

Dataset: 740 sampul (dataset final penelitian).
Tanggal pemutakhiran: 29 September 2026.

---

## Ringkasan — dua hal yang paling penting dibaca dulu

**Performa model (bagian 4) masih rendah untuk dipakai sebagai alat putus.**
Macro-F1 Task 2 (domain sumber metafora) hanya **0,320** dari skala 0-1.
Beberapa kelas seperti Konsumsi & Transaksi (0,214) dan Mesin &
Infrastruktur (0,220, meski kelas terbesar) sering salah diklasifikasikan.
Model jauh melampaui baseline (0,064) sehingga terbukti belajar sesuatu,
tetapi belum layak menilai sampul secara otomatis tanpa tinjauan manusia.

**Metode XAI di sini adalah adaptasi, bukan implementasi baku dari literatur
(bagian 1 dan 2).** Grad-CAM CNN tidak berlaku langsung pada Vision
Transformer — ini fakta metodologis yang dibuktikan lewat penelusuran
gradien, bukan kekurangan implementasi. Yang dipakai adalah Gradient ×
Activation pada blok kedua-dari-belakang. Begitu pula atribusi kata: LIME
di sini dibatasi 200 sampel demi kecepatan, sehingga hasilnya perkiraan,
bukan nilai pasti seperti LIME dengan sampel besar.

Kedua hal ini **tidak diperbaiki lebih jauh dalam paket ini** karena
melanggar batas ruang lingkup yang sudah disepakati 22 September 2026:
arsitektur model dan dataset tidak diubah. Memperbaikinya (data lebih
banyak per kelas, fine-tuning encoder, atau Grad-CAM native pada CNN)
adalah pekerjaan penelitian lanjutan, bukan perbaikan bug. Rincian tiap
poin ada di bagian 1-4 di bawah.

---

## 1. Grad-CAM di sini bukan Grad-CAM CNN

Grad-CAM asli dirancang untuk jaringan konvolusi: bobot diambil dari
rata-rata gradien pada peta fitur, lalu dikalikan aktivasinya.

Pada CLIP ViT-B/32 hal itu tidak berlaku langsung. `encode_image` hanya
memakai token CLS untuk menghasilkan embedding akhir, sehingga **gradien
token patch pada blok terakhir bernilai nol** dan rumus Grad-CAM CNN
menghasilkan peta kosong.

Yang dilakukan sistem ini:

- hook diambil pada **blok kedua dari belakang**
  (`visual.transformer.resblocks[-2]`), tempat informasi patch masih
  mengalir ke CLS melalui self-attention;
- besaran pengaruh tiap patch dihitung sebagai `|aktivasi × gradien|`
  per token — ini **Gradient × Input**, bukan Grad-CAM;
- hasilnya di-reshape menjadi grid 7×7 (49 patch pada input 224 px).

**Konsekuensi:** istilah "Grad-CAM" pada antarmuka dipakai secara longgar.
Di laporan, metode ini harus disebut sebagai *adaptasi Gradient × Activation
untuk ViT*, bukan Grad-CAM sebagaimana dimaksud Selvaraju dkk.

### Bila peta panas tidak muncul

Fungsi `gradcam()` mengembalikan `None` bila:

- gradien seluruh token bernilai nol (`g.abs().sum() == 0`);
- bentuk tensor aktivasi tidak dikenali (bukan 3 dimensi);
- jumlah token bukan bilangan kuadrat sempurna, sehingga tidak dapat
  di-reshape menjadi grid persegi.

Dalam keadaan itu antarmuka tidak menampilkan peta panas. Ini perilaku yang
disengaja — lebih baik tidak menampilkan apa pun daripada menampilkan peta
yang tidak bermakna.

---

## 2. Atribusi kata: LIME dan occlusion

Sejak revisi 28 September, tersedia **dua metode**. Antarmuka memakai LIME
secara baku; occlusion dapat dipilih lewat parameter `metode_atribusi`.

| | LIME | Occlusion |
|---|---|---|
| Cara kerja | Membangkitkan ratusan varian judul, mencocokkan regresi linear berbobot jarak | Menghapus satu kata, mengukur perubahan probabilitas |
| Pengaruh antar-kata | Terhitung | Tidak terhitung |
| Sifat | Berbasis sampling acak (diberi `random_state` agar dapat diulang) | Deterministik |
| Waktu per sampul | 17,68 detik | 0,83 detik |

Hasil uji banding pada 25 sampul
(`04_hasil_eksperimen/uji_banding_atribusi.json`):

| Ukuran | Nilai |
|---|---|
| Sampul dengan seluruh kata negatif — occlusion | 2 dari 25 |
| Sampul dengan seluruh kata negatif — LIME | 1 dari 25 |
| Kedua metode sepakat soal kata teratas | 22 dari 25 |
| Korelasi urutan kata (Spearman) | 0,851 |
| Stabilitas LIME bila diulang | 1,0 |

Kedua metode sepakat pada mayoritas kasus. LIME dipilih sebagai metode baku
karena diagram rancangan penelitian memang menyebut LIME, dan karena ia lebih
jarang menghasilkan gejala "seluruh kata negatif" yang dikeluhkan dosen.
Occlusion dipertahankan untuk pemrosesan banyak sampul: pada 740 sampul,
selisihnya sekitar 3,6 jam berbanding 10 menit.

**Batasan yang berlaku untuk kedua metode:**

- Hanya judul yang diperiksa; teks pendukung ikut menentukan prediksi tetapi
  tidak ikut diatribusi.
- IndoBERT memakai token CLS dari kalimat yang sudah diubah. Menghilangkan
  kata mengubah seluruh representasi kalimat, sehingga nilai kontribusi tidak
  dapat dibaca sebagai "sumbangan murni" kata itu.
- LIME berbasis sampling: jumlah varian dibatasi 200 demi kecepatan, sehingga
  hasilnya perkiraan, bukan nilai pasti.

**Catatan penting soal kasus yang dilaporkan dosen.** Sampul "GULA-GULA DEMO
BURUH" adalah gambar yang diunggah dosen sendiri, bukan bagian dari 740 sampul
korpus, sehingga berkasnya tidak tersedia untuk diuji ulang. Perbandingan di
atas dijalankan pada sampul dataset — tempat gambar dan teksnya benar-benar
cocok. Jadi dapat dinyatakan bahwa LIME mengurangi gejala tersebut secara
terukur, tetapi **belum dapat dibuktikan** bahwa kasus spesifik itu teratasi.
Untuk memastikannya, berkas sampul tersebut perlu diminta dari dosen.

### Seluruh kata bisa bernilai negatif

Nilai negatif berarti menghapus kata itu justru **menaikkan** probabilitas
kelas terpilih. Pada sebagian sampul, **semua** kata bernilai negatif —
artinya tidak ada satu pun kata pada judul yang menopang keputusan, dan
prediksi bertumpu pada elemen visual atau teks pendukung.

Contoh nyata pada dataset ini, sampul "GULA-GULA DEMO BURUH":

| Kata | Kontribusi |
|---|---|
| GULA-GULA | −0,023 |
| DEMO | −0,087 |
| BURUH | −0,089 |

Antarmuka menyatakan keadaan ini apa adanya, bukan menyebut kata yang paling
tidak melemahkan sebagai "penopang". Kasus ini juga menunjukkan bahwa model
belum menangkap kaitan antara kata "DEMO"/"BURUH" dan ilustrasi aksi unjuk
rasa pada sampul — keterbatasan yang dicatat untuk tindak lanjut.

---

## 3. Model bertumpu pada kepala sampul, bukan ilustrasi

Analisis 25 sampul secara leave-one-out (`04_hasil_eksperimen/analisis_zona_740.json`):

| Zona | Intensitas rata-rata | Dominan pada |
|---|---|---|
| Kepala sampul (logo, judul kecil) | 0,180 | 22 dari 25 |
| Bagian tengah (ilustrasi) | 0,086 | 2 dari 25 |
| Kaki sampul (headline besar, barcode) | 0,060 | 1 dari 25 |

**Prediksi yang benar belum tentu karena alasan yang benar.** Model lebih
sering bertumpu pada area logo dan teks tercetak daripada pada ilustrasi
metaforanya.

Temuan ini konsisten dengan demo 189 sampul (19 dari 25) dan **menguat**
setelah data bertambah hampir empat kali lipat. Jadi ini bukan artefak data
kecil, melainkan sifat model pada korpus ini.

Justru inilah yang membuat komponen XAI berguna: tanpa peta panas, kelemahan
ini tidak akan terlihat dari angka akurasi saja.

**Tindak lanjut yang disarankan** (belum dikerjakan, di luar ruang lingkup
paket ini per keputusan 22 September): memangkas area logo/judul kecil
sebelum encoding, lalu menguji apakah fokus model bergeser ke ilustrasi.
Ini butuh pelatihan ulang dan evaluasi ulang — bukan perubahan tampilan —
sehingga diperlakukan sebagai penelitian lanjutan, bukan perbaikan bug.

---

## 4. Performa model masih rendah

Hasil 5-fold cross-validation pada 740 sampul (`hasil_mtl_740_task2domain.json`):

| Task | Akurasi | Macro-F1 | Majority baseline |
|---|---|---|---|
| Task 1 — Isu utama | 0,455 | 0,438 | 0,036 |
| Task 2 — Domain sumber metafora | 0,320 | 0,320 | 0,064 |
| Task 3 — Tipe entitas sasaran | 0,355 | 0,276 | 0,075 |

Seluruh task jauh melampaui baseline, sehingga model memang mempelajari
sesuatu. Tetapi Macro-F1 di kisaran 0,28–0,44 **belum layak dipakai sebagai
alat putus**. Demo ini untuk memverifikasi alur XAI, bukan untuk dipakai
menilai sampul secara otomatis.

Recall per kelas Task 2 (`analisis_recall_per_kelas_740.csv`):

| Kelas | Jumlah | Recall |
|---|---|---|
| Tanpa Metafora | 83 | 0,651 |
| Permainan & Kontes | 106 | 0,387 |
| Hewan & Tubuh | 90 | 0,322 |
| Lainnya | 63 | 0,302 |
| Bencana & Jerat | 100 | 0,290 |
| Mesin & Infrastruktur | 214 | 0,220 |
| Konsumsi & Transaksi | 84 | 0,214 |

Perhatikan: MESIN_INFRASTRUKTUR adalah kelas **terbesar** (214 sampul)
tetapi recall-nya justru termasuk terendah. Ukuran kelas tidak menjamin
kemudahan pengenalan.

---

## 5. Penjelasan naratif tidak dihasilkan model bahasa

Setiap paragraf pada bagian "Penjelasan naratif" **dirangkai**, bukan
digenerasi. Tidak ada LLM yang dipakai. Setiap bagian diberi penanda asal:

| Penanda | Artinya |
|---|---|
| `MODEL` | Dihitung dari prediksi dan atribusi saat itu |
| `ANOTATOR` | Catatan manusia yang tersimpan di dataset |
| `CODEBOOK` | Definisi tetap yang ditulis manusia |
| `GABUNGAN` | Perbandingan antara keluaran model dan catatan anotator |

Akibatnya penjelasan tidak pernah mengarang, tetapi juga **kaku**: kalimatnya
mengikuti template dan tidak menyesuaikan diri dengan keunikan tiap sampul.

Sejak revisi 28 September ditambahkan **paragraf kesimpulan berbahasa awam**
di atas bagian teknis, menjawab permintaan dosen. Paragraf itu dirangkai
dengan cara yang sama — tidak ada model bahasa yang dipakai — dan menyusun
empat hal: apa yang dibicarakan (Task 1), siapa yang disorot (Task 3), cara
menyampaikannya (Task 2 atau catatan anotator), serta seberapa kuat dasarnya.

Bila keyakinan model rendah, tidak ada kata yang menopang, atau area panas
berada di luar ilustrasi, paragraf itu **menyatakan keraguannya secara
terbuka** alih-alih menyembunyikannya. Untuk sampul di luar dataset, paragraf
hanya dapat menyebut *jenis* kiasan ("perumpamaan mesin, alat, atau
bangunan"), bukan makna spesifiknya — makna spesifik berasal dari anotasi
manusia yang hanya tersedia untuk 657 sampul korpus.

Definisi pada `DEFINISI_DOMAIN` ditulis manusia berdasarkan pembacaan 657
catatan pemetaan makna. Definisi itu menjelaskan **domain secara umum**, bukan
sampul yang sedang dilihat.

---

## 6. Perbedaan mode dataset dan mode unggahan

| Hal | Mode dataset | Mode unggahan |
|---|---|---|
| Pelatihan | Leave-one-out (sampul uji dikeluarkan) | Seluruh 740 sampul |
| Label pembanding | Ada | Tidak ada |
| Catatan anotator | Ada (untuk 657 sampul bermetafora) | Tidak ada |
| Blok `ANOTATOR` | Muncul | Tidak muncul |
| Blok `GABUNGAN` | Membandingkan dengan catatan anotator | Hanya melaporkan letak area panas |

Pada mode unggahan tidak ada kebenaran acuan, sehingga **tidak ada yang dapat
diverifikasi**. Yang ditampilkan murni keluaran model.

Catatan: 83 sampul berlabel NON_METAFORA tidak memiliki catatan sumber
metafora — wajar, karena sampul itu memang dinilai tidak bermetafora. Blok
`ANOTATOR` tidak muncul untuk sampul tersebut.

---

## 7. Batasan dataset

- **740 sampul** — dataset final penelitian ini, seluruhnya memenuhi syarat
  kelayakan (`eligibility = eligible_sociopolitical`).
- Anotasi dikerjakan oleh satu anotator. Tidak ada pengukuran
  *inter-annotator agreement*, sehingga konsistensi label tidak terukur.
- Kolom `annotator_confidence` tersedia tetapi **tidak** dipakai sebagai bobot
  saat pelatihan.
- Kelas `LAINNYA` (63 sampul) adalah kelompok sisa yang belum ditinjau ulang.
- Stratifikasi 5-fold memakai Task 1 saja, sehingga keseimbangan kelas Task 2
  dan Task 3 antar-lipatan tidak dijamin.

---

## 8. Reproduksibilitas

Seluruh script memakai `torch.manual_seed(42)` dan `np.random.seed(42)` pada
titik yang sama dengan notebook asli, sehingga hasilnya deterministik pada
perangkat yang sama.

Yang **tidak** dijamin identik:

- hasil antar-versi PyTorch atau antar-perangkat keras (CPU vs GPU);
- urutan operasi titik-mengambang pada arsitektur prosesor berbeda.

Notebook `DEMO_XAI_TEMPO.ipynb` sempat tertinggal dari dataset pilot 189
sampul (path data dan seluruh narasi masih menyebut 189); diperbaiki 29
September untuk memakai dataset final 740 sampul. Notebook ini menjalankan
alur secara langsung (bukan replikasi) sampai bagian pemuatan data dan
pelatihan; angka pada tabel ringkasan (Bagian 15) diisi dari hasil
eksperimen yang sudah tersimpan di `04_hasil_eksperimen/`, bukan dari
menjalankan ulang seluruh pipeline Grad-CAM/LIME di dalam notebook itu
sendiri — proses itu tetap dijalankan lewat tiga script Python di
`01_notebook/` (`extract_features.py`, `run_evaluation.py`,
`run_xai_analysis.py`).

---

## 9. Yang belum dikerjakan

Tercatat terbuka per 28 September 2026:

- Area logo belum dipangkas untuk menguji pergeseran fokus model (bagian 3).
- Arsitektur masih tiga head paralel; belum ada aliran bertingkat antar-task.
- Mode pemrosesan banyak sampul sekaligus (batch) belum tersedia.
