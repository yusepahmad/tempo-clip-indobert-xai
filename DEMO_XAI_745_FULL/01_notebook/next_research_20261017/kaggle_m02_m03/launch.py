"""Kaggle M02/M03: pinned image encoders plus fair joint nested-CV heads."""
import csv, hashlib, json, random, time
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image
import torch
from torch import nn
import torch.nn.functional as F
from sklearn.metrics import f1_score
from sklearn.model_selection import StratifiedKFold
from transformers import AutoImageProcessor, AutoModel
from huggingface_hub import HfApi, snapshot_download

INPUT = Path('/kaggle/input')
DATA = next(p for p in INPUT.rglob('DATASET_740_TASK2_DOMAIN.csv') if p.parent.name == '03_data')
ROOT = DATA.parents[1]
WORK = Path('/kaggle/working/m02_m03')
E42 = next(INPUT.rglob('baseline_oof.csv'))
TEXT_CACHE = next(INPUT.rglob('front_cache.npz'))
TASKS = ('task1_issue','task2_domain_sumber','task3_primary_entity_type')
DATA_SHA = 'cba20f8250bcb59481ed2d3d7d5d42fb8242c96a7ba2d11a2cd02ad80862961a'
MODELS = {
 'M02_siglip2_indobert': dict(repo='google/siglip2-base-patch16-384', revision='f775b65a79762255128c981547af89addcfe0f88', weight='ed72c0ace85020ae610fc817c2538b9cae5a477b012a50859c60af5b3ad30857', size=384, pooling='siglip'),
 'M03_dinov2_indobert': dict(repo='facebook/dinov2-base', revision='f9e44c814b77203eaa57a6bdbbd535f21ede1415', weight='d73036b56966966d07975d696bde331762f37297e2f095de8cea0040c3aa0841', size=224, pooling='cls'),
}
CONFIGS = [
 dict(hidden=128,dropout=.20,lr=1e-3,wd=1e-4,power=0.,smooth=0.,epochs=35),
 dict(hidden=192,dropout=.25,lr=8e-4,wd=2e-4,power=.5,smooth=.05,epochs=35),
 dict(hidden=256,dropout=.30,lr=6e-4,wd=3e-4,power=.5,smooth=.05,epochs=35),
]

def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for block in iter(lambda:f.read(8*1024*1024),b''): h.update(block)
 return h.hexdigest()

def read(path):
 with path.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

def seed_all(seed): random.seed(seed);np.random.seed(seed);torch.manual_seed(seed);torch.cuda.manual_seed_all(seed)

def extract(name, spec, df):
 out=WORK/name;out.mkdir(parents=True,exist_ok=True)
 info=HfApi().model_info(spec['repo'],revision=spec['revision'],files_metadata=True);assert info.sha==spec['revision']
 weight=next(x for x in info.siblings if x.rfilename=='model.safetensors');assert weight.lfs.sha256==spec['weight']
 snap=Path(snapshot_download(spec['repo'],revision=spec['revision'],allow_patterns=['config.json','preprocessor_config.json','model.safetensors']))
 assert sha(snap/'model.safetensors')==spec['weight']
 proc=AutoImageProcessor.from_pretrained(snap,local_files_only=True,trust_remote_code=False,use_fast=False)
 model=AutoModel.from_pretrained(snap,local_files_only=True,trust_remote_code=False,use_safetensors=True,torch_dtype=torch.float32).cuda().eval()
 for p in model.parameters():p.requires_grad_(False)
 vectors=[];audit=[];started=time.time()
 for start in range(0,len(df),16):
  imgs=[]
  for row in df.iloc[start:start+16].itertuples():
   path=ROOT/'05_gambar'/Path(row.image_path).name;assert sha(path)==row.image_sha256
   with Image.open(path) as im:imgs.append(im.convert('RGB'))
   audit.append({'sample_id':row.sample_id,'image_sha256':row.image_sha256})
  px=proc(images=imgs,return_tensors='pt')['pixel_values'].cuda()
  with torch.inference_mode():
   if spec['pooling']=='siglip': z=model.get_image_features(pixel_values=px,return_dict=True).pooler_output
   else:z=model(pixel_values=px,return_dict=True).last_hidden_state[:,0]
   vectors.append(F.normalize(z.float(),dim=1).cpu().numpy())
  if start%160==0:print(name,'features',min(start+16,len(df)),flush=True)
 values=np.vstack(vectors);assert values.shape==(740,768) and np.isfinite(values).all()
 np.savez_compressed(out/'features.npz',sample_ids=df.sample_id.to_numpy(str),image=values)
 (out/'features_manifest.json').write_text(json.dumps({'model':spec,'samples':740,'dimension':768,'dataset_sha256':sha(DATA),'features_sha256':sha(out/'features.npz'),'labels_used':False,'seconds':time.time()-started,'audit':audit},indent=2)+'\n')
 del model;torch.cuda.empty_cache();return values

class Joint(nn.Module):
 def __init__(self,classes,cfg):
  super().__init__();self.shared=nn.Sequential(nn.Linear(1536,cfg['hidden']),nn.LayerNorm(cfg['hidden']),nn.GELU(),nn.Dropout(cfg['dropout']));self.heads=nn.ModuleDict({t:nn.Linear(cfg['hidden'],classes[t]) for t in TASKS})
 def forward(self,v,t):
  z=self.shared(torch.cat([F.normalize(v.float(),dim=1),F.normalize(t.float(),dim=1)],dim=1));return {k:self.heads[k](z) for k in TASKS}

