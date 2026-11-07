"""CPU preflight before any nested fit."""
import json
from dataclasses import replace
import numpy as np,torch
from fusion_model import *
from model import fit as baseline_fit,Config as BaseConfig

def main():
    torch.set_num_threads(1);rng=np.random.default_rng(42);X=rng.normal(size=(24,4352)).astype(np.float32)
    nc={t:3 for t in TASKS};y={t:np.arange(24)%3 for t in TASKS};tr=np.arange(18)
    c=replace(Config(),epochs=3);a=fit(X,y,nc,tr,c);b=baseline_fit(X[:,:1280],y,nc,tr,BaseConfig(epochs=3))
    assert state_hash(a)==state_hash(b)
    c=replace(grid()[-1],epochs=3);a=fit(X,y,nc,tr,c)
    y2={t:v.copy() for t,v in y.items()}
    for t in TASKS:y2[t][18:]=(y2[t][18:]+1)%3
    assert state_hash(a)==state_hash(fit(X,y2,nc,tr,c))==state_hash(fit(X,y,nc,tr,c))
    a.train();a.zero_grad();p=a(torch.tensor(X[tr]));loss=sum(nn.CrossEntropyLoss(weight=class_weights(y[t][tr],3,1.),label_smoothing=.2)(p[t],torch.tensor(y[t][tr])) for t in TASKS);loss.backward()
    for prefix in ['shared.','relation.']+[f'{group}.{t}.' for group in ['heads','refiners'] for t in TASKS]:
        assert any(v.grad is not None and torch.isfinite(v.grad).all() and v.grad.abs().sum()>0 for n,v in a.named_parameters() if n.startswith(prefix))
    X2=X.copy();X2[18:]=rng.normal(size=X2[18:].shape)
    assert state_hash(a)==state_hash(fit(X2,y,nc,tr,c))
    a.eval();a.zero_grad();a(torch.tensor(X[tr]))[TASKS[0]].sum().backward()
    assert all(a.heads[t].weight.grad is not None and a.heads[t].weight.grad.abs().sum()>0 for t in TASKS)
    assert all(c.label_smoothing in [0.,.1,.2] and c.weight_decay>0 for c in grid())
    print(json.dumps(dict(status='passed',baseline_smoothing0_exact=True,heldout_label_invariance=True,determinism=True,joint_shared_refinement_three_head_gradients=True,cross_task_gradient=True,heldout_feature_invariance=True,configs=len(grid()))))
if __name__=='__main__':main()
