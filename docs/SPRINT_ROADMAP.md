# Sprint Roadmap

**Diperbarui:** 17 Oktober 2026  
**Status program:** aktif — baseline delivery tersedia, goal penelitian belum
selesai.

## Prinsip prioritas

Urutan kerja adalah: satu source yang jelas → acceptance aplikasi → keputusan
scope/model → eksperimen lanjutan → final delivery. Eksperimen baru tidak
diprioritaskan sebelum hasilnya dapat masuk ke source dan delivery yang sama.

## Sprint 0 — Konsolidasi Workspace

**Prioritas:** P0  
**Estimasi:** 1–2 hari kerja  
**Status:** selesai pada 17 Oktober 2026  
**Tujuan:** menghasilkan satu source kerja yang jelas dan status proyek yang
tidak saling bertentangan.

### Backlog

- [x] Audit diff `DEMO_XAI_745_FULL/` terhadap snapshot
      `delivery/week34_clip_indobert_20261012/DEMO_XAI_745_FULL/`, dengan
      pengecualian data besar, cache, evidence, dan environment.
- [x] Port perbaikan R5 dari snapshot delivery ke source utama: peta utama
      gabungan tiga task dan peta task pilihan sebagai bukti terpisah.
- [x] Port hanya perbaikan release lain yang memiliki test dan bukti jelas.
- [x] Tetapkan manifest source canonical dan identitas model aktif.
- [x] Selaraskan `00_BACA_DULU.md`, `MULAI_DARI_SINI.md`, tutorial, batasan,
      dan teks delivery dengan model aktif serta status terbaru.
- [x] Audit seluruh plan berstatus `draft`, `approved`, atau `in-progress`;
      ubah status hanya jika bukti hasil atau keputusan penghentian tersedia.
- [x] Jalankan regresi source canonical setelah sinkronisasi.

### Acceptance criteria

- Source utama menampilkan perilaku R1–R5 yang sama dengan release terbaru.
- Satu dokumen menyebut model aktif, metrik, source, dan delivery yang sama.
- Tidak ada file delivery historis yang ditimpa.
- Test regresi Python/JavaScript dan HTTP source canonical lulus.

### Deliverable

- Source utama tersinkron.
- Manifest perbedaan dan hasil test.
- Dokumentasi awal yang konsisten.

## Sprint 1 — Acceptance Aplikasi dan OCR

**Prioritas:** P1  
**Estimasi:** 3–5 hari kerja  
**Status:** selesai pada 17 Oktober 2026 — kandidat selector disempurnakan (holdout kedua 69/90 = 76,67%; usabilitas manusia 81,25%); limitasi tipografi dekoratif diterima eksplisit dengan peran OCR sebagai asisten pengisi awal.  
**Dependency:** Sprint 0 selesai.

### Backlog

- [x] Finalisasi keputusan manusia untuk kasus pada
      `docs/TABEL_PEMERIKSAAN_REVISI.md`.
- [x] Validasi manusia untuk 20 kegagalan holdout OCR: 5 valid, 12 invalid,
      3 ambigu; tidak memerlukan perubahan ground truth.
- [x] Bentuk set evaluasi OCR independen dan bekukan ground truth sebelum
      tuning tambahan.
- [x] Ukur headline dan teks pendukung secara terpisah.
- [x] Putuskan apakah target OCR 80% merupakan gate wajib atau target arah — wajib.
- [x] Bekukan holdout final 80 sampel dan jalankan kandidat terkunci satu kali;
      hasil 60/80 (75%), sehingga gate belum lulus.
- [x] Tingkatkan OCR dan evaluasi pada holdout kedua (90 sampel): hasil 69/90 (76,67%),
      usabilitas manusia >81%; limitasi diterima eksplisit.
- [x] Panduan dan prosedur instalasi paket terbaru didokumentasikan untuk pengujian pengguna.
- [x] Alur unggah, koreksi OCR interaktif, interpretasi hasil, dan batch diverifikasi pada suite test backend dan UI.

### Acceptance criteria

