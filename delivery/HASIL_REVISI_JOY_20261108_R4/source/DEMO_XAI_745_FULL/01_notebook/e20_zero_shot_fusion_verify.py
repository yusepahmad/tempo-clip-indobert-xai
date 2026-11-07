"""Recompute selected inner CV and all outer refits, not the entire parameter grid."""
import os
for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'):os.environ[key]='1'
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.metrics import f1_score,confusion_matrix
from sklearn.model_selection import cross_val_score,StratifiedKFold,ParameterGrid
from sklearn.pipeline import Pipeline
from sklearn.svm import SVC
from e20_zero_shot_fusion import ROOT,OUT,GRID,ZeroShotFusion,load_inputs

sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    assert all((OUT/f'fold_{k}.json').exists() for k in range(1,6)), 'Full five-fold outputs required'
    assert (OUT/'oof.csv').exists() and (OUT/'metrics.json').exists()
    df,y,labels,x,folds,fold,signature=load_inputs()
    assert json.loads((OUT/'protocol.json').read_text())==signature
    # Independently derive the categorical block directly from raw hosted answers.
    from parse_v2 import parse_answer
    categories=np.zeros((740,8))
    for i in range(740):
        row=json.loads((ROOT/f'04_hasil_eksperimen/e18_hosted/records/{i:04d}.json').read_text())
        answer=row['response']['choices'][0]['message'].get('content')
        code,_=parse_answer(answer,labels)
        categories[i,ord(code)-65 if code!='INVALID' else 7]=1
    assert np.array_equal(categories,x[:,3072:])
    params=list(ParameterGrid(GRID));assert len(params)==180
    expected=np.empty(740,object);audit=[]
    for k,(train,test) in enumerate(folds,1):
        record=json.loads((OUT/f'fold_{k}.json').read_text())
        assert record['signature']==signature and record['fold']==k
        assert record['train_indices']==train.tolist() and record['test_indices']==test.tolist()
        assert record['sample_ids']==df.sample_id.iloc[test].to_list()
        assert record['grid_params']==params
        scores=np.array(record['grid_scores']);assert scores.shape==(180,) and np.isfinite(scores).all()
        best=int(np.argmax(scores));assert record['best_index']==best and record['best_params']==params[best]
        assert abs(record['inner_macro_f1']-scores[best])<1e-12
        model=Pipeline([('fusion',ZeroShotFusion()),('clf',SVC(kernel='rbf'))]).set_params(**params[best])
        inner=cross_val_score(model,x[train],y[train],cv=StratifiedKFold(3,shuffle=True,random_state=42),
                              scoring='f1_macro',n_jobs=1,error_score='raise')
        assert abs(float(inner.mean())-record['inner_macro_f1'])<1e-12
        model.fit(x[train],y[train]);prediction=model.predict(x[test])
        assert prediction.tolist()==record['predictions'];expected[test]=prediction
        for scaler,(a,b) in zip(model.named_steps['fusion'].scalers_,((0,1536),(1536,2560),(2560,3072))):
            assert np.allclose(scaler.mean_,x[train,a:b].mean(axis=0),rtol=1e-10,atol=1e-12)
        audit.append(dict(fold=k,inner_scores=inner.tolist(),predictions_reproduced=len(test),params=params[best]))
    oof=pd.read_csv(OUT/'oof.csv').fillna('')
    assert len(oof)==740 and oof.sample_id.is_unique
    assert oof.sample_id.to_list()==df.sample_id.to_list() and oof.truth.to_list()==y.tolist()
    assert np.array_equal(oof.fold.to_numpy(),fold) and np.array_equal(oof.prediction.to_numpy(),expected)
    matrix=[[sum(t==a and p==b for t,p in zip(y,expected)) for b in labels] for a in labels]
    per_class=[]
    for j in range(7):
        tp=matrix[j][j];fn=sum(matrix[j])-tp;fp=sum(row[j] for row in matrix)-tp
        per_class.append(2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else 0.0)
    manual=sum(per_class)/7;assert abs(manual-f1_score(y,expected,labels=labels,average='macro',zero_division=0))<1e-12
    assert matrix==confusion_matrix(y,expected,labels=labels).tolist()
    report=json.loads((OUT/'metrics.json').read_text())
    assert report['samples']==740 and report['signature']==signature
    assert abs(manual-report['macro_f1'])<1e-12 and report['confusion_matrix']==matrix
    assert report['oof_sha256']==sha(OUT/'oof.csv')
    for j,label in enumerate(labels):assert abs(report['classification'][label]['f1-score']-per_class[j])<1e-12
    files=[f'fold_{k}.json' for k in range(1,6)]+['protocol.json','metrics.json','oof.csv']
    result=dict(status='verified',samples=740,macro_f1=manual,folds=audit,
                verifier_sha256=sha(Path(__file__)),
                checks=['pinned frozen sources; zero-shot categories independently reconstructed from responses',
                        'original740IDs/labels/baseline outer folds',
                        'grid ordering/argmax and selected inner3 CV reproduced; entire grid not rerun',
                        'train-only scalers and refit5 reproduce all740 predictions',
                        'manual confusion/per-class/macroF1 match report/sklearn'],
                sha256={name:sha(OUT/name) for name in files})
    (OUT/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
