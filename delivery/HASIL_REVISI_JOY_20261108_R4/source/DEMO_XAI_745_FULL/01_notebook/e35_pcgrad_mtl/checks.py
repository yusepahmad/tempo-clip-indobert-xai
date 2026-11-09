from pcgrad_model import *
def main():
    torch.set_num_threads(1)
    g=project([torch.tensor([1.,-1.]),torch.tensor([-1.,0.])],random.Random(42))/2
    assert torch.allclose(g,torch.tensor([-.25,-.75]))
    g=project([torch.tensor([1.,0.]),torch.tensor([1.,1.])],random.Random(42))/2
    assert torch.equal(g,torch.tensor([1.,.5]))
    rng=np.random.default_rng(42);X=rng.normal(size=(30,1280)).astype(np.float32);nc=dict(zip(TASKS,[4,3,2]));y={t:np.arange(30)%n for t,n in nc.items()};tr=np.arange(24)
    c=replace(Config(),pcgrad=True,epochs=3)
    a=fit(X,y,nc,tr,c);b=fit(X,y,nc,tr,c);assert state_hash(a)==state_hash(b)
    xx=X.copy();xx[24:]*=99;yy={t:v.copy() for t,v in y.items()}
    for t in TASKS:yy[t][24:]=(yy[t][24:]+1)%nc[t]
    b=fit(xx,yy,nc,tr,c);assert state_hash(a)==state_hash(b)
    initial=fit(X,y,nc,tr,replace(c,epochs=0))
    for name,p in a.named_parameters():assert not torch.equal(p,dict(initial.named_parameters())[name]),name
    assert len(grid())==6
    print('PASS analytic projection, non-conflict identity, deterministicfit, heldoutisolation, shared and allheads updated,6configs')
if __name__=='__main__':main()
