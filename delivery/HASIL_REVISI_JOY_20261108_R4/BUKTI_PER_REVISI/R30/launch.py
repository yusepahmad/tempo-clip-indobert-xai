"""Sprint 2: deterministic SigLIP2 image augmentation ablation on frozen folds."""
import csv,hashlib,io,json,random,time
from pathlib import Path
import numpy as np,pandas as pd,torch
from PIL import Image,ImageEnhance
from torch import nn
import torch.nn.functional as F
from sklearn.metrics import f1_score
from sklearn.model_selection import StratifiedKFold
from transformers import AutoImageProcessor,AutoModel
from huggingface_hub import snapshot_download

I=Path('/kaggle/input');DATA=next(p for p in I.rglob('DATASET_740_TASK2_DOMAIN.csv') if p.parent.name=='03_data');ROOT=DATA.parents[1];FOLDS=next(I.rglob('baseline_oof.csv'));CACHE=next(I.rglob('front_cache.npz'));OUT=Path('/kaggle/working/augmentation');TASKS=('task1_issue','task2_domain_sumber','task3_primary_entity_type');VARIANTS=('A00_none','A01_light','A02_moderate','A03_light_sampler');FOLD_CFG=(1,1,1,2,2)
CFG=[dict(hidden=128,dropout=.2,lr=1e-3,wd=1e-4,power=0.,smooth=0.,epochs=35),dict(hidden=192,dropout=.25,lr=8e-4,wd=2e-4,power=.5,smooth=.05,epochs=35),dict(hidden=256,dropout=.3,lr=6e-4,wd=3e-4,power=.5,smooth=.05,epochs=35)]
MODEL='google/siglip2-base-patch16-384';REV='f775b65a79762255128c981547af89addcfe0f88';WEIGHT='ed72c0ace85020ae610fc817c2538b9cae5a477b012a50859c60af5b3ad30857'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def read(p):
 with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def seed(s):random.seed(s);np.random.seed(s);torch.manual_seed(s);torch.cuda.manual_seed_all(s)
def aug(im,sid,mode):
 r=random.Random(int(hashlib.sha256(f'{sid}:{mode}:20261018'.encode()).hexdigest()[:16],16));im=im.convert('RGB')
 if mode=='light':br,co,q,rot,sig=(.92,1.08),(.92,1.08),(88,96),0,1.5
 else:br,co,q,rot,sig=(.85,1.15),(.85,1.15),(78,90),r.uniform(-2,2),3.
 im=ImageEnhance.Brightness(im).enhance(r.uniform(*br));im=ImageEnhance.Contrast(im).enhance(r.uniform(*co))
 if rot:im=im.rotate(rot,resample=Image.Resampling.BICUBIC,fillcolor=(255,255,255))
 b=io.BytesIO();im.save(b,'JPEG',quality=r.randint(*q));b.seek(0);arr=np.asarray(Image.open(b).convert('RGB')).astype(np.int16);noise=np.random.default_rng(r.randrange(2**32)).normal(0,sig,arr.shape);return Image.fromarray(np.clip(arr+noise,0,255).astype('uint8'))
def features(df):
 snap=Path(snapshot_download(MODEL,revision=REV,allow_patterns=['config.json','preprocessor_config.json','model.safetensors']));assert sha(snap/'model.safetensors')==WEIGHT;proc=AutoImageProcessor.from_pretrained(snap,local_files_only=True,use_fast=False);model=AutoModel.from_pretrained(snap,local_files_only=True,use_safetensors=True,torch_dtype=torch.float32).cuda().eval();out={k:[] for k in ('clean','light','moderate')}
 for off in range(0,740,12):
  ims={k:[] for k in out}
  for row in df.iloc[off:off+12].itertuples():
   p=ROOT/'05_gambar'/Path(row.image_path).name;assert sha(p)==row.image_sha256
   with Image.open(p) as x:x=x.convert('RGB');ims['clean'].append(x.copy());ims['light'].append(aug(x,row.sample_id,'light'));ims['moderate'].append(aug(x,row.sample_id,'moderate'))
  for k in out:
   px=proc(images=ims[k],return_tensors='pt')['pixel_values'].cuda();
   with torch.inference_mode():z=model.get_image_features(pixel_values=px,return_dict=True).pooler_output
   out[k].append(F.normalize(z.float(),dim=1).cpu().numpy())
  if off%120==0:print('features',min(off+12,740),flush=True)
 for k in out:out[k]=np.vstack(out[k]);np.savez_compressed(OUT/f'{k}_features.npz',sample_ids=df.sample_id.to_numpy(str),image=out[k])
 del model;torch.cuda.empty_cache();return out
class Joint(nn.Module):
 def __init__(self,classes,c):super().__init__();self.s=nn.Sequential(nn.Linear(1536,c['hidden']),nn.LayerNorm(c['hidden']),nn.GELU(),nn.Dropout(c['dropout']));self.h=nn.ModuleDict({k:nn.Linear(c['hidden'],classes[k]) for k in TASKS})
 def forward(self,v,t):z=self.s(torch.cat([F.normalize(v.float(),dim=1),F.normalize(t.float(),dim=1)],1));return {k:self.h[k](z) for k in TASKS}
def weights(y,n,p):
 if p==0:return torch.ones(n,device='cuda')
 c=np.bincount(y,minlength=n).astype('float32');w=(len(y)/(n*c))**p;return torch.tensor(w/w.mean(),device='cuda')
