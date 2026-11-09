"""Nested SVC combining frozen semantic and fold-fitted lexical features."""
import os
for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'):
    os.environ[key]='1'
import fcntl
import hashlib
import json
from pathlib import Path
import time
import numpy as np
import pandas as pd
import sklearn
from joblib import Memory
from sklearn.base import BaseEstimator,TransformerMixin
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import f1_score,classification_report,confusion_matrix
from sklearn.model_selection import GridSearchCV,StratifiedKFold
from sklearn.pipeline import Pipeline,FeatureUnion
from sklearn.preprocessing import StandardScaler,normalize
from sklearn.svm import SVC

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'04_hasil_eksperimen/e09_semantic_lexical'

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

class FoldFeatures(BaseEstimator,TransformerMixin):
    def __init__(self,semantic,texts):
        self.semantic=semantic
        self.texts=texts

    def fit(self,indices,y=None):
        ids=np.asarray(indices).ravel()
        self.scale_=StandardScaler().fit(self.semantic[ids])
        self.lexical_=Pipeline([
            ('tfidf',FeatureUnion([
                ('word',TfidfVectorizer(ngram_range=(1,2),min_df=2,
                    sublinear_tf=True,max_features=12000)),
                ('char',TfidfVectorizer(analyzer='char_wb',ngram_range=(3,5),min_df=2,
                    sublinear_tf=True,max_features=24000))])),
            ('svd',TruncatedSVD(n_components=128,n_iter=5,random_state=42))])
        self.lexical_.fit(self.texts[ids])
        return self

    def transform(self,indices):
        ids=np.asarray(indices).ravel()
        semantic=normalize(self.scale_.transform(self.semantic[ids]))
        lexical=normalize(self.lexical_.transform(self.texts[ids]))
        return np.hstack([semantic,lexical])

