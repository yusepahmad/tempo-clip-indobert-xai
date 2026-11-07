# XAI model utama E42

Delapan ID dipilih acak dengan seed sebelum penjelasan. Setiap sampel dijelaskan dengan checkpoint outer fold yang tidak melatih sampel tersebut. Fitur CLIP, teks, dan prediksi direplay terhadap cache/OOF. Source, checkpoint dan hasil parity ada pada heldout_replay.csv.

Visual: attention rollout Abnar–Zuidema, mean heads, residualidentity dan matrix product lintas layer. Peta bersifat class-agnostic, bukan Grad-CAM dan bukan bukti keputusan kelas secara otomatis. Dua viewCLIP full/crop dipetakan kembali melalui area center-crop preprocessing sebelum digabung. Tidak mengganti backbone ke ResNet untuk memudahkan penjelasan.

Teks: LIME untuk skor kelas prediksi head yang sama dengan visual aktual ditahan tetap, 256 perturbasi lokal, seed tetap. Koefisien adalah atribusi kondisional terhadap citra dan surrogate lokal; local R² disertakan, sehingga contoh dengan kecocokan rendah tetap terlihat.

Faithfulness eksploratif: hapus20% sel grid8 × 8 bernilai rollout tertinggi, bandingkan penurunan skor kelas asal dengan rata-rata3 mask acak berukuran sama. Skor dapat naik setelah deletion; nilai negatif tidak dibuang. Hanya8 sampel, bukan evaluasi seluruh korpus atau model refit deployment.

| task | rollout_top20_drop | random20_mean_drop | drop_difference |
| --- | --- | --- | --- |
| task1_issue | 0.0229 | 0.0709 | -0.0480 |
| task2_domain_sumber | -0.0646 | 0.0861 | -0.1507 |
| task3_primary_entity_type | 0.0974 | 0.0250 | 0.0724 |

Hasil campuran tidak mendukung klaim universal bahwa rollout menjelaskan kelas dengan faithful. Peta tersedia sebagai attention-flow diagnostic; faithfulness yang belum kuat adalah hasil negatif yang harus dilaporkan.

Kecocokan surrogate LIME:

| index | task | min | mean | max |
| --- | --- | --- | --- | --- |
| 0 | task1_issue | 0.5805 | 0.6781 | 0.7656 |
| 1 | task2_domain_sumber | 0.5100 | 0.6755 | 0.8851 |
| 2 | task3_primary_entity_type | 0.3632 | 0.7078 | 0.9199 |

Penilaian manusia: paket berkode dan kontrol acak sudah disiapkan. Belum ada skor lima penilai dan belum ada agreement manusia. Instrumen menilai kejelasan/relevansi/keterpahaman, sedangkan faithfulness model diuji terpisah. Jangan menyebut persepsi manusia sebagai pengujian kausal perilaku model.

Metode rujukan: [Abnar & Zuidema2020](https://aclanthology.org/2020.acl-main.385/), [LIME](https://aclanthology.org/N16-3020/). [Chefer dkk.ICCV2021](https://openaccess.thecvf.com/content/ICCV2021/html/Chefer_Generic_Attention-Model_Explainability_for_Interpreting_Bi-Modal_and_Encoder-Decoder_Transformers_ICCV_2021_paper.html) merupakan alternatif khusus transformer, bukan nama metode yang diklaim sudah diimplementasikan dalam paket ini.
