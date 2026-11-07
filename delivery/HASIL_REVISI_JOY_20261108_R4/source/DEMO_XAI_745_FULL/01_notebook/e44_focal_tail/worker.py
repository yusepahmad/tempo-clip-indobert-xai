"""Offline cached-tail nested fine-tuning; all3task minimum selects epoch."""
from tail_model import *
import os,time,hashlib,platform,gc
from collections import Counter
import pandas as pd
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import f1_score,accuracy_score

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    torch.set_num_threads(1);seed();assert torch.cuda.is_available();gpus=torch.cuda.device_count();assert 1<=gpus<=2
    torch.backends.cuda.matmul.allow_tf32=False;torch.backends.cudnn.allow_tf32=False
    start=time.monotonic();smoke=os.environ.get('TEMPO_SMOKE')=='1';limit=240 if smoke else 3600
    out=Path('/kaggle/working/e44_smoke' if smoke else '/kaggle/working/e44_focal_tail');out.mkdir(exist_ok=True)
    cache=next(Path('/kaggle/input').rglob('front_cache.npz')).parent;manifest=json.loads((cache/'cache_manifest.json').read_text())
    assert sha(cache/'cache_manifest.json')==os.environ['TEMPO_CACHE_MANIFEST_SHA']
    for n,h in manifest['files'].items():assert sha(cache/n)==h,n
    df=pd.read_csv(cache/'DATASET_740_TASK2_DOMAIN.csv').fillna('');z=dict(np.load(cache/'front_cache.npz'));assert len(df)==740 and df.sample_id.is_unique and z['sample_ids'].tolist()==df.sample_id.tolist()
    classes={t:sorted(df[t].unique()) for t in TASKS};nc={t:len(classes[t]) for t in TASKS};y={t:df[t].map({v:i for i,v in enumerate(classes[t])}).to_numpy() for t in TASKS}
    def guard():
        if (time.monotonic()-start)*gpus>limit:raise RuntimeError('GPU budget guard exceeded; no partial CV score accepted')
    def infer(model,indices):
        model.eval();pred={t:[] for t in TASKS}
        with torch.inference_mode(),torch.autocast('cuda',dtype=torch.float16):
            for off in range(0,len(indices),CFG['batch']):
                ix=indices[off:off+CFG['batch']];p=model(*batch_tensors(z,ix,'cuda'))
                for t in TASKS:assert torch.isfinite(p[t]).all();pred[t].extend(p[t].argmax(1).cpu().tolist())
                guard()
        return {t:np.array(v) for t,v in pred.items()}
    def metric(indices,p):return {t:float(f1_score(y[t][indices],p[t],labels=range(nc[t]),average='macro',zero_division=0)) for t in TASKS}
    def reset(tr):
        seed();m=TailMTL(nc,cache);m.head.load_state_dict(warm_head(z,y,nc,tr));m.to('cuda')
        opt=torch.optim.AdamW([{'params':m.tail.parameters(),'lr':CFG['encoder_lr']},{'params':m.head.parameters(),'lr':CFG['head_lr']}],weight_decay=CFG['weight_decay'])
        losses={t:FocalLoss(class_weights(y[t][tr],nc[t]).pow(CFG['class_power']).to('cuda'),CFG['gamma']) for t in TASKS}
        return m,opt,losses,torch.amp.GradScaler('cuda')
    def epoch(m,opt,losses,scaler,tr,e,max_steps=None):
        order=np.array(tr).copy();np.random.default_rng(42+e).shuffle(order);m.train();steps=0
        for off in range(0,len(order),CFG['batch']):
            ix=order[off:off+CFG['batch']];opt.zero_grad(set_to_none=True)
            with torch.autocast('cuda',dtype=torch.float16):
                p=m(*batch_tensors(z,ix,'cuda'));l=sum(w*losses[t](p[t],torch.tensor(y[t][ix],device='cuda')) for t,w in zip(TASKS,CFG['loss_weights']))/sum(CFG['loss_weights'])
            assert torch.isfinite(l);scaler.scale(l).backward();scaler.unscale_(opt);nn.utils.clip_grad_norm_(m.parameters(),1.);scaler.step(opt);scaler.update();steps+=1;guard()
            if max_steps and steps>=max_steps:break
        return float(l.detach().cpu())
    protocol=dict(config=CFG.copy(),configs=CONFIGS,classes=classes,cache_manifest_sha256=sha(cache/'cache_manifest.json'),worker_sha256=sha(Path(__file__)),model_sha256=sha(Path(__file__).with_name('tail_model.py')),smoke=smoke,allocated_gpu_count=gpus,gpu=torch.cuda.get_device_name(0),gpu_seconds_limit=limit,outer='baselineTask1 rare<5 pooled5foldseed42',inner='Task2 stratified2foldseed123; max minimum across-task meaninnerF1; ties earliestepoch',canonical_evaluation='serverCPUFP32 all740checkpointOOF; GPUAMP scores provisional',torch=torch.__version__,python=platform.python_version())
    (out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');print('GPU',protocol['gpu'],'allocated',gpus,flush=True)
    if smoke:
        tr=np.arange(64);m,opt,losses,scaler=reset(tr);before={n:p.detach().clone() for n,p in m.named_parameters()};loss=epoch(m,opt,losses,scaler,tr,1,max_steps=2)
        changes={prefix:max(float((p-before[n]).abs().max().cpu()) for n,p in m.named_parameters() if n.startswith(prefix)) for prefix in ['tail.','head.shared.']+[f'head.heads.{t}.' for t in TASKS]}
        assert all(v>0 for v in changes.values());assert all(p.grad is None or torch.isfinite(p.grad).all() for p in m.parameters())
        report=dict(status='passed',changes=changes,loss=loss,seconds=time.monotonic()-start);(out/'smoke.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True);return
    count=Counter(y[TASKS[0]]);strata=[c if count[c]>=5 else -1 for c in y[TASKS[0]]];folds=list(StratifiedKFold(5,shuffle=True,random_state=42).split(np.arange(740),strata));predictions={t:np.full(740,-1,dtype=int) for t in TASKS};foldids=np.zeros(740,int);selected=[];selected_configs=[]
    for k,(tr,te) in enumerate(folds,1):
        inner=[(tr[a],tr[b]) for a,b in StratifiedKFold(2,shuffle=True,random_state=123).split(tr,y[TARGET][tr])];candidates=[]
        for ci,cfg in enumerate(CONFIGS):
            CFG.clear();CFG.update(cfg);traces=[]
            for j,(a,b) in enumerate(inner):
                assert not set(a)&set(b) and not (set(a)|set(b))&set(te)
                m,opt,losses,scaler=reset(a);trace={0:metric(b,infer(m,b))}
                for e in range(1,max(CFG['epoch_candidates'])+1):
                    epoch(m,opt,losses,scaler,a,e)
                    if e in CFG['epoch_candidates']:trace[e]=metric(b,infer(m,b))
                traces.append(dict(train_indices=a.tolist(),valid_indices=b.tolist(),epochs=trace));del m,opt,losses,scaler;gc.collect();torch.cuda.empty_cache()
            scores={e:min(float(np.mean([trace['epochs'][e][t] for trace in traces])) for t in TASKS) for e in CFG['epoch_candidates']}
            candidates.append(dict(config_index=ci,inner=traces,epoch_scores=scores))
        ci,chosen=select_candidate(candidates)
        CFG.clear();CFG.update(CONFIGS[ci]);selected.append(chosen);selected_configs.append(ci)
        m,opt,losses,scaler=reset(tr)
        for e in range(1,chosen+1):epoch(m,opt,losses,scaler,tr,e)
        p=infer(m,te);foldids[te]=k
        for t in TASKS:predictions[t][te]=p[t]
        cp=dict(state_dict={n:v.detach().cpu() for n,v in m.state_dict().items()},classes=classes,config=CFG.copy(),config_index=ci,train_indices=tr.tolist(),test_indices=te.tolist(),selected_epoch=chosen,cache_manifest_sha256=protocol['cache_manifest_sha256']);torch.save(cp,out/f'fold{k}.pt')
        info=dict(fold=k,train_indices=tr.tolist(),test_indices=te.tolist(),candidates=candidates,selected_config=ci,selected_epoch=chosen,gpu_metrics=metric(te,p),checkpoint_sha256=sha(out/f'fold{k}.pt'))
        (out/f'fold{k}.json').write_text(json.dumps(info,indent=2)+'\n');print('FOLD',k,'epoch',chosen,'alltasks',info['gpu_metrics'],flush=True);del m,opt,losses,scaler;gc.collect();torch.cuda.empty_cache();guard()
    assert all((v>=0).all() for v in predictions.values()) and (foldids>0).all();baseline=pd.read_csv(cache/'baseline_oof.csv');assert baseline.sample_id.tolist()==df.sample_id.tolist() and baseline.fold.tolist()==foldids.tolist()
    rows=[]
    for i,row in df.iterrows():
        d=dict(sample_id=row.sample_id,fold=int(foldids[i]))
        for t in TASKS:assert baseline.iloc[i][t+'_truth']==row[t];d[t+'_truth']=row[t];d[t+'_pred']=classes[t][predictions[t][i]];d[t+'_baseline']=baseline.iloc[i][t+'_baseline']
        rows.append(d)
    pd.DataFrame(rows).to_csv(out/'oof_gpu_amp.csv',index=False);scores=metric(np.arange(740),predictions)
    result=dict(status='completed_gpu_provisional',metrics=scores,selected_epochs=selected,selected_configs=selected_configs,seconds=time.monotonic()-start,target_reached=all(v>=.7 for v in scores.values()),oof_sha256=sha(out/'oof_gpu_amp.csv'))
    (out/'gpu_result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2),flush=True)
if __name__=='__main__':main()
