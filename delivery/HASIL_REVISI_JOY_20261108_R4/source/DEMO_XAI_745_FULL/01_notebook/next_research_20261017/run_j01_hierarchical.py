#!/usr/bin/env python3
"""J01 joint MTL with training-only Task-2 metaphor auxiliary supervision."""
import csv,hashlib,json,random,time
from pathlib import Path
import numpy as np
import torch
from torch import nn
import torch.nn.functional as F
from sklearn.metrics import f1_score
from sklearn.model_selection import StratifiedKFold

ROOT=Path(__file__).resolve().parents[3];P=ROOT/'DEMO_XAI_745_FULL';DATA=P/'03_data/DATASET_740_TASK2_DOMAIN.csv';CACHE=P/'04_hasil_eksperimen/e41_cached_tail/cache/front_cache.npz';FOLDS=P/'04_hasil_eksperimen/e42_tail_grid/oof.csv';PROTOCOL=P/'04_hasil_eksperimen/next_research_20261017/frozen_protocol.json';OUT=P/'04_hasil_eksperimen/next_research_20261017/03_joint_optimization/J01_hierarchical_task2';TASKS=('task1_issue','task2_domain_sumber','task3_primary_entity_type')
CONFIGS=[dict(hidden=192,adapter=64,dropout=.2,lr=8e-4,aux=.2,power=.5,epochs=40),dict(hidden=192,adapter=96,dropout=.25,lr=8e-4,aux=.5,power=.5,epochs=40),dict(hidden=256,adapter=96,dropout=.3,lr=6e-4,aux=.3,power=.5,epochs=40)]
def read(p):
 with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def seed(s):random.seed(s);np.random.seed(s);torch.manual_seed(s)
def weights(y,n,p=.5):
 c=np.bincount(y,minlength=n).astype('float32');w=(len(y)/(n*c))**p;return torch.tensor(w/w.mean(),dtype=torch.float32)
class Model(nn.Module):
 def __init__(self,classes,c):
  super().__init__();self.shared=nn.Sequential(nn.Linear(2304,c['hidden']),nn.LayerNorm(c['hidden']),nn.GELU(),nn.Dropout(c['dropout']));self.adapters=nn.ModuleDict({t:nn.Sequential(nn.Linear(c['hidden'],c['adapter']),nn.GELU(),nn.Dropout(c['dropout'])) for t in TASKS});self.heads=nn.ModuleDict({t:nn.Linear(c['adapter'],classes[t]) for t in TASKS});self.meta=nn.Linear(c['adapter'],2)
 def forward(self,v,t):
  z=self.shared(torch.cat([F.normalize(v.float(),dim=1),F.normalize(t.float(),dim=1)],1));a={k:self.adapters[k](z) for k in TASKS};return {**{k:self.heads[k](a[k]) for k in TASKS},'metaphor_aux':self.meta(a['task2_domain_sumber'])}
def fit(v,t,y,meta,classes,c,s):
 seed(s);m=Model(classes,c);opt=torch.optim.AdamW(m.parameters(),lr=c['lr'],weight_decay=2e-4);loss={k:nn.CrossEntropyLoss(weight=weights(y[k].numpy(),classes[k]),label_smoothing=.05) for k in TASKS};aux=nn.CrossEntropyLoss();m.train()
 for _ in range(c['epochs']):
  for idx in torch.randperm(len(v)).split(32):
   opt.zero_grad();o=m(v[idx],t[idx]);main=sum(loss[k](o[k],y[k][idx]) for k in TASKS)/3;l=main+c['aux']*aux(o['metaphor_aux'],meta[idx]);l.backward();opt.step()
 return m.eval()
@torch.inference_mode()
def pred(m,v,t):
 o=m(v,t);return {k:o[k].argmax(1).numpy() for k in TASKS}
def score(y,p,classes):
 d={k:float(f1_score(y[k],p[k],labels=range(classes[k]),average='macro',zero_division=0)) for k in TASKS};return {**d,'min':min(d.values()),'mean':float(np.mean(list(d.values())))}
def main():
 start=time.time();OUT.mkdir(parents=True,exist_ok=True);rows,fr=read(DATA),read(FOLDS);cache=np.load(CACHE);ids=[r['sample_id'] for r in rows];assert ids==cache['sample_ids'].tolist()==[r['sample_id'] for r in fr];assert json.loads(PROTOCOL.read_text())['dataset']['sha256']==sha(DATA)
 labels={k:sorted({r[k] for r in rows}) for k in TASKS};classes={k:len(labels[k]) for k in TASKS};y={k:np.array([{x:i for i,x in enumerate(labels[k])}[r[k]] for r in rows]) for k in TASKS};meta=np.array([0 if r['task2_metaphor_presence'].lower() in ('no','none','false','0') else 1 for r in rows]);v=torch.tensor(cache['visual'],dtype=torch.float32);t=torch.tensor(cache['base_mean'],dtype=torch.float32);folds=np.array([int(r['fold']) for r in fr]);oof={k:np.full(740,-1) for k in TASKS};details=[]
 for fold in range(1,6):
  tr,te=np.where(folds!=fold)[0],np.where(folds==fold)[0];splits=list(StratifiedKFold(3,shuffle=True,random_state=30100+fold).split(tr,y['task2_domain_sumber'][tr]));opts=[]
  for ci,c in enumerate(CONFIGS):
   vals=[]
   for si,(a,b) in enumerate(splits):
    a,b=tr[a],tr[b];m=fit(v[a],t[a],{k:torch.tensor(y[k][a]) for k in TASKS},torch.tensor(meta[a]),classes,c,310000+fold*100+ci*10+si);vals.append(score({k:y[k][b] for k in TASKS},pred(m,v[b],t[b]),classes))
   opts.append({'config':ci,'min':float(np.mean([x['min'] for x in vals])),'mean':float(np.mean([x['mean'] for x in vals]))})
  chosen=max(opts,key=lambda x:(x['min'],x['mean']));m=fit(v[tr],t[tr],{k:torch.tensor(y[k][tr]) for k in TASKS},torch.tensor(meta[tr]),classes,CONFIGS[chosen['config']],320000+fold);p=pred(m,v[te],t[te]);
  for k in TASKS:oof[k][te]=p[k]
  details.append({'fold':fold,'selected':chosen,'config':CONFIGS[chosen['config']],'outer':score({k:y[k][te] for k in TASKS},p,classes)});print('fold',fold,details[-1]['outer'],flush=True)
 overall=score(y,oof,classes);fields=['sample_id','fold']+[z for k in TASKS for z in (k+'_truth',k+'_pred')]
 with (OUT/'oof.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
  for i,sid in enumerate(ids):
   d={'sample_id':sid,'fold':int(folds[i])}
   for k in TASKS:d[k+'_truth']=labels[k][y[k][i]];d[k+'_pred']=labels[k][int(oof[k][i])]
   w.writerow(d)
 result={'schema':'tempo-j01-hierarchical-v1','status':'complete','joint_model':True,'inference_outputs':list(TASKS),'training_only_auxiliary':'task2_metaphor_presence','label_metadata_used_at_inference':False,'dataset_sha256':sha(DATA),'cache_sha256':sha(CACHE),'protocol_sha256':sha(PROTOCOL),'overall_scores':overall,'fold_details':details,'seconds':time.time()-start,'oof_sha256':sha(OUT/'oof.csv')};(OUT/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(overall,indent=2))
if __name__=='__main__':main()
