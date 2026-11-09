"""Controlled E42-family tail ablation; fresh private Kaggle jobs only.

The sibling tail_model.py is a byte-identical copy of historical E42 source.
New fixed recipe, independent inner-only epoch selection, same outer IDs.
Canonical evaluation here is GPU FP32 after checkpoint reload, not old E42 CPU.
"""
import os
for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'):os.environ[key]='1'
import gc
import hashlib
import json
from pathlib import Path
import time
import numpy as np
import pandas as pd
import torch
from torch import nn
from sklearn.metrics import f1_score
from sklearn.model_selection import StratifiedKFold
import tail_model as tm

TASKS=tm.TASKS
EPOCHS=(0,2,4,8)
ARMS=('RII_TAIL_MTL_WEIGHTED','RII_TAIL_MTL_UNWEIGHTED','RII_TAIL_SINGLE_TASK',
      'RII_TAIL_IMAGE_ONLY','RII_TAIL_TEXT_SUPPORTING')


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p,d):Path(p).write_text(json.dumps(d,indent=2,allow_nan=False)+'\n')


def main():
    start=time.monotonic();torch.set_num_threads(1)
    smoke=os.environ.get('RII_SMOKE','1')=='1';budget=180 if smoke else 3600
    out=Path('/kaggle/working/revisi_ii_tail_smoke' if smoke else '/kaggle/working/revisi_ii_tail_full');out.mkdir(exist_ok=True)
    assert torch.cuda.is_available()
    torch.backends.cuda.matmul.allow_tf32=False;torch.backends.cudnn.allow_tf32=False
    cache=next(Path('/kaggle/input').rglob('front_cache.npz')).parent
    assert sha(cache/'cache_manifest.json')=='9773684278f995f2d2da4f4c12158568077372270157ca85a0a99a2427829040'
    manifest=json.loads((cache/'cache_manifest.json').read_text())
    for name,h in manifest['files'].items():assert sha(cache/name)==h,name
    df=pd.read_csv(cache/'DATASET_740_TASK2_DOMAIN.csv').fillna('');z=dict(np.load(cache/'front_cache.npz'))
    assert df.sample_id.tolist()==z['sample_ids'].tolist()
    outer=pd.read_csv(cache/'baseline_oof.csv');assert outer.sample_id.tolist()==df.sample_id.tolist()
    labels={t:sorted(df[t].unique()) for t in TASKS};nc={t:len(labels[t]) for t in TASKS}
    y={t:df[t].map({c:i for i,c in enumerate(labels[t])}).to_numpy() for t in TASKS}
    tm.CFG.update(encoder_lr=2e-5,head_lr=3e-4,loss_weights=[1.,2.,2.])

    def guard():
        if time.monotonic()-start>budget:raise RuntimeError('Revisi II wall-time budget exceeded; no partial final CV accepted')

    def fixed_features(indices,arm):
        visual=z['visual'][indices]*2
        text=z['base_mean'][indices]
        if arm=='RII_TAIL_IMAGE_ONLY':text=np.zeros_like(text)
        if arm=='RII_TAIL_TEXT_SUPPORTING':visual=np.zeros_like(visual)
        return np.hstack([visual,text])

    def reset(tr,arm,active):
        tm.seed();m=tm.TailMTL(nc,cache)
        warm=tm.Head(nc)
        opt=torch.optim.AdamW(warm.parameters(),lr=.001,weight_decay=.0001)
        weights={t:tm.class_weights(y[t][tr],nc[t]) if arm!='RII_TAIL_MTL_UNWEIGHTED' else torch.ones(nc[t]) for t in active}
        criteria={t:nn.CrossEntropyLoss(weight=weights[t]) for t in active}
        x=torch.tensor(fixed_features(tr,arm));truth={t:torch.tensor(y[t][tr]) for t in active}
        for _ in range(120):
            opt.zero_grad();p=warm(x);loss=sum(tm.CFG['loss_weights'][TASKS.index(t)]*criteria[t](p[t],truth[t]) for t in active)/sum(tm.CFG['loss_weights'][TASKS.index(t)] for t in active)
            loss.backward();opt.step();guard()
        m.head.load_state_dict(warm.state_dict());del warm,opt
        m.to('cuda')
        if arm=='RII_TAIL_IMAGE_ONLY':
            for p in m.tail.parameters():p.requires_grad=False
        opt=torch.optim.AdamW([{'params':m.tail.parameters(),'lr':2e-5},{'params':m.head.parameters(),'lr':3e-4}],weight_decay=.01)
        criteria={t:nn.CrossEntropyLoss(weight=weights[t].cuda()) for t in active}
        return m,opt,criteria

    def forward(m,ix,arm):
        if arm=='RII_TAIL_IMAGE_ONLY':return m.head(torch.tensor(fixed_features(ix,arm),device='cuda'))
        inputs=list(tm.batch_tensors(z,ix,'cuda'))
        if arm=='RII_TAIL_TEXT_SUPPORTING':inputs[-1]=torch.zeros_like(inputs[-1])
        return m(*inputs)

    def epoch(m,opt,criteria,tr,arm,active,epoch_number):
        m.train();ix=np.array(tr).copy();np.random.default_rng(42+epoch_number).shuffle(ix)
        losses=[]
        for off in range(0,len(ix),32):
            batch=ix[off:off+32];opt.zero_grad(set_to_none=True)
            # Train FP32 too: avoids silent AMP skipped-update confounds.
            p=forward(m,batch,arm)
            loss=sum(tm.CFG['loss_weights'][TASKS.index(t)]*criteria[t](p[t],torch.tensor(y[t][batch],device='cuda')) for t in active)/sum(tm.CFG['loss_weights'][TASKS.index(t)] for t in active)
            assert torch.isfinite(loss);loss.backward();nn.utils.clip_grad_norm_(m.parameters(),1.);opt.step();losses.append(float(loss.detach().cpu()));guard()
        return float(np.mean(losses))

    @torch.inference_mode()
    def predict(m,ix,arm,active):
        m.eval();pred={t:[] for t in active}
        for off in range(0,len(ix),32):
            p=forward(m,ix[off:off+32],arm)
            for t in active:
                assert torch.isfinite(p[t]).all();pred[t].extend(p[t].argmax(1).cpu().tolist())
            guard()
        return {t:np.array(v) for t,v in pred.items()}

    def scores(ix,p,active):return {t:float(f1_score(y[t][ix],p[t],labels=range(nc[t]),average='macro',zero_division=0)) for t in active}

    protocol=dict(schema='revisi-ii-tail-controlled-v1',arms=ARMS,epochs=EPOCHS,seed=42,
                  selection='mean task Macro-F1 across two Task2-stratified inner folds seed123, earliest epoch tie',
                  architecture='E42 CLIP-L14 full/crop + frozen IndoBERT first10 blocks + trainable last2 +shared256+3heads',
                  single_task='3 independent copies, one task loss each, equal architecture and tuning candidates',
                  inputs='headline_verified [SEP] supporting_text_verified; frozen E41 cache',
                  loss='fixed weighted task CE sum / sum(active weights); class weights train-only except unweighted arm',
                  config=dict(tm.CFG),canonical='GPU FP32 reloaded checkpoint; no AMP or test-epoch selection',
                  source_sha256=sha(__file__),tail_model_sha256=sha(Path(tm.__file__)),cache_manifest_sha256=sha(cache/'cache_manifest.json'),
                  dataset_sha256=sha(cache/'DATASET_740_TASK2_DOMAIN.csv'),smoke=smoke,wall_seconds_limit=budget,
                  gpu=torch.cuda.get_device_name(0),allocated_gpu_count=torch.cuda.device_count(),torch=torch.__version__)
    dump(out/'protocol.json',protocol)
    if smoke:
        checks=[]
        for arm in ARMS:
            active=(TASKS[0],) if arm=='RII_TAIL_SINGLE_TASK' else TASKS
            tr=np.arange(32);m,opt,criteria=reset(tr,arm,active)
            before={n:p.detach().clone() for n,p in m.named_parameters()}
            loss=epoch(m,opt,criteria,tr,arm,active,1)
            changes={prefix:max(float((p-before[n]).abs().max().cpu()) for n,p in m.named_parameters() if n.startswith(prefix)) for prefix in ['tail.','head.shared.']+[f'head.heads.{t}.' for t in TASKS]}
            assert changes['head.shared.']>0
            assert changes['tail.']>0 if arm!='RII_TAIL_IMAGE_ONLY' else changes['tail.']==0
            for t in TASKS:assert (changes[f'head.heads.{t}.']>0)==(t in active)
            a=predict(m,tr[:4],arm,active);state={k:v.detach().cpu().clone() for k,v in m.state_dict().items()}
            m.load_state_dict(state);b=predict(m,tr[:4],arm,active)
            assert all(np.array_equal(a[t],b[t]) for t in active)
            checks.append(dict(arm=arm,changes=changes,loss=loss,reload_prediction_identical=True))
            del m,opt,criteria,before,state;gc.collect();torch.cuda.empty_cache()
        dump(out/'smoke.json',dict(status='passed',checks=checks,seconds=time.monotonic()-start));return
    for arm in ARMS:
        folder=out/arm;folder.mkdir(exist_ok=True);oof={t:np.full(740,-1) for t in TASKS};details=[]
        active_groups=[(t,) for t in TASKS] if arm=='RII_TAIL_SINGLE_TASK' else [TASKS]
        for fold in range(1,6):
            tr=np.where(outer.fold.to_numpy()!=fold)[0];te=np.where(outer.fold.to_numpy()==fold)[0]
            inner=[(tr[a],tr[b]) for a,b in StratifiedKFold(2,shuffle=True,random_state=123).split(tr,y[TASKS[1]][tr])]
            assert all(not set(a)&set(b) and not (set(a)|set(b))&set(te) for a,b in inner)
            for active in active_groups:
                traces=[]
                for a,b in inner:
                    m,opt,criteria=reset(a,arm,active);trace={0:scores(b,predict(m,b,arm,active),active)}
                    for epoch_number in range(1,max(EPOCHS)+1):
                        epoch(m,opt,criteria,a,arm,active,epoch_number)
                        if epoch_number in EPOCHS:trace[epoch_number]=scores(b,predict(m,b,arm,active),active)
                    traces.append(trace);del m,opt,criteria;gc.collect();torch.cuda.empty_cache()
                values={epoch_number:float(np.mean([v for trace in traces for v in trace[epoch_number].values()])) for epoch_number in EPOCHS}
                selected=max(EPOCHS,key=lambda ep:(values[ep],-ep))
                m,opt,criteria=reset(tr,arm,active);history=[]
                for epoch_number in range(1,selected+1):history.append(epoch(m,opt,criteria,tr,arm,active,epoch_number))
                pred=predict(m,te,arm,active)
                tag='joint' if len(active)>1 else active[0]
                checkpoint=folder/f'fold{fold}_{tag}.pt'
                state={k:v.detach().cpu().clone() for k,v in m.state_dict().items()}
                torch.save(dict(state_dict=state,labels=labels,selected_epoch=selected,arm=arm,active=active,train_indices=tr.tolist(),test_indices=te.tolist(),protocol_sha256=sha(out/'protocol.json')),checkpoint)
                m.load_state_dict(torch.load(checkpoint,map_location='cpu',weights_only=True)['state_dict'])
                reload=predict(m,te,arm,active);assert all(np.array_equal(pred[t],reload[t]) for t in active)
                for t in active:oof[t][te]=reload[t]
                details.append(dict(fold=fold,active=list(active),inner_scores=values,inner_trace=traces,selected_epoch=selected,
                                    train_indices=tr.tolist(),test_indices=te.tolist(),refit_loss=history,
                                    checkpoint_sha256=sha(checkpoint),reload_identical=True,metrics=scores(te,reload,active)))
                del m,opt,criteria,state;gc.collect();torch.cuda.empty_cache();guard()
                print('COMPLETED',arm,fold,tag,'epoch',selected,'seconds',round(time.monotonic()-start,1),flush=True)
        result=df[['sample_id']].copy();result['fold']=outer.fold
        for t in TASKS:
            assert (oof[t]>=0).all();result[t+'_truth']=df[t];result[t+'_pred']=[labels[t][i] for i in oof[t]]
        result.to_csv(folder/'predictions.csv',index=False)
        dump(folder/'result.json',dict(status='complete',arm=arm,samples=740,folds=details,metrics=scores(np.arange(740),oof,TASKS),
                                     protocol_sha256=sha(out/'protocol.json'),predictions_sha256=sha(folder/'predictions.csv')))
    dump(out/'completion.json',dict(status='complete',arms=ARMS,samples_each=740,seconds=time.monotonic()-start,
                                   protocol_sha256=sha(out/'protocol.json')))
    print('REVISION_II_TAIL_COMPLETE',flush=True)


if __name__=='__main__':main()
