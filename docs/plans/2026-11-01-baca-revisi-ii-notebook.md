# Membaca Revisi II Pemeriksaan Notebook

**Tanggal:** 2026-11-01
**Status:** done

## Tujuan
Memahami seluruh isi `revision/Daftar-Revisi-II-Pemeriksaan-Notebook-Joy.pdf` dan merangkum permintaan pemeriksa serta kaitannya dengan delivery terakhir.

## Ruang Lingkup
- Membaca PDF sumber, termasuk gambar/tabel bila diperlukan.
- Menulis hasil pembacaan pada plan ini dan mencatat pekerjaan selesai di `CHANGELOG.md`.
- Tidak mengubah notebook, source, model, data, PDF asli, atau paket delivery.

## Langkah
1. Ekstrak teks setiap halaman dan periksa kelengkapan pembacaan.
2. Periksa halaman bergambar secara visual bila teks tidak mencakup isinya; hasil render sementara ditempatkan di `/tmp/`.
3. Rangkum tiap revisi, keluaran yang diminta, dan kaitannya dengan temuan delivery yang sudah diperiksa.
4. Tandai plan selesai dan catat hasil di changelog.

## Risiko & Asumsi
- Permintaan saat ini adalah membaca dan memahami revisi; implementasi revisi belum diminta.
- Gambar atau anotasi mungkin tidak tertangkap ekstraksi teks sehingga perlu inspeksi visual.
- Penilaian pemeriksa dibedakan dari status aktual yang telah diverifikasi pada delivery.

## Verifikasi
- Seluruh halaman terbaca; semua nomor revisi dan kriteria keluaran tercakup dalam ringkasan.
- PDF asli serta artefak penelitian/delivery tetap utuh.

## Hasil Pembacaan

Seluruh 26 halaman PDF telah diekstrak dan dibaca dalam rentang halaman yang saling melengkapi. `pdfimages -list` tidak menemukan gambar raster tertanam; tabel tersedia sebagai teks. Tidak diperlukan OCR atau render sementara. Dokumen bertanggal 27 Oktober 2026, dari Feliks V. P. Samosir kepada Joy Eau Dia, memeriksa tiga notebook rilis 20 dan 27 Oktober. Ringkasan di bawah adalah isi/permintaan pemeriksa, bukan hasil audit ulang source atau statistik.

### Arah penelitian yang diminta

- Model utama: CLIP + IndoBERT, shared MTL layer, tiga head, Joint Loss; Qwen3-VL-8B + QLoRA hanya pembanding.
- Macro-F1 menjadi metrik utama; akurasi, macro-precision, macro-recall dan Cohen kappa melengkapi pelaporan.
- Identitas kandidat harus dipetakan dan seleksi setelah melihat hasil dinyatakan terbuka. Minimum lintas task tidak dipakai sebagai satu-satunya dasar keputusan; laporkan tiap task dan nyatakan bila memakai rata-rata Macro-F1.
- Menurut perhitungan pemeriksa, korelasi Spearman peringkat minimum micro versus minimum macro adalah +0,050 untuk 36 kandidat non-VLM; E11 berubah dari peringkat micro #1 menjadi macro #32. Angka ini belum dihitung ulang dalam pekerjaan membaca PDF.
- Pengantar meminta menuntaskan P1 sebelum eksperimen baru dan penulisan bab hasil. Beberapa butir P1 sendiri meminta komputasi/training pembanding, sehingga urutan pelaksanaan perlu ditetapkan dalam plan implementasi tersendiri.

### Seluruh butir baru dan keluaran yang diminta

