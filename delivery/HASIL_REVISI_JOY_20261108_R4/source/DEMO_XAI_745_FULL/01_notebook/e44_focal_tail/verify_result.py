"""Canonical CPU FP32 checkpoint OOF evaluation, never select precision by score."""
from tail_model import *
import sys,hashlib
from collections import Counter
import pandas as pd
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import f1_score,accuracy_score

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    cache,out=map(Path,sys.argv[1:3]);torch.set_num_threads(8)
    manifest=json.loads((cache/'cache_manifest.json').read_text())
    for n,h in manifest['files'].items():assert sha(cache/n)==h,n
    protocol=json.loads((out/'protocol.json').read_text())
    assert not protocol['smoke'] and protocol['config']==CFG and protocol['configs']==CONFIGS
    assert protocol['cache_manifest_sha256']==sha(cache/'cache_manifest.json')
    for name,key in [('worker.py','worker_sha256'),('tail_model.py','model_sha256')]:assert sha(Path(__file__).with_name(name))==protocol[key]
    df=pd.read_csv(cache/'DATASET_740_TASK2_DOMAIN.csv').fillna('');z=dict(np.load(cache/'front_cache.npz'))
    assert len(df)==740 and df.sample_id.is_unique and z['sample_ids'].tolist()==df.sample_id.tolist()
    classes={t:sorted(df[t].unique()) for t in TASKS};assert classes==protocol['classes'];nc={t:len(classes[t]) for t in TASKS}
    y={t:df[t].map({v:i for i,v in enumerate(classes[t])}).to_numpy() for t in TASKS}
    counts=Counter(y[TASKS[0]]);strata=[c if counts[c]>=5 else -1 for c in y[TASKS[0]]]
    folds=list(StratifiedKFold(5,shuffle=True,random_state=42).split(np.arange(740),strata))
    gpu=pd.read_csv(out/'oof_gpu_amp.csv');base=pd.read_csv(cache/'baseline_oof.csv');result_gpu=json.loads((out/'gpu_result.json').read_text())
    assert sha(out/'oof_gpu_amp.csv')==result_gpu['oof_sha256']
    assert gpu.sample_id.tolist()==base.sample_id.tolist()==df.sample_id.tolist()
    canonical=gpu.copy();selected=[];selected_configs=[]
    for k,(tr,te) in enumerate(folds,1):
        info=json.loads((out/f'fold{k}.json').read_text());assert info['train_indices']==tr.tolist() and info['test_indices']==te.tolist()
        inner=list(StratifiedKFold(2,shuffle=True,random_state=123).split(tr,y[TARGET][tr]))
        assert len(info['candidates'])==len(CONFIGS)
        recomputed=[]
        for ci,candidate in enumerate(info['candidates']):
            assert candidate['config_index']==ci and len(candidate['inner'])==2
            for trace,(a,b) in zip(candidate['inner'],inner):
                assert trace['train_indices']==tr[a].tolist() and trace['valid_indices']==tr[b].tolist()
                assert set(trace['epochs'])==set(map(str,CONFIGS[ci]['epoch_candidates']))
                assert all(0<=trace['epochs'][str(e)][t]<=1 for e in CONFIGS[ci]['epoch_candidates'] for t in TASKS)
            scores={e:min(sum(trace['epochs'][str(e)][t] for trace in candidate['inner'])/2 for t in TASKS) for e in CONFIGS[ci]['epoch_candidates']}
            assert all(abs(scores[e]-candidate['epoch_scores'][str(e)])<1e-12 for e in scores)
            recomputed.append(dict(epoch_scores=scores))
        # Independently implement tie order; do not call worker selection helper.
        ci,chosen=max([(ci,e) for ci in range(len(CONFIGS)) for e in CONFIGS[ci]['epoch_candidates']],key=lambda pair:recomputed[pair[0]]['epoch_scores'][pair[1]])
        assert ci==info['selected_config'] and chosen==info['selected_epoch']
        selected.append(chosen);selected_configs.append(ci);CFG.clear();CFG.update(CONFIGS[ci])
        assert sha(out/f'fold{k}.pt')==info['checkpoint_sha256']
        cp=torch.load(out/f'fold{k}.pt',map_location='cpu',weights_only=True)
        for key,value in [('classes',classes),('config',CFG),('config_index',ci),('train_indices',tr.tolist()),('test_indices',te.tolist()),('selected_epoch',chosen),('cache_manifest_sha256',sha(cache/'cache_manifest.json'))]:assert cp[key]==value,key
        assert all(torch.isfinite(v).all() for v in cp['state_dict'].values())
        model=TailMTL(nc,cache);model.load_state_dict(cp['state_dict'],strict=True);model.eval()
        assert gpu.iloc[te]['fold'].tolist()==[k]*len(te) and base.iloc[te]['fold'].tolist()==[k]*len(te)
        with torch.inference_mode():
            for off in range(0,len(te),32):
                ix=te[off:off+32];p=model(*batch_tensors(z,ix,'cpu'))
                for t in TASKS:
                    assert torch.isfinite(p[t]).all()
                    canonical.loc[ix,t+'_pred']=[classes[t][j] for j in p[t].argmax(1).tolist()]
    assert selected==result_gpu['selected_epochs'] and selected_configs==result_gpu['selected_configs']
    metrics={};baseline={};differences={};gpu_scores={}
    for t in TASKS:
        assert gpu[t+'_truth'].tolist()==base[t+'_truth'].tolist()==df[t].tolist()
        assert gpu[t+'_baseline'].tolist()==base[t+'_baseline'].tolist()
        def metric(pred):return dict(macro_f1=float(f1_score(df[t],pred,labels=classes[t],average='macro',zero_division=0)),accuracy=float(accuracy_score(df[t],pred)))
        metrics[t]=metric(canonical[t+'_pred']);baseline[t]=metric(base[t+'_baseline']);gpu_scores[t]=metric(gpu[t+'_pred'])['macro_f1']
        assert abs(gpu_scores[t]-result_gpu['metrics'][t])<1e-12
        differences[t]=int((canonical[t+'_pred']!=gpu[t+'_pred']).sum())
    assert result_gpu['target_reached']==all(v>=.7 for v in gpu_scores.values())
    canonical.to_csv(out/'oof.csv',index=False)
    result=dict(status='completed_cpu_fp32_canonical',metrics=metrics,baseline=baseline,selected_epochs=selected,selected_configs=selected_configs,target_reached=all(v['macro_f1']>=.7 for v in metrics.values()),minimum_task_macro_f1=min(v['macro_f1'] for v in metrics.values()),gpu_cpu_prediction_differences=differences,oof_sha256=sha(out/'oof.csv'))
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    audit=dict(status='passed',checkpoint_forward_samples=740,precision='CPU FP32 predeclared canonical',selection='structural audit of recorded inner scores; training not rerun',gpu_cpu_prediction_differences=differences,files={p.name:sha(p) for p in out.iterdir() if p.is_file() and p.name not in ['verification.json','root_verification.json']})
    root=Path(__file__).resolve().parents[2]
    inputs=[cache/n for n in manifest['files']]+[cache/'cache_manifest.json']+[Path(__file__).with_name(n) for n in ['worker.py','tail_model.py','verify_result.py']]
    audit['inputs']={str(p.resolve().relative_to(root)):sha(p) for p in inputs}
    (out/'verification.json').write_text(json.dumps(audit,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
