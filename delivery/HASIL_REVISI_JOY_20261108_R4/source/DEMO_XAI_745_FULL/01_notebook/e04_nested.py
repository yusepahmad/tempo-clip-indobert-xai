"""Reproducible nested CV for Task2; run from server learn, no downloads."""
import os
for key in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'):
    os.environ[key] = '1'
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import platform
import time
import numpy as np
import pandas as pd
import sklearn
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline, FeatureUnion
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from sklearn.metrics import classification_report, confusion_matrix, f1_score, accuracy_score
from sklearn.model_selection import GridSearchCV, StratifiedKFold

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = 'cba20f8250bcb59481ed2d3d7d5d42fb8242c96a7ba2d11a2cd02ad80862961a'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def read_rows(path, ids):
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    assert len(rows) == len(ids)
    mapping = {r['sample_id']: r for r in rows}
    assert len(mapping) == len(rows) and set(mapping) == set(ids)
    return [mapping[sid] for sid in ids]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--output', type=Path, default=ROOT / '04_hasil_eksperimen/e04_nested')
    args = ap.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    csv = ROOT / '03_data/DATASET_740_TASK2_DOMAIN.csv'
    assert sha(csv) == EXPECTED
    df = pd.read_csv(csv).fillna('')
    assert len(df) == 740 and df.sample_id.is_unique
    run = ROOT / '04_hasil_eksperimen/e01_vlm/kaggle_full/e01_vlm'
    meta = json.loads((run / 'meta.json').read_text())
    assert meta['data_csv_sha256'] == EXPECTED
    a = read_rows(run / 'deskripsi.jsonl', df.sample_id)
    b = read_rows(run / 'zeroshot.jsonl', df.sample_id)
    y = df.task2_domain_sumber.to_numpy()
    labels = sorted(set(y))
    desc = np.array([r['deskripsi'] for r in a])
    domain = np.array([' DOMAINVLM ' + r['domain'] for r in b])
    source = np.array([r.get('sumber_visual') or '' for r in b])
    reason = np.array([r.get('alasan') or '' for r in b])
    title = (df.headline_verified + ' ' + df.supporting_text_verified).to_numpy()
    variants = {
        'description': desc,
        'description_domain': desc + domain,
        'source_reason': source + ' ' + reason,
        'description_source_reason': desc + ' ' + source + ' ' + reason,
        'all_vlm': desc + ' ' + source + ' ' + reason + domain,
        'all_vlm_original_text': desc + ' ' + source + ' ' + reason + domain + ' ' + title,
    }
    # Match baseline's sorted integer class encoding and rare-class pooling exactly.
    issues = pd.Categorical(df.task1_issue, categories=sorted(set(df.task1_issue))).codes
    counts = Counter(issues)
    strat = np.array([v if counts[v] >= 5 else -1 for v in issues])
    folds = list(StratifiedKFold(5, shuffle=True, random_state=42).split(np.zeros(len(y)), strat))
    fold_id = np.zeros(len(y), dtype=int)
    for k, (tr, te) in enumerate(folds, 1):
        assert not set(tr) & set(te)
        fold_id[te] = k
    assert (fold_id > 0).all()
    hashes = {str(p.relative_to(ROOT)): sha(p) for p in (csv, Path(__file__), run/'meta.json', run/'deskripsi.jsonl', run/'zeroshot.jsonl')}
    protocol = {'data_sha256': EXPECTED, 'hashes': hashes, 'sklearn': sklearn.__version__,
                'python': platform.python_version(), 'labels': labels, 'jobs': 2,
                'split': 'baseline integer Task1 stratification, rare<5 pooled -1, seed42',
                'inner': '3-fold seed42; all preprocessing inside GridSearchCV Pipeline'}
    (args.output/'protocol.json').write_text(json.dumps(protocol, indent=2))
    pd.DataFrame({'sample_id': df.sample_id, 'fold': fold_id}).to_csv(args.output/'folds.csv', index=False)
    for name, texts in variants.items():
        start = time.monotonic()
        result_path = args.output / (name + '.json')
        if result_path.exists():
            print('already complete', name, flush=True)
            continue
        pred = np.empty(len(y), dtype=object)
        details = []
        for k, (tr, te) in enumerate(folds, 1):
            pipeline = Pipeline([
                ('text', FeatureUnion([
                    ('word', TfidfVectorizer(ngram_range=(1,2), min_df=2, sublinear_tf=True)),
                    ('char', TfidfVectorizer(analyzer='char_wb', ngram_range=(3,5), min_df=2, sublinear_tf=True)),
                ])),
                ('clf', LogisticRegression(max_iter=2500)),
            ])
            grid = [
                {'clf': [LogisticRegression(max_iter=2500, solver='liblinear')],
                 'clf__C': [0.3, 3, 30], 'clf__class_weight': [None, 'balanced']},
                {'clf': [LinearSVC(max_iter=5000, random_state=42)],
                 'clf__C': [0.3, 3, 30], 'clf__class_weight': [None, 'balanced']},
            ]
            search = GridSearchCV(pipeline, grid, scoring='f1_macro',
                                  cv=StratifiedKFold(3, shuffle=True, random_state=42),
                                  n_jobs=2, pre_dispatch=2, error_score='raise')
            search.fit(texts[tr], y[tr])
            pred[te] = search.predict(texts[te])
            score = float(f1_score(y[te], pred[te], labels=labels, average='macro', zero_division=0))
            details.append({'fold': k, 'macro_f1': score, 'inner_macro_f1': search.best_score_,
                            'params': {key: str(value) for key,value in search.best_params_.items()}})
            print(name, 'fold', k, 'f1', round(score,4), flush=True)
        report = {'macro_f1': float(f1_score(y,pred,labels=labels,average='macro',zero_division=0)),
                  'accuracy': float(accuracy_score(y,pred)), 'folds': details,
                  'report': classification_report(y,pred,labels=labels,output_dict=True,zero_division=0),
                  'confusion_matrix': confusion_matrix(y,pred,labels=labels).tolist(),
                  'seconds': time.monotonic()-start}
        pd.DataFrame({'sample_id': df.sample_id, 'fold': fold_id, 'truth': y, 'prediction': pred}).to_csv(args.output/(name+'_oof.csv'),index=False)
        result_path.write_text(json.dumps(report,indent=2))
        print('COMPLETE', name, report['macro_f1'], flush=True)
    # Select the feature family using only that fold's inner-CV scores.
    # This is equivalent to searching the union of all family-specific grids.
    selected=[]
    selection=[]
    for k in range(1,6):
        scores={name:json.loads((args.output/(name+'.json')).read_text())['folds'][k-1]['inner_macro_f1'] for name in variants}
        winner=max(scores,key=scores.get)
        rows=pd.read_csv(args.output/(winner+'_oof.csv'))
        selected.append(rows[rows.fold==k])
        selection.append({'fold':k,'family':winner,'inner_macro_f1':scores[winner]})
    joined=pd.concat(selected).set_index('sample_id').loc[df.sample_id].reset_index()
    assert len(joined)==740 and joined.sample_id.is_unique
    joined.to_csv(args.output/'nested_selected_oof.csv',index=False)
    result={'selection':selection,'macro_f1':float(f1_score(joined.truth,joined.prediction,labels=labels,average='macro',zero_division=0)),
            'accuracy':float(accuracy_score(joined.truth,joined.prediction)),
            'classification_report':classification_report(joined.truth,joined.prediction,labels=labels,output_dict=True,zero_division=0),
            'confusion_matrix':confusion_matrix(joined.truth,joined.prediction,labels=labels).tolist()}
    (args.output/'nested_selected.json').write_text(json.dumps(result,indent=2))
    print('COMPLETE NESTED FAMILY SELECTION',result['macro_f1'],flush=True)

if __name__ == '__main__':
    main()
