from l14_model import *
def main():
    torch.set_num_threads(1);rng=np.random.default_rng(42);X=rng.normal(size=(32,2816)).astype(np.float32);nc=dict(zip(TASKS,[4,3,2]));y={t:np.arange(32)%n for t,n in nc.items()};tr=np.arange(24)
    for view in ['baseline','full','crop','both']:
        c=Config(view=view,epochs=2);a=fit(X,y,nc,tr,c);b=fit(X,y,nc,tr,c);assert state_hash(a)==state_hash(b)
        xx=X.copy();xx[24:]*=99;yy={t:v.copy() for t,v in y.items()}
        for t in TASKS:yy[t][24:]=(yy[t][24:]+1)%nc[t]
        assert state_hash(fit(xx,yy,nc,tr,c))==state_hash(a)
        tensor=torch.tensor(X[:2],requires_grad=True);loss=sum(v.sum() for v in a(tensor).values());loss.backward()
        assert tensor.grad[:,512:1280].abs().sum()>0
        selected={'baseline':(0,512),'full':(1280,2048),'crop':(2048,2816),'both':(1280,2816)}[view]
        assert tensor.grad[:,selected[0]:selected[1]].abs().sum()>0
        assert tensor.grad[:,1280:].abs().sum()==0 if view=='baseline' else tensor.grad[:,:512].abs().sum()==0
    assert len(grid())==25
    print('PASS25configs; fourfeatureviews; deterministicfit; heldoutisolation; correctvisual/text gradientrouting')
if __name__=='__main__':main()
