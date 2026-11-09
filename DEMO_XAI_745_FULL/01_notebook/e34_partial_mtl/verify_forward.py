"""Reconstruct every delta checkpoint and compare three heldout inputs per fold."""
import json,hashlib
from pathlib import Path
import numpy as np,pandas as pd,torch
from PIL import Image
from worker import PartialMTL,TASKS
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'04_hasil_eksperimen/e34_partial_mtl'
def main():
    torch.set_num_threads(8);df=pd.read_csv(ROOT/'03_data/DATASET_740_TASK2_DOMAIN.csv').fillna('');p=json.loads((OUT/'protocol.json').read_text());classes=p['classes'];m=PartialMTL({t:len(classes[t]) for t in TASKS});m.eval()
    base={n:v.detach().clone() for n,v in m.state_dict().items()};checks=[]
    for k in range(1,6):
        cp=torch.load(OUT/f'fold{k}_delta.pt',map_location='cpu',weights_only=True);m.load_state_dict(base);m.load_state_dict(cp['delta'],strict=False);m.eval()
        z=np.load(OUT/f'fold{k}_predictions.npz');positions=[0,73,147];indices=z['indices'][positions];ims=[];texts=[]
        for i in indices:
            r=df.iloc[i];im=Image.open(ROOT/'05_gambar'/Path(r.image_path).name).convert('RGB');ims.append(m.preprocess(im));texts.append(f'{r.headline_verified} [SEP] {r.supporting_text_verified}'.strip())
        tok=m.tokenizer(texts,truncation=True,max_length=128,padding='max_length',return_tensors='pt')
        with torch.inference_mode():pred=m(torch.stack(ims),tok['input_ids'],tok['attention_mask'])
        for t in TASKS:
            actual=pred[t].argmax(1).numpy();expected=z[t][positions]
            checks.append(dict(fold=k,task=t,indices=indices.tolist(),cpu_pred=actual.tolist(),gpu_pred=expected.tolist(),matched=bool(np.array_equal(actual,expected))))
    report=dict(status='passed' if all(c['matched'] for c in checks) else 'numerical_mismatch',samples=15,task_predictions=45,checks=checks,note='Reconstructed all five delta checkpoints on CPU FP32; GPU inference used AMP FP16. This is a sampled forward audit, not a full training/OOF rerun.')
    (OUT/'forward_verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(status=report['status'],samples=15,matched=sum(c['matched'] for c in checks),checks=len(checks)),indent=2))
    assert report['status']=='passed'
if __name__=='__main__':main()
