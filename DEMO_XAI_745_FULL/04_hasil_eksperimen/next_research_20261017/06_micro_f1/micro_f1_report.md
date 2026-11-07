# Laporan Target Micro-F1 0,70

Untuk multiclass single-label, micro-F1 identik dengan accuracy. Semua skor berasal dari 740 OOF pada split E42.

| Model | Task 1 | Task 2 | Task 3 | Minimum | Gate |
| --- | ---: | ---: | ---: | ---: | --- |
| MICRO_E14_joint_qlora_oof | 0.7203 | 0.5662 | 0.6676 | 0.5662 | Gagal |
| MICRO_E11_hierarchical_task3 | 0.5811 | 0.5595 | 0.5324 | 0.5324 | Gagal |
| MICRO_E10_nested_vlm_stacking | 0.5811 | 0.5595 | 0.5270 | 0.5270 | Gagal |
| MICRO_E12_structured_decoder | 0.5784 | 0.5446 | 0.5108 | 0.5108 | Gagal |
| MICRO_E02_nested_stacking | 0.5311 | 0.5041 | 0.5392 | 0.5041 | Gagal |
| MICRO_E08_vlm_embeddings | 0.5554 | 0.5378 | 0.4824 | 0.4824 | Gagal |
| MICRO_E06_vlm_text | 0.5351 | 0.5122 | 0.4635 | 0.4635 | Gagal |
| MICRO_E05_siglip_finetune | 0.4514 | 0.5203 | 0.4865 | 0.4514 | Gagal |
| E42 | 0.5541 | 0.4351 | 0.5189 | 0.4351 | Gagal |
| MICRO_E03_classifier_chain | 0.4216 | 0.3595 | 0.4689 | 0.3595 | Gagal |
| MICRO_E04_lexical | 0.4743 | 0.2649 | 0.4473 | 0.2649 | Gagal |

Kandidat terbaik saat ini adalah **MICRO_E14_joint_qlora_oof** dengan minimum micro-F1 **0.5662**.

Evaluasi ini internal. Pemilihan model berulang pada korpus sama menyebabkan bias seleksi tingkat penelitian; bukan hasil validasi independen baru.

## MICRO-E07 smoke

Selesai pada 24 sampel fold 1, Micro-F1: {'task1_issue': 0.625, 'task2_domain_sumber': 0.5416666666666666, 'task3_primary_entity_type': 0.4583333333333333}. Hanya diagnostic smoke; tidak masuk ranking 740 OOF. Training smoke 48 sampel belum cukup menyimpulkan QLoRA secara umum gagal. Pilot inner-training penuh MICRO-E13 menilai kelayakan selanjutnya.

## MICRO-E13 inner-validation pilot

Status complete; epoch terpilih 3 dari 6. Micro-F1 pada 119 validation sampel: {'task1_issue': 0.7226890756302521, 'task2_domain_sumber': 0.5882352941176471, 'task3_primary_entity_type': 0.680672268907563}. Kontrol pada split sama: {'task1_issue': 0.5546218487394958, 'task2_domain_sumber': 0.4957983193277311, 'task3_primary_entity_type': 0.5546218487394958}. Kenaikan minimum 9.24 poin persentase; gate praktis pilot: True.

Tidak masuk ranking OOF: epoch dipilih pada validation ini, outer-test belum dievaluasi. Ketiga skor berasal dari satu epoch/adapter yang sama. Target 0,70 pada 740 OOF belum terbukti.

Oracle hanya menunjukkan complementarity dan tidak eligible sebagai model. Tidak ada aturan yang boleh melihat truth outer-test untuk memilih prediksi.
