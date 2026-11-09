"""Nested feature-weight search; frozen inputs, no supervised OOF input features."""
import os
for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'):os.environ[key]='1'
import fcntl
import hashlib
import json
from pathlib import Path
import time
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator,TransformerMixin
from sklearn.metrics import f1_score,classification_report,confusion_matrix
from sklearn.model_selection import StratifiedKFold,GridSearchCV
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler,normalize
from sklearn.svm import SVC

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'04_hasil_eksperimen/e14_weighted_fusion'
FAMILIES=('description','source_reason','combined','description_reason','semantic_visual')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

class BlockFusion(TransformerMixin,BaseEstimator):
    def __init__(self,e5_weight=1,clip_weight=1):
        self.e5_weight=e5_weight;self.clip_weight=clip_weight

    def fit(self,x,y=None):
        assert x.shape[1]==3072
        self.scalers_=[StandardScaler().fit(x[:,a:b]) for a,b in ((0,1536),(1536,2560),(2560,3072))]
        return self

    def transform(self,x):
        blocks=[]
        for scaler,(a,b),weight in zip(self.scalers_,((0,1536),(1536,2560),(2560,3072)),
                                      (self.e5_weight,1,self.clip_weight)):
            blocks.append(normalize(scaler.transform(x[:,a:b]))*weight)
        result=np.hstack(blocks);assert np.isfinite(result).all()
        return result

def save(path,value):
    temp=path.with_suffix(path.suffix+'.tmp')
    temp.write_text(json.dumps(value,indent=2)+'\n');temp.replace(path)

