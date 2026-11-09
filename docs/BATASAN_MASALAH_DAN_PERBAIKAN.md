# Batasan Masalah dan Rencana Perbaikan

**Proyek:** Klasifikasi Multitask Sampul Majalah Tempo dengan OCR dan XAI  
**Tanggal:** 17 Oktober 2026  
**Status:** Sprint 1 dan Sprint 2 belum final

## 1. Tujuan Sistem

Sistem menerima gambar sampul majalah Tempo, mengekstrak headline secara
otomatis, lalu melakukan klasifikasi bersama untuk tiga task. Sistem juga
menampilkan bukti visual atau XAI untuk membantu pengguna memahami hasil.

Target penerimaan yang wajib dipenuhi:

1. OCR headline exact match minimal **80%** pada data independen.
2. Macro-F1 minimal **0,70 pada masing-masing Task 1, Task 2, dan Task 3** dari
   satu model dan satu protokol evaluasi yang sama.
3. Aplikasi dapat menjalankan alur unggah, koreksi OCR, prediksi, dan
   interpretasi hasil secara konsisten.

## 2. Batasan Masalah

### 2.1 Objek penelitian

- Objek dibatasi pada gambar sampul majalah Tempo yang tersedia di dataset
  proyek.
- Sistem belum dapat diklaim berlaku untuk majalah lain, halaman artikel,
  dokumen umum, atau gambar dari domain yang berbeda.
- Variasi kualitas gambar, tipografi artistik, rotasi, kontras, objek yang
  menutupi teks, dan tata letak sampul menjadi bagian dari kesulitan OCR.

### 2.2 Dataset

- Dataset utama berisi **740 sampul**.
- Evaluasi hanya mewakili distribusi data yang tersedia dan belum membuktikan
  generalisasi terhadap edisi baru di luar dataset.
- Distribusi kelas tidak seimbang. Kelas minoritas, khususnya `other_issue`,
  membatasi jumlah sampel evaluasi seimbang yang dapat dibentuk.
- Ground truth headline berasal dari anotasi dataset. Kasus ambigu tetap perlu
  pemeriksaan manusia terhadap gambar asli.
- `supporting_text_verified` belum dibuktikan sebagai transkripsi lengkap
  seluruh teks visual. Metrik teks pendukung hanya boleh dianggap sebagai
  proxy, bukan acceptance OCR utama.

### 2.3 Ruang lingkup OCR

- Acceptance utama hanya mengukur **headline**, bukan seluruh teks pada sampul.
- Exact match dihitung setelah normalisasi kapitalisasi, tanda baca, dan spasi
  sesuai evaluator proyek.
- OCR berfungsi sebagai pengisi awal. Pengguna tetap harus dapat mengoreksi
  teks sebelum analisis apabila hasil pembacaan tidak tepat.
- Evaluasi final pertama menggunakan 80 sampel seimbang, delapan sampel untuk
  masing-masing kelas Task 1, tanpa overlap dengan 90 sampel development.
- Hasil holdout yang sudah dibuka tidak boleh digunakan kembali sebagai bukti
  independen setelah tuning lanjutan.

### 2.4 Ruang lingkup klasifikasi

- Model wajib memprediksi ketiga task melalui satu model joint/multitask.
- Kelulusan tidak boleh dihitung dari rata-rata ketiga task. Setiap task wajib
  mencapai Macro-F1 minimal 0,70.
- Metrik training, hasil pada subset terpilih, atau hasil terbaik dari model
  berbeda tidak dapat menggantikan evaluasi OOF/held-out yang sama.
- Hasil eksperimen saat ini hanya berlaku pada dataset dan protokol evaluasi
  yang tercatat di workspace.

### 2.5 XAI

- Peta XAI menunjukkan sensitivitas model, bukan bukti sebab-akibat atau
  jaminan bahwa prediksi benar.
- Peta gabungan dan peta per task harus dibedakan dengan jelas.
- Kualitas XAI tidak dapat dinilai hanya dari tampilan visual; fidelity,
  keterkaitan dengan model aktif, dan konsistensi input perlu diaudit.

### 2.6 Deployment dan pengujian pengguna

- Pengujian lokal tidak otomatis membuktikan clean install pada Windows.
- Uji pengguna manusia belum dapat digantikan oleh unit test atau evaluasi
  otomatis.
