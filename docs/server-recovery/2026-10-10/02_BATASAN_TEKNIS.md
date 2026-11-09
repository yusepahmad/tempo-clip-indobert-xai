> **Pemutakhiran 6 Oktober 2026.** Dokumen ini diselaraskan dengan demo yang kini berjalan di server review: model **baseline**, dataset 740 sampul, navigasi Analisis / Batch / Panduan. Yang berubah: peta gabungan tiga task (R5) di bagian 1, catatan waktu LIME dan foto asli GULA-GULA di bagian 2, sumber zona di bagian 3, hasil fine-tuning Kaggle di bagian 4, penjelasan terikat task di bagian 5, batasan OCR, batas masukan dan batch di bagian 6, versi pustaka (kini ada `requirements-lock-linux.txt`) di bagian 8, serta daftar terbuka di bagian 9. Matriks status revisi terbaru ada di [docs/STATUS_REVISI_20261006.md](docs/STATUS_REVISI_20261006.md), bukti Week 3 dan 6 Oktober di [docs/DELIVERY_WEEK_3.md](docs/DELIVERY_WEEK_3.md). Demo belum dinyatakan final.

# Batasan Teknis — Demo XAI Dekoding Metafora Sampul Tempo

Dokumen ini menjelaskan apa yang **tidak** dilakukan sistem ini, dan di mana
hasilnya harus dibaca dengan hati-hati. Ditulis terpisah supaya setiap klaim
pada demo dapat ditelusuri batasannya.

Dataset: 740 sampul (dataset final penelitian).
Tanggal pemutakhiran: 6 Oktober 2026 (sebelumnya 29 September 2026).

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
di aplikasi dibatasi 120 varian per analisis demi kecepatan (uji banding
memakai 200), sehingga hasilnya perkiraan, bukan nilai pasti seperti LIME
dengan sampel besar.

Kedua hal ini **tidak diperbaiki lebih jauh dalam paket ini** karena
melanggar batas ruang lingkup yang sudah disepakati 22 September 2026:
arsitektur model dan dataset tidak diubah. Memperbaikinya (data lebih
banyak per kelas, fine-tuning encoder, atau Grad-CAM native pada CNN)
adalah pekerjaan penelitian lanjutan, bukan perbaikan bug. Full fine-tuning
encoder sudah dicoba terpisah di Kaggle, tetapi Task 2 justru turun sehingga
demo tetap memakai baseline (bagian 4). Rincian tiap poin ada di bagian 1-4
di bawah.

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

### Peta gabungan tiga task (R5, ditutup 6 Oktober 2026)

Tab **Bukti gambar** kini menampilkan satu **peta gabungan tiga task** sebagai
peta utama, sesuai permintaan client agar peta yang dilihat pembaca "hanya satu
dan sama dan itu harus mencakup semua".

Cara hitungnya (`gradcam_terpadu()` di `02_web_demo/xai_core.py`):

1. untuk tiap task (Isu, Kiasan/domain sumber, Sasaran) dihitung peta
   Gradient × Activation di atas, masing-masing terhadap kelas yang
   diprediksi untuk task itu, lalu dinormalisasi ke rentang 0–1;
2. peta per task yang tersedia dirata-rata;
3. hasil rata-rata dinormalisasi ulang ke 0–1 agar kontrasnya setara dengan
   peta tunggal.

Normalisasi per task mencegah satu task yang kebetulan bergradien besar
mendominasi rata-rata. Bila tidak satu pun task menghasilkan peta, peta
gabungan tidak dibuat dan antarmuka menulis "Peta gabungan tidak tersedia"
— tidak menampilkan peta task pilihan dengan label gabungan.

**Batas tafsir peta gabungan:**

- Untuk satu sampul dan input yang sama, peta gabungan **sama untuk semua
  pilihan task**. Ini memang tujuan R5; pemeriksaan HTTP 6 Oktober
  menunjukkan hash PNG peta gabungan identik pada ketiga task
  (`04_hasil_eksperimen/revisi_week3/r5_heatmap_verification.json`).
- Peta gabungan merangkum area yang memengaruhi ketiga prediksi sekaligus.
  Ia **bukan dasar** atribusi kata, paragraf penjelasan, maupun zona yang
  disebut di penjelasan, dan bukan deteksi objek.
