"""Train-only probability calibration and class biases, evaluated on outer OOF."""
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
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import f1_score,classification_report,confusion_matrix
from sklearn.model_selection import StratifiedKFold,cross_val_predict
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'04_hasil_eksperimen/e11_decision_calibration'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def score(y,p):return float(f1_score(y,p,labels=list(range(7)),average='macro',zero_division=0))

def optimize_bias(y,prob):
    logp=np.log(np.clip(prob,1e-12,1));bias=np.zeros(7)
    best=score(y,logp.argmax(1));initial=best;trace=[]
    for iteration in range(5):
        improved=False
        for label in range(7):
            value=bias[label]
            for candidate_value in np.linspace(-1,1,17):
                candidate=bias.copy();candidate[label]=candidate_value
                candidate_score=score(y,(logp+candidate).argmax(1))
                if candidate_score>best+1e-12:
                    best=candidate_score;value=float(candidate_value);improved=True
            bias[label]=value
        trace.append({'iteration':iteration+1,'training_macro_f1':best,'bias':bias.tolist()})
        if not improved:break
    assert best>=initial and (np.abs(bias)<=1).all()
    return bias,{'raw_training_macro_f1':initial,'adjusted_training_macro_f1':best,'trace':trace}

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    lock=(OUT/'run.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    lock.write(str(os.getpid()));lock.flush();started=time.monotonic()
    csv=ROOT/'03_data/DATASET_740_TASK2_DOMAIN.csv'
    feature=ROOT/'04_hasil_eksperimen/e06_semantic/e06_semantic/embeddings.npz'
    original=ROOT/'03_data/fitur_clip_indobert_740.npz'
    assert sha(csv)=='cba20f8250bcb59481ed2d3d7d5d42fb8242c96a7ba2d11a2cd02ad80862961a'
    assert sha(feature)=='1f0d2b2f346071fa673701847af39e8a22faf9e6a98195734982cd71e99af374'
    assert sha(original)=='d27cd5dbecfffba3a8bbb96037f3181da20f1c95eb246a7d38a4627a90599e5c'
    df=pd.read_csv(csv);z=np.load(feature,allow_pickle=False)
    assert len(df)==740 and df.sample_id.is_unique and np.array_equal(z['sample_id'],df.sample_id)
    classes=sorted(set(df.task2_domain_sumber));assert len(classes)==7
    y=pd.Categorical(df.task2_domain_sumber,categories=classes).codes
    variants={key:z[key] for key in ('description','source_reason','combined')}
    variants['description_reason']=np.hstack([z['description'],z['source_reason']])
    variants['semantic_visual']=np.hstack([z['combined'],np.load(original,allow_pickle=False)['img']])
    assert all(x.shape[0]==740 and np.isfinite(x).all() for x in variants.values())
    evidence=ROOT/'04_hasil_eksperimen/e06_nested'
    paths={name:evidence/(name+'.json') for name in variants}
    reports={name:json.loads(path.read_text()) for name,path in paths.items()}
    issues=pd.Categorical(df.task1_issue,categories=sorted(set(df.task1_issue))).codes
    counts=np.bincount(issues);strat=np.array([i if counts[i]>=5 else -1 for i in issues])
    folds=list(StratifiedKFold(5,shuffle=True,random_state=42).split(np.zeros(740),strat))
    protocol={'hashes':{str(p.relative_to(ROOT)):sha(p) for p in
        (csv,feature,original,Path(__file__),*paths.values())},'sklearn':sklearn.__version__,
        'classes':classes,'jobs':1,'calibration':'sigmoid3fold seed42 ensembleFalse, scaler inside estimator',
        'bias_crossfit':'3fold Task2 seed1042 on outer-training; conditional E06 inner-selected params',
        'bias_grid':np.linspace(-1,1,17).tolist(),'bias_rounds':5,
        'outer':'baseline integer Task1 seed42 5fold','main_output':'adjusted prediction; raw control reported separately'}
    p=OUT/'protocol.json'
    if p.exists():assert json.loads(p.read_text())==protocol,'Protocol mismatch'
    p.write_text(json.dumps(protocol,indent=2))
    pred=np.zeros(740,int);raw=np.zeros(740,int);probs=np.zeros((740,7));fold_ids=np.zeros(740,int);records=[]
    for k,(tr,te) in enumerate(folds,1):
        assert not set(tr)&set(te);fold_ids[te]=k
        checkpoint=OUT/f'fold_{k}.json'
        if checkpoint.exists():
            old=json.loads(checkpoint.read_text());assert old['test_indices']==te.tolist()
            pred[te]=old['prediction'];raw[te]=old['raw_prediction'];probs[te]=old['probabilities']
            records.append(old['record']);continue
        # Only inner selection scores and parameters are read; never outer metrics.
        inner_scores={name:report['folds'][k-1]['inner_macro_f1'] for name,report in reports.items()}
        family=max(inner_scores,key=inner_scores.get);x=variants[family]
        parameters=reports[family]['folds'][k-1]['params'];assert parameters['clf']=='SVC()'
        gamma=parameters['clf__gamma'];gamma=gamma if gamma=='scale' else float(gamma)
        weight=parameters['clf__class_weight'];assert weight in ('None','balanced')
        base=Pipeline([('scale',StandardScaler()),('clf',SVC(C=float(parameters['clf__C']),
            gamma=gamma,class_weight=None if weight=='None' else weight))])
        calibrated=CalibratedClassifierCV(base,method='sigmoid',
            cv=StratifiedKFold(3,shuffle=True,random_state=42),ensemble=False,n_jobs=1)
        crossfit=list(StratifiedKFold(3,shuffle=True,random_state=1042).split(x[tr],y[tr]))
        training_fold=np.zeros(len(tr),int)
        for j,(a,b) in enumerate(crossfit,1):
            assert not set(tr[a])&set(tr[b]) and not set(tr[b])&set(te)
            training_fold[b]=j
        print('START fold',k,'family',family,flush=True)
        training_prob=cross_val_predict(calibrated,x[tr],y[tr],cv=crossfit,
            method='predict_proba',n_jobs=1)
        assert training_prob.shape==(len(tr),7) and np.isfinite(training_prob).all()
        assert np.allclose(training_prob.sum(1),1)
        bias,diagnostic=optimize_bias(y[tr],training_prob)
        pd.DataFrame({'sample_id':df.sample_id.iloc[tr].to_numpy(),'index':tr,
            'training_crossfit_fold':training_fold,'truth':[classes[i] for i in y[tr]],
            **{'p_'+name:training_prob[:,i] for i,name in enumerate(classes)}}).to_csv(
            OUT/f'fold_{k}_train_crossfit.csv',index=False)
        calibrated.fit(x[tr],y[tr]);assert np.array_equal(calibrated.classes_,np.arange(7))
        test_prob=calibrated.predict_proba(x[te])
        assert test_prob.shape==(148,7) and np.isfinite(test_prob).all() and np.allclose(test_prob.sum(1),1)
        probs[te]=test_prob;raw[te]=test_prob.argmax(1)
        pred[te]=(np.log(np.clip(test_prob,1e-12,1))+bias).argmax(1)
        record={'fold':k,'family':family,'inner_family_scores':inner_scores,'base_params':parameters,
            'bias':bias.tolist(),'training_diagnostic':diagnostic,
            'raw_macro_f1':score(y[te],raw[te]),'adjusted_macro_f1':score(y[te],pred[te])}
        records.append(record)
        checkpoint.write_text(json.dumps({'test_indices':te.tolist(),'train_indices':tr.tolist(),
            'prediction':pred[te].tolist(),'raw_prediction':raw[te].tolist(),
            'probabilities':test_prob.tolist(),'record':record},indent=2))
        print('COMPLETE fold',k,'raw',record['raw_macro_f1'],'adjusted',record['adjusted_macro_f1'],flush=True)
    assert (fold_ids>0).all()
    predicted=np.array(classes)[pred];truth=np.array(classes)[y]
    pd.DataFrame({'sample_id':df.sample_id,'fold':fold_ids,'truth':truth,'prediction':predicted,
        'raw_prediction':np.array(classes)[raw],**{'p_'+name:probs[:,i] for i,name in enumerate(classes)}}).to_csv(OUT/'oof.csv',index=False)
    report={'macro_f1':score(y,pred),'raw_macro_f1':score(y,raw),'folds':records,
        'classification':classification_report(truth,predicted,labels=classes,output_dict=True,zero_division=0),
        'confusion_matrix':confusion_matrix(truth,predicted,labels=classes).tolist(),'seconds':time.monotonic()-started}
    (OUT/'metrics.json').write_text(json.dumps(report,indent=2))
    print('COMPLETE OOF',report['macro_f1'],'raw',report['raw_macro_f1'],flush=True)

if __name__=='__main__':main()
