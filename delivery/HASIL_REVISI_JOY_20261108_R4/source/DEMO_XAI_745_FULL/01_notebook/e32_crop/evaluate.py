"""Frozen fullimage + fixed illustration ROI, small nested RBF fusion grid."""
import os
for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'):os.environ[key]='1'
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))
from e16_hierarchical import sha, save
import importlib.util,hashlib,json,fcntl,time
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator,TransformerMixin
from sklearn.preprocessing import StandardScaler,normalize
from sklearn.pipeline import Pipeline
from sklearn.svm import SVC
from sklearn.model_selection import GridSearchCV,ParameterGrid,StratifiedKFold
from sklearn.metrics import f1_score,confusion_matrix,classification_report
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'04_hasil_eksperimen/e32_oof'
EMB=ROOT/'04_hasil_eksperimen/e32_crop'
GRID=dict(fusion__e5_weight=[.5,2],fusion__full_weight=[0,1],fusion__crop_weight=[0,1],
          clf__C=[1,10],clf__gamma=[.1,'scale'],clf__class_weight=[None,'balanced'])
digest=lambda x:hashlib.sha256(np.ascontiguousarray(x).tobytes()).hexdigest()

class CropFusion(TransformerMixin,BaseEstimator):
    def __init__(self,e5_weight=.5,full_weight=1,crop_weight=1):
        self.e5_weight=e5_weight;self.full_weight=full_weight;self.crop_weight=crop_weight
    def fit(self,x,y=None):
        assert x.shape[1]==4608
        self.blocks_=[((0,1536),self.e5_weight),((1536,2560),1),((2560,3072),1),((3072,3840),self.full_weight),((3840,4608),self.crop_weight)]
        self.scalers_=[StandardScaler().fit(x[:,a:b]) for (a,b),w in self.blocks_]
        return self
    def transform(self,x):
        out=np.asarray(np.hstack([normalize(s.transform(x[:,a:b]))*w for s,((a,b),w) in zip(self.scalers_,self.blocks_)]),dtype=np.float64)
        assert np.isfinite(out).all();return out
    def metadata(self):
        return [dict(start=a,stop=b,weight=w,mean_sha256=digest(s.mean_),scale_sha256=digest(s.scale_)) for s,((a,b),w) in zip(self.scalers_,self.blocks_)]

def pipeline():return Pipeline([('fusion',CropFusion()),('clf',SVC(kernel='rbf'))])

def fit_metadata(model,x,y):
    c=model.named_steps['clf']
    return dict(fusion=model.named_steps['fusion'].metadata(),classifier=dict(classes=c.classes_.tolist(),
       gamma=float(c._gamma),support_sha256=digest(c.support_),dual_sha256=digest(c.dual_coef_),
       intercept_sha256=digest(c.intercept_),training_decision_sha256=digest(model.decision_function(x))))

def load_inputs():
    loader=ROOT/'01_notebook/e23_siglip2/evaluate.py'
    assert sha(loader)=='de41e071e4dbdbad4cea998bf8ae4816866562e33e1da5f489eefa5b0881ef9c'
    spec=importlib.util.spec_from_file_location('e32_fullimage_loader',loader);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    df,original,y,labels,folds,reference=m.load_inputs()
    verified=json.loads((EMB/'verification.json').read_text());assert verified['status']=='verified' and verified['samples']==740 and verified['dimension']==768
    assert verified['verifier_sha256']==sha(Path(__file__).with_name('verify_features.py'))
    for n,h in verified['sha256'].items():assert sha(EMB/n)==h
    meta=json.loads((EMB/'meta.json').read_text());assert meta['signature']['worker_sha256']==sha(Path(__file__).with_name('extract.py'))
    full_meta=json.loads((ROOT/'04_hasil_eksperimen/e23_siglip2/meta.json').read_text())
    assert meta['signature']['model_snapshot']==full_meta['signature']['model_snapshot']
    assert meta['signature']['crop_fractions']==[.05,.12,.95,.93]
    features=np.load(EMB/'embeddings.npz',allow_pickle=False);assert features['sample_id'].tolist()==df.sample_id.to_list()
    x=np.hstack([original,features['image']]);assert x.shape==(740,4608) and np.isfinite(x).all()
    signature=dict(worker_sha256=sha(Path(__file__)),reference_loader_sha256=sha(loader),reference=reference,
        embedding_verification_sha256=sha(EMB/'verification.json'),embedding_meta_sha256=sha(EMB/'meta.json'),
        features_sha256=digest(x),grid=GRID,outer='Task1 baseline5 seed42',inner='Task2 stratified3 seed42',n_jobs=1)
    return df,x,y,labels,folds,signature