- Dasar penjelasan tetap **peta task pilihan**, ditampilkan di blok terpisah
  "Bukti task pilihan: <task> — kelas <kelas>". Zona dominan pada penjelasan
  dihitung dari peta ini (bagian 3).
- Peta per task ketiganya tetap tersedia di "Lihat peta panas per task
  (tampilan teknis)".
- Rata-rata tiga peta dapat meredam area yang hanya penting bagi satu task.
  Untuk menelusuri alasan satu task, baca peta task pilihan atau peta per
  task, bukan peta gabungan.

---

## 2. Atribusi kata: LIME dan occlusion

Sejak revisi 28 September, tersedia **dua metode**. Analisis satuan memakai
LIME secara baku; di halaman Batch pengguna memilih Occlusion (bawaan, pilihan
cepat untuk banyak sampul) atau LIME. Lewat API, metode
dipilih dengan parameter `metode_atribusi`.

| | LIME | Occlusion |
|---|---|---|
| Cara kerja | Membangkitkan varian judul (aplikasi 120; uji banding ini 200), mencocokkan regresi linear berbobot jarak | Menghapus satu kata, mengukur perubahan probabilitas |
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

Waktu pada tabel pertama berasal dari uji banding itu (LIME 200 varian, mesin
asal). Aplikasi memakai nilai baku 120 varian (`atribusi_kata_lime()` di
`xai_core.py`); di server CPU 6 Oktober satu analisis satuan dengan LIME
memakan sekitar 15–20 detik.

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
- LIME berbasis sampling: jumlah varian dibatasi (120 di aplikasi) demi
  kecepatan, sehingga hasilnya perkiraan, bukan nilai pasti.

**Catatan penting soal kasus yang dilaporkan dosen.** Sampul "GULA-GULA DEMO
BURUH" adalah gambar yang diunggah dosen sendiri, bukan bagian dari 740 sampul
korpus. Saat paragraf ini pertama ditulis (28 September), berkasnya belum
tersedia, sehingga perbandingan di atas hanya dijalankan pada sampul dataset.
Dari situ dapat dinyatakan bahwa LIME mengurangi gejala "seluruh kata negatif"
secara terukur pada dataset.

*Pembaruan 5–6 Oktober.* Tiga foto asli dosen (GULA-GULA, WASWAS, CUKAI) kini
tersedia di `06_gambar_revisi/`. Hash berkasnya berbeda dari sampul korpus
berjudul sama, sehingga label dan anotasi korpus tidak dipindahkan ke
unggahan. Audit 6 Oktober pada foto GULA-GULA asli (Task 2, LIME, judul
diketik manual "GULA-GULA DEMO BURUH", teks pendukung kosong) memberi kelas
Permainan & Kontes dengan kontribusi GULA-GULA −0,012, **DEMO +0,018**, BURUH
−0,038 (`04_hasil_eksperimen/revisi_week3/audit_gula_original_lime.json`).
Pada konfigurasi itu gejala "seluruh kata negatif" tidak muncul.

Hasil ini **bukan validasi kelas** dan bukan bukti bahwa gejalanya hilang
secara umum:

- unggahan tidak memiliki label pembanding, jadi benar-tidaknya kelas tidak
  diketahui;
- ini satu konfigurasi input; hasilnya bergantung pada input. Pada smoke
  browser 6 Oktober, foto yang sama dengan teks pendukung terisi hasil OCR
  (Task 2, LIME) tetap diprediksi Permainan & Kontes, tetapi ketiga kata
  judul bernilai negatif (`revisi_week3/browser_smoke_20261006.json`);
- pada sampul **korpus** berjudul sama, uji LIME Week 3
  (`revisi_week3/gula_gula_candidate.json`) masih memberi ketiga kata
  bernilai negatif.

### Seluruh kata bisa bernilai negatif

Nilai negatif berarti menghapus kata itu justru **menaikkan** probabilitas
kelas terpilih. Pada sebagian sampul, **semua** kata bernilai negatif —
artinya tidak ada satu pun kata pada judul yang menopang keputusan, dan
prediksi bertumpu pada elemen visual atau teks pendukung.

Contoh riwayat pada dataset ini, sampul korpus "GULA-GULA DEMO BURUH"
(dicatat sebelum Week 3 dan sebelum foto asli dosen tersedia; angkanya tidak
mewakili keluaran aplikasi saat ini — lihat pembaruan di atas):

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

