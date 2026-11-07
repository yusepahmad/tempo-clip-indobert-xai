"""Nested fusion with frozen zero-shot categories; no supervised OOF inputs."""
import os
for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'):os.environ[key]='1'
import fcntl
import hashlib
import json
from pathlib import Path
import sys
import time
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator,TransformerMixin
from sklearn.metrics import f1_score,classification_report,confusion_matrix
from sklearn.model_selection import GridSearchCV,StratifiedKFold,ParameterGrid
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler,normalize
from sklearn.svm import SVC

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'04_hasil_eksperimen/e20_zero_shot_fusion'
sys.path.insert(0,str(ROOT/'01_notebook/e18_hosted'))
from parse_v2 import parse_answer
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
GRID={'fusion__e5_weight':[.5,2],'fusion__vlm_weight':[0,.5,1,2,4],
      'clf__C':[1,10,100],'clf__gamma':['scale',.1,1],'clf__class_weight':[None,'balanced']}

class ZeroShotFusion(TransformerMixin,BaseEstimator):
    def __init__(self,e5_weight=.5,vlm_weight=1):
        self.e5_weight=e5_weight;self.vlm_weight=vlm_weight
    def fit(self,x,y=None):
        assert x.shape[1]==3080 and np.isfinite(x).all()
        self.scalers_=[StandardScaler().fit(x[:,a:b]) for a,b in ((0,1536),(1536,2560),(2560,3072))]
        return self
    def transform(self,x):
        assert x.shape[1]==3080 and np.isfinite(x).all()
        category=x[:,3072:]
        assert np.all((category==0)|(category==1)) and np.all(category.sum(axis=1)==1)
        blocks=[normalize(s.transform(x[:,a:b]))*weight for s,(a,b),weight in zip(
            self.scalers_,((0,1536),(1536,2560),(2560,3072)),(self.e5_weight,1,1))]
        result=np.hstack(blocks+[category*self.vlm_weight]);assert np.isfinite(result).all()
        return result

def save(path,value):
    tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(value,indent=2)+'\n');tmp.replace(path)

def load_inputs():
    csv=ROOT/'03_data/DATASET_740_TASK2_DOMAIN.csv'
    assert sha(csv)=='cba20f8250bcb59481ed2d3d7d5d42fb8242c96a7ba2d11a2cd02ad80862961a'
    df=pd.read_csv(csv).fillna('');assert len(df)==740 and df.sample_id.is_unique
    y=df.task2_domain_sumber.to_numpy();labels=sorted(set(y));assert len(labels)==7
    prior=ROOT/'04_hasil_eksperimen/e18_hosted'
    verified=json.loads((prior/'verification.json').read_text())
    assert verified['status']=='verified' and verified['samples']==740
    assert verified['verifier_sha256']==sha(ROOT/'01_notebook/e18_hosted/verify.py')
    for name,digest in verified['sha256'].items():assert sha(prior/name)==digest
    parsed=json.loads((prior/'parsed_v2/metrics.json').read_text())
    assert parsed['status']=='verified' and parsed['samples']==740 and parsed['classes']==labels
    assert parsed['strict_verification_sha256']==sha(prior/'verification.json')
    assert parsed['parser_sha256']==sha(ROOT/'01_notebook/e18_hosted/parse_v2.py')
    assert parsed['evaluator_sha256']==sha(ROOT/'01_notebook/e18_hosted/evaluate_parsed_v2.py')
    assert parsed['oof_sha256']==sha(prior/'parsed_v2/oof.csv')
    e18config=json.loads((prior/'config.json').read_text())
    assert e18config['protocol']=='zero_shot_no_fit_no_target_in_prompt_no_retries_invalid_counts_wrong'
    assert e18config['model']=='google/gemini-3-flash-preview'
    rows=pd.read_csv(prior/'parsed_v2/oof.csv').fillna('')
    assert rows.sample_id.to_list()==df.sample_id.to_list() and rows.truth.to_list()==y.tolist()
    onehot=np.zeros((740,8),dtype=np.float64);category=[]
    for i,row in rows.iterrows():
        record=json.loads((prior/'records'/f'{i:04d}.json').read_text())
        assert record['status']=='complete' and record['sample_id']==row.sample_id
        code,_=parse_answer(record['response']['choices'][0]['message'].get('content'),labels)
        index=ord(code)-ord('A') if code!='INVALID' else 7
        value=labels[index] if index<7 else 'INVALID';assert row.prediction==value
        onehot[i,index]=1;category.append(value)
    assert np.all(onehot.sum(axis=1)==1)
    e5_path=ROOT/'04_hasil_eksperimen/e06_semantic/e06_semantic/embeddings.npz'
    bge_path=ROOT/'04_hasil_eksperimen/e13_bge_m3/e13_bge_m3/embeddings.npz'
    clip_path=ROOT/'03_data/fitur_clip_indobert_740.npz'
    assert sha(e5_path)=='1f0d2b2f346071fa673701847af39e8a22faf9e6a98195734982cd71e99af374'
    assert sha(bge_path)=='c0d7d1fc9ac42988b0d107a694d7d3b355105f8640f776ace2617eed936495c4'
    assert sha(clip_path)=='d27cd5dbecfffba3a8bbb96037f3181da20f1c95eb246a7d38a4627a90599e5c'
    e5=np.load(e5_path,allow_pickle=False);bge=np.load(bge_path,allow_pickle=False);clip=np.load(clip_path,allow_pickle=False)
    assert np.array_equal(e5['sample_id'],df.sample_id) and np.array_equal(bge['sample_id'],df.sample_id)
    x=np.hstack([e5['description'],e5['source_reason'],bge['combined'],clip['img'],onehot])
    assert x.shape==(740,3080) and np.isfinite(x).all()
    issues=pd.Categorical(df.task1_issue,categories=sorted(set(df.task1_issue))).codes
    count=np.bincount(issues);strat=[v if count[v]>=5 else -1 for v in issues]
    folds=list(StratifiedKFold(5,shuffle=True,random_state=42).split(np.zeros(740),strat))
    fold=np.zeros(740,dtype=int)
    for k,(_,test) in enumerate(folds,1):fold[test]=k
    assert np.array_equal(fold,rows.fold.to_numpy())
    signature=dict(worker_sha256=sha(Path(__file__)),data_sha256=sha(csv),e5_sha256=sha(e5_path),
                   bge_sha256=sha(bge_path),clip_sha256=sha(clip_path),
                   strict_verification_sha256=sha(prior/'verification.json'),
                   parsed_metrics_sha256=sha(prior/'parsed_v2/metrics.json'),
                   parsed_oof_sha256=sha(prior/'parsed_v2/oof.csv'),
                   category_sha256=hashlib.sha256(json.dumps(category).encode()).hexdigest(),
                   feature_sha256=hashlib.sha256(x.tobytes()).hexdigest(),
                   grid=GRID,outer='Task1 baseline stratified5 seed42',inner='Task2 stratified3 seed42',
                   normalization='train-fit StandardScaler/L2 per numeric block; fixed one-hot8 unscaled; then weights',
                   n_jobs=1)
    return df,y,labels,x,folds,fold,signature

