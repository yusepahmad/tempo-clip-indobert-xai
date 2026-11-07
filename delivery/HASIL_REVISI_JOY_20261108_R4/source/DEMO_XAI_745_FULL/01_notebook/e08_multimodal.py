"""Nested multimodal SVC; every learned transformation stays inside CV."""
import os
for key in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'):
    os.environ[key] = '1'
import fcntl
import hashlib
import json
from pathlib import Path
import time
import numpy as np
import pandas as pd
import scipy.sparse as sp
import sklearn
from joblib import Memory
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import f1_score, classification_report, confusion_matrix
from sklearn.model_selection import GridSearchCV, StratifiedKFold
from sklearn.pipeline import Pipeline, FeatureUnion
from sklearn.preprocessing import normalize
from sklearn.svm import SVC

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'04_hasil_eksperimen/e08_multimodal'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

class Modalities(BaseEstimator, TransformerMixin):
    def __init__(self, visual, bert, texts, family='visual_bert', text_weight=1.0):
        self.visual = visual
        self.bert = bert
        self.texts = texts
        self.family = family
        self.text_weight = text_weight

    def fit(self, indices, y=None):
        if 'text' in self.family:
            self.vectorizer_ = FeatureUnion([
                ('word', TfidfVectorizer(ngram_range=(1,2), min_df=2,
                    sublinear_tf=True, max_features=12000)),
                ('char', TfidfVectorizer(analyzer='char_wb', ngram_range=(3,5),
                    min_df=2, sublinear_tf=True, max_features=24000)),
            ])
            self.vectorizer_.fit(self.texts[np.asarray(indices).ravel()])
        return self

    def transform(self, indices):
        ids = np.asarray(indices).ravel()
        blocks = [sp.csr_matrix(normalize(self.visual[ids]))]
        if 'bert' in self.family:
            blocks.append(sp.csr_matrix(normalize(self.bert[ids])))
        if 'text' in self.family:
            blocks.append(normalize(self.vectorizer_.transform(self.texts[ids])) * self.text_weight)
        return normalize(sp.hstack(blocks, format='csr'))

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    lock = (OUT/'run.lock').open('w')
    fcntl.flock(lock, fcntl.LOCK_EX|fcntl.LOCK_NB)
    lock.write(str(os.getpid())); lock.flush()
    csv = ROOT/'03_data/DATASET_740_TASK2_DOMAIN.csv'
    features = ROOT/'03_data/fitur_clip_indobert_740.npz'
    assert sha(csv) == 'cba20f8250bcb59481ed2d3d7d5d42fb8242c96a7ba2d11a2cd02ad80862961a'
    assert sha(features) == 'd27cd5dbecfffba3a8bbb96037f3181da20f1c95eb246a7d38a4627a90599e5c'
    df = pd.read_csv(csv).fillna('')
    assert len(df) == 740 and df.sample_id.is_unique
    z = np.load(features, allow_pickle=False)
    visual, bert = z['img'], z['txt']
    assert visual.shape[0] == bert.shape[0] == 740
    assert np.isfinite(visual).all() and np.isfinite(bert).all()
    run = ROOT/'04_hasil_eksperimen/e01_vlm/kaggle_full/e01_vlm'
    assert json.loads((run/'meta.json').read_text())['data_csv_sha256'] == sha(csv)
    def aligned(name):
        rows = [json.loads(line) for line in (run/name).read_text().splitlines()]
        lookup = {r['sample_id']:r for r in rows}
        assert len(rows) == len(lookup) == 740 and set(lookup) == set(df.sample_id)
        return [lookup[sid] for sid in df.sample_id]
    descriptions, predictions = aligned('deskripsi.jsonl'), aligned('zeroshot.jsonl')
    texts = np.array([' '.join([a['deskripsi'], b.get('sumber_visual') or '',
        b.get('alasan') or '', 'DOMAINVLM '+b['domain'], title, supporting])
        for a,b,title,supporting in zip(descriptions,predictions,df.headline_verified,df.supporting_text_verified)])
    y = df.task2_domain_sumber.to_numpy(); labels = sorted(set(y))
    issues = pd.Categorical(df.task1_issue, categories=sorted(set(df.task1_issue))).codes
    counts = np.bincount(issues)
    strat = np.array([v if counts[v] >= 5 else -1 for v in issues])
    folds = list(StratifiedKFold(5,shuffle=True,random_state=42).split(np.zeros(740),strat))
    fold_ids = np.zeros(740, int)
    for k,(tr,te) in enumerate(folds,1):
        assert not set(tr)&set(te)
        fold_ids[te] = k
    families = ('visual_bert','visual_text','visual_bert_text')
    hashes = {str(p.relative_to(ROOT)):sha(p) for p in
              (csv,features,Path(__file__),run/'deskripsi.jsonl',run/'zeroshot.jsonl')}
    protocol = {'hashes':hashes,'sklearn':sklearn.__version__,'families':families,
        'outer':'baseline Task1 integer stratification seed42, 5 folds',
        'inner':'3 folds Task2 stratification seed42; TF-IDF inside Pipeline',
        'jobs':1,'grid':{'C':[1,10,100],'gamma':['scale',1],
                        'class_weight':[None,'balanced'],'text_weight':[0.5,2.0]},
        'visual_shape':list(visual.shape),'bert_shape':list(bert.shape)}
    protocol_path = OUT/'protocol.json'
    if protocol_path.exists():
        previous = json.loads(protocol_path.read_text())
        assert previous['hashes'] == hashes, 'Refusing to reuse checkpoints from another data/script version'
        assert previous['sklearn'] == protocol['sklearn']
    protocol_path.write_text(json.dumps(protocol,indent=2))
    cache = Memory(OUT/'cache',verbose=0)
    for family in families:
        result_path = OUT/(family+'.json')
        if result_path.exists():
            print('already complete',family,flush=True); continue
        start = time.monotonic(); pred = np.empty(740,object); records = []
        for k,(tr,te) in enumerate(folds,1):
            checkpoint = OUT/f'{family}_fold{k}.json'
            if checkpoint.exists():
                row = json.loads(checkpoint.read_text())
                assert row['test_indices'] == te.tolist()
                pred[te] = row['predictions']; records.append(row['record']); continue
            pipeline = Pipeline([('features',Modalities(visual,bert,texts,family)),
                                 ('clf',SVC(kernel='rbf',cache_size=200))],memory=cache)
            grid = {'clf__C':[1,10,100], 'clf__gamma':['scale',1],
                    'clf__class_weight':[None,'balanced']}
            if 'text' in family:
                grid['features__text_weight'] = [0.5,2.0]
            search = GridSearchCV(pipeline,grid,scoring='f1_macro',
                cv=StratifiedKFold(3,shuffle=True,random_state=42),
                n_jobs=1,error_score='raise')
            search.fit(tr,y[tr]); pred[te] = search.predict(te)
            row = {'fold':k,'inner_macro_f1':float(search.best_score_),
                'macro_f1':float(f1_score(y[te],pred[te],labels=labels,average='macro',zero_division=0)),
                'params':search.best_params_}
            records.append(row)
            checkpoint.write_text(json.dumps({'test_indices':te.tolist(),
                'predictions':pred[te].tolist(),'record':row},indent=2))
            print(family,'fold',k,json.dumps(row),flush=True)
            cache.clear(warn=False)
        pd.DataFrame({'sample_id':df.sample_id,'fold':fold_ids,'truth':y,'prediction':pred}).to_csv(
            OUT/(family+'_oof.csv'),index=False)
        report = {'macro_f1':float(f1_score(y,pred,labels=labels,average='macro',zero_division=0)),
            'folds':records,'classification':classification_report(y,pred,labels=labels,output_dict=True,zero_division=0),
            'confusion_matrix':confusion_matrix(y,pred,labels=labels).tolist(),
            'seconds':time.monotonic()-start}
        result_path.write_text(json.dumps(report,indent=2))
        print('COMPLETE',family,report['macro_f1'],flush=True)
    selected=[]; choices=[]
    for k in range(1,6):
        scores={family:json.loads((OUT/(family+'.json')).read_text())['folds'][k-1]['inner_macro_f1']
                for family in families}
        best=max(scores,key=scores.get)
        rows=pd.read_csv(OUT/(best+'_oof.csv'))
        selected.append(rows[rows.fold==k]); choices.append({'fold':k,'family':best,'inner_scores':scores})
    oof=pd.concat(selected).set_index('sample_id').loc[df.sample_id].reset_index()
    assert len(oof)==740 and oof.sample_id.is_unique and (oof.fold.to_numpy()==fold_ids).all()
    oof.to_csv(OUT/'nested_selected_oof.csv',index=False)
    result={'macro_f1':float(f1_score(oof.truth,oof.prediction,labels=labels,average='macro',zero_division=0)),
        'selection':choices,'classification':classification_report(oof.truth,oof.prediction,labels=labels,output_dict=True,zero_division=0),
        'confusion_matrix':confusion_matrix(oof.truth,oof.prediction,labels=labels).tolist()}
    (OUT/'nested_selected.json').write_text(json.dumps(result,indent=2))
    print('COMPLETE NESTED',result['macro_f1'],flush=True)
    cache.clear(warn=False)

if __name__ == '__main__':
    main()