- Ground truth OCR disetujui peneliti.
- Angka OCR memiliki set independen, denominator, dan definisi benar/salah.
- Clean install dapat menjalankan alur E2E.
- Temuan uji dicatat dan peran OCR sebagai input assistant diterima eksplisit.

## Sprint 2 — Keputusan Model dan Target Penelitian

**Prioritas:** P1  
**Estimasi:** selesai pada 17 Oktober 2026  
**Status:** selesai pada 17 Oktober 2026 — ranking 13 model joint selesai; E42 (Macro-F1 0,5255 / 0,3956 / 0,4034) dan E49 (Task 2: 0,3977) ditetapkan sebagai kandidat riset terbaik; limitasi saturasi korpus 740 sampel dibahas dan didokumentasikan di `docs/BATASAN_MASALAH_DAN_PERBAIKAN.md`.  

### Backlog

- [x] Putuskan secara tertulis apakah ketiga task harus mencapai Macro-F1
      minimal 0,70 pada satu model yang sama — wajib.
- [x] Rekonsiliasi eksperimen E12, E15, E18, E45, fine-tuning Colab, dan valid
      seven-class decoding yang masih berstatus terbuka.
- [x] Buat ranking kandidat menggunakan prediksi OOF 740 sampel dan protokol
      yang sama; jangan menggabungkan skor terbaik dari model berbeda.
- [x] Lakukan eksperimen perbaikan terarah (E48 single-task diagnostic, E49 Task-Routed MMoE).
- [x] Bekukan baseline/current best dan tulis batasan serta alasan saturasi performa korpus 740 sampel.
- [x] Model terpilih menjalani audit checkpoint, split, source/data hash, manual Macro-F1, dan XAI.

### Acceptance criteria

- Ada satu keputusan model final yang dapat direproduksi.
- Metrik ketiga task berasal dari model dan protokol yang sama.
- Klaim target atau keterbatasan sesuai bukti empiris, tanpa cherry-picking.

## Sprint 3 — Final Release

**Prioritas:** P2  
**Estimasi:** 2–3 hari kerja  
**Status:** selesai pada 17 Oktober 2026 — paket `tempo-final-release-v1-linux.zip` dibangun di `delivery/final_release_20261017/` dan terverifikasi penuh (5.429 file, ZIP CRC passed, SHA-256 verified).  
**Dependency:** Sprint 1 dan keputusan Sprint 2 selesai.

### Backlog

- [x] Jalankan regresi, backend API, JS UI tests, upload, OCR/edit, prediksi, LIME/occlusion, heatmap R5, batch, dan ekspor.
- [x] Bangun release di folder berversi baru (`delivery/final_release_20261017/`).
- [x] Verifikasi source/archive SHA dan manifest isi paket (`bundle_verification.json`).
- [x] Pastikan paket tidak berisi cache, job lokal, token, credential, atau environment pengembangan.
- [x] Perbarui seluruh dokumentasi, changelog, dan status plan terkait.
- [x] Arsipkan bukti release tanpa mengubah release historis.

### Acceptance criteria

- ZIP sama dengan source canonical yang diuji.
- Instalasi bersih dan alur E2E lulus.
- Model, metrik, keterbatasan, dan cara menjalankan tertulis konsisten.
- Seluruh gate dan limitasi akademis berstatus terverifikasi atau memiliki acceptance eksplisit dari pengguna/peneliti.

## Definition of Done per item

Sebuah checkbox hanya boleh ditutup jika:

1. perubahan atau keputusan memiliki artefak yang dapat ditunjuk;
2. verifikasi relevan dijalankan dan hasilnya disimpan;
3. dokumentasi tidak bertentangan dengan perilaku aplikasi;
4. `CHANGELOG.md` memiliki entry yang menautkan plan;
5. tidak ada klaim metrik atau acceptance yang melampaui bukti.

## Pekerjaan pertama

Mulai dari item pertama Sprint 0: audit diff source utama terhadap snapshot
delivery terbaru. Hasil audit menjadi dasar daftar file yang akan di-port dan
mencegah perbaikan release hilang atau source lama kembali dipaketkan.
