"""Partial two-encoder fine-tuning; epoch selection sees inner labels only."""
import os,sys,json,time,hashlib,gc,random,argparse
from pathlib import Path
from collections import Counter
import numpy as np,pandas as pd,torch
from torch import nn
from sklearn.model_selection import StratifiedKFold,train_test_split
from sklearn.metrics import f1_score,accuracy_score
from PIL import Image
TASKS=('task1_issue','task2_domain_sumber','task3_primary_entity_type');TARGET=TASKS[1]
CFG=dict(hidden=256,dropout=.4,visual_weight=2.,loss_weights=[1.,2.,1.],encoder_lr=2e-6,head_lr=3e-4,weight_decay=1e-4,max_epochs=12,batch=16,seed=42)
class Head(nn.Module):
    def __init__(self,nc):
        super().__init__();self.shared=nn.Sequential(nn.Linear(1280,256),nn.ReLU(),nn.Dropout(.4));self.heads=nn.ModuleDict({t:nn.Linear(256,nc[t]) for t in TASKS})
    def forward(self,x):
        h=self.shared(x);return {t:layer(h) for t,layer in self.heads.items()}
class PartialMTL(nn.Module):
    def __init__(self,nc,root=None):
        super().__init__();import open_clip
        from transformers import AutoModel,AutoTokenizer
        clip_weights=str(root/'weights/clip/open_clip_model.safetensors') if root and (root/'weights/clip/open_clip_model.safetensors').exists() else 'laion2b_s34b_b79k'
        bert_weights=str(root/'weights/indobert') if root and (root/'weights/indobert').exists() else 'indobenchmark/indobert-base-p1'
        clip,_,self.preprocess=open_clip.create_model_and_transforms('ViT-B-32',pretrained=clip_weights)
        self.visual=clip.visual;del clip
        self.bert=AutoModel.from_pretrained(bert_weights);self.tokenizer=AutoTokenizer.from_pretrained(bert_weights)
        self.head=Head(nc)
        for p in list(self.visual.parameters())+list(self.bert.parameters()):p.requires_grad=False
        for block in self.visual.transformer.resblocks[-2:]:
            for p in block.parameters():p.requires_grad=True
        for p in self.visual.ln_post.parameters():p.requires_grad=True
        self.visual.proj.requires_grad=True
        for block in self.bert.encoder.layer[-2:]:
            for p in block.parameters():p.requires_grad=True
    def train(self,mode=True):
        super().train(mode);self.visual.eval();self.bert.eval()
        if mode:
            for block in self.visual.transformer.resblocks[-2:]:block.train()
            for block in self.bert.encoder.layer[-2:]:block.train()
        return self
    def features(self,im,ids,mask):
        v=self.visual(im).float();h=self.bert(input_ids=ids,attention_mask=mask).last_hidden_state[:,0,:].float()
        v=nn.functional.normalize(v,p=2,dim=1);h=nn.functional.normalize(h,p=2,dim=1)
        return torch.cat([v*CFG['visual_weight'],h],dim=1)
    def forward(self,im,ids,mask):return self.head(self.features(im,ids,mask))
def seed():random.seed(42);np.random.seed(42);torch.manual_seed(42)
def cw(y,n):
    c=np.bincount(y,minlength=n).astype(np.float32)
    return torch.tensor(np.where(c>0,len(y)/(np.maximum(c,1)*(c>0).sum()),0.),dtype=torch.float32)
