"""Explicit R18 identity and Joint Loss, audited against preserved artifacts."""
import json
from pathlib import Path
from evaluate import sha, write_json

HERE=Path(__file__).resolve().parent;APP=HERE.parents[1];REPO=APP.parent


def create():
    source=APP/'01_notebook/e42_tail_grid'
    results=APP/'04_hasil_eksperimen/e42_tail_grid'
    protocol=json.loads((results/'protocol.json').read_text())
    assert protocol['model_sha256']==sha(source/'tail_model.py')
    assert protocol['worker_sha256']==sha(source/'worker.py')
    folds=[]
    for fold in range(1,6):
        meta=json.loads((results/f'fold{fold}.json').read_text())
        config=protocol['configs'][meta['selected_config']]
        assert sha(results/f'fold{fold}.pt')==meta['checkpoint_sha256']
        folds.append(dict(fold=fold,selected_config=meta['selected_config'],encoder_lr=config['encoder_lr'],
            head_lr=config['head_lr'],loss_weights=config['loss_weights'],epoch=meta['selected_epoch'],
            checkpoint_sha256=meta['checkpoint_sha256']))
    table='| Fold | Config | LR tail | LR head | Bobot task 1:2:3 | Epoch |\n|---|---|---|---|---|---|\n'
    for f in folds:
        table+=f"| {f['fold']} | {f['selected_config']} | {f['encoder_lr']:g} | {f['head_lr']:g} | {':'.join(str(int(a)) for a in f['loss_weights'])} | {f['epoch']} |\n"
    material=r'''## R18 — Arsitektur Multi-Task Learning CLIP–IndoBERT dengan Joint Loss

**Model utama penelitian adalah E42 (`e42_tail_grid`, alias `M00_e42_baseline`): arsitektur Multi-Task Learning CLIP–IndoBERT dengan Joint Loss.** Satu representasi bersama dipakai untuk memprediksi tiga task. Qwen3-VL merupakan pembanding; nama kandidat lain tidak otomatis berarti model utama yang sama.

| Komponen | Implementasi E42 yang dipakai |
|---|---|
| Cabang visual | CLIP **ViT-L/14**, frozen; full-view dan crop area vertikal 20%–94% |
| Cabang teks | IndoBERT-base-p1; embedding dan 10 blok pertama frozen, **2 blok terakhir trainable** |
| Input teks dasar | `headline_verified` + `supporting_text_verified`, maksimum 128 token pada E42 historis |
| Fusi | Dua vektor visual 768 dimensi dan teks mean-pooled 768 dimensi; total **2.304** dimensi |
| Shared layer | Linear(2304, 256) → ReLU → Dropout(0,3) |
| Head 1 | Isu utama, **10 kelas** |
| Head 2 | Domain sumber metafora, **7 kelas** |
| Head 3 | Tipe entitas sasaran, **8 kelas** |
| Optimisasi | AdamW; gradien loss gabungan mengubah shared layer, tiga head dan dua blok tail teks |

```text
Sampul → CLIP-L/14 frozen → full768 + crop768 ───────────┐
Judul + supporting → IndoBERT front frozen → tail2 → teks768
                                                       ↓
                     concat([2×visual_full, 2×visual_crop, teks])
                                                       ↓
                         shared Linear256 / ReLU / Dropout0.3
                                   ↙          ↓          ↘
                             isu10       domain7       entitas8
                                   ↘          ↓          ↙
                                      Joint Loss
```

Setiap view visual dan representasi teks dinormalisasi L2 sebelum fusi. Istilah MTL merujuk pada shared representation dan optimisasi bersama; tiga model terpisah yang hanya digabungkan pada tabel bukan implementasi E42 ini.

### Joint Loss aktual

Untuk batch training, masing-masing task memakai weighted cross entropy bawaan PyTorch (`nn.CrossEntropyLoss(weight=class_weights(...))`). Jika $n_{t,c}>0$, bobot kelas dihitung **hanya dari subset training**:

$$
w_{t,c}=\frac{N_{train}}{K_{t,present}\,n_{t,c}}.
$$

Kelas yang tidak muncul pada subset training diberi bobot nol. Weighted CE memakai weighted-mean reduction PyTorch; loss gabungannya:

$$
\mathcal L_{joint}=\frac{\alpha_1\mathcal L_{issue}+\alpha_2\mathcal L_{domain}+\alpha_3\mathcal L_{entity}}{\alpha_1+\alpha_2+\alpha_3}.
$$

Bobot task $\alpha$ tetap selama satu training run. **Implementasi ini tidak menggunakan learned uncertainty weighting Kendall.** Source historis berisi:

```python
losses = {t: nn.CrossEntropyLoss(weight=class_weights(y[t][tr], nc[t]).to('cuda')) for t in TASKS}
l = sum(w * losses[t](p[t], torch.tensor(y[t][ix], device='cuda'))
        for t, w in zip(TASKS, CFG['loss_weights'])) / sum(CFG['loss_weights'])
```

### Konfigurasi checkpoint outerfold

Lima outerfold masing-masing menyumbang 148 prediksi held-out. Konfigurasi/epoch di bawah dipilih pada inner folds historis, lalu direfit pada training outerfold. Tabel ini berasal dari protocol/fold metadata dan hash checkpoint yang telah diperiksa; jangan menyatakan bobot 1:2:2 berlaku pada semua fold.

'''+table+r'''

Seleksi **historis di dalam E42** memakai minimum Macro-F1 antartask pada inner CV. Penetapan **E42 sebagai model utama pada audit revisi** memakai mean Macro-F1 kandidat CLIP–IndoBERT yang memenuhi arsitektur proposal, dan dinyatakan post-hoc. Dua tingkat keputusan tersebut tidak disamakan atau diubah seolah protokol lama sudah memakai aturan baru.

### Posisi terhadap kandidat dan demo

- `BASELINE_CLIP_INDoBERT`: baseline encoder beku CLIP-B32 + IndoBERT CLS; hasilnya berbeda dari E42.
- `M01_clip_indobert`: kontrol keluarga backbone; tidak otomatis identik dengan E42.
- `e36_clip_l14`: eksperimen fitur CLIP-L14 dengan head beku; tidak otomatis mencakup tail IndoBERT E42.
- `e42_tail_grid` / `M00_e42_baseline`: model utama yang identitasnya dibekukan pada revisi ini.
- E11/E12/Qwen: comparator dengan protokol dan fitur sendiri, bukan alias model utama.
- Demo web historis memakai CLIP-B32; **belum merupakan deployment E42**. Screenshot web lama hanya bukti demo historis.

Hasil E42 dari 740 prediksi OOF: Macro-F1 task1 **0,5255**, task2 **0,3956**, task3 **0,4034**. Ini hasil internal pada korpus yang digunakan berulang, bukan validasi eksternal. Penetapan model tidak berarti nilai agreement anotator atau lima penilai XAI sudah tersedia.

Source lengkap tersedia dalam paket pada `source/DEMO_XAI_745_FULL/01_notebook/e42_tail_grid/{tail_model.py,worker.py}`; tabel konfigurasi dan hash lengkap pada `documentation/R18_ARCHITECTURE_AUDIT.json`. Lima checkpoint tersedia pada lampiran model E42.
'''
    doc=REPO/'docs/revisi-ii'
    (doc/'R18_ARSITEKTUR_JOINT_LOSS.md').write_text(material)
    write_json(doc/'R18_ARCHITECTURE_AUDIT.json',dict(status='verified_against_original_protocol_source_checkpoint_hashes',
        model='e42_tail_grid',model_sha256=sha(source/'tail_model.py'),worker_sha256=sha(source/'worker.py'),
        protocol_sha256=sha(results/'protocol.json'),folds=folds,learned_uncertainty=False,
        historical_inner_selection='minimum task Macro-F1',revision_model_selection='post-hoc mean task Macro-F1 among eligible architectures'))
    print('R18 MATERIAL VERIFIED',len(folds),'folds')


if __name__=='__main__':create()
