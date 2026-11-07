# Keputusan Kandidat Model — Sprint 2

**Tanggal:** 17 Oktober 2026  
**Status:** target 0,70 wajib; tidak ada kandidat yang lulus dan model delivery
belum diganti.

## Aturan ranking

Ranking utama hanya menerima kandidat yang:

1. menghasilkan ketiga skor dari model/protokol yang sama;
2. memiliki prediksi OOF 740 sampel dan root verification berstatus `passed`;
3. tidak mengambil skor terbaik per task dari eksperimen berbeda.

Urutan ditentukan oleh Macro-F1 terendah dari ketiga task, menurun. Mean ketiga
task menjadi tie-breaker. Tujuannya mencegah model dipilih hanya karena satu task
bagus sementara task lain dikorbankan.

## Ranking terverifikasi

| Rank | Model | Task 1 | Task 2 | Task 3 | Minimum | Mean |
|---:|---|---:|---:|---:|---:|---:|
| 1 | **E42** | 0,5255 | 0,3956 | 0,4034 | **0,3956** | **0,4415** |
| 2 | E44 | 0,5255 | 0,3937 | 0,4038 | 0,3937 | 0,4410 |
| 3 | E41 | 0,4957 | 0,4207 | 0,3857 | 0,3857 | 0,4340 |
| 4 | E47 | 0,4565 | 0,4248 | 0,3759 | 0,3759 | 0,4191 |
| 5 | E38 | 0,4835 | 0,4055 | 0,3747 | 0,3747 | 0,4212 |
| 6 | E40 | 0,4617 | 0,4183 | 0,3736 | 0,3736 | 0,4179 |
| 7 | E43 | 0,4673 | 0,4246 | 0,3675 | 0,3675 | 0,4198 |
| 8 | E46 | 0,4575 | 0,4178 | 0,3534 | 0,3534 | 0,4096 |
| 9 | E36 | 0,4178 | 0,4315 | 0,3455 | 0,3455 | 0,3983 |
| 10 | E37 | 0,4851 | 0,3692 | 0,3443 | 0,3443 | 0,3996 |
| 11 | E39 | 0,4304 | 0,4348 | 0,3366 | 0,3366 | 0,4006 |
| 12 | Baseline delivery | 0,4380 | 0,3197 | 0,2764 | 0,2764 | 0,3447 |

Sumber mesin ranking:
`DEMO_XAI_745_FULL/04_hasil_eksperimen/joint_candidate_ranking.json`.

## Keputusan sementara

**E42 dipilih sebagai kandidat riset utama untuk audit kelayakan delivery**, karena
memiliki task terlemah terbaik dan mean terbaik di antara kandidat teraudit.
Keputusan ini belum mempromosikan E42 menjadi model aplikasi.

E44 tidak dipilih karena peningkatan Task 1/3 yang sangat kecil dibayar oleh
penurunan Task 2, sehingga minimum dan mean tetap di bawah E42. E41 tetap
penting sebagai kandidat dengan audit graph/XAI paling matang, tetapi minimum
Task 3 lebih rendah daripada E42.

## Kandidat yang tidak masuk ranking utama

- E33–E35: skor tercatat dalam laporan/changelog, tetapi artefak canonical
  `root_verification.json` tidak tersedia pada result tree saat ini.
- E45: baru smoke; full experiment belum selesai.
- E12/E15/E18 dan eksperimen Task 2 saja: berguna sebagai pembanding Task 2,
  tetapi tidak sah untuk keputusan satu model joint tiga-task.
- Fine-tuning Colab: notebook tersedia, tetapi eksekusi yang dimaksud plan belum
  memiliki bukti final lokal.

## Gate yang masih harus dilalui E42

Sebelum model delivery dapat diganti, E42 harus memiliki satu paket konsisten:

- checkpoint dan source hash;
- split/data/input hash;
- reproduksi 740 prediksi OOF dan manual Macro-F1;
- pipeline unggahan baru menggunakan encoder/checkpoint yang sama;
- XAI visual dan teks yang benar-benar melewati model E42;
- batch/ekspor dan identitas versi model;
- regresi serta clean-install release.

Root audit skor E42 sudah lulus, tetapi integrasi unggahan dan XAI delivery belum
ditutup. Karena itu model aktif tetap `clip-indobert-mtl-v1`.

Root audit E42 dijalankan ulang pada 17 Oktober 2026. Auditor sintetis menerima
fixture valid dan menolak target palsu, skor Task 3 salah, OOF berubah, serta
provenance input berubah. Rekonstruksi 740 OOF kembali berstatus `passed`.

## Implikasi target 0,70

Tidak satu pun dari 12 kandidat mencapai 0,70 pada satu task terlemahnya;
minimum terbaik hanya 0,3956. Jarak ini terlalu besar untuk diasumsikan dapat
ditutup dengan tuning kecil. Jika 0,70 tetap wajib, prioritas berikutnya sebaiknya
audit label/data, external validation, dan perubahan metodologi yang memiliki
hipotesis jelas—bukan meneruskan grid hyperparameter tanpa batas pada korpus
yang sama.

Ranking ini tetap rentan selection bias karena banyak eksperimen dipilih setelah
berulang kali melihat hasil pada korpus yang sama. Ia bukan external validation.

Pada 17 Oktober 2026 pengguna menetapkan ambang 0,70 pada ketiga task sebagai
gate wajib. Karena itu E42 hanya menjadi baseline program peningkatan berikutnya,
bukan kandidat final yang dapat diterima.
