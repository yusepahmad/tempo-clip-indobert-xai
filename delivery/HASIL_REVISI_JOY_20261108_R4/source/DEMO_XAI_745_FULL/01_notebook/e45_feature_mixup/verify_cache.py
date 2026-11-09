from tail_model import *
import hashlib,pandas as pd
ROOT=Path(__file__).resolve().parents[2];CACHE=ROOT/'04_hasil_eksperimen/e41_cached_tail/cache'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    assert len(CONFIGS)==6 and all(all(w>0 for w in c['loss_weights']) for c in CONFIGS)
    fixture=[dict(epoch_scores={e:0.2 for e in c['epoch_candidates']}) for c in CONFIGS]
    assert select_candidate(fixture)==(0,0)
    fixture[4]['epoch_scores'][8]=.4;assert select_candidate(fixture)==(4,8)
    xx=torch.randn(4,6,requires_grad=True);perm=torch.tensor([3,2,1,0])
    identity,order,lam=mix_features(xx,0.);assert identity is xx and order.tolist()==[0,1,2,3] and lam==1.
    left,_,_=mix_features(xx,.2,perm,1.);right,_,_=mix_features(xx,.2,perm,0.);assert torch.equal(left,xx) and torch.equal(right,xx[perm])
    logits=torch.randn(4,3,requires_grad=True);labels=torch.tensor([0,1,2,0]);ce=nn.CrossEntropyLoss(weight=torch.tensor([.5,1.,2.]))
    base=ce(logits,labels);identityloss=lam*ce(logits,labels)+(1-lam)*ce(logits,labels[order]);assert torch.equal(base,identityloss)
    assert torch.equal(torch.autograd.grad(base,logits,retain_graph=True)[0],torch.autograd.grad(identityloss,logits)[0])
    mixed,_,_=mix_features(xx,.2,perm,.3);assert torch.allclose(mixed,.3*xx+.7*xx[perm]);mixed.sum().backward();assert torch.isfinite(xx.grad).all() and (xx.grad!=0).all()
    torch.set_num_threads(8);f=json.loads((CACHE/'cache_manifest.json').read_text())
    assert f['status']=='completed' and f['labels_used_for_extraction'] is False and f['source_sha256']==sha(ROOT/'01_notebook/e41_cached_tail/extract.py')
    for n,h in f['files'].items():assert sha(CACHE/n)==h,n
    for n,h in f['inputs'].items():assert sha(ROOT/n)==h,n
    z=dict(np.load(CACHE/'front_cache.npz'));d=pd.read_csv(CACHE/'DATASET_740_TASK2_DOMAIN.csv').fillna('');assert z['sample_ids'].tolist()==d.sample_id.tolist() and len(d)==740
    assert z['h10'].shape==(740,128,768) and z['h10'].dtype==np.float32 and np.isfinite(z['h10']).all()
    a=z['attention'].astype(bool);p=z['pool_mask'].astype(bool);assert a.shape==p.shape==(740,128) and not (p & ~a).any() and p.any(axis=1).all() and (z['h10'][~a]==0).all()
    for v in [z['base_mean'],z['visual'][:,:768],z['visual'][:,768:]]:assert v.shape==(740,768) and np.isfinite(v).all() and np.allclose(np.linalg.norm(v,axis=1),1,atol=2e-5)
    nc={t:d[t].nunique() for t in TASKS};m=TailMTL(nc,CACHE).eval();checks=[]
    for i in [0,147,295,443,591,739]:
        with torch.inference_mode():v=m.features(*batch_tensors(z,np.array([i]),'cpu')).numpy()[0,-768:]
        err=float(np.abs(v-z['base_mean'][i]).max());assert err<2e-5;checks.append(dict(index=i,max_abs=err))
    CFG['mixup_alpha']=.2
    torch.set_num_threads(1);y={t:d[t].map({v:i for i,v in enumerate(sorted(d[t].unique()))}).to_numpy() for t in TASKS};tr=np.arange(24)
    h1=warm_head(z,y,nc,tr);changed={k:v.copy() for k,v in z.items()};changed['visual'][24:]*=99;changed['base_mean'][24:]*=99;yy={t:v.copy() for t,v in y.items()}
    for t in TASKS:yy[t][24:]=(yy[t][24:]+1)%nc[t]
    h2=warm_head(changed,yy,nc,tr);assert all(torch.equal(h1[k],h2[k]) for k in h1)
    m.train();features=m.features(*batch_tensors(z,np.array([0,1]),'cpu'));mixed,_,_=mix_features(features,.2);pred=m.head(mixed);loss=sum(nn.functional.cross_entropy(pred[t],torch.zeros(2,dtype=torch.long)) for t in TASKS);loss.backward()
    for prefix in ['tail.0.','tail.1.','head.shared.']+[f'head.heads.{t}.' for t in TASKS]:assert any(n.startswith(prefix) and p.grad is not None and p.grad.abs().sum()>0 for n,p in m.named_parameters()),prefix
    assert all(p.grad is None or torch.isfinite(p.grad).all() for p in m.parameters())
    report=dict(status='passed',samples=740,hashes=True,mask_and_padding=True,all_unit_features=True,tail_reconstruction=checks,heldout_warmhead_invariance=True,joint_tail_shared_all3head_gradients=True)
    (ROOT/'04_hasil_eksperimen/e45_feature_mixup_preflight.json').write_text(json.dumps(report,indent=2)+'\n');print('CACHE/PREFLIGHT AUDIT PASSED',flush=True)
if __name__=='__main__':main()
