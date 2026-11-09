"""Frozen full/crop CLIP-L14 features; no labels used in extraction."""
import os,time,json,hashlib,sys
from pathlib import Path
import numpy as np,pandas as pd,torch,open_clip
from PIL import Image
from huggingface_hub import hf_hub_download

def extract(root,out,pin,device):
    start=time.monotonic();torch.set_num_threads(2);torch.backends.cuda.matmul.allow_tf32=False;torch.backends.cudnn.allow_tf32=False
    out.mkdir(parents=True,exist_ok=True);csv=root/'03_data/DATASET_740_TASK2_DOMAIN.csv';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    assert sha(csv)==os.environ['TEMPO_EXPECTED_CSV_SHA'];df=pd.read_csv(csv).fillna('');assert len(df)==740 and df.sample_id.is_unique
    weights=Path(hf_hub_download(pin['repo'],pin['file'],revision=pin['revision'],token=False));assert weights.stat().st_size==pin['bytes'] and sha(weights)==pin['sha256']
    cfg_path=Path(hf_hub_download(pin['repo'],'open_clip_config.json',revision=pin['revision'],token=False));cfg=json.loads(cfg_path.read_text());pre=cfg.get('preprocess_cfg',{})
    m,_,transform=open_clip.create_model_and_transforms('ViT-L-14',pretrained=str(weights),precision='fp32',image_mean=pre.get('mean'),image_std=pre.get('std'))
    visual=m.visual.eval().to(device);del m
    for p in visual.parameters():p.requires_grad=False
    full=[];crop=[];hashes=[];gpu_count=torch.cuda.device_count() if device=='cuda' else 0
    print('PINNED MODEL',pin['revision'],'device',device,'allocated',gpu_count,flush=True)
    for off in range(0,740,16):
        a=[];b=[]
        for row in df.iloc[off:off+16].itertuples():
            p=root/'05_gambar'/Path(row.image_path).name;digest=sha(p);assert digest==row.image_sha256,row.sample_id;hashes.append(digest)
            with Image.open(p) as im:
                im=im.convert('RGB');w,h=im.size;roi=im.crop((0,int(.20*h),w,int(.94*h)))
                a.append(transform(im));b.append(transform(roi))
        with torch.inference_mode():
            va=visual(torch.stack(a).to(device)).float();vb=visual(torch.stack(b).to(device)).float()
            full.append(torch.nn.functional.normalize(va,p=2,dim=1).cpu().numpy());crop.append(torch.nn.functional.normalize(vb,p=2,dim=1).cpu().numpy())
        if (off//16)%6==0:print('FEATURES',min(off+16,740),'seconds',round(time.monotonic()-start,1),flush=True)
        if device=='cuda' and (time.monotonic()-start)*max(gpu_count,1)>900:raise RuntimeError('GPU budget guard; no partial features accepted')
    full=np.vstack(full);crop=np.vstack(crop)
    for v in [full,crop]:assert v.shape==(740,768) and np.isfinite(v).all() and np.allclose(np.linalg.norm(v,axis=1),1,atol=2e-5)
    np.savez(out/'features.npz',sample_ids=df.sample_id.to_numpy(dtype=str),full=full,crop=crop)
    report=dict(status='completed',model=pin,model_cfg=cfg,csv_sha256=sha(csv),feature_sha256=sha(out/'features.npz'),image_sha256=hashes,
        source_sha256=sha(Path(__file__)),crop_roi=[0,.20,1,.94],samples=740,dim=768,seconds=time.monotonic()-start,
        gpu_count=gpu_count,gpu_name=torch.cuda.get_device_name(0) if gpu_count else None,torch=torch.__version__,open_clip=open_clip.__version__,dtype='float32; TF32 disabled',labels_used=False)
    (out/'features_manifest.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ['status','samples','dim','seconds','gpu_name']},indent=2),flush=True)
if __name__=='__main__':
    assert torch.cuda.is_available() and 1<=torch.cuda.device_count()<=2
    root=next(Path('/kaggle/input').rglob('DATASET_740_TASK2_DOMAIN.csv')).parents[1]
    pin=json.loads(os.environ['TEMPO_MODEL_PIN']);extract(root,Path('/kaggle/working/e36_clip_l14'),pin,'cuda')
