"""Two-view E5 supervised fine-tuning with inner epoch selection and outer refit."""
import os
for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'):
    os.environ[key]='1'
os.environ['HF_HOME']='/kaggle/working/.cache/huggingface'
import gc
import hashlib
import json
from pathlib import Path
import random
import time
import numpy as np
import pandas as pd
import torch
from torch import nn
from torch.utils.data import DataLoader
from sklearn.metrics import f1_score,classification_report,confusion_matrix
from sklearn.model_selection import StratifiedKFold,train_test_split
from transformers import AutoModel,AutoTokenizer

MODEL='intfloat/multilingual-e5-base'
REVISION='d128750597153bb5987e10b1c3493a34e5a4502a'
SMOKE=os.environ.get('E10_SMOKE','1')=='1'
OUT=Path('/kaggle/working/e10_smoke' if SMOKE else '/kaggle/working/e10_full')
OUT.mkdir(exist_ok=True)
MAX_EPOCHS=2 if SMOKE else 12
BATCH=8
MAX_LENGTH=384

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

csvs=list(Path('/kaggle/input').rglob('DATASET_740_TASK2_DOMAIN.csv'));assert len(csvs)==1
csv=csvs[0]
assert sha(csv)=='cba20f8250bcb59481ed2d3d7d5d42fb8242c96a7ba2d11a2cd02ad80862961a'
df=pd.read_csv(csv).fillna('');assert len(df)==740 and df.sample_id.is_unique
files={}
def aligned(name):
    paths=list(Path('/kaggle/input').rglob(name));assert len(paths)==1
    files[name]=paths[0]
    rows=[json.loads(s) for s in paths[0].read_text().splitlines()]
    lookup={r['sample_id']:r for r in rows}
    assert len(rows)==len(lookup)==740 and set(lookup)==set(df.sample_id)
    return [lookup[sid] for sid in df.sample_id]
desc,reason=aligned('deskripsi.jsonl'),aligned('zeroshot.jsonl')
assert sha(files['deskripsi.jsonl'])=='c75e8df3f9b71d6786462f8d0f1187ebe4234fb8dd079924f3f35707ff1b8cd2'
assert sha(files['zeroshot.jsonl'])=='10c07b06b13fbbf647f2b1ed12a722d9bff8f97caa6b621430d8bc0429ab38c9'
views=np.array([['query: '+a['deskripsi'],
    'query: '+(b.get('sumber_visual') or '')+' '+(b.get('alasan') or '')]
    for a,b in zip(desc,reason)])
classes=sorted(set(df.task2_domain_sumber));assert len(classes)==7
y=pd.Categorical(df.task2_domain_sumber,categories=classes).codes.astype(np.int64)
issues=pd.Categorical(df.task1_issue,categories=sorted(set(df.task1_issue))).codes
counts=np.bincount(issues);strat=np.array([i if counts[i]>=5 else -1 for i in issues])
folds=list(StratifiedKFold(5,shuffle=True,random_state=42).split(np.zeros(740),strat))
assert torch.cuda.is_available()
device=torch.device('cuda:0')
tokenizer=AutoTokenizer.from_pretrained(MODEL,revision=REVISION)
config={'model':MODEL,'revision':REVISION,'smoke':SMOKE,'data_sha256':sha(csv),
    'worker_sha256':sha(Path(__file__)),'e01_hashes':{name:sha(p) for name,p in files.items()},
    'views':'E01 description and source+reason; query prefixes; shared encoder',
    'pooling':'attention-mask mean per view, concatenate, LayerNorm, dropout0.1, linear7',
    'trainable':'all encoder and classifier parameters','encoder_lr':2e-5,'head_lr':2e-4,
    'batch':BATCH,'max_length':MAX_LENGTH,'max_epochs':MAX_EPOCHS,'patience':3,
    'epoch_selection':'inner20percent stratified Task2, reinitialize then outer-training refit',
    'amp':'float16','gradient_checkpointing':True,'seed':42,
    'warmup':'10percent steps then constant LR','inner_seed':'42+fold',
    'torch':str(torch.__version__),'gpu':torch.cuda.get_device_name(0)}
(OUT/'config.json').write_text(json.dumps(config,indent=2))

def seed(fold):
    random.seed(42+fold);np.random.seed(42+fold);torch.manual_seed(42+fold)
    torch.cuda.manual_seed_all(42+fold)

