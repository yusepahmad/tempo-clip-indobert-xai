import ast
from collections import Counter
import json
from pathlib import Path
import unittest

import numpy as np
import pandas as pd
import torch
from sklearn.model_selection import StratifiedKFold

import build
from protocol_utils import TASKS, duplicate_train, split_audit, select_epoch, sha
from tail_model import CFG, TailMTL, warm_head, batch_tensors


class ProtocolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(2)
        cls.protocol=json.loads((build.HERE/'frozen_protocol.json').read_text())
        cls.frame=pd.read_csv(build.CACHE/'DATASET_740_TASK2_DOMAIN.csv').fillna('')
        cls.ids=cls.frame.sample_id.tolist()
        cls.folds=np.array([cls.protocol['fold_mapping'][i] for i in cls.ids])

    def test_all_splits_duplicate_training_only(self):
        for fold in range(1,6):
            train=np.where(self.folds!=fold)[0];test=np.where(self.folds==fold)[0]
            labels=self.frame.iloc[train][TASKS[1]].to_numpy()
            for factor in (1,2):
                audit=split_audit(self.ids,train,[],test,factor)
                self.assertEqual(audit['train_exposures_per_epoch'],592*factor)
                for a,b in StratifiedKFold(2,shuffle=True,random_state=123).split(train,labels):
                    audit=split_audit(self.ids,train[a],train[b],test,factor)
                    self.assertEqual(audit['unique_train_samples'],296)
                    self.assertEqual(audit['train_exposures_per_epoch'],296*factor)
                    self.assertEqual(set(audit['multiplicity'].values()),{factor})

    def test_rejects_presplit_duplicates_leaks_bad_factor(self):
        for train,forbidden,factor in (([0,0],[1],2),([0,1],[1],2),([0,1],[],3)):
            with self.assertRaises(AssertionError):duplicate_train(train,forbidden,factor)
        self.assertEqual(Counter(duplicate_train([0,2,4],[1,3],2)),Counter({0:2,2:2,4:2}))

    def test_selection_macro_minimum_and_earliest_tie(self):
        traces=[dict(epochs={str(e):dict(zip(TASKS,v)) for e,v in [(0,[.9,.1,.9]),(2,[.4,.4,.4]),(4,[.4,.4,.4])]}) for _ in range(2)]
        epoch,scores=select_epoch(traces,[0,2,4])
        self.assertEqual(epoch,2)
        self.assertAlmostEqual(scores[2],.4)

    def test_payload_hashes_and_historical_model_untouched(self):
        manifest=json.loads((build.HERE/'build_manifest.json').read_text())
        self.assertEqual(sha(build.APP/'01_notebook/e42_tail_grid/tail_model.py'),manifest['payload']['tail_model.py'])
        for name,h in manifest['payload'].items():self.assertEqual(sha(build.HERE/name),h)
        for name,h in manifest['kernel_files'].items():
            self.assertEqual(sha(build.HERE/name),h)
            if name.endswith('.py'):compile((build.HERE/name).read_text(),name,'exec')
        for mode in ('smoke','full'):
            tree=ast.parse((build.HERE/mode/'launch.py').read_text())
            data=[ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign)
                  and any(isinstance(t,ast.Name) and t.id=='data' for t in n.targets)]
            self.assertEqual(set(data),{(build.HERE/name).read_text() for name in manifest['payload']})

    def test_unique_warmup_and_no_heldout_dependency(self):
        z=dict(np.load(build.CACHE/'front_cache.npz'))
        nc={t:self.frame[t].nunique() for t in TASKS}
        y={t:pd.Categorical(self.frame[t],categories=sorted(self.frame[t].unique())).codes.astype(np.int64) for t in TASKS}
        train=np.where(self.folds!=1)[0][:16]
        first=warm_head(z,y,nc,train)
        changed={k:v.copy() for k,v in z.items() if k in ('visual','base_mean')}
        heldout=np.setdiff1d(np.arange(740),train)
        for value in changed.values():value[heldout]*=5
        wrong={t:v.copy() for t,v in y.items()}
        for t in TASKS:wrong[t][heldout]=(wrong[t][heldout]+1)%nc[t]
        second=warm_head(changed,wrong,nc,train)
        self.assertTrue(all(torch.equal(first[k],second[k]) for k in first))

    def test_real_cached_model_joint_gradients(self):
        z=dict(np.load(build.CACHE/'front_cache.npz'))
        nc={t:self.frame[t].nunique() for t in TASKS}
        model=TailMTL(nc,build.CACHE)
        out=model(*batch_tensors(z,np.array([0,1]),'cpu'))
        loss=sum(torch.nn.functional.cross_entropy(out[t],torch.zeros(2,dtype=torch.long)) for t in TASKS)
        loss.backward()
        for prefix in ['tail.0.','tail.1.','head.shared.']+[f'head.heads.{t}.' for t in TASKS]:
            self.assertTrue(any(n.startswith(prefix) and p.grad is not None and p.grad.abs().sum()>0 for n,p in model.named_parameters()),prefix)
        self.assertTrue(all(p.grad is None or torch.isfinite(p.grad).all() for p in model.parameters()))

    def test_canonical_and_unmatched_updates_explicit(self):
        worker=(build.HERE/'worker.py').read_text()
        self.assertIn("canonical=predict(model,test,'cpu',False)",worker)
        self.assertIn("weights_only=True",worker)
        self.assertIn('not optimizer-step matched',self.protocol['comparison'])
        self.assertFalse(self.protocol['qwen_used'])
        self.assertEqual(self.protocol['threshold']['metric'],'macro_f1')

    def test_smoke_verifier_rejects_tampered_remote_evidence(self):
        import copy
        import tempfile
        from unittest.mock import patch
        import manage
        source=build.OUT/'smoke/raw/ci_d01_smoke/smoke.json'
        if not source.exists():self.skipTest('Real GPU smoke has not been collected yet')
        real=json.loads(source.read_text())
        # Mutations of real evidence exist ONLY inside this temporary test directory.
        with tempfile.TemporaryDirectory(prefix='ci-d01-verifier-') as tmp:
            root=Path(tmp);(root/'smoke').mkdir();folder=root/'fixture';folder.mkdir()
            with patch.object(build,'OUT',root):
                (folder/'smoke.json').write_text(json.dumps(real))
                self.assertEqual(manage.verify_smoke(folder)['status'],'verified')
                for kind in ('leak','multiplicity','frozen_head','wrong_source'):
                    bad=copy.deepcopy(real)
                    if kind=='leak':bad['arms']['2x']['split']['train_ids'][0]=bad['arms']['2x']['split']['test_ids'][0]
                    elif kind=='multiplicity':bad['arms']['2x']['training']['exposures']=40
                    elif kind=='frozen_head':bad['arms']['2x']['changes']['head.shared.']=0.
                    else:bad['source_sha256']='0'*64
                    (folder/'smoke.json').write_text(json.dumps(bad))
                    with self.assertRaises(AssertionError,msg=kind):manage.verify_smoke(folder)


if __name__=='__main__':unittest.main()
