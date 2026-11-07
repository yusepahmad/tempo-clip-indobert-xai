"""Frozen BGE-M3 CLS embeddings; original labels never enter model inputs."""
import os
for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'):os.environ[key]='1'
os.environ['HF_HOME']='/kaggle/working/.cache/huggingface'
import hashlib
import json
from pathlib import Path
import time
import numpy as np
import pandas as pd
import torch
from transformers import AutoTokenizer,AutoModel

MODEL='BAAI/bge-m3'
REVISION='5617a9f61b028005a4858fdac845db406aefb181'
OUT=Path('/kaggle/working/e13_bge_m3');OUT.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
paths=list(Path('/kaggle/input').rglob('DATASET_740_TASK2_DOMAIN.csv'));assert len(paths)==1
csv=paths[0];assert sha(csv)=='cba20f8250bcb59481ed2d3d7d5d42fb8242c96a7ba2d11a2cd02ad80862961a'
df=pd.read_csv(csv).fillna('');assert len(df)==740 and df.sample_id.is_unique
hashes={}
def aligned(name,expected):
    paths=list(Path('/kaggle/input').rglob(name));assert len(paths)==1
    hashes[name]=sha(paths[0]);assert hashes[name]==expected
    rows=list(map(json.loads,paths[0].read_text().splitlines()));lookup={r['sample_id']:r for r in rows}
    assert len(rows)==len(lookup)==740 and set(lookup)==set(df.sample_id)
    return [lookup[sid] for sid in df.sample_id]
a=aligned('deskripsi.jsonl','c75e8df3f9b71d6786462f8d0f1187ebe4234fb8dd079924f3f35707ff1b8cd2')
b=aligned('zeroshot.jsonl','10c07b06b13fbbf647f2b1ed12a722d9bff8f97caa6b621430d8bc0429ab38c9')
description=[r['deskripsi'] for r in a]
reason=[(r.get('sumber_visual') or '')+' '+(r.get('alasan') or '') for r in b]
original=(df.headline_verified+' '+df.supporting_text_verified).tolist()
texts={'description':description,'source_reason':reason,
       'combined':[x+' '+z+' '+t for x,z,t in zip(description,reason,original)]}
assert torch.cuda.is_available();torch.manual_seed(42)
tokenizer=AutoTokenizer.from_pretrained(MODEL,revision=REVISION)
model=AutoModel.from_pretrained(MODEL,revision=REVISION,dtype=torch.float16).cuda().eval()
assert all(not p.grad for p in model.parameters())
for p in model.parameters():p.requires_grad_(False)
audit=[]
for name,items in texts.items():
    for idx,text in enumerate(items):
        length=len(tokenizer.encode(text,add_special_tokens=True,truncation=False))
        audit.append({'view':name,'sample_id':df.sample_id.iloc[idx],'index':idx,
                      'text_sha256':hashlib.sha256(text.encode()).hexdigest(),
                      'untruncated_tokens':length,'truncated':length>1024})
(OUT/'input_audit.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in audit))
def encode(items):
    values=[]
    with torch.inference_mode():
        for start in range(0,len(items),8):
            inputs=tokenizer(items[start:start+8],padding=True,truncation=True,max_length=1024,return_tensors='pt').to('cuda')
            h=model(**inputs).last_hidden_state[:,0].float()
            h=torch.nn.functional.normalize(h,p=2,dim=1)
            assert torch.isfinite(h).all()
            values.append(h.cpu().numpy())
    return np.concatenate(values)
smoke=encode(description[:12]);assert smoke.shape==(12,1024)
assert np.allclose(np.linalg.norm(smoke,axis=1),1,atol=1e-4)
print('Technical smoke12 valid',flush=True)
vectors={};elapsed={}
for name,items in texts.items():
    torch.cuda.synchronize();started=time.monotonic();vectors[name]=encode(items);torch.cuda.synchronize()
    elapsed[name]=time.monotonic()-started
    assert vectors[name].shape==(740,1024) and np.allclose(np.linalg.norm(vectors[name],axis=1),1,atol=1e-4)
    print('Encoded',name,elapsed[name],flush=True)
np.savez_compressed(OUT/'embeddings.npz',sample_id=df.sample_id.to_numpy(dtype=str),**vectors)
meta={'status':'complete','model':MODEL,'revision':REVISION,'csv_sha256':sha(csv),
      'e01_hashes':hashes,'worker_sha256':sha(Path(__file__)),'samples':740,'dimension':1024,
      'prefix':'','pooling':'CLS then L2','batch':8,'max_length':1024,'dtype':'float16',
      'input_audit_sha256':sha(OUT/'input_audit.jsonl'),'embeddings_sha256':sha(OUT/'embeddings.npz'),
      'seconds_by_view':elapsed,'truncated_by_view':{name:sum(r['truncated'] for r in audit if r['view']==name) for name in texts},
      'peak_cuda_bytes':torch.cuda.max_memory_allocated(),'torch':str(torch.__version__)}
(OUT/'meta.json').write_text(json.dumps(meta,indent=2));print('COMPLETE',flush=True)
