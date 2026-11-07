"""CI-D01: paired CLIP-L14/IndoBERT training with exact train-only 2x copies."""
import gc
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import random
import time

import numpy as np
import pandas as pd
import torch
from torch import nn
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from sklearn.model_selection import StratifiedKFold

from tail_model import CFG, TailMTL, warm_head, batch_tensors, class_weights
from protocol_utils import TASKS, sha, write, duplicate_train, split_audit, select_epoch


def state_hash(state):
    h=hashlib.sha256()
    for name,value in sorted(state.items()):
        h.update(name.encode());h.update(str(tuple(value.shape)).encode());h.update(str(value.dtype).encode())
        h.update(value.detach().cpu().contiguous().numpy().tobytes())
    return h.hexdigest()


def seed_all():
    random.seed(42);np.random.seed(42);torch.manual_seed(42);torch.cuda.manual_seed_all(42)


def main():
    started=time.monotonic()
    smoke=os.environ.get('CI_D01_SMOKE')=='1'
    here=Path(__file__).resolve().parent
    protocol=json.loads((here/'frozen_protocol.json').read_text())
    build=json.loads((here/'build_manifest.json').read_text())
    for name in ('worker.py','tail_model.py','protocol_utils.py','frozen_protocol.json'):
        assert sha(here/name)==build['payload'][name],name
    out=Path('/kaggle/working/ci_d01_smoke' if smoke else '/kaggle/working/ci_d01_dup2')
    out.mkdir(exist_ok=True)
    matches=list(Path('/kaggle/input').rglob('front_cache.npz'))
    assert len(matches)==1
    cache=matches[0].parent
    assert sha(cache/'cache_manifest.json')==protocol['cache_manifest_sha256']
    manifest=json.loads((cache/'cache_manifest.json').read_text())
    assert manifest['labels_used_for_extraction'] is False
    for name,digest in manifest['files'].items():assert sha(cache/name)==digest,name
    frame=pd.read_csv(cache/'DATASET_740_TASK2_DOMAIN.csv').fillna('')
    z=dict(np.load(cache/'front_cache.npz'))
    assert sha(cache/'DATASET_740_TASK2_DOMAIN.csv')==protocol['dataset_sha256']
    assert len(frame)==740 and frame.sample_id.is_unique and frame.sample_id.tolist()==z['sample_ids'].tolist()
    ids=frame.sample_id.tolist()
    baseline=pd.read_csv(cache/'baseline_oof.csv')
    assert baseline.sample_id.tolist()==ids
    folds=np.asarray([protocol['fold_mapping'][i] for i in ids])
    assert folds.tolist()==baseline.fold.tolist()
    classes={t:sorted(frame[t].unique()) for t in TASKS}
    nc={t:len(classes[t]) for t in TASKS}
    y={t:pd.Categorical(frame[t],categories=classes[t]).codes.astype(np.int64) for t in TASKS}
    CFG.clear();CFG.update(protocol['config'])
    torch.set_num_threads(2)
    assert torch.cuda.is_available()
    torch.backends.cuda.matmul.allow_tf32=False
    torch.backends.cudnn.allow_tf32=False
    runtime=dict(torch=torch.__version__,python=platform.python_version(),
                 transformers=__import__('transformers').__version__,gpu=torch.cuda.get_device_name(0),
                 allocated_gpu_count=torch.cuda.device_count(),used_gpu='cuda:0',
                 canonical_precision='CPU FP32 checkpoint reload',inner_precision='GPU AMP FP16')
    write(out/'runtime.json',runtime)
    def guard():
        if time.monotonic()-started>protocol['wall_seconds_limit']:
            raise RuntimeError('Budget exceeded; partial folds are NOT complete OOF')

    # Verify cached frozen front against the original two-layer IndoBERT tail.
    check=TailMTL(nc,cache).eval()
    with torch.inference_mode():
        for i in (0,147,295,443,591,739):
            value=check.features(*batch_tensors(z,np.array([i]),'cpu')).numpy()[0,-768:]
            assert np.max(np.abs(value-z['base_mean'][i]))<2e-5
    del check

    def reset(train,warm):
        seed_all()
        model=TailMTL(nc,cache)
        model.head.load_state_dict(warm,strict=True)
        initial_hash=state_hash(model.state_dict())
        model.to('cuda:0')
        optimizer=torch.optim.AdamW([{'params':model.tail.parameters(),'lr':CFG['encoder_lr']},
                  {'params':model.head.parameters(),'lr':CFG['head_lr']}],weight_decay=CFG['weight_decay'])
        losses={t:nn.CrossEntropyLoss(weight=class_weights(y[t][train],nc[t]).to('cuda:0')) for t in TASKS}
        return model,optimizer,losses,torch.amp.GradScaler('cuda'),initial_hash

    def train_epoch(model,optimizer,losses,scaler,original_train,forbidden,factor,epoch):
        order=duplicate_train(original_train,forbidden,factor)
        np.random.default_rng(42+epoch).shuffle(order)
        model.train();loss_sum=0.;steps=0;skipped=0
        begin=time.monotonic()
        for off in range(0,len(order),CFG['batch']):
            ix=order[off:off+CFG['batch']]
            optimizer.zero_grad(set_to_none=True)
            with torch.autocast('cuda',dtype=torch.float16):
                pred=model(*batch_tensors(z,ix,'cuda:0'))
                loss=sum(w*losses[t](pred[t],torch.tensor(y[t][ix],device='cuda:0'))
                         for t,w in zip(TASKS,CFG['loss_weights']))/sum(CFG['loss_weights'])
            assert torch.isfinite(loss)
            scaler.scale(loss).backward();scaler.unscale_(optimizer)
            nn.utils.clip_grad_norm_(model.parameters(),1.,error_if_nonfinite=True)
            scale=scaler.get_scale();scaler.step(optimizer);scaler.update()
            skipped+=int(scaler.get_scale()<scale)
            loss_sum+=float(loss.detach())*len(ix);steps+=1;guard()
        assert steps==math.ceil(len(order)/CFG['batch'])
        return dict(epoch=epoch,loss=loss_sum/len(order),batches=steps,optimizer_updates=steps-skipped,
                    skipped_updates=skipped,unique_train_samples=len(original_train),exposures=len(order),
                    seconds=time.monotonic()-begin)

    def predict(model,indices,device,amp):
        model.eval();probabilities={t:[] for t in TASKS}
        with torch.inference_mode():
            for off in range(0,len(indices),CFG['batch']):
                ix=indices[off:off+CFG['batch']]
                if amp:
                    with torch.autocast('cuda',dtype=torch.float16):out=model(*batch_tensors(z,ix,device))
                else:out=model(*batch_tensors(z,ix,device))
                for task in TASKS:
                    assert torch.isfinite(out[task]).all()
                    probabilities[task].extend(out[task].float().softmax(-1).cpu().tolist())
                guard()
        return {t:np.asarray(v) for t,v in probabilities.items()}

    def macro(indices,probabilities):
        return {t:float(f1_score(y[t][indices],probabilities[t].argmax(1),labels=range(nc[t]),average='macro',zero_division=0)) for t in TASKS}

    if smoke:
        train=np.where(folds!=1)[0][:40]
        test=np.where(folds==1)[0][:8]
        warm=warm_head(z,y,nc,train)
        reports={};initial_hashes=[]
        for factor in (1,2):
            model,opt,losses,scaler,initial=reset(train,warm);initial_hashes.append(initial)
            before={name:v.detach().clone() for name,v in model.named_parameters()}
            record=train_epoch(model,opt,losses,scaler,train,test,factor,1)
            changes={prefix:max(float((v-before[name]).abs().max().cpu()) for name,v in model.named_parameters() if name.startswith(prefix))
                     for prefix in ['tail.0.','tail.1.','head.shared.']+[f'head.heads.{t}.' for t in TASKS]}
            assert all(v>0 for v in changes.values())
            assert all(p.grad is None or torch.isfinite(p.grad).all() for p in model.parameters())
            del before,opt,losses,scaler
            model.cpu();before_probs=predict(model,test,'cpu',False)
            cp=out/f'smoke_{factor}x.pt'
            torch.save(model.state_dict(),cp)
            model.load_state_dict(torch.load(cp,map_location='cpu',weights_only=True),strict=True)
            after_probs=predict(model,test,'cpu',False)
            assert all(np.array_equal(before_probs[t],after_probs[t]) for t in TASKS)
            reports[f'{factor}x']=dict(training=record,changes=changes,checkpoint_sha256=sha(cp),
                split=split_audit(ids,train,[],test,factor),cpu_save_reload_identical=True)
            del model;gc.collect();torch.cuda.empty_cache()
        assert initial_hashes[0]==initial_hashes[1]
        write(out/'smoke.json',dict(status='passed',schema='ci-d01-smoke-v1',arms=reports,initial_state_sha256=initial_hashes[0],
             source_sha256=sha(here/'worker.py'),protocol_sha256=sha(here/'frozen_protocol.json'),
             benchmark='Not Evaluated: gradient and persistence smoke only',seconds=time.monotonic()-started))
        print('SMOKE_PASSED',flush=True);return

    all_rows={factor:[] for factor in (1,2)}
    fold_reports=[]
    for fold in range(1,6):
        train=np.where(folds!=fold)[0];test=np.where(folds==fold)[0]
        assert (len(train),len(test))==(592,148)
        inner=[(train[a],train[b]) for a,b in StratifiedKFold(2,shuffle=True,random_state=123).split(train,y[TASKS[1]][train])]
        traces={factor:[] for factor in (1,2)}
        for inner_index,(a,b) in enumerate(inner):
            warm=warm_head(z,y,nc,a);paired=[]
            for factor in (1,2):
                model,opt,losses,scaler,initial=reset(a,warm);paired.append(initial)
                trace=dict(inner=inner_index,split=split_audit(ids,a,b,test,factor),initial_state_sha256=initial,
                           epochs={'0':macro(b,predict(model,b,'cuda:0',True))},training=[])
                for epoch in range(1,max(CFG['epoch_candidates'])+1):
                    record=train_epoch(model,opt,losses,scaler,a,set(b)|set(test),factor,epoch)
                    trace['training'].append(record)
                    if epoch in CFG['epoch_candidates']:
                        trace['epochs'][str(epoch)]=macro(b,predict(model,b,'cuda:0',True))
                    write(out/'progress.json',dict(status='running',fold=fold,phase='inner',inner=inner_index,factor=factor,epoch=epoch))
                traces[factor].append(trace)
                del model,opt,losses,scaler;gc.collect();torch.cuda.empty_cache()
            assert paired[0]==paired[1]
        warm=warm_head(z,y,nc,train);paired=[];arms={}
        for factor in (1,2):
            chosen,scores=select_epoch(traces[factor],CFG['epoch_candidates'])
            model,opt,losses,scaler,initial=reset(train,warm);paired.append(initial)
            history=[]
            for epoch in range(1,chosen+1):
                history.append(train_epoch(model,opt,losses,scaler,train,test,factor,epoch))
                write(out/'progress.json',dict(status='running',fold=fold,phase='refit',factor=factor,epoch=epoch))
            gpu=predict(model,test,'cuda:0',True)
            checkpoint=out/f'fold{fold}_{factor}x.pt'
            torch.save(dict(state_dict={n:v.detach().cpu() for n,v in model.state_dict().items()},classes=classes,
                 config=CFG.copy(),selected_epoch=chosen,factor=factor,train_ids=[ids[i] for i in train],test_ids=[ids[i] for i in test],
                 initial_state_sha256=initial,protocol_sha256=sha(here/'frozen_protocol.json')),checkpoint)
            del model,opt,losses,scaler;gc.collect();torch.cuda.empty_cache()
            # Canonical CPU FP32 FROM THE SAVED CHECKPOINT, not a better-looking GPU score.
            cp=torch.load(checkpoint,map_location='cpu',weights_only=True)
            model=TailMTL(nc,cache);model.load_state_dict(cp['state_dict'],strict=True)
            canonical=predict(model,test,'cpu',False)
            for position,index in enumerate(test):
                row=dict(sample_id=ids[index],fold=fold)
                for t in TASKS:
                    row[t+'_truth']=frame.iloc[index][t]
                    row[t+'_pred']=classes[t][int(canonical[t][position].argmax())]
                    for ci,label in enumerate(classes[t]):row[t+'_p_'+label]=float(canonical[t][position,ci])
                all_rows[factor].append(row)
            arms[str(factor)]=dict(selected_epoch=chosen,epoch_scores=scores,traces=traces[factor],training=history,
                 split=split_audit(ids,train,[],test,factor),initial_state_sha256=initial,checkpoint_sha256=sha(checkpoint),
                 canonical_macro_f1=macro(test,canonical),gpu_cpu_prediction_differences={t:int((gpu[t].argmax(1)!=canonical[t].argmax(1)).sum()) for t in TASKS})
            del model,cp;gc.collect()
        assert paired[0]==paired[1]
        info=dict(fold=fold,arms=arms)
        write(out/f'fold{fold}.json',info);fold_reports.append(info)
        print('FOLD_COMPLETE',fold,{f:arms[str(f)]['canonical_macro_f1'] for f in (1,2)},flush=True)
    metrics={};files={}
    for factor in (1,2):
        predictions=pd.DataFrame(all_rows[factor]).set_index('sample_id').loc[ids].reset_index()
        assert len(predictions)==predictions.sample_id.nunique()==740
        predictions.to_csv(out/f'oof_{factor}x.csv',index=False)
        files[f'oof_{factor}x.csv']=sha(out/f'oof_{factor}x.csv')
        metrics[str(factor)]={}
        for task in TASKS:
            actual=frame[task].tolist();pred=predictions[task+'_pred'].tolist()
            metrics[str(factor)][task]=dict(macro_f1=float(f1_score(actual,pred,labels=classes[task],average='macro',zero_division=0)),
                micro_f1=float(f1_score(actual,pred,average='micro')),accuracy=float(accuracy_score(actual,pred)),
                precision_macro=float(precision_score(actual,pred,labels=classes[task],average='macro',zero_division=0)),
                recall_macro=float(recall_score(actual,pred,labels=classes[task],average='macro',zero_division=0)))
    deltas={t:{m:metrics['2'][t][m]-metrics['1'][t][m] for m in metrics['1'][t]} for t in TASKS}
    result=dict(schema='tempo-ci-d01-result-v1',status='complete',samples=740,unique_original_samples=740,
         protocol_sha256=sha(here/'frozen_protocol.json'),worker_sha256=sha(here/'worker.py'),
         canonical_precision='CPU FP32 checkpoint reload',metrics=metrics,deltas_2x_minus_1x=deltas,
         all_tasks_macro_f1_at_least_0_70={str(f):all(metrics[str(f)][t]['macro_f1']>=.7 for t in TASKS) for f in (1,2)},
         files=files,seconds=time.monotonic()-started,runtime=runtime,classes=classes,
         note='Exact duplication is extra exposure, not 1480 independent samples. Same-epoch comparison is not optimizer-step matched; repeated internal CV, no independent external test.')
    write(out/'result.json',result)
    write(out/'progress.json',dict(status='complete',folds=5))
    print('COMPLETE',json.dumps(result),flush=True)


if __name__=='__main__':main()