def fit(v,t,y,classes,c,s,sampler=False):
 seed(s);m=Joint(classes,c).cuda();opt=torch.optim.AdamW(m.parameters(),lr=c['lr'],weight_decay=c['wd']);loss={k:nn.CrossEntropyLoss(weight=weights(y[k],classes[k],c['power']),label_smoothing=c['smooth']) for k in TASKS};vt=torch.tensor(v,device='cuda');tt=torch.tensor(t,device='cuda');yt={k:torch.tensor(y[k],device='cuda') for k in TASKS};m.train();n=len(v)
 tuples=list(zip(*(y[k] for k in TASKS)));counts={x:tuples.count(x) for x in set(tuples)};prob=torch.tensor([counts[x]**-.5 for x in tuples],device='cuda');prob/=prob.sum()
 for _ in range(c['epochs']):
  order=torch.multinomial(prob,n,replacement=True) if sampler else torch.randperm(n,device='cuda')
  for idx in order.split(32):opt.zero_grad();o=m(vt[idx],tt[idx]);l=sum(loss[k](o[k],yt[k][idx]) for k in TASKS)/3;l.backward();opt.step()
 return m.eval()
@torch.inference_mode()
def pred(m,v,t):o=m(torch.tensor(v,device='cuda'),torch.tensor(t,device='cuda'));return {k:o[k].argmax(1).cpu().numpy() for k in TASKS}
def score(y,p,classes):
 d={k:float(f1_score(y[k],p[k],labels=range(classes[k]),average='macro',zero_division=0)) for k in TASKS};return {**d,'min':min(d.values()),'mean':float(np.mean(list(d.values())))}
def trainset(var,idx,f,text,y):
 if var=='A00_none':return f['clean'][idx],text[idx],{k:y[k][idx] for k in TASKS}
 key='moderate' if var=='A02_moderate' else 'light';return np.vstack([f['clean'][idx],f[key][idx]]),np.vstack([text[idx],text[idx]]),{k:np.concatenate([y[k][idx],y[k][idx]]) for k in TASKS}
def main():
 assert torch.cuda.is_available();OUT.mkdir(exist_ok=True);df=pd.read_csv(DATA).fillna('');rows,fr=read(DATA),read(FOLDS);assert [r['sample_id'] for r in rows]==[r['sample_id'] for r in fr];f=features(df);text=np.load(CACHE)['base_mean'];labels={k:sorted({r[k] for r in rows}) for k in TASKS};classes={k:len(labels[k]) for k in TASKS};y={k:np.array([{x:i for i,x in enumerate(labels[k])}[r[k]] for r in rows]) for k in TASKS};folds=np.array([int(r['fold']) for r in fr]);all_oof={v:{k:np.full(740,-1) for k in TASKS} for v in VARIANTS};selected={k:np.full(740,-1) for k in TASKS};details=[]
 for fold in range(1,6):
  tr,te=np.where(folds!=fold)[0],np.where(folds==fold)[0];c=CFG[FOLD_CFG[fold-1]];splits=list(StratifiedKFold(3,shuffle=True,random_state=40100+fold).split(tr,y['task2_domain_sumber'][tr]));inner=[]
  for vi,var in enumerate(VARIANTS):
   vals=[]
   for si,(a,b) in enumerate(splits):
    a,b=tr[a],tr[b];vv,tt,yy=trainset(var,a,f,text,y);m=fit(vv,tt,yy,classes,c,410000+fold*100+vi*10+si,var=='A03_light_sampler');vals.append(score({k:y[k][b] for k in TASKS},pred(m,f['clean'][b],text[b]),classes));del m
   inner.append({'variant':var,'min':float(np.mean([x['min'] for x in vals])),'mean':float(np.mean([x['mean'] for x in vals]))})
  chosen=max(inner,key=lambda x:(x['min'],x['mean']))['variant']
  for vi,var in enumerate(VARIANTS):
   vv,tt,yy=trainset(var,tr,f,text,y);m=fit(vv,tt,yy,classes,c,420000+fold*100+vi,var=='A03_light_sampler');p=pred(m,f['clean'][te],text[te]);del m
   for k in TASKS:all_oof[var][k][te]=p[k]
   if var==chosen:
    for k in TASKS:selected[k][te]=p[k]
  details.append({'fold':fold,'inner':inner,'selected_variant':chosen});print('fold',fold,'selected',chosen,flush=True)
 results={v:score(y,all_oof[v],classes) for v in VARIANTS};results['selected_pipeline']=score(y,selected,classes)
 for var,preds in {**all_oof,'selected_pipeline':selected}.items():
  with (OUT/f'{var}_oof.csv').open('w',newline='') as h:
   fields=['sample_id','fold']+[z for k in TASKS for z in (k+'_truth',k+'_pred')];w=csv.DictWriter(h,fieldnames=fields);w.writeheader()
   for i,r in enumerate(rows):
    d={'sample_id':r['sample_id'],'fold':int(folds[i])}
    for k in TASKS:d[k+'_truth']=labels[k][y[k][i]];d[k+'_pred']=labels[k][int(preds[k][i])]
    w.writerow(d)
 result={'schema':'tempo-sprint2-augmentation-v1','status':'complete','encoder':MODEL,'revision':REV,'dataset_sha256':sha(DATA),'results':results,'fold_details':details,'features':{k:sha(OUT/f'{k}_features.npz') for k in f}};(OUT/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(results,indent=2))
if __name__=='__main__':main()
