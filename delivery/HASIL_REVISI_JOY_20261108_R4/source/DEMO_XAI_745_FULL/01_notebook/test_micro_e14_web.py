"""CPU/API and Chromium fixtures; NONE of these are a GPU benchmark."""
import io
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from urllib.parse import urlparse

HERE = Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'02_web_demo'))
TMP = tempfile.TemporaryDirectory(prefix='tempo_e14_test_')
os.environ['TEMPO_BACKEND'] = 'micro-e14-qlora'
os.environ['TEMPO_CACHE_DIR'] = str(Path(TMP.name)/'cache')
os.environ['TEMPO_JOBS_DIR'] = str(Path(TMP.name)/'jobs')
Path(os.environ['TEMPO_CACHE_DIR']).mkdir()
import app as A
from micro_e14_engine import VERSION, BACKEND, TASKS
from PIL import Image


def fixture_predictions():
    return {t:dict(prediksi=A.ENG.maps[t][0], prediksi_tampil='Fixture '+t, probabilitas=.6,
        nama_task=t, model_version=VERSION, backend=BACKEND, score_kind='class_token_softmax_uncalibrated',
        score_label='Fixture only', evaluation_mode='fixture, not a GPU prediction',
        evaluation={'deployment':'Not Evaluated'}, prompt_sha256='0'*64,
        semua=[dict(kelas=c, prob=.6 if i==0 else .4/(len(A.ENG.maps[t])-1)) for i,c in enumerate(A.ENG.maps[t])]) for t in TASKS}


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.client = A.app.test_client()
        self.sample = A.ENG.df.sample_id.iloc[0]

    def test_not_ready_metadata_and_503(self):
        self.assertFalse(A.ENG.ready)
        info = self.client.get('/api/models').get_json()
        self.assertEqual(info['version'],VERSION)
        self.assertFalse(info['ready'])
        r = self.client.post('/api/analisis',data={'sample_id':self.sample})
        self.assertEqual(r.status_code,503)
        self.assertTrue(r.get_json()['error'])

    def test_upload_rejected_without_model_or_files(self):
        data = io.BytesIO()
        Image.new('RGB',(100,100)).save(data,format='PNG')
        data.seek(0)
        with patch.object(A.ENG,'predict_image') as predict:
            r = self.client.post('/api/analisis',data={'headline':'Test','gambar':(data,'test.png')})
        self.assertEqual(r.status_code,503)
        self.assertIn('fitur visual E01',r.get_json()['error'])
        predict.assert_not_called()
        self.assertEqual(list(A.CACHE.iterdir()),[])

    def test_contract_not_baseline_xai_or_loo(self):
        with patch.object(A.ENG,'predict_image',return_value=fixture_predictions()) as predict:
            r = self.client.post('/api/analisis',data={'sample_id':self.sample})
        self.assertEqual(r.status_code,200)
        result = r.get_json()
        self.assertIn('in-sample',result['mode'])
        self.assertFalse(result['xai']['available'])
        self.assertIsNone(result['heatmap_url'])
        self.assertEqual(result['atribusi_kata'],[])
        self.assertEqual(result['snapshot']['model'],VERSION)
        self.assertEqual(len(predict.call_args.args),4) # image, text, supporting, ID only
        self.assertFalse(hasattr(A.ENG,'train'))


class BrowserTests(unittest.TestCase):
    def test_status_and_results_do_not_claim_baseline_xai(self):
        from playwright.sync_api import sync_playwright
        with patch.object(A.ENG,'predict_image',return_value=fixture_predictions()):
            result = A.analyse_e14(A.siapkan_masukan({'sample_id':A.ENG.df.sample_id.iloc[0]},None))
        info = A.ENG.description()
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            try:
                for ready in (False,True):
                    context = browser.new_context(viewport={'width':1440,'height':1000})
                    page = context.new_page()
                    errors=[]
                    page.on('pageerror',lambda e:errors.append(str(e)))
                    def route(r):
                        path=urlparse(r.request.url).path
                        if path=='/':r.fulfill(content_type='text/html',body=(A.HERE/'index.html').read_text())
                        elif path=='/api/models':r.fulfill(json=dict(info,ready=ready))
                        elif path=='/api/catalog':r.fulfill(json=[])
                        elif path=='/api/samples':r.fulfill(json=[])
                        elif path.startswith('/api/image/'):r.fulfill(status=204)
                        else:raise AssertionError('Unexpected request '+path)
                    context.route('**/*',route)
                    page.goto('http://tempo.test/')
                    page.wait_for_function("document.getElementById('activeModelStatus').textContent.includes('micro-e14-qlora-v1')")
                    status=page.inner_text('#activeModelStatus')
                    self.assertIn('Model aktif:' if ready else 'Model diminta, belum aktif:',status)
                    if not ready:self.assertNotIn('Model aktif:',status)
                    page.evaluate('result=>tampil(result,true)',result)
                    self.assertIn('belum tersedia',page.inner_text('#kataBox'))
                    self.assertNotIn('occlusion',page.inner_text('#metodeAtribusi'))
                    self.assertIn('XAI belum tersedia',page.inner_text('#ringkas'))
                    self.assertEqual(page.locator('#imgHeat').get_attribute('src'),None)
                    self.assertIn('micro-e14-qlora-v1',page.inner_text('#tabelPred'))
                    self.assertEqual(errors,[])
                    context.close()
            finally:browser.close()


if __name__=='__main__':
    unittest.main()
