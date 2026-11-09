# Arsitektur dan kekayaan masukan

Basic yang benar untuk model utama adalah citra + headline_verified + supporting_text_verified. Rich menambah description1000char, sumber_visual250char dan alasan500char dari E01. Label gold dan domain prediksi tidak dialirkan menjadi field fitur.

| Arsitektur | Basic | Rich |
|---|---|---|
| CLIP–IndoBERT tail controlled | RII_TAIL_MTL_WEIGHTED (128 token) | RII_TAIL_RICH256 (256 token) |
| Qwen3-VL QLoRA | RII_QWEN_QLORA_BASIC | MICRO_E14_joint_qlora_oof historis |

Zero-shot Qwen basic/rich adalah kontrol tambahan tanpa training, bukan OOF model terlatih. RII_FROZEN_MTL_RICH adalah kontrol CLS128 terpisah:736/740teks terpotong. Cache rich256 meliputi seluruh input pada data ini, tetapi tokenisasi/input efektif tetap berbeda antarmodel. Pada tail, nilai max-length ikut berubah agar rich tidak terpotong; perbandingan ini menilai konfigurasi input praktis, bukan isolasi panjang token.

Basic QLoRA memakai epoch per fold yang sama dengan pilihan inner rich historis[3,1,3,2,3], seed/refit/protokol sama; fold1 mengembalikan adapter awal pilot yang sama. Ini kontras input bersyarat pada resep rich, bukan tuningbasic independen berbasisMacro. Hanya tabel hasil yang benar-benar tersedia boleh dipakai; sel kosong tetap Not Evaluated dan R21terbuka sampai740 prediksi diverifikasi.


## Pembaruan 8 November 2026

# R21 — citra dan judul literal

Tabel ini mengikuti definisi citra+judul pada PDF; supporting text tidak masuk arm basic literal. Hasil basic lama yang memuat supporting text tetap tersedia sebagai kontrol terpisah, bukan pengganti arm literal.

| Arsitektur | Task | Citra+judul: Macro-F1 [CI]; kappa [CI] | Rich: Macro-F1 [CI]; kappa [CI] |
|---|---|---|---|
| CLIP-IndoBERT | task1_issue | 0.4197 [0.3725, 0.4632]; 0.3437 [0.3056, 0.3837] | 0.4619 [0.4175, 0.5013]; 0.4201 [0.3798, 0.4623] |
| CLIP-IndoBERT | task2_domain_sumber | 0.4557 [0.4178, 0.4900]; 0.3781 [0.3355, 0.4183] | 0.4967 [0.4584, 0.5320]; 0.4293 [0.3880, 0.4705] |
| CLIP-IndoBERT | task3_primary_entity_type | 0.3735 [0.3300, 0.4143]; 0.3459 [0.3002, 0.3913] | 0.4001 [0.3559, 0.4459]; 0.3671 [0.3239, 0.4097] |
| Qwen3-VL QLoRA | task1_issue | Not Evaluated — menunggu lima fold/740 prediksi | 0.6733 [0.6259, 0.7163]; 0.6746 [0.6363, 0.7110] |
| Qwen3-VL QLoRA | task2_domain_sumber | Not Evaluated — menunggu lima fold/740 prediksi | 0.5103 [0.4733, 0.5478]; 0.4711 [0.4308, 0.5123] |
| Qwen3-VL QLoRA | task3_primary_entity_type | Not Evaluated — menunggu lima fold/740 prediksi | 0.5955 [0.5457, 0.6417]; 0.5515 [0.5075, 0.5942] |

Rich CLIP128/256 dan QLoRA2048 memiliki kapasitas konteks berbeda. Resep epoch QLoRA diwarisi dari pilihan inner rich historis, bukan dituning ulang pada basic. Selisih mencampur konteks, pretraining dan input; tidak disebut efek fitur murni. Zero-shot rich/basic lama ada pada R21_MATRIX_DAN_ZERO_SHOT.csv dan bukan training OOF.

Status: 9/12 baris literal tersedia. Tidak ada nilai smoke yang digunakan sebagai angka penelitian.


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
