# Audit Baseline E42

**Tanggal:** 2026-10-17  
**Dataset:** `DEMO_XAI_745_FULL/03_data/DATASET_740_TASK2_DOMAIN.csv`  
**SHA-256 dataset:** `cba20f8250bcb59481ed2d3d7d5d42fb8242c96a7ba2d11a2cd02ad80862961a`

## Reproduksi metrik

| task | macro_f1 | accuracy | classes |
| --- | --- | --- | --- |
| task1_issue | 0.525483 | 0.554054 | 10 |
| task2_domain_sumber | 0.395560 | 0.435135 | 7 |
| task3_primary_entity_type | 0.403398 | 0.518919 | 8 |

Semua angka dihitung ulang dari `e42_tail_grid/oof.csv` dan cocok dengan `result.json` sampai toleransi 1e-12. Minimum Macro-F1 E42 adalah **0.395560**, sehingga gate tiga task ≥0,70 **belum tercapai**.

## Integritas

- OOF: 740 baris, 740 ID unik, setiap ID muncul tepat sekali.
- Fold: 5 fold, masing-masing 148, 148, 148, 148, 148 sampel.
- Hash OOF: `bc4c55291463106d398cf90c9f796724f7f22595d92668bda324a51e9799b642`.
- Detail per kelas: `per_class_metrics.csv`.
- Distribusi label: `data_distribution.csv`.
- Leakage/parity: `leakage_report.md`.
