"""Reconstruct all outer-training retrievals and request prompts independently of preparer."""
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

def check_inputs():
    folder=ROOT/'04_hasil_eksperimen/e19_fewshot'
    config=json.loads((folder/'config.json').read_text())
    assert config['status']=='prepared_no_api_calls' and config['samples']==740
    assert config['worker_sha256']==sha(Path(__file__).with_name('prepare.py'))
    assert config['prompt_helper_sha256']==sha(ROOT/'01_notebook/kaggle_e15/prompt.py')
    assert config['examples_per_class']==2 and config['max_description_chars']==400
    assert config['max_reason_chars']==200 and config['max_headline_chars']==120
    csv=ROOT/'03_data/DATASET_740_TASK2_DOMAIN.csv'
    assert sha(csv)==config['csv_sha256']=='cba20f8250bcb59481ed2d3d7d5d42fb8242c96a7ba2d11a2cd02ad80862961a'
    df=pd.read_csv(csv).fillna('');assert len(df)==740 and df.sample_id.is_unique
    classes=sorted(DEFINITIONS);assert config['classes']==classes==sorted(set(df.task2_domain_sumber))
    path=ROOT/'04_hasil_eksperimen/e13_bge_m3/e13_bge_m3/embeddings.npz'
    assert sha(path)==config['bge_sha256']=='c0d7d1fc9ac42988b0d107a694d7d3b355105f8640f776ace2617eed936495c4'
    vectors=np.load(path,allow_pickle=False)
    assert np.array_equal(vectors['sample_id'],df.sample_id.to_numpy())
    x=vectors['combined'].astype(np.float64)
    assert x.shape==(740,1024) and np.isfinite(x).all()
    assert np.allclose(np.linalg.norm(x,axis=1),1,atol=1e-4)
    x=x/np.linalg.norm(x,axis=1,keepdims=True)
    e01=ROOT/'04_hasil_eksperimen/e01_vlm/kaggle_full/e01_vlm';sources=[]
    for name,digest in [('deskripsi.jsonl','c75e8df3f9b71d6786462f8d0f1187ebe4234fb8dd079924f3f35707ff1b8cd2'),
                        ('zeroshot.jsonl','10c07b06b13fbbf647f2b1ed12a722d9bff8f97caa6b621430d8bc0429ab38c9')]:
        assert sha(e01/name)==digest
        records=[json.loads(line) for line in (e01/name).read_text().splitlines()]
        lookup={r['sample_id']:r for r in records}
        assert len(lookup)==len(records)==740 and set(lookup)==set(df.sample_id)
        sources.append([lookup[sid] for sid in df.sample_id])
    descriptions,reasons=sources
    inputs=folder/'inputs.jsonl';assert sha(inputs)==config['inputs_sha256']
    rows=[json.loads(line) for line in inputs.read_text().splitlines()];assert len(rows)==740
    issues=pd.Categorical(df.task1_issue,categories=sorted(set(df.task1_issue))).codes
    counts=np.bincount(issues);strat=[v if counts[v]>=5 else -1 for v in issues]
    folds=list(StratifiedKFold(5,shuffle=True,random_state=42).split(np.zeros(740),strat))
    fold=np.zeros(740,dtype=int)
    for k,(_,test) in enumerate(folds,1):fold[test]=k
    labels=df.task2_domain_sumber.to_numpy()
    permuted=df.copy();permuted['task2_domain_sumber']=labels[::-1]
    for i,row in enumerate(rows):
        assert set(row)=={'index','sample_id','fold','examples','prompt','prompt_sha256','image_sha256'}
        assert row['index']==i and row['sample_id']==df.sample_id.iloc[i] and row['fold']==int(fold[i])
        train,test=folds[fold[i]-1];assert i in test and i not in train
        assert len(train)==592 and len(test)==148 and len(row['examples'])==14
        expected=[]
        for label in classes:
            candidates=train[labels[train]==label]
            sims=x[candidates]@x[i]
            ranked=sorted(zip(candidates.tolist(),sims.tolist()),key=lambda pair:(-pair[1],pair[0]))[:2]
            for j,similarity in ranked:
                expected.append((j,label,similarity))
        pieces=[];indices=[]
        for example,(j,label,sim) in zip(row['examples'],expected):
            assert example['index']==j and example['sample_id']==df.sample_id.iloc[j]
            assert example['label']==label and j not in test and j in train and i!=j
            assert abs(example['cosine']-sim)<1e-12
            code='ABCDEFG'[classes.index(label)];assert example['code']==code
            indices.append(j)
            reason=((reasons[j].get('sumber_visual') or '')+' '+(reasons[j].get('alasan') or ''))[:200]
            headline=(df.headline_verified.iloc[j]+' '+df.supporting_text_verified.iloc[j])[:120]
            pieces.append(f'Contoh training, kode {code} ({label}):\nDeskripsi: '+descriptions[j]['deskripsi'][:400]
                          +'\nSumber dan alasan: '+reason+'\nJudul dan teks: '+headline)
        assert len(set(indices))==14
        prefix='Berikut contoh berlabel dari data training untuk memahami kategori. Contoh tidak menentukan jawaban target secara otomatis.\n\n'
        prefix+='\n\n'.join(pieces)+'\n\nSekarang nilai TARGET berikut secara mandiri; gambar yang disertakan hanya milik target.\n'
        target=build_prompt(i,df,descriptions,reasons,classes)
        assert target==build_prompt(i,permuted,descriptions,reasons,classes)
        text=prefix+target
        assert row['prompt']==text and row['prompt_sha256']==hashlib.sha256(text.encode()).hexdigest()
        image=ROOT/'05_gambar'/Path(df.image_path.iloc[i]).name
        assert row['image_sha256']==sha(image)
    return config,rows,df,fold

if __name__=='__main__':
    config,rows,df,fold=check_inputs()
    result=dict(status='verified',samples=740,examples_checked=10360,
                inputs_sha256=config['inputs_sha256'],verifier_sha256=sha(Path(__file__)),
                checks=['all740 nearest rankings reconstructed independently',
                        'all10360 example IDs/labels belong only to target outer-training592',
                        'all740 full prompts and images reconstructed; query target permutation invariant'])
    out=ROOT/'04_hasil_eksperimen/e19_fewshot/input_verification.json'
    out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
