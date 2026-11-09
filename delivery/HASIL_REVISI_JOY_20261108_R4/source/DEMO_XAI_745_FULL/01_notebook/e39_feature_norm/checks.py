from norm_model import *
import model as baseline
def main():
    torch.set_num_threads(1);rng=np.random.default_rng(42);X=rng.normal(size=(32,2816)).astype(np.float32);nc=dict(zip(TASKS,[4,3,2]));y={t:np.arange(32)%n for t,n in nc.items()};tr=np.arange(24)
    original=baseline.fit(X[:,:1280],y,nc,tr,baseline.Config(epochs=2))
    control=fit(X,y,nc,tr,Config(epochs=2))
    for t in TASKS:assert np.array_equal(predict(original,X[:,:1280])[t],predict(control,X)[t])
    for norm in ['none','center','standard']:
        c=Config(view='both',norm=norm,epochs=2);a=fit(X,y,nc,tr,c);assert state_hash(a)==state_hash(fit(X,y,nc,tr,c))
        xx=X.copy();xx[24:]*=99;yy={t:v.copy() for t,v in y.items()}
        for t in TASKS:yy[t][24:]=(yy[t][24:]+1)%nc[t]
        assert state_hash(a)==state_hash(fit(xx,yy,nc,tr,c))
        if norm!='none':
            raw=np.hstack([X[tr,1280:2816],X[tr,512:1280]])
            assert np.allclose(a.feature_mean.numpy(),raw.mean(axis=0),atol=1e-6)
            assert np.allclose(a.feature_scale.numpy(),np.maximum(raw.std(axis=0),1e-4) if norm=='standard' else 1,atol=1e-6)
        assert all(p.grad is not None and torch.isfinite(p.grad).all() for p in a.parameters())
        constant=fit(np.ones_like(X),y,nc,tr,c);assert all(torch.isfinite(v).all() for v in constant(torch.ones((2,2816))).values())
    assert len(grid())==10
    print('PASS10configs; baselineparity; train-onlybuffers; heldoutinvariance; determinism; zero-variance; jointgradients')
if __name__=='__main__':main()
