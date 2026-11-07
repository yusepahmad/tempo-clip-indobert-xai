#!/usr/bin/env python3
"""Summarize already-opened OCR acceptance sets without tuning on them."""
import hashlib,json,re
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[3];P=ROOT/'DEMO_XAI_745_FULL';BASE=P/'04_hasil_eksperimen/revisi_week3';OUT=P/'04_hasil_eksperimen/next_research_20261017/04_ocr'
SETS={'holdout_1':BASE/'ocr_final_holdout/results.json','holdout_2':BASE/'ocr_second_holdout/results.json','independent':BASE/'ocr_independent/results.json'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def norm(s):return re.sub(r'\s+',' ',re.sub(r'[^A-Z0-9 ]',' ',str(s).upper())).strip()
def lev(a,b):
 prev=list(range(len(b)+1))
 for i,x in enumerate(a,1):
  cur=[i]
  for j,y in enumerate(b,1):cur.append(min(cur[-1]+1,prev[j]+1,prev[j-1]+(x!=y)))
  prev=cur
 return prev[-1]
def token_f1(a,b):
 from collections import Counter
 a,b=Counter(norm(a).split()),Counter(norm(b).split());common=sum((a&b).values())
 if not a and not b:return 1.
 if not common:return 0.
 p,r=common/sum(a.values()),common/sum(b.values());return 2*p*r/(p+r)
def main():
 OUT.mkdir(parents=True,exist_ok=True);summary=[]
 for name,path in SETS.items():
  d=json.loads(path.read_text());rows=d['results'];cers=[];tf=[];times=[];fail=[]
  for x in rows:
   truth,pred=norm(x['headline_truth']),norm(x['headline_prediction']);exact=bool(x.get('exact',pred==truth));cers.append(lev(pred,truth)/max(1,len(truth)));tf.append(token_f1(pred,truth));times.append(float(x.get('seconds',0)))
   if not exact:fail.append({'sample_id':x['sample_id'],'truth':x['headline_truth'],'prediction':x['headline_prediction'],'cer':cers[-1],'token_f1':tf[-1]})
  correct=len(rows)-len(fail);summary.append({'set':name,'samples':len(rows),'exact_correct':correct,'exact_accuracy':correct/len(rows),'mean_cer':float(np.mean(cers)),'mean_token_f1':float(np.mean(tf)),'seconds_p50':float(np.percentile(times,50)),'seconds_p95':float(np.percentile(times,95)),'selector_sha256':d.get('selector_sha256'),'source_sha256':sha(path),'failures':fail})
 (OUT/'ocr_metrics.json').write_text(json.dumps({'schema':'tempo-ocr-final-summary-v1','read_only_summary':True,'sets':summary},indent=2)+'\n')
 lines=['# Laporan Final OCR','', 'Laporan ini hanya merangkum acceptance set yang sudah dibuka. Tidak ada parameter selector yang dituning dari holdout tersebut.','', '| Set | N | Exact | CER | Token-F1 | P50 | P95 |','| --- | ---: | ---: | ---: | ---: | ---: | ---: |']
 for s in summary:lines.append(f"| {s['set']} | {s['samples']} | {s['exact_correct']}/{s['samples']} ({100*s['exact_accuracy']:.2f}%) | {s['mean_cer']:.4f} | {s['mean_token_f1']:.4f} | {s['seconds_p50']:.3f}s | {s['seconds_p95']:.3f}s |")
 lines += ['', '## Keputusan', '', '- Gate exact match ≥80% **belum lulus** pada dua holdout utama (75,00% dan 76,67%).', '- Holdout yang sudah dibuka tidak boleh digunakan lagi untuk memilih aturan selector.', '- Acceptance baru yang sah memerlukan gambar prospektif yang belum pernah dipakai. Dengan data yang dinyatakan tetap, pengujian itu belum tersedia.', '- Pengujian manusia dan clean-Windows tetap merupakan acceptance eksternal yang harus dilakukan pengguna.', '']
 (OUT/'ocr_final_report.md').write_text('\n'.join(lines))
 print(json.dumps([{k:v for k,v in s.items() if k!='failures'} for s in summary],indent=2))
if __name__=='__main__':main()
