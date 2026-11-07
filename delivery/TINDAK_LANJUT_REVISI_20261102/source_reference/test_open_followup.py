"""Prospective data guards, known kappa, and a dry-run collector publication."""
import csv
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
import pandas as pd
from sklearn.metrics import cohen_kappa_score
import label_blind_bundle as blind
import followup_r21
import watch_qwen_basic

REPO=Path(__file__).resolve().parents[3]
PACKAGE=REPO/'delivery/HASIL_REVISI_JOY_20261102_R3_FULL'
BUNDLE=REPO/'delivery/TINDAK_LANJUT_REVISI_20261102/R22_INPUT_TANPA_LABEL'


class FollowupTests(unittest.TestCase):
    def test_exported_bundle_has_no_gold_columns(self):
        result=blind.verify(BUNDLE);self.assertEqual(result['samples'],740)
        self.assertEqual(result['columns'],blind.FIELDS)

    def test_unlisted_input_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)/'inputs';shutil.copytree(BUNDLE,root,copy_function=shutil.copy2)
            (root/'hidden_gold.csv').write_text('sample_id,gold\none,x\n')
            with self.assertRaises(AssertionError):blind.verify(root)

    def test_gold_header_rejected_even_if_file_hash_updated(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)/'inputs';shutil.copytree(BUNDLE,root)
            data=pd.read_csv(root/'inputs.csv');data['task2_domain_sumber']='FORBIDDEN'
            data.to_csv(root/'inputs.csv',index=False)
            m=json.loads((root/'MANIFEST_INPUT.json').read_text());m['files']['inputs.csv']=blind.sha(root/'inputs.csv')
            (root/'MANIFEST_INPUT.json').write_text(json.dumps(m))
            with self.assertRaises(AssertionError):blind.verify(root)

    def test_kappa_point_matches_independent_sklearn(self):
        a=['a','b','c','a','b','c']*20;b=['a','b','b','a','c','c']*20
        result=followup_r21.kappa_ci(a,b,['a','b','c'],resamples=2000)
        self.assertAlmostEqual(result['kappa'],cohen_kappa_score(a,b))
        self.assertLess(result['kappa_ci_low'],result['kappa']);self.assertGreater(result['kappa_ci_high'],result['kappa'])

    def test_pending_basic_not_filled_with_smoke(self):
        with tempfile.TemporaryDirectory() as temp:
            result=followup_r21.build(PACKAGE,Path(temp))
            self.assertEqual(result['pending_rows'],3)
            rows=pd.read_csv(Path(temp)/'R21_MATRIX_DAN_ZERO_SHOT.csv')
            basic=rows[rows.experiment.eq('RII_QWEN_QLORA_BASIC')]
            self.assertTrue(basic.macro_f1.isna().all());self.assertTrue(basic.samples.eq(0).all())

    def test_collection_publication_pipeline_on_known_fixture_only(self):
        # This fixture is an existing comparator, not new training; it is
        # confined to TemporaryDirectory and never published as research data.
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);app=root/'app';source=app/'04_hasil_eksperimen/revisi_ii/experiments/RII_QWEN_QLORA_BASIC'
            source.mkdir(parents=True)
            shutil.copy2(PACKAGE/'inputs/predictions/MICRO_E14_joint_qlora_oof.csv',source/'predictions.csv')
            (source/'result.json').write_text(json.dumps(dict(status='TEST_FIXTURE_NOT_REAL_TRAINING')))
            with patch.object(watch_qwen_basic.jobs,'APP',app):watch_qwen_basic.publish(PACKAGE,root/'result')
            table=pd.read_csv(root/'result/R21_MATRIX_DAN_ZERO_SHOT.csv')
            self.assertEqual(len(table),18);self.assertTrue(table.status.eq('Available').all())
            paired=pd.read_csv(root/'result/R21_PAIRED_BASIC_VS_RICH.csv')
            self.assertTrue(paired.macro_f1_delta.abs().lt(1e-12).all())


if __name__=='__main__':unittest.main()
