"""Fixed historical-head input ablations from new label-blind text encodings."""
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
    app=Path(workspace).resolve()/'DEMO_XAI_745_FULL';root=app/'04_hasil_eksperimen/revisi_ii'
    mf=json.loads((root/'text_inputs/manifest.json').read_text());assert mf['status']=='complete'
    data=pd.read_csv(app/'03_data/DATASET_740_TASK2_DOMAIN.csv').fillna('')
    folds=pd.read_csv(app/'04_hasil_eksperimen/e42_tail_grid/oof.csv')
    old=np.load(app/'03_data/fitur_clip_indobert_740.npz')
    z={v:np.load(root/f'text_inputs/{v}_front_cache.npz') for v in ['headline','rich']}
    assert all(z[v]['sample_ids'].tolist()==data.sample_id.tolist() for v in z)
    features={'RII_FROZEN_TEXT_HEADLINE':z['headline']['cls'],
              'RII_FROZEN_MTL_HEADLINE':np.hstack([old['img'],z['headline']['cls']]),
              'RII_FROZEN_MTL_RICH':np.hstack([old['img'],z['rich']['cls']])}
    labels={t:sorted(data[t].unique()) for t in TASKS};nc={t:len(labels[t]) for t in TASKS}
    y={t:data[t].map({x:i for i,x in enumerate(labels[t])}).to_numpy() for t in TASKS}
    torch.set_num_threads(2)
    protocol={'schema':'revisi-ii-input-control-v1','source_sha256':sha(__file__),
              'fit_source_sha256':sha(Path(__file__).with_name('train_frozen_controls.py')),
              'text_manifest_sha256':sha(root/'text_inputs/manifest.json'),'arms':list(features),
              'recipe':'historical fixed weighted head120epoch; frozen CLIP-B32/IndoBERT CLS; not E42 tail ablation',
              'selection':'no outer-test selection','seed':42,'maximum_text_tokens':128}
    pp=root/'input_controls_protocol.json'
    if pp.exists():assert json.loads(pp.read_text())==protocol
    else:write_json(pp,protocol)
    for name,x in features.items():
        out=root/'experiments'/name;out.mkdir(parents=True,exist_ok=True)
        if (out/'result.json').exists():continue
        start=time.monotonic();p={t:np.full(len(data),-1) for t in TASKS};details=[]
        for fold in range(1,6):
            tr=np.where(folds.fold.to_numpy()!=fold)[0];te=np.where(folds.fold.to_numpy()==fold)[0]
            model=fit(x.astype('float32'),y,nc,tr)
            with torch.inference_mode():pred=model(torch.tensor(x[te],dtype=torch.float32))
            for t in TASKS:p[t][te]=pred[t].argmax(1).numpy()
            details.append(dict(fold=fold,train_ids=data.iloc[tr].sample_id.tolist(),test_ids=data.iloc[te].sample_id.tolist()))
            print(name,fold,round(time.monotonic()-start,2),flush=True)
        frame=data[['sample_id']].copy();frame['fold']=folds.fold
        for t in TASKS:frame[t+'_truth']=data[t];frame[t+'_pred']=[labels[t][i] for i in p[t]]
        frame.to_csv(out/'predictions.csv',index=False)
        write_json(out/'result.json',dict(status='complete',arm=name,samples=740,protocol_sha256=sha(pp),
                   source_sha256=sha(__file__),folds=details,predictions_sha256=sha(out/'predictions.csv'),seconds=time.monotonic()-start))


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--workspace',required=True,type=Path);main(ap.parse_args().workspace)
