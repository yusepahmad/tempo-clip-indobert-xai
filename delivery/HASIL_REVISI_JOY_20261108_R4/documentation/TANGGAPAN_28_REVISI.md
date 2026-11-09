# Tanggapan 28 Revisi

Status paket: **19 butir selesai secara teknis; 9 masih terbuka**. Setiap butir terbuka tetap memerlukan tindakan/bukti di bawah. Status Selesai pada draf naskah berarti materi revisi tersedia, bukan persetujuan pembimbing atau publikasi.

## R18 — Identitas dan pemetaan kandidat

Status: **Selesai**. Prioritas: P1. Tenggat asli: 31 Oktober 2026.

Bukti: `candidate_mapping_36.csv; MAIN_MODEL_DECISION.md`.

Bukti teknis dan penjelasan tersedia dalam paket; hasil tetap dibatasi oleh protokol dan data yang tersedia.

## R19 — Pemeringkatan Macro-F1

Status: **Selesai**. Prioritas: P1. Tenggat asli: 3 November 2026.

Bukti: `analysis/ranking_36_legacy.csv; analysis/rank_correlation.json`.

Bukti teknis dan penjelasan tersedia dalam paket; hasil tetap dibatasi oleh protokol dan data yang tersedia.

## R20 — Diagnosis Task 3 dan weighting

Status: **Selesai**. Prioritas: P1. Tenggat asli: 3 November 2026.

Bukti: `analysis/task3_entropy.csv; analysis/class_distribution.csv; analysis/paired_tests.csv`.

Bukti teknis dan penjelasan tersedia dalam paket; hasil tetap dibatasi oleh protokol dan data yang tersedia.

## R21 — Kesetaraan masukan dan Qwen zero-shot

Status: **Berjalan**. Prioritas: P1. Tenggat asli: 9 November 2026.

Bukti: `INPUT_PARITY.md; analysis/metrics.csv`.

Yang tersisa: Hasil belum lengkap: RII_QWEN_QLORA_HEADLINE_ONLY. Arm basic sebelumnya memuat supporting text sehingga bukan citra+judul literal yang diminta PDF.

Penanggung jawab: Eksperimen GPU/collector.

## R22 — Provenance fitur E01

Status: **Berjalan**. Prioritas: P1. Tenggat asli: 31 Oktober 2026.

Bukti: `FEATURE_PROVENANCE.json; feature_provenance_20_examples.csv`.

Yang tersisa: Generator/hash/prompt tersedia; tuntutan isolasi proses historis dan timestamp penciptaan asli belum dapat dibuktikan.

Penanggung jawab: Peneliti/pembimbing: terima bukti field-flow atau minta regenerasi fitur versi baru.

## R23 — Agreement manusia dan riwayat korpus

Status: **Berjalan**. Prioritas: P1. Tenggat asli: 9 November 2026.

Bukti: `CORPUS_HISTORY.md; HUMAN_EVIDENCE_SEARCH.json; human_inputs/annotation/`.

Yang tersisa: Alasan umum eksklusi sudah diklarifikasi Joy: kualitas citra buruk sehingga tidak dapat dilabeli, dan menurut Joy pernah disampaikan. Yang belum tersedia: dua set anotasi independen untuk kappa; dokumentasi korpus awal/keputusan per ID dan sensitivitas belum dapat direkonstruksi.

Penanggung jawab: Dua anotator; pemilik data untuk dokumentasi rinci bila tersedia.

## R24 — Macro-F1 utama, akurasi/kappa pendamping

Status: **Selesai**. Prioritas: P2. Tenggat asli: 10 November 2026.

Bukti: `analysis/metrics.csv; analysis/per_class.csv; tools/evaluate.py`.

Bukti teknis dan penjelasan tersedia dalam paket; hasil tetap dibatasi oleh protokol dan data yang tersedia.

## R25 — CI dan perbandingan berpasangan

Status: **Selesai**. Prioritas: P2. Tenggat asli: 16 November 2026.

Bukti: `analysis/metrics.csv; analysis/paired_tests.csv; STATISTICAL_METHOD.md`.

Bukti teknis dan penjelasan tersedia dalam paket; hasil tetap dibatasi oleh protokol dan data yang tersedia.

