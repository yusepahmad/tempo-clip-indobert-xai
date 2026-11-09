# Timeline 3 Minggu — Revisi Demo XAI Tempo

**Tanggal:** 2026-09-22
**Deadline:** 12 Oktober 2026
**Status:** done

> Ditutup sebagai timeline historis pada 17 Oktober 2026. Implementasi dan
> bukti lanjutan berada di `docs/DELIVERY_WEEK_3.md`,
> `docs/DELIVERY_MAIN_MODEL.md`, dan `docs/SPRINT_ROADMAP.md`. Checkbox Week 3
> di bawah merekam keadaan rencana awal, bukan status workspace terbaru.

**Judul project:** Eksperimen Multi-Task Learning CLIP-IndoBERT Berbasis XAI
untuk Dekoding Metafora Sampul Majalah Tempo

## Tujuan

Dosen akan mengirim seluruh sampul; sistem harus mengeluarkan output lengkap
sesuai yang sudah dibangun **plus** lima revisi 15 Sep. Target akhir: mode
batch dan satu-per-satu, keduanya jalan.

## Keputusan yang mengunci ruang lingkup

Diputuskan 22 Sep 2026:

| Isu | Keputusan | Konsekuensi |
|---|---|---|
| Arsitektur model | **Tidak diubah** — 3 head paralel dipertahankan | Tidak ada pelatihan ulang; metrik skripsi tetap valid. Kaskade antar-task di diagram jadi rencana lanjutan, ditulis di Batasan |
| Atribusi teks (R4) | **Implementasi LIME sungguhan** | Menutup celah diagram-vs-kode; berpeluang memperbaiki R4 |
| Fokus model ke logo (22/25) | **Dilaporkan jujur sebagai temuan** | Tidak ada cropping/latih ulang. Jadi kekuatan narasi XAI, bukan cacat disembunyikan |
| Bentuk output | **Batch dan satu-per-satu** | Satu core pemrosesan, dua mode UI |

## Ruang lingkup

Disentuh: `02_web_demo/` (xai_core.py, app.py, index.html), file baru untuk
OCR/LIME/label display/sintesis, `docs/`, `CHANGELOG.md`.

**Tidak disentuh:** `03_data/` (dataset **tidak** diubah — perintah tegas
dosen pada R2), `05_gambar/`, arsitektur `KepalaMTL`, hasil di
`04_hasil_eksperimen/` (kecuali menambah hasil eksperimen LIME).

---

## MINGGU 1 — Fondasi & perbaikan yang pasti (22–28 Sep)

Semua item minggu ini berisiko rendah dan tidak bergantung eksperimen.

### Hari 1–2: Bersih-bersih + R2 (rename label)
- [x] Perbaiki bug format `+-0.023` (`xai_core.py:419-420`) dan logika keliru
      "paling menopang" untuk kontribusi negatif
- [x] Perbaiki bug `GABUNGAN` tidak muncul: tangani `catatan = None` di mode
      unggahan, dan string `"nan"` pada 83 sampul NON_METAFORA
- [x] Buang teks usang versi 189: `index.html:347` ("Macro-F1 0,174"),
      `DEFINISI_DOMAIN` ("12 sampul"→63, "16 dari 189"→83), komentar `app.py`
- [x] **R2**: buat `label_display.py` — peta nama kelas teknis → istilah awam
      untuk **seluruh** kelas 3 task (10+7+8). Dataset tidak disentuh
- [x] Tulis `02_BATASAN_TEKNIS.md` yang hilang (dirujuk 2× di tutorial)

**Keluaran:** semua bug tampilan tertutup, label terbaca manusia.

### Hari 3–5: R1 (OCR otomatis)
- [x] Uji banding TrOCR (saran dosen) vs EasyOCR/PaddleOCR pada ~20 sampul
- [x] Ukur akurasi headline, catat hasil sebagai bukti eksperimen
- [x] Integrasikan pemenang: upload gambar → headline terisi otomatis,
      tetap **bisa disunting manual** (OCR tak pernah sempurna)
- [x] Tulis justifikasi pemilihan (dosen mengizinkan: "kalo bisa pake yang lain")

**Keluaran:** dosen tidak perlu mengetik ulang headline.

### Hari 6–7: R5 (heatmap terpadu)
- [x] Buat heatmap gabungan: rata-rata cam task1+2+3 setelah normalisasi
      masing-masing
- [x] Mode teknis tetap bisa menampilkan 3 heatmap terpisah; mode user hanya
      satu
- [ ] Verifikasi pada sampul "CUKAI ABAL-ABAL ROKOK ILEGAL" dari revisi
      **Terblokir**: sampul itu tidak ada di dataset 740 (diunggah dosen, bukan
      dari korpus). R5 sudah diverifikasi pada sampul dataset lain; untuk sampul
      ini perlu berkas gambarnya dari dosen.

