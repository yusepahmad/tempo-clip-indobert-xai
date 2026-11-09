"""Micro-E05: partial SigLIP2 fine-tuning with three jointly optimized heads."""
import csv,hashlib,json,random,time
from pathlib import Path
import numpy as np,pandas as pd,torch
from PIL import Image
from torch import nn
import torch.nn.functional as F
from torch.utils.data import Dataset,DataLoader
from sklearn.metrics import f1_score
from sklearn.model_selection import StratifiedShuffleSplit
from transformers import AutoImageProcessor,AutoModel
from huggingface_hub import snapshot_download

I=Path('/kaggle/input');DATA=next(p for p in I.rglob('DATASET_740_TASK2_DOMAIN.csv') if p.parent.name=='03_data');ROOT=DATA.parents[1];FOLDS=next(I.rglob('baseline_oof.csv'));CACHE=next(I.rglob('front_cache.npz'));OUT=Path('/kaggle/working/MICRO_E05');TASKS=('task1_issue','task2_domain_sumber','task3_primary_entity_type');MODEL='google/siglip2-base-patch16-384';REV='f775b65a79762255128c981547af89addcfe0f88';WEIGHT='ed72c0ace85020ae610fc817c2538b9cae5a477b012a50859c60af5b3ad30857';DATA_SHA='cba20f8250bcb59481ed2d3d7d5d42fb8242c96a7ba2d11a2cd02ad80862961a'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def read(p):
 with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def seed(s):random.seed(s);np.random.seed(s);torch.manual_seed(s);torch.cuda.manual_seed_all(s)
class DS(Dataset):
 def __init__(self,df,idx,text,y,processor,train=False):self.df=df;self.idx=np.array(idx);self.text=text;self.y=y;self.p=processor;self.train=train
 def __len__(self):return len(self.idx)
 def __getitem__(self,j):
  i=int(self.idx[j]);row=self.df.iloc[i];path=ROOT/'05_gambar'/Path(row.image_path).name
  with Image.open(path) as im:im=im.convert('RGB');px=self.p(images=im,return_tensors='pt')['pixel_values'][0]
  return px,torch.tensor(self.text[i],dtype=torch.float32),torch.tensor([self.y[t][i] for t in TASKS]),i
class Joint(nn.Module):
 def __init__(self,vision,classes):
  super().__init__();self.vision=vision;self.shared=nn.Sequential(nn.Linear(1536,256),nn.LayerNorm(256),nn.GELU(),nn.Dropout(.25));self.heads=nn.ModuleDict({t:nn.Linear(256,classes[t]) for t in TASKS})
 def forward(self,px,text):
  v=self.vision.get_image_features(pixel_values=px,return_dict=True).pooler_output;v=F.normalize(v.float(),dim=1);z=self.shared(torch.cat([v,F.normalize(text.float(),dim=1)],1));return {t:self.heads[t](z) for t in TASKS}
def fresh(snapshot,classes):
 vision=AutoModel.from_pretrained(snapshot,local_files_only=True,use_safetensors=True,torch_dtype=torch.float32)
 for p in vision.parameters():p.requires_grad_(False)
 for p in vision.vision_model.encoder.layers[-2:].parameters():p.requires_grad_(True)
 for name in ('post_layernorm','head'):
  obj=getattr(vision.vision_model,name,None)
  if obj:
   for p in obj.parameters():p.requires_grad_(True)
 proj=getattr(vision,'visual_projection',None)
 if proj:
  for p in proj.parameters():p.requires_grad_(True)
 return Joint(vision,classes).cuda()
def train_epoch(m,loader,opt,scaler):
 m.train();losses=[]
 for px,text,y,_ in loader:
  px,text,y=px.cuda(non_blocking=True),text.cuda(non_blocking=True),y.cuda(non_blocking=True);opt.zero_grad(set_to_none=True)
  with torch.autocast('cuda',dtype=torch.float16):
   o=m(px,text);loss=(F.cross_entropy(o[TASKS[0]],y[:,0])+1.2*F.cross_entropy(o[TASKS[1]],y[:,1])+F.cross_entropy(o[TASKS[2]],y[:,2]))/3.2
  scaler.scale(loss).backward();scaler.step(opt);scaler.update();losses.append(loss.item())
 return float(np.mean(losses))
@torch.inference_mode()
def predict(m,loader):
 m.eval();out={t:[] for t in TASKS};idx=[]
 for px,text,_,ii in loader:
  o=m(px.cuda(),text.cuda());idx.extend(ii.numpy().tolist())
  for t in TASKS:out[t].extend(o[t].argmax(1).cpu().numpy().tolist())
 return np.array(idx),{t:np.array(out[t]) for t in TASKS}
def scores(y,idx,p):
 d={t:float(f1_score(y[t][idx],p[t],average='micro')) for t in TASKS};return {**d,'min':min(d.values()),'mean':float(np.mean(list(d.values())))}
