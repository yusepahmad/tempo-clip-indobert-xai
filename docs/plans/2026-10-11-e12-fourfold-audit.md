# Audit empat fold E12 selesai

**Tanggal:** 2026-10-11
**Status:** done

## Tujuan
Memverifikasi hasil QLoRA fold1–4 yang sudah tersedia sebelum fold5 dapat dijalankan. Target keseluruhan tetap OOF740 Macro-F1 minimal0,70; hasil parsial tidak menjadi skor agregat.

## Ruang Lingkup
- Bukti server `04_hasil_eksperimen/e12_qlora/partial_four_audit/verification.json`, salinan lima artefak ringan/fold3–4 di recovery2026-10-11, plan/changelog.
- Auditor memakai seluruh pemeriksaan per fold dari sumber aggregator E12 yang ada, berhenti sebelum concatenation/penulisan agregat. Worker, data, label, hasil asli, monitor dan job aktif tidak diubah.

## Langkah
1. Jalankan pemeriksaan aggregator hanya untuk fold1–4: hash/protocol/model/input, ID/label/baselinefold/inner split, pemilihan epoch/patience/refit dan probability/argmax/F1.
2. Simpan bukti parsial terpisah dengan hash20 artefak dan source aggregator, tanpa overwrite bukti audit dua fold sebelumnya atau menghitung skor pooled parsial.
3. Salin JSON/JSONL/CSV fold3–4 saja, tanpa bobot adapter. Cocokkan semua hash salinan; hitung TP/FP/FN/confusion matrix per fold secara terpisah di lokal dan cocokkan baseline ID/fold/label.
4. Catat hasil aktual ke changelog. E15 tetap berjalan, fold5 tetap menunggu kuota aman untuk protokol yang sama.

## Risiko & Asumsi
- Empat fold tidak membuktikan skor740; tidak melakukan pemilihan model/epoch dari outer-test atau mengubah protokol untuk mengejar angka.
- Kelulusan audit konfigurasi/artefak bukan reproduksi training QLoRA; reset/base-frozen didukung cek runtime worker dan smoke yang sudah diverifikasi.

## Verifikasi
Empat hasil148 sampel,20 hash salinan cocok, manualF1/matrix/ID/fold/label tiapfold benar. Aggregate_samples_required740 dan aggregate_score_available=false wajib tercatat.

## Hasil
Empat fold lolos pemeriksaan per-fold aggregator; 20 hash salinan cocok. Pemeriksaan lokal ID/fold/label, confusion matrix dan Macro-F1 manual cocok: 0,5265211670 / 0,5533934468 / 0,5665131261 / 0,5449290553. Bukti `docs/server-recovery/2026-10-11/e12_qlora/partial_four_audit/verification.json` menyatakan aggregate_score_available=false; fold5 belum tersedia. Tidak ada skor agregat parsial atau perubahan training.
