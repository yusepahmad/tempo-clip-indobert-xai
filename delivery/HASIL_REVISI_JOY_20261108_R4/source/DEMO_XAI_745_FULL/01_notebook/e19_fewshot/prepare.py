"""Freeze label-blind queries and14 outer-training-only retrieval examples per target."""
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedKFold

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'01_notebook/kaggle_e15'))
from prompt import DEFINITIONS,build_prompt
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
csv=ROOT/'03_data/DATASET_740_TASK2_DOMAIN.csv'
assert sha(csv)=='cba20f8250bcb59481ed2d3d7d5d42fb8242c96a7ba2d11a2cd02ad80862961a'
df=pd.read_csv(csv).fillna('');assert len(df)==740 and df.sample_id.is_unique
labels=df.task2_domain_sumber.to_numpy();classes=sorted(DEFINITIONS)
assert sorted(set(labels))==classes
bge=ROOT/'04_hasil_eksperimen/e13_bge_m3/e13_bge_m3'
assert sha(bge/'embeddings.npz')=='c0d7d1fc9ac42988b0d107a694d7d3b355105f8640f776ace2617eed936495c4'
meta=json.loads((bge/'meta.json').read_text())
assert meta['model']=='BAAI/bge-m3' and meta['revision']=='5617a9f61b028005a4858fdac845db406aefb181'
z=np.load(bge/'embeddings.npz',allow_pickle=False)
assert np.array_equal(z['sample_id'],df.sample_id.to_numpy())
x=z['combined'].astype(np.float64)
assert x.shape==(740,1024) and np.isfinite(x).all()
assert np.allclose(np.linalg.norm(x,axis=1),1,atol=1e-4)
x/=np.linalg.norm(x,axis=1,keepdims=True)
similarity=x@x.T
e01=ROOT/'04_hasil_eksperimen/e01_vlm/kaggle_full/e01_vlm'
sources=[]
for name,digest in [('deskripsi.jsonl','c75e8df3f9b71d6786462f8d0f1187ebe4234fb8dd079924f3f35707ff1b8cd2'),
                    ('zeroshot.jsonl','10c07b06b13fbbf647f2b1ed12a722d9bff8f97caa6b621430d8bc0429ab38c9')]:
    assert sha(e01/name)==digest
    records=[json.loads(line) for line in (e01/name).read_text().splitlines()]
    lookup={r['sample_id']:r for r in records}
    assert len(records)==len(lookup)==740 and set(lookup)==set(df.sample_id)
    sources.append([lookup[sid] for sid in df.sample_id])
descriptions,reasons=sources
issues=pd.Categorical(df.task1_issue,categories=sorted(set(df.task1_issue))).codes
counts=np.bincount(issues);strat=np.array([v if counts[v]>=5 else -1 for v in issues])
folds=list(StratifiedKFold(5,shuffle=True,random_state=42).split(np.zeros(740),strat))
foldid=np.zeros(740,dtype=int)
for k,(_,test) in enumerate(folds,1):foldid[test]=k
assert all(np.sum(foldid==k)==148 for k in range(1,6))
out=ROOT/'04_hasil_eksperimen/e19_fewshot';out.mkdir(exist_ok=True)
assert not (out/'inputs.jsonl').exists(), 'Do not overwrite frozen inputs'
def example_text(j):
    label=labels[j];code='ABCDEFG'[classes.index(label)]
    reason=((reasons[j].get('sumber_visual') or '')+' '+(reasons[j].get('alasan') or ''))[:200]
    headline=(df.headline_verified.iloc[j]+' '+df.supporting_text_verified.iloc[j])[:120]
    return (f'Contoh training, kode {code} ({label}):\nDeskripsi: '+descriptions[j]['deskripsi'][:400]
            +'\nSumber dan alasan: '+reason+'\nJudul dan teks: '+headline)
def query_prompt(i,selected,frame):
    prefix='Berikut contoh berlabel dari data training untuk memahami kategori. Contoh tidak menentukan jawaban target secara otomatis.\n\n'
    prefix+='\n\n'.join(example_text(j) for j in selected)
    return prefix+'\n\nSekarang nilai TARGET berikut secara mandiri; gambar yang disertakan hanya milik target.\n'+build_prompt(i,frame,descriptions,reasons,classes)
permuted=df.copy();permuted['task2_domain_sumber']=df.task2_domain_sumber.iloc[::-1].to_numpy()
config=dict(status='prepared_no_api_calls',samples=740,model='google/gemini-3-flash-preview',
            protocol='outer5_task1_seed42_two_cosine_nearest_per_training_class_no_tuning',examples_per_class=2,
            max_description_chars=400,max_reason_chars=200,max_headline_chars=120,
            worker_sha256=sha(Path(__file__)),csv_sha256=sha(csv),
            bge_sha256=sha(bge/'embeddings.npz'),bge_revision=meta['revision'],
            prompt_helper_sha256=sha(ROOT/'01_notebook/kaggle_e15/prompt.py'),classes=classes)
prepared=[]
for i in range(740):
    train,test=folds[foldid[i]-1];assert i in test and i not in train
    selected=[];trace=[]
    for label in classes:
        candidates=train[labels[train]==label]
        assert len(candidates)>=2
        ordered=candidates[np.lexsort((candidates,-similarity[i,candidates]))]
        chosen=ordered[:2];selected.extend(chosen.tolist())
        assert all(similarity[i,chosen[-1]]>=similarity[i,j]-1e-12 for j in ordered[2:])
        for j in chosen:
            assert j in train and j not in test and i!=j
            trace.append(dict(index=int(j),sample_id=df.sample_id.iloc[j],label=labels[j],
                              code='ABCDEFG'[classes.index(label)],cosine=float(similarity[i,j])))
    assert len(selected)==len(set(selected))==14
    assert all(sum(labels[j]==label for j in selected)==2 for label in classes)
    text=query_prompt(i,selected,df)
    assert text==query_prompt(i,selected,permuted)
    image=ROOT/'05_gambar'/Path(df.image_path.iloc[i]).name
    prepared.append(dict(index=i,sample_id=df.sample_id.iloc[i],fold=int(foldid[i]),examples=trace,
                         prompt=text,prompt_sha256=hashlib.sha256(text.encode()).hexdigest(),
                         image_sha256=sha(image)))
with (out/'inputs.jsonl').open('w') as f:
    for row in prepared:f.write(json.dumps(row,ensure_ascii=False)+'\n')
config.update(inputs_sha256=sha(out/'inputs.jsonl'),min_prompt_chars=min(len(r['prompt']) for r in prepared),
              max_prompt_chars=max(len(r['prompt']) for r in prepared),
              mean_prompt_chars=sum(len(r['prompt']) for r in prepared)/740,
              checks=['740 target queries;14 unique examples each;2 per class',
                      'all examples from target outer-training592; none from148 outer-test',
                      'cosine nearest ranking with stable index tie-break',
                      'query prompt invariant under target-label permutation',
                      'target labels absent from input manifest; example labels are training only'])
(out/'config.json').write_text(json.dumps(config,indent=2)+'\n')
print(json.dumps(config,indent=2))
