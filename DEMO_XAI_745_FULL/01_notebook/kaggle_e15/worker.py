"""Frozen visual-language hidden states; no labels or classifier fitting on GPU."""
import os
for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'):os.environ[key]='1'
os.environ['HF_HOME']='/kaggle/working/.cache/huggingface'
import hashlib
import json
from pathlib import Path
import time
import numpy as np
import pandas as pd
from PIL import Image
import torch
from transformers import AutoProcessor,AutoModelForImageTextToText
from e15_prompt import DEFINITIONS,build_prompt

MODEL='Qwen/Qwen3-VL-8B-Instruct'
REVISION='0c351dd01ed87e9c1b53cbc748cba10e6187ff3b'
OUT=Path('/kaggle/working/e15_vlm_features');OUT.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
paths=list(Path('/kaggle/input').rglob('DATASET_740_TASK2_DOMAIN.csv'));assert len(paths)==1
csv=paths[0];root=csv.parents[1]
assert sha(csv)=='cba20f8250bcb59481ed2d3d7d5d42fb8242c96a7ba2d11a2cd02ad80862961a'
df=pd.read_csv(csv).fillna('');assert len(df)==740 and df.sample_id.is_unique
hashes={}
def aligned(name,expected):
    paths=list(Path('/kaggle/input').rglob(name));assert len(paths)==1
    hashes[name]=sha(paths[0]);assert hashes[name]==expected
    rows=list(map(json.loads,paths[0].read_text().splitlines()));lookup={r['sample_id']:r for r in rows}
    assert len(rows)==len(lookup)==740 and set(lookup)==set(df.sample_id)
    return [lookup[sid] for sid in df.sample_id]
descriptions=aligned('deskripsi.jsonl','c75e8df3f9b71d6786462f8d0f1187ebe4234fb8dd079924f3f35707ff1b8cd2')
reasons=aligned('zeroshot.jsonl','10c07b06b13fbbf647f2b1ed12a722d9bff8f97caa6b621430d8bc0429ab38c9')
classes=sorted(DEFINITIONS)  # Constant codebook; never read the target label column.
assert torch.cuda.device_count()==2
processor=AutoProcessor.from_pretrained(MODEL,revision=REVISION,min_pixels=128*128,max_pixels=384*384)
model=AutoModelForImageTextToText.from_pretrained(MODEL,revision=REVISION,dtype=torch.float16,
    device_map='auto',max_memory={0:'14GiB',1:'14GiB'},attn_implementation='sdpa').eval()
assert not any(str(value) in ('cpu','disk') for value in model.hf_device_map.values())
for parameter in model.parameters():parameter.requires_grad_(False)
assert all(not p.requires_grad for p in model.parameters())
assert model.config.text_config.hidden_size==4096
audit=[];last=[];tail=[]

def extract(index):
    prompt=build_prompt(index,df,descriptions,reasons,classes)
    image_path=root/'05_gambar'/Path(df.image_path.iloc[index]).name
    with Image.open(image_path) as original:
        image=original.convert('RGB');image.thumbnail((384,384))
    messages=[{'role':'user','content':[{'type':'image','image':image},{'type':'text','text':prompt}]}]
    inputs=processor.apply_chat_template(messages,tokenize=True,add_generation_prompt=True,
        return_dict=True,return_tensors='pt')
    inputs.pop('token_type_ids',None)
    token_count=int(inputs['input_ids'].shape[1]);assert token_count<=2048
    token_sha=hashlib.sha256(inputs['input_ids'].numpy().tobytes()).hexdigest()
    inputs=inputs.to(model.device)
    with torch.inference_mode():
        hidden=model.model(**inputs,use_cache=False,return_dict=True).last_hidden_state.float()
        assert hidden.shape==(1,token_count,4096) and torch.isfinite(hidden).all()
        ids=inputs['input_ids'].to(hidden.device);mask=inputs['attention_mask'].to(hidden.device).bool()
        mask&=(ids!=model.config.image_token_id)&(ids!=model.config.video_token_id)
        text_indices=torch.nonzero(mask[0],as_tuple=False).flatten()[-128:];assert len(text_indices)>0
        a=torch.nn.functional.normalize(hidden[:,-1,:],p=2,dim=1)[0]
        b=torch.nn.functional.normalize(hidden[:,text_indices,:].mean(1),p=2,dim=1)[0]
        a,b=a.cpu().numpy(),b.cpu().numpy()
    assert np.isfinite(a).all() and np.isfinite(b).all()
    assert np.allclose(np.linalg.norm(a),1,atol=1e-4) and np.allclose(np.linalg.norm(b),1,atol=1e-4)
    last.append(a);tail.append(b)
    audit.append({'sample_id':df.sample_id.iloc[index],'index':index,'tokens':token_count,
        'tail_tokens':len(text_indices),'prompt_sha256':hashlib.sha256(prompt.encode()).hexdigest(),
        'image_sha256':sha(image_path),'token_ids_sha256':token_sha})

for gpu in range(2):torch.cuda.synchronize(gpu)
started=time.monotonic()
for index in range(12):extract(index)
for gpu in range(2):torch.cuda.synchronize(gpu)
seconds=time.monotonic()-started
smoke={'status':'verified','samples':12,'dimension':4096,'seconds':seconds,
       'projected_inference_seconds':seconds/12*740,'frozen':True,'finite':True,'unit_norm':True}
(OUT/'smoke.json').write_text(json.dumps(smoke,indent=2));print(json.dumps(smoke),flush=True)
assert smoke['projected_inference_seconds']<=2100,'Inference projection exceeds initial budget; audit before extending'
for index in range(12,740):
    extract(index)
    if (index+1)%100==0:print('Extracted',index+1,flush=True)
assert len(audit)==len(last)==len(tail)==740
last,tail=np.asarray(last),np.asarray(tail);assert last.shape==tail.shape==(740,4096)
np.savez_compressed(OUT/'embeddings.npz',sample_id=df.sample_id.to_numpy(dtype=str),last_token=last,tail_text_mean=tail)
(OUT/'input_audit.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in audit))
meta={'status':'complete','model':MODEL,'revision':REVISION,'csv_sha256':sha(csv),'e01_hashes':hashes,
      'worker_sha256':sha(Path(__file__)),'prompt_helper_sha256':sha(Path(__file__).with_name('e15_prompt.py')),
      'samples':740,'dimension':4096,'pooling':['last token L2','mean last128 non-image/video text positions L2'],
      'frozen':True,'dtype':'float16','max_image_side':384,'max_tokens':2048,
      'device_map':{name:str(value) for name,value in model.hf_device_map.items()},
      'peak_cuda_bytes':[torch.cuda.max_memory_allocated(gpu) for gpu in range(2)],
      'seconds_all_inference':time.monotonic()-started,'embeddings_sha256':sha(OUT/'embeddings.npz'),
      'input_audit_sha256':sha(OUT/'input_audit.jsonl'),'torch':str(torch.__version__)}
(OUT/'meta.json').write_text(json.dumps(meta,indent=2));print('COMPLETE E15',flush=True)
