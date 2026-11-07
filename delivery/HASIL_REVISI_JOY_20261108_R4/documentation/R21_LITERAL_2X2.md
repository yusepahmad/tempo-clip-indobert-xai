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
