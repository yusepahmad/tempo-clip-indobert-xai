#!/usr/bin/env python3
"""Micro-E01: one multitask bundle with independently selected tabular heads."""
import csv,hashlib,json,time
from pathlib import Path
import numpy as np
from sklearn.ensemble import ExtraTreesClassifier,RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

ROOT=Path(__file__).resolve().parents[3];P=ROOT/'DEMO_XAI_745_FULL';DATA=P/'03_data/DATASET_740_TASK2_DOMAIN.csv';CLIP=P/'04_hasil_eksperimen/e41_cached_tail/cache/front_cache.npz';SIG=P/'04_hasil_eksperimen/next_research_20261017/01_model_comparison/M02_siglip2_indobert/features.npz';FOLDS=P/'04_hasil_eksperimen/e42_tail_grid/oof.csv';OUT=P/'04_hasil_eksperimen/next_research_20261017/06_micro_f1/MICRO_E01_tabular_heads';TASKS=('task1_issue','task2_domain_sumber','task3_primary_entity_type')
CANDIDATES=[
 ('logreg_all',dict(kind='lr',features='all',C=.1,class_weight=None)),('logreg_all_bal',dict(kind='lr',features='all',C=.1,class_weight='balanced')),
 ('svc_all',dict(kind='svc',features='all',C=1.,class_weight=None)),('svc_all_c5',dict(kind='svc',features='all',C=5.,class_weight=None)),('svc_all_bal',dict(kind='svc',features='all',C=1.,class_weight='balanced')),
 ('extra_all',dict(kind='extra',features='all',max_features=.5,min_samples_leaf=1,class_weight=None)),('extra_all_bal',dict(kind='extra',features='all',max_features='sqrt',min_samples_leaf=1,class_weight='balanced')),
]
def read(p):
 with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def model(cfg,seed):
 if cfg['kind']=='lr':return make_pipeline(StandardScaler(),LogisticRegression(C=cfg['C'],class_weight=cfg['class_weight'],max_iter=3000,random_state=seed))
 if cfg['kind']=='svc':return make_pipeline(StandardScaler(),SVC(C=cfg['C'],class_weight=cfg['class_weight'],kernel='rbf',gamma='scale',random_state=seed))
 if cfg['kind']=='extra':return ExtraTreesClassifier(n_estimators=120,max_features=cfg['max_features'],min_samples_leaf=cfg['min_samples_leaf'],class_weight=cfg['class_weight'],n_jobs=-1,random_state=seed)
 return RandomForestClassifier(n_estimators=120,max_features=cfg['max_features'],min_samples_leaf=cfg['min_samples_leaf'],class_weight=cfg['class_weight'],n_jobs=-1,random_state=seed)
def main():
 start=time.time();OUT.mkdir(parents=True,exist_ok=True);rows,fr=read(DATA),read(FOLDS);c=np.load(CLIP);s=np.load(SIG);ids=[r['sample_id'] for r in rows];assert ids==c['sample_ids'].tolist()==s['sample_ids'].tolist()==[r['sample_id'] for r in fr]
 feats={'cliptext':np.hstack([c['visual'],c['base_mean']]).astype('float32'),'all':np.hstack([c['visual'],s['image'],c['base_mean']]).astype('float32')};folds=np.array([int(r['fold']) for r in fr]);labels={t:sorted({r[t] for r in rows}) for t in TASKS};y={t:np.array([{x:i for i,x in enumerate(labels[t])}[r[t]] for r in rows]) for t in TASKS};oof={t:np.full(740,-1) for t in TASKS};details=[]
 for fold in range(1,6):
  tr,te=np.where(folds!=fold)[0],np.where(folds==fold)[0];fold_info={'fold':fold,'tasks':{}}
  for ti,t in enumerate(TASKS):
   inner=list(StratifiedKFold(3,shuffle=True,random_state=61000+fold*10+ti).split(tr,y[t][tr]));scores=[]
   for ci,(name,cfg) in enumerate(CANDIDATES):
    vals=[]
    for si,(a,b) in enumerate(inner):
     a,b=tr[a],tr[b];m=model(cfg,62000+fold*1000+ti*100+ci*10+si);m.fit(feats[cfg['features']][a],y[t][a]);vals.append(f1_score(y[t][b],m.predict(feats[cfg['features']][b]),average='micro'))
    scores.append({'candidate':name,'config':cfg,'inner_micro_f1':float(np.mean(vals))})
   chosen=max(scores,key=lambda x:x['inner_micro_f1']);m=model(chosen['config'],63000+fold*10+ti);m.fit(feats[chosen['config']['features']][tr],y[t][tr]);oof[t][te]=m.predict(feats[chosen['config']['features']][te]);fold_info['tasks'][t]={'selected':chosen,'outer_micro_f1':float(f1_score(y[t][te],oof[t][te],average='micro'))};print(fold,t,fold_info['tasks'][t],flush=True)
  details.append(fold_info)
 fields=['sample_id','fold']+[z for t in TASKS for z in (t+'_truth',t+'_pred')]
 with (OUT/'predictions.csv').open('w',newline='') as h:
  w=csv.DictWriter(h,fieldnames=fields);w.writeheader()
  for i,sid in enumerate(ids):
   d={'sample_id':sid,'fold':int(folds[i])}
   for t in TASKS:d[t+'_truth']=labels[t][y[t][i]];d[t+'_pred']=labels[t][int(oof[t][i])]
   w.writerow(d)
 micro={t:float(f1_score(y[t],oof[t],average='micro')) for t in TASKS};macro={t:float(f1_score(y[t],oof[t],average='macro')) for t in TASKS};result={'schema':'tempo-micro-e01-v1','status':'complete','model_contract':'one serialized multitask bundle with three training-only-selected heads','micro_f1':micro,'macro_f1_diagnostic':macro,'minimum_micro_f1':min(micro.values()),'all_tasks_at_least_0_70':min(micro.values())>=.7,'fold_details':details,'dataset_sha256':sha(DATA),'feature_sha256':{'clip':sha(CLIP),'siglip':sha(SIG)},'seconds':time.time()-start,'predictions_sha256':sha(OUT/'predictions.csv')};(OUT/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result['micro_f1'],indent=2))
if __name__=='__main__':main()
