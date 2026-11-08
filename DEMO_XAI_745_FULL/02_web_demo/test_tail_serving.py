"""Verify original checkpoint replay and the actual serving API, without retraining."""
from pathlib import Path
import io
import json
import os
import sys
import tempfile
import time
import unittest
import numpy as np
import pandas as pd
import torch
os.environ['TEMPO_BACKEND']='clip-indobert-tail-rich256'
os.environ['HF_HUB_OFFLINE']='1'
HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
TMP=tempfile.TemporaryDirectory(prefix='tempo-tail-web-')
os.environ['TEMPO_CACHE_DIR']=str(Path(TMP.name)/'cache')
os.environ['TEMPO_JOBS_DIR']=str(Path(TMP.name)/'jobs')
Path(os.environ['TEMPO_CACHE_DIR']).mkdir()
import app
from tail_rich_engine import FIELDS, VERSION

class ServingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine=app.ENG
        cls.client=app.app.test_client()
        cls.row=cls.engine.df.iloc[0]
        cls.sid=str(cls.row.sample_id)
        cls.path=app._gambar_dataset(cls.sid)
        cls.input=cls.engine.rich_inputs[cls.sid]
        cls.fields={k:cls.input[k] for k in FIELDS}

    def test_01_original_oof_all_740(self):
        e=self.engine
        reference=pd.read_csv(ROOT/'04_hasil_eksperimen/revisi_ii/experiments/RII_TAIL_RICH256/predictions.csv')
        self.assertEqual(e.df.sample_id.tolist(),reference.sample_id.tolist())
        correct={t:0 for t in e.tasks}
        for fold in range(1,6):
            indices=np.where(reference.fold.to_numpy()==fold)[0]
            self.assertEqual(len(indices),148)
            self.assertTrue(all(e._fold_for_id[str(e.df.iloc[i].sample_id)]==fold for i in indices))
            for start in range(0,len(indices),8):
                ix=indices[start:start+8]
                values=e._tm.batch_tensors(e.cache,ix,'cpu')
                with torch.no_grad():out=e._models[fold](*values)
                for task in e.tasks:
                    actual=[e.maps[task][i] for i in out[task].argmax(1).tolist()]
                    self.assertEqual(actual,reference.iloc[ix][task+'_pred'].tolist())
                    correct[task]+=sum(a==b for a,b in zip(actual,reference.iloc[ix][task+'_truth']))
            print('REPLAY_FOLD_VERIFIED',fold,flush=True)
        for task in e.tasks:
            self.assertAlmostEqual(correct[task]/740,e.manifest['evaluation']['micro_f1'][task],places=12)

    def test_02_dataset_live_front_and_visual_parity(self):
        e=self.engine
        image,text,vec=e.prepare_analysis(self.path,self.input['headline'],self.input['supporting'],self.sid,self.fields)
        e._ensure_front()
        hidden,attention,pool=e._front_inputs([e.rich_text(self.input['headline'],self.input['supporting'],self.fields)])
        cached=e.cache['h10'][0,:hidden.shape[1]]
        error=np.abs(hidden[0].numpy()[attention[0].numpy()]-cached[attention[0].numpy()]).max()
        self.assertLess(float(error),2e-4)
        e._ensure_visual()
        with torch.no_grad():visual=torch.nn.functional.normalize(e._visual(e._images(self.path)).float(),p=2,dim=1).reshape(-1).numpy()
        self.assertLess(float(np.max(np.abs(visual-image))),2e-4)
        pred=e.predict_vector(vec)
        for task in e.tasks:
            probabilities=e._prob_banyak_teks(image,[self.input['headline']],self.input['supporting'],task)[0]
            order=np.array([next(v['prob'] for v in pred[task]['semua'] if v['kelas']==label) for label in e.maps[task]])
            self.assertLess(float(np.max(np.abs(probabilities-order))),2e-4)
        self.assertEqual(len(e._active),1)
        self.assertIn('held-out',e._context['protocol'])

    def test_03_api_and_input_validation(self):
        c=self.client
        model=c.get('/api/models').get_json()
        self.assertTrue(model['ready']);self.assertEqual(model['version'],VERSION)
        self.assertEqual(len(c.get('/api/samples').get_json()),740)
        self.assertEqual(c.get('/').status_code,200)
        self.assertEqual(c.get('/api/catalog').status_code,200)
        self.assertEqual(c.post('/api/analisis',data={'sample_id':'UNKNOWN'}).status_code,400)
        with open(self.path,'rb') as f:
            response=c.post('/api/analisis',data={'headline':'Sampul baru','gambar':(io.BytesIO(f.read()),'test.jpg')},content_type='multipart/form-data')
        self.assertEqual(response.status_code,400)
        self.assertIn('deskripsi',response.get_json()['error'].lower())
        with open(self.path,'rb') as f:
            response=c.post('/api/batch',data={'gambar':(io.BytesIO(f.read()),'test.jpg')},content_type='multipart/form-data')
        self.assertEqual(response.status_code,422)

    def test_04_api_prediction_xai_same_checkpoint(self):
        response=self.client.post('/api/analisis',data={'sample_id':self.sid,'metode_atribusi':'occlusion'})
        self.assertEqual(response.status_code,200,response.get_data(as_text=True)[:500])
        data=response.get_json()
        self.assertEqual(data['snapshot']['model'],VERSION)
        self.assertEqual(data['xai']['folds'],[self.engine._fold_for_id[self.sid]])
        self.assertIn('outer-fold',data['mode'])
        self.assertEqual(set(data['snapshot']['rich_fields']),set(FIELDS))
        self.assertIsNotNone(data['heatmap_url'])
        self.assertEqual(self.client.get(data['heatmap_url']).status_code,200)
        self.assertEqual(len(data['prediksi']),3)
        for task,pred in data['prediksi'].items():
            self.assertEqual(pred['model_version'],VERSION)
            self.assertAlmostEqual(sum(r['prob'] for r in pred['semua']),1,places=5)
        scores,_,_=self.engine.atribusi_kata_lime(self.engine._context['visual'],self.input['headline'],self.input['supporting'],self.engine.tasks[1],n_sampel=24)
        self.assertTrue(scores)
        self.assertTrue(all(np.isfinite(r['kontribusi']) for r in scores))

    def test_05_actual_upload_ensemble(self):
        data={'headline':self.input['headline'],'supporting':self.input['supporting'],'metode_atribusi':'occlusion',**self.fields}
        with open(self.path,'rb') as f:data['gambar']=(io.BytesIO(f.read()),'new-cover.jpg')
        response=self.client.post('/api/analisis',data=data,content_type='multipart/form-data')
        self.assertEqual(response.status_code,200,response.get_data(as_text=True)[:500])
        result=response.get_json()
        self.assertEqual(result['snapshot']['input_source'],'upload')
        self.assertIsNone(result['label_anotator'])
        self.assertEqual(result['xai']['folds'],[1,2,3,4,5])
        self.assertIn('Not Evaluated',result['mode'])
        # Check the ensemble numerically, independently of the serving helper.
        e=self.engine
        hidden,attention,pool=e._front_inputs([e.rich_text(self.input['headline'],self.input['supporting'],self.fields)])
        visual=torch.tensor(e._context['visual']).reshape(1,-1)
        with torch.no_grad():
            outputs=[e._models[f](hidden,attention,pool,visual) for f in range(1,6)]
        for task in e.tasks:
            expected=np.mean([torch.softmax(o[task],dim=1)[0].numpy() for o in outputs],axis=0)
            actual=np.array([next(row['prob'] for row in result['prediksi'][task]['semua'] if row['kelas']==label) for label in e.maps[task]])
            np.testing.assert_allclose(actual,expected,atol=2e-5,rtol=0)
        self.assertEqual(self.client.get(result['heatmap_url']).status_code,200)

if __name__=='__main__':
    start=time.monotonic()
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(ServingTests)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    path=os.environ.get('TEMPO_WEB_VERIFICATION')
    if path:
        Path(path).write_text(json.dumps(dict(status='passed' if result.wasSuccessful() else 'failed',tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),seconds=time.monotonic()-start,model=VERSION,samples_replayed=740 if result.wasSuccessful() else None,checks=['original checkpoint SHA-256','all740 original OOF labels and Micro-F1','pinned live IndoBERT front/cache parity','pinned live CLIP full/crop/cache parity','dataset API and held-out model XAI','headline LIME and occlusion','actual new upload 5fold ensemble and XAI','missing rich inputs rejected']),indent=2)+'\n')
    raise SystemExit(0 if result.wasSuccessful() else 1)
