"""Recover raw OOF for historical frozen CLIP-B32/IndoBERT controls.

Matches the historical baseline head recipe (120 epochs, full batch, seed42,
class weights from training). New results are never substituted for old JSON.
This family is explicitly NOT a pure ablation of the trainable-tail E42 model.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import time

import numpy as np
import pandas as pd
import torch
from torch import nn

from evaluate import TASKS,sha,write_json


class Head(nn.Module):
    def __init__(self,dim,classes):
        super().__init__()
        self.bersama=nn.Sequential(nn.Linear(dim,256),nn.ReLU(),nn.Dropout(.4))
        self.kepala=nn.ModuleDict({t:nn.Linear(256,n) for t,n in classes.items()})
    def forward(self,x):
        z=self.bersama(x)
        return {t:layer(z) for t,layer in self.kepala.items()}


def fit(x,y,classes,train,weighted=True,tasks=TASKS):
    torch.manual_seed(42);np.random.seed(42)
    model=Head(x.shape[1],classes)
    optimizer=torch.optim.AdamW(model.parameters(),lr=1e-3,weight_decay=1e-4)
    loss={}
    for t in tasks:
        counts=np.bincount(y[t][train],minlength=classes[t]).astype(np.float32)
        weights=len(train)/(np.maximum(counts,1)*(counts>0).sum()) if weighted else np.ones(classes[t])
        weights[counts==0]=0
        loss[t]=nn.CrossEntropyLoss(weight=torch.tensor(weights,dtype=torch.float32))
    xt=torch.tensor(x[train]);yt={t:torch.tensor(y[t][train]) for t in tasks}
    for _ in range(120):
        model.train();optimizer.zero_grad();p=model(xt)
        value=sum(loss[t](p[t],yt[t]) for t in tasks)/len(tasks)
        value.backward();optimizer.step()
    return model.eval()


def main(workspace):
    started=time.monotonic();torch.set_num_threads(2)
    app=Path(workspace).resolve()/'DEMO_XAI_745_FULL';root=app/'04_hasil_eksperimen/revisi_ii'
    data=app/'03_data/DATASET_740_TASK2_DOMAIN.csv';features=app/'03_data/fitur_clip_indobert_740.npz'
    df=pd.read_csv(data).fillna('');z=np.load(features)
    origin=pd.read_csv(app/'04_hasil_eksperimen/e42_tail_grid/oof.csv')
    assert df.sample_id.tolist()==origin.sample_id.tolist()
    xs={'image':z['img'].astype('float32'),'text':z['txt'].astype('float32')}
    xs['both']=np.hstack([xs['image'],xs['text']])
    labels={t:sorted(df[t].unique()) for t in TASKS};nc={t:len(labels[t]) for t in TASKS}
    y={t:df[t].map({c:i for i,c in enumerate(labels[t])}).to_numpy() for t in TASKS}
    arms={'RII_FROZEN_MTL_WEIGHTED':('both',True,False),
          'RII_FROZEN_MTL_UNWEIGHTED':('both',False,False),
          'RII_FROZEN_IMAGE_ONLY':('image',True,False),
          'RII_FROZEN_TEXT_SUPPORTING':('text',True,False),
          'RII_FROZEN_SINGLE_TASK':('both',True,True)}
    protocol={'schema':'revisi-ii-frozen-control-v1','seed':42,'epochs':120,'batch':'full training fold',
              'optimizer':'AdamW lr0.001 wd0.0001','head':'1280/input ->256 ReLU dropout0.4 ->3 heads',
              'class_weights':'inverse training counts only','selection':'fixed recipe; no selection on outer test',
              'purpose':'recover baseline ablations; not E42 trainable-tail ablations',
              'arms':arms,'dataset_sha256':sha(data),'features_sha256':sha(features),'source_sha256':sha(__file__)}
    protocol_path=root/'frozen_controls_protocol.json'
    if protocol_path.exists():assert json.loads(protocol_path.read_text())==protocol
    else:write_json(protocol_path,protocol)
    for name,(feature,weighted,single) in arms.items():
        out=root/'experiments'/name
        if (out/'result.json').exists():
            result=json.loads((out/'result.json').read_text());assert result['protocol_sha256']==sha(protocol_path)
            print('preserved completed',name,flush=True);continue
        out.mkdir(parents=True,exist_ok=True);pred={t:np.full(len(df),-1) for t in TASKS};details=[]
        begin=time.monotonic()
        for fold in range(1,6):
            tr=np.where(origin.fold.to_numpy()!=fold)[0];te=np.where(origin.fold.to_numpy()==fold)[0]
            assert not set(tr)&set(te)
            if single:
                for t in TASKS:
                    model=fit(xs[feature],y,nc,tr,weighted,tasks=(t,))
                    with torch.inference_mode():pred[t][te]=model(torch.tensor(xs[feature][te]))[t].argmax(1).numpy()
            else:
                model=fit(xs[feature],y,nc,tr,weighted)
                with torch.inference_mode():
                    p=model(torch.tensor(xs[feature][te]))
                    for t in TASKS:pred[t][te]=p[t].argmax(1).numpy()
            details.append(dict(fold=fold,train_ids=df.iloc[tr].sample_id.tolist(),test_ids=df.iloc[te].sample_id.tolist()))
            print(name,'fold',fold,'seconds',round(time.monotonic()-begin,2),flush=True)
        result=df[['sample_id']].copy();result['fold']=origin.fold
        for t in TASKS:
            assert (pred[t]>=0).all()
            result[t+'_truth']=df[t];result[t+'_pred']=[labels[t][i] for i in pred[t]]
        result.to_csv(out/'predictions.csv',index=False)
        parity={t:int((result[t+'_pred']!=origin[t+'_baseline']).sum()) for t in TASKS} if name=='RII_FROZEN_MTL_WEIGHTED' else None
        write_json(out/'result.json',dict(status='complete',schema='revisi-ii-frozen-oof-v1',protocol_sha256=sha(protocol_path),
                   source_sha256=sha(__file__),arm=name,samples=740,labels=labels,folds=details,seconds=time.monotonic()-begin,
                   oof_sha256=sha(out/'predictions.csv'),historical_baseline_prediction_differences=parity,
                   model_family='historical frozen CLIP-B32/IndoBERT; not E42',fixed_epochs=120))
    print('ALL FROZEN CONTROLS COMPLETE',round(time.monotonic()-started,2),flush=True)


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--workspace',required=True,type=Path);args=ap.parse_args();main(args.workspace)
