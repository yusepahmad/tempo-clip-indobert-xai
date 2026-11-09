"""Desktop/mobile real joint MTL UI smoke; results and screenshots retained."""
import json,time,os
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'07_delivery_evidence/browser';OUT.mkdir(parents=True,exist_ok=True)
assert (OUT.parent/'extended_verification.json').exists(), 'Run HTTP checks first'
checks=[]
with sync_playwright() as p:
 browser=p.chromium.launch(headless=True)
 for name,size in [('desktop',dict(width=1440,height=1000)),('mobile',dict(width=390,height=844))]:
  page=browser.new_page(viewport=size);errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  page.goto(os.environ.get('TEMPO_DEMO_URL','http://127.0.0.1:7862'));page.wait_for_function("document.getElementById('sample').options.length>700")
  page.wait_for_function("document.getElementById('activeModelStatus').textContent.includes('clip-indobert-mtl-v1')")
  assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
  page.screenshot(path=str(OUT/(name+'_input.png')),full_page=True)
  with page.expect_response(lambda r:r.url.endswith('/api/analisis'),timeout=600000) as response:
   page.click('#jalan');page.wait_for_selector('#processingOverlay:not([hidden])',timeout=3000)
  d=response.value.json();assert 'error' not in d,d
  page.wait_for_selector('#hasil',state='visible');assert d['prediksi']['task2_domain_sumber']['model_version']=='clip-indobert-mtl-v1'
  assert d['kelas_untuk_atribusi']==d['prediksi'][d['task_id']]['prediksi']
  for tab in ['ringkasan','visual','teks','sumber','verifikasi']:
   sel='#result-tab-'+tab
   assert page.locator(sel).count()==1
   page.click(sel);page.screenshot(path=str(OUT/(name+'_'+tab+'.png')),full_page=True)
  assert not errors,errors
  checks.append(dict(viewport=name,status='passed',model_version='clip-indobert-mtl-v1',analysis_id=d['analysis_id'],seconds=d['durasi_detik'],page_errors=errors))
  page.close()
 browser.close()
(OUT.parent/'browser_verification.json').write_text(json.dumps(dict(status='passed',checks=checks),indent=2)+'\n');print('BROWSER DELIVERY VERIFIED',flush=True)
