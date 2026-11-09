# R21 — tabel arsitektur × kekayaan input

Seluruh angka berasal dari prediksi tersimpan. Sel QLoRA basic tetap kosong sampai lima fold/740 prediksi lulus verifikasi. Empat sampel smoke tidak dipakai sebagai hasil utama. CI kappa adalah percentile bootstrap 2.000 pengambilan pasangan sampel, seed 20261102, bersyarat pada prediksi tetap.

| Task | CLIP basic | CLIP rich | QLoRA basic | QLoRA rich |
|---|---|---|---|---|
| task1_issue | Macro-F1 0.5073 [0.4612, 0.5472]; κ 0.4603 [0.4204, 0.5039] | Macro-F1 0.4619 [0.4175, 0.5013]; κ 0.4201 [0.3798, 0.4623] | Menunggu full 740 | Macro-F1 0.6733 [0.6259, 0.7163]; κ 0.6746 [0.6363, 0.7110] |
| task2_domain_sumber | Macro-F1 0.4104 [0.3739, 0.4465]; κ 0.3209 [0.2791, 0.3619] | Macro-F1 0.4967 [0.4584, 0.5320]; κ 0.4293 [0.3880, 0.4705] | Menunggu full 740 | Macro-F1 0.5103 [0.4733, 0.5478]; κ 0.4711 [0.4308, 0.5123] |
| task3_primary_entity_type | Macro-F1 0.3661 [0.3268, 0.4054]; κ 0.3367 [0.2926, 0.3823] | Macro-F1 0.4001 [0.3559, 0.4459]; κ 0.3671 [0.3239, 0.4097] | Menunggu full 740 | Macro-F1 0.5955 [0.5457, 0.6417]; κ 0.5515 [0.5075, 0.5942] |

## Batas kesetaraan

- Basic pada resep revisi ini mencakup citra, headline, dan supporting text; bukan eksperimen headline-only literal. Arm headline-only E42 tersedia terpisah di paket utama.
- CLIP basic memakai 128 token dan rich 256 token karena pemotongan rich128; selisih mencampur kekayaan teks dan batas konteks. Tidak dinyatakan sebagai efek fitur murni.
- QLoRA basic/rich memakai resep epoch yang dipilih pada inner rich historis; ini intervensi input bersyarat pada resep tersebut, bukan tuning basic independen.
- Zero-shot tidak disebut OOF training; hasilnya berada dalam CSV yang sama dengan label arsitektur tersendiri.
- Penutupan R21 menunggu hasil QLoRA basic serta penilaian pembimbing atas batas kesetaraan di atas.
