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
    norm:str='none'
def grid():
    out=[Config(),Config(view='both',dropout=.2,visual_weight=2.,task2_weight=2.)]
    for norm,w,v in product(['center','standard'],[1.,2.],[1.,2.]):
        out.append(Config(view='both',norm=norm,dropout=.2,task2_weight=w,visual_weight=v))
    assert len(out)==10
    return out
class JointMTL(nn.Module):
    def __init__(self,nclasses,config,train_features):
        super().__init__();self.config=config
        dim={'baseline':1280,'full':1536,'crop':1536,'both':2304}[config.view]
        self.shared=nn.Sequential(nn.Linear(dim,config.hidden),nn.ReLU(),nn.Dropout(config.dropout))
        self.heads=nn.ModuleDict({t:nn.Linear(config.hidden,nclasses[t]) for t in TASKS})
        mean=torch.zeros(2304);scale=torch.ones(2304)
        if config.norm!='none':
            raw=torch.tensor(np.hstack([train_features[:,1280:2816],train_features[:,512:1280]]))
            mean=raw.mean(dim=0)
            if config.norm=='standard':scale=raw.std(dim=0,correction=0).clamp_min(1e-4)
        self.register_buffer('feature_mean',mean);self.register_buffer('feature_scale',scale)
    def forward(self,x):
        c=self.config
        images={'baseline':x[:,:512],'full':x[:,1280:2048],'crop':x[:,2048:2816],'both':x[:,1280:2816]}[c.view]
        text=x[:,512:1280]
        if c.norm!='none':
            assert c.view=='both'
            raw=(torch.cat([images,text],dim=1)-self.feature_mean)/self.feature_scale
            full,crop,text=[torch.nn.functional.normalize(v,p=2,dim=1) for v in raw.split(768,dim=1)]
            images=torch.cat([full,crop],dim=1)
        features=torch.cat([images*c.visual_weight,text],dim=1)
        h=self.shared(features);return {t:head(h) for t,head in self.heads.items()}

def fit(X,y,nclasses,indices,config,seed=42):
    torch.manual_seed(seed);np.random.seed(seed)
    indices=np.asarray(indices);model=JointMTL(nclasses,config,X[indices])
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

