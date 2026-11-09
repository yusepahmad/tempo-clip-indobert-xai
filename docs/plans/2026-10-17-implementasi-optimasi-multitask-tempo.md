# Implementasi Optimasi Multitask Tempo

**Tanggal:** 2026-10-17
**Status:** done

## Tujuan
Mengimplementasikan `docs/PLAN_OPTIMASI_MULTITASK_TEMPO_2026-10-17.md` secara
bertahap dan auditable untuk mengejar Macro-F1 ≥0,70 pada ketiga task dari satu
model joint serta OCR exact match ≥80%.

## Ruang Lingkup
- Sprint 0: audit provenance E41/E42, E48/E49, dataset, split, train–serve
  parity, reproduksi metrik, frozen protocol, dan registry eksperimen.
- Sprint 1–3: model comparison, augmentation/sampling, dan optimasi joint
  berdasarkan gate Sprint 0; training GPU dijalankan melalui Kaggle.
- Sprint 4: OCR dan evaluasi/delivery setelah kandidat terkunci.
- Artefak baru ditempatkan di
  `04_hasil_eksperimen/next_research_20261017/` tanpa menimpa E01–E49.
- Tidak mengubah label, menambah data, atau mengklaim hasil independen yang
  belum tersedia.

## Langkah
1. Rekonsiliasi plan dengan kondisi workspace aktual dan audit seluruh artefak
   yang disebut sebagai dependency.
2. Buat registry eksperimen historis, audit E42, distribusi/per-class metrics,
   leakage/train–serve report, serta frozen protocol ber-hash.
3. Verifikasi autentikasi, kuota, dataset privat, dan kemampuan Kaggle tanpa
   meluncurkan training sebelum source/config/auditor lulus lokal.
4. Implementasikan model comparison termurah (M00/M01 serta reuse hasil
   M02/M03 yang sebanding); hindari mengulang eksperimen historis tanpa
   hipotesis baru.
5. Siapkan augmentation ablation dan task-specific routing berdasarkan E48;
   jalankan smoke kemudian full job Kaggle dalam anggaran yang tercatat.
6. Audit seluruh output Kaggle di server dan lokal, lalu pilih kandidat memakai
   minimum Macro-F1 tiga task.
7. Lanjutkan OCR hanya dengan holdout kedua yang tetap tertutup sampai selector
   baru dikunci.
8. Perbarui roadmap, temuan, manifest, dan changelog setelah hasil aktual.

## Risiko & Asumsi
- Pengujian berulang pada 740 sampel menimbulkan selection bias; hasil akhir
  internal OOF tidak diklaim sebagai external validation.
- Target 0,70 mungkin tidak tercapai tanpa data tambahan; ambang tidak akan
  diturunkan dan hasil negatif tetap disimpan.
- Kaggle hanya digunakan setelah status quota/pay-to-scale dan job aktif
  diperiksa; tidak membuat duplicate live job.
- Holdout OCR kedua ternyata sudah mempunyai hasil sah 69/90 (76,67%); hasil
  ini diperlakukan sebagai evaluasi final dan tidak dipakai lagi untuk tuning.
- E49 sudah tersedia lengkap dan diaudit sebagai hasil negatif; arsitektur
  task-routed MMoE yang sama tidak akan diulang.

## Verifikasi
- Sprint 0 menghasilkan seluruh output wajib dan hash yang dapat dihitung ulang.
- Setiap eksperimen memiliki config, metrics, predictions, manifest, log, dan
  decision; smoke tidak dipakai sebagai klaim kualitas.
- Kaggle output diverifikasi terhadap source/input hash dan metrik manual.
- Hanya satu model joint dengan tiga skor ≥0,70 yang dapat dipromosikan.
- Holdout OCR kedua hanya dibuka setelah selector hash dikunci.

## Hasil Akhir Implementasi

- Sprint 0–4 telah dijalankan untuk seluruh pekerjaan yang dapat dikerjakan
  dari workspace dan Kaggle.
- E42 tetap kandidat joint terbaik: Macro-F1 `0,5255/0,3956/0,4034`.
- Augmentation terpilih menghasilkan minimum `0,3564`; M04 SigLIP2 adapters
  menghasilkan minimum `0,3805`; keduanya tidak mengalahkan E42.
- OCR holdout kedua mencapai `69/90 (76,67%)`.
- Gate Macro-F1 ≥0,70 dan OCR ≥80% tidak tercapai serta tidak diturunkan.
- Acceptance Windows bersih dan uji pengguna manusia tetap menjadi pekerjaan
  eksternal pengguna; data prospektif baru tidak tersedia karena dataset tetap.
