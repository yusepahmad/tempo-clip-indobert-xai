"""Contract and numerical tests for Revisi II evaluation."""
import unittest
import numpy as np
import pandas as pd
from scipy.stats import binomtest
from sklearn.metrics import f1_score
import evaluate as e


class EvaluationTests(unittest.TestCase):
    def setUp(self):
        self.ref=pd.DataFrame({'sample_id':['c','a','d','b'],**{t:['x','x','y','y'] for t in e.TASKS}})
        self.folds=pd.Series([1,2,1,2],index=self.ref.sample_id)
        self.frame=self.ref[['sample_id']].copy();self.frame['fold']=self.folds.loc[self.frame.sample_id].to_numpy()
        for t in e.TASKS:
            self.frame[t+'_truth']=self.ref[t];self.frame[t+'_pred']=['x','y','y','y']

    def test_alignment_is_by_id_not_position(self):
        out=e.validate_predictions(self.frame.sample(frac=1,random_state=3),self.ref,self.folds)
        self.assertEqual(out.sample_id.tolist(),['a','b','c','d'])

    def test_zero_shot_grouping_does_not_relax_trained_or_truth_contract(self):
        raw=self.frame.drop(columns='fold').iloc[::-1]
        with self.assertRaises(ValueError):e.normalize_new_predictions(raw,self.ref,self.folds)
        grouped=e.normalize_new_predictions(raw,self.ref,self.folds,no_training=True)
        self.assertEqual(grouped.fold.tolist(),[2,2,1,1])
        bad=raw.copy();bad.loc[0,e.TASKS[0]+'_truth']='y'
        with self.assertRaises(ValueError):e.normalize_new_predictions(bad,self.ref,self.folds,no_training=True)
        bad=self.frame.copy();bad.loc[0,'fold']=9
        with self.assertRaises(ValueError):e.normalize_new_predictions(bad,self.ref,self.folds,no_training=True)

    def test_duplicate_missing_and_unknown_ids_rejected(self):
        for bad in [self.frame.iloc[[0,0,2,3]],self.frame.iloc[:3],self.frame.assign(sample_id=['new','a','d','b'])]:
            with self.assertRaises(ValueError):e.validate_predictions(bad,self.ref,self.folds)

    def test_wrong_fold_truth_and_label_rejected(self):
        bad=self.frame.copy();bad.loc[0,'fold']=9
        with self.assertRaises(ValueError):e.validate_predictions(bad,self.ref,self.folds)
        bad=self.frame.copy();bad.loc[0,e.TASKS[0]+'_truth']='y'
        with self.assertRaises(ValueError):e.validate_predictions(bad,self.ref,self.folds)
        bad=self.frame.copy();bad.loc[0,e.TASKS[0]+'_pred']='unknown'
        with self.assertRaises(ValueError):e.validate_predictions(bad,self.ref,self.folds)

    def test_fixed_class_macro_and_missing_class_prediction(self):
        y=['x']*8+['y']*2;p=['x']*10
        self.assertAlmostEqual(e.metrics(y,p,['x','y'])['macro_f1'],f1_score(y,p,average='macro'))
        self.assertAlmostEqual(e.matrix_macro(np.array([[8,0],[2,0]])),4/9)
        lo,hi=e.bootstrap_macro(y,p,['x','y'])
        self.assertTrue(0<=lo<=hi<=1)

    def test_wilson_independent_boundary(self):
        self.assertAlmostEqual(e.wilson(0,10)[0],0.)
        self.assertAlmostEqual(e.wilson(10,10)[1],1.)
        self.assertAlmostEqual(e.wilson(5,10)[0]+e.wilson(5,10)[1],1.)
        with self.assertRaises(ValueError):e.wilson(11,10)

    def test_paired_identity_and_asymmetric_direction(self):
        y=['a']*40+['b']*40
        a=y.copy();b=['a']*80
        same=e.paired_comparison(y,a,a,['a','b'])
        self.assertEqual(same['mcnemar_exact_p'],1)
        self.assertEqual(same['macro_delta_ci_low'],0)
        forward=e.paired_comparison(y,a,b,['a','b'])
        reverse=e.paired_comparison(y,b,a,['a','b'])
        self.assertAlmostEqual(forward['macro_f1_delta'],-reverse['macro_f1_delta'])
        self.assertLess(forward['macro_delta_ci_high'],0)
        self.assertGreater(reverse['macro_delta_ci_low'],0)
        self.assertAlmostEqual(forward['mcnemar_exact_p'],binomtest(40,40).pvalue)

    def test_bootstrap_deterministic_and_contains_point_in_example(self):
        y=['x']*15+['y']*15;p=['x']*12+['y']*3+['x']*3+['y']*12
        a=e.bootstrap_macro(y,p,['x','y']);b=e.bootstrap_macro(y,p,['x','y'])
        self.assertEqual(a,b)
        self.assertLess(a[0],.8);self.assertGreater(a[1],.8)

    def test_holm_monotonic_independent_expected_values(self):
        np.testing.assert_allclose(e.holm([.04,.01,.03]),[.06,.03,.06])

    def test_alias_signature_ignores_order_not_predictions(self):
        self.assertEqual(e.signature(self.frame),e.signature(self.frame.iloc[::-1]))
        changed=self.frame.copy();changed.loc[0,e.TASKS[0]+'_pred']='y'
        self.assertNotEqual(e.signature(self.frame),e.signature(changed))


if __name__=='__main__':unittest.main()
