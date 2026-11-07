"""Audit all E13 OOF families and train-selected family routing independently."""
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedKFold

ROOT=Path(__file__).resolve().parents[2]
out=ROOT/'04_hasil_eksperimen/e13_nested'
feature=ROOT/'04_hasil_eksperimen/e13_bge_m3/e13_bge_m3'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
# Demand complete nested artifacts before constructing an audit or writing evidence.
nested=json.loads((out/'nested_selected.json').read_text())
selected=pd.read_csv(out/'nested_selected_oof.csv')
df=pd.read_csv(ROOT/'03_data/DATASET_740_TASK2_DOMAIN.csv').fillna('')
meta=json.loads((feature/'meta.json').read_text())
assert sha(ROOT/'03_data/DATASET_740_TASK2_DOMAIN.csv')==meta['csv_sha256']=='cba20f8250bcb59481ed2d3d7d5d42fb8242c96a7ba2d11a2cd02ad80862961a'
assert sha(feature/'embeddings.npz')==meta['embeddings_sha256']
assert sha(ROOT/'01_notebook/kaggle_e13/worker.py')==meta['worker_sha256']
assert sha(ROOT/'03_data/fitur_clip_indobert_740.npz')=='d27cd5dbecfffba3a8bbb96037f3181da20f1c95eb246a7d38a4627a90599e5c'
labels=sorted(set(df.task2_domain_sumber));indices={label:i for i,label in enumerate(labels)}
issues=pd.Categorical(df.task1_issue,categories=sorted(set(df.task1_issue))).codes
counts=np.bincount(issues);strat=np.array([v if counts[v]>=5 else -1 for v in issues])
fold_ids=np.zeros(740,int)
for k,(_,te) in enumerate(StratifiedKFold(5,shuffle=True,random_state=42).split(np.zeros(740),strat),1):fold_ids[te]=k

def audit_rows(rows):
    assert len(rows)==740 and rows.sample_id.is_unique
    assert rows.sample_id.tolist()==df.sample_id.tolist()
    assert rows.truth.tolist()==df.task2_domain_sumber.tolist()
    assert np.array_equal(rows.fold.to_numpy(),fold_ids)
    assert set(rows.prediction)<=set(labels)

def count_scores(rows):
    scores={};matrix=np.zeros((7,7),int)
    for a,b in zip(rows.truth,rows.prediction):matrix[indices[a],indices[b]]+=1
    for label,i in indices.items():
        tp=int(matrix[i,i]);fp=int(matrix[:,i].sum())-tp;fn=int(matrix[i,:].sum())-tp
        scores[label]=2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else 0
    return sum(scores.values())/7,scores,matrix.tolist()

families=('description','source_reason','combined','description_reason','semantic_visual')
reports={};predictions={};scores={};models={}
for name in families:
    report=json.loads((out/(name+'.json')).read_text());rows=pd.read_csv(out/(name+'_oof.csv'))
    audit_rows(rows);score,per_class,matrix=count_scores(rows)
    assert abs(score-report['macro_f1'])<1e-12 and report['source_meta']==meta
    assert report['confusion_matrix']==matrix
    assert len(report['folds'])==5
    for label in labels:assert abs(report['classification'][label]['f1-score']-per_class[label])<1e-12
    for k,record in enumerate(report['folds'],1):
        assert record['fold']==k and 0<=record['inner_macro_f1']<=1
        fold_score,_,_=count_scores(rows[rows.fold==k])
        assert abs(fold_score-record['macro_f1'])<1e-12
    reports[name]=report;predictions[name]=rows;scores[name]=score
    models[name]=[r['params']['clf'] for r in report['folds']]
audit_rows(selected);assert len(nested['selection'])==5
for k,record in enumerate(nested['selection'],1):
    best=max(families,key=lambda name:reports[name]['folds'][k-1]['inner_macro_f1'])
    assert record=={'fold':k,'family':best}
    assert selected[selected.fold==k].prediction.tolist()==predictions[best][predictions[best].fold==k].prediction.tolist()
score,per_class,_=count_scores(selected)
assert abs(score-nested['macro_f1'])<1e-12
result={'status':'verified','samples':740,'macro_f1_manual':score,'per_class_f1':per_class,
        'family_macro_f1_manual':scores,'selection':nested['selection'],'selected_classifiers':models,
        'checks':['original data and source/feature hashes','all six sets of 740 original IDs/labels/baseline folds',
                  'all family and fold scores counted manually','all class scores and confusion matrices',
                  'nested family chosen only by recorded inner-CV score','routed predictions exactly match selected families'],
        'evaluator_sha256':sha(Path(__file__).parent/'evaluate.py'),
        'sha256':{p.name:sha(p) for p in sorted(out.iterdir()) if p.is_file() and p.name!='verification.json'}}
(out/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
