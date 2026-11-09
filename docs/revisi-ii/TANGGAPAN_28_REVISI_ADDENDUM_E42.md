# Addendum Daftar R — Perbedaan Eksperimen dan Bukti E42

Addendum ini menambahkan penjelasan yang diminta klien tanpa mengubah paket R4 bertanda hash.

| R | Tambahan jawaban | Bukti |
|---|---|---|
| R18 — Arsitektur MTL dan Joint Loss | Identitas E42 dibedakan secara eksplisit dari E36–E49, termasuk perubahan epoch, LR, loss, backbone, pooling, dan routing. | [Tabel perbedaan E36–E49](E42_PERBEDAAN_E36_E49_DAN_BUKTI_MODEL.md), [CLIP](e42_model_evidence/01_clip_e42.png), [IndoBERT](e42_model_evidence/02_indobert_e42.png) |
| R27 — MTL vs single-task | E48 dinyatakan sebagai diagnostik single-task `LinearSVC`, bukan model joint atau ablation neural E42. | [Baris E48 dan interpretasi](E42_PERBEDAAN_E36_E49_DAN_BUKTI_MODEL.md) |
| R29 — Backbone/arsitektur | E36–E40 dan E43 dijelaskan sebagai pengujian backbone, pooling, normalisasi, MMoE, dan spatial attention yang berbeda dari E42. | [Tabel E36–E43](E42_PERBEDAAN_E36_E49_DAN_BUKTI_MODEL.md) |
| R30 — Training/augmentasi | E41–E47 memuat perubahan kandidat epoch, LR, bobot loss, focal loss, mixup, label smoothing, dan relasi task. Fitur eksperimen tersebut tidak otomatis menjadi bagian E42. | [Tabel E41–E47](E42_PERBEDAAN_E36_E49_DAN_BUKTI_MODEL.md) |
| R34 — Explainability | Bukti visual per komponen disertakan. XAI aktual adalah attention rollout class-agnostic + LIME kondisional; bukan Grad-CAM, dan human rating belum dievaluasi. | [XAI aktual](e42_model_evidence/03_xai_e42.png) |

