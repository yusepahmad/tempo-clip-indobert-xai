# Keputusan Sprint 1 — Model Comparison

Semua skor dihitung dari 740 OOF pada split E42 yang sama. M02 dan M03
menggunakan preprocessing native checkpoint yang dipin beserta hash weight.
Perhitungan Macro-F1 dan hash embedding telah diverifikasi ulang secara lokal.

- E42/M00 tetap terbaik menurut minimum Macro-F1 (`0,395560`).
- M02 SigLIP2 meningkatkan Task 2 menjadi `0,421342`, tetapi Task 3 turun ke
  `0,374939`; M02 dipromosikan ke augmentation sebagai kandidat representasi.
- M01 dan M03 dihentikan.
- M04 task-specific adapter menaikkan minimum SigLIP2 menjadi `0,380511`,
  tetapi tetap di bawah E42; M04 dihentikan.
- Tidak ada kandidat yang mendekati gate tiga task ≥0,70.

Karena maksimum dua kandidat diperbolehkan, Sprint 2 memakai E42 sebagai
kontrol dan M02 sebagai kandidat augmentation. Eksperimen augmentation GPU
difokuskan pada M02 karena pipeline encoder native-nya sudah tervalidasi.
