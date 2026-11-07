import sys,unittest
from pathlib import Path
import torch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'02_web_demo'))
from mtl_engine import MTLDeliveryEngine
from xai_core import MTLHead,TASKS
class TestJointMTL(unittest.TestCase):
    def test_all_tasks_backpropagate_into_shared_layer(self):
        torch.manual_seed(42);m=MTLHead(1280,dict(zip(TASKS,[10,7,8])))
        x=torch.randn(4,1280);out=m(x);losses=[]
        for task in TASKS:
            loss=torch.nn.functional.cross_entropy(out[task],torch.zeros(4,dtype=torch.long));losses.append(loss)
            grad=torch.autograd.grad(loss,m.shared[0].weight,retain_graph=True)[0]
            self.assertGreater(grad.abs().sum().item(),0)
        (sum(losses)/3).backward()
        for head in m.heads.values():self.assertGreater(head.weight.grad.abs().sum().item(),0)
    def test_prediction_and_xai_identity_all_tasks(self):
        e=MTLDeliveryEngine();e.train(epochs=2)
        for sample,batch,expected in [(None,False,'new upload'),('test',False,'leave-one-out'),('test',True,'in-sample')]:
            e.set_context(None,'','',None,sample,batch)
            for task,p in e.predict_vector(e.X[0]).items():
                self.assertEqual(p['model_version'],'clip-indobert-mtl-v1')
                self.assertIn(expected,p['evaluation_mode'])
                self.assertEqual(e.xai_contract(task)['model_version'],p['model_version'])
        self.assertFalse(hasattr(e,'backend'))
if __name__=='__main__':unittest.main()
