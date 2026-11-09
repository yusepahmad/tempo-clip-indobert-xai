"""Audit fixed protocol, inner-only epoch selection and OOF; no GPU rerun."""
import json,hashlib
from pathlib import Path
from collections import Counter
import numpy as np,pandas as pd,torch
from sklearn.model_selection import StratifiedKFold,train_test_split
from sklearn.metrics import f1_score,accuracy_score
from worker import TASKS,TARGET,CFG
ROOT=Path(__file__).resolve().parents[2]
def main():
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument('output',type=Path);args=ap.parse_args();out=args.output
    csv=ROOT/'03_data/DATASET_740_TASK2_DOMAIN.csv';df=pd.read_csv(csv).fillna('');protocol=json.loads((out/'protocol.json').read_text());result=json.loads((out/'result.json').read_text())
    assert protocol['config']==CFG and not protocol['smoke'] and protocol['allocated_gpu_count']<=2
    assert hashlib.sha256(csv.read_bytes()).hexdigest()==protocol['csv_sha256']
    assert hashlib.sha256(Path(__file__).with_name('worker.py').read_bytes()).hexdigest()==protocol['worker_sha256']
    classes=protocol['classes'];y={t:df[t].map({v:i for i,v in enumerate(classes[t])}).to_numpy() for t in TASKS};counts=Counter(y[TASKS[0]]);strata=[c if counts[c]>=5 else -1 for c in y[TASKS[0]]]
    oof=pd.read_csv(out/'oof.csv');assert len(oof)==740 and oof.sample_id.tolist()==df.sample_id.tolist() and oof.sample_id.is_unique
    checkpoints=[]
    for k,(tr,te) in enumerate(StratifiedKFold(5,shuffle=True,random_state=42).split(df,strata),1):
        f=json.loads((out/f'fold{k}.json').read_text());a,b=train_test_split(tr,test_size=.2,random_state=123,stratify=y[TARGET][tr])
        assert f['train']==tr.tolist() and f['test']==te.tolist() and f['inner_train']==a.tolist() and f['inner_valid']==b.tolist()
        assert not set(a)&set(b) and not (set(a)|set(b))&set(te)
        assert [r['epoch'] for r in f['epochs']]==list(range(13))
        assert f['selected_epoch']==int(np.argmax([r['inner_macro_f1'] for r in f['epochs']]))==result['selected_epochs'][k-1]
        assert (oof.iloc[te].fold==k).all();p=np.load(out/f'fold{k}_predictions.npz');assert np.array_equal(p['indices'],te)
        for t in TASKS:
            assert oof.iloc[te][t+'_truth'].tolist()==df.iloc[te][t].tolist()
            assert oof.iloc[te][t+'_pred'].tolist()==[classes[t][v] for v in p[t]]
        cp_path=out/f'fold{k}_delta.pt'
        if cp_path.exists():
            cp=torch.load(cp_path,map_location='cpu',weights_only=True)
            assert cp['train']==tr.tolist() and cp['test']==te.tolist() and cp['epoch']==f['selected_epoch'] and cp['config']==CFG
            assert set(cp['delta'])==set(protocol['trainable'])
            for n,v in cp['delta'].items():
                assert torch.isfinite(v).all(),n
                assert n.startswith(('head.','visual.transformer.resblocks.10.','visual.transformer.resblocks.11.','visual.ln_post.','bert.encoder.layer.10.','bert.encoder.layer.11.')) or n=='visual.proj',n
            checkpoints.append(k)
    for t in TASKS:
        score=f1_score(oof[t+'_truth'],oof[t+'_pred'],labels=classes[t],average='macro',zero_division=0)
        assert abs(score-result['metrics'][t]['macro_f1'])<1e-12
        assert accuracy_score(oof[t+'_truth'],oof[t+'_pred'])==result['metrics'][t]['accuracy']
    report=dict(status='passed',samples=740,inner_epoch_selection=True,baseline_splits_match=True,source_hash=True,metrics_all_three_tasks=True,delta_checkpoint_folds_audited=checkpoints,training_rerun=False,checkpoint_prediction_rerun=False,
                limits='Protocol/output audit only; full encoder training and checkpoint forward are not reproduced here',files={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir() if p.is_file() and p.name!='verification.json'})
    (out/'verification.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
if __name__=='__main__':main()
