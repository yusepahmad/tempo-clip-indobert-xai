from mmoe_model import *
import model as baseline
import io

def main():
    torch.set_num_threads(1);rng=np.random.default_rng(42);X=rng.normal(size=(32,4352)).astype(np.float32);nc=dict(zip(TASKS,[4,3,2]));y={t:np.arange(32)%n for t,n in nc.items()};tr=np.arange(24)
    old=baseline.fit(X[:,:1280],y,nc,tr,baseline.Config(epochs=2));control=fit(X,y,nc,tr,Config(epochs=2))
    with torch.no_grad():
        for t in TASKS:assert torch.equal(old(torch.tensor(X[:,:1280]))[t],control(torch.tensor(X))[t])
    bad=[dict(zip(TASKS,[.8,.9,.1]))]*2;balanced=[dict(zip(TASKS,[.6,.6,.6]))]*2
    assert balanced_objective(balanced)>balanced_objective(bad)
    for e in [2,4]:
        c=Config(view='both',text_view='mean',experts=e,hidden=64,epochs=2)
        a=fit(X,y,nc,tr,c);assert state_hash(a)==state_hash(fit(X,y,nc,tr,c))
        xx=X.copy();xx[24:]*=99;yy={t:v.copy() for t,v in y.items()}
        for t in TASKS:yy[t][24:]=(yy[t][24:]+1)%nc[t]
        assert state_hash(a)==state_hash(fit(xx,yy,nc,tr,c))
        tensor=torch.tensor(X[:4],requires_grad=True)
        for t in TASKS:
            a.zero_grad();tensor.grad=None
            nn.CrossEntropyLoss()(a(tensor)[t],torch.tensor(y[t][:4])).backward()
            for expert in a.shared:assert expert[0].weight.grad is not None and expert[0].weight.grad.abs().sum()>0
            assert a.gates[t].weight.grad.abs().sum()>0 and a.heads[t].weight.grad.abs().sum()>0
            assert torch.isfinite(tensor.grad).all() and tensor.grad[:,1280:2816].abs().sum()>0 and tensor.grad[:,2816:3584].abs().sum()>0
            assert tensor.grad[:,:1280].abs().sum()==0 and tensor.grad[:,3584:].abs().sum()==0
            for other in TASKS:
                if other!=t:assert a.heads[other].weight.grad is None
        features=torch.cat([tensor[:,1280:2816]*c.visual_weight,tensor[:,2816:3584]],dim=1)
        for gate in a.gates.values():
            probs=torch.softmax(gate(features),dim=1);assert torch.isfinite(probs).all() and (probs>=0).all() and torch.allclose(probs.sum(dim=1),torch.ones(4))
        buf=io.BytesIO();torch.save(a.state_dict(),buf);buf.seek(0);restored=JointMTL(nc,c);restored.load_state_dict(torch.load(buf,weights_only=True));restored.eval();assert state_hash(restored)==state_hash(a)
    assert len(grid())==26
    print('PASS26configs; exactbaseline; balancedselection; sharedexpertgradients-eachtask; simplexgates; heldoutisolation; determinism; XAIinputgradient; checkpointparity')
if __name__=='__main__':main()
