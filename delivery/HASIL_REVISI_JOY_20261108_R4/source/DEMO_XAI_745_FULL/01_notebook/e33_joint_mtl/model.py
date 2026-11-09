"""Joint three-task heads over frozen CLIP512 + IndoBERT768 features."""
from dataclasses import dataclass,asdict,replace
import hashlib
import numpy as np
import torch
from torch import nn
TASKS=('task1_issue','task2_domain_sumber','task3_primary_entity_type')
TARGET=TASKS[1]
@dataclass(frozen=True)
class Config:
    hidden:int=256
    dropout:float=.4
    task2_weight:float=1.
    visual_weight:float=1.
    epochs:int=120
    lr:float=.001
    class_power:float=1.
    residual:bool=False

def grid():
    base=Config();out=[base]
    for name,values in [('task2_weight',[2.,4.]),('dropout',[0.,.2,.6]),('hidden',[128,512]),('epochs',[60,240]),('lr',[.003,.0003]),('visual_weight',[.5,2.,4.]),('class_power',[0.,.5]),('residual',[True])]:
        out += [replace(base,**{name:v}) for v in values]
    for hidden,dropout,weight,visual,epochs,residual in [(128,.2,2.,2.,160,True),(256,.2,4.,2.,160,True),(512,.4,2.,1.,120,True),(256,.6,2.,4.,240,False),(128,.4,4.,1.,240,False),(256,.2,2.,2.,240,False)]:
        out.append(replace(base,hidden=hidden,dropout=dropout,task2_weight=weight,visual_weight=visual,epochs=epochs,residual=residual))
    assert len(out)==24 and len({str(asdict(c)) for c in out})==24
    return out

class JointMTL(nn.Module):
    def __init__(self,nclasses,config):
        super().__init__();self.config=config
        self.shared=nn.Sequential(nn.Linear(1280,config.hidden),nn.ReLU(),nn.Dropout(config.dropout))
        self.heads=nn.ModuleDict({t:nn.Linear(config.hidden,nclasses[t]) for t in TASKS})
        self.residual=nn.ModuleDict({t:nn.Linear(1280,nclasses[t],bias=False) for t in TASKS}) if config.residual else None
    def forward(self,x):
        x=torch.cat([x[:,:512]*self.config.visual_weight,x[:,512:]],dim=1)
        shared=self.shared(x)
        return {t:self.heads[t](shared)+(self.residual[t](x) if self.residual is not None else 0) for t in TASKS}

def class_weights(y,nclasses,power):
    count=np.bincount(y,minlength=nclasses).astype(np.float32)
    balanced=len(y)/(np.maximum(count,1)*(count>0).sum())
    return torch.tensor(np.where(count>0,balanced**power,0.),dtype=torch.float32)

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

def predict(model,X):
    with torch.no_grad():return {t:z.argmax(1).numpy() for t,z in model(torch.tensor(X)).items()}

def state_hash(model):
    h=hashlib.sha256()
    for name,tensor in sorted(model.state_dict().items()):h.update(name.encode());h.update(tensor.detach().cpu().numpy().tobytes())
    return h.hexdigest()
