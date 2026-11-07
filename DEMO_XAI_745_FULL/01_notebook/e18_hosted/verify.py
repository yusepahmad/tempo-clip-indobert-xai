"""Independent reconstruction of740 inputs, response parsing, budget and seven-class F1."""
import hashlib
import io
import json
from pathlib import Path
import sys
import numpy as np
import pandas as pd
from PIL import Image
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import f1_score, classification_report

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT / '01_notebook/kaggle_e15'))
from prompt import DEFINITIONS, build_prompt
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
out = ROOT / '04_hasil_eksperimen/e18_hosted'
config = json.loads((out/'config.json').read_text())
assert config['model']=='google/gemini-3-flash-preview' and config['max_tokens']==2048
assert config['max_image_side']==384 and config['image_format']=='PNG' and config['budget_usd']==6.0
assert config['worker_sha256']==sha(Path(__file__).with_name('run.py'))
assert config['quota_source_sha256']==sha(Path(__file__).with_name('quota.py'))
assert config['prompt_helper_sha256']==sha(ROOT/'01_notebook/kaggle_e15/prompt.py')
csv=ROOT/'03_data/DATASET_740_TASK2_DOMAIN.csv'
assert config['csv_sha256']==sha(csv)=='cba20f8250bcb59481ed2d3d7d5d42fb8242c96a7ba2d11a2cd02ad80862961a'
df=pd.read_csv(csv).fillna(''); assert len(df)==740 and df.sample_id.is_unique
classes=sorted(DEFINITIONS); assert config['classes']==classes==sorted(set(df.task2_domain_sumber))
e01=ROOT/'04_hasil_eksperimen/e01_vlm/kaggle_full/e01_vlm'
sources=[]
for name,digest in [('deskripsi.jsonl','c75e8df3f9b71d6786462f8d0f1187ebe4234fb8dd079924f3f35707ff1b8cd2'),
                    ('zeroshot.jsonl','10c07b06b13fbbf647f2b1ed12a722d9bff8f97caa6b621430d8bc0429ab38c9')]:
    assert sha(e01/name)==digest
    rows=[json.loads(x) for x in (e01/name).read_text().splitlines()]
    lookup={x['sample_id']:x for x in rows}
    assert len(rows)==len(lookup)==740 and set(lookup)==set(df.sample_id)
    sources.append([lookup[sid] for sid in df.sample_id])
permuted=df.copy();permuted['task2_domain_sumber']=df.task2_domain_sumber.iloc[::-1].to_numpy()
files=sorted((out/'records').glob('*.json'))
assert len(files)==740 and [p.name for p in files]==[f'{i:04d}.json' for i in range(740)]
predictions=[]; costs=[]; evidence_hashes={};invalid=0
for i,p in enumerate(files):
    r=json.loads(p.read_text()); assert r['status']=='complete' and r['index']==i
    assert r['sample_id']==df.sample_id.iloc[i] and r['model']==config['model']
    assert r['config_sha256']==sha(out/'config.json')
    prompt=build_prompt(i,df,*sources,classes)
    assert prompt==build_prompt(i,permuted,*sources,classes)
    assert r['prompt_sha256']==hashlib.sha256(prompt.encode()).hexdigest()
    ip=ROOT/'05_gambar'/Path(df.image_path.iloc[i]).name
    assert r['image_sha256']==sha(ip)
    with Image.open(ip) as original:
        im=original.convert('RGB');im.thumbnail((384,384),Image.Resampling.LANCZOS)
        buffer=io.BytesIO();im.save(buffer,format='PNG')
    assert r['image_size']==list(im.size)
    assert r['transmitted_image_sha256']==hashlib.sha256(buffer.getvalue()).hexdigest()
    result=r['response'];assert result['model']==config['model'] and len(result['choices'])==1
    answer=(result['choices'][0]['message'].get('content') or '').strip()
    valid=len(answer)==1 and answer in 'ABCDEFG'
    code=answer if valid else 'INVALID'
    prediction=classes[ord(code)-ord('A')] if valid else 'INVALID'
    assert r['code']==code and r['prediction']==prediction
    assert r['finish_reason']==result['choices'][0].get('finish_reason')
    cost=result['usage']['cost']
    value=sum(cost[k] for k in ('input_tokens_cost_nanodollars','output_tokens_cost_nanodollars'))/1e9
    assert abs(value-r['cost_usd'])<1e-12 and 0<=value<=0.03
    assert len(r['quota_before'])==len(r['quota_after'])==2
    for before,after in zip(r['quota_before'],r['quota_after']):
        assert before['period']==after['period']
        assert abs(after['used']-before['used']-value)<1e-6
        assert after['remaining']>=0.1
    predictions.append(prediction);costs.append(value);invalid+=not valid
    evidence_hashes[str(p.relative_to(out))]=sha(p)
assert sum(costs)<=6
issue=pd.Categorical(df.task1_issue,categories=sorted(set(df.task1_issue))).codes
counts=np.bincount(issue);strat=np.array([x if counts[x]>=5 else -1 for x in issue])
fold=np.zeros(740,dtype=int)
for k,(_,test) in enumerate(StratifiedKFold(5,shuffle=True,random_state=42).split(np.zeros(740),strat),1):
    fold[test]=k
assert all(np.sum(fold==k)==148 for k in range(1,6))
truth=df.task2_domain_sumber.to_list()
# An eighth prediction column explicitly retains every malformed response as a false negative.
matrix=[[sum(t==label and pred==value for t,pred in zip(truth,predictions))
         for value in classes+['INVALID']] for label in classes]
per_class=[]
for j,label in enumerate(classes):
    tp=matrix[j][j];fn=sum(matrix[j])-tp;fp=sum(row[j] for row in matrix)-tp
    per_class.append(2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else 0.0)
manual=sum(per_class)/7
sk=float(f1_score(truth,predictions,labels=classes,average='macro',zero_division=0))
assert abs(manual-sk)<1e-12
oof=pd.DataFrame(dict(sample_id=df.sample_id,truth=truth,prediction=predictions,fold=fold))
oof.to_csv(out/'oof.csv',index=False)
metrics=dict(protocol='zero_shot_no_fit',samples=740,macro_f1=manual,invalid_predictions=invalid,
             cost_usd=sum(costs),classes=classes,prediction_columns=classes+['INVALID'],
             confusion_matrix=matrix,per_class_f1=per_class,
             fold_macro_f1={str(k):float(f1_score(np.array(truth)[fold==k],np.array(predictions)[fold==k],
                 labels=classes,average='macro',zero_division=0)) for k in range(1,6)},
             classification=classification_report(truth,predictions,labels=classes,output_dict=True,zero_division=0),
             config_sha256=sha(out/'config.json'),oof_sha256=sha(out/'oof.csv'))
(out/'metrics.json').write_text(json.dumps(metrics,indent=2)+'\n')
verification=dict(status='verified',samples=740,macro_f1=manual,verifier_sha256=sha(Path(__file__)),
                  checks=['740 aligned IDs/labels/baseline folds', '740 input image/prompt reconstructions; target permutation invariant',
                          '740 cached responses parsed independently; INVALID retained as wrong',
                          'usage costs reconcile with official quota for each request; budget6USD',
                          'manual confusion/F1 match sklearn; hosted inference not reproduced'],
                  sha256={'config.json':sha(out/'config.json'),'metrics.json':sha(out/'metrics.json'),
                          'oof.csv':sha(out/'oof.csv'),**evidence_hashes})
(out/'verification.json').write_text(json.dumps(verification,indent=2)+'\n')
print(json.dumps(metrics,indent=2))
