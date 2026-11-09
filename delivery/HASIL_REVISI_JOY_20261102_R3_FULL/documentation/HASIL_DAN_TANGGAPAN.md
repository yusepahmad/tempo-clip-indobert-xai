# Hasil Revisi II dan Koreksi Penafsiran

Model utama penelitian ditetapkan E42, bukan baseline web historis dan bukan Qwen. Pemilihan post-hoc berdasarkan rerata Macro-F1 kandidat proposal yang layak dinyatakan terbuka.

| experiment | task | macro_f1 | macro_ci_low | macro_ci_high | accuracy | accuracy_ci_low | accuracy_ci_high | kappa |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BASELINE_CLIP_INDoBERT | task1_issue | 0.4380 | 0.3957 | 0.4749 | 0.4554 | 0.4198 | 0.4914 | 0.3811 |
| BASELINE_CLIP_INDoBERT | task2_domain_sumber | 0.3197 | 0.2871 | 0.3511 | 0.3203 | 0.2877 | 0.3547 | 0.2067 |
| BASELINE_CLIP_INDoBERT | task3_primary_entity_type | 0.2764 | 0.2423 | 0.3103 | 0.3554 | 0.3217 | 0.3906 | 0.2157 |
| e42_tail_grid | task1_issue | 0.5255 | 0.4810 | 0.5647 | 0.5541 | 0.5181 | 0.5895 | 0.4853 |
| e42_tail_grid | task2_domain_sumber | 0.3956 | 0.3606 | 0.4295 | 0.4351 | 0.3998 | 0.4711 | 0.3154 |
| e42_tail_grid | task3_primary_entity_type | 0.4034 | 0.3555 | 0.4469 | 0.5189 | 0.4829 | 0.5547 | 0.3537 |
| MICRO_E11_hierarchical_task3 | task1_issue | 0.5103 | 0.4600 | 0.5565 | 0.5811 | 0.5452 | 0.6161 | 0.5090 |
| MICRO_E11_hierarchical_task3 | task2_domain_sumber | 0.5025 | 0.4641 | 0.5381 | 0.5595 | 0.5235 | 0.5948 | 0.4555 |
| MICRO_E11_hierarchical_task3 | task3_primary_entity_type | 0.2825 | 0.2504 | 0.3145 | 0.5324 | 0.4964 | 0.5681 | 0.3201 |
| MICRO_E12_structured_decoder | task1_issue | 0.5167 | 0.4671 | 0.5570 | 0.5784 | 0.5425 | 0.6135 | 0.5071 |
| MICRO_E12_structured_decoder | task2_domain_sumber | 0.4935 | 0.4554 | 0.5301 | 0.5446 | 0.5086 | 0.5802 | 0.4400 |
| MICRO_E12_structured_decoder | task3_primary_entity_type | 0.2872 | 0.2545 | 0.3177 | 0.5108 | 0.4748 | 0.5467 | 0.2920 |
| MICRO_E14_joint_qlora_oof | task1_issue | 0.6733 | 0.6259 | 0.7163 | 0.7203 | 0.6869 | 0.7514 | 0.6746 |
| MICRO_E14_joint_qlora_oof | task2_domain_sumber | 0.5103 | 0.4733 | 0.5478 | 0.5662 | 0.5303 | 0.6015 | 0.4711 |
| MICRO_E14_joint_qlora_oof | task3_primary_entity_type | 0.5955 | 0.5457 | 0.6417 | 0.6676 | 0.6328 | 0.7006 | 0.5515 |

Angka dalam tabel menggunakan fraksi; CSV menyimpan presisi penuh. Perbedaan poin persentase =100×selisih fraksi. Tidak ada gate kelulusan absolut0,70 dalam keputusan baru.

Ranking36 nama mereproduksi Pearson 0.395320 dan Spearman 0.064329 untuk minimum akurasi versus minimum macro. Spearman berbeda dari0,050 di PDF; ties ditangani sebagai tied ranks, bukan ordinal berdasarkan urutan baris. Kesimpulan kualitatif korelasi lemah tetap berlaku.

Filter nama non-vlm/non-qlora bukan bukti backbone: E11/E12 tetap mengandung fitur turunan VLM. M00/E42 dan representasi A00/A01/selected mempunyai salinan prediksi; jumlah nama bukan jumlah eksperimen independen.

Baselinehistoris memang lebih rendah dari majority pada akurasi Task 3, tetapi diagnosis itu tidak boleh otomatis dipindahkan ke E42 terpilih. Kenaikan E11→E14 Task 2 tidak didukung bukti selisih akurasi signifikan pada prediksi yang tersedia; tidak signifikan juga bukan pembuktian equivalence. E12 dinilai per task dan metrik, bukan sekadar diberi label gagal dari minimum akurasi.

Source extractorbaseline sudah memakai headline_verified + supporting_text_verified, dan source training sudah memakai class weighting. Permintaan menambahkan supporting/weighting dijawab dengan bukti aktual dan kontrol yang benar, bukan mengulang asumsi bahwa keduanya tidak pernah ada.
