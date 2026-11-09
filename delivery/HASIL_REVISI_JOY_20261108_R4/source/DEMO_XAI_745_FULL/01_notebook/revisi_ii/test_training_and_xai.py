import unittest
import numpy as np
import torch
from evaluate import TASKS
from train_frozen_controls import fit
from explain_e42 import rollout_from_attention,inverse_center_map


class TrainingAndXAITests(unittest.TestCase):
    def test_training_is_invariant_to_heldout_labels_and_features(self):
        torch.set_num_threads(1)
        x=np.random.default_rng(4).normal(size=(12,5)).astype('float32')
        y={t:np.array([0,1]*6) for t in TASKS};classes={t:2 for t in TASKS};train=np.arange(8)
        a=fit(x,y,classes,train)
        changed=x.copy();changed[8:]*=1000
        labels={t:v.copy() for t,v in y.items()}
        for t in TASKS:labels[t][8:]=1-labels[t][8:]
        b=fit(changed,labels,classes,train)
        self.assertTrue(all(torch.equal(a.state_dict()[k],b.state_dict()[k]) for k in a.state_dict()))

    def test_single_task_does_not_use_other_tasks_labels(self):
        torch.set_num_threads(1);x=np.ones((8,4),dtype='float32')
        y={t:np.array([0,1]*4) for t in TASKS};classes={t:2 for t in TASKS};tr=np.arange(8)
        a=fit(x,y,classes,tr,tasks=(TASKS[0],))
        y[TASKS[1]]=1-y[TASKS[1]];y[TASKS[2]]=1-y[TASKS[2]]
        b=fit(x,y,classes,tr,tasks=(TASKS[0],))
        self.assertTrue(all(torch.equal(a.state_dict()[k],b.state_dict()[k]) for k in a.state_dict()))

    def test_rollout_matrix_product_matches_independent_formula(self):
        a=np.array([[.1,.7,.2],[.2,.3,.5],[.4,.2,.4]],dtype='float32')
        b=np.array([[.6,.1,.3],[.4,.4,.2],[.1,.1,.8]],dtype='float32')
        aa=(a+np.eye(3))/2;bb=(b+np.eye(3))/2
        np.testing.assert_allclose(rollout_from_attention([torch.tensor(a),torch.tensor(b)]),(bb@aa)[0,1:],atol=1e-7)
        with self.assertRaises(ValueError):rollout_from_attention([])

    def test_rollout_maps_only_preprocessed_center_region(self):
        mapped=inverse_center_map(np.ones(16,dtype='float32'),100,200)
        self.assertEqual(mapped.shape,(200,100));self.assertTrue((mapped[:50]==0).all());self.assertTrue((mapped[50:150]==1).all())
        cropped=inverse_center_map(np.ones(16,dtype='float32'),100,200,(0,40,100,188))
        self.assertTrue((cropped[:64]==0).all())
        with self.assertRaises(ValueError):inverse_center_map(np.ones(5),10,10)


if __name__=='__main__':unittest.main()
