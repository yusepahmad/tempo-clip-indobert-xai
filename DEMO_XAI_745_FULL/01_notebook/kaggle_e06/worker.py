"""Frozen multilingual E5 embeddings; labels never enter embedding inputs."""
import os
for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'):
    os.environ[key]='1'
os.environ['HF_HOME']='/kaggle/working/.cache/huggingface'
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
import torch
from transformers import AutoModel, AutoTokenizer

OUT=Path('/kaggle/working/e06_semantic'); OUT.mkdir(exist_ok=True)
MODEL='intfloat/multilingual-e5-base'
REVISION='d128750597153bb5987e10b1c3493a34e5a4502a'
assert torch.cuda.is_available()
paths=list(Path('/kaggle/input').rglob('DATASET_740_TASK2_DOMAIN.csv'));assert len(paths)==1
csv=paths[0]; sha=hashlib.sha256(csv.read_bytes()).hexdigest()
assert sha=='cba20f8250bcb59481ed2d3d7d5d42fb8242c96a7ba2d11a2cd02ad80862961a'
df=pd.read_csv(csv).fillna('')
def records(name):
    paths=list(Path('/kaggle/input').rglob(name));assert len(paths)==1,(name,paths)
    rows=[json.loads(x) for x in paths[0].read_text().splitlines()]
    mapping={r['sample_id']:r for r in rows}
    assert len(rows)==len(mapping)==740 and set(mapping)==set(df.sample_id)
    return [mapping[sid] for sid in df.sample_id],hashlib.sha256(paths[0].read_bytes()).hexdigest()
a,hash_a=records('deskripsi.jsonl');b,hash_b=records('zeroshot.jsonl')
descriptions=[r['deskripsi'] for r in a]
reasons=[(r.get('sumber_visual') or '')+' '+(r.get('alasan') or '') for r in b]
original=(df.headline_verified+' '+df.supporting_text_verified).tolist()
texts={'description':descriptions,'source_reason':reasons,
       'combined':[x+' '+z+' '+t for x,z,t in zip(descriptions,reasons,original)]}
tok=AutoTokenizer.from_pretrained(MODEL,revision=REVISION)
model=AutoModel.from_pretrained(MODEL,revision=REVISION).cuda().eval()
def encode(items):
    result=[]
    with torch.inference_mode():
        for start in range(0,len(items),16):
            batch=tok(['query: '+s for s in items[start:start+16]],padding=True,truncation=True,max_length=512,return_tensors='pt').to('cuda')
            with torch.autocast('cuda',dtype=torch.float16):
                h=model(**batch).last_hidden_state.float()
            mask=batch['attention_mask'].unsqueeze(-1).bool()
            h=h.masked_fill(~mask,0).sum(1)/mask.sum(1)
            h=torch.nn.functional.normalize(h,p=2,dim=1)
            assert torch.isfinite(h).all()
            result.append(h.cpu().numpy())
    return np.concatenate(result)
# Technical smoke on 12 samples before full inference in this kernel.
smoke=encode(descriptions[:12]);assert smoke.shape==(12,768)
assert np.allclose(np.linalg.norm(smoke,axis=1),1,atol=1e-4)
print('Smoke embeddings valid',flush=True)
vectors={}
for name,items in texts.items():
    vectors[name]=encode(items)
    assert vectors[name].shape==(740,768)
    print('Encoded',name,flush=True)
np.savez_compressed(OUT/'embeddings.npz',sample_id=df.sample_id.to_numpy(dtype=str),**vectors)
(OUT/'meta.json').write_text(json.dumps({'model':MODEL,'revision':REVISION,'csv_sha256':sha,
    'description_sha256':hash_a,'zeroshot_sha256':hash_b,'samples':740,'dimension':768,
    'prefix':'query:','pooling':'masked mean then L2','torch':torch.__version__},indent=2))
print('COMPLETE E06 EMBEDDINGS',flush=True)