- Kompatibilitas browser selain Chromium belum boleh diklaim sebelum diuji.
- Model, cache OCR, dependency, dan aset runtime harus tersedia pada instalasi
  bersih tanpa meminjam environment pengembangan.

## 3. Kondisi Aktual dan Gap Target

| Area | Hasil terbaik teraudit | Target wajib | Gap | Status |
|---|---:|---:|---:|---|
| OCR headline final | 60/80 = **0,7500** | ≥0,8000 | 4 sampel benar | Belum lulus |
| Macro-F1 Task 1 | **0,5255** | ≥0,7000 | 0,1745 | Belum lulus |
| Macro-F1 Task 2 | **0,3956** | ≥0,7000 | 0,3044 | Belum lulus |
| Macro-F1 Task 3 | **0,4034** | ≥0,7000 | 0,2966 | Belum lulus |
| Clean install Windows | Belum diuji | E2E lulus | Belum ada bukti | Pending |
| Uji pengguna manusia | Belum dilakukan | Skenario utama lulus | Belum ada bukti | Pending |
| Browser non-Chromium | Belum diuji | Alur utama lulus | Belum ada bukti | Pending |

Model E42 adalah baseline joint terbaik berdasarkan minimum Macro-F1, tetapi
belum memenuhi target dan belum dipromosikan menjadi model delivery final.

## 4. Masalah yang Perlu Diperbaiki

### P0 — Wajib sebelum Sprint 1 dan 2 dinyatakan final

#### 4.1 Akurasi OCR headline belum mencapai 80%

Masalah:

- Hasil final pertama hanya 60/80 atau 75%.
- Sebagian kegagalan berasal dari baris judul yang hilang, pemilihan teaser,
  salah pengenalan karakter, dan tipografi dekoratif.
- Terdapat kegagalan berat ketika judul sama sekali tidak menjadi kandidat
  utama.

Perbaikan:

1. Kelompokkan 20 kegagalan menjadi kesalahan deteksi, penggabungan baris,
   pemilihan kandidat, dan pengenalan karakter.
2. Evaluasi crop adaptif, deskew, peningkatan kontras, serta OCR multi-pass
   dengan aturan pemilihan yang tidak memakai judul ground truth saat inferensi.
3. Tambahkan confidence/risk flag agar kasus ambigu wajib dikoreksi pengguna.
4. Tambahkan regression fixture untuk setiap pola kesalahan yang sudah
   diperbaiki.
5. Bekukan set evaluasi baru sebelum kandidat berikutnya dijalankan. Holdout
   80 sampel yang sudah dibuka menjadi data diagnosis dan tidak boleh disebut
   independen lagi setelah tuning.

Acceptance:

- Minimal 80% exact match pada set baru yang dibekukan sebelum evaluasi.
- Tidak ada lookup berdasarkan ID gambar atau headline dataset saat inferensi.
- Raw prediction, hash selector, hash gambar, denominator, dan kegagalan
  disimpan agar hasil dapat diaudit.

#### 4.2 Macro-F1 ketiga task masih jauh di bawah 0,70

Masalah:

- Task 2 dan Task 3 merupakan bottleneck terbesar.
- Eksperimen sebelumnya menunjukkan performa training tinggi tetapi held-out
  rendah, yang mengindikasikan generalization gap/overfitting.
- Optimasi arsitektur dan loss sebelumnya belum menghasilkan lompatan yang
  cukup untuk mencapai target.

Perbaikan:

1. Audit label dan confusion matrix per kelas, terutama kelas minoritas dan
   pasangan kelas yang sering tertukar.
2. Ukur dukungan sampel per kelas dan lakukan review label tanpa mengubah label
   hanya demi meningkatkan skor.
3. Tetapkan split/fold final yang group-safe serta cegah duplikasi atau leakage.
4. Bangun baseline sederhana per task untuk mengetahui apakah joint learning
   membantu atau justru menimbulkan negative transfer.
5. Prioritaskan perbaikan representasi dan data: augmentasi yang relevan,
   sampling seimbang, regularisasi, serta pemanfaatan teks OCR yang tervalidasi.
6. Gunakan nested selection berdasarkan nilai minimum ketiga task, bukan hanya
   task atau mean terbaik.
7. Promosikan model hanya bila satu artefak model mencapai ≥0,70 pada ketiga
   task di evaluasi canonical yang sama.

