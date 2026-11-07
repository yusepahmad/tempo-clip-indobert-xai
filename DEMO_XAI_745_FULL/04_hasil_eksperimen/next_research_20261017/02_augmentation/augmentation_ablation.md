# Ablation Augmentasi

| Varian | Task 1 | Task 2 | Task 3 | Minimum | Mean |
| --- | ---: | ---: | ---: | ---: | ---: |
| A00_none | 0.4833 | 0.4307 | 0.3595 | 0.3595 | 0.4245 |
| A01_light | 0.4696 | 0.4276 | 0.3663 | 0.3663 | 0.4212 |
| A02_moderate | 0.4808 | 0.4272 | 0.3307 | 0.3307 | 0.4129 |
| A03_light_sampler | 0.4692 | 0.4284 | 0.3556 | 0.3556 | 0.4177 |
| selected_pipeline | 0.4785 | 0.4219 | 0.3564 | 0.3564 | 0.4189 |

Varian dipilih per outer fold hanya dari inner-validation. Outer test selalu memakai gambar bersih. Fitur augmented tidak pernah dipakai pada validation/test.

Pipeline terpilih menghasilkan minimum Macro-F1 **0.3564**. Target 0,70 belum tercapai.
