# Teks Delivery — Demo XAI Tempo (paket delivery revisi Week 3, 6 Oktober 2026)

Draf pesan serah terima. Siap disalin; sesuaikan sapaan bila perlu.

---

Yth. Bapak/Ibu,

Bersama ini kami serahkan **paket delivery revisi Week 3** Demo XAI Dekoding
Metafora Sampul Majalah Tempo (dataset final 740 sampul, model baseline),
dalam berkas `TEMPO_XAI_DELIVERY_WEEK3_20261006.zip`. Paket ini sudah diuji
dari instalasi bersih di Linux. Rinciannya ada di
`docs/plans/2026-10-06-paket-delivery-final.md`. Beberapa hal masih terbuka,
dan kami cantumkan di bawah.

**Revisi yang sudah diterapkan**

- **R1 — teks otomatis:** gambar unggahan dibaca OCR secara otomatis. Aplikasi
  menampilkan pilihan judul hasil pembacaan, lalu judul dan teks pendukung
  dapat dikoreksi manual sebelum dianalisis.
- **R2 — istilah mudah dipahami:** label dan nama task memakai bahasa
  sehari-hari (Topik utama, Ranah metafora, Pihak yang disorot).
- **R3 — kesimpulan awam:** ringkasan dan penjelasan dirangkai dari bukti
  model (bukan dibuat LLM), dengan penanda asal MODEL / ANOTATOR / CODEBOOK /
  GABUNGAN.
- **R4 — atribusi kata dengan LIME:** LIME menjadi metode baku di analisis
  satuan (sekitar 15–20 detik per analisis di CPU server).
- **R5 — peta gabungan:** peta utama di tab Bukti gambar adalah peta
  gabungan tiga task. Blok terpisah "Bukti task pilihan" menampilkan peta
  yang menjadi dasar penjelasan.
- **Katalog 25 kelas** (10 isu, 7 domain metafora, 8 tipe entitas) dengan
  codebook operasional yang kami susun sesuai arahan.
- **Batch dan ekspor:** analisis banyak sampul sekaligus (ID dataset dan/atau
  gambar unggahan), ekspor CSV/JSON, serta lanjut/ulang item yang gagal.

**Perubahan terakhir (6 Oktober)**

1. **Ringkasan dan penjelasan lebih luwes:** tab Prediksi menampilkan ringkasan
   awam untuk ketiga task sekaligus, beserta perbandingannya dengan label
   anotator. Tab Penjelasan membahas task pilihan saja, dalam bagian
   "Mengapa", "Arti kelas", "Catatan anotator" dan "Yang perlu dicek".
2. **OCR lebih rapi:** teks pendukung kini disusun menurut tata letak sampul
   sehingga teks dari kolom berbeda tidak lagi saling menyelip. Judul berhuruf
   hias lebih jarang terpotong, dan teks baku sampul yang salah terbaca (alamat
   situs, label rubrik, harga) dibuang.
3. **Unggah gambar:** memilih berkas yang sama lagi kini memicu pembacaan ulang.
   Gambar baru selalu mengganti judul dan teks dengan hasil pembacaannya.
   Nama berkas yang sedang dipakai tampil sebagai "Gambar aktif".
4. **Audit kode:** sejumlah perbaikan keamanan dan ketahanan. Antara lain,
   celah penyisipan skrip (XSS) ditutup, ukuran unggahan dan panjang teks
   dibatasi (judul ≤300 karakter, teks pendukung ≤2000 karakter, unggahan
   ≤25 MB, gambar berukuran ekstrem ditolak), analisis yang dibatalkan ikut
   berhenti di server, pilihan task tersedia di halaman Batch, dan status
   batch "gagal" kini tampil dengan benar.
5. **Notebook metodologi:** teks `DEMO_XAI_TEMPO.ipynb` dimutakhirkan dengan
   catatan beda notebook dan aplikasi; sel kode tidak berubah.

Pengujian: dari instalasi bersih paket ini di Linux, 70 test Python, 13 test
frontend dan 4 test JavaScript lulus, dan uji otomatis di browser Chromium
(desktop dan mobile) lulus 94/94. Instalasi bersih di Windows belum diuji.

**Hasil model**

Aplikasi memakai **model baseline** (CLIP + IndoBERT beku + head multi-task).
Macro-F1 5-fold: Task 1 **0,438**, Task 2 **0,320**, Task 3 **0,276**.

Full fine-tuning di Kaggle juga sudah kami selesaikan, dengan hasil
0,5139 / 0,2461 / 0,3699. Task 1 dan Task 3 naik, tetapi **Task 2 (ranah
metafora, fokus demo) turun**, sehingga kami tetap memakai baseline.
Checkpoint fine-tuning belum diintegrasikan ke aplikasi.

**Batasan yang perlu kami sampaikan**

- **OCR belum mencapai sasaran:** dengan versi aplikasi terakhir, judul
  terbaca tepat 68–78% pada dua set validasi 60 sampul. Angka ini cenderung
  optimistis karena kedua set ikut dipakai saat perbaikan (angka saat kode
  dibekukan 63–72%), dan tetap di bawah sasaran usulan 80%. Dari 3 foto sampul dari Bapak/Ibu, 2
  terbaca tepat (GULA-GULA dan CUKAI); WASWAS salah huruf. Karena itu hasil OCR
  tetap **wajib diperiksa dan dikoreksi** sebelum analisis.
- **Kelas untuk gambar unggahan tidak tervalidasi.** Atribusi kata LIME
  bergantung pada input. Contohnya pada foto GULA-GULA: kata "DEMO" bernilai
  positif bila teks pendukung kosong, tetapi bernilai negatif bila teks
  pendukung diisi hasil OCR. Dalam kasus seperti itu aplikasi menyatakan
  bahwa tidak ada kata yang berkontribusi positif. Kedua hasil ini **bukan**
  bukti bahwa kelas yang diprediksi sudah benar.
- **Model masih lebih bertumpu pada kepala sampul** (logo/judul kecil)
  daripada ilustrasi: 22 dari 25 sampul yang dianalisis.
- **Pengujian tampilan** dilakukan otomatis di Chromium. Ini **bukan uji oleh
  pengguna manusia**, dan browser lain belum diuji.

**Yang masih terbuka**

- Uji instalasi bersih di Windows.
- Uji di browser selain Chromium dan uji oleh pengguna.
- Peningkatan OCR menuju sasaran 80% dan evaluasi lanjutan.
- Eksperimen lanjutan model (E01/E02) dan keputusan apakah checkpoint
  fine-tuning akan diintegrasikan.
- Autentikasi bila aplikasi akan dibuka di jaringan. Bawaannya, aplikasi hanya
  dapat diakses dari komputer yang menjalankannya.

Cara menjalankan ada di `MULAI_DARI_SINI.md` (aplikasi terbuka di
http://127.0.0.1:7860). Gambaran paket ada di `00_BACA_DULU.md`, panduan
pemakaian di `01_TUTORIAL.md`, batasan teknis di `02_BATASAN_TEKNIS.md`, dan
status per revisi di `docs/STATUS_REVISI_20261006.md`. Integritas berkas dapat
dicek dengan `DELIVERY_MANIFEST.json` (SHA256 tiap berkas).

Masukan Bapak/Ibu atas paket ini akan sangat membantu kami. Terima kasih.

Hormat kami,