class TwoView(nn.Module):
    def __init__(self):
        super().__init__()
        self.encoder=AutoModel.from_pretrained(MODEL,revision=REVISION)
        self.encoder.gradient_checkpointing_enable(gradient_checkpointing_kwargs={'use_reentrant':False})
        hidden=self.encoder.config.hidden_size
        self.classifier=nn.Sequential(nn.LayerNorm(hidden*2),nn.Dropout(0.1),nn.Linear(hidden*2,7))

    def forward(self,**inputs):
        hidden=self.encoder(**inputs).last_hidden_state
        mask=inputs['attention_mask'].unsqueeze(-1).to(hidden.dtype)
        pooled=(hidden*mask).sum(1)/mask.sum(1).clamp_min(1)
        return self.classifier(pooled.reshape(-1,pooled.shape[-1]*2))

def collate(indices):
    indices=np.asarray(indices,dtype=int)
    text=views[indices].reshape(-1).tolist()
    inputs=tokenizer(text,padding=True,truncation=True,max_length=MAX_LENGTH,
        pad_to_multiple_of=8,return_tensors='pt')
    return {k:v.to(device) for k,v in inputs.items()},torch.tensor(y[indices],device=device)

def loader(indices,shuffle=False,fold=0):
    return DataLoader(list(map(int,indices)),batch_size=BATCH,shuffle=shuffle,
        generator=torch.Generator().manual_seed(42+fold),num_workers=0,collate_fn=collate)

def predict(model,indices):
    model.eval();probabilities=[]
    with torch.inference_mode():
        for inputs,_ in loader(indices):
            with torch.autocast('cuda',dtype=torch.float16):logits=model(**inputs)
            assert torch.isfinite(logits).all()
            probabilities.append(logits.float().softmax(-1).cpu().numpy())
    probs=np.concatenate(probabilities)
    assert np.isfinite(probs).all() and np.allclose(probs.sum(1),1,atol=1e-5)
    return probs

def fit(indices,validation,epochs,fold,phase):
    seed(fold)
    model=TwoView().to(device)
    assert all(p.requires_grad for p in model.encoder.parameters())
    probes=[p for n,p in model.encoder.named_parameters()
        if p.ndim==2 and p.shape==(model.encoder.config.hidden_size,)*2 and 'pooler' not in n]
    assert probes
    encoder_probe=probes[-1];before_encoder=encoder_probe.detach().cpu().clone()
    before_head=model.classifier[-1].weight.detach().cpu().clone()
    frequencies=np.bincount(y[indices],minlength=7);assert (frequencies>0).all()
    weight=torch.tensor(len(indices)/(7*frequencies),dtype=torch.float32,device=device)
    criterion=nn.CrossEntropyLoss(weight=weight)
    optimizer=torch.optim.AdamW([{'params':model.encoder.parameters(),'lr':2e-5},
        {'params':model.classifier.parameters(),'lr':2e-4}],weight_decay=0.01)
    scaler=torch.amp.GradScaler('cuda',init_scale=128)
    batches=loader(indices,True,fold)
    warmup=max(1,int(len(batches)*epochs*0.1))
    scheduler=torch.optim.lr_scheduler.LambdaLR(optimizer,lambda step:min((step+1)/warmup,1.0))
    best=-1;chosen=1;stale=0;history=[]
    for epoch in range(1,epochs+1):
        torch.cuda.synchronize();started=time.monotonic();model.train();total=0
        for inputs,targets in batches:
            optimizer.zero_grad(set_to_none=True)
            with torch.autocast('cuda',dtype=torch.float16):logits=model(**inputs)
            loss=criterion(logits.float(),targets)
            assert torch.isfinite(loss)
            scaler.scale(loss).backward();scaler.unscale_(optimizer)
            norm=nn.utils.clip_grad_norm_(model.parameters(),1.0,error_if_nonfinite=True)
            assert torch.isfinite(norm) and encoder_probe.grad is not None
            assert torch.isfinite(encoder_probe.grad).all() and torch.isfinite(model.classifier[-1].weight.grad).all()
            scaler.step(optimizer);scaler.update();scheduler.step()
            total+=float(loss.detach())*len(targets)
        torch.cuda.synchronize();seconds=time.monotonic()-started
        score=None
        if validation is not None:
            score=float(f1_score(y[validation],predict(model,validation).argmax(1),
                labels=list(range(7)),average='macro',zero_division=0))
            if score>best+1e-9:best=score;chosen=epoch;stale=0
            else:stale+=1
        row={'fold':fold,'phase':phase,'epoch':epoch,'loss':total/len(indices),
            'validation_macro_f1':score,'seconds':seconds,'samples':len(indices),
            'peak_cuda_bytes':torch.cuda.max_memory_allocated()}
        history.append(row)
        with (OUT/'history.jsonl').open('a') as f:f.write(json.dumps(row)+'\n')
        print(json.dumps(row),flush=True)
        if validation is not None and stale>=3:break
    changed={'encoder':not torch.equal(before_encoder,encoder_probe.detach().cpu()),
             'head':not torch.equal(before_head,model.classifier[-1].weight.detach().cpu())}
    assert all(changed.values())
    del optimizer,scaler,batches,scheduler
    return model,chosen,{'changed':changed,'history':history}

