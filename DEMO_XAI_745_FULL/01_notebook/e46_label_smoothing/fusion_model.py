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
    label_smoothing:float=0.
    weight_decay:float=.0001
    task3_weight:float=1.
def grid():
    out=[Config()]
    for smoothing,wd in product([0.,.1,.2],[.0001,.01]):
        out.append(Config(view='both',text_view='mean',visual_weight=2.,task2_weight=2.,task3_weight=2.,label_smoothing=smoothing,weight_decay=wd))
    assert len(out)==7
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
    opt=torch.optim.AdamW(model.parameters(),lr=config.lr,weight_decay=config.weight_decay)
    losses={t:nn.CrossEntropyLoss(weight=class_weights(y[t][indices],nclasses[t],config.class_power),label_smoothing=config.label_smoothing) for t in TASKS}
    weights={t:config.task2_weight if t==TARGET else config.task3_weight if t==TASKS[2] else 1. for t in TASKS}
    data=torch.tensor(X[indices]);truth={t:torch.tensor(y[t][indices]) for t in TASKS}
    model.train()
    for _ in range(config.epochs):
        opt.zero_grad();logits=model(data)
        loss=sum(weights[t]*losses[t](logits[t],truth[t]) for t in TASKS)/sum(weights.values())
        if not torch.isfinite(loss):raise ValueError('Non-finite training loss')
        loss.backward();opt.step()
    model.eval();return model


def balanced_objective(scores):
    return min(float(np.mean([v[t] for v in scores])) for t in TASKS)
