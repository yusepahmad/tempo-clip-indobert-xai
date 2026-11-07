"""Real HTTP delivery verification; outputs isolated from historical evidence."""
import json,time,io,csv,os
from pathlib import Path
import requests
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'07_delivery_evidence';OUT.mkdir(exist_ok=True)
BASE=os.environ.get('TEMPO_DEMO_URL','http://127.0.0.1:7862')
T='task2_domain_sumber'
def save(n,x): (OUT/(n+'.json')).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def post(data,files=None):
 r=requests.post(BASE+'/api/analisis',data=data,files=files,timeout=7200)
 assert r.ok,r.text
 d=r.json();assert all(p['model_version']=='clip-indobert-mtl-v1' for p in d['prediksi'].values())
 assert d['xai']['model_version']=='clip-indobert-mtl-v1'
 assert d['prediksi'][T]['score_kind']=='softmax_uncalibrated'
 assert d['kelas_untuk_atribusi']==d['prediksi'][d['task_id']]['prediksi']
 for x in [d['heatmap_url'],d['heatmap_padu_url']]+[v['url'] for v in d['heatmap_per_task'].values()]:assert requests.get(BASE+x).ok
 return d
samples=requests.get(BASE+'/api/samples').json();s=samples[0]
assets=requests.get(BASE+'/api/models').json();save('models',assets)
assert assets['backend']=='clip-indobert-mtl' and len(assets['tasks'])==3,assets
for t in [T,'task1_issue','task3_primary_entity_type']:
 d=post(dict(sample_id=s['sample_id'],task=t,metode_atribusi='occlusion'));save(t,d)
 assert all('leave-one-out' in p['evaluation_mode'] for p in d['prediksi'].values())
 print('DATASET',t,d['durasi_detik'],flush=True)
# Upload uses CLIP + IndoBERT and the joint all740 refit head; no sample_id supplied.
image=requests.get(BASE+'/api/image/'+s['sample_id']).content
form=dict(headline=s['headline'],supporting=s['supporting'],task=T,metode_atribusi='occlusion')
d=post(form,{'gambar':('new_cover.png',image,'image/png')});save('new_upload',d)
assert 'new upload' in d['prediksi'][T]['evaluation_mode']
print('NEW UPLOAD',d['durasi_detik'],flush=True)
# LIME target must match the selected joint MTL head prediction.
form['metode_atribusi']='lime';d=post(form,{'gambar':('repeat.png',image,'image/png')});save('new_upload_lime',d)
assert d['metode_atribusi']=='lime'
print('UPLOAD LIME',d['durasi_detik'],flush=True)
# Mixed batch: original sample + corrupt input. Error isolation and CSV metadata.
r=requests.post(BASE+'/api/batch',data=dict(sample_ids=json.dumps([s['sample_id']]),task=T),files=[('gambar',('broken.png',b'broken','image/png'))]);assert r.status_code==202,r.text
jid=r.json()['id']
for _ in range(1800):
 j=requests.get(BASE+'/api/batch/'+jid).json()
 if j['status'] not in ('queued','running'):break
 time.sleep(1)
assert [x['status'] for x in j['items']]==['success','failed'],j
save('batch',j)
for kind in ('json','csv'):
 r=requests.get(BASE+'/api/batch/'+jid+'/export/'+kind);assert r.ok
 (OUT/('batch_export.'+kind)).write_text(r.text)
rows=list(csv.DictReader(io.StringIO((OUT/'batch_export.csv').read_text().lstrip('\ufeff'))));assert rows[0]['model_version']=='clip-indobert-mtl-v1' and rows[0]['score_kind']=='softmax_uncalibrated'
# Bad inputs produce controlled errors.
for data in [dict(sample_id='unknown'),dict(sample_id=s['sample_id'],task='invalid')]:
 r=requests.post(BASE+'/api/analisis',data=data);assert 400<=r.status_code<500
save('http_verification',dict(status='passed',samples=len(samples),batch_id=jid,hosted_ai_requests=0))
print('HTTP DELIVERY VERIFIED',flush=True)
