#!/usr/bin/env python3
"""Micro-E03: nested task-order selection for a multiclass classifier chain."""
import csv,hashlib,itertools,json,time
from pathlib import Path
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score
from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import OneHotEncoder

ROOT=Path(__file__).resolve().parents[3];P=ROOT/'DEMO_XAI_745_FULL';DATA=P/'03_data/DATASET_740_TASK2_DOMAIN.csv';CLIP=P/'04_hasil_eksperimen/e41_cached_tail/cache/front_cache.npz';SIG=P/'04_hasil_eksperimen/next_research_20261017/01_model_comparison/M02_siglip2_indobert/features.npz';FOLDS=P/'04_hasil_eksperimen/e42_tail_grid/oof.csv';OUT=P/'04_hasil_eksperimen/next_research_20261017/06_micro_f1/MICRO_E03_classifier_chain';TASKS=('task1_issue','task2_domain_sumber','task3_primary_entity_type');ORDERS=list(itertools.permutations(TASKS))
def read(p):
 with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def onehot(values,n):
 out=np.zeros((len(values),n),dtype='float32');out[np.arange(len(values)),values.astype(int)]=1;return out
def fit_predict(xtr,ytr,xte,classes,order,seed):
 train=xtr;test=xte;pred={}
 for i,t in enumerate(order):
  m=LogisticRegression(C=.3,solver='liblinear',max_iter=800,random_state=seed+i);m.fit(train,ytr[t]);p=m.predict(test);pred[t]=p
  train=np.hstack([train,onehot(ytr[t],classes[t])]);test=np.hstack([test,onehot(p,classes[t])])
 return pred
def score(y,p):return {t:float(f1_score(y[t],p[t],average='micro')) for t in TASKS}
def main():
 start=time.time();OUT.mkdir(parents=True,exist_ok=True);rows,fr=read(DATA),read(FOLDS);c=np.load(CLIP);s=np.load(SIG);ids=[r['sample_id'] for r in rows];assert ids==c['sample_ids'].tolist()==s['sample_ids'].tolist()==[r['sample_id'] for r in fr]
 parts=[c['visual'],s['image'],c['base_mean']];parts=[z/(np.linalg.norm(z,axis=1,keepdims=True)+1e-8) for z in parts];x=np.hstack(parts).astype('float32');folds=np.array([int(r['fold']) for r in fr]);labels={t:sorted({r[t] for r in rows}) for t in TASKS};classes={t:len(labels[t]) for t in TASKS};y={t:np.array([{z:i for i,z in enumerate(labels[t])}[r[t]] for r in rows]) for t in TASKS};joint=np.array(['|'.join(r[t] for t in TASKS) for r in rows]);oof={t:np.full(740,-1) for t in TASKS};details=[]
 for fold in range(1,6):
  tr,te=np.where(folds!=fold)[0],np.where(folds==fold)[0];strat=y['task2_domain_sumber'][tr];splits=list(StratifiedKFold(3,shuffle=True,random_state=81000+fold).split(tr,strat));opts=[]
  for oi,order in enumerate(ORDERS):
   vals=[]
   for si,(a,b) in enumerate(splits):
    a,b=tr[a],tr[b];p=fit_predict(x[a],{t:y[t][a] for t in TASKS},x[b],classes,order,82000+fold*100+oi*10+si);q=score({t:y[t][b] for t in TASKS},p);vals.append(q)
   avg={t:float(np.mean([q[t] for q in vals])) for t in TASKS};opts.append({'order':list(order),'micro_f1':avg,'minimum':min(avg.values()),'mean':float(np.mean(list(avg.values())))})
  chosen=max(opts,key=lambda z:(z['minimum'],z['mean']));p=fit_predict(x[tr],{t:y[t][tr] for t in TASKS},x[te],classes,chosen['order'],83000+fold)
  for t in TASKS:oof[t][te]=p[t]
  outer=score({t:y[t][te] for t in TASKS},p);details.append({'fold':fold,'selected':chosen,'outer_micro_f1':outer});print(details[-1],flush=True)
 fields=['sample_id','fold']+[z for t in TASKS for z in (t+'_truth',t+'_pred')]
 with (OUT/'predictions.csv').open('w',newline='') as h:
  w=csv.DictWriter(h,fieldnames=fields);w.writeheader()
  for i,sid in enumerate(ids):
   d={'sample_id':sid,'fold':int(folds[i])}
   for t in TASKS:d[t+'_truth']=labels[t][y[t][i]];d[t+'_pred']=labels[t][int(oof[t][i])]
   w.writerow(d)
 micro=score(y,oof);macro={t:float(f1_score(y[t],oof[t],average='macro')) for t in TASKS};result={'schema':'tempo-micro-e03-v1','status':'complete','model_contract':'one multiclass classifier chain; task order selected on inner folds','micro_f1':micro,'macro_f1_diagnostic':macro,'minimum_micro_f1':min(micro.values()),'all_tasks_at_least_0_70':min(micro.values())>=.7,'fold_details':details,'dataset_sha256':sha(DATA),'feature_sha256':{'clip':sha(CLIP),'siglip':sha(SIG)},'seconds':time.time()-start,'predictions_sha256':sha(OUT/'predictions.csv')};(OUT/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