**Zona pada penjelasan.** Zona dominan yang disebut pada tab Penjelasan
dihitung dari **peta task pilihan** (`zona_dominan()` di `xai_core.py`), bukan
dari peta gabungan tiga task. Pembagiannya posisional — sepertiga atas,
tengah, bawah grid — sehingga zona tidak mengidentifikasi apakah area itu
logo, teks atau ilustrasi; penjelasan menyatakan hal ini bila zona dominan
berada di luar bagian tengah.

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

### Hasil full fine-tuning Kaggle (5 Oktober 2026)

Full fine-tuning kedua encoder dijalankan terpisah di Kaggle dengan protokol
5-fold yang sama dan berstatus COMPLETE; audit metrik/protokol lulus
([laporan](docs/HASIL_FULL_TRAINING_KAGGLE.md)).

| Task | Macro-F1 baseline | Macro-F1 fine-tuned |
|---|---|---|
| Task 1 — Isu utama | 0,438 | 0,5139 |
| Task 2 — Domain sumber metafora | 0,320 (0,3197) | 0,2461 |
| Task 3 — Tipe entitas sasaran | 0,276 | 0,3699 |

Task 1 dan Task 3 naik, tetapi Task 2 — fokus utama demo — turun. Karena
itu **demo tetap memakai baseline** (CLIP ViT-B/32 + IndoBERT beku + head
MTL). Checkpoint fine-tuned belum diunduh, belum diperiksa isinya dan belum
diintegrasikan, sehingga perilaku demo dan tabel performa/recall di atas
tetap milik baseline. Integrasi checkpoint menunggu keputusan berbasis
evaluasi, bukan sekadar karena training sudah selesai.

---

## 5. Penjelasan naratif tidak dihasilkan model bahasa

Setiap paragraf ringkasan (tab Prediksi) dan penjelasan (tab Penjelasan)
**dirangkai**, bukan digenerasi. Tidak ada LLM yang dipakai. Setiap bagian
diberi penanda asal:

| Penanda | Artinya |
|---|---|
| `MODEL` | Dihitung dari prediksi dan atribusi saat itu |
| `ANOTATOR` | Catatan manusia yang tersimpan di dataset |
| `CODEBOOK` | Definisi tetap yang ditulis manusia |
| `GABUNGAN` | Perbandingan antara keluaran model dan catatan anotator |

Akibatnya penjelasan tidak pernah mengarang, tetapi kalimatnya tetap
mengikuti templat dan tidak menyesuaikan diri dengan keunikan tiap sampul
(bahasanya ditulis ulang 6 Oktober agar tidak kaku, lihat di bawah).

*Riwayat 28 September.* Sejak revisi 28 September ditambahkan **paragraf
kesimpulan berbahasa awam**
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

**Perubahan Week 3 (berlaku saat ini).** Paragraf kesimpulan empat bagian di
atas sudah diganti penjelasan yang **terikat pada task dan kelas yang sedang
dipilih** (`02_web_demo/explanation_evidence.py`). Tab Penjelasan hanya memuat
bukti untuk task itu: prediksi dan skornya, kata pendukung/pelemah dari
atribusi kata, zona dominan dari peta task pilihan, definisi kelas dari
codebook operasional (dibuat atas instruksi user, bukan codebook resmi), dan
catatan anotator bila ada. Penjelasan tidak lagi menggabungkan klaim lintas
task dan tidak memakai peta gabungan. Keraguan (skor rendah, tidak ada kata
pendukung, zona di luar tengah, judul pendek) tetap dinyatakan terbuka.
Definisi kelas dan catatan anotator ditampilkan sebagai rujukan, bukan alasan
model. Prinsipnya tetap sama: dirangkai dari bukti, tanpa LLM.

**Pembaruan 6 Oktober (narasi lebih luwes).** Atas masukan bahwa teks terasa
kaku, keluaran dipisah menjadi dua dan bahasanya ditulis ulang, tetap tanpa
LLM:

- **Ringkasan interpretasi** (tab Prediksi) membahas ketiga task dalam bahasa
  awam: isu, pihak yang disorot, dan jenis kiasan beserta makna umum kiasan
  semacam itu (frasa yang ditulis manusia dari 657 catatan pemetaan makna,
  bukan tafsir sampul ini), lalu tingkat keyakinan (tanpa persen). Pada mode
  dataset ditambah blok ANOTATOR: aspek yang labelnya berbeda dan kutipan
  catatan pemetaan makna.
