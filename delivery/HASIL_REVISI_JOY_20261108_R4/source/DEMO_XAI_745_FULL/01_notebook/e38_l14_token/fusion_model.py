"""One shared MTL head over selected frozen CLIP view(s) + IndoBERT."""
import sys
from pathlib import Path
from dataclasses import dataclass,replace
from itertools import product
import numpy as np,torch
from torch import nn
sys.path.append(str(Path(__file__).resolve().parent.parent/'e33_joint_mtl'))
from model import Config as BaseConfig,TASKS,TARGET,class_weights,predict,state_hash
@dataclass(frozen=True)
class Config(BaseConfig):
    view:str='baseline'
    text_view:str='cls'
def grid():
    out=[Config()]
    for view,text,w,v in product(['full','crop','both'],['mean','last4'],[1.,2.],[1.,2.]):
        out.append(Config(view=view,text_view=text,task2_weight=w,visual_weight=v))
    assert len(out)==25
    return out
class JointMTL(nn.Module):
    def __init__(self,nclasses,config):
        super().__init__();self.config=config
        dim={'baseline':1280,'full':1536,'crop':1536,'both':2304}[config.view]
        self.shared=nn.Sequential(nn.Linear(dim,config.hidden),nn.ReLU(),nn.Dropout(config.dropout))
        self.heads=nn.ModuleDict({t:nn.Linear(config.hidden,nclasses[t]) for t in TASKS})
    def forward(self,x):
        c=self.config
        images={'baseline':x[:,:512],'full':x[:,1280:2048],'crop':x[:,2048:2816],'both':x[:,1280:2816]}[c.view]
        text={'cls':x[:,512:1280],'mean':x[:,2816:3584],'last4':x[:,3584:4352]}[c.text_view]
        features=torch.cat([images*c.visual_weight,text],dim=1)
        h=self.shared(features);return {t:head(h) for t,head in self.heads.items()}

def fit(X,y,nclasses,indices,config,seed=42):
    torch.manual_seed(seed);np.random.seed(seed)
    indices=np.asarray(indices);model=JointMTL(nclasses,config)
    opt=torch.optim.AdamW(model.parameters(),lr=config.lr,weight_decay=.0001)
    losses={t:nn.CrossEntropyLoss(weight=class_weights(y[t][indices],nclasses[t],config.class_power)) for t in TASKS}
    weights={t:config.task2_weight if t==TARGET else 1. for t in TASKS}
    data=torch.tensor(X[indices]);truth={t:torch.tensor(y[t][indices]) for t in TASKS}
    model.train()
    for _ in range(config.epochs):
        opt.zero_grad();logits=model(data)
        loss=sum(weights[t]*losses[t](logits[t],truth[t]) for t in TASKS)/sum(weights.values())
        if not torch.isfinite(loss):raise ValueError('Non-finite training loss')
        loss.backward();opt.step()
    model.eval();return model

