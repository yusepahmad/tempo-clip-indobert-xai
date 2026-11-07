"""Require all five intact protocol-matching QLoRA folds before reporting OOF."""
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.metrics import f1_score,classification_report,confusion_matrix
from sklearn.model_selection import StratifiedKFold,train_test_split

ROOT=Path(__file__).resolve().parents[2]
csv=ROOT/'03_data/DATASET_740_TASK2_DOMAIN.csv'
assert hashlib.sha256(csv.read_bytes()).hexdigest()=='cba20f8250bcb59481ed2d3d7d5d42fb8242c96a7ba2d11a2cd02ad80862961a'
df=pd.read_csv(csv);labels=sorted(set(df.task2_domain_sumber))
issues=pd.Categorical(df.task1_issue,categories=sorted(set(df.task1_issue))).codes
counts=np.bincount(issues);strat=np.array([i if counts[i]>=5 else -1 for i in issues])
folds=list(StratifiedKFold(5,shuffle=True,random_state=42).split(np.zeros(740),strat))
result=ROOT/'04_hasil_eksperimen/e12_qlora';joined=[];config_reference=None;reports=[]
for k,(tr,te) in enumerate(folds,1):
    run=result/f'fold{k}'/f'e12_fold{k}'
    config=json.loads((run/'config.json').read_text());report=json.loads((run/'metrics.json').read_text())
    rows=pd.read_csv(run/'oof.csv')
    assert not config['smoke'] and not report['smoke'] and config['fold']==report['fold']==k
    assert config['classes']==labels and config['data_sha256']==hashlib.sha256(csv.read_bytes()).hexdigest()
    assert config['worker_sha256']==hashlib.sha256((Path(__file__).parent/'worker.py').read_bytes()).hexdigest()
    assert config['revision']=='0c351dd01ed87e9c1b53cbc748cba10e6187ff3b'
    assert config['e01_hashes']=={
        'deskripsi.jsonl':'c75e8df3f9b71d6786462f8d0f1187ebe4234fb8dd079924f3f35707ff1b8cd2',
        'zeroshot.jsonl':'10c07b06b13fbbf647f2b1ed12a722d9bff8f97caa6b621430d8bc0429ab38c9'}
    assert config['input_audit_sha256']==hashlib.sha256((run/'input_audit.jsonl').read_bytes()).hexdigest()
    audit=[json.loads(s) for s in (run/'input_audit.jsonl').read_text().splitlines()]
    assert len(audit)==740 and [r['index'] for r in audit]==list(range(740))
    assert [r['sample_id'] for r in audit]==df.sample_id.tolist()
    assert all(0<r['tokens']<=config['max_input_tokens'] for r in audit)
    invariant={name:value for name,value in config.items() if name not in ('fold',)}
    if config_reference is None:config_reference=invariant
    else:assert config_reference==invariant,'Fold protocol/weights/input mismatch'
    assert len(rows)==148 and rows.sample_id.is_unique and rows['index'].tolist()==te.tolist()
    assert (rows.fold==k).all()
    assert rows.sample_id.tolist()==df.sample_id.iloc[te].tolist() and rows.truth.tolist()==df.task2_domain_sumber.iloc[te].tolist()
    assert report['train_indices']==tr.tolist() and report['test_indices']==te.tolist()
    a,b=set(report['inner_train_indices']),set(report['inner_validation_indices'])
    assert not a&b and a|b==set(tr) and not set(tr)&set(te)
    y=pd.Categorical(df.task2_domain_sumber,categories=labels).codes
    inner,val=train_test_split(tr,test_size=.2,stratify=y[tr],random_state=42+k)
    assert report['inner_train_indices']==inner.tolist() and report['inner_validation_indices']==val.tolist()
    assert 1<=report['selected_epoch']<=config['max_epochs']
    assert all(report['inner_checks'].values()) and all(report['refit_checks'].values())
    history=[json.loads(s) for s in (run/'history.jsonl').read_text().splitlines()]
    assert all(r['fold']==k and r['phase'] in ('inner','refit') for r in history)
    h=[r for r in history if r['phase']=='inner']
    best=-1;chosen=1;stale=0
    for epoch,r in enumerate(h,1):
        assert r['epoch']==epoch and r['samples']==len(inner) and np.isfinite(r['weighted_loss'])
        score=r['validation_macro_f1'];assert np.isfinite(score) and 0<=score<=1
        if score>best+1e-9:best=score;chosen=epoch;stale=0
        else:stale+=1
        assert stale<config['patience'] or epoch==len(h)
    assert 1<=len(h)<=config['max_epochs'] and chosen==report['selected_epoch']
    assert len(h)==config['max_epochs'] or stale==config['patience']
    refit=[r for r in history if r['phase']=='refit']
    assert [r['epoch'] for r in refit]==list(range(1,chosen+1))
    assert all(r['samples']==len(tr) and r['validation_macro_f1'] is None and np.isfinite(r['weighted_loss']) for r in refit)
    probabilities=rows[['p_'+label for label in labels]].to_numpy()
    assert np.isfinite(probabilities).all() and (probabilities>=0).all() and (probabilities<=1).all()
    assert np.allclose(probabilities.sum(1),1,atol=1e-5)
    assert np.array_equal(np.array(labels)[probabilities.argmax(1)],rows.prediction.to_numpy())
    assert abs(f1_score(rows.truth,rows.prediction,labels=labels,average='macro')-report['macro_f1'])<1e-12
    joined.append(rows);reports.append(report)
oof=pd.concat(joined).sort_values('index');assert len(oof)==740 and oof.sample_id.is_unique
assert oof['index'].tolist()==list(range(740)) and oof.sample_id.tolist()==df.sample_id.tolist()
out=result/'aggregate';out.mkdir(exist_ok=True)
oof.to_csv(out/'oof.csv',index=False)
metrics={'samples':740,'macro_f1':float(f1_score(oof.truth,oof.prediction,labels=labels,average='macro',zero_division=0)),
    'classification':classification_report(oof.truth,oof.prediction,labels=labels,output_dict=True,zero_division=0),
    'confusion_matrix':confusion_matrix(oof.truth,oof.prediction,labels=labels).tolist(),
    'folds':reports,'protocol':config_reference}
(out/'metrics.json').write_text(json.dumps(metrics,indent=2))
print('COMPLETE ALL740 OOF',metrics['macro_f1'])
