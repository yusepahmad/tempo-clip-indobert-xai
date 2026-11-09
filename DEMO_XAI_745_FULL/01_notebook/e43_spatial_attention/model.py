"""Shared text-conditioned regional attention and jointly trained three heads."""
from dataclasses import dataclass,asdict
from itertools import product
import numpy as np,torch
from torch import nn
TASKS=('task1_issue','task2_domain_sumber','task3_primary_entity_type')
@dataclass(frozen=True)
class Config:
    attention:bool=False
    hidden:int=256
    text:str='mean'
    loss_weights:tuple=(1.,1.,1.)
    epochs:int=120
    lr:float=.001
    dropout:float=.4
    weight_decay:float=.001
def grid():return [Config()]+[Config(True,h,t,w) for h,t,w in product([128,256],['mean','cls'],[(1.,1.,1.),(1.,2.,2.)])]
def select(scores):return max(range(len(scores)),key=lambda i:min(sum(row[t] for row in scores[i])/len(scores[i]) for t in TASKS))
def class_weights(y,n):
    counts=np.bincount(y,minlength=n);return torch.tensor(np.where(counts>0,len(y)/(np.maximum(counts,1)*(counts>0).sum()),0),dtype=torch.float32)
class JointMTL(nn.Module):
    def __init__(self,nc,c):
        super().__init__();self.config=c
        if c.attention:
            self.query=nn.Linear(768,64);self.key=nn.Linear(768,64);self.value=nn.Linear(768,128)
            self.position=nn.Parameter(torch.zeros(32,64));nn.init.normal_(self.position,std=.02)
        self.shared=nn.Sequential(nn.Linear(2304+(128 if c.attention else 0),c.hidden),nn.ReLU(),nn.Dropout(c.dropout))
        self.heads=nn.ModuleDict({t:nn.Linear(c.hidden,nc[t]) for t in TASKS})
    def forward(self,visual,text,regions,return_attention=False):
        pieces=[visual*2.,text];attention=None
        if self.config.attention:
            scores=(self.query(text)[:,None,:]*(self.key(regions)+self.position[None])).sum(-1)/8.
            attention=torch.softmax(scores,dim=1);pieces.append((self.value(regions)*attention[:,:,None]).sum(1))
        h=self.shared(torch.cat(pieces,dim=1));pred={t:head(h) for t,head in self.heads.items()}
        return (pred,attention) if return_attention else pred
def tensors(z,indices,c,device):return tuple(torch.tensor(z[k][indices],device=device) for k in ['visual',c.text,'regions'])
def fit(z,y,nc,indices,c,device='cpu',guard=lambda:None):
    torch.manual_seed(42);np.random.seed(42);m=JointMTL(nc,c).to(device)
    x=tensors(z,indices,c,device);truth={t:torch.tensor(y[t][indices],device=device) for t in TASKS}
    losses={t:nn.CrossEntropyLoss(weight=class_weights(y[t][indices],nc[t]).to(device)) for t in TASKS}
    optimizer=torch.optim.AdamW(m.parameters(),lr=c.lr,weight_decay=c.weight_decay);m.train()
    for _ in range(c.epochs):
        optimizer.zero_grad(set_to_none=True);p=m(*x)
        loss=sum(w*losses[t](p[t],truth[t]) for t,w in zip(TASKS,c.loss_weights))/sum(c.loss_weights)
        assert torch.isfinite(loss);loss.backward();assert all(p.grad is None or torch.isfinite(p.grad).all() for p in m.parameters());optimizer.step();guard()
    return m.eval()
def predict(m,z,indices,device='cpu'):
    with torch.inference_mode():
        p=m(*tensors(z,indices,m.config,device));assert all(torch.isfinite(v).all() for v in p.values())
        return {t:v.argmax(1).cpu().numpy() for t,v in p.items()}