| Butir | Prioritas | Tenggat 2026 | Keluaran inti |
| --- | --- | --- | --- |
| R18 | P1 | 31 Oktober | Pemetaan 36 kandidat: backbone/varian, teks, frozen/fine-tuned, head/shared layer, loss/uncertainty weighting, augmentasi; satu model utama dan pernyataan seleksi post-hoc. |
| R19 | P1 | 3 November | Hitung ulang metrik dari prediksi, tabel peringkat micro/macro 36 baris, pergeseran peringkat dan peninjauan kesimpulan E12. |
| R20 | P1 | 3 November | Dua confusion matrix Task 3, distribusi gold/prediksi, entropi, perbandingan sebelum/sesudah class weighting pada training saja. |
| R21 | P1 | 9 November | Kesetaraan input: Qwen zero-shot 740 sampel, QLoRA citra+judul, CLIP–IndoBERT dengan teks tambahan; tabel arsitektur × kekayaan input, Macro-F1/kappa/CI. |
| R22 | P1 | 31 Oktober | Provenance `deskripsi.jsonl`/`zeroshot.jsonl`: generator, prompt, model/revisi/waktu, input proses, SHA-256 dan audit manual 20 baris. |
| R23 | P1 | 9 November | Kappa antaranotator per task; bila belum ada, anotasi ganda minimal 150 sampul; riwayat 1.040→740 dan sensitivitas sampel yang dikeluarkan. |
| R24 | P2 | 10 November | Tabel Macro-F1 utama, akurasi, kappa, precision/recall dan metrik per kelas; revisi penamaan/seleksi dalam `results.py`. |
| R25 | P2 | 16 November | CI Wilson 95% akurasi, bootstrap Macro-F1 minimal 2.000 resampling, tabel McNemar berpasangan, pembulatan poin persentase dua desimal. |
| R26 | P2 | 16 November | Jumlah konfigurasi pasti, pilihan penanganan bias seleksi; pengungkapan pemakaian ulang korpus, dengan validasi eksternal sebagai opsi. |
| R27 | P2 | 16 November | Buka e48 single-task, e49 dan J01; kesetaraan konfigurasi, tabel MTL/single-task dengan CI/uji berpasangan dan kode Joint Loss aktual. |
| R28 | P2 | 16 November | Empat berkas prediksi baseline/ablasi, termasuk text-only judul+supporting; metrik lengkap dan perbandingan multimodal/unimodal. |
| R29 | P2 | 23 November | Ablasi M01–M04 per task, audit kesetaraan head/input/split, perbandingan backbone dan pernyataan varian CLIP utama. |
| R30 | P2 | 23 November | Parameter A00–A03, alasan AUG_SELECTED, audit rotasi/crop, pemeriksaan manual minimal 30 hasil back-translation. |
| R31 | P2 | 23 November | Macro-F1 dengan/tanpa kelas penampung, audit 30 LAINNYA + 30 multiple_or_other, pemisahan pelaporan deteksi metafora dan domain sumber. |
| R32 | P2 | 23 November | Arsip reproduksi lengkap: notebook/tools/result/prediksi/split/dataset, versi dependensi, README/ROOT/mode baca output; bukti Run all di Colab bersih. |
| R33 | P3 | 24 Desember | Naskah hasil negatif terkendali; kontribusi dataset, pembalikan peringkat dan batas arsitektur; Qwen sebagai pembanding dengan konteks perbandingan jelas. |
| R34 | P3 | 7 Desember | Audit metode visual sesuai backbone, atribusi teks kondisional, rubrik, minimal lima penilai independen, kontrol peta acak dan agreement penilai; amendemen lingkup bila gagal bersama pembimbing. |
| R35 | P3 | 24 Desember | Hapus gate keberhasilan absolut 0,70; ganti patokan komparatif terhadap majority, unimodal/single-task, dan agreement manusia; target proposal historis tetap dilaporkan jujur. |
| R36 | P3 | 24 Desember | Keterbatasan seleksi/korpus/label/split/fitur/pilot, etika penyalahgunaan, batas distribusi, dan verifikasi sitasi dari sumber resmi. |

### Butir lama dan jadwal

- Tabel Agustus mencantumkan R2, R4, R6, R8, R9, R12, R13, R16 dan R17. Ada sembilan baris, meskipun pengantar menyebut tujuh butir belum tuntas; jangan menghilangkan dua butir hanya untuk mengikuti jumlah pengantar.
- Gerbang 1: 9 November — identitas model beku, pemeringkatan ulang, provenance bersih, anotasi ganda berjalan.
- Gerbang 2: 23 November — ablasi/metrik/statistik dan reproduksi bersih; jika belum selesai, pangkas klaim/backbone/augmentasi sesuai hasil yang tersedia.
- Gerbang 3: 7 Desember — XAI dan evaluasi lima penilai; jika gagal, amendemen lingkup bersama pembimbing.
- 8–24 Desember: penulisan; 25–31 Desember: submit dan laporan akhir. Pertemuan mingguan wajib membawa artefak.
- Per 1 November, tanggal tenggat R18/R22 (31 Oktober) sudah lewat; ini tidak menetapkan status keterlambatan pekerjaan aktual karena pemenuhan tiap butir belum diaudit.

### Kaitannya dengan delivery dan hal yang perlu diverifikasi

1. Pemeriksa menyatakan hanya menerima tiga `.ipynb`, tanpa tools/source/prediksi. Pemeriksaan delivery lokal sebelumnya menemukan paket final 3,13 GB beserta source, tools dan manifest. Perbedaan ini menunjukkan perlunya mengidentifikasi arsip yang diterima pemeriksa; tidak membuktikan paket lengkap sudah dikirim atau seluruh syarat R32 terpenuhi.
2. Notebook yang tidak memuat bukti XAI tidak membuktikan implementasi web tidak ada. Pemeriksaan delivery sebelumnya mencatat runtime CLIP–IndoBERT; metode, kesetaraan dengan model utama terpilih dan evaluasi independennya masih perlu audit khusus.
3. R24 meminta memindahkan gate ke macro, sementara R35 meminta menghapus gate 0,70. Implementasi berikutnya perlu menyelaraskan keduanya: Macro-F1 sebagai metrik utama dan kriteria keberhasilan komparatif, tanpa mengubah hasil historis.
4. Klaim statistik, pembalikan peringkat, input model, provenance fitur, stratifikasi fold, serta kelayakan metode XAI dalam PDF belum diverifikasi ulang pada pekerjaan ini. Dugaan kontaminasi atau kolaps bukan temuan baru yang telah terbukti oleh pembacaan PDF saja.
5. Tidak ada implementasi revisi, training, pengiriman, perubahan notebook, atau perubahan paket delivery dalam task ini.
