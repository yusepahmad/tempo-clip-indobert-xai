# E04 evaluasi nested dan fitur alasan VLM

**Tanggal:** 2026-10-10
**Status:** done

## Tujuan
Memvalidasi ulang E01/E03 dan menguji sinyal deskripsi, sumber visual, alasan, domain zero-shot, serta teks asli menuju Macro-F1 Task2 0,70.

## Ruang Lingkup
- Skrip baru `DEMO_XAI_745_FULL/01_notebook/e04_nested.py`, bukti `04_hasil_eksperimen/e04_nested/`, salinan di server learn, plan dan changelog.
- Tidak mengubah dataset, label, source aplikasi, checkpoint, atau mengunduh model di luar learn.

## Langkah
1. Validasi hash CSV, keunikan/kelengkapan ID output VLM dan kesamaan split numerik baseline.
2. Gunakan Pipeline dalam inner-CV sehingga TF-IDF dan hyperparameter dipelajari dari inner-training saja.
3. Uji ablation deskripsi, domain, sumber visual, alasan, judul/pendukung dengan LR dan LinearSVC; pilih kandidat melalui inner-CV, lalu evaluasi outer-fold.
4. Simpan OOF semua sampel, konfigurasi tiap fold, klasifikasi per kelas, confusion matrix, versi dan hash.
5. Jalankan sebagai satu proses durable dengan BLAS 1 thread dan maksimal 2 job, catat hasil serta lanjutkan eksperimen sesuai bukti.
6. Pilih keluarga fitur per outer-fold memakai skor inner-CV saja, lalu gabungkan OOF kandidat terpilih. Jangan memilih keluarga fitur berdasarkan skor outer-test untuk klaim nested.

## Risiko & Asumsi
- Skrip E02/E03 sebelumnya tidak menggabungkan kelas Task1 langka dan preprocessing inner-CV belum sepenuhnya terisolasi. Angka lama eksploratif.
- Neural E02 belum menerapkan early stopping dan inferensi eval mode; hasil itu bukan bukti kegagalan fine-tuning encoder.
- Teks judul yang tersedia saat inferensi adalah fitur sah, tetapi deskripsi anotator dan mapping label tidak boleh menjadi fitur produksi.
- Pemilihan strategi berulang berdasarkan OOF dapat memberi optimisme; hasil 0,70 perlu konfirmasi tambahan sebelum klaim generalisasi.

## Verifikasi
Tiap sampel tepat sekali menjadi outer-test; split identik baseline; 740 ID cocok hash; Pipeline inner-CV lengkap; skor dapat dihitung kembali dari CSV OOF; log/proses tunggal terbukti.

## Hasil
- Enam keluarga fitur selesai. Nested family selection memakai skor inner-CV menghasilkan Macro-F1 0,5092774569, dengan 740 OOF disimpan di `docs/server-recovery/2026-10-10/e04_nested/nested_selected_oof.csv`.
- Gabungan semua fitur VLM+teks asli sebagai kandidat tetap: 0,5054959037. Deskripsi+domain: 0,4764244402.
- Hash gambar dan duplicate_group_id tidak duplikat. Semua kelas Task1 aktual ≥14 sampel, sehingga pooling kelas langka tidak mengubah split pada dataset ini; potensi perbedaan pooling di skrip lama bukan penyebab perbedaan skor aktual.
- E05 visual dan E06 semantik menjadi eksperimen berikutnya dalam plan terpisah. Target belum tercapai.