- **Penjelasan** (tab Penjelasan) hanya untuk task pilihan: "Mengapa
  <kelas>?" (kata pendorong/penarik dan posisi area paling berpengaruh),
  "Arti kelas ini" (CODEBOOK), "Catatan anotator" (ANOTATOR, bila ada), lalu
  satu daftar **"Yang perlu dicek"** yang menggantikan peringatan berulang di
  setiap kalimat.
- Posisi disebut sebagai "bagian atas/tengah/bawah sampul", tidak pernah
  menamai objek. Kelas Task 3 diparafrasakan (mis. "seorang tokoh"), tanpa
  menambah klaim di luar nama kelas.
- Ringkasan tetap membaca skor yang belum dikalibrasi; kata "dugaan" dipakai
  bila keyakinan rendah. Ringkasan bukan bukti bahwa prediksi benar.

---

## 6. Perbedaan mode dataset dan mode unggahan

| Hal | Mode dataset (analisis satuan) | Mode unggahan |
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

### Batch dataset adalah in-sample

Halaman **Batch** menerima ID dataset dan/atau gambar unggahan. Berbeda dari
analisis satuan mode dataset, item dataset di batch memakai head yang dilatih
pada **seluruh 740 sampul** (tanpa leave-one-out), sehingga sampul yang
dianalisis ikut dilatih. Hasil batch dataset adalah eksplorasi **in-sample**:
tidak boleh dibaca sebagai akurasi atau dibandingkan dengan Macro-F1 5-fold di
bagian 4. Uji skala 740/740 (bukti historis mesin asal,
`revisi_week3/scale740_verification.json`) membuktikan alurnya berjalan, bukan
akurasinya. Item unggahan di batch menunggu konfirmasi judul sebelum
dianalisis dan, seperti analisis satuan, tidak memiliki label pembanding.

### OCR pada mode unggahan

Unggahan menjalankan OCR otomatis (EasyOCR) untuk mengisi judul utama dan
menawarkan "Pilihan judul hasil pembacaan otomatis". Kualitasnya masih
terbatas:

- *Riwayat 5 Oktober:* selector judul saat itu tepat pada **19/30 (63,3%)**
  set diagnosis (`revisi_week3/selector_comparison.json`). Set ini **bukan set
  independen**: 20 contoh diagnosis historis ditambah 10 contoh variasi
  panjang judul, belum representatif secara layout.
- Audit urutan 6 Oktober (`docs/AUDIT_OCR_URUTAN_20261006.md`): teks pendukung
  kini disusun menurut tata letak (kolom teaser tidak lagi saling menyelip).
  Pada set validasi independen 60 sampul, urutan teks pendukung sempurna naik
  13→35/56 dan judul tepat 41→43/60; tiga judul yang memburuk kemudian
  diperbaiki. Pada validasi kedua 60 sampul (per sore 6 Oktober): judul tepat
  37→39/60 (65%) tanpa judul yang memburuk. Salah baca huruf tidak berubah,
  dan judul yang salah pilih blok bisa menyerap kalimat deck (batas 6 baris
  judul dipertahankan atas keputusan user).
- Malam 6 Oktober, sampah teks baku sampul yang salah terbaca (footer
  tempo.co/mingguan, label rubrik, harga/ISSN rusak, potongan acak huruf+angka,
  pecahan logo) dibuang, dan filter rubrik tidak lagi membuang kata judul sah.
  **Versi aplikasi terakhir:** judul tepat 41/60 (68%) pada validasi kedua dan
  47/60 (78%) pada validasi pertama, tanpa judul yang memburuk dibanding
  sebelum audit. Kedua set sudah ikut dipakai saat perbaikan, jadi angka ini
  cenderung optimistis; angka saat kode dibekukan 63–72% (rincian di laporan
  audit OCR).
- Tiga foto asli dosen: **2/3** judul tepat. GULA-GULA dan CUKAI tepat;
  WASWAS terbaca `VJASWAS RUPIAH` di server 6 Oktober (`VJJASWAS` di mesin
  asal — perbedaan kemungkinan karena versi pustaka).
- Sasaran 80% adalah usulan, belum tercapai.
- Skor pembacaan OCR bukan peluang judul benar.

