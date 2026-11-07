"""PCGrad on shared parameters; private heads keep ordinary weighted gradients."""
import sys,random
from pathlib import Path
from dataclasses import dataclass,replace
import numpy as np,torch
from torch import nn
BASE_MODEL_SOURCE=Path(__file__).resolve().parent.parent/'e33_joint_mtl/model.py'
sys.path.append(str(BASE_MODEL_SOURCE.parent))
from model import Config as BaseConfig,JointMTL,TASKS,TARGET,predict,state_hash,class_weights,fit as ordinary_fit
@dataclass(frozen=True)
class Config(BaseConfig):pcgrad:bool=False

def grid():
    b=Config()
    return [b,replace(b,task2_weight=2.)]+[replace(b,pcgrad=True,task2_weight=w,visual_weight=v) for w in [1.,2.] for v in [1.,2.]]

def project(gradients,rng):
    projected=[]
    for i,g in enumerate(gradients):
        current=g.clone();order=list(range(len(gradients)));rng.shuffle(order)
        for j in order:
            if i==j:continue
            other=gradients[j];dot=torch.dot(current,other)
            if dot<0:current-=dot/torch.dot(other,other).clamp_min(1e-12)*other
        projected.append(current)
    return sum(projected)

def fit(X,y,nclasses,indices,config,seed=42):
    if not config.pcgrad:return ordinary_fit(X,y,nclasses,indices,config,seed)
    torch.manual_seed(seed);np.random.seed(seed);rng=random.Random(seed)
    tr=np.asarray(indices);m=JointMTL(nclasses,config);opt=torch.optim.AdamW(m.parameters(),lr=config.lr,weight_decay=.0001)
    xx=torch.tensor(X[tr]);yy={t:torch.tensor(y[t][tr]) for t in TASKS}
    losses={t:nn.CrossEntropyLoss(weight=class_weights(y[t][tr],nclasses[t],config.class_power)) for t in TASKS}
    weights={t:config.task2_weight if t==TARGET else 1. for t in TASKS};denom=sum(weights.values());shared=list(m.shared.parameters());heads={t:list(m.heads[t].parameters()) for t in TASKS}
    conflicts=0;pairs=0;m.train()
    for _ in range(config.epochs):
        opt.zero_grad();out=m(xx);grads=[];private={}
        for j,t in enumerate(TASKS):
            loss=weights[t]*losses[t](out[t],yy[t]);assert torch.isfinite(loss)
            g=torch.autograd.grad(loss,shared+heads[t],retain_graph=j<len(TASKS)-1)
            grads.append(torch.cat([v.reshape(-1) for v in g[:len(shared)]]));private[t]=g[len(shared):]
        for i in range(len(grads)):
            for j in range(i):conflicts+=int(torch.dot(grads[i],grads[j])<0);pairs+=1
        combined=project(grads,rng)/denom;offset=0
        for p in shared:p.grad=combined[offset:offset+p.numel()].reshape_as(p);offset+=p.numel()
        for t in TASKS:
            for p,g in zip(heads[t],private[t]):p.grad=g/denom
        assert all(p.grad is not None and torch.isfinite(p.grad).all() for p in m.parameters())
        opt.step()
    m.eval();m.pcgrad_diagnostics=dict(conflicting_original_pairs=conflicts,total_original_pairs=pairs,frequency=conflicts/pairs if pairs else None)
    return m