**Checkpoint M1: TERCAPAI (22 Sep 2026).** R1, R2, R5 selesai dan
terverifikasi lewat HTTP dengan model sungguhan. Sembilan bug tertutup.
Ditambahkan di luar rencana: dukungan Windows (skrip setup + menjalankan),
pembersihan cache, dan laporan `docs/DELIVERY_WEEK_1.md`.

---

## MINGGU 2 — LIME & lapisan sintesis (29 Sep – 5 Okt)

Bagian paling berisiko ditaruh di sini, supaya masih ada minggu penyangga.

### Hari 8–11: R4 — LIME sungguhan
- [x] Implementasi LIME dengan surrogate model untuk atribusi kata
- [x] Bandingkan LIME vs occlusion pada kasus uji dosen
      ("GULA-GULA DEMO BURUH" — sekarang DEMO −0,087, BURUH −0,089)
- [x] Simpan perbandingan ke `04_hasil_eksperimen/` sebagai bukti
- [x] Occlusion **tidak dihapus** — tetap tersedia sebagai pembanding

**Kriteria berhasil:** "DEMO" dan "BURUH" tidak lagi bernilai negatif, atau
ada penjelasan berbasis data mengapa tetap begitu.

**Rencana cadangan** (bila LIME tidak memperbaiki, putuskan paling lambat
hari 11): laporkan sebagai batasan dengan bukti dua metode sudah diuji.
Ini tetap hasil yang sah untuk skripsi.

### Hari 12–14: R3 — Synthesized Macro-Label + paragraf awam
- [x] Lapisan sintesis: gabungkan 3 prediksi + zona dominan + kata kunci LIME
      → satu paragraf berbahasa awam ("apa pesan tersirat sampul ini")
- [x] Berbasis template/aturan, **bukan** model bahasa — supaya tetap bisa
      dilacak asalnya, konsisten dengan prinsip paket ini
