# Audit Penyelesaian Sprint 0–4

**Tanggal:** 2026-10-18  
**Ruang lingkup:** `PLAN_OPTIMASI_MULTITASK_TEMPO_2026-10-17.md`

## Status per sprint

| Sprint | Status implementasi | Bukti utama | Gate |
| --- | --- | --- | --- |
| 0 — audit/provenance | Selesai | `00_audit/`, `frozen_protocol.json`, registry dan manifest | Lulus audit |
| 1 — model comparison | Selesai | M00–M04, `model_comparison.csv`, OOF dan manifest | E42 tetap terbaik |
| 2 — augmentation | Selesai | A00–A03, contoh QA, ablation, fitur dan OOF | Tidak membantu minimum |
| 3 — joint optimization | Selesai | E48/E49 diagnostic, J01, M04 dan laporan joint | Target 0,70 gagal |
| 4 — OCR/evaluasi/QA | Selesai untuk bagian otomatis | laporan OCR, evaluasi kanonik, model manifest, 13/13 browser test | OCR 80% gagal; acceptance eksternal menunggu pengguna |

## Keputusan model

E42 dikunci sebagai kandidat terbaik menurut aturan maksimum minimum Macro-F1:

- Task 1: `0,525483`
- Task 2: `0,395560`
- Task 3: `0,403398`
- Minimum: `0,395560`

Model tidak dipromosikan menggantikan runtime delivery karena gate tiga task
`≥0,70` gagal. Mempertahankan runtime lama mencegah klaim bahwa model penelitian
yang gagal gate sudah menjadi model produksi.

## Keputusan OCR

Exact match pada dua holdout adalah `60/80 (75,00%)` dan `69/90 (76,67%)`.
Selector tidak dituning kembali memakai holdout yang sudah dibuka. Gate `80%`
gagal.

## Verifikasi aplikasi

- 63 test non-frontend lulus.
- 13/13 test Playwright Chromium lulus terhadap server lokal.
- Clean install Windows dan uji pengguna manusia harus dilakukan pengguna,
  sesuai pembagian kerja yang telah dinyatakan.

## Batas penyelesaian

Seluruh eksperimen dalam anggaran protokol sudah dieksekusi. Target angka tidak
tercapai dan tidak diturunkan. Peningkatan berikutnya membutuhkan data
prospektif/independen atau perubahan ruang lingkup yang disetujui; pengulangan
grid pada 740 OOF yang sama dihentikan untuk mencegah selection bias.
