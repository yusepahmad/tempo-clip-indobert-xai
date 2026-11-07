"""Frozen preregistered nested search; all three tasks remain jointly trained."""
import json,hashlib,time,platform
from dataclasses import asdict
from pathlib import Path
from collections import Counter
import numpy as np
import pandas as pd
import torch,sklearn
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import f1_score,accuracy_score,classification_report,confusion_matrix
from pcgrad_model import TASKS,TARGET,Config,grid,fit,predict,state_hash
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'04_hasil_eksperimen/e35_pcgrad_mtl'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(name,value):(OUT/name).write_text(json.dumps(value,indent=2)+'\n')
def metrics(y,pred,nclasses):
    return {t:dict(macro_f1=float(f1_score(y[t],pred[t],labels=range(nclasses[t]),average='macro',zero_division=0)),accuracy=float(accuracy_score(y[t],pred[t]))) for t in TASKS}
def main():
    torch.set_num_threads(1);OUT.mkdir(parents=True,exist_ok=True)
    assert not (OUT/'result.json').exists(),'Completed experiment must not be overwritten'
    start=time.monotonic();csv=ROOT/'03_data/DATASET_740_TASK2_DOMAIN.csv';features=ROOT/'03_data/fitur_clip_indobert_740.npz'
    release=Path('/home/yusep/workspace/learn/delivery_week34_clip_indobert_20261012/DEMO_XAI_745_FULL/06_models/clip-indobert-mtl-v1/manifest.json')
    manifest=json.loads(release.read_text())
    for p in [csv,features]:assert sha(p)==manifest['data_sha256'][str(p.relative_to(ROOT))]
    df=pd.read_csv(csv).fillna('');z=np.load(features);X=np.hstack([z['img'],z['txt']]).astype(np.float32)
    assert len(df)==740 and df.sample_id.is_unique and X.shape==(740,1280) and np.isfinite(X).all()
    classes={t:sorted(df[t].astype(str).unique()) for t in TASKS};nc={t:len(classes[t]) for t in TASKS}
    y={t:df[t].map({c:i for i,c in enumerate(classes[t])}).to_numpy() for t in TASKS}
    counts=Counter(y[TASKS[0]]);strata=np.array([c if counts[c]>=5 else -1 for c in y[TASKS[0]]])
    folds=list(StratifiedKFold(5,shuffle=True,random_state=42).split(X,strata));configs=grid()
    inputs={str(p.relative_to(ROOT)):sha(p) for p in [csv,features,Path(__file__),Path(__file__).with_name('pcgrad_model.py'),Path(__file__).parent.parent/'e33_joint_mtl/model.py']}
    save('protocol.json',dict(inputs=inputs,grid=[asdict(c) for c in configs],classes=classes,
        outer='5fold Task1 stratification rare<5 pooled seed42, identical baseline',inner='2fold Task2 stratification seed123 on outer train only',
        selection='max mean inner Task2 macro-F1; ties first config',seed=42,torch=torch.__version__,sklearn=sklearn.__version__,python=platform.python_version(),
        excluded_inputs=['source_description','mapping_note','primary_entity','annotator_confidence','Qwen/E5/BGE features'],encoder='frozen CLIP512 + IndoBERT768',
        limitation='Repeated experiments on same corpus; nested CV is not an independent external holdout'))
    predictions={t:np.full(len(df),-1,dtype=int) for t in TASKS};baseline={t:np.full(len(df),-1,dtype=int) for t in TASKS};foldids=np.zeros(len(df),int);details=[]
    for k,(tr,te) in enumerate(folds,1):
        assert not set(tr)&set(te);foldids[te]=k
        inner=[(tr[a],tr[b]) for a,b in StratifiedKFold(2,shuffle=True,random_state=123).split(X[tr],y[TARGET][tr])]
        trace=[]
        for j,c in enumerate(configs):
            scores=[]
            for a,b in inner:
                assert not set(a)&set(b) and not (set(a)|set(b))&set(te)
                m=fit(X,y,nc,a,c);p=predict(m,X[b])[TARGET]
                scores.append(float(f1_score(y[TARGET][b],p,labels=range(nc[TARGET]),average='macro',zero_division=0)))
            trace.append(dict(config_index=j,inner_scores=scores,mean=float(np.mean(scores))))
            if (j+1)%2==0:print('fold',k,'config',j+1,'of',len(configs),'elapsed',round(time.monotonic()-start,1),flush=True)
        winner=max(range(len(configs)),key=lambda j:trace[j]['mean']);chosen=configs[winner]
        m=fit(X,y,nc,tr,chosen);p=predict(m,X[te]);model_digest=state_hash(m)
        torch.save(dict(state_dict=m.state_dict(),config=asdict(chosen),classes=classes,train_indices=tr.tolist(),test_indices=te.tolist(),state_sha256=model_digest,inputs=inputs),OUT/f'fold{k}.pt')
        b=fit(X,y,nc,tr,Config());bp=predict(b,X[te])
        for t in TASKS:predictions[t][te]=p[t];baseline[t][te]=bp[t]
        info=dict(fold=k,train_indices=tr.tolist(),test_indices=te.tolist(),inner_splits=[dict(train=a.tolist(),valid=b.tolist()) for a,b in inner],search=trace,
                  winner=winner,config=asdict(chosen),state_sha256=model_digest,gradient_diagnostics=getattr(m,'pcgrad_diagnostics',None),metrics=metrics({t:y[t][te] for t in TASKS},p,nc),baseline_metrics=metrics({t:y[t][te] for t in TASKS},bp,nc))
        details.append(info);save(f'fold{k}.json',info)
        print('FOLD COMPLETE',k,'winner',winner,'Task2',round(info['metrics'][TARGET]['macro_f1'],4),flush=True)
    assert (foldids>0).all() and all((p>=0).all() for p in predictions.values())
    rows=[]
    for i,row in df.iterrows():
        d=dict(sample_id=row.sample_id,fold=int(foldids[i]))
        for t in TASKS:d[t+'_truth']=row[t];d[t+'_pred']=classes[t][predictions[t][i]];d[t+'_baseline']=classes[t][baseline[t][i]]
        rows.append(d)
    pd.DataFrame(rows).to_csv(OUT/'oof.csv',index=False)
    historical=json.loads((ROOT/'04_hasil_eksperimen/hasil_mtl_740_task2domain.json').read_text())['fusion MTL (CLIP+IndoBERT)']
    result=dict(status='completed',metrics=metrics(y,predictions,nc),baseline=metrics(y,baseline,nc),historical=historical,
                baseline_identical=metrics(y,baseline,nc)==historical,seconds=time.monotonic()-start,selected_configs=[d['winner'] for d in details],
                per_class=classification_report(y[TARGET],predictions[TARGET],labels=range(nc[TARGET]),target_names=classes[TARGET],output_dict=True,zero_division=0),
                confusion=confusion_matrix(y[TARGET],predictions[TARGET],labels=range(nc[TARGET])).tolist(),oof_sha256=sha(OUT/'oof.csv'),
                target_reached=metrics(y,predictions,nc)[TARGET]['macro_f1']>=.7)
    # Labels are only used here for post-hoc diagnostics after OOF predictions are fixed.
    errors=[]
    for i,row in df.iterrows():
        if predictions[TARGET][i]!=y[TARGET][i]:errors.append(dict(sample_id=row.sample_id,fold=int(foldids[i]),truth=row[TARGET],prediction=classes[TARGET][predictions[TARGET][i]],headline=row.headline_verified,supporting=row.supporting_text_verified,annotator_confidence=row.annotator_confidence))
    save('errors.json',errors)
    overlap={}
    for column in ['image_sha256','duplicate_group_id']:
        groups=df[df[column].astype(str)!=''].groupby(column)
        shared=[str(key) for key,group in groups if len(group)>1 and len(set(foldids[group.index]))>1]
        overlap[column]=dict(cross_fold_group_count=len(shared),groups=shared)
    result['duplicate_audit']=overlap
    save('result.json',result);print(json.dumps(result,indent=2),flush=True)
    assert result['baseline_identical'],'Baseline parity failed; candidate not validated'
if __name__=='__main__':main()
