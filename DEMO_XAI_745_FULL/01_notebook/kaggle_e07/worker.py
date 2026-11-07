"""OOF VLM few-shot: demonstrators strictly from the outer training fold."""
import os
for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'): os.environ[key]='1'
os.environ['HF_HOME']='/kaggle/working/.cache/huggingface'
import hashlib
import json
from pathlib import Path
import re
import time
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import f1_score,classification_report,confusion_matrix
from sklearn.model_selection import StratifiedKFold
from PIL import Image
import torch
from transformers import AutoProcessor,AutoModelForImageTextToText

MODEL='Qwen/Qwen3-VL-8B-Instruct'
REVISION='0c351dd01ed87e9c1b53cbc748cba10e6187ff3b'
SMOKE=os.environ.get('E07_SMOKE','1')=='1'
OUT=Path('/kaggle/working/e07_smoke' if SMOKE else '/kaggle/working/e07_full');OUT.mkdir(exist_ok=True)
paths=list(Path('/kaggle/input').rglob('DATASET_740_TASK2_DOMAIN.csv'));assert len(paths)==1
csv=paths[0];root=csv.parents[1]
csv_hash=hashlib.sha256(csv.read_bytes()).hexdigest()
assert csv_hash=='cba20f8250bcb59481ed2d3d7d5d42fb8242c96a7ba2d11a2cd02ad80862961a'
df=pd.read_csv(csv).fillna('');assert len(df)==740 and df.sample_id.is_unique
paths=list(Path('/kaggle/input').rglob('deskripsi.jsonl'));assert len(paths)==1
rows=[json.loads(x) for x in paths[0].read_text().splitlines()]
lookup={r['sample_id']:r['deskripsi'] for r in rows}
assert len(rows)==len(lookup)==740 and set(lookup)==set(df.sample_id)
description=np.array([lookup[sid] for sid in df.sample_id])
title=(df.headline_verified+' '+df.supporting_text_verified).to_numpy()
texts=description+' '+title
y=df.task2_domain_sumber.to_numpy();classes=sorted(set(y))
issues=pd.Categorical(df.task1_issue,categories=sorted(set(df.task1_issue))).codes
counts=np.bincount(issues);strat=np.array([v if counts[v]>=5 else -1 for v in issues])
folds=list(StratifiedKFold(5,shuffle=True,random_state=42).split(np.zeros(740),strat))
RULES='''Tugas: pilih domain sumber metafora sampul Tempo, bukan isu politiknya.
MESIN_INFRASTRUKTUR: mesin, alat kerja, kendaraan, bangunan atau mekanisme buatan sebagai kiasan.
PERMAINAN_KONTES: permainan, pertandingan, kompetisi atau panggung pertunjukan sebagai kiasan.
BENCANA_JERAT: ancaman, bencana, perangkap, jerat atau keadaan fisik terjepit sebagai kiasan.
HEWAN_TUBUH: hewan, anatomi, deformasi atau perilaku biologis sebagai kiasan.
KONSUMSI_TRANSAKSI: makanan, jamuan, makan, selera, jual-beli atau pertukaran nilai sebagai kiasan.
NON_METAFORA: gambar/adegan literal tanpa pemetaan metaforis; potret, bangunan atau benda biasa tidak otomatis metafora.
LAINNYA: ada metafora, tetapi sumbernya bukan lima domain metafora di atas. Jangan memaksakan domain terdekat.
Contoh berlabel berikut berasal hanya dari data latih. Gunakan contoh untuk memahami konvensi label.
Tentukan label target dari ilustrasi dan konteks teks. Jawab tepat satu KODE, tanpa penjelasan.'''
config={'model':MODEL,'revision':REVISION,'smoke':SMOKE,'csv_sha256':csv_hash,
        'description_sha256':hashlib.sha256(paths[0].read_bytes()).hexdigest(),
        'worker_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'retrieval':'word TF-IDF fit outer-training only, cosine two nearest per class',
        'rules_sha256':hashlib.sha256(RULES.encode()).hexdigest(),
        'batch':2,'max_tokens':40,'image_side':768,'seed':42}