def head_warmstart(X,y,nc,tr):
    seed();h=Head(nc);opt=torch.optim.AdamW(h.parameters(),lr=.001,weight_decay=.0001)
    loss={t:nn.CrossEntropyLoss(weight=cw(y[t][tr],nc[t])) for t in TASKS};xx=torch.tensor(X[tr]);yy={t:torch.tensor(y[t][tr]) for t in TASKS}
    h.train()
    for _ in range(120):
        opt.zero_grad();z=h(xx);l=sum(w*loss[t](z[t],yy[t]) for t,w in zip(TASKS,CFG['loss_weights']))/4;l.backward();opt.step()
    return {k:v.detach().clone() for k,v in h.state_dict().items()}
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--check',action='store_true');args=ap.parse_args();torch.set_num_threads(2);seed()
    if args.check:
        m=PartialMTL(dict(zip(TASKS,[10,7,8])));m.train()
        trainable=[n for n,p in m.named_parameters() if p.requires_grad]
        assert any(n.startswith('visual.') for n in trainable) and any(n.startswith('bert.') for n in trainable)
        assert not any(n.startswith('bert.embeddings.') for n in trainable)
        assert not any(n.startswith('visual.transformer.resblocks.0.') for n in trainable)
        x=torch.randn(2,3,224,224);ids=torch.ones((2,128),dtype=torch.long);mask=torch.ones_like(ids)
        z=m(x,ids,mask);loss=sum(nn.functional.cross_entropy(v,torch.zeros(2,dtype=torch.long)) for v in z.values())/3;loss.backward()
        for prefix in ['visual.transformer.resblocks.11.','bert.encoder.layer.11.','head.shared.','head.heads.task1_issue.','head.heads.task2_domain_sumber.','head.heads.task3_primary_entity_type.']:
            assert any(n.startswith(prefix) and p.grad is not None and p.grad.abs().sum()>0 for n,p in m.named_parameters()),prefix
        for n,p in m.named_parameters():
            if not p.requires_grad:assert p.grad is None,n
        assert all(p.grad is None or torch.isfinite(p.grad).all() for p in m.parameters())
        print('CPU CHECK PASSED: masks, frozen parameters, both encoder gradients, all3 heads/shared gradients, finite loss');return
    assert torch.cuda.is_available(),'Free Kaggle GPU required'
    allocated_gpu_count=torch.cuda.device_count()
    print('ALLOCATED',allocated_gpu_count,[torch.cuda.get_device_name(i) for i in range(allocated_gpu_count)],flush=True)
    assert 1<=allocated_gpu_count<=2,'At most two free GPUs allowed'
    device=torch.device('cuda');start=time.monotonic();smoke=os.environ.get('TEMPO_SMOKE')=='1';OUT=Path('/kaggle/working/e34_smoke' if smoke else '/kaggle/working/e34_partial_mtl');OUT.mkdir(exist_ok=True)
    paths=list(Path('/kaggle/input').rglob('DATASET_740_TASK2_DOMAIN.csv'));assert len(paths)==1;csv=paths[0];root=csv.parents[1]
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    expected=os.environ['TEMPO_EXPECTED_CSV_SHA'];assert sha(csv)==expected,'Dataset hash mismatch'
    df=pd.read_csv(csv).fillna('');assert len(df)==740 and df.sample_id.is_unique
    classes={t:sorted(df[t].astype(str).unique()) for t in TASKS};nc={t:len(classes[t]) for t in TASKS};y={t:df[t].map({c:i for i,c in enumerate(classes[t])}).to_numpy() for t in TASKS}
    m=PartialMTL(nc,root);images=[]
    print('GPU',torch.cuda.get_device_name(0),'count',torch.cuda.device_count(),flush=True)
    for row in df.itertuples():
        files=list((root/'05_gambar').glob(row.sample_id+'.*'));assert len(files)==1
        if row.image_sha256:assert sha(files[0])==row.image_sha256,row.sample_id
        images.append(m.preprocess(Image.open(files[0]).convert('RGB')))
    images=torch.stack(images);texts=[f'{h} [SEP] {s}'.strip() for h,s in zip(df.headline_verified,df.supporting_text_verified)]
    tokens=m.tokenizer(texts,truncation=True,max_length=128,padding='max_length',return_tensors='pt')
    ids=tokens['input_ids'];mask=tokens['attention_mask'];m.to(device).eval()
    def batches(indices,shuffle=False,epoch=0):
        indices=np.array(indices).copy()
        if shuffle:np.random.default_rng(42+epoch).shuffle(indices)
        for off in range(0,len(indices),CFG['batch']):
            ix=indices[off:off+CFG['batch']]
            yield ix,images[ix].to(device),ids[ix].to(device),mask[ix].to(device)
    def infer(model,indices):
        pred={t:[] for t in TASKS};model.eval()
        with torch.inference_mode(),torch.autocast('cuda',dtype=torch.float16):
            for ix,im,ii,mm in batches(indices):
                z=model(im,ii,mm)
                for t in TASKS:assert torch.isfinite(z[t]).all();pred[t].extend(z[t].argmax(1).cpu().tolist())
        return {t:np.array(v) for t,v in pred.items()}
    def timed_guard():
        if (time.monotonic()-start)*allocated_gpu_count>2400:raise RuntimeError('Compute budget guard reached; partial result only')
    base_features=[]
    with torch.inference_mode(),torch.autocast('cuda',dtype=torch.float16):
        for ix,im,ii,mm in batches(np.arange(740)):
            base_features.append(m.features(im,ii,mm).cpu().numpy());timed_guard()
    X=np.vstack(base_features).astype(np.float32)
    base_trainable={k:v.detach().cpu().clone() for k,v in m.state_dict().items() if k in dict(m.named_parameters()) and dict(m.named_parameters())[k].requires_grad}
    def reset(tr):
        seed();m.load_state_dict(base_trainable,strict=False);m.head.load_state_dict(head_warmstart(X,y,nc,tr));m.to(device)
        encoder=[p for n,p in m.named_parameters() if p.requires_grad and not n.startswith('head.')]
        opt=torch.optim.AdamW([{'params':encoder,'lr':CFG['encoder_lr']},{'params':m.head.parameters(),'lr':CFG['head_lr']}],weight_decay=CFG['weight_decay'])
        return opt,torch.amp.GradScaler('cuda',init_scale=1024)
    def train_epoch(tr,opt,scaler,epoch,limit=None):
        m.train();weights={t:cw(y[t][tr],nc[t]).to(device) for t in TASKS};loss_sum=0.;steps=0
        for ix,im,ii,mm in batches(tr,True,epoch):
            timed_guard();opt.zero_grad(set_to_none=True)
            with torch.autocast('cuda',dtype=torch.float16):
                z=m(im,ii,mm);loss=sum(w*nn.functional.cross_entropy(z[t],torch.tensor(y[t][ix],device=device),weight=weights[t]) for t,w in zip(TASKS,CFG['loss_weights']))/4
            assert torch.isfinite(loss);scaler.scale(loss).backward();scaler.unscale_(opt)
            assert all(p.grad is None or torch.isfinite(p.grad).all() for p in m.parameters())
            nn.utils.clip_grad_norm_([p for p in m.parameters() if p.requires_grad],1.);scaler.step(opt);scaler.update();loss_sum+=float(loss);steps+=1
            if limit and steps>=limit:break
        return loss_sum/steps
    counts=Counter(y[TASKS[0]]);strata=[c if counts[c]>=5 else -1 for c in y[TASKS[0]]];folds=list(StratifiedKFold(5,shuffle=True,random_state=42).split(X,strata));oof={t:np.full(740,-1,int) for t in TASKS};foldids=np.zeros(740,int);records=[]
    base_hashes={str(p.relative_to(root)):sha(p) for p in sorted((root/'weights').rglob('*')) if p.is_file() and p.suffix in ('.safetensors','.bin','.json')}
    protocol=dict(config=CFG,csv_sha256=sha(csv),worker_sha256=sha(Path(__file__)),classes=classes,base_weights=base_hashes,trainable=list(base_trainable),encoder='CLIP ViT-B32 laion2b_s34b_b79k and IndoBERTbasep1; last2blocks only',gpu=torch.cuda.get_device_name(0),allocated_gpu_count=allocated_gpu_count,quota_gpu_minutes_limit=40,outer='baseline Task1 fivefold seed42',inner='20percent Task2 stratified seed123; epoch0..12; first maximum',smoke=smoke)
    (OUT/'protocol.json').write_text(json.dumps(protocol,indent=2))
    for k,(tr,te) in enumerate(folds,1):
        a,b=train_test_split(tr,test_size=.2,random_state=123,stratify=y[TARGET][tr]);assert not set(a)&set(b) and not (set(a)|set(b))&set(te)
        opt,scaler=reset(a)
        if smoke:
            probes={n:p.detach().cpu().clone() for n,p in m.named_parameters() if n in ['visual.proj','bert.encoder.layer.11.output.dense.weight','head.shared.0.weight']}
            loss=train_epoch(a,opt,scaler,1,limit=2)
            changed={n:float((dict(m.named_parameters())[n].detach().cpu()-v).abs().max()) for n,v in probes.items()};assert all(v>0 for v in changed.values())
            d=dict(status='passed',steps=2,loss=loss,encoder_head_update=changed,seconds=time.monotonic()-start,not_performance_score=True)
            (OUT/'smoke_result.json').write_text(json.dumps(d,indent=2));print(json.dumps(d),flush=True);return
        def valid_score():return float(f1_score(y[TARGET][b],infer(m,b)[TARGET],labels=range(nc[TARGET]),average='macro',zero_division=0))
        scores=[valid_score()];epochs=[dict(epoch=0,inner_macro_f1=scores[0])]
        for epoch in range(1,CFG['max_epochs']+1):
            loss=train_epoch(a,opt,scaler,epoch);score=valid_score();scores.append(score);epochs.append(dict(epoch=epoch,inner_macro_f1=score,train_loss=loss));print('INNER',k,epoch,'f1',round(score,4),'seconds',round(time.monotonic()-start,1),flush=True)
        best=int(np.argmax(scores));opt,scaler=reset(tr)
        for epoch in range(1,best+1):train_epoch(tr,opt,scaler,epoch)
        pred=infer(m,te);foldids[te]=k
        for t in TASKS:oof[t][te]=pred[t]
        delta={n:p.detach().cpu() for n,p in m.named_parameters() if p.requires_grad}
        torch.save(dict(delta=delta,config=CFG,classes=classes,train=tr.tolist(),test=te.tolist(),epoch=best,base_weights=base_hashes),OUT/f'fold{k}_delta.pt')
        record=dict(fold=k,train=tr.tolist(),test=te.tolist(),inner_train=a.tolist(),inner_valid=b.tolist(),epochs=epochs,selected_epoch=best)
        (OUT/f'fold{k}.json').write_text(json.dumps(record,indent=2));np.savez(OUT/f'fold{k}_predictions.npz',indices=te,**pred);records.append(record);print('FOLD',k,'COMPLETE epoch',best,flush=True)
    assert all((v>=0).all() for v in oof.values()) and (foldids>0).all()
    rows=[]
    for i,row in df.iterrows():
        d=dict(sample_id=row.sample_id,fold=int(foldids[i]))
        for t in TASKS:d[t+'_truth']=row[t];d[t+'_pred']=classes[t][oof[t][i]]
        rows.append(d)
    pd.DataFrame(rows).to_csv(OUT/'oof.csv',index=False)
    metrics={t:dict(macro_f1=float(f1_score(y[t],oof[t],labels=range(nc[t]),average='macro',zero_division=0)),accuracy=float(accuracy_score(y[t],oof[t]))) for t in TASKS}
    result=dict(status='completed',metrics=metrics,selected_epochs=[r['selected_epoch'] for r in records],seconds=time.monotonic()-start,target_reached=metrics[TARGET]['macro_f1']>=.7)
    (OUT/'result.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2),flush=True)
if __name__=='__main__':main()
