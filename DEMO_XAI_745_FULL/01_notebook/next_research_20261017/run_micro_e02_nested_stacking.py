#!/usr/bin/env python3
"""Micro-E02: leakage-safe nested stacking with cross-task probability features."""
import csv,hashlib,json,time
from pathlib import Path
import numpy as np
from sklearn.ensemble import ExtraTreesClassifier
from sklearn.linear_model import LogisticRegression,SGDClassifier
from sklearn.metrics import f1_score
from sklearn.model_selection import StratifiedKFold

ROOT=Path(__file__).resolve().parents[3];P=ROOT/'DEMO_XAI_745_FULL';DATA=P/'03_data/DATASET_740_TASK2_DOMAIN.csv';CLIP=P/'04_hasil_eksperimen/e41_cached_tail/cache/front_cache.npz';SIG=P/'04_hasil_eksperimen/next_research_20261017/01_model_comparison/M02_siglip2_indobert/features.npz';FOLDS=P/'04_hasil_eksperimen/e42_tail_grid/oof.csv';OUT=P/'04_hasil_eksperimen/next_research_20261017/06_micro_f1/MICRO_E02_nested_stacking';TASKS=('task1_issue','task2_domain_sumber','task3_primary_entity_type');BASES=('lr','sgd','extra')
def read(p):
 with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def make(kind,seed):
 if kind=='lr':return LogisticRegression(C=.3,solver='liblinear',max_iter=800,random_state=seed)
 if kind=='sgd':return SGDClassifier(loss='log_loss',alpha=1e-4,max_iter=1500,tol=1e-4,average=True,random_state=seed)
 return ExtraTreesClassifier(n_estimators=150,max_features='sqrt',min_samples_leaf=1,n_jobs=-1,random_state=seed)
def aligned_proba(m,x,n):
 p=m.predict_proba(x);out=np.zeros((len(x),n),dtype='float32');out[:,m.classes_.astype(int)]=p;return out
def main():
 start=time.time();OUT.mkdir(parents=True,exist_ok=True);rows,fr=read(DATA),read(FOLDS);c=np.load(CLIP);s=np.load(SIG);ids=[r['sample_id'] for r in rows];assert ids==c['sample_ids'].tolist()==s['sample_ids'].tolist()==[r['sample_id'] for r in fr]
 parts=[c['visual'],s['image'],c['base_mean']];parts=[x/(np.linalg.norm(x,axis=1,keepdims=True)+1e-8) for x in parts];x=np.hstack(parts).astype('float32');folds=np.array([int(r['fold']) for r in fr]);labels={t:sorted({r[t] for r in rows}) for t in TASKS};classes={t:len(labels[t]) for t in TASKS};y={t:np.array([{z:i for i,z in enumerate(labels[t])}[r[t]] for r in rows]) for t in TASKS};oof={t:np.full(740,-1) for t in TASKS};details=[]
 for fold in range(1,6):
  tr,te=np.where(folds!=fold)[0],np.where(folds==fold)[0];meta_tr=[];meta_te=[]
  for ti,t in enumerate(TASKS):
   splits=list(StratifiedKFold(3,shuffle=True,random_state=71000+fold*10+ti).split(tr,y[t][tr]))
   for bi,kind in enumerate(BASES):
    cross=np.zeros((len(tr),classes[t]),dtype='float32')
    for si,(a,b) in enumerate(splits):
     m=make(kind,72000+fold*1000+ti*100+bi*10+si);m.fit(x[tr[a]],y[t][tr[a]]);cross[b]=aligned_proba(m,x[tr[b]],classes[t])
    full=make(kind,73000+fold*100+ti*10+bi);full.fit(x[tr],y[t][tr]);meta_tr.append(cross);meta_te.append(aligned_proba(full,x[te],classes[t]))
  ztr=np.hstack(meta_tr);zte=np.hstack(meta_te);info={'fold':fold,'tasks':{}}
  for ti,t in enumerate(TASKS):
   meta=LogisticRegression(C=.3,solver='liblinear',max_iter=1000,class_weight=None,random_state=74000+fold*10+ti);meta.fit(ztr,y[t][tr]);oof[t][te]=meta.predict(zte);info['tasks'][t]={'outer_micro_f1':float(f1_score(y[t][te],oof[t][te],average='micro'))}
  details.append(info);print(info,flush=True)
 fields=['sample_id','fold']+[z for t in TASKS for z in (t+'_truth',t+'_pred')]
 with (OUT/'predictions.csv').open('w',newline='') as h:
  w=csv.DictWriter(h,fieldnames=fields);w.writeheader()
  for i,sid in enumerate(ids):
   d={'sample_id':sid,'fold':int(folds[i])}
   for t in TASKS:d[t+'_truth']=labels[t][y[t][i]];d[t+'_pred']=labels[t][int(oof[t][i])]
   w.writerow(d)
 micro={t:float(f1_score(y[t],oof[t],average='micro')) for t in TASKS};macro={t:float(f1_score(y[t],oof[t],average='macro')) for t in TASKS};result={'schema':'tempo-micro-e02-v1','status':'complete','model_contract':'one nested-stacking pipeline with three task heads','base_models':list(BASES),'micro_f1':micro,'macro_f1_diagnostic':macro,'minimum_micro_f1':min(micro.values()),'all_tasks_at_least_0_70':min(micro.values())>=.7,'fold_details':details,'dataset_sha256':sha(DATA),'feature_sha256':{'clip':sha(CLIP),'siglip':sha(SIG)},'seconds':time.time()-start,'predictions_sha256':sha(OUT/'predictions.csv')};(OUT/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
