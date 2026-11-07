"""Offline GPU FP32 nested shared regional-attention MTL."""
from model import *
import os,json,time,hashlib,gc
from pathlib import Path
from collections import Counter
import pandas as pd
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import f1_score
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    torch.set_num_threads(1);assert torch.cuda.is_available();gpus=torch.cuda.device_count();assert 1<=gpus<=2
    torch.backends.cuda.matmul.allow_tf32=False;torch.backends.cudnn.allow_tf32=False
    smoke=os.environ.get('TEMPO_SMOKE')=='1';start=time.monotonic();limit=240 if smoke else 3600
    package=next(Path('/kaggle/input').rglob('training_features.npz')).parent;manifest=json.loads((package/'manifest.json').read_text());assert sha(package/'manifest.json')==os.environ['TEMPO_PACKAGE_SHA']
    for n,h in manifest['files'].items():assert sha(package/n)==h,n
    z=dict(np.load(package/'training_features.npz'));df=pd.read_csv(package/'DATASET_740_TASK2_DOMAIN.csv').fillna('');assert len(df)==740 and df.sample_id.is_unique and z['sample_ids'].tolist()==df.sample_id.tolist()
    assert z['regions'].shape==(740,32,768) and z['visual'].shape==(740,1536)
    classes={t:sorted(df[t].unique()) for t in TASKS};nc={t:len(classes[t]) for t in TASKS};y={t:df[t].map({c:i for i,c in enumerate(classes[t])}).to_numpy() for t in TASKS}
    configs=grid();out=Path('/kaggle/working/e43_smoke' if smoke else '/kaggle/working/e43_spatial_attention');out.mkdir(exist_ok=True)
    def save(n,v):(out/n).write_text(json.dumps(v,indent=2)+'\n')
    def guard():
        if (time.monotonic()-start)*gpus>limit:raise RuntimeError('GPU budget exceeded; partial CV rejected')
    def metric(ix,p):return {t:float(f1_score(y[t][ix],p[t],labels=range(nc[t]),average='macro',zero_division=0)) for t in TASKS}
    protocol=dict(configs=[asdict(c) for c in configs],classes=classes,package_sha256=sha(package/'manifest.json'),source_sha256=sha(Path(__file__)),model_sha256=sha(Path(__file__).with_name('model.py')),smoke=smoke,allocated_gpu_count=gpus,gpu=torch.cuda.get_device_name(0),gpu_seconds_limit=limit,precision='GPU FP32 TF32off; CPU FP32 canonical all740 checkpoint OOF',outer='baseline5foldTask1rare<5poolseed42',inner='Task2strat2foldseed123; maxminimummeaninnerF1all3;tiesfirstconfig')
    save('protocol.json',protocol);print('START',protocol['gpu'],gpus,flush=True)
    if smoke:
        from dataclasses import replace
        c=replace(configs[1],epochs=2);torch.manual_seed(42);initial=JointMTL(nc,c);before={n:p.clone() for n,p in initial.state_dict().items()};m=fit(z,y,nc,np.arange(64),c,'cuda',guard)
        changes={prefix:max(float((v.cpu()-before[n]).abs().max()) for n,v in m.state_dict().items() if n.startswith(prefix)) for prefix in ['query.','key.','value.','position','shared.']+[f'heads.{t}.' for t in TASKS]}
        assert all(v>0 for v in changes.values());save('smoke.json',dict(status='passed',changes=changes,seconds=time.monotonic()-start));print('SMOKE PASSED',flush=True);return
    counts=Counter(y[TASKS[0]]);strata=[c if counts[c]>=5 else -1 for c in y[TASKS[0]]];folds=list(StratifiedKFold(5,shuffle=True,random_state=42).split(np.arange(740),strata))
    predictions={t:np.full(740,-1,int) for t in TASKS};foldids=np.zeros(740,int);selected=[]
    for k,(tr,te) in enumerate(folds,1):
        inner=[(tr[a],tr[b]) for a,b in StratifiedKFold(2,shuffle=True,random_state=123).split(tr,y[TASKS[1]][tr])];search=[]
        for ci,c in enumerate(configs):
            scores=[]
            for a,b in inner:
                assert not set(a)&set(b) and not (set(a)|set(b))&set(te)
                m=fit(z,y,nc,a,c,'cuda',guard);scores.append(metric(b,predict(m,z,b,'cuda')));del m;gc.collect();torch.cuda.empty_cache()
            search.append(scores);print('FOLD',k,'CONFIG',ci,'inner',scores,flush=True)
        winner=select(search);c=configs[winner];selected.append(winner);m=fit(z,y,nc,tr,c,'cuda',guard);p=predict(m,z,te,'cuda');foldids[te]=k
        for t in TASKS:predictions[t][te]=p[t]
        torch.save(dict(state_dict={n:v.cpu() for n,v in m.state_dict().items()},config=asdict(c),classes=classes,train_indices=tr.tolist(),test_indices=te.tolist(),package_sha256=protocol['package_sha256']),out/f'fold{k}.pt')
        save(f'fold{k}.json',dict(fold=k,train_indices=tr.tolist(),test_indices=te.tolist(),inner=[dict(train=a.tolist(),valid=b.tolist()) for a,b in inner],search=search,winner=winner,checkpoint_sha256=sha(out/f'fold{k}.pt'),gpu_metrics=metric(te,p)))
        del m;gc.collect();torch.cuda.empty_cache();guard()
    baseline=pd.read_csv(package/'baseline_oof.csv');assert baseline.sample_id.tolist()==df.sample_id.tolist() and baseline.fold.tolist()==foldids.tolist()
    rows=[]
    for i,row in df.iterrows():
        d=dict(sample_id=row.sample_id,fold=int(foldids[i]))
        for t in TASKS:
            assert predictions[t][i]>=0 and baseline.iloc[i][t+'_truth']==row[t]
            d[t+'_truth']=row[t];d[t+'_pred']=classes[t][predictions[t][i]];d[t+'_baseline']=baseline.iloc[i][t+'_baseline']
        rows.append(d)
    pd.DataFrame(rows).to_csv(out/'oof_gpu.csv',index=False);scores=metric(np.arange(740),predictions)
    save('gpu_result.json',dict(status='completed_gpu_provisional',metrics=scores,target_reached=all(v>=.7 for v in scores.values()),selected_configs=selected,seconds=time.monotonic()-start,oof_sha256=sha(out/'oof_gpu.csv')));print('FULL COMPLETE',scores,flush=True)
if __name__=='__main__':main()
