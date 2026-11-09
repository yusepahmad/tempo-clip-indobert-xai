"""CPU checks before spending GPU quota on five-fold QLoRA."""
import ast
import base64
import hashlib
import json
import unittest
from unittest.mock import patch
import tempfile
from pathlib import Path

import numpy as np
from sklearn.model_selection import StratifiedKFold, train_test_split
import pandas as pd
import torch

import build
import results


class ProtocolTests(unittest.TestCase):
    def test_launcher_payloads(self):
        protocol=(build.OUT/'frozen_protocol.json').read_bytes()
        worker=(build.HERE/'worker.py').read_bytes()
        for fold in range(1,6):
            tree=ast.parse((build.HERE/f'fold{fold}/launch.py').read_text())
            values={node.targets[0].id:base64.b64decode(ast.literal_eval(node.value.args[0]))
                    for node in tree.body if isinstance(node,ast.Assign) and isinstance(node.targets[0],ast.Name)
                    and node.targets[0].id in ('protocol','worker')}
            self.assertEqual(values['protocol'],protocol)
            self.assertEqual(values['worker'],worker)
            compile(values['worker'],'worker.py','exec')

    def test_fixed_splits_and_reuse(self):
        protocol=json.loads((build.OUT/'frozen_protocol.json').read_text())
        pilot=json.loads(build.PILOT.read_text())
        frame=pd.read_csv(build.APP/'03_data/DATASET_740_TASK2_DOMAIN.csv')
        names=sorted(frame.task1_issue.unique())
        y=pd.Categorical(frame.task1_issue,categories=names).codes
        for fold,(train,test) in enumerate(StratifiedKFold(5,shuffle=True,random_state=42).split(np.zeros(740),y),1):
            inner,validation=train_test_split(train,test_size=.2,stratify=y[train],random_state=42+fold)
            self.assertEqual((len(inner),len(validation),len(test)),(473,119,148))
            self.assertFalse(set(inner)&set(validation))
            self.assertFalse(set(train)&set(test))
            self.assertTrue(all(protocol['fold_mapping'][frame.sample_id.iloc[i]]==fold for i in test))
            if fold==1:
                self.assertEqual(set(frame.sample_id.iloc[inner]),set(pilot['split']['inner_train_ids']))
                self.assertEqual(set(frame.sample_id.iloc[validation]),set(pilot['split']['inner_validation_ids']))
                chosen=max(pilot['history'][:3],key=lambda r:(r['minimum'],r['mean']))
                self.assertEqual(chosen['epoch'],3)

    def test_adapter_reset_ignores_frozen_quant_buffers(self):
        parsed=ast.parse((build.HERE/'worker.py').read_text())
        functions=[node for node in parsed.body if isinstance(node,ast.FunctionDef) and node.name in ('capture_adapter','restore_adapter')]
        scope={'torch':torch}
        exec(compile(ast.Module(body=functions,type_ignores=[]),'adapter_helpers','exec'),scope)
        model=torch.nn.Module()
        model.lora_A=torch.nn.Parameter(torch.randn(4,3))
        model.frozen=torch.nn.Parameter(torch.randn(3),requires_grad=False)
        model.register_buffer('quant_map',torch.arange(7.0))
        state=scope['capture_adapter'](model)
        self.assertEqual(set(state),{'lora_A'})
        with torch.no_grad():model.lora_A.add_(5)
        scope['restore_adapter'](model,state)
        self.assertTrue(torch.equal(model.lora_A,state['lora_A']))
        self.assertTrue(torch.equal(model.quant_map,torch.arange(7.0)))
        with self.assertRaises(AssertionError):scope['restore_adapter'](model,{'unexpected':torch.zeros(1)})

    def test_selection_and_checkpoint_order(self):
        source=(build.HERE/'worker.py').read_text()
        reset=source.index('    restore_adapter(model, initial_state)')
        refit=source.index('    for epoch in range(1, selected_epoch + 1):')
        outer=source.index('    probabilities = predict(test)')
        self.assertLess(reset,refit)
        self.assertLess(refit,outer)
        self.assertIn('seed_all(42000 + FOLD)',source[reset:refit])
        self.assertIn('save_checkpoint("inner"',source)
        self.assertIn('save_checkpoint("refit"',source)
        self.assertIn('if FOLD != 1:\n        return None',source)

    def test_result_verifier_rejects_tampered_labels(self):
        # Synthetic artifacts are confined to a temporary directory; they are
        # never part of the research outputs or OOF ranking.
        with tempfile.TemporaryDirectory(prefix='tempo-e14-verifier-') as temp:
            root=Path(temp);folder=root/'fold1';folder.mkdir()
            (root/'frozen_protocol.json').write_bytes((build.OUT/'frozen_protocol.json').read_bytes())
            protocol=json.loads((root/'frozen_protocol.json').read_text())
            pilot=json.loads(build.PILOT.read_text())
            data=pd.read_csv(build.APP/'03_data/DATASET_740_TASK2_DOMAIN.csv')
            test=[k for k,v in protocol['fold_mapping'].items() if v==1]
            train=[k for k,v in protocol['fold_mapping'].items() if v!=1]
            split={'inner_train_ids':pilot['split']['inner_train_ids'],
                   'inner_validation_ids':pilot['split']['inner_validation_ids'],
                   'outer_train_ids':train,'outer_test_ids':test}
            results.write(folder/'split.json',split)
            df=data.set_index('sample_id').loc[test].reset_index()
            pred=pd.DataFrame({'sample_id':test,'fold':1})
            classes={t:sorted(data[t].unique().tolist()) for t in results.TASKS}
            for task in results.TASKS:
                pred[task+'_truth']=df[task]
                pred[task+'_pred']=df[task]
                for name in classes[task]:pred[task+'_p_'+name]=(df[task]==name).astype(float)
            pred.to_csv(folder/'predictions.csv',index=False)
            audits=''.join(json.dumps({'sample_id':sample_id,'task':task})+'\n' for sample_id in data.sample_id for task in results.TASKS)
            (folder/'input_audit.jsonl').write_text(audits)
            history=[{'epoch':i,'minimum':i/10,'mean':i/10,'validation_micro_f1':{t:i/10 for t in results.TASKS}} for i in range(1,4)]
            result={'status':'complete','smoke':False,'fold':1,
                    'protocol_sha256':results.sha(root/'frozen_protocol.json'),
                    'source_sha256':results.sha(build.HERE/'worker.py'),
                    'initial_adapter_sha256':'0'*64,'adapter_sha256':'1'*64,
                    'data_sha256':protocol['dataset_sha256'],
                    'predictions_sha256':results.sha(folder/'predictions.csv'),
                    'split_sha256':results.sha(folder/'split.json'),
                    'input_audit_sha256':results.sha(folder/'input_audit.jsonl'),
                    'history':history,'selected_epoch':3,'refit_history':[{'epoch':i} for i in range(1,4)],
                    'outer_train_samples':592,'samples':148,'reused_pilot_inner_history':True,
                    'classes':classes,'micro_f1':{t:1.0 for t in results.TASKS}}
            results.write(folder/'result.json',result)
            with patch.object(build,'OUT',root):
                self.assertEqual(results.verify_fold(1)['status'],'verified')
                # Rehash the corrupt CSV as well, so the verifier must detect
                # semantic label mismatch rather than just a changed checksum.
                task=results.TASKS[0]
                pred.loc[0,task+'_truth']='incorrect_annotation'
                pred.to_csv(folder/'predictions.csv',index=False)
                result['predictions_sha256']=results.sha(folder/'predictions.csv')
                results.write(folder/'result.json',result)
                with self.assertRaises(AssertionError):results.verify_fold(1)


if __name__=='__main__':unittest.main()