Acceptance:

- Task 1 Macro-F1 ≥0,70.
- Task 2 Macro-F1 ≥0,70.
- Task 3 Macro-F1 ≥0,70.
- Skor berasal dari satu model, satu split/protokol, dan dapat dihitung ulang
  dari prediksi tersimpan.

### P1 — Wajib sebelum release final aplikasi

#### 4.3 Validasi ground truth dan kasus ambigu

- Periksa gambar asli untuk seluruh kegagalan OCR.
- Bedakan headline, kicker, subheadline, dan teaser secara konsisten.
- Catat keputusan manusia beserta alasan; jangan mengoreksi ground truth hanya
  karena berbeda dari output model.

#### 4.4 Clean install dan dependency

- Uji pada Windows bersih dengan prosedur instalasi dari dokumentasi.
- Pastikan model, OCR, font, dan dependency terpasang tanpa cache tersembunyi.
- Jalankan alur upload → OCR → edit → prediksi → XAI → ekspor/batch.
- Catat waktu startup, penggunaan memori, kegagalan instalasi, dan solusi.

#### 4.5 Uji pengguna manusia

- Libatkan dosen atau calon pengguna yang tidak mengembangkan sistem.
- Uji kemampuan menemukan fungsi, memperbaiki OCR, memahami tiga task, dan
  menafsirkan XAI.
- Tutup masalah severity P0/P1 atau dokumentasikan penerimaan risikonya.

#### 4.6 Kompatibilitas browser dan regresi aplikasi

- Uji minimal Chromium dan satu browser lain yang disepakati.
- Periksa desktop serta viewport mobile untuk alur utama.
- Jalankan kembali unit test, backend test, JavaScript test, dan HTTP smoke test
  setelah model/OCR final dipasang.

### P2 — Kualitas dokumentasi dan reproducibility

- Sinkronkan model manifest, hash artefak, metrik, dan nama model aktif.
- Pisahkan hasil eksperimen, baseline, kandidat, dan model produksi.
- Dokumentasikan seed, fold, preprocessing, dependency, dan command evaluasi.
- Pastikan seluruh klaim pada skripsi memiliki artefak bukti yang dapat dilacak.

## 5. Urutan Pengerjaan yang Disarankan

1. Audit dan kategorisasi 20 kegagalan OCR final pertama.
2. Buat kandidat OCR berikutnya menggunakan seluruh data diagnosis yang sudah
   terbuka, lalu bekukan set evaluasi baru sebelum pengujian.
3. Audit label, distribusi kelas, leakage, dan confusion matrix ketiga task.
4. Tetapkan eksperimen model berikutnya berdasarkan hasil audit, dengan fokus
   pertama pada Task 2 dan Task 3 tanpa menjatuhkan Task 1.
5. Jalankan evaluasi canonical dan hanya promosikan artefak yang melampaui
   seluruh gate wajib.
6. Setelah OCR dan model lulus, lakukan clean install, uji pengguna, browser,
   serta regresi release lengkap.

## 6. Definisi Selesai

Sprint 1 dan Sprint 2 baru dapat dinyatakan final jika seluruh kondisi berikut
terpenuhi:

- [ ] OCR headline exact match ≥80% pada evaluasi independen yang sah.
- [ ] Macro-F1 Task 1 ≥0,70.
- [ ] Macro-F1 Task 2 ≥0,70.
- [ ] Macro-F1 Task 3 ≥0,70.
- [ ] Ground truth kasus ambigu telah diperiksa manusia.
- [ ] Model final dan selector OCR tercatat beserta SHA-256.
- [ ] Clean install Windows dan alur E2E lulus.
- [ ] Uji pengguna manusia selesai dan isu kritis ditangani.
- [ ] Regresi aplikasi serta browser target lulus.
- [ ] Dokumentasi, roadmap, dan changelog sesuai dengan artefak delivery.

## 7. Referensi Bukti

- `docs/OCR_INDEPENDENT_ACCEPTANCE.md`
- `docs/MODEL_CANDIDATE_DECISION.md`
- `docs/SPRINT_ROADMAP.md`
- `DEMO_XAI_745_FULL/04_hasil_eksperimen/revisi_week3/ocr_final_holdout/results.json`
- `DEMO_XAI_745_FULL/04_hasil_eksperimen/joint_candidate_ranking.json`
