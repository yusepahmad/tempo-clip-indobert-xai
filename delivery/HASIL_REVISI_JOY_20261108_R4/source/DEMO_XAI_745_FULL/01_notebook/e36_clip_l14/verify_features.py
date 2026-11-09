"""Verify pinned weights, source/order/image hashes, norms and six CPU forwards."""
from pathlib import Path
import json,hashlib,os,sys
import numpy as np,pandas as pd,torch,open_clip
from PIL import Image
from huggingface_hub import hf_hub_download
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'04_hasil_eksperimen/e36_clip_l14'
def main():
    torch.set_num_threads(8);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();pin=json.loads(Path(__file__).with_name('pinned_model.json').read_text())
    weights=Path(hf_hub_download(pin['repo'],pin['file'],revision=pin['revision'],token=False));assert sha(weights)==pin['sha256']
    cfg_path=Path(hf_hub_download(pin['repo'],'open_clip_config.json',revision=pin['revision'],token=False));cfg=json.loads(cfg_path.read_text());pre=cfg.get('preprocess_cfg',{})
    if '--download-only' in sys.argv:print('Pinned CPU weights cached and verified',flush=True);return
    f=json.loads((OUT/'features_manifest.json').read_text());z=np.load(OUT/'features.npz');df=pd.read_csv(ROOT/'03_data/DATASET_740_TASK2_DOMAIN.csv').fillna('')
    assert f['model']==pin and f['model_cfg']==cfg and f['crop_roi']==[0,.20,1,.94]
    gpu_source=Path(__file__).with_name('extract.py');cpu_source=Path(__file__).with_name('cpu_extract_impl.py')
    assert cpu_source.read_text()==gpu_source.read_text().replace('torch.set_num_threads(2)','torch.set_num_threads(8)')
    expected_source=cpu_source if f['gpu_count']==0 else gpu_source
    assert f['source_sha256']==sha(expected_source) and f['feature_sha256']==sha(OUT/'features.npz')
    assert f['csv_sha256']==sha(ROOT/'03_data/DATASET_740_TASK2_DOMAIN.csv') and z['sample_ids'].tolist()==df.sample_id.tolist()
    for v in [z['full'],z['crop']]:assert v.shape==(740,768) and np.isfinite(v).all() and np.allclose(np.linalg.norm(v,axis=1),1,atol=2e-5)
    for i,row in df.iterrows():assert sha(ROOT/'05_gambar'/Path(row.image_path).name)==f['image_sha256'][i]==row.image_sha256
    m,_,transform=open_clip.create_model_and_transforms('ViT-L-14',pretrained=str(weights),precision='fp32',image_mean=pre.get('mean'),image_std=pre.get('std'));m.eval();indices=[0,147,295,443,591,739];checks=[]
    for i in indices:
        row=df.iloc[i];im=Image.open(ROOT/'05_gambar'/Path(row.image_path).name).convert('RGB');w,h=im.size;roi=im.crop((0,int(.20*h),w,int(.94*h)))
        with torch.inference_mode():v=m.encode_image(torch.stack([transform(im),transform(roi)]));v=torch.nn.functional.normalize(v.float(),p=2,dim=1).numpy()
        for j,name in enumerate(['full','crop']):
            cosine=float(np.dot(v[j],z[name][i]));maxabs=float(np.abs(v[j]-z[name][i]).max());assert cosine>.999999 and maxabs<2e-5,(i,name,cosine,maxabs)
            checks.append(dict(index=i,view=name,cosine=cosine,max_abs_error=maxabs))
    report=dict(status='passed',samples=740,all_image_hashes=True,unit_norm=True,pinned_lfs_hash=True,source_hash=True,cpu_reproduction=checks)
    (OUT/'feature_verification.json').write_text(json.dumps(report,indent=2)+'\n');print('FEATURE AUDIT PASSED',flush=True)
if __name__=='__main__':main()
