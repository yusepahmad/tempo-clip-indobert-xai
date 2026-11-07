"""Pure frozen-backbone comparison with identical768 image/text dimensions.

CLIP full-view only vs SigLIP2 vs DINOv2, same fixed baseline-style head and
IndoBERT mean text. This is a new controlled family, not the E42 tail grid.
"""
import argparse
import json
from pathlib import Path
import time
import numpy as np
import pandas as pd
import torch
from evaluate import TASKS,sha,write_json
from train_frozen_controls import fit


def main(workspace):
    app=Path(workspace).resolve()/'DEMO_XAI_745_FULL';res=app/'04_hasil_eksperimen';out=res/'revisi_ii'
    data=pd.read_csv(app/'03_data/DATASET_740_TASK2_DOMAIN.csv').fillna('');outer=pd.read_csv(res/'e42_tail_grid/oof.csv')
    textfile=res/'e41_cached_tail/cache/front_cache.npz';cache=np.load(textfile);text=cache['base_mean']
    sources={'RII_BACKBONE_CLIP_FULL':(res/'e36_clip_l14/features.npz','full'),
             'RII_BACKBONE_SIGLIP2':(res/'next_research_20261017/01_model_comparison/M02_siglip2_indobert/features.npz','image'),
             'RII_BACKBONE_DINOV2':(res/'next_research_20261017/01_model_comparison/M03_dinov2_indobert/features.npz','image')}
    labels={t:sorted(data[t].unique()) for t in TASKS};nc={t:len(labels[t]) for t in TASKS}
    ys={t:data[t].map({c:i for i,c in enumerate(labels[t])}).to_numpy() for t in TASKS}
    protocol=dict(schema='revisi-ii-frozen-backbone-parity-v1',arms=list(sources),input_dimension=1536,
                  image_dimension=768,text='same frozen IndoBERT mean768 for every arm',
                  recipe='fixed shared256 ReLU dropout0.4, weighted CE equal tasks, AdamW1e-3/wd1e-4, 120 full-batch epochs, seed42',
                  tuning='none; no outer-test parameter selection',source_sha256=sha(__file__),fit_source_sha256=sha(Path(__file__).with_name('train_frozen_controls.py')),
                  text_cache_sha256=sha(textfile),visual_features={n:sha(p) for n,(p,k) in sources.items()},
                  limitation='encoder-native resolutions/pretraining differ by definition; CLIP full only, not E42 full+crop/trainable text tail')
    pp=out/'backbone_controls_protocol.json'
    if pp.exists():assert json.loads(pp.read_text())==protocol
    else:write_json(pp,protocol)
    torch.set_num_threads(2)
    for name,(path,key) in sources.items():
        target=out/'experiments'/name;target.mkdir(parents=True,exist_ok=True)
        if (target/'result.json').exists():continue
        start=time.monotonic();z=np.load(path);assert z['sample_ids'].tolist()==data.sample_id.tolist()==cache['sample_ids'].tolist()
        x=np.hstack([z[key],text]).astype('float32');assert x.shape==(740,1536)
        predictions={t:np.full(740,-1) for t in TASKS};details=[]
        for fold in range(1,6):
            tr=np.where(outer.fold.to_numpy()!=fold)[0];te=np.where(outer.fold.to_numpy()==fold)[0]
            m=fit(x,ys,nc,tr)
            with torch.inference_mode():p=m(torch.tensor(x[te]))
            for t in TASKS:predictions[t][te]=p[t].argmax(1).numpy()
            details.append(dict(fold=fold,train_indices=tr.tolist(),test_indices=te.tolist()))
            print(name,fold,round(time.monotonic()-start,1),flush=True)
        frame=data[['sample_id']].copy();frame['fold']=outer.fold
        for t in TASKS:frame[t+'_truth']=data[t];frame[t+'_pred']=[labels[t][i] for i in predictions[t]]
        frame.to_csv(target/'predictions.csv',index=False)
        write_json(target/'result.json',dict(status='complete',arm=name,samples=740,protocol_sha256=sha(pp),
                   predictions_sha256=sha(target/'predictions.csv'),folds=details,seconds=time.monotonic()-start))


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--workspace',required=True,type=Path);main(ap.parse_args().workspace)
