from fusion_model import *
def main():
    torch.set_num_threads(1);rng=np.random.default_rng(42);X=rng.normal(size=(32,4352)).astype(np.float32);nc=dict(zip(TASKS,[4,3,2]));y={t:np.arange(32)%n for t,n in nc.items()};tr=np.arange(24)
    pairs=[('baseline','cls')]+list(product(['full','crop','both'],['mean','last4']))
    for view,text in pairs:
        c=Config(view=view,text_view=text,epochs=2);a=fit(X,y,nc,tr,c);b=fit(X,y,nc,tr,c);assert state_hash(a)==state_hash(b)
        xx=X.copy();xx[24:]*=99;yy={t:v.copy() for t,v in y.items()}
        for t in TASKS:yy[t][24:]=(yy[t][24:]+1)%nc[t]
        assert state_hash(fit(xx,yy,nc,tr,c))==state_hash(a)
        tensor=torch.tensor(X[:2],requires_grad=True);loss=sum(v.sum() for v in a(tensor).values());loss.backward()
        span={'baseline':(0,512),'full':(1280,2048),'crop':(2048,2816),'both':(1280,2816)}[view];assert tensor.grad[:,span[0]:span[1]].abs().sum()>0
        tspan={'cls':(512,1280),'mean':(2816,3584),'last4':(3584,4352)}[text];assert tensor.grad[:,tspan[0]:tspan[1]].abs().sum()>0
        for other,s in {'cls':(512,1280),'mean':(2816,3584),'last4':(3584,4352)}.items():
            if other!=text:assert tensor.grad[:,s[0]:s[1]].abs().sum()==0
        assert all(p.grad is not None for p in a.heads.parameters())
    assert len(grid())==25
    print('PASS25configs; sevenviewpairs; deterministicfit; heldoutisolation; routing; jointgradients')
if __name__=='__main__':main()
