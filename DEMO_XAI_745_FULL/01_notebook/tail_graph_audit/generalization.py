"""Read-only checkpoint inference diagnosis; training scores are not OOF quality."""
import sys,json,hashlib,importlib
from pathlib import Path
import numpy as np,pandas as pd,torch
from sklearn.metrics import f1_score
ROOT=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    source,out=map(Path,sys.argv[1:3]);sys.path.insert(0,str(source));tm=importlib.import_module('tail_model');torch.set_num_threads(8)
    audit=json.loads((out/'verification.json').read_text());assert audit['status']=='passed'
    for n,h in audit['files'].items():assert sha(out/n)==h
    for n,h in audit['inputs'].items():assert sha(ROOT/n)==h
    cache=ROOT/'04_hasil_eksperimen/e41_cached_tail/cache';z=dict(np.load(cache/'front_cache.npz'));df=pd.read_csv(cache/'DATASET_740_TASK2_DOMAIN.csv').fillna('');oof=pd.read_csv(out/'oof.csv');assert oof.sample_id.tolist()==df.sample_id.tolist()==z['sample_ids'].tolist()
    records=[]
    for k in range(1,6):
        cp=torch.load(out/f'fold{k}.pt',map_location='cpu',weights_only=True);info=json.loads((out/f'fold{k}.json').read_text());assert sha(out/f'fold{k}.pt')==info['checkpoint_sha256']
        tr,te=map(np.array,[cp['train_indices'],cp['test_indices']]);assert not set(tr)&set(te) and set(tr)|set(te)==set(range(740))
        classes=cp['classes'];tm.CFG.clear();tm.CFG.update(cp['config']);m=tm.TailMTL({t:len(classes[t]) for t in tm.TASKS},cache);m.load_state_dict(cp['state_dict']);m.eval();pred={t:[] for t in tm.TASKS};confidence={t:[] for t in tm.TASKS}
        with torch.inference_mode():
            for off in range(0,740,32):
                p=m(*tm.batch_tensors(z,np.arange(off,min(off+32,740)),'cpu'))
                for t in tm.TASKS:
                    assert torch.isfinite(p[t]).all();prob=torch.softmax(p[t],dim=1);pred[t].extend([classes[t][i] for i in prob.argmax(1).tolist()]);confidence[t].extend(prob.max(1).values.tolist())
        metrics={}
        for t in tm.TASKS:
            p=np.array(pred[t]);conf=np.array(confidence[t]);assert p[te].tolist()==oof.iloc[te][t+'_pred'].tolist()
            train=float(f1_score(df.iloc[tr][t],p[tr],labels=classes[t],average='macro',zero_division=0));test=float(f1_score(df.iloc[te][t],p[te],labels=classes[t],average='macro',zero_division=0))
            metrics[t]=dict(train_macro_f1=train,heldout_macro_f1=test,gap=train-test,train_mean_max_probability=float(conf[tr].mean()),heldout_mean_max_probability=float(conf[te].mean()))
        records.append(dict(fold=k,checkpoint_sha256=sha(out/f'fold{k}.pt'),metrics=metrics));print('DIAGNOSIS FOLD',k,metrics,flush=True)
    report=dict(status='passed',scope='Train metrics are in-sample diagnostic only; test matches fixed canonical OOF. Mean fold scores are not pooled OOF.',source_sha256=sha(Path(__file__)),folds=records,mean_fold_gap={t:float(np.mean([r['metrics'][t]['gap'] for r in records])) for t in tm.TASKS})
    (out/'generalization_diagnosis.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report['mean_fold_gap'],indent=2))
if __name__=='__main__':main()
