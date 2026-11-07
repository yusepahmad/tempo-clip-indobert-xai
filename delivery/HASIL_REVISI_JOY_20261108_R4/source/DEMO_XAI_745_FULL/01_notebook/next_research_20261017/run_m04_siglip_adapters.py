#!/usr/bin/env python3
"""M04: SigLIP2 + IndoBERT with shared trunk and task-specific adapters."""
import csv,hashlib,json,random,time
from pathlib import Path
import numpy as np,torch
from torch import nn
import torch.nn.functional as F
from sklearn.metrics import f1_score
from sklearn.model_selection import StratifiedKFold

ROOT=Path(__file__).resolve().parents[3];P=ROOT/'DEMO_XAI_745_FULL';DATA=P/'03_data/DATASET_740_TASK2_DOMAIN.csv';TEXT=P/'04_hasil_eksperimen/e41_cached_tail/cache/front_cache.npz';VIS=P/'04_hasil_eksperimen/next_research_20261017/01_model_comparison/M02_siglip2_indobert/features.npz';FOLDS=P/'04_hasil_eksperimen/e42_tail_grid/oof.csv';PROTOCOL=P/'04_hasil_eksperimen/next_research_20261017/frozen_protocol.json';OUT=P/'04_hasil_eksperimen/next_research_20261017/01_model_comparison/M04_siglip2_adapters';TASKS=('task1_issue','task2_domain_sumber','task3_primary_entity_type')
CFG=[dict(shared=192,adapter=64,drop=.2,lr=8e-4,wd=2e-4,power=.5,smooth=.05,loss=(1,1,1),epochs=40),dict(shared=256,adapter=96,drop=.25,lr=6e-4,wd=3e-4,power=.5,smooth=.05,loss=(1,1.25,1.25),epochs=40),dict(shared=192,adapter=96,drop=.3,lr=6e-4,wd=2e-4,power=.4,smooth=.08,loss=(1,1.5,1.5),epochs=40)]
def read(p):
 with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def seed(s):random.seed(s);np.random.seed(s);torch.manual_seed(s)
def weights(y,n,p):
 c=np.bincount(y,minlength=n).astype('float32');w=(len(y)/(n*c))**p;return torch.tensor(w/w.mean(),dtype=torch.float32)
class Net(nn.Module):
 def __init__(self,classes,c):
  super().__init__();self.s=nn.Sequential(nn.Linear(1536,c['shared']),nn.LayerNorm(c['shared']),nn.GELU(),nn.Dropout(c['drop']));self.a=nn.ModuleDict({k:nn.Sequential(nn.Linear(c['shared'],c['adapter']),nn.LayerNorm(c['adapter']),nn.GELU(),nn.Dropout(c['drop'])) for k in TASKS});self.h=nn.ModuleDict({k:nn.Linear(c['adapter'],classes[k]) for k in TASKS})
 def forward(self,v,t):z=self.s(torch.cat([F.normalize(v.float(),dim=1),F.normalize(t.float(),dim=1)],1));return {k:self.h[k](self.a[k](z)) for k in TASKS}
def fit(v,t,y,classes,c,s):
 seed(s);m=Net(classes,c);opt=torch.optim.AdamW(m.parameters(),lr=c['lr'],weight_decay=c['wd']);loss={k:nn.CrossEntropyLoss(weight=weights(y[k].numpy(),classes[k],c['power']),label_smoothing=c['smooth']) for k in TASKS};m.train()
 for _ in range(c['epochs']):
  for idx in torch.randperm(len(v)).split(32):opt.zero_grad();o=m(v[idx],t[idx]);l=sum(w*loss[k](o[k],y[k][idx]) for k,w in zip(TASKS,c['loss']))/sum(c['loss']);l.backward();opt.step()
 return m.eval()
@torch.inference_mode()
def pred(m,v,t):o=m(v,t);return {k:o[k].argmax(1).numpy() for k in TASKS}
def score(y,p,classes):
 d={k:float(f1_score(y[k],p[k],labels=range(classes[k]),average='macro',zero_division=0)) for k in TASKS};return {**d,'min':min(d.values()),'mean':float(np.mean(list(d.values())))}
def main():
 start=time.time();OUT.mkdir(parents=True,exist_ok=True);rows,fr=read(DATA),read(FOLDS);vc=np.load(VIS);tc=np.load(TEXT);ids=[r['sample_id'] for r in rows];assert ids==vc['sample_ids'].tolist()==tc['sample_ids'].tolist()==[r['sample_id'] for r in fr];assert json.loads(PROTOCOL.read_text())['dataset']['sha256']==sha(DATA)
 labels={k:sorted({r[k] for r in rows}) for k in TASKS};classes={k:len(labels[k]) for k in TASKS};y={k:np.array([{x:i for i,x in enumerate(labels[k])}[r[k]] for r in rows]) for k in TASKS};v=torch.tensor(vc['image'],dtype=torch.float32);t=torch.tensor(tc['base_mean'],dtype=torch.float32);folds=np.array([int(r['fold']) for r in fr]);oof={k:np.full(740,-1) for k in TASKS};details=[]
 for fold in range(1,6):
  tr,te=np.where(folds!=fold)[0],np.where(folds==fold)[0];splits=list(StratifiedKFold(3,shuffle=True,random_state=50100+fold).split(tr,y['task2_domain_sumber'][tr]));opts=[]
  for ci,c in enumerate(CFG):
   vals=[]
   for si,(a,b) in enumerate(splits):
    a,b=tr[a],tr[b];m=fit(v[a],t[a],{k:torch.tensor(y[k][a]) for k in TASKS},classes,c,510000+fold*100+ci*10+si);vals.append(score({k:y[k][b] for k in TASKS},pred(m,v[b],t[b]),classes))
   opts.append({'config':ci,'min':float(np.mean([x['min'] for x in vals])),'mean':float(np.mean([x['mean'] for x in vals]))})
  chosen=max(opts,key=lambda x:(x['min'],x['mean']));m=fit(v[tr],t[tr],{k:torch.tensor(y[k][tr]) for k in TASKS},classes,CFG[chosen['config']],520000+fold);p=pred(m,v[te],t[te])
  for k in TASKS:oof[k][te]=p[k]
  details.append({'fold':fold,'selected':chosen,'config':CFG[chosen['config']],'outer':score({k:y[k][te] for k in TASKS},p,classes)});print('fold',fold,details[-1]['outer'],flush=True)
 overall=score(y,oof,classes);fields=['sample_id','fold']+[z for k in TASKS for z in (k+'_truth',k+'_pred')]
 with (OUT/'oof.csv').open('w',newline='') as h:
  w=csv.DictWriter(h,fieldnames=fields);w.writeheader()
  for i,sid in enumerate(ids):
   d={'sample_id':sid,'fold':int(folds[i])}
   for k in TASKS:d[k+'_truth']=labels[k][y[k][i]];d[k+'_pred']=labels[k][int(oof[k][i])]
   w.writerow(d)
 result={'schema':'tempo-m04-siglip-adapters-v1','status':'complete','joint_model':True,'overall_scores':overall,'fold_details':details,'dataset_sha256':sha(DATA),'visual_features_sha256':sha(VIS),'text_features_sha256':sha(TEXT),'protocol_sha256':sha(PROTOCOL),'seconds':time.time()-start,'oof_sha256':sha(OUT/'oof.csv')};(OUT/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(overall,indent=2))
if __name__=='__main__':main()
