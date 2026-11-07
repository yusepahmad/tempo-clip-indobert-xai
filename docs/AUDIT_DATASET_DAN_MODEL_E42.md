# Audit Dataset dan Model E42

**Tanggal:** 17 Oktober 2026

## Ringkasan

- Sampel/ID unik: 740/740.
- Grup hash gambar duplikat: 0.
- Grup duplikat deklaratif: 0.
- Konflik label pada hash gambar identik: 0 grup.
- Konflik label pada grup duplikat deklaratif: 0 grup.
- Confidence anotator: `{'high': 565, 'low': 4, 'medium': 171}`.

## Audit per task

### task1_issue

- Macro-F1 E42: **0.5255**; baseline: 0.4380.
- Rasio kelas terbesar:terkecil: **11.43:1**.
- Sampel diperbaiki terhadap baseline: 156; regresi: 83.
- Tiga kelas F1 terendah: `other_issue` 0.333, `security_defense_and_terrorism` 0.438, `human_rights_and_social_conflict` 0.473.
- Lima confusion terbesar: `election_and_political_competition`→`power_and_governance` (26); `power_and_governance`→`election_and_political_competition` (22); `corruption_and_bribery`→`economy_business_and_state_enterprise` (14); `corruption_and_bribery`→`power_and_governance` (13); `economy_business_and_state_enterprise`→`power_and_governance` (13).

### task2_domain_sumber

- Macro-F1 E42: **0.3956**; baseline: 0.3197.
- Rasio kelas terbesar:terkecil: **3.40:1**.
- Sampel diperbaiki terhadap baseline: 152; regresi: 67.
- Tiga kelas F1 terendah: `LAINNYA` 0.224, `KONSUMSI_TRANSAKSI` 0.239, `HEWAN_TUBUH` 0.317.
- Lima confusion terbesar: `KONSUMSI_TRANSAKSI`→`MESIN_INFRASTRUKTUR` (26); `BENCANA_JERAT`→`MESIN_INFRASTRUKTUR` (23); `PERMAINAN_KONTES`→`MESIN_INFRASTRUKTUR` (21); `MESIN_INFRASTRUKTUR`→`BENCANA_JERAT` (18); `MESIN_INFRASTRUKTUR`→`PERMAINAN_KONTES` (18).

### task3_primary_entity_type

- Macro-F1 E42: **0.4034**; baseline: 0.2764.
- Rasio kelas terbesar:terkecil: **16.58:1**.
- Sampel diperbaiki terhadap baseline: 179; regresi: 58.
- Tiga kelas F1 terendah: `political_party` 0.196, `legislature` 0.267, `multiple_or_other` 0.312.
- Lima confusion terbesar: `multiple_or_other`→`individual` (33); `individual`→`multiple_or_other` (32); `individual`→`government` (23); `government`→`multiple_or_other` (21); `government`→`individual` (19).

## Kesimpulan teknis

- E42 memperbaiki lebih banyak sampel daripada yang diregresikan terhadap baseline, tetapi performa kelas ekor masih membatasi Macro-F1.
- Tidak ditemukan gambar identik atau grup duplikat deklaratif, sehingga audit
  ini tidak menemukan konflik label berbasis duplikasi.
- Empat anotasi ber-confidence `low` dan 171 ber-confidence `medium` perlu
  diprioritaskan dalam validasi label pengguna.
- Eksperimen berikutnya harus membandingkan single-task dengan joint pada split yang sama untuk mengukur negative transfer secara langsung.
- Tidak ada label yang diubah oleh audit ini.

## Diagnosis single-task E48

E48 memakai outer fold E42 yang sama dan memilih feature family, normalisasi,
serta C hanya melalui inner validation masing-masing task. Hasil OOF:

| Task | E42 joint | E48 single-task | Selisih E48−E42 |
|---|---:|---:|---:|
| Task 1 | 0,5255 | 0,4861 | -0,0393 |
| Task 2 | 0,3956 | 0,4185 | +0,0229 |
| Task 3 | 0,4034 | 0,3883 | -0,0151 |

Task 2 memperoleh sinyal lebih baik ketika dipisahkan, sedangkan Task 1 dan
Task 3 masih mendapat manfaat dari joint learning. Ini mendukung eksperimen
task-specific routing/gating untuk Task 2, bukan pemisahan total seluruh task.
E48 hanya diagnosis dan tidak memenuhi kontrak satu model joint final.

## Artefak

- `DEMO_XAI_745_FULL/04_hasil_eksperimen/audit_targets_20261017/audit.json`
- `DEMO_XAI_745_FULL/04_hasil_eksperimen/e48_single_task_diagnostic/result.json`
- `docs/OCR_LABEL_VALIDATION_20.csv`