def fit_epochs(df,idx,text,y,proc,snapshot,classes,epochs,s):
 seed(s);m=fresh(snapshot,classes);loader=DataLoader(DS(df,idx,text,y,proc,True),batch_size=8,shuffle=True,num_workers=2,pin_memory=True);opt=torch.optim.AdamW([p for p in m.parameters() if p.requires_grad],lr=2e-5,weight_decay=1e-3);scaler=torch.amp.GradScaler('cuda')
 for _ in range(epochs):train_epoch(m,loader,opt,scaler)
 return m
def main():
 assert torch.cuda.is_available() and sha(DATA)==DATA_SHA;seed(42);OUT.mkdir(exist_ok=True);df=pd.read_csv(DATA).fillna('');rows,fr=read(DATA),read(FOLDS);text=np.load(CACHE)['base_mean'];ids=[r['sample_id'] for r in rows];assert ids==[r['sample_id'] for r in fr];labels={t:sorted({r[t] for r in rows}) for t in TASKS};classes={t:len(labels[t]) for t in TASKS};y={t:np.array([{z:i for i,z in enumerate(labels[t])}[r[t]] for r in rows]) for t in TASKS};folds=np.array([int(r['fold']) for r in fr]);snap=Path(snapshot_download(MODEL,revision=REV,allow_patterns=['config.json','preprocessor_config.json','model.safetensors']));assert sha(snap/'model.safetensors')==WEIGHT;proc=AutoImageProcessor.from_pretrained(snap,local_files_only=True,use_fast=False);oof={t:np.full(740,-1) for t in TASKS};details=[];started=time.time()
 for fold in range(1,6):
  tr,te=np.where(folds!=fold)[0],np.where(folds==fold)[0];a,b=next(StratifiedShuffleSplit(1,test_size=.18,random_state=1000+fold).split(tr,y['task2_domain_sumber'][tr]));fit_idx,val_idx=tr[a],tr[b];m=fresh(snap,classes);loader=DataLoader(DS(df,fit_idx,text,y,proc,True),batch_size=8,shuffle=True,num_workers=2,pin_memory=True);val_loader=DataLoader(DS(df,val_idx,text,y,proc),batch_size=16,shuffle=False,num_workers=2,pin_memory=True);opt=torch.optim.AdamW([p for p in m.parameters() if p.requires_grad],lr=2e-5,weight_decay=1e-3);scaler=torch.amp.GradScaler('cuda');best=(-1,None,None);history=[]
  for ep in range(1,9):
   loss=train_epoch(m,loader,opt,scaler);idx,p=predict(m,val_loader);sc=scores(y,idx,p);history.append({'epoch':ep,'loss':loss,'validation':sc});key=(sc['min'],sc['mean'])
   if key>best[:2]:best=(key[0],key[1],ep)
   print('fold',fold,'epoch',ep,sc,flush=True)
  del m;torch.cuda.empty_cache();chosen=best[2];m=fit_epochs(df,tr,text,y,proc,snap,classes,chosen,2000+fold);test_loader=DataLoader(DS(df,te,text,y,proc),batch_size=16,shuffle=False,num_workers=2,pin_memory=True);idx,p=predict(m,test_loader)
  for t in TASKS:oof[t][idx]=p[t]
  details.append({'fold':fold,'selected_epoch':chosen,'validation_history':history,'outer':scores(y,idx,p)});del m;torch.cuda.empty_cache();print('outer',details[-1],flush=True)
 fields=['sample_id','fold']+[z for t in TASKS for z in (t+'_truth',t+'_pred')]
 with (OUT/'predictions.csv').open('w',newline='') as h:
  w=csv.DictWriter(h,fieldnames=fields);w.writeheader()
  for i,sid in enumerate(ids):
   d={'sample_id':sid,'fold':int(folds[i])}
   for t in TASKS:d[t+'_truth']=labels[t][y[t][i]];d[t+'_pred']=labels[t][int(oof[t][i])]
   w.writerow(d)
 micro={t:float(f1_score(y[t],oof[t],average='micro')) for t in TASKS};macro={t:float(f1_score(y[t],oof[t],average='macro')) for t in TASKS};result={'schema':'tempo-micro-e05-v1','status':'complete','model':MODEL,'revision':REV,'weight_sha256':WEIGHT,'unfrozen':'last 2 vision blocks + vision pool/projection + joint heads','micro_f1':micro,'macro_f1_diagnostic':macro,'minimum_micro_f1':min(micro.values()),'all_tasks_at_least_0_70':min(micro.values())>=.7,'fold_details':details,'seconds':time.time()-started,'dataset_sha256':sha(DATA),'predictions_sha256':sha(OUT/'predictions.csv')};(OUT/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
