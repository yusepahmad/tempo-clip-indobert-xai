# Sprint 2 — Keputusan Model dan Target Penelitian

**Tanggal:** 2026-10-17
**Status:** in-progress

## Tujuan
Menyusun inventaris dan ranking kandidat model berdasarkan bukti OOF 740 sampel
yang dapat dibandingkan, merekonsiliasi eksperimen terbuka, dan menghasilkan
rekomendasi model tanpa menggabungkan skor dari model berbeda atau melakukan
promosi delivery sebelum gate lengkap.

## Ruang Lingkup
- Audit hasil eksperimen baseline dan E01–E47 yang tersedia secara lokal.
- Memasukkan kandidat ke ranking utama hanya bila ketiga task berasal dari satu
  model/protokol yang sama dan bukti OOF/audit memadai.
- Menyajikan metrik per task, minimum antar-task, mean antar-task, dan status
  reproducibility/gate.
- Merekonsiliasi E12, E15, E18, E45, fine-tuning Colab, dan valid seven-class
  decoding berdasarkan bukti lokal.
- Menentukan kandidat audit berikutnya; tidak mempromosikan checkpoint atau
  mengganti model delivery secara otomatis.
- Tidak mengubah dataset, split, label, checkpoint, maupun hasil eksperimen.

## Langkah
1. Temukan seluruh artefak hasil dan dokumen audit model.
2. Ekstrak skor tiga task, jumlah sampel, protokol, model ID, serta status audit.
3. Pisahkan kandidat joint tiga-task dari eksperimen Task 2 saja atau kandidat
   dengan protokol yang tidak sebanding.
4. Hitung ranking deterministik berdasarkan minimum Macro-F1 tiga task, lalu
   mean sebagai tie-breaker; baseline delivery tetap dicatat terpisah.
5. Audit status eksperimen terbuka dan dependency yang belum selesai.
6. Susun rekomendasi kandidat tanpa mengklaim target 0,70 tercapai.
7. Verifikasi laporan terhadap artefak sumber, lalu perbarui roadmap dan
   `CHANGELOG.md`.

## Risiko & Asumsi
- Nama field dan format hasil berbeda antar eksperimen; ekstraksi otomatis harus
  divalidasi terhadap laporan/auditor masing-masing.
- Banyak eksperimen Task 2 tidak sah dibandingkan sebagai kandidat model tiga
  task dan harus ditempatkan pada tabel pembanding terpisah.
- Eksperimen berulang pada korpus yang sama meningkatkan risiko selection bias;
  ranking bukan external validation.
- Keputusan apakah ambang 0,70 wajib masih menunggu pengguna/peneliti.

## Keputusan Pengguna 17 Oktober 2026

Target **Macro-F1 minimal 0,70 untuk ketiga task pada satu model yang sama wajib
tercapai**. E42 tetap kandidat terbaik saat ini, tetapi tidak memenuhi gate dan
tidak boleh menjadi final delivery. Sprint harus berlanjut sebagai program
peningkatan model yang menjaga split/label tetap sah dan tidak menggabungkan
skor dari model berbeda.

## Verifikasi
- Setiap angka pada ranking memiliki path artefak sumber.
- Satu baris hanya berisi tiga skor dari model/protokol yang sama.
- Perhitungan minimum/mean dapat direproduksi oleh script audit.
- Kandidat yang tidak lengkap tidak masuk ranking utama.
- Tidak ada file hasil/checkpoint lama yang diubah.
