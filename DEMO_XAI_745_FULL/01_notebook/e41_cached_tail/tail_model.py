"""Trainable IndoBERT last two layers with frozen-front/CLIP caches."""
from pathlib import Path
import json,random
import numpy as np,torch
from torch import nn
from transformers import BertConfig
from transformers.models.bert.modeling_bert import BertLayer
TASKS=('task1_issue','task2_domain_sumber','task3_primary_entity_type');TARGET=TASKS[1]
CFG=dict(hidden=256,dropout=.3,visual_weight=2.,loss_weights=[1.,2.,2.],encoder_lr=2e-5,head_lr=3e-4,weight_decay=.01,batch=32,epoch_candidates=[0,2,4,8,12],seed=42)
def seed():random.seed(42);np.random.seed(42);torch.manual_seed(42)
def class_weights(y,n):
    c=np.bincount(y,minlength=n).astype(np.float32)
    return torch.tensor(np.where(c>0,len(y)/(np.maximum(c,1)*(c>0).sum()),0.),dtype=torch.float32)
class Head(nn.Module):
    def __init__(self,nc):
        super().__init__();self.shared=nn.Sequential(nn.Linear(2304,CFG['hidden']),nn.ReLU(),nn.Dropout(CFG['dropout']));self.heads=nn.ModuleDict({t:nn.Linear(CFG['hidden'],nc[t]) for t in TASKS})
    def forward(self,x):
        h=self.shared(x);return {t:layer(h) for t,layer in self.heads.items()}
class TailMTL(nn.Module):
    def __init__(self,nc,cache):
        super().__init__();config=BertConfig.from_dict(json.loads((Path(cache)/'bert_config.json').read_text()));config._attn_implementation='sdpa'
        self.tail=nn.ModuleList([BertLayer(config),BertLayer(config)]);self.tail.load_state_dict(torch.load(Path(cache)/'tail_initial.pt',map_location='cpu',weights_only=True));self.head=Head(nc)
    def features(self,h,attention,pool_mask,visual):
        am=(~attention.bool()[:,None,None,:]).to(h.dtype)*torch.finfo(h.dtype).min
        for layer in self.tail:
            h=layer(h,attention_mask=am)
            if isinstance(h,tuple):h=h[0]
        pm=pool_mask.to(h.dtype);text=(h*pm.unsqueeze(-1)).sum(dim=1)/pm.sum(dim=1,keepdim=True)
        text=nn.functional.normalize(text.float(),p=2,dim=1)
        return torch.cat([visual.float()*CFG['visual_weight'],text],dim=1)
    def forward(self,h,attention,pool_mask,visual):return self.head(self.features(h,attention,pool_mask,visual))
def warm_head(z,y,nc,tr):
    seed();head=Head(nc);opt=torch.optim.AdamW(head.parameters(),lr=.001,weight_decay=.0001)
    x=torch.tensor(np.hstack([z['visual'][tr]*CFG['visual_weight'],z['base_mean'][tr]]));truth={t:torch.tensor(y[t][tr]) for t in TASKS};loss={t:nn.CrossEntropyLoss(weight=class_weights(y[t][tr],nc[t])) for t in TASKS}
    head.train()
    for _ in range(120):
        opt.zero_grad();pred=head(x);l=sum(w*loss[t](pred[t],truth[t]) for t,w in zip(TASKS,CFG['loss_weights']))/sum(CFG['loss_weights']);l.backward();opt.step()
    return {k:v.detach().clone() for k,v in head.state_dict().items()}
def batch_tensors(z,ix,device):
    length=int(z['attention'][ix].sum(axis=1).max())
    return tuple(torch.tensor(z[k][ix,:length] if k in ['h10','attention','pool_mask'] else z[k][ix],device=device) for k in ['h10','attention','pool_mask','visual'])
