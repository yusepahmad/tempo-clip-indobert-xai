"""Canonical full OOF CPU FP32 audit of source/splits/config selection/checkpoints."""
from model import *
from pathlib import Path
from collections import Counter
import sys,json,hashlib
import pandas as pd
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import f1_score,accuracy_score
ROOT=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def normalized(value):return json.loads(json.dumps(value))
def main():
    package,out=map(Path,sys.argv[1:3]);torch.set_num_threads(8)
    manifest=json.loads((package/'manifest.json').read_text());assert manifest['status']=='audited_package'
    for n,h in manifest['files'].items():assert sha(package/n)==h,n
    for n,h in manifest['inputs'].items():assert sha(ROOT/n)==h,n
    protocol=json.loads((out/'protocol.json').read_text());configs=grid();assert not protocol['smoke'] and protocol['configs']==normalized([asdict(c) for c in configs])
    assert protocol['package_sha256']==sha(package/'manifest.json')
    for name,key in [('worker.py','source_sha256'),('model.py','model_sha256')]:assert sha(Path(__file__).with_name(name))==protocol[key]
    df=pd.read_csv(package/'DATASET_740_TASK2_DOMAIN.csv').fillna('');z=dict(np.load(package/'training_features.npz'));assert len(df)==740 and df.sample_id.is_unique and z['sample_ids'].tolist()==df.sample_id.tolist()
    classes={t:sorted(df[t].unique()) for t in TASKS};assert classes==protocol['classes'];nc={t:len(classes[t]) for t in TASKS};y={t:df[t].map({c:i for i,c in enumerate(classes[t])}).to_numpy() for t in TASKS}
    gpu=pd.read_csv(out/'oof_gpu.csv');baseline=pd.read_csv(package/'baseline_oof.csv');result_gpu=json.loads((out/'gpu_result.json').read_text());assert sha(out/'oof_gpu.csv')==result_gpu['oof_sha256']
    assert gpu.sample_id.tolist()==baseline.sample_id.tolist()==df.sample_id.tolist();canonical=gpu.copy();selected=[]
    counts=Counter(y[TASKS[0]]);strata=[c if counts[c]>=5 else -1 for c in y[TASKS[0]]]
    folds=list(StratifiedKFold(5,shuffle=True,random_state=42).split(np.arange(740),strata))
    for k,(tr,te) in enumerate(folds,1):
        info=json.loads((out/f'fold{k}.json').read_text());assert info['train_indices']==tr.tolist() and info['test_indices']==te.tolist()
        inner=[(tr[a],tr[b]) for a,b in StratifiedKFold(2,shuffle=True,random_state=123).split(tr,y[TASKS[1]][tr])]
        assert info['inner']==[dict(train=a.tolist(),valid=b.tolist()) for a,b in inner]
        assert len(info['search'])==len(configs) and all(len(scores)==2 for scores in info['search'])
        assert all(set(row)==set(TASKS) and all(0<=row[t]<=1 for t in TASKS) for scores in info['search'] for row in scores)
        # Independent implementation of max-min scoring and first-config tie rule.
        objectives=[min((scores[0][t]+scores[1][t])/2 for t in TASKS) for scores in info['search']]
        winner=max(range(len(configs)),key=lambda j:objectives[j]);assert winner==info['winner'];selected.append(winner)
        assert sha(out/f'fold{k}.pt')==info['checkpoint_sha256'];cp=torch.load(out/f'fold{k}.pt',map_location='cpu',weights_only=True)
        for key,value in [('classes',classes),('config',asdict(configs[winner])),('train_indices',tr.tolist()),('test_indices',te.tolist()),('package_sha256',protocol['package_sha256'])]:assert normalized(cp[key])==normalized(value),key
        assert all(torch.isfinite(v).all() for v in cp['state_dict'].values());m=JointMTL(nc,configs[winner]);m.load_state_dict(cp['state_dict'],strict=True);m.eval()
        assert gpu.iloc[te]['fold'].tolist()==baseline.iloc[te]['fold'].tolist()==[k]*len(te)
        for off in range(0,len(te),32):
            ix=te[off:off+32];p=predict(m,z,ix)
            for t in TASKS:canonical.loc[ix,t+'_pred']=[classes[t][j] for j in p[t]]
    assert selected==result_gpu['selected_configs'];metrics={};base={};differences={};gpu_scores={}
    for t in TASKS:
        assert gpu[t+'_truth'].tolist()==baseline[t+'_truth'].tolist()==df[t].tolist()
        assert gpu[t+'_baseline'].tolist()==baseline[t+'_baseline'].tolist()
        def metric(pred):return dict(macro_f1=float(f1_score(df[t],pred,labels=classes[t],average='macro',zero_division=0)),accuracy=float(accuracy_score(df[t],pred)))
        metrics[t]=metric(canonical[t+'_pred']);base[t]=metric(baseline[t+'_baseline']);gpu_scores[t]=metric(gpu[t+'_pred'])['macro_f1'];assert abs(gpu_scores[t]-result_gpu['metrics'][t])<1e-12
        differences[t]=int((canonical[t+'_pred']!=gpu[t+'_pred']).sum())
    assert result_gpu['target_reached']==all(v>=.7 for v in gpu_scores.values());canonical.to_csv(out/'oof.csv',index=False)
    result=dict(status='completed_cpu_fp32_canonical',metrics=metrics,baseline=base,selected_configs=selected,minimum_task_macro_f1=min(v['macro_f1'] for v in metrics.values()),target_reached=all(v['macro_f1']>=.7 for v in metrics.values()),gpu_cpu_prediction_differences=differences,oof_sha256=sha(out/'oof.csv'))
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    inputs=dict(manifest['inputs'])
    for p in [package/n for n in manifest['files']]+[package/'manifest.json']+[Path(__file__).with_name(n) for n in ['worker.py','model.py','verify_result.py']]:inputs[str(p.resolve().relative_to(ROOT))]=sha(p)
    report=dict(status='passed',checkpoint_forward_samples=740,selection='structural audit of all recorded inner scores; GPU training not rerun',inputs=inputs,files={p.name:sha(p) for p in out.iterdir() if p.is_file() and p.name not in ['verification.json','root_verification.json']})
    (out/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
