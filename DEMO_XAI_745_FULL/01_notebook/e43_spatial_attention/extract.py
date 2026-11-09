"""Label-free regional CLIP features; fixed spatial pooling, original two views."""
from pathlib import Path
import json,time,hashlib
import numpy as np,pandas as pd,torch,open_clip
from PIL import Image
from huggingface_hub import hf_hub_download
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'04_hasil_eksperimen/e43_spatial_attention'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def regions(tokens,projection):
    assert tokens.shape[1:]==(256,1024),tokens.shape
    spatial=tokens.reshape(-1,16,16,1024).permute(0,3,1,2)
    pooled=torch.nn.functional.avg_pool2d(spatial,kernel_size=4,stride=4).permute(0,2,3,1).reshape(-1,16,1024)
    return torch.nn.functional.normalize((pooled@projection).float(),dim=-1)
def load_visual():
    old=ROOT/'04_hasil_eksperimen/e36_clip_l14';manifest=json.loads((old/'features_manifest.json').read_text());pin=manifest['model']
    assert json.loads((old/'feature_verification.json').read_text())['status']=='passed'
    weights=Path(hf_hub_download(pin['repo'],pin['file'],revision=pin['revision'],local_files_only=True));assert sha(weights)==pin['sha256']
    pre=manifest['model_cfg'].get('preprocess_cfg',{})
    model,_,transform=open_clip.create_model_and_transforms('ViT-L-14',pretrained=str(weights),precision='fp32',image_mean=pre.get('mean'),image_std=pre.get('std'))
    visual=model.visual.eval();visual.output_tokens=True
    for p in visual.parameters():p.requires_grad=False
    return visual,transform,manifest
def views(row,transform):
    p=ROOT/'05_gambar'/Path(row.image_path).name;assert sha(p)==row.image_sha256
    with Image.open(p) as image:
        image=image.convert('RGB');w,h=image.size
        return transform(image),transform(image.crop((0,int(.20*h),w,int(.94*h))))
def main():
    torch.set_num_threads(8);start=time.monotonic();OUT.mkdir(parents=True,exist_ok=True);assert not (OUT/'features.npz').exists(),'Do not overwrite completed features'
    visual,transform,manifest=load_visual();csv=ROOT/'03_data/DATASET_740_TASK2_DOMAIN.csv';assert sha(csv)==manifest['csv_sha256']
    df=pd.read_csv(csv).fillna('');oldpath=ROOT/'04_hasil_eksperimen/e36_clip_l14/features.npz';assert sha(oldpath)==manifest['feature_sha256'];old=np.load(oldpath)
    assert len(df)==740 and df.sample_id.is_unique and df.sample_id.tolist()==old['sample_ids'].tolist();result=[];errors=[]
    for off in range(0,740,16):
        pairs=[views(row,transform) for row in df.iloc[off:off+16].itertuples()];tokens=[]
        for view,key in [(0,'full'),(1,'crop')]:
            with torch.inference_mode():
                global_feature,patch=visual(torch.stack([pair[view] for pair in pairs]));global_feature=torch.nn.functional.normalize(global_feature.float(),dim=1)
                err=float(np.abs(global_feature.numpy()-old[key][off:off+len(pairs)]).max());assert err<2e-5,err;errors.append(err)
                tokens.append(regions(patch,visual.proj).numpy())
        result.append(np.concatenate(tokens,axis=1));print('REGIONS',off+len(pairs),'seconds',round(time.monotonic()-start,1),flush=True)
    array=np.concatenate(result);assert array.shape==(740,32,768) and np.isfinite(array).all() and np.allclose(np.linalg.norm(array,axis=-1),1,atol=2e-5)
    np.savez_compressed(OUT/'features.npz',sample_ids=df.sample_id.to_numpy(dtype=str),regions=array)
    report=dict(status='completed',labels_used=False,samples=740,shape=list(array.shape),layout='full16 then crop16; row-major4x4 spatial averages of16x16 patchtokens, visual.proj then L2',model=manifest['model'],csv_sha256=sha(csv),image_sha256=df.image_sha256.tolist(),reference_features_sha256=sha(oldpath),source_sha256=sha(Path(__file__)),feature_sha256=sha(OUT/'features.npz'),all740_global_max_abs=max(errors),seconds=time.monotonic()-start)
    (OUT/'features_manifest.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ['status','shape','all740_global_max_abs','seconds']},indent=2))
if __name__=='__main__':main()
