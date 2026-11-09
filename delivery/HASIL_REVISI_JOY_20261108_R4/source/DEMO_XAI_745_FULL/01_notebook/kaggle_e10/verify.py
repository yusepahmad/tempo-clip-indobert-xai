"""Independently audit the complete E10 OOF evidence (no model weights needed)."""
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedKFold, train_test_split

root, out = map(Path, sys.argv[1:])
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
df = pd.read_csv(root/'03_data/DATASET_740_TASK2_DOMAIN.csv').fillna('')
cfg = json.loads((out/'config.json').read_text())
metrics = json.loads((out/'metrics.json').read_text())
assert not cfg['smoke'] and not metrics['smoke'] and metrics['status']=='complete'
assert cfg['data_sha256']==sha(root/'03_data/DATASET_740_TASK2_DOMAIN.csv')
assert cfg['worker_sha256']==sha(root/'01_notebook/kaggle_e10/worker.py')
assert cfg['revision']=='d128750597153bb5987e10b1c3493a34e5a4502a'
classes=sorted(df.task2_domain_sumber.unique())
y=pd.Categorical(df.task2_domain_sumber,categories=classes).codes
issues=pd.Categorical(df.task1_issue,categories=sorted(df.task1_issue.unique())).codes
counts=np.bincount(issues)
strat=np.array([i if counts[i]>=5 else -1 for i in issues])
rows=pd.read_csv(out/'oof.csv').sort_values('index').reset_index(drop=True)
assert len(rows)==740 and rows.sample_id.is_unique
assert rows['index'].tolist()==list(range(740))
assert rows.sample_id.tolist()==df.sample_id.tolist()
assert rows.truth.tolist()==df.task2_domain_sumber.tolist()
p=rows[['p_'+c for c in classes]].to_numpy()
assert np.isfinite(p).all() and (p>=0).all() and (p<=1).all()
assert np.allclose(p.sum(1),1,atol=1e-5)
assert rows.prediction.tolist()==[classes[i] for i in p.argmax(1)]
history=[json.loads(s) for s in (out/'history.jsonl').read_text().splitlines()]
epochs=[]
for fold,(tr,te) in enumerate(StratifiedKFold(5,shuffle=True,random_state=42).split(np.zeros(740),strat),1):
    report=json.loads((out/f'fold_{fold}.json').read_text())
    assert report==metrics['folds'][fold-1]
    inner,val=train_test_split(tr,test_size=.2,stratify=y[tr],random_state=42+fold)
    for key,expected in [('train_indices',tr),('test_indices',te),('inner_train_indices',inner),('inner_validation_indices',val)]:
        assert report[key]==expected.tolist(),(fold,key)
    assert rows.loc[te,'fold'].tolist()==[fold]*148
    assert all(report['inner_changed'].values()) and all(report['refit_changed'].values())
    h=[r for r in history if r['fold']==fold and r['phase']=='inner']
    best=-1;chosen=1;stale=0
    for epoch,r in enumerate(h,1):
        assert r['epoch']==epoch and np.isfinite(r['loss']) and r['samples']==len(inner)
        score=r['validation_macro_f1']
        if score>best+1e-9:best=score;chosen=epoch;stale=0
        else:stale+=1
        assert stale<3 or epoch==len(h)
    assert chosen==report['selected_epoch'] and (len(h)==12 or stale==3)
    refit=[r for r in history if r['fold']==fold and r['phase']=='refit']
    assert [r['epoch'] for r in refit]==list(range(1,chosen+1))
    assert all(r['samples']==len(tr) and np.isfinite(r['loss']) and r['validation_macro_f1'] is None for r in refit)
    epochs.append(chosen)
scores={}
for c in classes:
    truth=rows.truth.eq(c);pred=rows.prediction.eq(c)
    tp=int((truth&pred).sum());fp=int((~truth&pred).sum());fn=int((truth&~pred).sum())
    scores[c]=2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else 0
score=sum(scores.values())/7
assert abs(score-metrics['macro_f1'])<1e-12
manifest={str(p.relative_to(out)):sha(p) for p in sorted(out.iterdir()) if p.is_file() and p.name!='verification.json'}
result={'status':'verified','samples':740,'macro_f1_manual':score,'per_class_f1':scores,
        'selected_epochs':epochs,'checks':['original data/source hashes','baseline outer folds',
        'exact inner splits and epoch selection','encoder/head changed','finite normalized probabilities',
        'argmax predictions','unique original IDs and labels','manual TP/FP/FN score'], 'sha256':manifest}
(out/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
