"""Extract full rich input at256 tokens from pre-existing label-free JSONL."""
import argparse
import json
from pathlib import Path
import time
import numpy as np
import torch
from transformers import AutoTokenizer,AutoModel
from huggingface_hub import snapshot_download
from evaluate import sha,write_json


def main(workspace):
    repo=Path(workspace).resolve();app=repo/'DEMO_XAI_745_FULL';base=app/'04_hasil_eksperimen/revisi_ii'
    out=base/'rich256';out.mkdir(exist_ok=True)
    if (out/'manifest.json').exists():
        d=json.loads((out/'manifest.json').read_text());assert sha(out/'rich256_front_cache.npz')==d['cache_sha256'];return
    torch.set_num_threads(2);start=time.monotonic()
    inputs=base/'text_inputs/label_blind_inputs.jsonl';rows=[json.loads(l) for l in inputs.read_text().splitlines()]
    assert all(set(r)=={'sample_id','headline','supporting','description','source_visual','reason'} for r in rows)
    old=json.loads((app/'04_hasil_eksperimen/e37_token_pool/features_manifest.json').read_text())
    snap=Path(snapshot_download('indobenchmark/indobert-base-p1',revision=old['model_snapshot'],local_files_only=True))
    tok=AutoTokenizer.from_pretrained(snap,local_files_only=True);model=AutoModel.from_pretrained(snap,local_files_only=True).eval()
    for p in model.parameters():p.requires_grad=False
    xs=[];ams=[];pms=[];base_mean=[];lens=[]
    texts=[f"{r['headline']} [SEP] {r['supporting']} [SEP] Deskripsi visual: {r['description']}. Observasi sumber visual: {r['source_visual']}. Alasan visual: {r['reason']}." for r in rows]
    for off in range(0,len(rows),4):
        segment=texts[off:off+4];lens.extend([len(tok.encode(t,truncation=False)) for t in segment])
        enc=tok(segment,return_tensors='pt',truncation=True,max_length=256,padding='max_length');mask=enc['attention_mask'].bool();pool=mask.clone()
        for sid in tok.all_special_ids:pool &= enc['input_ids']!=sid
        with torch.inference_mode():
            result=model(**enc,output_hidden_states=True);hidden=result.hidden_states[10].clone();hidden[~mask]=0
            mean=(result.last_hidden_state*pool.unsqueeze(-1)).sum(1)/pool.sum(1,keepdim=True)
            xs.append(hidden.numpy());ams.append(mask.numpy().astype('uint8'));pms.append(pool.numpy().astype('uint8'));base_mean.append(torch.nn.functional.normalize(mean.float(),p=2,dim=1).numpy())
        if off%96==0:print('RICH256',off+len(segment),round(time.monotonic()-start,1),flush=True)
    oldcache=np.load(app/'04_hasil_eksperimen/e41_cached_tail/cache/front_cache.npz')
    assert oldcache['sample_ids'].tolist()==[r['sample_id'] for r in rows]
    target=out/'rich256_front_cache.npz'
    np.savez_compressed(target,sample_ids=oldcache['sample_ids'],h10=np.concatenate(xs),attention=np.vstack(ams),pool_mask=np.vstack(pms),base_mean=np.vstack(base_mean),visual=oldcache['visual'])
    write_json(out/'manifest.json',dict(status='complete',samples=740,maximum_tokens=256,truncated_samples=sum(n>256 for n in lens),
               original_tokens_max=max(lens),cache_sha256=sha(target),input_sha256=sha(inputs),source_sha256=sha(__file__),
               labels_read=False,bert_revision=old['model_snapshot'],seconds=time.monotonic()-start))
    print('RICH256 COMPLETE',round(time.monotonic()-start,1),flush=True)


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--workspace',required=True,type=Path);main(ap.parse_args().workspace)