## R26 — Bias seleksi dan jumlah kandidat

Status: **Selesai**. Prioritas: P2. Tenggat asli: 16 November 2026.

Bukti: `analysis/ranking_36_legacy.csv; analysis/evaluation_verification.json; SELECTION_BIAS.md`.

Bukti teknis dan penjelasan tersedia dalam paket; hasil tetap dibatasi oleh protokol dan data yang tersedia.

## R27 — MTL versus single-task dan loss aktual

Status: **Selesai**. Prioritas: P2. Tenggat asli: 16 November 2026.

Bukti: `analysis/metrics.csv; analysis/paired_tests.csv; source/; ABLATION_PARITY.md`.

Bukti teknis dan penjelasan tersedia dalam paket; hasil tetap dibatasi oleh protokol dan data yang tersedia.

## R28 — Prediksi baseline/unimodal

Status: **Selesai**. Prioritas: P2. Tenggat asli: 16 November 2026.

Bukti: `inputs/predictions/; HISTORICAL_REPLAY.md`.

Bukti teknis dan penjelasan tersedia dalam paket; hasil tetap dibatasi oleh protokol dan data yang tersedia.

## R29 — Backbone dan SigLIP2

Status: **Selesai**. Prioritas: P2. Tenggat asli: 23 November 2026.

Bukti: `analysis/metrics.csv; analysis/paired_tests.csv; ABLATION_PARITY.md`.

Bukti teknis dan penjelasan tersedia dalam paket; hasil tetap dibatasi oleh protokol dan data yang tersedia.

## R30 — Augmentasi dan pemilihan inner

Status: **Selesai**. Prioritas: P2. Tenggat asli: 23 November 2026.

Bukti: `AUGMENTATION_AUDIT.md; analysis/metrics.csv; source/`.

Bukti teknis dan penjelasan tersedia dalam paket; hasil tetap dibatasi oleh protokol dan data yang tersedia.

## R31 — Kelas penampung dan dekomposisi Task 2

Status: **Berjalan**. Prioritas: P2. Tenggat asli: 23 November 2026.

Bukti: `analysis/catchall_sensitivity.csv; analysis/task2_decomposed.csv; human_inputs/catchall_review_60.csv`.

Yang tersisa: Tabel/codebook/sensitivitas selesai; audit manusia60 sampul dan adjudikasi codebook belum diisi.

Penanggung jawab: Joy/anotator.

## R32 — Reproduksi mandiri dan Colab bersih

Status: **Berjalan**. Prioritas: P2. Tenggat asli: 23 November 2026.

Bukti: `README.md; requirements.txt; tools/validate_package.py; qa/`.

Yang tersisa: Paket dan uji lokal disediakan; bukti Run all Colab bersih belum terverifikasi.

Penanggung jawab: Uji Colab melalui akun pengguna.

## R33 — Pembingkaian hasil penelitian

Status: **Selesai**. Prioritas: P3. Tenggat asli: 24 Desember 2026.

Bukti: `MANUSKRIP_DRAF.md; HASIL_DAN_TANGGAPAN.md`.

Bukti teknis dan penjelasan tersedia dalam paket; hasil tetap dibatasi oleh protokol dan data yang tersedia.

## R34 — XAI dan penilai independen

Status: **Berjalan**. Prioritas: P3. Tenggat asli: 7 Desember 2026.

Bukti: `xai_e42/; human_inputs/XAI_RUBRIC.md; human_inputs/xai/`.

Yang tersisa: XAI aktual/tes/model replay/rubrik/kontrol tersedia; skor nyata minimal5 penilai independen dan agreement belum tersedia.

Penanggung jawab: Joy/lima penilai independen.

## R35 — Kriteria komparatif tanpa gate0.70

Status: **Selesai**. Prioritas: P3. Tenggat asli: 24 Desember 2026.

Bukti: `MAIN_MODEL_DECISION.md; STATISTICAL_METHOD.md; tools/evaluate.py`.

Bukti teknis dan penjelasan tersedia dalam paket; hasil tetap dibatasi oleh protokol dan data yang tersedia.

## R36 — Keterbatasan, etika, sitasi