def main():
    OUT.mkdir(exist_ok=True)
    lock=(OUT/'run.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    csv=ROOT/'03_data/DATASET_740_TASK2_DOMAIN.csv'
    assert sha(csv)=='cba20f8250bcb59481ed2d3d7d5d42fb8242c96a7ba2d11a2cd02ad80862961a'
    df=pd.read_csv(csv).fillna('');y=df.task2_domain_sumber.to_numpy();labels=sorted(set(y))
    e5_path=ROOT/'04_hasil_eksperimen/e06_semantic/e06_semantic/embeddings.npz'
    bge_folder=ROOT/'04_hasil_eksperimen/e13_bge_m3/e13_bge_m3'
    clip_path=ROOT/'03_data/fitur_clip_indobert_740.npz'
    assert sha(e5_path)=='1f0d2b2f346071fa673701847af39e8a22faf9e6a98195734982cd71e99af374'
    assert sha(clip_path)=='d27cd5dbecfffba3a8bbb96037f3181da20f1c95eb246a7d38a4627a90599e5c'
    bge_meta=json.loads((bge_folder/'meta.json').read_text())
    assert bge_meta['embeddings_sha256']==sha(bge_folder/'embeddings.npz') and bge_meta['csv_sha256']==sha(csv)
    e5=np.load(e5_path,allow_pickle=False);bge=np.load(bge_folder/'embeddings.npz',allow_pickle=False)
    assert np.array_equal(e5['sample_id'],df.sample_id) and np.array_equal(bge['sample_id'],df.sample_id)
    x=np.hstack([e5['description'],e5['source_reason'],bge['combined'],np.load(clip_path)['img']])
    assert x.shape==(740,3072) and np.isfinite(x).all()
    ref=ROOT/'04_hasil_eksperimen/e13_nested'
    verification=json.loads((ref/'verification.json').read_text());assert verification['status']=='verified'
    for name,digest in verification['sha256'].items():assert sha(ref/name)==digest
    reports={name:json.loads((ref/(name+'.json')).read_text()) for name in FAMILIES}
    predictions={name:pd.read_csv(ref/(name+'_oof.csv')) for name in FAMILIES}
    issues=pd.Categorical(df.task1_issue,categories=sorted(set(df.task1_issue))).codes
    counts=np.bincount(issues);strat=np.array([v if counts[v]>=5 else -1 for v in issues])
    folds=list(StratifiedKFold(5,shuffle=True,random_state=42).split(np.zeros(740),strat))
    expected_folds=np.zeros(740,int)
    for k,(_,te) in enumerate(folds,1):expected_folds[te]=k
    for name,rows in predictions.items():
        assert rows.sample_id.tolist()==df.sample_id.tolist() and rows.truth.tolist()==y.tolist()
        assert np.array_equal(rows.fold.to_numpy(),expected_folds)
        assert reports[name]['source_meta']==bge_meta
    grid={'fusion__e5_weight':[0,.5,1,2],'fusion__clip_weight':[0,.5,1,2],
          'clf__C':[1,10,100],'clf__gamma':['scale',.1,1],'clf__class_weight':[None,'balanced']}
    signature={'worker_sha256':sha(Path(__file__)),'data_sha256':sha(csv),'e5_sha256':sha(e5_path),
               'bge_sha256':sha(bge_folder/'embeddings.npz'),'clip_sha256':sha(clip_path),
               'reference_verification_sha256':sha(ref/'verification.json'),
               'grid':grid,'normalization':'StandardScaler fit per block, L2 per block, then weights',
               'outer':'Task1 baseline stratified5 seed42','inner':'Task2 stratified3 seed42',
               'selection_order':list(FAMILIES)+['weighted'],'n_jobs':1}
    save(OUT/'protocol.json',signature)
    fold_reports=[];weighted=np.empty(740,object);nested=np.empty(740,object)
    for k,(tr,te) in enumerate(folds,1):
        checkpoint=OUT/f'fold_{k}.json'
        if checkpoint.exists():
            record=json.loads(checkpoint.read_text())
            assert record['signature']==signature and record['train_indices']==tr.tolist() and record['test_indices']==te.tolist()
            assert record['sample_ids']==df.sample_id.iloc[te].tolist()
        else:
            started=time.monotonic()
            pipe=Pipeline([('fusion',BlockFusion()),('clf',SVC(kernel='rbf'))])
            search=GridSearchCV(pipe,grid,cv=StratifiedKFold(3,shuffle=True,random_state=42),
                                scoring='f1_macro',n_jobs=1,error_score='raise')
            search.fit(x[tr],y[tr]);weighted_prediction=search.predict(x[te])
            scores={name:reports[name]['folds'][k-1]['inner_macro_f1'] for name in FAMILIES}
            scores['weighted']=float(search.best_score_);best=max(scores,key=scores.get)
            routed=weighted_prediction if best=='weighted' else predictions[best].prediction.iloc[te].to_numpy()
            record={'signature':signature,'fold':k,'train_indices':tr.tolist(),'test_indices':te.tolist(),
                    'sample_ids':df.sample_id.iloc[te].tolist(),'inner_scores':scores,'family':best,
                    'weighted_params':search.best_params_,'weighted_predictions':weighted_prediction.tolist(),
                    'nested_predictions':routed.tolist(),'seconds':time.monotonic()-started}
            save(checkpoint,record)
            print(json.dumps({'fold':k,'family':best,'inner_scores':scores,'params':search.best_params_,
                              'seconds':record['seconds']}),flush=True)
        weighted[te]=record['weighted_predictions'];nested[te]=record['nested_predictions'];fold_reports.append(record)
    assert len(fold_reports)==5
    summaries={}
    for name,pred in (('weighted',weighted),('nested_selected',nested)):
        assert all(value in labels for value in pred)
        pd.DataFrame({'sample_id':df.sample_id,'truth':y,'prediction':pred,'fold':expected_folds}).to_csv(OUT/(name+'_oof.csv'),index=False)
        report={'samples':740,'macro_f1':float(f1_score(y,pred,labels=labels,average='macro',zero_division=0)),
                'classification':classification_report(y,pred,labels=labels,output_dict=True,zero_division=0),
                'confusion_matrix':confusion_matrix(y,pred,labels=labels).tolist(),
                'folds':fold_reports,'signature':signature}
        save(OUT/(name+'.json'),report);summaries[name]=report['macro_f1']
    print('COMPLETE E14',json.dumps(summaries),flush=True)

if __name__=='__main__':main()
