# Evaluasi agen Week 3

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
