"""Nested evaluation of frozen E5 features on server learn, limited CPU."""
import os
for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'):os.environ[key]='1'
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score, classification_report, confusion_matrix
from sklearn.model_selection import StratifiedKFold,GridSearchCV
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC,LinearSVC
ROOT=Path(__file__).resolve().parents[2]
ap=argparse.ArgumentParser();ap.add_argument('features',type=Path);args=ap.parse_args()
csv=ROOT/'03_data/DATASET_740_TASK2_DOMAIN.csv'
df=pd.read_csv(csv).fillna('');y=df.task2_domain_sumber.to_numpy();labels=sorted(set(y))
meta=json.loads((args.features/'meta.json').read_text())
assert hashlib.sha256(csv.read_bytes()).hexdigest()==meta['csv_sha256']
z=np.load(args.features/'embeddings.npz',allow_pickle=False)
assert np.array_equal(z['sample_id'],df.sample_id.to_numpy())
out=ROOT/'04_hasil_eksperimen/e13_nested';out.mkdir(exist_ok=True)
issues=pd.Categorical(df.task1_issue,categories=sorted(set(df.task1_issue))).codes
count=np.bincount(issues);strat=np.array([v if count[v]>=5 else -1 for v in issues])
folds=list(StratifiedKFold(5,shuffle=True,random_state=42).split(np.zeros(len(y)),strat))
variants={key:z[key] for key in ('description','source_reason','combined')}
variants['description_reason']=np.hstack([z['description'],z['source_reason']])
feature_path=ROOT/'03_data/fitur_clip_indobert_740.npz'
assert hashlib.sha256(feature_path.read_bytes()).hexdigest()=='d27cd5dbecfffba3a8bbb96037f3181da20f1c95eb246a7d38a4627a90599e5c'
original=np.load(feature_path)
variants['semantic_visual']=np.hstack([z['combined'],original['img']])
for name,x in variants.items():
    assert x.shape[0]==740 and np.isfinite(x).all()
    if (out/(name+'.json')).exists():continue
    pred=np.empty(len(y),object);fold_id=np.zeros(len(y),int);records=[]
    for k,(tr,te) in enumerate(folds,1):
        model=Pipeline([('scale',StandardScaler()),('clf',SVC())])
        grid=[{'clf':[SVC(kernel='rbf')],'clf__C':[1,10,100],
               'clf__gamma':['scale',0.0003,0.003],'clf__class_weight':[None,'balanced']},
              {'clf':[LinearSVC(max_iter=10000,random_state=42)],'clf__C':[.01,.1,1],
               'clf__class_weight':[None,'balanced']},
              {'clf':[LogisticRegression(max_iter=3000)],'clf__C':[.01,.1,1],
               'clf__class_weight':[None,'balanced']}]
        search=GridSearchCV(model,grid,cv=StratifiedKFold(3,shuffle=True,random_state=42),
                            scoring='f1_macro',n_jobs=1,pre_dispatch=1,error_score='raise')
        search.fit(x[tr],y[tr]);pred[te]=search.predict(x[te]);fold_id[te]=k
        score=float(f1_score(y[te],pred[te],labels=labels,average='macro',zero_division=0))
        records.append({'fold':k,'macro_f1':score,'inner_macro_f1':search.best_score_,
                        'params':{key:str(v) for key,v in search.best_params_.items()}})
        print(name,k,score,flush=True)
    pd.DataFrame({'sample_id':df.sample_id,'truth':y,'prediction':pred,'fold':fold_id}).to_csv(out/(name+'_oof.csv'),index=False)
    report={'macro_f1':float(f1_score(y,pred,labels=labels,average='macro',zero_division=0)),
            'folds':records,'classification':classification_report(y,pred,labels=labels,output_dict=True,zero_division=0),
            'confusion_matrix':confusion_matrix(y,pred,labels=labels).tolist(),'source_meta':meta}
    (out/(name+'.json')).write_text(json.dumps(report,indent=2))
    print('COMPLETE',name,report['macro_f1'],flush=True)
joined=[];selection=[]
for k in range(1,6):
    scores={name:json.loads((out/(name+'.json')).read_text())['folds'][k-1]['inner_macro_f1'] for name in variants}
    best=max(scores,key=scores.get);rows=pd.read_csv(out/(best+'_oof.csv'))
    joined.append(rows[rows.fold==k]);selection.append({'fold':k,'family':best})
oof=pd.concat(joined).set_index('sample_id').loc[df.sample_id].reset_index()
oof.to_csv(out/'nested_selected_oof.csv',index=False)
(out/'nested_selected.json').write_text(json.dumps({'macro_f1':float(f1_score(oof.truth,oof.prediction,average='macro',zero_division=0)),
    'selection':selection,'classification':classification_report(oof.truth,oof.prediction,output_dict=True,zero_division=0)},indent=2))
