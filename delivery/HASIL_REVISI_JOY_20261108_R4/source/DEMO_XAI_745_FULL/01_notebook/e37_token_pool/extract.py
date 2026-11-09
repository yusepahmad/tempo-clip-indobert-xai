"""Frozen IndoBERT token pooling; labels are never extraction inputs."""
from pathlib import Path
import json,hashlib,time
import numpy as np,pandas as pd,torch
from transformers import AutoModel,AutoTokenizer
from huggingface_hub import snapshot_download
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'04_hasil_eksperimen/e37_token_pool'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def pool(hidden,mask):
    assert mask.any(dim=1).all(),"No non-special text tokens"
    return (hidden*mask.unsqueeze(-1)).sum(dim=1)/mask.sum(dim=1,keepdim=True)
def main():
    torch.set_num_threads(8);start=time.monotonic();OUT.mkdir(parents=True,exist_ok=True)
    assert not (OUT/'features.npz').exists(),'Completed extraction cannot be overwritten'
    csv=ROOT/'03_data/DATASET_740_TASK2_DOMAIN.csv';cache=ROOT/'03_data/fitur_clip_indobert_740.npz'
    release=Path('/home/research-user/workspace/learn/delivery_week34_clip_indobert_20261012/DEMO_XAI_745_FULL/06_models/clip-indobert-mtl-v1/manifest.json')
    ref=json.loads(release.read_text())
    for p in [csv,cache]:assert sha(p)==ref['data_sha256'][str(p.relative_to(ROOT))]
    df=pd.read_csv(csv).fillna('');assert len(df)==740 and df.sample_id.is_unique
    snapshot=Path(snapshot_download('indobenchmark/indobert-base-p1',local_files_only=True));model_hashes={p.name:sha(p) for p in snapshot.iterdir() if p.is_file()}
    tok=AutoTokenizer.from_pretrained(snapshot,local_files_only=True);m=AutoModel.from_pretrained(snapshot,local_files_only=True).eval()
    for p in m.parameters():p.requires_grad=False
    views={k:[] for k in ['cls','mean','last4']};valid_tokens=[]
    for off in range(0,740,16):
        rows=df.iloc[off:off+16];texts=[f'{r.headline_verified} [SEP] {r.supporting_text_verified}'.strip() for r in rows.itertuples()]
        enc=tok(texts,return_tensors='pt',truncation=True,max_length=128,padding='max_length')
        mask=enc['attention_mask'].bool()
        for token_id in tok.all_special_ids:mask=mask & (enc['input_ids']!=token_id)
        valid_tokens.extend(mask.sum(dim=1).tolist())
        with torch.inference_mode():
            out=m(**enc,output_hidden_states=True)
            raw={'cls':out.last_hidden_state[:,0,:],'mean':pool(out.last_hidden_state,mask),'last4':pool(torch.stack(out.hidden_states[-4:]).mean(dim=0),mask)}
            for k,v in raw.items():views[k].append(torch.nn.functional.normalize(v.float(),p=2,dim=1).numpy())
        if off%96==0:print('TEXT FEATURES',min(off+16,740),'seconds',round(time.monotonic()-start,1),flush=True)
    views={k:np.vstack(v) for k,v in views.items()}
    for v in views.values():assert v.shape==(740,768) and np.isfinite(v).all() and np.allclose(np.linalg.norm(v,axis=1),1,atol=2e-5)
    old=np.load(cache)['txt'];cos=(old*views['cls']).sum(axis=1);err=np.abs(old-views['cls']).max();assert cos.min()>.999999 and err<2e-5,(cos.min(),err)
    np.savez(OUT/'features.npz',sample_ids=df.sample_id.to_numpy(dtype=str),**views)
    report=dict(status='completed',samples=740,dim=768,pooling=['mean','last4'],labels_used=False,source_sha256=sha(Path(__file__)),csv_sha256=sha(csv),cache_sha256=sha(cache),feature_sha256=sha(OUT/'features.npz'),model_snapshot=snapshot.name,model_hashes=model_hashes,cls_parity=dict(samples=740,min_cosine=float(cos.min()),max_abs=float(err)),mask='attention and nonspecial token ids',max_length=128,min_valid_tokens=min(valid_tokens),seconds=time.monotonic()-start)
    (OUT/'features_manifest.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2),flush=True)
if __name__=='__main__':main()