def selected_inner(x, y, train, options):
    scores, metadata = [], []
    splits = list(StratifiedKFold(3, shuffle=True, random_state=42).split(np.zeros(len(train)), y[train]))
    for a, b in splits:
        model = pipeline().set_params(**options).fit(x[train[a]], y[train[a]])
        pred = model.predict(x[train[b]])
        scores.append(float(f1_score(y[train[b]], pred, average='macro', zero_division=0)))
        metadata.append(fit_metadata(model, x[train[a]], y[train[a]]))
    return scores, metadata


def main():
    df, x, y, labels, folds, signature = load_inputs()
    OUT.mkdir(exist_ok=True)
    lock = (OUT / 'run.lock').open('a'); fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    protocol = OUT / 'protocol.json'
    if protocol.exists():
        assert json.loads(protocol.read_text()) == signature
    else:
        save(protocol, signature)
    parameters = list(ParameterGrid(GRID)); assert len(parameters) == 64
    predictions = np.empty(740, object); fold_ids = np.zeros(740, int)
    for k, (train, test) in enumerate(folds, 1):
        checkpoint = OUT / f'fold_{k}.json'
        if checkpoint.exists():
            record = json.loads(checkpoint.read_text())
            assert record['signature'] == signature and record['train_indices'] == train.tolist() and record['test_indices'] == test.tolist()
            assert record['sample_ids'] == df.sample_id.iloc[test].to_list()
        else:
            started = time.monotonic()
            search = GridSearchCV(pipeline(), GRID, scoring='f1_macro', n_jobs=1, error_score='raise',
                                  cv=StratifiedKFold(3, shuffle=True, random_state=42))
            search.fit(x[train], y[train]); best = int(search.best_index_)
            assert search.cv_results_['params'] == parameters
            scores = np.column_stack([search.cv_results_[f'split{j}_test_score'] for j in range(3)])
            assert best == int(np.argmax(scores.mean(axis=1)))
            reproduced, fits = selected_inner(x, y, train, parameters[best])
            assert np.allclose(reproduced, scores[best], rtol=0, atol=1e-12)
            pred = search.predict(x[test])
            record = dict(signature=signature, fold=k, train_indices=train.tolist(), test_indices=test.tolist(),
                          sample_ids=df.sample_id.iloc[test].to_list(), predictions=pred.tolist(),
                          grid_params=parameters, inner_fold_scores=scores.tolist(), best_index=best,
                          best_params=parameters[best], inner_macro_f1=float(search.best_score_),
                          selected_inner_fit=fits, outer_fit=fit_metadata(search.best_estimator_, x[train], y[train]),
                          seconds=time.monotonic() - started)
            save(checkpoint, record)
            print(json.dumps(dict(fold=k, params=parameters[best], inner_macro_f1=record['inner_macro_f1'],
                                  seconds=record['seconds'])), flush=True)
        predictions[test] = record['predictions']; fold_ids[test] = k
    assert set(predictions) <= set(labels)
    pd.DataFrame(dict(sample_id=df.sample_id, truth=y, prediction=predictions, fold=fold_ids)).to_csv(OUT / 'oof.csv', index=False)
    save(OUT / 'metrics.json', dict(samples=740, macro_f1=float(f1_score(y, predictions, average='macro', zero_division=0)),
         confusion_matrix=confusion_matrix(y, predictions, labels=labels).tolist(),
         classification=classification_report(y, predictions, labels=labels, output_dict=True, zero_division=0),
         signature=signature, oof_sha256=sha(OUT / 'oof.csv')))
    print('OOF COMPLETE; independent audit required', flush=True)


if __name__ == '__main__':
    main()