Karena itu **koreksi manual tersedia dan wajib diperiksa**: model dan XAI
selalu memakai teks final di kolom judul/teks pendukung, bukan hasil OCR
mentah. Sejak 6 Oktober, memilih gambar baru (atau berkas yang sama lagi)
selalu menjalankan OCR ulang dan **mengganti** judul serta teks pendukung,
termasuk yang sudah disunting untuk gambar sebelumnya; hanya ketikan selama
OCR gambar itu berjalan yang tidak ditimpa. Periksa ulang kedua kolom setiap
kali gambar diganti. Atribusi kata dan penjelasan hanya sebaik judul yang
diperiksa pengguna.

### Batas masukan (6 Oktober)

Untuk melindungi server, masukan dibatasi (`02_web_demo/app.py`): judul
≤300 karakter, teks pendukung ≤2000 karakter, unggahan analisis/OCR ≤25 MB
(permintaan batch ≤200 MB). Gambar dengan sisi >8000 px, rasio sisi >5:1
atau lebih dari 40 megapiksel ditolak; gambar yang lolos diperkecil ke sisi
terpanjang 2000 px sebelum disimpan dan diproses. Paling banyak 2 job batch
berjalan/antre; job ketiga ditolak. Galat dikembalikan sebagai JSON tanpa path
server. Analisis yang dibatalkan di browser ikut dibatalkan di server pada
titik periksa berikutnya; pelatihan ulang *leave-one-out* yang sedang berjalan
tidak dapat diputus.

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

**Versi pustaka.** `requirements.txt` hanya memuat batas bawah
(mis. `transformers>=4.40`), sehingga instalasi baru dapat memasang versi yang
lebih baru dari mesin asal. Sejak 6 Oktober tersedia
`requirements-lock-linux.txt` berisi versi persis yang lulus seluruh test di
server Linux (Python 3.10, CPU); uji instalasi bersih Linux dari paket memakai
versi yang sama. Lock ini belum diuji di Windows. Server review 6 Oktober
(Python 3.10.12, CPU saja)
terpasang antara lain transformers 5.18.0 dan torch 2.14.1+cpu; daftar
lengkap di `04_hasil_eksperimen/revisi_week3/server_baseline_20261006/pip_freeze.txt`.
Akibatnya angka probabilitas, atribusi dan peta panas **tidak dijamin
identik bit-per-bit** dengan mesin asal atau bukti historis. Contoh nyata:
OCR WASWAS terbaca `VJASWAS` di server, `VJJASWAS` di mesin asal. Regresi dan
verifikasi HTTP di server lulus (`revisi_week3/server_baseline_20261006.json`),
tetapi itu memeriksa alur dan kontrak, bukan kesamaan angka.

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

Tercatat terbuka per 6 Oktober 2026 (matriks lengkap di
[docs/STATUS_REVISI_20261006.md](docs/STATUS_REVISI_20261006.md)):

- Area logo belum dipangkas untuk menguji pergeseran fokus model (bagian 3).
- Arsitektur masih tiga head paralel; belum ada aliran bertingkat antar-task.
- Checkpoint fine-tuning Kaggle belum diunduh/diperiksa/diintegrasikan;
  keputusan integrasi masih terbuka (bagian 4).
- OCR belum mencapai sasaran usulan 80%; evaluasi pada set independen dan
  ground truth judul/teks pendukung masih perlu riset (bagian 6).
- Belum diuji: Windows dengan instalasi bersih paket terbaru, browser selain
  Chromium (Firefox/Safari), dan uji pengguna manusia. Smoke browser 6
  Oktober memakai Chromium headless otomatis, dan
  [evaluasi agen Week 3](docs/EVALUASI_AGEN_WEEK3.md) juga bukan uji pengguna
  manusia.
- Autentikasi: aplikasi tidak memiliki login. Launcher paket hanya
  mendengarkan `127.0.0.1:7860`; server review 6 Oktober dibuka di
  `0.0.0.0:7861` atas permintaan user, tanpa autentikasi (keputusan user
  tertunda).

Sudah tidak terbuka lagi: mode pemrosesan banyak sampul sekaligus (**batch**)
kini tersedia di halaman Batch (bagian 6), peta utama gabungan tiga task
(R5) sudah diterapkan (bagian 1), dan paket ZIP delivery
(`TEMPO_XAI_DELIVERY_WEEK3_20261006.zip`) sudah dibangun dan diuji dari
instalasi bersih di Linux (Windows masih terbuka, lihat butir di atas).
