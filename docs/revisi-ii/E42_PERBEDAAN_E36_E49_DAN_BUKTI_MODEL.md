# Perbedaan E36–E49 terhadap E42 dan Bukti Model

Dokumen ini adalah penjelasan pendamping daftar revisi R. Acuan tetapnya ialah **E42 (`e42_tail_grid`)**, bukan asumsi bahwa seluruh eksperimen E36–E49 ditumpuk menjadi satu model.

## Acuan E42

E42 memakai CLIP ViT-L/14 frozen pada full-view dan crop 20%–94% (2 × 768), IndoBERT-base-p1 dengan embedding dan 10 blok pertama frozen serta 2 blok terakhir trainable (mean pool 768), lalu fusi 2.304 → Linear 256 → ReLU → Dropout 0,3 → tiga head (10/7/8 kelas). Grid-nya adalah LR tail `{2e-6, 2e-5, 1e-4}` × bobot task `{1:1:1, 1:2:2}`, LR head `3e-4`, weight decay `0,01`, batch 32, dan kandidat epoch `{0,2,4,8,12,24}`.

Checkpoint outerfold terpilih adalah: F1 config 5/epoch 12; F2 config 5/epoch 12; F3 config 5/epoch 2; F4 config 3/epoch 8; F5 config 4/epoch 8. Detail LR, bobot loss, dan hash checkpoint ada di `R18_ARCHITECTURE_AUDIT.json`.

## Apa yang berubah pada setiap E

| E | Fokus/perubahan yang diuji | Epoch/LR/loss utama | Perbedaan langsung dari E42 |
|---|---|---|---|
| E36 | CLIP-L/14 full, crop, atau keduanya; IndoBERT CLS frozen | 120 epoch; LR 1e-3; dropout 0,2/0,4; bobot visual dan Task 2 diuji | Encoder teks seluruhnya frozen; hanya head dilatih; tidak ada tail 2 blok atau seleksi epoch per fold. |
| E37 | Pooling token IndoBERT mean/last-4 dibanding CLS, dengan CLIP-B/32 | 120 epoch; LR 1e-3; dropout 0,2/0,4 | Backbone visual B/32 dan teks frozen; E42 memakai L/14 dua-view dan tail trainable. |
| E38 | Kombinasi CLIP-L/14 dua-view dengan pooling IndoBERT mean/last-4 | 120 epoch; LR 1e-3 | Masih eksperimen fitur frozen; E42 melatih dua blok IndoBERT terakhir dan memakai grid LR tail. |
| E39 | Normalisasi fitur center/standard | 120 epoch; LR 1e-3 | Menguji normalisasi pada fitur frozen; bukan arsitektur tail E42. |
| E40 | MMoE: shared experts dan task gates | 120 epoch; LR 1e-3 | Routing MMoE menggantikan shared MLP tunggal; encoder tetap frozen, berbeda dari tail trainable E42. |
| E41 | Pendahulu E42: CLIP-L/14 dua-view + tail IndoBERT 2 blok | LR tail 2e-5; LR head 3e-4; loss 1:2:2; epoch `{0,2,4,8,12}` | E42 memperluas menjadi 6 kombinasi LR/loss dan menambah kandidat epoch 24. |
| **E42** | **Model utama: grid tail IndoBERT 2 blok + shared MTL** | **LR tail 3 nilai; loss 2 skema; epoch `{0,2,4,8,12,24}`** | **Acuan pembanding. Epoch final berbeda per fold: 12/12/2/8/8.** |
| E43 | 32 region CLIP dan text-conditioned spatial attention | 120 epoch; LR 1e-3; hidden 128/256 | Mengganti dua vektor global E42 dengan attention regional; tidak memakai tail E42. |
| E44 | Focal loss pada keluarga tail | gamma 0/1/2; class-power 0,5/1; LR tail 1e-4; epoch E42 | Arsitektur dekat E42, tetapi CE berbobot diganti/diuji dengan focal loss. |
| E45 | Feature mixup setelah fusi | alpha 0/0,2/0,4; WD 1e-4/0,01; LR tail 1e-4; epoch E42 | Menambah mixup pada fused representation; E42 tidak memakai mixup. |
| E46 | Label smoothing pada head fitur frozen | smoothing 0/0,1/0,2; WD 1e-4/0,01; 120 epoch; LR 1e-3 | E42 tidak memakai label smoothing dan memiliki tail trainable. |
| E47 | Refinement relasi antartask | hidden 64/128; scale 0,25/0,5/1; 120 epoch; LR 1e-3 | Menambah hubungan prediksi antartask pada fitur frozen; E42 memakai tiga head paralel. |
| E48 | Diagnostik single-task nested CV dengan LinearSVC | 24 kombinasi fitur `{visual,text,both}` × normalisasi `{L2,standard}` × C; tanpa epoch neural | Bukan model joint/neural; dipakai mengukur negative transfer pada outerfold E42. Tidak boleh disebut ablation neural E42. |
| E49 | Task-routed MMoE dengan 4 expert dan tower per task | 60 epoch; LR 1e-3; loss 1:1,5:1,5; smoothing 0,05 | Fitur encoder frozen dan routing per task; berbeda dari shared MLP + tail IndoBERT E42. |

## Cara membaca rangkaian eksperimen

E36–E40 menguji backbone, pooling, normalisasi, dan MMoE berbasis fitur frozen. E41 adalah pendahulu langsung; E42 memperluas pencarian LR/loss/epoch dan menjadi model utama. E43–E47 adalah alternatif regional, loss, augmentasi, dan relasi task. E48 adalah diagnostik single-task non-neural, sedangkan E49 adalah alternatif routed MTL. Karena itu, focal loss E44, mixup E45, label smoothing E46, relasi E47, dan routing E49 **tidak boleh diklaim sebagai bagian E42**.

## Bukti per komponen

| Komponen | Bukti screenshot | Bukti machine-readable/source |
|---|---|---|
| CLIP | [`e42_model_evidence/01_clip_e42.png`](e42_model_evidence/01_clip_e42.png) | `tail_model.py`, `tools/explain_e42.py`, dan protocol E42 |
| IndoBERT | [`e42_model_evidence/02_indobert_e42.png`](e42_model_evidence/02_indobert_e42.png) | `tail_model.py` (`BertLayer` × 2), audit checkpoint per fold |
| XAI aktual | [`e42_model_evidence/03_xai_e42.png`](e42_model_evidence/03_xai_e42.png) | `xai_e42/verification.json`, `heldout_replay.csv`, `conditional_lime.csv`, `deletion_faithfulness.csv` |

Screenshot CLIP/IndoBERT adalah render bukti source dan konfigurasi aktual, bukan tangkapan UI training. Screenshot XAI memakai gambar rollout E42 aktual. Metode visual adalah attention rollout class-agnostic, **bukan Grad-CAM**; teks memakai LIME 256 perturbasi dengan fitur visual aktual ditahan tetap. Human rating belum dievaluasi.

## Lokasi sumber audit

- E42 source: `delivery/HASIL_REVISI_JOY_20261108_R4_ANALISIS/joy_revisi_ii/source/DEMO_XAI_745_FULL/01_notebook/e42_tail_grid/tail_model.py`
- E48 source: `.../01_notebook/e48_single_task_diagnostic.py`
- E49 source: `.../01_notebook/e49_task_routed_mtl/model.py`
- XAI source dan hasil: `delivery/HASIL_REVISI_JOY_20261108_R4_ANALISIS/joy_revisi_ii/{tools/explain_e42.py,xai_e42/,documentation/XAI_METHOD.md}`