def main():
    df,y,labels,x,folds,fold,signature=load_inputs()
    OUT.mkdir(exist_ok=True)
    lock=(OUT/'run.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    if (OUT/'protocol.json').exists():assert json.loads((OUT/'protocol.json').read_text())==signature
    else:save(OUT/'protocol.json',signature)
    reports=[];prediction=np.empty(740,object)
    for k,(train,test) in enumerate(folds,1):
        path=OUT/f'fold_{k}.json'
        if path.exists():
            record=json.loads(path.read_text());assert record['signature']==signature
            assert record['train_indices']==train.tolist() and record['test_indices']==test.tolist()
            assert record['sample_ids']==df.sample_id.iloc[test].to_list()
        else:
            started=time.monotonic()
            pipe=Pipeline([('fusion',ZeroShotFusion()),('clf',SVC(kernel='rbf'))])
            search=GridSearchCV(pipe,GRID,cv=StratifiedKFold(3,shuffle=True,random_state=42),
                                scoring='f1_macro',n_jobs=1,error_score='raise')
            search.fit(x[train],y[train]);pred=search.predict(x[test])
            assert len(search.cv_results_['params'])==len(list(ParameterGrid(GRID)))==180
            record=dict(signature=signature,fold=k,train_indices=train.tolist(),test_indices=test.tolist(),
                        sample_ids=df.sample_id.iloc[test].to_list(),predictions=pred.tolist(),
                        best_params=search.best_params_,best_index=int(search.best_index_),
                        inner_macro_f1=float(search.best_score_),grid_params=search.cv_results_['params'],
                        grid_scores=search.cv_results_['mean_test_score'].tolist(),seconds=time.monotonic()-started)
            save(path,record)
            print(json.dumps(dict(fold=k,inner_macro_f1=record['inner_macro_f1'],params=record['best_params'],
                                  seconds=record['seconds'])),flush=True)
        prediction[test]=record['predictions'];reports.append(record)
    assert all(value in labels for value in prediction)
    pd.DataFrame(dict(sample_id=df.sample_id,truth=y,prediction=prediction,fold=fold)).to_csv(OUT/'oof.csv',index=False)
    report=dict(samples=740,macro_f1=float(f1_score(y,prediction,labels=labels,average='macro',zero_division=0)),
                classification=classification_report(y,prediction,labels=labels,output_dict=True,zero_division=0),
                confusion_matrix=confusion_matrix(y,prediction,labels=labels).tolist(),signature=signature,
                oof_sha256=sha(OUT/'oof.csv'),folds=reports)
    save(OUT/'metrics.json',report);print('COMPLETE E20',report['macro_f1'],flush=True)

if __name__=='__main__':main()
