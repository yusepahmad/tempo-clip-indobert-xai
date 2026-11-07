"""Package audited frozen features for private offline training."""
from extract import ROOT,OUT,sha
import json,shutil,numpy as np,pandas as pd
def main():
    folders={k:ROOT/'04_hasil_eksperimen'/v for k,v in [('regional','e43_spatial_attention'),('visual','e36_clip_l14'),('text','e37_token_pool')]}
    csv=ROOT/'03_data/DATASET_740_TASK2_DOMAIN.csv';inputs=[]
    for folder in folders.values():
        assert json.loads((folder/'feature_verification.json').read_text())['status']=='passed'
        m=json.loads((folder/'features_manifest.json').read_text());assert sha(folder/'features.npz')==m['feature_sha256'] and m['csv_sha256']==sha(csv)
        inputs.extend([folder/'features.npz',folder/'features_manifest.json',folder/'feature_verification.json'])
    csv=ROOT/'03_data/DATASET_740_TASK2_DOMAIN.csv';df=pd.read_csv(csv).fillna('');assert len(df)==740 and df.sample_id.is_unique
    regional=np.load(folders['regional']/'features.npz');visual=np.load(folders['visual']/'features.npz');text=np.load(folders['text']/'features.npz')
    for z in [regional,visual,text]:assert z['sample_ids'].tolist()==df.sample_id.tolist()
    package=OUT/'package';package.mkdir(exist_ok=True);assert not (package/'manifest.json').exists()
    np.savez_compressed(package/'training_features.npz',sample_ids=df.sample_id.to_numpy(dtype=str),regions=regional['regions'],visual=np.hstack([visual['full'],visual['crop']]),mean=text['mean'],cls=text['cls'])
    baseline=ROOT/'04_hasil_eksperimen/e41_cached_tail/cache/baseline_oof.csv'
    shutil.copy2(csv,package/csv.name);shutil.copy2(baseline,package/'baseline_oof.csv');inputs.extend([csv,baseline,Path(__file__)])
    report=dict(status='audited_package',samples=740,inputs={str(p.relative_to(ROOT)):sha(p) for p in inputs},files={p.name:sha(p) for p in package.iterdir() if p.is_file()})
    (package/'manifest.json').write_text(json.dumps(report,indent=2)+'\n');print('PACKAGE READY')
from pathlib import Path
if __name__=='__main__':main()
