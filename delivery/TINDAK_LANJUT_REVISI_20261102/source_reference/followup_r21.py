"""R21 2x2 input comparison, explicit pending cells and bootstrap kappa CIs."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
from evaluate import TASKS,sha

ARMS=[('CLIP-IndoBERT','basic','RII_TAIL_MTL_WEIGHTED',128),
      ('CLIP-IndoBERT','rich','RII_TAIL_RICH256',256),
      ('Qwen3-VL QLoRA','basic','RII_QWEN_QLORA_BASIC',2048),
      ('Qwen3-VL QLoRA','rich','MICRO_E14_joint_qlora_oof',2048),
      ('Qwen3-VL zero-shot','basic','RII_QWEN_ZERO_BASIC',2048),
      ('Qwen3-VL zero-shot','rich','RII_QWEN_ZERO_RICH',2048)]


def kappa_ci(truth,prediction,labels,resamples=2000,seed=20261102):
    mapping={label:i for i,label in enumerate(labels)};k=len(labels);n=len(truth)
    pair=np.array([mapping[a]*k+mapping[b] for a,b in zip(truth,prediction)],dtype=int)
    def score(codes):
        matrix=np.bincount(codes,minlength=k*k).reshape(k,k);size=matrix.sum()
        observed=np.trace(matrix)/size;expected=(matrix.sum(0)*matrix.sum(1)).sum()/size**2
        return (observed-expected)/(1-expected) if expected<1 else np.nan
    rng=np.random.default_rng(seed);values=np.array([score(pair[rng.integers(n,size=n)]) for _ in range(resamples)])
    finite=values[np.isfinite(values)];assert len(finite)>=int(.99*resamples),'Too many unidentifiable bootstrap samples'
    low,high=np.quantile(finite,[.025,.975])
    return dict(kappa=float(score(pair)),kappa_ci_low=float(low),kappa_ci_high=float(high),kappa_bootstrap_valid=len(finite))


def build(package,destination):
    package=Path(package);destination=Path(destination);destination.mkdir(parents=True,exist_ok=True)
    metrics=pd.read_csv(package/'analysis/metrics.csv');data=pd.read_csv(package/'inputs/DATASET_740_TASK2_DOMAIN.csv')
    rows=[]
    for architecture,variant,name,tokens in ARMS:
        selected=metrics[metrics.experiment.eq(name)]
        path=package/f'inputs/predictions/{name}.csv'
        for task in TASKS:
            row=dict(architecture=architecture,input_variant=variant,experiment=name,task=task,max_text_tokens=tokens,
                     status='Not Evaluated',samples=0,macro_f1=None,macro_ci_low=None,macro_ci_high=None,
                     kappa=None,kappa_ci_low=None,kappa_ci_high=None,kappa_bootstrap_valid=0,predictions_sha256='')
            if not selected.empty:
                source=selected[selected.task.eq(task)].iloc[0];pred=pd.read_csv(path)
                row.update(status='Available',samples=int(source.samples),macro_f1=float(source.macro_f1),
                           macro_ci_low=float(source.macro_ci_low),macro_ci_high=float(source.macro_ci_high),
                           **kappa_ci(pred[task+'_truth'],pred[task+'_pred'],sorted(data[task].unique())),predictions_sha256=sha(path))
                assert abs(row['kappa']-float(source.kappa))<1e-12
            rows.append(row)
    pd.DataFrame(rows).to_csv(destination/'R21_MATRIX_DAN_ZERO_SHOT.csv',index=False)
    text='# R21 — tabel arsitektur × kekayaan input\n\n'
    text+='Seluruh angka berasal dari prediksi tersimpan. Sel QLoRA basic tetap kosong sampai lima fold/740 prediksi lulus verifikasi. Empat sampel smoke tidak dipakai sebagai hasil utama. CI kappa adalah percentile bootstrap 2.000 pengambilan pasangan sampel, seed 20261102, bersyarat pada prediksi tetap.\n\n'
    text+='| Task | CLIP basic | CLIP rich | QLoRA basic | QLoRA rich |\n|---|---|---|---|---|\n'
    for task in TASKS:
        cells=[]
        for architecture,variant,_,_ in ARMS[:4]:
            row=next(r for r in rows if r['task']==task and r['architecture']==architecture and r['input_variant']==variant)
            cells.append('Menunggu full 740' if row['status']!='Available' else f"Macro-F1 {row['macro_f1']:.4f} [{row['macro_ci_low']:.4f}, {row['macro_ci_high']:.4f}]; κ {row['kappa']:.4f} [{row['kappa_ci_low']:.4f}, {row['kappa_ci_high']:.4f}]")
        text+='| '+task+' | '+' | '.join(cells)+' |\n'
    text+='\n## Batas kesetaraan\n\n- Basic pada resep revisi ini mencakup citra, headline, dan supporting text; bukan eksperimen headline-only literal. Arm headline-only E42 tersedia terpisah di paket utama.\n- CLIP basic memakai 128 token dan rich 256 token karena pemotongan rich128; selisih mencampur kekayaan teks dan batas konteks. Tidak dinyatakan sebagai efek fitur murni.\n- QLoRA basic/rich memakai resep epoch yang dipilih pada inner rich historis; ini intervensi input bersyarat pada resep tersebut, bukan tuning basic independen.\n- Zero-shot tidak disebut OOF training; hasilnya berada dalam CSV yang sama dengan label arsitektur tersendiri.\n- Penutupan R21 menunggu hasil QLoRA basic serta penilaian pembimbing atas batas kesetaraan di atas.\n'
    (destination/'R21_TABEL_2X2.md').write_text(text)
    return dict(status='partial_actual_results',rows=len(rows),available_rows=sum(r['status']=='Available' for r in rows),pending_rows=sum(r['status']!='Available' for r in rows),bootstrap_resamples=2000)
