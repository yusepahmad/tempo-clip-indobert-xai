"""Reconstruct every E07 retrieval/prompt and independently count OOF F1."""
import ast
import hashlib
import json
from pathlib import Path
import re
import sys
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import StratifiedKFold

root,out,description_path=map(Path,sys.argv[1:])
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
worker=root/'01_notebook/kaggle_e07/worker.py'
rules=next(ast.literal_eval(n.value) for n in ast.parse(worker.read_text()).body
           if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='RULES' for t in n.targets))
cfg=json.loads((out/'config.json').read_text());metrics=json.loads((out/'metrics.json').read_text())
assert not cfg['smoke'] and not metrics['smoke'] and metrics['status']=='complete'
assert cfg['worker_sha256']==sha(worker) and cfg['rules_sha256']==hashlib.sha256(rules.encode()).hexdigest()
csv=root/'03_data/DATASET_740_TASK2_DOMAIN.csv'
assert cfg['csv_sha256']==sha(csv)=='cba20f8250bcb59481ed2d3d7d5d42fb8242c96a7ba2d11a2cd02ad80862961a'
assert cfg['description_sha256']==sha(description_path)=='c75e8df3f9b71d6786462f8d0f1187ebe4234fb8dd079924f3f35707ff1b8cd2'
assert cfg['revision']=='0c351dd01ed87e9c1b53cbc748cba10e6187ff3b'
df=pd.read_csv(csv).fillna('')
lookup={r['sample_id']:r['deskripsi'] for r in map(json.loads,description_path.read_text().splitlines())}
assert len(lookup)==740 and set(lookup)==set(df.sample_id)
desc=np.array([lookup[sid] for sid in df.sample_id]);title=(df.headline_verified+' '+df.supporting_text_verified).to_numpy()
texts=desc+' '+title;y=df.task2_domain_sumber.to_numpy();classes=sorted(set(y))
rows=list(map(json.loads,(out/'predictions.jsonl').read_text().splitlines()))
assert len(rows)==len({r['sample_id'] for r in rows})==740
by_index={r['index']:r for r in rows};assert set(by_index)==set(range(740))
issues=pd.Categorical(df.task1_issue,categories=sorted(set(df.task1_issue))).codes
counts=np.bincount(issues);strat=np.array([v if counts[v]>=5 else -1 for v in issues])
for fold,(tr,te) in enumerate(StratifiedKFold(5,shuffle=True,random_state=42).split(np.zeros(740),strat),1):
    vector=TfidfVectorizer(ngram_range=(1,2),min_df=2,sublinear_tf=True)
    train=vector.fit_transform(texts[tr]);test=vector.transform(texts[te])
    for j,idx in enumerate(te):
        r=by_index[int(idx)];assert r['sample_id']==df.sample_id.iloc[idx] and r['fold']==fold
        similarity=(train@test[j].T).toarray().ravel();examples=[]
        for label in classes:
            candidates=np.where(y[tr]==label)[0]
            best=candidates[np.argsort(-similarity[candidates],kind='stable')[:2]]
            examples.extend(tr[best].tolist())
        assert len(set(examples))==14 and set(examples)<=set(tr) and not set(examples)&set(te)
        assert r['exemplars']==df.sample_id.iloc[examples].tolist()
        demo=[f'Contoh: {desc[i][:650]}\nJudul: {title[i][:200]}\nLabel: {y[i]}' for i in examples]
        prompt=rules+'\n\n'+'\n\n'.join(demo)+f'\n\nTARGET:\nDeskripsi: {desc[idx]}\nJudul dan teks: {title[idx]}\nLabel:'
        assert r['prompt_sha256']==hashlib.sha256(prompt.encode()).hexdigest()
        found=[c for c in classes if re.search(r'\b'+c+r'\b',r['answer'].upper())]
        assert len(found)==1 and r['prediction']==found[0]
scores={}
for c in classes:
    tp=sum(y[i]==c and by_index[i]['prediction']==c for i in range(740))
    fp=sum(y[i]!=c and by_index[i]['prediction']==c for i in range(740))
    fn=sum(y[i]==c and by_index[i]['prediction']!=c for i in range(740))
    scores[c]=2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else 0
score=sum(scores.values())/7
assert abs(score-metrics['macro_f1'])<1e-12 and metrics['valid']
result={'status':'verified','samples':740,'macro_f1_manual':score,'per_class_f1':scores,
        'checks':['source/data/description/revision hashes','all baseline folds and original IDs',
                  'all 740 retrievals exactly reconstructed','14 training exemplars, two per class',
                  'all 740 prompt hashes reconstructed','valid parsed labels','manual TP/FP/FN score'],
        'sha256':{p.name:sha(p) for p in sorted(out.iterdir()) if p.is_file() and p.name!='verification.json'}}
(out/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
