"""Audit actual E01 prompt AST with objects that prohibit all gold access."""
import ast
import importlib.util
import unittest
from pathlib import Path
import pandas as pd
from evaluate import sha,write_json


def audit(workspace):
    repo=Path(workspace).resolve();source=repo/'docs/server-recovery/2026-10-10/01_notebook/kaggle_e01/full/e01_vlm.py'
    spec=importlib.util.spec_from_file_location('e01_invariance',source);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    tree=ast.parse(source.read_text());calls={}
    for node in ast.walk(tree):
        if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name) and node.targets[0].id in ['teks_a','teks_b']:
            if isinstance(node.value,ast.Call) and isinstance(node.value.func,ast.Name) and node.value.func.id=='generate':
                calls[node.targets[0].id]=ast.Expression(body=node.value.args[1])
    assert set(calls)=={'teks_a','teks_b'}
    data=pd.read_csv(repo/'DEMO_XAI_745_FULL/03_data/DATASET_740_TASK2_DOMAIN.csv').fillna('')
    access=[]
    class WhitelistRow:
        def __init__(self,fields):object.__setattr__(self,'fields',fields)
        def __getattribute__(self,name):
            if name not in {'image_path','sample_id','headline_verified','supporting_text_verified'}:
                raise AssertionError('Forbidden gold/annotation attribute accessed: '+name)
            access.append(name);return object.__getattribute__(self,'fields')[name]
    rows=[WhitelistRow(r) for r in data.to_dict('records')]
    scope={'bagian':rows,'PROMPT_A':module.PROMPT_A,'prompt_b':module.prompt_b}
    prompts={name:eval(compile(ast.fix_missing_locations(expr),'<actual_e01_prompt_ast>','eval'),scope) for name,expr in calls.items()}
    assert len(prompts['teks_a'])==len(prompts['teks_b'])==740
    for i,r in enumerate(data.itertuples()):assert prompts['teks_b'][i]==module.prompt_b(r.headline_verified,r.supporting_text_verified)
    return dict(status='passed',samples=740,generator_sha256=sha(source),
                actual_prompt_ast_executed=True,allowed_prompt_row_attributes=sorted(set(access)),
                forbidden_gold_fields_raised_on_access=True,
                limitation='Proves these source prompt expressions do not access gold; does not imply full labeled CSV was never loaded, historical runtime attestation, or independent human label validity')


class ProvenanceTests(unittest.TestCase):
    def test_workspace_actual_prompts_never_access_gold(self):
        repo=Path(__file__).resolve().parents[3]
        if not (repo/'docs/server-recovery').exists():self.skipTest('Source-workspace-only test; report ships with package')
        report=audit(repo);self.assertEqual(report['samples'],740)


if __name__=='__main__':
    repo=Path(__file__).resolve().parents[3]
    report=audit(repo);write_json(repo/'docs/revisi-ii/PROMPT_GOLD_INVARIANCE.json',report)
    print('Actual E01 prompt AST: 740 rows, only headline/supporting accessed; gold access forbidden')