class BlockWeight(BaseEstimator,TransformerMixin):
    def __init__(self,semantic_dim=1536,lexical_weight=1.0):
        self.semantic_dim=semantic_dim
        self.lexical_weight=lexical_weight

    def fit(self,x,y=None):
        assert x.shape[1]==self.semantic_dim+128
        return self

    def transform(self,x):
        weighted=x.copy()
        weighted[:,self.semantic_dim:]*=self.lexical_weight
        return normalize(weighted)

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    lock=(OUT/'run.lock').open('w')
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    lock.write(str(os.getpid()));lock.flush()
    start=time.monotonic()
    csv=ROOT/'03_data/DATASET_740_TASK2_DOMAIN.csv'
    assert sha(csv)=='cba20f8250bcb59481ed2d3d7d5d42fb8242c96a7ba2d11a2cd02ad80862961a'
    feature=ROOT/'04_hasil_eksperimen/e06_semantic/e06_semantic/embeddings.npz'
    assert sha(feature)=='1f0d2b2f346071fa673701847af39e8a22faf9e6a98195734982cd71e99af374'
    df=pd.read_csv(csv).fillna('');z=np.load(feature,allow_pickle=False)
    assert len(df)==740 and df.sample_id.is_unique and np.array_equal(z['sample_id'],df.sample_id)
    semantic=np.hstack([z['description'],z['source_reason']])
    assert semantic.shape==(740,1536) and np.isfinite(semantic).all()
    run=ROOT/'04_hasil_eksperimen/e01_vlm/kaggle_full/e01_vlm'
    def aligned(name):
        rows=[json.loads(s) for s in (run/name).read_text().splitlines()]
        lookup={r['sample_id']:r for r in rows}
        assert len(rows)==len(lookup)==740 and set(lookup)==set(df.sample_id)
        return [lookup[sid] for sid in df.sample_id]
    desc,pred=aligned('deskripsi.jsonl'),aligned('zeroshot.jsonl')
    meta=json.loads((feature.parent/'meta.json').read_text())
    assert sha(run/'deskripsi.jsonl')==meta['description_sha256']
    assert sha(run/'zeroshot.jsonl')==meta['zeroshot_sha256']
    texts=np.array([' '.join([a['deskripsi'],b.get('sumber_visual') or '',b.get('alasan') or '',
        'DOMAINVLM '+b['domain'],title,support]) for a,b,title,support in
        zip(desc,pred,df.headline_verified,df.supporting_text_verified)])
    y=df.task2_domain_sumber.to_numpy();labels=sorted(set(y))
    issues=pd.Categorical(df.task1_issue,categories=sorted(set(df.task1_issue))).codes
    counts=np.bincount(issues);strat=np.array([i if counts[i]>=5 else -1 for i in issues])
    folds=list(StratifiedKFold(5,shuffle=True,random_state=42).split(np.zeros(740),strat))
    grid={'weight__lexical_weight':[0,0.5,2,8], 'clf__C':[1,10,100],
          'clf__gamma':['scale',1],'clf__class_weight':[None,'balanced']}
    protocol={'hashes':{str(p.relative_to(ROOT)):sha(p) for p in
        (csv,feature,Path(__file__),run/'deskripsi.jsonl',run/'zeroshot.jsonl')},
        'grid':grid,'sklearn':sklearn.__version__,'jobs':1,
        'outer':'baseline integer Task1 stratification5fold seed42',
        'inner':'Task2 stratification3fold seed42; learned transforms fit inside Pipeline',
        'svd_components':128,'semantic':'E5 description + source_reason frozen',
        'text':'E01 description/source/reason/domain + original headline/support'}
    p=OUT/'protocol.json'
    if p.exists():assert json.loads(p.read_text())==protocol,'Protocol mismatch; refusing old checkpoints'
    p.write_text(json.dumps(protocol,indent=2))
    cache=Memory(OUT/'cache',verbose=0)
    predicted=np.empty(740,object);fold_ids=np.zeros(740,int);records=[]
    for k,(tr,te) in enumerate(folds,1):
        assert not set(tr)&set(te)
        fold_ids[te]=k;checkpoint=OUT/f'fold_{k}.json'
        if checkpoint.exists():
            old=json.loads(checkpoint.read_text());assert old['test_indices']==te.tolist()
            predicted[te]=old['predictions'];records.append(old['record']);continue
        pipe=Pipeline([('features',FoldFeatures(semantic,texts)),('weight',BlockWeight()),
                       ('clf',SVC(kernel='rbf',cache_size=200))],memory=cache)
        search=GridSearchCV(pipe,grid,scoring='f1_macro',
            cv=StratifiedKFold(3,shuffle=True,random_state=42),n_jobs=1,error_score='raise')
        search.fit(tr,y[tr]);predicted[te]=search.predict(te)
        record={'fold':k,'inner_macro_f1':float(search.best_score_),
            'macro_f1':float(f1_score(y[te],predicted[te],labels=labels,average='macro',zero_division=0)),
            'params':search.best_params_}
        records.append(record)
        checkpoint.write_text(json.dumps({'test_indices':te.tolist(),
            'predictions':predicted[te].tolist(),'record':record},indent=2))
        print('fold',k,json.dumps(record),flush=True)
        cache.clear(warn=False)
    assert (fold_ids>0).all()
    pd.DataFrame({'sample_id':df.sample_id,'fold':fold_ids,'truth':y,'prediction':predicted}).to_csv(OUT/'oof.csv',index=False)
    report={'macro_f1':float(f1_score(y,predicted,labels=labels,average='macro',zero_division=0)),
        'folds':records,'classification':classification_report(y,predicted,labels=labels,output_dict=True,zero_division=0),
        'confusion_matrix':confusion_matrix(y,predicted,labels=labels).tolist(),'seconds':time.monotonic()-start}
    (OUT/'metrics.json').write_text(json.dumps(report,indent=2))
    print('COMPLETE',report['macro_f1'],flush=True)
    cache.clear(warn=False)

if __name__=='__main__':
    main()
