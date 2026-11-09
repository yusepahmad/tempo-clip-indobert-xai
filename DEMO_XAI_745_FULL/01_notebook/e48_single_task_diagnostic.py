#!/usr/bin/env python3
"""E48: nested single-task diagnostic on the exact E42 outer folds."""
import csv, hashlib, json, time
from collections import Counter
from pathlib import Path
import numpy as np
from sklearn.metrics import f1_score
from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import StandardScaler, normalize
from sklearn.svm import LinearSVC

ROOT=Path(__file__).resolve().parents[1]
CACHE=ROOT/'04_hasil_eksperimen/e41_cached_tail/cache/front_cache.npz'
DATA=ROOT/'03_data/DATASET_740_TASK2_DOMAIN.csv'
E42=ROOT/'04_hasil_eksperimen/e42_tail_grid/oof.csv'
OUT=ROOT/'04_hasil_eksperimen/e48_single_task_diagnostic'
TASKS=('task1_issue','task2_domain_sumber','task3_primary_entity_type')
CONFIGS=[(feature,scale,c) for feature in ('visual','text','both') for scale in ('l2','standard') for c in (.001,.01,.1,1.)]

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(path):
    with path.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def matrix(z,feature):
    if feature=='visual':return z['visual'].astype('float32')
    if feature=='text':return z['base_mean'].astype('float32')
    return np.hstack([z['visual'],z['base_mean']]).astype('float32')
def transform(x,tr,te,scale):
    if scale=='l2':return normalize(x[tr]),normalize(x[te])
    s=StandardScaler().fit(x[tr]);return s.transform(x[tr]),s.transform(x[te])

started=time.time();rows=read(DATA);old=read(E42);z=dict(np.load(CACHE));ids=[r['sample_id'] for r in rows]
assert len(rows)==740 and ids==z['sample_ids'].tolist()==[r['sample_id'] for r in old]
outer=np.array([int(r['fold']) for r in old]);assert sorted(set(outer))==[1,2,3,4,5]
predictions={};details={}
for task in TASKS:
    labels=sorted({r[task] for r in rows});enc={v:i for i,v in enumerate(labels)};y=np.array([enc[r[task]] for r in rows]);pred=np.full(740,-1)
    folds=[]
    for fold in range(1,6):
        tr=np.where(outer!=fold)[0];te=np.where(outer==fold)[0]
        inner=list(StratifiedKFold(3,shuffle=True,random_state=4800+fold).split(tr,y[tr]))
        scores=[]
        for ci,(feature,scale,c) in enumerate(CONFIGS):
            x=matrix(z,feature);inner_scores=[]
            for a,b in inner:
                ia,ib=tr[a],tr[b];xa,xb=transform(x,ia,ib,scale)
                model=LinearSVC(C=c,class_weight='balanced',dual='auto',max_iter=10000,random_state=42)
                model.fit(xa,y[ia]);p=model.predict(xb)
                inner_scores.append(f1_score(y[ib],p,labels=range(len(labels)),average='macro',zero_division=0))
            scores.append(float(np.mean(inner_scores)))
        best=max(range(len(CONFIGS)),key=lambda i:(scores[i],-i));feature,scale,c=CONFIGS[best];x=matrix(z,feature);xa,xb=transform(x,tr,te,scale)
        model=LinearSVC(C=c,class_weight='balanced',dual='auto',max_iter=10000,random_state=42).fit(xa,y[tr]);pred[te]=model.predict(xb)
        folds.append({'fold':fold,'selected_config':{'feature':feature,'scale':scale,'C':c},'inner_macro_f1':scores[best],
                      'outer_macro_f1':f1_score(y[te],pred[te],labels=range(len(labels)),average='macro',zero_division=0),
                      'train_indices':tr.tolist(),'test_indices':te.tolist()})
    assert (pred>=0).all();predictions[task]=[labels[i] for i in pred]
    details[task]={'labels':labels,'folds':folds,'macro_f1':f1_score(y,pred,labels=range(len(labels)),average='macro',zero_division=0),
                   'class_counts':dict(sorted(Counter(r[task] for r in rows).items()))}

OUT.mkdir(parents=True,exist_ok=True)
fields=['sample_id','fold']+[v for t in TASKS for v in (t+'_truth',t+'_pred',t+'_e42')]
with (OUT/'oof.csv').open('w',encoding='utf-8',newline='') as f:
    w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
    for i,r in enumerate(rows):
        q={'sample_id':r['sample_id'],'fold':int(outer[i])}
        for t in TASKS:q.update({t+'_truth':r[t],t+'_pred':predictions[t][i],t+'_e42':old[i][t+'_pred']})
        w.writerow(q)
result={'schema':'tempo-e48-single-task-diagnostic-v1','status':'complete','eligible_for_joint_delivery':False,
        'purpose':'measure negative transfer; not a final joint model','dataset_sha256':sha(DATA),'cache_sha256':sha(CACHE),'e42_oof_sha256':sha(E42),
        'configs':[{'feature':a,'scale':b,'C':c} for a,b,c in CONFIGS], 'tasks':details,'seconds':time.time()-started}
(OUT/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2,sort_keys=True)+'\n')
print(json.dumps({'status':'complete','macro_f1':{t:details[t]['macro_f1'] for t in TASKS},'seconds':result['seconds']},indent=2))