Status: **Selesai**. Prioritas: P3. Tenggat asli: 24 Desember 2026.

Bukti: `MANUSKRIP_DRAF.md; REFERENCES.md`.

Bukti teknis dan penjelasan tersedia dalam paket; hasil tetap dibatasi oleh protokol dan data yang tersedia.

## R2 — Codebook dan kelas penampung

Status: **Selesai**. Prioritas: Agustus. Tenggat asli: belum diperbarui.

Bukti: `CODEBOOK_REVISI.md; human_inputs/catchall_review_60.csv`.

Bukti teknis dan penjelasan tersedia dalam paket; hasil tetap dibatasi oleh protokol dan data yang tersedia.

## R4 — Kelayakan metode visual CLIP

Status: **Selesai**. Prioritas: Agustus. Tenggat asli: 7 Desember 2026 terkaitR34.

Bukti: `XAI_METHOD.md; xai_e42/`.

Bukti teknis dan penjelasan tersedia dalam paket; hasil tetap dibatasi oleh protokol dan data yang tersedia.

## R6 — Adjudikasi dan eksklusi

Status: **Berjalan**. Prioritas: Agustus. Tenggat asli: 9 November 2026 terkaitR23.

Bukti: `CORPUS_HISTORY.md; human_inputs/annotation/`.

Yang tersisa: Alasan umum eksklusi sudah diklarifikasi Joy: kualitas citra buruk sehingga tidak dapat dilabeli, dan menurut Joy pernah disampaikan. Yang belum tersedia: dua set anotasi independen untuk kappa; dokumentasi korpus awal/keputusan per ID dan sensitivitas belum dapat direkonstruksi.

Penanggung jawab: Dua anotator; pemilik data untuk dokumentasi rinci bila tersedia.

## R8 — Baseline dan ablasi

Status: **Berjalan**. Prioritas: Agustus. Tenggat asli: 16 November 2026 terkaitR28.

Bukti: `HISTORICAL_REPLAY.md; analysis/metrics.csv`.

Yang tersisa: Ablasi/prediksi tersedia; wording lengkap dokumen Agustus asli belum ditemukan, jadi penutupan R8 lama belum dapat dipastikan.

Penanggung jawab: Joy/pembimbing: dokumenAgustus.

## R9 — Lima penilai independen

Status: **Berjalan**. Prioritas: Agustus. Tenggat asli: 7 Desember 2026 terkaitR34.

Bukti: `human_inputs/XAI_RUBRIC.md; human_inputs/xai/`.

Yang tersisa: XAI aktual/tes/model replay/rubrik/kontrol tersedia; skor nyata minimal5 penilai independen dan agreement belum tersedia.

Penanggung jawab: Joy/lima penilai independen.

## R12 — Macro-F1 sebagai metrik utama

Status: **Selesai**. Prioritas: Agustus. Tenggat asli: 10 November 2026 terkaitR24.

Bukti: `analysis/metrics.csv; tools/evaluate.py`.

Bukti teknis dan penjelasan tersedia dalam paket; hasil tetap dibatasi oleh protokol dan data yang tersedia.

## R13 — Justifikasi ulang target

Status: **Selesai**. Prioritas: Agustus. Tenggat asli: 24 Desember 2026 terkaitR35.

Bukti: `STATISTICAL_METHOD.md; MANUSKRIP_DRAF.md`.

Bukti teknis dan penjelasan tersedia dalam paket; hasil tetap dibatasi oleh protokol dan data yang tersedia.

## R16 — Sitasi relevan dan terverifikasi

Status: **Selesai**. Prioritas: Agustus. Tenggat asli: 24 Desember 2026 terkaitR36.

Bukti: `REFERENCES.md`.

Bukti teknis dan penjelasan tersedia dalam paket; hasil tetap dibatasi oleh protokol dan data yang tersedia.

## R17 — Etika dan penyalahgunaan

Status: **Selesai**. Prioritas: Agustus. Tenggat asli: 24 Desember 2026 terkaitR36.

Bukti: `MANUSKRIP_DRAF.md`.

Bukti teknis dan penjelasan tersedia dalam paket; hasil tetap dibatasi oleh protokol dan data yang tersedia.
