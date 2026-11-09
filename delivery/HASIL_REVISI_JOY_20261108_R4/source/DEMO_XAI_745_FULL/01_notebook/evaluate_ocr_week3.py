"""Diagnosis OCR on 30 corpus images; headline truth is dataset verified text."""
import csv,json,sys,time,re
from pathlib import Path
import numpy as np
import torch
torch.set_num_threads(4)
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/"02_web_demo"))
from ocr_headline import baca
out=root/"04_hasil_eksperimen/revisi_week3";out.mkdir(exist_ok=True)
rows=list(csv.DictReader((root/"03_data/DATASET_740_TASK2_DOMAIN.csv").open(encoding="utf-8-sig")))
lookup={r["sample_id"]:r for r in rows}
history=json.loads((root/"04_hasil_eksperimen/uji_banding_ocr.json").read_text())["easyocr_headline"]
ids=[r["sample_id"] for r in history["rinci"]]
extra=sorted((r for r in rows if r["sample_id"] not in ids),key=lambda r:(len(r["headline_verified"]),r["sample_id"]))
ids+= [extra[int(i)]["sample_id"] for i in np.linspace(0,len(extra)-1,10)]
def norm(s):return re.sub(r"\s+"," ",s.strip()).upper()
def distance(a,b):
 prev=list(range(len(b)+1))
 for i,x in enumerate(a,1):
  cur=[i]
  for j,y in enumerate(b,1):cur.append(min(cur[-1]+1,prev[j]+1,prev[j-1]+(x!=y)))
  prev=cur
 return prev[-1]
manifest=[];results=[]
for index,id in enumerate(ids):
 r=lookup[id];truth=norm(r["headline_verified"])
 m={"sample_id":id,"headline_truth":r["headline_verified"],"source":"headline_verified corpus","subset":"historical_diagnosis" if index<20 else "additional_check","difficulty":"short_text" if len(truth.split())<3 else "long_text" if len(truth)>40 else "normal_text","layout_annotation":"belum diperiksa manusia","supporting_truth":r.get("supporting_text_verified","")}
 manifest.append(m)
 path=next((root/"05_gambar"/(id+ext) for ext in (".jpg",".jpeg",".png",".webp") if (root/"05_gambar"/(id+ext)).exists()))
 begin=time.perf_counter();result=baca(path);elapsed=time.perf_counter()-begin;prediction=norm(result["headline"])
 item={"sample_id":id,"truth":truth,"prediction":prediction,"exact":prediction==truth,"headline_cer":distance(truth,prediction)/max(len(truth),1),"seconds":elapsed,"ocr":result}
 results.append(item);print(id,item["exact"],round(elapsed,2),flush=True)
summary={"count":len(results),"exact_correct":sum(r["exact"] for r in results),"exact_accuracy":np.mean([r["exact"] for r in results]),"mean_headline_cer":np.mean([r["headline_cer"] for r in results]),"median_seconds":float(np.median([r["seconds"] for r in results])),"p95_seconds":float(np.percentile([r["seconds"] for r in results],95)),"caveat":"30 diagnosis samples, not full-text extraction evaluation; layout difficulty and supporting truth need human review; historical20 are not independent validation."}
(out/"ocr_manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
(out/"ocr_diagnosis.json").write_text(json.dumps({"summary":summary,"results":results},ensure_ascii=False,indent=2))
print(json.dumps(summary),flush=True)
