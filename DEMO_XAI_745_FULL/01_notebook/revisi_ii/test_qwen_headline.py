"""Verify the literal R21 input intervention and isolation from historical jobs."""
import ast
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import json

import manage_qwen_basic as basic
import manage_qwen_headline as headline


class HeadlineTests(unittest.TestCase):
    def test_new_job_cannot_overwrite_old_basic_job(self):
        self.assertNotEqual(headline.OUT,basic.OUT)
        self.assertEqual(headline.OUT.name,'qwen_headline_jobs')
        self.assertNotEqual(headline.REF,basic.REF)
        source=headline.derive().read_text()
        self.assertIn('rii_qwen_headline_fold',source)
        self.assertNotIn('rii_qwen_basic_fold',source)

    def test_prompt_ignores_supporting_text_and_all_gold_labels(self):
        tree=ast.parse(headline.derive().read_text())
        assignments=[node for node in ast.walk(tree) if isinstance(node,ast.Assign)
                     and any(isinstance(t,ast.Name) and t.id=='common' for t in node.targets)]
        self.assertEqual(len(assignments),1)
        expression=ast.Expression(assignments[0].value)
        compiled=compile(ast.fix_missing_locations(expression),'<headline prompt>','eval')
        class Row:
            headline_verified='Satu judul'
            def __getattr__(self,name):raise AssertionError('Forbidden prompt field '+name)
        prompt=eval(compiled,{'row':Row()})
        self.assertIn('Satu judul',prompt)
        self.assertNotIn('Teks pendukung',prompt)
        self.assertNotIn('supporting_text_verified',headline.derive().read_text())

    def test_build_records_literal_inputs_and_unchanged_training_recipe(self):
        with tempfile.TemporaryDirectory() as temp,patch.object(headline,'OUT',Path(temp)):
            root=headline.build('full')
            protocol=json.loads((Path(temp)/'full/protocol.json').read_text())
            metadata=json.loads((root/'kernel-metadata.json').read_text())
            self.assertEqual(protocol['input_fields'],['image384','headline_verified'])
            self.assertIn('supporting_text_verified',protocol['excluded'])
            self.assertEqual(protocol['fixed_epochs'],[3,1,3,2,3])
            self.assertEqual(protocol['wall_seconds_limit'],32400)
            self.assertTrue(metadata['is_private'])
            compile((root/'launch.py').read_text(),'<launcher>','exec')

    def test_existing_basic_protocols_still_match_saved_remote_protocols(self):
        for mode in ['smoke','full']:
            expected=json.loads((basic.OUT/mode/'raw/protocol.json').read_text())
            actual=json.loads((basic.OUT/mode/'protocol.json').read_text())
            self.assertEqual(actual,expected)


if __name__=='__main__':unittest.main()
