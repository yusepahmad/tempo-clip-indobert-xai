"""Read-only checkpoint replay from an E42 annex, without encoder downloads."""
import argparse
import json
from pathlib import Path
import sys
import numpy as np
import pandas as pd
import torch
from evaluate import TASKS, sha, write_json


def run(workspace, output):
    root=Path(workspace).resolve();app=root/'DEMO_XAI_745_FULL'
    sys.path.insert(0,str(app/'01_notebook/e42_tail_grid'))
    import tail_model as tm
    torch.set_num_threads(2)
    cache=app/'04_hasil_eksperimen/e41_cached_tail/cache'
    folder=app/'04_hasil_eksperimen/e42_tail_grid'
    manifest=json.loads((root/'MANIFEST_SHA256.json').read_text())['files']
    for name,digest in manifest.items():
        assert sha(root/name)==digest,name
    df=pd.read_csv(cache/'DATASET_740_TASK2_DOMAIN.csv').fillna('')
    z=dict(np.load(cache/'front_cache.npz'))
    assert z['sample_ids'].tolist()==df.sample_id.tolist()
    oof=pd.read_csv(folder/'oof.csv').set_index('sample_id').loc[df.sample_id].reset_index()
    classes={task:sorted(df[task].unique()) for task in TASKS}
    seen=set();checkpoints=[];differences={task:0 for task in TASKS}
    for fold in range(1,6):
        path=folder/f'fold{fold}.pt'
        cp=torch.load(path,map_location='cpu',weights_only=True)
        assert cp['classes']==classes
        tr,te=cp['train_indices'],cp['test_indices']
        assert not set(tr)&set(te) and not seen&set(te)
        seen.update(te)
        assert oof.iloc[te].fold.eq(fold).all()
        tm.CFG.clear();tm.CFG.update(cp['config'])
        model=tm.TailMTL({t:len(classes[t]) for t in TASKS},cache).eval()
        model.load_state_dict(cp['state_dict'],strict=True)
        with torch.inference_mode():
            for start in range(0,len(te),32):
                ix=te[start:start+32]
                predictions=model(*tm.batch_tensors(z,ix,'cpu'))
                for task in TASKS:
                    pred=np.asarray(classes[task])[predictions[task].argmax(1).numpy()]
                    differences[task]+=int((pred!=oof.iloc[ix][task+'_pred'].to_numpy()).sum())
        checkpoints.append(dict(fold=fold,sha256=sha(path),test_samples=len(te)))
        print('E42 REPLAY',fold,'passed',flush=True)
    assert len(seen)==740 and not any(differences.values()),differences
    report=dict(status='verified',precision='CPU FP32',samples=740,checkpoint_folds=5,
                differences=differences,checkpoints=checkpoints,manifest_files_verified=len(manifest),
                training=False,encoder_download=False)
    write_json(output,report);print(json.dumps(report,indent=2));return report


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--workspace',required=True,type=Path);ap.add_argument('--output',required=True,type=Path)
    args=ap.parse_args();run(args.workspace,args.output)
