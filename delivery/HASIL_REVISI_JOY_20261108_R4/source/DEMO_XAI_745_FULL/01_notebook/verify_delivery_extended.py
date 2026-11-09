"""OCR review, batch upload, edited text and cancellation through real HTTP."""
import sys,time,json,uuid,concurrent.futures
from pathlib import Path
import requests
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'07_delivery_evidence';BASE=__import__('os').environ.get('TEMPO_DEMO_URL','http://127.0.0.1:7862');T='task2_domain_sumber'
assert (OUT/'http_verification.json').exists(), 'Run verify_delivery_mtl.py first'
def save(n,x):(OUT/(n+'.json')).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
s=requests.get(BASE+'/api/samples').json()[0];image=requests.get(BASE+'/api/image/'+s['sample_id']).content
r=requests.post(BASE+'/api/ocr',files={'gambar':('cover.png',image,'image/png')},timeout=600);assert r.ok,r.text;save('ocr',r.json())
r=requests.post(BASE+'/api/batch',data={'task':T},files={'gambar':('cover.png',image,'image/png')});assert r.status_code==202,r.text;jid=r.json()['id']
def wait():
 for _ in range(3600):
  j=requests.get(BASE+'/api/batch/'+jid).json()
  if j['status'] not in ('running','queued'):return j
  time.sleep(1)
 raise AssertionError('Batch timed out')
j=wait();assert j['items'][0]['status']=='needs_review',j
r=requests.post(BASE+'/api/batch/'+jid+'/review/0',data=dict(headline=s['headline'],supporting=s['supporting']));assert r.status_code==202,r.text
j=wait();assert j['items'][0]['status']=='success',j
assert j['items'][0]['result']['prediksi'][T]['model_version']=='clip-indobert-mtl-v1';save('batch_upload_review',j)
# Edited dataset recomputes CLIP/IndoBERT features using leave-one-out head.
r=requests.post(BASE+'/api/analisis',data=dict(sample_id=s['sample_id'],headline=s['headline']+'?',supporting=s['supporting'],task=T,metode_atribusi='occlusion'),timeout=7200);assert r.ok,r.text;d=r.json();save('edited_dataset',d);assert 'leave-one-out' in d['prediksi'][T]['evaluation_mode'];assert d['headline'].endswith('?')
# Pre-cancel skips inference and cannot poison the next request.
req=uuid.uuid4().hex
assert requests.post(BASE+'/api/analisis/batal',data={'req_id':req}).ok
r=requests.post(BASE+'/api/analisis',data=dict(sample_id=s['sample_id'],req_id=req,task=T));assert r.status_code==409,r.text
r=requests.post(BASE+'/api/analisis',data=dict(sample_id=s['sample_id'],task=T,metode_atribusi='occlusion'),timeout=600);assert r.ok,r.text
save('extended_verification',dict(status='passed',ocr=True,batch_upload_review=True,edited_dataset=True,pre_cancel_and_next_request=True))
print('EXTENDED HTTP VERIFIED',flush=True)