(OUT/'config.json').write_text(json.dumps(config,indent=2))
processor=AutoProcessor.from_pretrained(MODEL,revision=REVISION)
processor.tokenizer.padding_side='left'
assert torch.cuda.device_count()==2
model=AutoModelForImageTextToText.from_pretrained(MODEL,revision=REVISION,
    dtype=torch.float16,device_map='auto',max_memory={0:'14GiB',1:'14GiB'}).eval()
assert not any(str(v) in ('cpu','disk') for v in model.hf_device_map.values())
completed=[]
for fold,(tr,te) in enumerate(folds,1):
    if SMOKE and fold>1:break
    vector=TfidfVectorizer(ngram_range=(1,2),min_df=2,sublinear_tf=True)
    train=vector.fit_transform(texts[tr]);test=vector.transform(texts[te])
    count=12 if SMOKE else len(te)
    for start in range(0,count,2):
        batch=[];audits=[]
        for j in range(start,min(start+2,count)):
            idx=int(te[j]);similarity=(train@test[j].T).toarray().ravel()
            examples=[]
            for label in classes:
                candidates=np.where(y[tr]==label)[0]
                best=candidates[np.argsort(-similarity[candidates],kind='stable')[:2]]
                examples.extend(tr[best].tolist())
            assert set(examples)<=set(tr) and not set(examples)&set(te) and idx not in examples
            demonstrations=[]
            for i in examples:
                demonstrations.append(f'Contoh: {description[i][:650]}\nJudul: {title[i][:200]}\nLabel: {y[i]}')
            # Only this line contains the target's text; it never references y[idx].
            prompt=RULES+'\n\n'+'\n\n'.join(demonstrations)+f'\n\nTARGET:\nDeskripsi: {description[idx]}\nJudul dan teks: {title[idx]}\nLabel:'
            image=Image.open(root/'05_gambar'/Path(df.image_path.iloc[idx]).name).convert('RGB')
            image.thumbnail((768,768))
            batch.append([{'role':'user','content':[{'type':'image','image':image},{'type':'text','text':prompt}]}])
            audits.append({'sample_id':df.sample_id.iloc[idx],'index':idx,'fold':fold,
                'exemplars':[df.sample_id.iloc[i] for i in examples],
                'prompt_sha256':hashlib.sha256(prompt.encode()).hexdigest()})
        begin=time.monotonic()
        inputs=processor.apply_chat_template(batch,tokenize=True,add_generation_prompt=True,
            return_dict=True,return_tensors='pt',padding=True).to(model.device)
        with torch.inference_mode():
            generated=model.generate(**inputs,max_new_tokens=40,do_sample=False)
        replies=processor.batch_decode(generated[:,inputs['input_ids'].shape[1]:],skip_special_tokens=True)
        for record,reply in zip(audits,replies):
            found=[label for label in classes if re.search(r'\b'+label+r'\b',reply.upper())]
            record.update({'answer':reply,'prediction':found[0] if len(found)==1 else None,
                'seconds_per_sample':(time.monotonic()-begin)/len(replies)})
            completed.append(record)
            with (OUT/'predictions.jsonl').open('a') as f:f.write(json.dumps(record,ensure_ascii=False)+'\n')
        print('fold',fold,'samples',start+len(batch),'invalid',sum(r['prediction'] is None for r in completed),flush=True)
        if sum(r['prediction'] is None for r in completed)>3:raise RuntimeError('Too many invalid labels')
assert len(completed)==(12 if SMOKE else 740)
assert len({r['sample_id'] for r in completed})==len(completed)
valid=all(r['prediction'] is not None for r in completed)
pred=np.array([r['prediction'] or 'INVALID' for r in completed]);truth=y[[r['index'] for r in completed]]
report={'status':'complete','smoke':SMOKE,'samples':len(completed),'valid':valid,
        'macro_f1':float(f1_score(truth,pred,labels=classes,average='macro',zero_division=0)),
        'classification':classification_report(truth,pred,labels=classes,output_dict=True,zero_division=0),
        'confusion_matrix':confusion_matrix(truth,pred,labels=classes).tolist(),
        'mean_seconds_per_sample':float(np.mean([r['seconds_per_sample'] for r in completed]))}
(OUT/'metrics.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report),flush=True)
