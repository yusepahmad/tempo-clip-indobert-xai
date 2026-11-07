"""Audit inputs, splits, selected inner scores, checkpoint refits and OOF metrics."""
import json,hashlib
from pathlib import Path
from dataclasses import asdict
from collections import Counter
import numpy as np,pandas as pd,torch
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import f1_score,accuracy_score
from fusion_model import *
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'04_hasil_eksperimen/e38_l14_token'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    torch.set_num_threads(1);protocol=json.loads((OUT/'protocol.json').read_text());result=json.loads((OUT/'result.json').read_text())
    for name,digest in protocol['inputs'].items():assert sha(ROOT/name)==digest,name
    assert protocol['grid']==[asdict(c) for c in grid()]
    df=pd.read_csv(ROOT/'03_data/DATASET_740_TASK2_DOMAIN.csv').fillna('');z=np.load(ROOT/'03_data/fitur_clip_indobert_740.npz');l=np.load(ROOT/'04_hasil_eksperimen/e36_clip_l14/features.npz');p=np.load(ROOT/'04_hasil_eksperimen/e37_token_pool/features.npz');X=np.hstack([z['img'],z['txt'],l['full'],l['crop'],p['mean'],p['last4']]).astype(np.float32)
    classes=protocol['classes'];nc={t:len(classes[t]) for t in TASKS};y={t:df[t].map({c:i for i,c in enumerate(classes[t])}).to_numpy() for t in TASKS}
    oof=pd.read_csv(OUT/'oof.csv');assert len(oof)==740 and oof.sample_id.tolist()==df.sample_id.tolist() and oof.sample_id.is_unique
    count=Counter(y[TASKS[0]]);strata=[c if count[c]>=5 else -1 for c in y[TASKS[0]]];seen=[]
    for k,(tr,te) in enumerate(StratifiedKFold(5,shuffle=True,random_state=42).split(X,strata),1):
        f=json.loads((OUT/f'fold{k}.json').read_text());assert f['train_indices']==tr.tolist() and f['test_indices']==te.tolist()
        assert (oof.iloc[te].fold==k).all();seen.extend(te.tolist());inner=list(StratifiedKFold(2,shuffle=True,random_state=123).split(X[tr],y[TARGET][tr]))
        for row in f['search']:assert abs(row['mean']-np.mean(row['inner_scores']))<1e-14
        assert f['winner']==max(range(len(grid())),key=lambda j:f['search'][j]['mean'])
        c=grid()[f['winner']];assert f['config']==asdict(c)
        for j,(a,b) in enumerate(inner):
            assert f['inner_splits'][j]==dict(train=tr[a].tolist(),valid=tr[b].tolist())
            assert not set(tr[a])&set(tr[b]) and not (set(tr[a])|set(tr[b]))&set(te)
            m=fit(X,y,nc,tr[a],c);pred=predict(m,X[tr[b]])[TARGET]
            score=f1_score(y[TARGET][tr[b]],pred,labels=range(nc[TARGET]),average='macro',zero_division=0)
            assert abs(score-f['search'][f['winner']]['inner_scores'][j])<1e-12
        cp=torch.load(OUT/f'fold{k}.pt',weights_only=True);m=JointMTL(nc,c);m.load_state_dict(cp['state_dict']);m.eval()
        assert state_hash(m)==f['state_sha256']==cp['state_sha256']
        assert state_hash(fit(X,y,nc,tr,c))==state_hash(m)
        p=predict(m,X[te]);baseline=predict(fit(X,y,nc,tr,Config()),X[te])
        for t in TASKS:
            assert oof.iloc[te][t+'_truth'].tolist()==df.iloc[te][t].tolist()
            assert oof.iloc[te][t+'_pred'].tolist()==[classes[t][v] for v in p[t]]
            assert oof.iloc[te][t+'_baseline'].tolist()==[classes[t][v] for v in baseline[t]]
    assert sorted(seen)==list(range(740)) and sha(OUT/'oof.csv')==result['oof_sha256']
    for kind,suffix in [('metrics','_pred'),('baseline','_baseline')]:
        for t in TASKS:
            f1=f1_score(oof[t+'_truth'],oof[t+suffix],labels=classes[t],average='macro',zero_division=0)
            assert abs(f1-result[kind][t]['macro_f1'])<1e-12
            assert accuracy_score(oof[t+'_truth'],oof[t+suffix])==result[kind][t]['accuracy']
    report=dict(status='passed',samples=740,inputs=True,baseline_fold_match=True,inner_outer_isolation=True,selected_inner_reproduced=True,selected_models_refit_reproduced=True,all_baseline_refits_reproduced=True,all_three_task_oof=True,full_grid_rerun=False,
        files={p.name:sha(p) for p in sorted(OUT.iterdir()) if p.is_file() and p.name!='verification.json'})
    (OUT/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print('AUDIT PASSED',flush=True)
if __name__=='__main__':main()
