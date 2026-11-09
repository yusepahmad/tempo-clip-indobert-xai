# Addendum R21 — Qwen QLoRA Citra + Judul Literal

Addendum ini dibuat 10 November 2026 setelah job Kaggle privat `research-account/tempo-revisi-ii-qwen-headline-full` versi 2 diamati live berstatus `COMPLETE`. Hasil dikoleksi dengan collector proyek dari working copy terpisah; snapshot R4 tidak ditimpa.

## Hasil tervalidasi

| Task | Macro-F1 | 95% bootstrap CI | Accuracy | Cohen κ |
|---|---:|---:|---:|---:|
| Task 1 — isu | 0,5486 | [0,5135; 0,5824] | 0,6149 | 0,5536 |
| Task 2 — domain sumber | 0,4779 | [0,4402; 0,5146] | 0,5405 | 0,4378 |
| Task 3 — tipe entitas | 0,5029 | [0,4477; 0,5499] | 0,5824 | 0,4402 |

CI Macro-F1 memakai 2.000 bootstrap draw confusion matrix dengan seed evaluator proyek. Ini hasil internal OOF, bukan validasi eksternal atau uji ekuivalensi.

## Validasi collector

- 740 baris dan 740 `sample_id` unik.
- Lima outerfold, masing-masing 148 sampel held-out.
- Truth cocok dataset canonical; indeks test cocok fold E42.
- Probabilitas finite, berada pada [0,1], menjumlah satu, dan argmax cocok label prediksi.
- Masing-masing fold memiliki 2.220 audit prompt (740 sampel × 3 task), tanpa supporting text atau fitur E01.
- Epoch per fold `3/1/3/2/3` sesuai protocol conditional paired-input; tidak dituning ulang pada test fold.
- Hash prediksi: `f0362f73cf4722eb41b52fbd17ce6fbab3c3e4a22fbbea961d9f3ebd50173a5c`.
- Hash hasil: `dfa588a41370ca2c4616c01f067d9606e7237025cb6603df0dff11ab50d5faba`.

## Isi

- `RII_QWEN_QLORA_HEADLINE_ONLY/predictions.csv`: prediksi OOF dan probabilitas.
- `RII_QWEN_QLORA_HEADLINE_ONLY/result.json`: metadata lima fold dan hash.
- `metrics.csv`: metrik hasil regenerasi.
- `provenance/`: protocol, submission ledger, status live, dan verification collector.

Secara teknis sel QLoRA citra+judul literal R21 sudah tersedia. Penutupan akademik R21 tetap perlu memastikan cara penyajian perbandingan input diterima pembimbing; supporting-text dan headline-only tidak disamakan.

