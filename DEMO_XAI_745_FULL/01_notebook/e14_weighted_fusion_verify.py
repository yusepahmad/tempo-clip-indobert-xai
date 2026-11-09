"""Re-score chosen inner parameters and reproduce all E14 outer predictions."""
import os
for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'):os.environ[key]='1'
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedKFold,cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.svm import SVC
from e14_weighted_fusion import BlockFusion,FAMILIES

ROOT=Path(__file__).resolve().parents[1]
out=ROOT/'04_hasil_eksperimen/e14_weighted_fusion'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
# No audit output is created unless both complete OOF artifacts already exist.
reports={name:json.loads((out/(name+'.json')).read_text()) for name in ('weighted','nested_selected')}
rows={name:pd.read_csv(out/(name+'_oof.csv')) for name in reports}
protocol=json.loads((out/'protocol.json').read_text())
assert protocol['worker_sha256']==sha(Path(__file__).with_name('e14_weighted_fusion.py'))
assert protocol['n_jobs']==1 and protocol['inner']=='Task2 stratified3 seed42'
assert protocol['outer']=='Task1 baseline stratified5 seed42'
csv=ROOT/'03_data/DATASET_740_TASK2_DOMAIN.csv';assert sha(csv)==protocol['data_sha256']
assert sha(csv)=='cba20f8250bcb59481ed2d3d7d5d42fb8242c96a7ba2d11a2cd02ad80862961a'
df=pd.read_csv(csv).fillna('');y=df.task2_domain_sumber.to_numpy();labels=sorted(set(y))
e5_path=ROOT/'04_hasil_eksperimen/e06_semantic/e06_semantic/embeddings.npz'
bge_path=ROOT/'04_hasil_eksperimen/e13_bge_m3/e13_bge_m3/embeddings.npz'
clip_path=ROOT/'03_data/fitur_clip_indobert_740.npz'
for key,path in [('e5_sha256',e5_path),('bge_sha256',bge_path),('clip_sha256',clip_path)]:assert sha(path)==protocol[key]
e5=np.load(e5_path,allow_pickle=False);bge=np.load(bge_path,allow_pickle=False)
assert np.array_equal(e5['sample_id'],df.sample_id) and np.array_equal(bge['sample_id'],df.sample_id)
x=np.hstack([e5['description'],e5['source_reason'],bge['combined'],np.load(clip_path)['img']])
assert x.shape==(740,3072) and np.isfinite(x).all()
ref=ROOT/'04_hasil_eksperimen/e13_nested'
assert sha(ref/'verification.json')==protocol['reference_verification_sha256']
reference=json.loads((ref/'verification.json').read_text())
assert reference['status']=='verified'
for name,digest in reference['sha256'].items():assert sha(ref/name)==digest
controls={name:json.loads((ref/(name+'.json')).read_text()) for name in FAMILIES}
control_rows={name:pd.read_csv(ref/(name+'_oof.csv')) for name in FAMILIES}
issues=pd.Categorical(df.task1_issue,categories=sorted(set(df.task1_issue))).codes
counts=np.bincount(issues);strat=np.array([i if counts[i]>=5 else -1 for i in issues])
folds=list(StratifiedKFold(5,shuffle=True,random_state=42).split(np.zeros(740),strat))
fold_ids=np.zeros(740,int);records=[];reproduced=np.empty(740,object);routed=np.empty(740,object)
for k,(tr,te) in enumerate(folds,1):
    record=json.loads((out/f'fold_{k}.json').read_text());records.append(record);fold_ids[te]=k
    assert record['signature']==protocol and record['fold']==k
    assert record['train_indices']==tr.tolist() and record['test_indices']==te.tolist()
    assert record['sample_ids']==df.sample_id.iloc[te].tolist() and not set(tr)&set(te)
    assert set(record['weighted_params'])==set(protocol['grid'])
    for key,value in record['weighted_params'].items():assert value in protocol['grid'][key]
    pipe=Pipeline([('fusion',BlockFusion()),('clf',SVC(kernel='rbf'))])
    pipe.set_params(**record['weighted_params'])
    inner=float(cross_val_score(pipe,x[tr],y[tr],cv=StratifiedKFold(3,shuffle=True,random_state=42),
                               scoring='f1_macro',n_jobs=1,error_score='raise').mean())
    assert abs(inner-record['inner_scores']['weighted'])<1e-12
    pipe.fit(x[tr],y[tr]);pred=pipe.predict(x[te])
    assert pred.tolist()==record['weighted_predictions'];reproduced[te]=pred
    scores={name:controls[name]['folds'][k-1]['inner_macro_f1'] for name in FAMILIES}
    scores['weighted']=inner
    for name,value in scores.items():assert abs(value-record['inner_scores'][name])<1e-12
    best=max(scores,key=scores.get);assert best==record['family']
    routed[te]=pred if best=='weighted' else control_rows[best].prediction.iloc[te].to_numpy()
    assert routed[te].tolist()==record['nested_predictions']
    print('Verified refit/inner/routing fold',k,flush=True)

def count_scores(frame):
    lookup={label:i for i,label in enumerate(labels)};matrix=np.zeros((7,7),int)
    for truth,prediction in zip(frame.truth,frame.prediction):matrix[lookup[truth],lookup[prediction]]+=1
    scores={}
    for label,i in lookup.items():
        tp=int(matrix[i,i]);denominator=int(matrix[i,:].sum()+matrix[:,i].sum())
        scores[label]=2*tp/denominator if denominator else 0
    return sum(scores.values())/7,scores,matrix.tolist()

scores={}
for name,expected in [('weighted',reproduced),('nested_selected',routed)]:
    frame=rows[name];report=reports[name]
    assert len(frame)==740 and frame.sample_id.is_unique and report['samples']==740
    assert frame.sample_id.tolist()==df.sample_id.tolist() and frame.truth.tolist()==y.tolist()
    assert np.array_equal(frame.fold.to_numpy(),fold_ids) and np.array_equal(frame.prediction.to_numpy(),expected)
    assert report['signature']==protocol and report['folds']==records
    score,per_class,matrix=count_scores(frame);assert abs(score-report['macro_f1'])<1e-12
    assert matrix==report['confusion_matrix']
    for label in labels:assert abs(per_class[label]-report['classification'][label]['f1-score'])<1e-12
    scores[name]={'macro_f1_manual':score,'per_class_f1':per_class}
result={'status':'verified','samples':740,'scores':scores,
        'checks':['original data/source/feature/reference hashes','exact baseline outer splits and original IDs/labels',
                  'chosen parameters belong to predeclared grid','chosen inner score recomputed on training only',
                  'all 740 weighted predictions reproduced from outer-training refits',
                  'family choice and routed predictions reconstructed','manual TP/FP/FN and confusion matrices'],
        'selected_families':[r['family'] for r in records],
        'sha256':{p.name:sha(p) for p in sorted(out.iterdir()) if p.is_file() and p.name not in ('verification.json','run.lock') and not p.name.endswith('.tmp')}}
(out/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'status':'verified','samples':740,'scores':scores},indent=2),flush=True)
