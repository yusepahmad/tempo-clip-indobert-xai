# Evaluasi agen Week 3

> **Dokumen riwayat per 5 Oktober 2026.** Status terbaru: [STATUS_REVISI_20261006.md](STATUS_REVISI_20261006.md) (6 Oktober 2026). Sebagian perbaikan di bawah sudah diubah lagi 6 Okt; lihat "Koreksi 6 Oktober 2026" di akhir dokumen.

Tanggal: 2026-10-05. Atas permintaan user, tiga sub-agent melakukan evaluasi dari sudut pandang berbeda. **Tidak ada peserta manusia dan tidak ada skor kepuasan manusia.** Hasil ini inspeksi agen, bukan pengganti uji kegunaan dengan manusia.

| Agen / perspektif | Metode dan skenario | Temuan |
|---|---|---|
| Input/OCR dan batch | Inspeksi source, regresi JS respons terlambat, review edit manual/antrean/retry | Form review tanpa label/preview; input bisa terhapus saat polling; resume gagal tanpa pesan |
| Pembaca penelitian/XAI | Inspeksi source, tiga artefak HTTP terdahulu, tiga narasi sintetis | Peta utama gabungan berbeda dari narasi task pilihan; zona spasial disimpulkan logo/teks; skor berpotensi dibaca terkalibrasi |
| Pembaca awam | Inspeksi UI, seluruh25definisi, tabel13kasus dan delivery | Counter edit kandidat OCR salah tipe; sumber definisi lama; Task3 perlu konteks jenis entitas |

## Perbaikan setelah tinjauan

- Peta panas utama mengikuti task yang dipilih dan kelas yang dijelaskan.
- Zona panas dilaporkan sebagai posisi; tidak dinamai objek berdasarkan posisi saja.
- Kolom skor menyebut belum dikalibrasi sebagai peluang benar.
- Review batch memiliki label teks, preview gambar dan kandidat OCR. Input dinonaktifkan selama job aktif, sehingga polling tidak menghapus draft yang dapat diketik.
- Resume menampilkan error. Pemilihan kandidat meningkatkan counter headline yang benar.
- Katalog memuat definisi operasional baru beserta kriteria, pembeda dan contoh; narasi memakai sumber definisi yang sama.

## Batas dan penerimaan

Ketiga agen tidak menguji manusia, tidak menetapkan ground truth ambigu, dan tidak memvalidasi semua740sampul. Dua agen melaporkan API lokal belum tersedia saat tinjauan mereka; tidak diklaim sebagai browser test baru. Temuan agen dipakai untuk perbaikan konkret, lalu regresi Python/JS dan HTTP dijalankan oleh agen utama.

Definisi baru memenuhi kebutuhan rumusan operasional atas instruksi user. Penyelarasan ke seluruh anotasi historis tetap pekerjaan validasi semantik tersendiri. Tabel pemeriksaan menyediakan tempat keputusan, bukan keputusan yang dikarang. Target OCR80%, uji skala/Windows serta pengalaman pengguna manusia tetap belum terverifikasi.

## Koreksi 6 Oktober 2026

Isi di atas adalah catatan 5 Okt. Perubahan sesudahnya (bukti di [STATUS_REVISI_20261006.md](STATUS_REVISI_20261006.md)):

- **Peta panas utama:** butir "Peta panas utama mengikuti task yang dipilih" tidak berlaku lagi. Sejak 6 Okt (R5) peta utama tab Bukti gambar adalah peta gabungan tiga task, sama untuk semua pilihan task; peta task pilihan tampil sebagai blok terpisah "Bukti task pilihan: <task> — kelas <kelas>" (`01_notebook/test_r5_heatmap.js`, `04_hasil_eksperimen/revisi_week3/r5_heatmap_verification.json`).
- **Narasi:** ringkasan dan penjelasan ditulis ulang 6 Okt, tetap tanpa LLM. Catatan anotator di penjelasan task kini hanya milik task itu, dan peta datar tidak lagi diklaim punya zona dominan.
- **Uji skala/Windows:** skala 740/740 lulus di mesin asal (`scale740_verification.json`). Uji Windows lama hanya mencakup backend di folder terisolasi; instalasi bersih paket di Windows belum diuji. Smoke browser Chromium headless final 94/94 tersedia, tetapi tetap bukan uji pengguna manusia.
- Target OCR 80% masih belum tercapai — judul tepat 68–78% pada dua set validasi audit OCR 6 Okt untuk versi aplikasi terakhir (cenderung optimistis; 63–72% saat kode dibekukan).
