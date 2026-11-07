# R21 — hasil aktual QLoRA basic dengan supporting text

Lima fold telah dikoleksi dan diverifikasi pada 7 November 2026: tepat 740 ID unik, label/fold canonical, split, probabilitas, source/protocol dan hash input audit. Tidak ada training ulang untuk angka pada tabel ini. Bobot checkpoint tidak direplay lokal.

| experiment | task | macro_f1 | macro_ci_low | macro_ci_high | accuracy | kappa |
| --- | --- | --- | --- | --- | --- | --- |
| MICRO_E14_joint_qlora_oof | task1_issue | 0.6733 | 0.6259 | 0.7163 | 0.7203 | 0.6746 |
| MICRO_E14_joint_qlora_oof | task2_domain_sumber | 0.5103 | 0.4733 | 0.5478 | 0.5662 | 0.4711 |
| MICRO_E14_joint_qlora_oof | task3_primary_entity_type | 0.5955 | 0.5457 | 0.6417 | 0.6676 | 0.5515 |
| RII_QWEN_QLORA_BASIC | task1_issue | 0.6847 | 0.6372 | 0.7259 | 0.7365 | 0.6939 |
| RII_QWEN_QLORA_BASIC | task2_domain_sumber | 0.4927 | 0.4571 | 0.5271 | 0.5514 | 0.4537 |
| RII_QWEN_QLORA_BASIC | task3_primary_entity_type | 0.5909 | 0.5405 | 0.6361 | 0.6514 | 0.5348 |

## Perbandingan berpasangan: basic supporting → rich

| task | macro_f1_delta | macro_delta_ci_low | macro_delta_ci_high | mcnemar_exact_p | mcnemar_holm_p_three_tasks |
| --- | --- | --- | --- | --- | --- |
| task1_issue | -0.0113 | -0.0352 | 0.0124 | 0.1945 | 0.5835 |
| task2_domain_sumber | 0.0175 | -0.0189 | 0.0555 | 0.3998 | 0.5835 |
| task3_primary_entity_type | 0.0046 | -0.0320 | 0.0411 | 0.2664 | 0.5835 |

Delta adalah rich dikurangi basic; CI Macro-F1 bersifat pointwise eksploratif. McNemar/Holm menguji akurasi, bukan Macro-F1. Tidak signifikan tidak berarti setara. Family tiga task R21 dilaporkan terpisah dari family seluruh uji pada analysis/paired_tests.csv.

Arm ini memuat citra+judul+supporting text. Untuk tuntutan literal citra+judul, lihat R21_LITERAL_2X2.md dan tracker. Tabel supporting 18/18 lengkap tidak otomatis menutup R21.
