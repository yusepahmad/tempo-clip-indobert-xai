"""Independent regional pooling forward checks, original image and source hashes."""
from extract import ROOT,OUT,sha,load_visual,views
from pathlib import Path
import json,numpy as np,pandas as pd,torch
def main():
    torch.set_num_threads(8);m=json.loads((OUT/'features_manifest.json').read_text())
    assert m['status']=='completed' and m['labels_used'] is False
    assert m['source_sha256']==sha(Path(__file__).with_name('extract.py')) and m['feature_sha256']==sha(OUT/'features.npz')
    csv=ROOT/'03_data/DATASET_740_TASK2_DOMAIN.csv';assert sha(csv)==m['csv_sha256'];df=pd.read_csv(csv).fillna('');z=np.load(OUT/'features.npz')
    assert z['sample_ids'].tolist()==df.sample_id.tolist() and z['regions'].shape==(740,32,768)
    assert np.isfinite(z['regions']).all() and np.allclose(np.linalg.norm(z['regions'],axis=-1),1,atol=2e-5)
    for row in df.itertuples():assert sha(ROOT/'05_gambar'/Path(row.image_path).name)==row.image_sha256
    visual,transform,pin=load_visual();assert pin['model']==m['model'];checks=[]
    for ix in [0,147,295,443,591,739]:
        images=views(df.iloc[ix],transform);parts=[]
        with torch.inference_mode():
            for image in images:
                _,tokens=visual(image[None]);grid=tokens.reshape(1,16,16,1024);cells=[]
                for r in range(4):
                    for c in range(4):cells.append(grid[:,r*4:(r+1)*4,c*4:(c+1)*4].mean(dim=(1,2)))
                projected=torch.stack(cells,dim=1)@visual.proj
                parts.append((projected/projected.norm(dim=-1,keepdim=True)).numpy())
        err=float(np.abs(np.concatenate(parts,axis=1)[0]-z['regions'][ix]).max());assert err<2e-5,err;checks.append(dict(index=ix,max_abs=err))
    report=dict(status='passed',samples=740,all_image_hashes=True,source_and_feature_hashes=True,layout_shape_unitnorm=True,independent_sampled_forward=checks,source_sha256=sha(Path(__file__)))
    (OUT/'feature_verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
