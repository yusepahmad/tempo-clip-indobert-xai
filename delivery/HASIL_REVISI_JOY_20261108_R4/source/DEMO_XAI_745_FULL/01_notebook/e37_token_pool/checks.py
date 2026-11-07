from pool_model import *
from extract import pool
def main():
    torch.set_num_threads(1)
    h=torch.tensor([[[99.,99.],[1.,3.],[5.,7.],[999.,999.]]]);mask=torch.tensor([[False,True,True,False]])
    assert torch.equal(pool(h,mask),torch.tensor([[3.,5.]]));h[0,0]=0;h[0,3]=0;assert torch.equal(pool(h,mask),torch.tensor([[3.,5.]]))
    rng=np.random.default_rng(42);X=rng.normal(size=(32,2816)).astype(np.float32);nc=dict(zip(TASKS,[4,3,2]));y={t:np.arange(32)%n for t,n in nc.items()};tr=np.arange(24)
    for view in ['baseline','mean','last4']:
        c=Config(view=view,epochs=2);a=fit(X,y,nc,tr,c);b=fit(X,y,nc,tr,c);assert state_hash(a)==state_hash(b)
        xx=X.copy();xx[24:]*=99;yy={t:v.copy() for t,v in y.items()}
        for t in TASKS:yy[t][24:]=(yy[t][24:]+1)%nc[t]
        assert state_hash(fit(xx,yy,nc,tr,c))==state_hash(a)
        tensor=torch.tensor(X[:2],requires_grad=True);loss=sum(v.sum() for v in a(tensor).values());loss.backward()
        assert tensor.grad[:,:512].abs().sum()>0
        selected={'baseline':(512,1280),'mean':(1280,2048),'last4':(2048,2816)}[view]
        assert tensor.grad[:,selected[0]:selected[1]].abs().sum()>0
        for other,span in {'baseline':(512,1280),'mean':(1280,2048),'last4':(2048,2816)}.items():
            if other!=view:assert tensor.grad[:,span[0]:span[1]].abs().sum()==0
        assert all(p.grad is not None for p in a.heads.parameters())
    assert len(grid())==17
    print('PASS17configs; padding/special exclusion; deterministicfit; heldoutisolation; gradientrouting')
if __name__=='__main__':main()
