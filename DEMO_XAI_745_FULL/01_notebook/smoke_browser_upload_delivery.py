"""Real browser upload -> OCR -> manual text confirmation -> joint MTL -> XAI."""
import json,time,os
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'07_delivery_evidence'
assert (OUT/'browser_verification.json').exists(), 'Run browser delivery checks first'
with sync_playwright() as p:
 b=p.chromium.launch(headless=True);page=b.new_page(viewport=dict(width=1440,height=1000));errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto(os.environ.get('TEMPO_DEMO_URL','http://127.0.0.1:7862'));page.wait_for_function("document.getElementById('sample').options.length>700")
 page.click('#tabUnggah');photo=next((ROOT/'06_gambar_revisi').glob('*04.33.42*'))
 with page.expect_response(lambda r:r.url.endswith('/api/ocr'),timeout=300000) as resp:page.set_input_files('#gambar',str(photo))
 assert resp.value.ok;page.wait_for_function("document.getElementById('workspace').dataset.state!=='ocr'")
 page.fill('#headline','GULA-GULA DEMO BURUH');page.fill('#supporting','')
 with page.expect_response(lambda r:r.url.endswith('/api/analisis'),timeout=600000) as response:
  page.click('#jalan');page.wait_for_selector('#processingOverlay:not([hidden])',timeout=3000)
 d=response.value.json();assert 'error' not in d,d;assert all(p['model_version']=='clip-indobert-mtl-v1' for p in d['prediksi'].values());assert d['label_anotator'] is None
 page.wait_for_selector('#hasil',state='visible');assert d['headline']=='GULA-GULA DEMO BURUH';assert d['metode_atribusi']=='lime'
 page.screenshot(path=str(OUT/'browser/upload_result.png'),full_page=True)
 page.click('#result-tab-visual');page.wait_for_function("document.getElementById('imgHeatTask').complete && document.getElementById('imgHeatTask').naturalWidth>0")
 page.screenshot(path=str(OUT/'browser/upload_visual.png'),full_page=True)
 assert not errors,errors;b.close()
(OUT/'browser_upload.json').write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
(OUT/'browser_upload_verification.json').write_text(json.dumps(dict(status='passed',ocr=True,manual_text=True,actual_joint_mtl=True,model_version='clip-indobert-mtl-v1',lime=True,seconds=d['durasi_detik'],page_errors=errors),indent=2)+'\n');print('BROWSER UPLOAD DELIVERY VERIFIED',flush=True)
