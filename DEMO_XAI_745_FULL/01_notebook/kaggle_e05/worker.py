"""Task2-only visual fine-tuning. Outer test never selects epoch."""
import gc
import hashlib
import json
import os
from pathlib import Path
import random
import time
import numpy as np
import pandas as pd
import torch
from sklearn.metrics import classification_report, confusion_matrix, f1_score
from sklearn.model_selection import StratifiedKFold, train_test_split
from torch.utils.data import DataLoader

SMOKE = os.environ.get('TEMPO_E05_SMOKE', '1') == '1'
TASK = 'task2_domain_sumber'
OUT = Path('/kaggle/working/e05_smoke' if SMOKE else '/kaggle/working/e05_full')
OUT.mkdir(exist_ok=True)
torch.set_num_threads(2)
assert torch.cuda.is_available(), 'Kaggle GPU required'
paths = list(Path('/kaggle/input').rglob('DATASET_740_TASK2_DOMAIN.csv'))
assert len(paths) == 1
csv = paths[0]
root = csv.parents[1]
assert hashlib.sha256(csv.read_bytes()).hexdigest() == 'cba20f8250bcb59481ed2d3d7d5d42fb8242c96a7ba2d11a2cd02ad80862961a'
notebook = json.loads((root/'01_notebook/finetune_encoder_colab.ipynb').read_text())
scope = {'torch': torch, 'np': np, 'pd': pd, 'DATA_CSV': csv, 'DIR_GAMBAR': root/'05_gambar'}
for index in (7, 9, 10, 12):
    source = ''.join(notebook['cells'][index]['source'])
    if index == 9:
        source = source.replace('CLIP_PRETRAINED = "laion2b_s34b_b79k"',
            'CLIP_PRETRAINED = ' + repr(str(root/'weights/clip/open_clip_model.safetensors')))
        source = source.replace('INDOBERT = "indobenchmark/indobert-base-p1"',
            'INDOBERT = ' + repr(str(root/'weights/indobert')))
    if index == 12:
        source = source.split('# Uji cepat:')[0]
    exec(compile(source, f'baseline-cell-{index}', 'exec'), scope)
df = scope['df'].fillna('')
y = scope['y'][TASK]
classes = scope['peta'][TASK]
strat = scope['y']['task1_issue']
counts = np.bincount(strat)
strat = np.array([v if counts[v] >= 5 else -1 for v in strat])
Dataset = scope['SampulDataset']
CONFIG = {'smoke': SMOKE, 'seed':42, 'max_epochs':2 if SMOKE else 30,
          'patience':5, 'visual_lr':1e-5, 'head_lr':1e-3, 'batch':8,
          'unfrozen_visual_blocks':2, 'text_encoder':'frozen eval',
          'objective':'weighted CE Task2 only', 'epoch_selection':'inner20percent then reinitialize and refit',
          'data_sha256':hashlib.sha256(csv.read_bytes()).hexdigest(),
          'worker_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
          'notebook_sha256':hashlib.sha256((root/'01_notebook/finetune_encoder_colab.ipynb').read_bytes()).hexdigest(),
          'torch':torch.__version__, 'gpu':torch.cuda.get_device_name(0)}
(OUT/'config.json').write_text(json.dumps(CONFIG,indent=2))

def initialize():
    random.seed(42); np.random.seed(42); torch.manual_seed(42); torch.cuda.manual_seed_all(42)
    m = scope['ModelFineTuned']({TASK:len(classes)})
    # Remove unused CLIP text tower before allocating GPU memory.
    for name in ('transformer','token_embedding','ln_final','positional_embedding','text_projection','logit_scale','logit_bias'):
        if hasattr(m.clip,name): delattr(m.clip,name)
    for p in m.parameters(): p.requires_grad_(False)
    for block in m.clip.visual.transformer.resblocks[-2:]:
        for p in block.parameters(): p.requires_grad_(True)
    for p in m.head.parameters(): p.requires_grad_(True)
    m.cuda()
    visual = [p for p in m.clip.visual.parameters() if p.requires_grad]
    opt = torch.optim.AdamW([{'params':visual,'lr':1e-5},
                            {'params':m.head.parameters(),'lr':1e-3}],weight_decay=1e-4)
    return m, opt

def loader(indices, shuffle=False):
    return DataLoader(Dataset(df,indices),batch_size=8,shuffle=shuffle,num_workers=0,pin_memory=True)

def predict(m, indices):
    m.eval(); outputs=[]
    with torch.no_grad():
        for image,ids,mask,_ in loader(indices):
            with torch.autocast('cuda',dtype=torch.float16):
                z=m(image.cuda(),ids.cuda(),mask.cuda())[TASK]
            assert torch.isfinite(z).all()
            outputs.extend(z.argmax(1).cpu().tolist())
    return np.array(outputs)

