"""Label-free frozen front cache; no trainable weights or labels fitted here."""
from pathlib import Path
import json,time,hashlib
import torch,numpy as np,pandas as pd
from transformers import AutoModel,AutoTokenizer
from huggingface_hub import snapshot_download
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'04_hasil_eksperimen/e41_cached_tail/cache'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    torch.set_num_threads(8);start=time.monotonic();OUT.mkdir(parents=True,exist_ok=True);assert not (OUT/'cache_manifest.json').exists()
    csv=ROOT/'03_data/DATASET_740_TASK2_DOMAIN.csv';df=pd.read_csv(csv).fillna('');assert len(df)==740 and df.sample_id.is_unique
    tf=ROOT/'04_hasil_eksperimen/e37_token_pool';vf=ROOT/'04_hasil_eksperimen/e36_clip_l14'
    for folder in [tf,vf]:
        assert json.loads((folder/'feature_verification.json').read_text())['status']=='passed'
        fm=json.loads((folder/'features_manifest.json').read_text());assert fm['feature_sha256']==sha(folder/'features.npz') and fm['csv_sha256']==sha(csv)
    text_manifest=json.loads((tf/'features_manifest.json').read_text());snap=Path(snapshot_download('indobenchmark/indobert-base-p1',revision=text_manifest['model_snapshot'],local_files_only=True))
    for name,digest in text_manifest['model_hashes'].items():assert sha(snap/name)==digest
    tok=AutoTokenizer.from_pretrained(snap,local_files_only=True);m=AutoModel.from_pretrained(snap,local_files_only=True).eval();m.config._attn_implementation='sdpa'
    for p in m.parameters():p.requires_grad=False
    hidden=[];attention=[];pool=[];base=[];sample_checks=[]
    for off in range(0,740,16):
        rows=df.iloc[off:off+16];texts=[f'{r.headline_verified} [SEP] {r.supporting_text_verified}'.strip() for r in rows.itertuples()]
        enc=tok(texts,return_tensors='pt',truncation=True,max_length=128,padding='max_length');mask=enc['attention_mask'].bool();pm=mask.clone()
        for token_id in tok.all_special_ids:pm &= enc['input_ids']!=token_id
        assert pm.any(dim=1).all()
        with torch.inference_mode():
            out=m(**enc,output_hidden_states=True);h10=out.hidden_states[10].clone();h10[~mask]=0
            mean=(out.last_hidden_state*pm.unsqueeze(-1)).sum(dim=1)/pm.sum(dim=1,keepdim=True)
            base.append(torch.nn.functional.normalize(mean.float(),p=2,dim=1).numpy())
            if off in [0,144,288,432,576,736]:
                h=h10[:1];am=(~mask[:1,None,None,:]).to(h.dtype)*torch.finfo(h.dtype).min
                for layer in m.encoder.layer[-2:]:h=layer(h,attention_mask=am)
                err=float((h[mask[:1]]-out.last_hidden_state[:1][mask[:1]]).abs().max());assert err<2e-4,(off,err);sample_checks.append(dict(index=off,max_abs_valid_token=err))
        hidden.append(h10.numpy());attention.append(mask.numpy().astype(np.uint8));pool.append(pm.numpy().astype(np.uint8))
        if off%96==0:print('FROZEN FRONT',min(off+16,740),'seconds',round(time.monotonic()-start,1),flush=True)
    base=np.vstack(base);old=np.load(tf/'features.npz');visual=np.load(vf/'features.npz');assert old['sample_ids'].tolist()==visual['sample_ids'].tolist()==df.sample_id.tolist()
    error=float(np.abs(base-old['mean']).max());assert error<2e-5
    np.savez_compressed(OUT/'front_cache.npz',sample_ids=df.sample_id.to_numpy(dtype=str),h10=np.concatenate(hidden),attention=np.vstack(attention),pool_mask=np.vstack(pool),base_mean=base,visual=np.hstack([visual['full'],visual['crop']]).astype(np.float32))
    tail=torch.nn.ModuleList(list(m.encoder.layer[-2:]));torch.save(tail.state_dict(),OUT/'tail_initial.pt');(OUT/'bert_config.json').write_text(json.dumps(m.config.to_dict(),indent=2)+'\n')
    import shutil
    shutil.copy2(csv,OUT/csv.name);shutil.copy2(ROOT/'04_hasil_eksperimen/e33_joint_mtl/oof.csv',OUT/'baseline_oof.csv')
    report=dict(status='completed',samples=740,labels_used_for_extraction=False,padding_zeroed_only=True,base_mean_all740_max_abs=error,full_vs_cached_tail=sample_checks,model_snapshot=snap.name,model_hashes=text_manifest['model_hashes'],source_sha256=sha(Path(__file__)),inputs={str(p.relative_to(ROOT)):sha(p) for p in [csv,tf/'features.npz',tf/'features_manifest.json',vf/'features.npz',vf/'features_manifest.json']},files={p.name:sha(p) for p in OUT.iterdir() if p.is_file()},seconds=time.monotonic()-start,torch=torch.__version__)
    (OUT/'cache_manifest.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ['status','samples','base_mean_all740_max_abs','seconds']},indent=2),flush=True)
if __name__=='__main__':main()