- [x] Kaitkan judul dengan konteks bawah (permintaan "Konteks Key word", hal.5)
      — `xai_core.py:899-920` (`susun_kesimpulan`): kata kunci teratas
      disandingkan langsung dengan isu yang diprediksi ("Kata 'X' pada judul
      yang paling mengarahkan model ke pembacaan Y itu"), kata yang menarik
      ke arah berbeda ikut disebut bila pengaruhnya ≥50% dari kata teratas.
      Diverifikasi ulang lewat HTTP 29 Sep (checkbox sempat tertinggal tak
      tercentang meski kodenya sudah ada sejak 28 Sep)
- [x] Tampilkan di bawah bagian teknis (sesuai "untuk sementara biar saja
      begitu tapi tambah penjelasan di akhir di bawahnya")

**Checkpoint M2: TERCAPAI (28 Sep 2026).** R3 dan R4 selesai dan
terverifikasi lewat HTTP. Kelima revisi tertutup.

- R4: LIME dipakai sebagai metode baku (gejala "seluruh kata negatif"
  1/25 vs 2/25 occlusion); occlusion tetap tersedia untuk mode batch.
- R3: paragraf kesimpulan dirangkai tanpa model bahasa, menyatakan
  keraguannya bila dasarnya lemah.
- Catatan: kasus spesifik dosen belum dapat diuji ulang — sampulnya bukan
  bagian dari korpus 740. Perlu diminta berkasnya.

---

## Proposal tambahan untuk Minggu 3 — menunggu ACC dosen (ditulis 29 Sep)

Dua batasan tercatat di `02_BATASAN_TEKNIS.md` (performa model 0,320 dan
bias ke zona logo, 22/25 sampul) **tidak bisa diperbaiki dalam ruang
lingkup yang sudah disepakati 22 September** — dataset dan arsitektur model
dikunci tidak berubah. Memperkaya dataset (anotasi tambahan per kelas) juga
bukan pekerjaan teknis: itu proses manual anotator/dosen, bukan sesuatu yang
bisa dikerjakan sepihak.

Dua opsi berikut **memerlukan ACC dosen sebelum dikerjakan**, karena
mengubah premis yang sudah dikunci:

### Opsi A — Crop area logo (risiko rendah, direkomendasikan diajukan dulu)
- **Apa:** pangkas area logo/judul kecil pada gambar sebelum masuk encoder
  CLIP, lalu latih ulang head MTL dan evaluasi ulang 5-fold CV
- **Tujuan:** menguji apakah fokus model bergeser ke ilustrasi metafora
  setelah jalan pintas (logo TEMPO yang posisinya konsisten) dihilangkan
- **Tidak menyentuh:** arsitektur `KepalaMTL`, dataset mentah (hanya
  preprocessing gambar sebelum fitur diekstrak)
- **Perkiraan waktu:** 2-3 hari (crop + ekstraksi ulang fitur CLIP + 5-fold
  CV ulang + update dokumen batasan)
- **Risiko:** hasil bisa dua arah — fokus bergeser ke ilustrasi (temuan
  positif) atau tetap ke area lain seperti headline besar (temuan negatif
  yang tetap sah dilaporkan)

### Opsi B — Fine-tuning encoder CLIP/IndoBERT (risiko tinggi, skala waktu
tidak pasti)
- **Apa:** melepas sebagian pembekuan encoder (partial unfreeze), latih
  ulang dengan learning rate kecil dan regularisasi ketat
- **Kenapa berisiko:** encoder dibekukan sejak awal justru karena 740
  sampul dinilai terlalu sedikit untuk melatih ulang ratusan juta parameter
  tanpa overfitting (lihat Bagian 3 notebook demo). Fine-tuning yang asal
  dijalankan berisiko memperburuk hasil, bukan memperbaikinya
- **Dampak beruntun bila disetujui:** seluruh angka Macro-F1 di
  `04_hasil_eksperimen/`, `02_BATASAN_TEKNIS.md`, notebook demo, dan
  `index.html` perlu dihitung ulang dan didokumentasikan ulang — ini bukan
  patch kecil, tapi eksperimen baru yang mengubah metrik skripsi
- **Perkiraan waktu:** tidak dapat dipastikan tanpa scoping lebih dulu
  (strategi unfreeze mana yang dicoba, berapa kali validasi silang
  diperlukan untuk memastikan tidak overfitting) — **jangan dijanjikan ke
  dosen sebagai selesai dalam Minggu 3** tanpa scoping terpisah lebih dulu

**Rekomendasi urutan pengajuan:** ajukan Opsi A dulu sebagai eksperimen
tambahan Minggu 3 (risiko rendah, waktu realistis). Opsi B diajukan
terpisah sebagai kemungkinan penelitian lanjutan pasca-Minggu 3, dengan
scoping waktu sendiri — jangan digabung ke deadline 12 Oktober.

---

## MINGGU 3 — Batch, pengujian, dokumentasi (6–12 Okt)

### Hari 15–17: Mode batch
- [ ] Endpoint batch: unggah banyak sampul sekaligus
- [ ] Satu core pemrosesan dipakai dua mode (batch & satu-per-satu)
- [ ] Ekspor hasil (CSV/JSON) agar dosen bisa menelaah offline
- [ ] Indikator progres — 740 sampul tidak selesai seketika

### Hari 18–19: Pengujian menyeluruh
- [ ] Uji end-to-end kedua mode
- [ ] Uji kasus batas: OCR gagal, gambar rusak, headline kosong,
      Grad-CAM mengembalikan None
- [ ] Uji ulang seluruh kasus dari `revision.pdf`

### Hari 20–21: Dokumentasi & penyerahan
- [ ] Perbarui `00_BACA_DULU.md`, `01_TUTORIAL.md`, `TEKS_DELIVERY.md`
- [ ] Tulis bagian **Batasan**: temuan fokus-ke-logo (22/25), kaskade
      antar-task belum diimplementasikan, akurasi OCR
- [ ] Dokumen pemetaan revisi → implementasi (bukti tiap butir dijawab)
- [ ] `CHANGELOG.md` final

**Checkpoint M3:** paket siap kirim.

---

## Risiko

| Risiko | Dampak | Penanganan |
|---|---|---|
| LIME tidak memperbaiki R4 | Sedang | Cadangan sudah disiapkan (hari 11); tetap jadi bukti eksperimen |
| OCR buruk pada sampul berlatar ilustrasi | Sedang | Headline tetap dapat disunting manual; uji banding 2 pustaka dulu |
| Batch 740 sampul terlalu lambat | Rendah | Leave-one-out mahal → untuk batch pakai satu model terlatih penuh, bukan per-sampul |
| Dosen menambah revisi baru di tengah jalan | Sedang | Dosen sudah bilang "ga harus mingdep selesai semua"; prioritas R1-R5 dulu |

## Verifikasi keberhasilan

1. Kelima revisi (R1–R5) tertutup, tiap butir bisa ditunjuk bukti implementasinya
2. Dosen bisa unggah sampul — satuan maupun banyak — tanpa mengetik headline
3. Tiap sampul menghasilkan: 3 label (istilah awam), satu heatmap terpadu,
   atribusi kata LIME, dan satu paragraf kesimpulan awam
4. Batasan tertulis jujur, tidak ada klaim yang tidak didukung data