def train(m,opt,indices,epochs,fold,phase,validation=None):
    weights=np.bincount(y[indices],minlength=len(classes)).astype('float32')
    weights=torch.tensor(len(indices)/(len(classes)*np.maximum(weights,1)),device='cuda')
    scaler=torch.amp.GradScaler('cuda',init_scale=1024)
    best=-1; best_epoch=1; stale=0
    # Probe high-gradient parameter coordinates to prove actual updates in smoke.
    probes={}; changed={}
    bert_before=next(m.bert.parameters()).detach().flatten()[:32].cpu().clone()
    for epoch in range(1,epochs+1):
        m.train(); m.bert.eval()
        loss_sum=0; steps=0; begin=time.monotonic()
        for image,ids,mask,labels in loader(indices,True):
            opt.zero_grad(set_to_none=True)
            with torch.autocast('cuda',dtype=torch.float16):
                logits=m(image.cuda(),ids.cuda(),mask.cuda())[TASK]
                loss=torch.nn.functional.cross_entropy(logits,labels[TASK].cuda(),weight=weights)
            assert torch.isfinite(loss)
            scaler.scale(loss).backward(); scaler.unscale_(opt)
            assert all(torch.isfinite(p.grad).all() for p in m.parameters() if p.grad is not None)
            if not steps and epoch==1:
                for name,module in [('visual',m.clip.visual),('head',m.head)]:
                    p=next(p for p in module.parameters() if p.grad is not None and p.grad.abs().max()>0)
                    pos=p.grad.abs().flatten().argmax().item()
                    probes[name]=(p,pos,p.detach().flatten()[pos].item())
            torch.nn.utils.clip_grad_norm_([p for p in m.parameters() if p.requires_grad],1.)
            scaler.step(opt); scaler.update()
            for name,(p,pos,before) in probes.items(): changed[name]=p.detach().flatten()[pos].item()!=before
            loss_sum+=loss.item();steps+=1
        score=None
        if validation is not None:
            pred=predict(m,validation)
            score=float(f1_score(y[validation],pred,labels=range(len(classes)),average='macro',zero_division=0))
            if score>best:
                best=score;best_epoch=epoch;stale=0
            else: stale+=1
        record={'fold':fold,'phase':phase,'epoch':epoch,'loss':loss_sum/steps,
                'validation_macro_f1':score,'seconds':time.monotonic()-begin,'changed':changed}
        print(json.dumps(record),flush=True)
        with (OUT/'history.jsonl').open('a') as f:f.write(json.dumps(record)+'\n')
        if validation is not None and stale>=5:break
    assert all(changed.values()), 'Encoder/head weights did not update'
    assert torch.equal(bert_before,next(m.bert.parameters()).detach().flatten()[:32].cpu())
    assert not any(p.requires_grad or p.grad is not None for p in m.bert.parameters())
    return best_epoch

folds=list(StratifiedKFold(5,shuffle=True,random_state=42).split(np.zeros(len(y)),strat))
for fold,(outer_train,outer_test) in enumerate(folds,1):
    if SMOKE and fold>1:break
    destination=OUT/f'fold_{fold}.csv'
    if destination.exists():continue
    inner_train,validation=train_test_split(outer_train,test_size=.2,stratify=y[outer_train],random_state=42)
    if SMOKE:
        inner_train=inner_train[:32];validation=validation[:16]
    assert not set(outer_test)&set(inner_train) and not set(outer_test)&set(validation)
    m,opt=initialize()
    epoch=train(m,opt,inner_train,CONFIG['max_epochs'],fold,'select_epoch',validation)
    del m,opt;gc.collect();torch.cuda.empty_cache()
    m,opt=initialize()
    refit=outer_train[:32] if SMOKE else outer_train
    train(m,opt,refit,epoch,fold,'refit')
    test=outer_test[:16] if SMOKE else outer_test
    pred=predict(m,test)
    torch.save({'state_dict':m.state_dict(),'epoch':epoch,'classes':classes,'config':CONFIG},OUT/f'fold_{fold}.pt')
    if SMOKE:
        payload=torch.load(OUT/f'fold_{fold}.pt',map_location='cpu',weights_only=False)
        m.load_state_dict(payload['state_dict']); del payload
        assert np.array_equal(pred,predict(m,test)), 'Checkpoint eval differs'
    pd.DataFrame({'sample_id':df.sample_id.iloc[test],'index':test,'truth':y[test],
                  'prediction':pred,'fold':fold}).to_csv(destination,index=False)
    (OUT/f'fold_{fold}.json').write_text(json.dumps({'selected_epoch':epoch,'samples':len(test),
           'macro_f1':float(f1_score(y[test],pred,labels=range(len(classes)),average='macro',zero_division=0))},indent=2))
    del m,opt;gc.collect();torch.cuda.empty_cache()
if not SMOKE:
    oof=pd.concat([pd.read_csv(OUT/f'fold_{fold}.csv') for fold in range(1,6)]).sort_values('index')
    assert oof['index'].tolist()==list(range(740)) and oof.sample_id.is_unique
    oof.to_csv(OUT/'oof.csv',index=False)
    report={'macro_f1':float(f1_score(oof.truth,oof.prediction,labels=range(len(classes)),average='macro',zero_division=0)),
            'classes':classes,'classification':classification_report(oof.truth,oof.prediction,output_dict=True,zero_division=0),
            'confusion_matrix':confusion_matrix(oof.truth,oof.prediction,labels=range(len(classes))).tolist()}
    (OUT/'metrics.json').write_text(json.dumps(report,indent=2))
(OUT/'status.json').write_text(json.dumps({'status':'complete','smoke':SMOKE,'folds':1 if SMOKE else 5}))
