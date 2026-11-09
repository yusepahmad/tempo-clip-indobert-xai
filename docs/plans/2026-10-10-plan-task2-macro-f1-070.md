# Plan peningkatan Macro-F1 Task 2 ke minimal 0,70

**Tanggal:** 2026-10-10
**Status:** approved

## Tujuan
Menguji jalur model dan fitur yang dapat menaikkan Macro-F1 Task 2 (domain sumber metafora) dari baseline sekitar 0,320 menuju target minimal 0,70, dengan evaluasi yang dapat dibandingkan dan tanpa kebocoran data.

## Ruang Lingkup
- `01_notebook/e01_vlm.py`, `e01_evaluasi.py`, kernel Kaggle E01, dan bukti di `04_hasil_eksperimen/e01_vlm/`.
- Eksperimen E01 deskripsi visual VLM, fusi fitur, dan evaluasi OOF 5-fold.
- Eksperimen E02 fine-tuning/klasifikasi terkontrol hanya bila E01 memberi dasar yang cukup.
- Dokumentasi hasil, metrik per kelas, confusion matrix, dan keputusan integrasi.
- Tidak mengubah label asli, dataset, aplikasi produksi, atau checkpoint baseline tanpa bukti.

## Langkah
1. Bekukan baseline dan protokol: split StratifiedKFold yang sama, seed 42, metrik Macro-F1 per kelas, weighted/micro F1, confusion matrix, dan interval variasi antar-fold.
2. Jalankan full E01 tahap 1 pada 740 sampul setelah memastikan kuota Kaggle dan batas waktu. Simpan deskripsi literal, label zero-shot, prompt hash, model revision, dan metadata resume.
3. Evaluasi beberapa varian tanpa kebocoran: baseline; VLM zero-shot; TF-IDF deskripsi; deskripsi + judul/teks; deskripsi + fitur CLIP/IndoBERT; fusi dengan bobot yang dituning hanya di fold latih.
4. Audit kualitas E01: validitas label, distribusi kelas, contoh salah, ketergantungan pada judul, kepatuhan mengabaikan teks, dan performa enam kelas metafora secara terpisah dari NON_METAFORA.
5. Jika belum mencapai 0,70, jalankan E02 terkontrol: head Task 2 terpisah, class-weight/focal loss, learning rate encoder kecil atau LoRA, early stopping berbasis inner validation, dan ablation input visual versus teks. Setiap kandidat memakai split dan protokol yang sama.
6. Pilih kandidat hanya jika Macro-F1 Task 2 mencapai ≥0,70 secara konsisten antar-fold dan tidak mengalami penurunan yang tidak dapat diterima pada Task 1/3. Jika target tidak tercapai, laporkan plafon empiris dan kandidat terbaik tanpa mengganti produksi secara prematur.
7. Integrasikan kandidat ke demo hanya setelah evaluasi selesai, uji regresi aplikasi, dan keputusan eksplisit berbasis bukti. Perbarui dokumentasi dan changelog.

## Risiko & Asumsi
- Target 0,70 mungkin berada di atas plafon informasi dataset; hasil E01 smoke tidak menjamin target.
- Deskripsi anotator memiliki bias karena kosong pada kelas NON_METAFORA; angka itu tidak boleh dipakai sebagai pembanding langsung.
- VLM dapat membaca teks sampul atau memakai judul sebagai jalan pintas; audit leakage wajib.
- Full Kaggle diperkirakan sekitar 1,92 jam inferensi, tetapi overhead dan kuota GPU harus diperiksa sebelum push.
- Macro-F1 0,70 pada split yang sama bukan bukti generalisasi eksternal.

## Verifikasi
- Semua eksperimen mencatat hash data/prompt/model, seed, split, konfigurasi, waktu, dan jumlah sampel.
- Evaluasi OOF dapat diulang dan menghasilkan tabel per kelas serta confusion matrix.
- Tidak ada kandidat yang diintegrasikan hanya berdasarkan satu fold, accuracy, atau hasil smoke.

## Strategi lanjutan yang disetujui
Eksperimen diteruskan secara berurutan: ensemble zero-shot + TF-IDF, fitur visual/teks dengan head terpisah, fine-tuning Task 2 atau LoRA di Kaggle, dan prompt VLM yang lebih ketat. Setiap strategi dihentikan bila tidak mengalahkan kandidat terbaik setelah evaluasi OOF; target 0,70 tetap sasaran, bukan jaminan.
