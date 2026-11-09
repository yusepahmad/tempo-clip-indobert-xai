"""Meaningful split-isolation, deterministic training and joint-gradient checks."""
import numpy as np,torch
from dataclasses import replace
from model import *
def main():
    torch.set_num_threads(1);torch.manual_seed(5)
    rng=np.random.default_rng(5);X=rng.normal(size=(40,1280)).astype(np.float32)
    nc={t:n for t,n in zip(TASKS,[4,3,2])};y={t:np.arange(40)%n for t,n in nc.items()};tr=np.arange(30)
    for c in [replace(Config(),epochs=3),replace(grid()[-6],epochs=3)]:
        a=fit(X,y,nc,tr,c);b=fit(X,y,nc,tr,c)
        assert state_hash(a)==state_hash(b)
        modified={t:v.copy() for t,v in y.items()}
        for t in TASKS:modified[t][30:]=(modified[t][30:]+1)%nc[t]
        XX=X.copy();XX[30:]*=100
        b=fit(XX,modified,nc,tr,c);assert state_hash(a)==state_hash(b),'heldout contamination'
        logits=a(torch.tensor(X[:6]))
        for t in TASKS:
            loss=torch.nn.functional.cross_entropy(logits[t],torch.tensor(y[t][:6]))
            grad=torch.autograd.grad(loss,a.shared[0].weight,retain_graph=True)[0]
            assert torch.isfinite(grad).all() and grad.abs().sum()>0,'task disconnected from shared representation'
    assert len(grid())==24 and all(c.task2_weight>0 for c in grid())
    assert torch.equal(class_weights(np.array([0,0,0,1]),2,1),torch.tensor([2/3,2.]))
    print('PASS deterministicfit; heldout feature/label isolation; training-only weights; all3 shared gradients;24fixedconfigs')
if __name__=='__main__':main()
