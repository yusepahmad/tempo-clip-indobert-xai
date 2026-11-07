"""Synthetic structural checks, never a model quality score."""
from model import *
from dataclasses import replace
def main():
    torch.set_num_threads(1);torch.manual_seed(42);rng=np.random.default_rng(42)
    assert len(grid())==9 and all(all(w>0 for w in c.loss_weights) for c in grid())
    fixture=[[dict(zip(TASKS,[.4,.9,.1]))]*2,[dict(zip(TASKS,[.4,.4,.4]))]*2]
    assert select(fixture)==1 and select([fixture[1],fixture[1]])==0
    nc={t:3 for t in TASKS};m=JointMTL(nc,grid()[1]).eval()
    visual=torch.randn(4,1536);text=torch.randn(4,768);regions=torch.randn(4,32,768,requires_grad=True)
    p,a=m(visual,text,regions,True);assert a.shape==(4,32) and torch.allclose(a.sum(1),torch.ones(4)) and (a>0).all()
    for t in TASKS:
        m.zero_grad();regions.grad=None;p[t].sum().backward(retain_graph=True)
        for prefix in ['query.','key.','value.','shared.','heads.'+t+'.']:
            assert any(n.startswith(prefix) and v.grad is not None and v.grad.abs().sum()>0 for n,v in m.named_parameters()),prefix
        assert m.position.grad.abs().sum()>0 and regions.grad.abs().sum()>0
    z={k:rng.normal(size=shape).astype(np.float32) for k,shape in [('visual',(12,1536)),('mean',(12,768)),('cls',(12,768)),('regions',(12,32,768))]}
    y={t:np.arange(12)%3 for t in TASKS};tr=np.arange(8);c=replace(grid()[1],epochs=2)
    first=fit(z,y,nc,tr,c);changed={k:v.copy() for k,v in z.items()};yy={t:v.copy() for t,v in y.items()}
    for v in changed.values():v[8:]=100
    for v in yy.values():v[8:]=(v[8:]+1)%3
    second=fit(changed,yy,nc,tr,c)
    assert all(torch.equal(v,second.state_dict()[k]) for k,v in first.state_dict().items())
    third=fit(z,y,nc,tr,c);assert all(torch.equal(v,third.state_dict()[k]) for k,v in first.state_dict().items())
    clone=JointMTL(nc,c).eval();clone.load_state_dict(first.state_dict())
    assert all(np.array_equal(v,predict(clone,z,tr)[t]) for t,v in predict(first,z,tr).items())
    print('CHECKS PASSED:9configs, balancedselection/ties, attention simplex, shared3task gradients, heldout isolation, determinism, checkpoint parity')
if __name__=='__main__':main()
