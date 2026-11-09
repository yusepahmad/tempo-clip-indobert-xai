"""R30: remove rotation, preserve transformation RNG, equalize train exposure.

SigLIP2 frozen feature family, explicitly separate from E42. Outer-test always
uses clean features. Augmented training uses one draw per training ID per epoch
(50% clean/50% fixed augmented image) rather than doubling optimizer updates.
"""
import argparse
import ast
import hashlib
import io
import json
from pathlib import Path
import random
import time

import numpy as np
import pandas as pd
from PIL import Image,ImageEnhance
import torch
from torch import nn
from torch.nn import functional as F
from sklearn.metrics import f1_score
from sklearn.model_selection import StratifiedKFold
from huggingface_hub import snapshot_download
from transformers import AutoModel,AutoImageProcessor
from evaluate import TASKS,sha,write_json


class Joint(nn.Module):
    def __init__(self,nc):
        super().__init__();self.shared=nn.Sequential(nn.Linear(1536,192),nn.LayerNorm(192),nn.GELU(),nn.Dropout(.25))
        self.heads=nn.ModuleDict({t:nn.Linear(192,nc[t]) for t in TASKS})
    def forward(self,x):
        h=self.shared(x);return {t:layer(h) for t,layer in self.heads.items()}


def main(workspace):
    repo=Path(workspace).resolve();app=repo/'DEMO_XAI_745_FULL';results=app/'04_hasil_eksperimen'
    base=results/'revisi_ii';out=base/'augmentation';out.mkdir(exist_ok=True)
    start=time.monotonic();torch.set_num_threads(2)
    df=pd.read_csv(app/'03_data/DATASET_740_TASK2_DOMAIN.csv').fillna('')
    folds=pd.read_csv(results/'e42_tail_grid/oof.csv');old=results/'next_research_20261017/02_augmentation'
    source=app/'01_notebook/next_research_20261017/kaggle_a01_a03/launch.py'
    tree=ast.parse(source.read_text());function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='aug')
    augmented_source=ast.get_source_segment(source.read_text(),function)
    assert augmented_source.count('r.uniform(-2,2)')==1
    no_rotation_source=augmented_source.replace('r.uniform(-2,2)','0.0*r.uniform(-2,2)')
    scope=dict(hashlib=hashlib,random=random,np=np,Image=Image,ImageEnhance=ImageEnhance,io=io)
    exec(compile(no_rotation_source,'moderate_no_rotation.py','exec'),scope);augment=scope['aug']
    (out/'moderate_no_rotation.py').write_text(no_rotation_source+'\n')
    protocol=dict(schema='revisi-ii-augmentation-no-rotation-v1',seed=20261101,source_sha256=sha(__file__),
        legacy_augmentation_source_sha256=sha(source),transform_source_sha256=sha(out/'moderate_no_rotation.py'),
        model='google/siglip2-base-patch16-384',revision='f775b65a79762255128c981547af89addcfe0f88',
        weight_sha256='ed72c0ace85020ae610fc817c2538b9cae5a477b012a50859c60af5b3ad30857',
        arms=['RII_A00_CLEAN','RII_A01_LIGHT','RII_A02_MODERATE_NO_ROTATION','RII_A03_LIGHT_SAMPLER'],
        augmentation='A01 original light; A02 original photometric/jpeg/noise with original rotation RNG draw consumed but rotation zero; no geometric crop',
        head='shared192 LayerNorm GELU dropout0.25 +3heads',epochs=35,batch_size=32,
        optimizer='AdamW lr8e-4 wd2e-4',loss='mean task CE, inverse-sqrt training class weights, smoothing0.05',
        exposure='exactly n training draws/epoch each arm, 50% fixed clean/aug per ID except clean; sampler replacement n draws',
        validation_test='clean features only',selection='two inner Task2-stratified folds seed123, mean task Macro-F1; ties declared arm order',
        note='new controlled SigLIP2 family, not historical duplication-based augmentation or E42-tail ablation')
    pp=out/'protocol.json'
    if pp.exists():assert json.loads(pp.read_text())==protocol
    else:write_json(pp,protocol)
    feature_path=out/'moderate_no_rotation_features.npz'
    if not feature_path.exists():
        snap=Path(snapshot_download(protocol['model'],revision=protocol['revision'],allow_patterns=['config.json','preprocessor_config.json','model.safetensors']))
        assert sha(snap/'model.safetensors')==protocol['weight_sha256']
        processor=AutoImageProcessor.from_pretrained(snap,local_files_only=True,use_fast=False)
        model=AutoModel.from_pretrained(snap,local_files_only=True,use_safetensors=True,dtype=torch.float32).eval()
        for p in model.parameters():p.requires_grad=False
        values=[];qa=[]
        for off in range(0,740,4):
            ims=[]
            for row in df.iloc[off:off+4].itertuples():
                path=app/'05_gambar'/Path(row.image_path).name;assert sha(path)==row.image_sha256
                with Image.open(path) as image:
                    altered=augment(image,row.sample_id,'moderate')
                    if off<4:
                        assert altered.size==image.size;altered.save(out/f'QA_no_rotation_{row.sample_id}.jpg',quality=95)
                    ims.append(altered)
            with torch.inference_mode():
                z=model.get_image_features(**processor(images=ims,return_tensors='pt'),return_dict=True).pooler_output
            values.append(F.normalize(z.float(),p=2,dim=1).numpy())
            if off%96==0:print('NO ROTATION FEATURES',off+len(ims),round(time.monotonic()-start,1),flush=True)
        np.savez_compressed(feature_path,sample_ids=df.sample_id.to_numpy(str),image=np.vstack(values))
        write_json(out/'feature_manifest.json',dict(status='complete',samples=740,features_sha256=sha(feature_path),
                    weight_sha256=protocol['weight_sha256'],protocol_sha256=sha(pp),labels_used_for_extraction=False,seconds=time.monotonic()-start))
        del model;gc_collect()
    cache=np.load(results/'e41_cached_tail/cache/front_cache.npz');text=cache['base_mean']
    clean=np.load(old/'clean_features.npz');light=np.load(old/'light_features.npz');moderate=np.load(feature_path)
    assert clean['sample_ids'].tolist()==light['sample_ids'].tolist()==moderate['sample_ids'].tolist()==df.sample_id.tolist()
    views={'RII_A00_CLEAN':clean['image'],'RII_A01_LIGHT':light['image'],
           'RII_A02_MODERATE_NO_ROTATION':moderate['image'],'RII_A03_LIGHT_SAMPLER':light['image']}
    labels={t:sorted(df[t].unique()) for t in TASKS};nc={t:len(labels[t]) for t in TASKS}
    y={t:df[t].map({v:i for i,v in enumerate(labels[t])}).to_numpy() for t in TASKS}
    clean_x=np.hstack([clean['image'],text]).astype('float32')
    variants={name:np.hstack([image,text]).astype('float32') for name,image in views.items()}

    def fit(tr,name,seed):
        torch.manual_seed(seed);np.random.seed(seed);rng=np.random.default_rng(seed)
        m=Joint(nc);optimizer=torch.optim.AdamW(m.parameters(),lr=8e-4,weight_decay=2e-4)
        losses={}
        for t in TASKS:
            counts=np.bincount(y[t][tr],minlength=nc[t]).astype('float32')
            weights=np.sqrt(len(tr)/(nc[t]*np.maximum(counts,1)));weights/=weights.mean()
            losses[t]=nn.CrossEntropyLoss(weight=torch.tensor(weights,dtype=torch.float32),label_smoothing=.05)
        tuples=list(zip(*(y[t][tr] for t in TASKS)));counts={v:tuples.count(v) for v in set(tuples)}
        probs=np.array([counts[v]**-.5 for v in tuples]);probs/=probs.sum()
        for epoch in range(35):
            ix=rng.choice(tr,size=len(tr),replace=True,p=probs) if name=='RII_A03_LIGHT_SAMPLER' else rng.permutation(tr)
            mask=rng.random(len(ix))<.5 if name!='RII_A00_CLEAN' else np.zeros(len(ix),dtype=bool)
            m.train()
            for off in range(0,len(ix),32):
                ids=ix[off:off+32];use=mask[off:off+32]
                x=clean_x[ids].copy();x[use]=variants[name][ids[use]]
                optimizer.zero_grad();p=m(torch.tensor(x));loss=sum(losses[t](p[t],torch.tensor(y[t][ids])) for t in TASKS)/3
                assert torch.isfinite(loss);loss.backward();optimizer.step()
        return m.eval()

    @torch.inference_mode()
    def predict(m,ix):return {t:p.argmax(1).numpy() for t,p in m(torch.tensor(clean_x[ix])).items()}
    def score(ix,p):return float(np.mean([f1_score(y[t][ix],p[t],labels=range(nc[t]),average='macro',zero_division=0) for t in TASKS]))
    predictions={name:{t:np.full(740,-1) for t in TASKS} for name in views}
    selected={t:np.full(740,-1) for t in TASKS};details=[]
    for fold in range(1,6):
        tr=np.where(folds.fold.to_numpy()!=fold)[0];te=np.where(folds.fold.to_numpy()==fold)[0]
        splits=[(tr[a],tr[b]) for a,b in StratifiedKFold(2,shuffle=True,random_state=123).split(tr,y[TASKS[1]][tr])]
        scores=[]
        for name in views:
            values=[]
            for j,(a,b) in enumerate(splits):values.append(score(b,predict(fit(a,name,20261101+fold*100+j),b)))
            scores.append(float(np.mean(values)))
        winner=list(views)[max(range(len(scores)),key=lambda k:(scores[k],-k))]
        for name in views:
            p=predict(fit(tr,name,20271101+fold),te)
            for t in TASKS:
                predictions[name][t][te]=p[t]
                if name==winner:selected[t][te]=p[t]
        details.append(dict(fold=fold,train_indices=tr.tolist(),test_indices=te.tolist(),inner_mean_macro=dict(zip(views,scores)),selected_variant=winner))
        print('AUGMENTATION FOLD',fold,winner,'seconds',round(time.monotonic()-start,1),flush=True)
    for name,preds in {**predictions,'RII_AUG_SELECTED_INNER':selected}.items():
        folder=base/'experiments'/name;folder.mkdir(parents=True,exist_ok=True)
        if (folder/'result.json').exists():raise RuntimeError('Do not overwrite completed augmentation results')
        frame=df[['sample_id']].copy();frame['fold']=folds.fold
        for t in TASKS:
            assert (preds[t]>=0).all();frame[t+'_truth']=df[t];frame[t+'_pred']=[labels[t][i] for i in preds[t]]
        frame.to_csv(folder/'predictions.csv',index=False)
        write_json(folder/'result.json',dict(status='complete',samples=740,arm=name,folds=details,predictions_sha256=sha(folder/'predictions.csv'),
                   protocol_sha256=sha(pp),source_sha256=sha(__file__),wall_seconds_including_extraction=time.monotonic()-start))
    write_json(out/'completion.json',dict(status='complete',samples=740,arms=list(predictions)+['RII_AUG_SELECTED_INNER'],protocol_sha256=sha(pp),seconds=time.monotonic()-start))


def gc_collect():
    import gc
    gc.collect()


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--workspace',type=Path,required=True);main(ap.parse_args().workspace)