all_rows=[];fold_reports=[]
for fold,(tr,te) in enumerate(folds,1):
    inner,validation=train_test_split(tr,test_size=0.2,stratify=y[tr],random_state=42+fold)
    assert not set(inner)&set(validation) and not set(tr)&set(te)
    if SMOKE:
        inner,_=train_test_split(inner,train_size=32,stratify=y[inner],random_state=42)
        validation,_=train_test_split(validation,train_size=16,stratify=y[validation],random_state=42)
        tr=np.concatenate([inner,validation]);te=te[:16]
    model,chosen,inner_info=fit(inner,validation,MAX_EPOCHS,fold,'inner')
    del model;gc.collect();torch.cuda.empty_cache()
    model,_,refit_info=fit(tr,None,chosen,fold,'refit')
    probabilities=predict(model,te);predictions=probabilities.argmax(1)
    checkpoint=OUT/f'fold_{fold}.pt'
    torch.save({'state_dict':{k:v.detach().cpu() for k,v in model.state_dict().items()},
        'config':config,'classes':classes,'selected_epoch':chosen},checkpoint)
    reload_matches=None
    if SMOKE:
        del model;gc.collect();torch.cuda.empty_cache()
        model=TwoView().to(device)
        saved=torch.load(checkpoint,map_location='cpu',weights_only=True)
        model.load_state_dict(saved['state_dict']);del saved
        reloaded=predict(model,te)
        assert np.allclose(probabilities,reloaded,atol=1e-5,rtol=1e-5)
        assert np.array_equal(predictions,reloaded.argmax(1));reload_matches=True
    report={'fold':fold,'selected_epoch':chosen,'samples':len(te),
        'train_indices':tr.tolist(),'inner_train_indices':inner.tolist(),
        'inner_validation_indices':validation.tolist(),'test_indices':te.tolist(),
        'macro_f1':float(f1_score(y[te],predictions,labels=list(range(7)),average='macro',zero_division=0)),
        'inner_changed':inner_info['changed'],'refit_changed':refit_info['changed'],
        'checkpoint_reload_matches':reload_matches}
    (OUT/f'fold_{fold}.json').write_text(json.dumps(report,indent=2));fold_reports.append(report)
    for idx,prediction,prob in zip(te,predictions,probabilities):
        all_rows.append({'sample_id':df.sample_id.iloc[idx],'index':int(idx),'fold':fold,
            'truth':classes[y[idx]],'prediction':classes[prediction],
            **{'p_'+label:float(value) for label,value in zip(classes,prob)}})
    pd.DataFrame(all_rows).sort_values('index').to_csv(OUT/'oof.csv',index=False)
    del model;gc.collect();torch.cuda.empty_cache()
    if SMOKE:break
assert len(all_rows)==(16 if SMOKE else 740) and len({r['sample_id'] for r in all_rows})==len(all_rows)
truth=[r['truth'] for r in all_rows];predicted=[r['prediction'] for r in all_rows]
metrics={'status':'complete','smoke':SMOKE,'samples':len(all_rows),'folds':fold_reports,
    'macro_f1':float(f1_score(truth,predicted,labels=classes,average='macro',zero_division=0)),
    'classification':classification_report(truth,predicted,labels=classes,output_dict=True,zero_division=0),
    'confusion_matrix':confusion_matrix(truth,predicted,labels=classes).tolist()}
(OUT/'metrics.json').write_text(json.dumps(metrics,indent=2))
print(json.dumps(metrics),flush=True)
