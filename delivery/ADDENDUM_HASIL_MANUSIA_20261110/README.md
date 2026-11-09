# Addendum Hasil Isian Manusia — 10 November 2026

Addendum ini memvalidasi berkas pada `HASIL_ISIAN/` terhadap template canonical. Snapshot R4, gold, prediksi, dan model tidak diubah.

## Status ringkas

| Revisi | Hasil audit | Status |
|---|---|---|
| R22 | 20/20 contoh terisi; kode Task 2 pada `sumber_visual`: 0/20 | Selesai sebagai verifikasi prospektif dan audit sampel; batas historis dinyatakan eksplisit |
| R23/R6 | Dua anotator × 150 sampel lengkap; kappa dihitung | Selesai; label kanonik dipertahankan untuk disagreement dan keterbatasan riwayat per-ID didokumentasikan |
| R31 | 60/60 audit lengkap; 41 usulan perubahan label | Selesai sebagai audit sensitivitas; gold/codebook tidak diubah sehingga tidak ada rerun |
| R34/R9 | Lima file × 48 skor lengkap, tetapi skor dan alasan R1–R5 identik sel demi sel | Ditolak sebagai bukti lima penilai independen; ICC tidak dilaporkan |

## R22 — review 20 contoh

- Observasi bebas: `ya` 10, `tidak` 10.
- Memuat kode Task 2 di `sumber_visual`: `tidak` 20.
- Kesimpulan terbatas: reviewer tidak menemukan kebocoran kode Task 2 pada 20 contoh. R22 ditutup sebagai verifikasi prospektif dan audit sampel; review ini tidak diklaim membuktikan isolasi proses historis atau timestamp asli.

## R23/R6 — agreement dua anotator

| Task | Exact agreement | Cohen’s κ | Disagreement |
|---|---:|---:|---:|
| Task 1 — isu | 0,6267 | 0,5721 | 56/150 |
| Task 2 — domain sumber | 0,9600 | 0,9498 | 6/150 |
| Task 3 — tipe entitas | 0,9533 | 0,9430 | 7/150 |

`R23_DISAGREEMENTS.csv` mempertahankan seluruh pasangan label yang berbeda; hasil anotator mentah tidak ditimpa. Keputusan adjudikasi konservatif mempertahankan label kanonik dataset pada semua disagreement. Riwayat eksklusi per-ID yang tidak tersedia dinyatakan sebagai keterbatasan. Dengan keputusan tersebut, R23/R6 ditutup.

## R31 — audit kelas penampung

- Task 2 `LAINNYA`: 26/30 mengusulkan perubahan; 4/30 mempertahankan label.
- Task 3 `multiple_or_other`: 15/30 mengusulkan perubahan; 15/30 mempertahankan label.
- Total usulan perubahan: 41/60.

Angka ini disimpan sebagai rekomendasi audit/sensitivitas. Keputusan penelitian mempertahankan gold dan codebook versi saat ini; karena tidak ada relabeling, evaluasi tidak dijalankan ulang dan R31 ditutup.

## R34/R9 — kegagalan independensi

Kelima `ratings.csv` memiliki 16 item × 3 dimensi dan skor Likert valid. Namun seluruh skor **dan seluruh alasan singkat** R1, R2, R3, R4, dan R5 identik pada semua 48 baris. Semua 10 pasangan profil rater identik.

Karena itu:

- file tidak diterima sebagai lima penilaian independen;
- ICC(2,1) tidak dihitung/dilaporkan;
- R34/R9 tetap terbuka;
- lima orang harus menilai paket masing-masing secara mandiri tanpa menyalin jawaban.

## Reproduksi

Jalankan `tools/integrate_human_results.py` dengan input asli, working extraction, dan output baru. `VERIFICATION.json` mencatat hash ZIP sumber serta keputusan validasi. Identitas manusia tidak diautentikasi oleh script; hanya kontrak file, nilai, dan pola duplikasi yang diperiksa.