def class_weights(y,n,power):
 if power==0:return torch.ones(n,device='cuda')
 c=np.bincount(y,minlength=n).astype('float32');w=(len(y)/(n*c))**power;return torch.tensor(w/w.mean(),device='cuda')

def fit(v,t,ys,classes,cfg,seed):
 seed_all(seed);m=Joint(classes,cfg).cuda();opt=torch.optim.AdamW(m.parameters(),lr=cfg['lr'],weight_decay=cfg['wd'])
 losses={k:nn.CrossEntropyLoss(weight=class_weights(ys[k],classes[k],cfg['power']),label_smoothing=cfg['smooth']) for k in TASKS}
 vt=torch.tensor(v,device='cuda');tt=torch.tensor(t,device='cuda');yt={k:torch.tensor(ys[k],device='cuda') for k in TASKS};m.train()
 for _ in range(cfg['epochs']):
  for idx in torch.randperm(len(v),device='cuda').split(32):
   opt.zero_grad();logits=m(vt[idx],tt[idx]);loss=sum(losses[k](logits[k],yt[k][idx]) for k in TASKS)/3;loss.backward();opt.step()
 return m.eval()

@torch.inference_mode()
def predict(m,v,t):
 out=m(torch.tensor(v,device='cuda'),torch.tensor(t,device='cuda'));return {k:out[k].argmax(1).cpu().numpy() for k in TASKS}

def score(y,p,classes):
 d={k:float(f1_score(y[k],p[k],labels=range(classes[k]),average='macro',zero_division=0)) for k in TASKS};return {**d,'min':min(d.values()),'mean':float(np.mean(list(d.values())))}

def evaluate(name,visual,text,rows,fold_rows):
 out=WORK/name;labels={k:sorted({r[k] for r in rows}) for k in TASKS};classes={k:len(labels[k]) for k in TASKS};y={}
 for k in TASKS:
  enc={x:i for i,x in enumerate(labels[k])};y[k]=np.array([enc[r[k]] for r in rows])
 folds=np.array([int(r['fold']) for r in fold_rows]);oof={k:np.full(740,-1) for k in TASKS};details=[];started=time.time()
 for fold in range(1,6):
  tr,te=np.where(folds!=fold)[0],np.where(folds==fold)[0];splits=list(StratifiedKFold(3,shuffle=True,random_state=10100+fold).split(tr,y['task2_domain_sumber'][tr]));choices=[]
  for ci,cfg in enumerate(CONFIGS):
   vals=[]
   for si,(a,b) in enumerate(splits):
    a,b=tr[a],tr[b];m=fit(visual[a],text[a],{k:y[k][a] for k in TASKS},classes,cfg,100000+fold*100+ci*10+si);vals.append(score({k:y[k][b] for k in TASKS},predict(m,visual[b],text[b]),classes));del m
   choices.append({'config':ci,'min':float(np.mean([x['min'] for x in vals])),'mean':float(np.mean([x['mean'] for x in vals]))})
  chosen=max(choices,key=lambda x:(x['min'],x['mean']));m=fit(visual[tr],text[tr],{k:y[k][tr] for k in TASKS},classes,CONFIGS[chosen['config']],200000+fold);pred=predict(m,visual[te],text[te]);del m
  for k in TASKS:oof[k][te]=pred[k]
  details.append({'fold':fold,'selected':chosen,'outer':score({k:y[k][te] for k in TASKS},pred,classes)});print(name,'fold',fold,details[-1]['outer'],flush=True)
 overall=score(y,oof,classes);fields=['sample_id','fold']+[z for k in TASKS for z in (k+'_truth',k+'_pred')]
 with (out/'oof.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
  for i,row in enumerate(rows):
   d={'sample_id':row['sample_id'],'fold':int(folds[i])}
   for k in TASKS:d[k+'_truth']=labels[k][y[k][i]];d[k+'_pred']=labels[k][int(oof[k][i])]
   w.writerow(d)
 result={'schema':'tempo-alt-encoder-joint-v1','status':'complete','model_id':name,'joint_model':True,'overall_scores':overall,'fold_details':details,'configs':CONFIGS,'seconds':time.time()-started,'oof_sha256':sha(out/'oof.csv')};(out/'result.json').write_text(json.dumps(result,indent=2)+'\n');return result

def main():
 assert torch.cuda.is_available();WORK.mkdir(exist_ok=True);assert sha(DATA)==DATA_SHA
 df=pd.read_csv(DATA).fillna('');rows=read(DATA);fold_rows=read(E42);assert [r['sample_id'] for r in rows]==[r['sample_id'] for r in fold_rows]
 cache=np.load(TEXT_CACHE);text=cache['base_mean'];assert text.shape==(740,768)
 summary=[]
 for name,spec in MODELS.items():
  visual=extract(name,spec,df);summary.append(evaluate(name,visual,text,rows,fold_rows))
 (WORK/'summary.json').write_text(json.dumps({'status':'complete','dataset_sha256':sha(DATA),'results':[{'model_id':x['model_id'],'overall_scores':x['overall_scores']} for x in summary]},indent=2)+'\n')
 print('ALL COMPLETE',flush=True)

if __name__=='__main__':main()
