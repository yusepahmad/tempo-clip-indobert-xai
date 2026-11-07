"""Three pinned decoders plus training-only fallback; all final OOF predictions are seven-class."""
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.metrics import f1_score,confusion_matrix
from sklearn.model_selection import StratifiedKFold
from parse import parse_answer as parse_v1
from parse_v2 import parse_answer as parse_v2
from valid_labels import training_majority_fallback

ROOT=Path(__file__).resolve().parents[2]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
prior=ROOT/'04_hasil_eksperimen/e18_hosted'
verified=json.loads((prior/'verification.json').read_text())
assert verified['status']=='verified' and verified['samples']==740
assert verified['verifier_sha256']==sha(Path(__file__).with_name('verify.py'))
for name,digest in verified['sha256'].items():assert sha(prior/name)==digest
config=json.loads((prior/'config.json').read_text())
assert config['worker_sha256']==sha(Path(__file__).with_name('run.py'))
assert config['protocol']=='zero_shot_no_fit_no_target_in_prompt_no_retries_invalid_counts_wrong'
csv=ROOT/'03_data/DATASET_740_TASK2_DOMAIN.csv'
assert sha(csv)==config['csv_sha256']=='cba20f8250bcb59481ed2d3d7d5d42fb8242c96a7ba2d11a2cd02ad80862961a'
df=pd.read_csv(csv).fillna('');assert len(df)==740 and df.sample_id.is_unique
truth=df.task2_domain_sumber.to_list();classes=config['classes'];assert classes==sorted(set(truth))
issues=pd.Categorical(df.task1_issue,categories=sorted(set(df.task1_issue))).codes
counts=np.bincount(issues);strat=[x if counts[x]>=5 else -1 for x in issues]
fold=np.zeros(740,dtype=int)
for k,(_,test) in enumerate(StratifiedKFold(5,shuffle=True,random_state=42).split(np.zeros(740),strat),1):fold[test]=k
cached=[]
for i in range(740):
    r=json.loads((prior/'records'/f'{i:04d}.json').read_text())
    assert r['status']=='complete' and r['index']==i and r['sample_id']==df.sample_id.iloc[i]
    cached.append(r['response']['choices'][0]['message'].get('content') or '')
routes={};source_hashes={}
for route,relative,parser_file,evaluator_file in [('v1','parsed','parse.py','evaluate_parsed.py'),
                                                ('v2','parsed_v2','parse_v2.py','evaluate_parsed_v2.py')]:
    report=json.loads((prior/relative/'metrics.json').read_text())
    assert report['status']=='verified' and report['samples']==740
    assert report['strict_verification_sha256']==sha(prior/'verification.json')
    assert report['parser_sha256']==sha(Path(__file__).with_name(parser_file))
    assert report['evaluator_sha256']==sha(Path(__file__).with_name(evaluator_file))
    assert report['oof_sha256']==sha(prior/relative/'oof.csv')
    source_hashes[route]=sha(prior/relative/'metrics.json')
out=prior/'valid';out.mkdir(exist_ok=True);hashes={}
for route in ('strict','v1','v2'):
    codes=[]
    for content in cached:
        text=content.strip()
        code=(text if len(text)==1 and text in 'ABCDEFG' else 'INVALID') if route=='strict' else (
            parse_v1(content,classes)[0] if route=='v1' else parse_v2(content,classes)[0])
        codes.append(code)
    raw=[classes[ord(code)-65] if code!='INVALID' else 'INVALID' for code in codes]
    reference=prior/('oof.csv' if route=='strict' else ('parsed/oof.csv' if route=='v1' else 'parsed_v2/oof.csv'))
    original=pd.read_csv(reference).fillna('')
    assert original.sample_id.to_list()==df.sample_id.to_list() and original.truth.to_list()==truth
    assert original.prediction.to_list()==raw and np.array_equal(original.fold.to_numpy(),fold)
    final,applied,policies=training_majority_fallback(raw,truth,fold.tolist(),classes)
    assert all(p['training_samples']==592 and p['test_samples']==148 for p in policies.values())
    matrix=[[sum(t==a and p==b for t,p in zip(truth,final)) for b in classes] for a in classes]
    per_class=[]
    for j in range(7):
        tp=matrix[j][j];fn=sum(matrix[j])-tp;fp=sum(r[j] for r in matrix)-tp
        per_class.append(2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else 0.0)
    score=sum(per_class)/7
    assert abs(score-f1_score(truth,final,average='macro',zero_division=0))<1e-12
    assert matrix==confusion_matrix(truth,final,labels=classes).tolist()
    dest=out/route;dest.mkdir(exist_ok=True)
    pd.DataFrame(dict(sample_id=df.sample_id,truth=truth,prediction=final,fold=fold,
                      raw_prediction=raw,fallback_applied=applied,
                      fallback_class=[policies[str(k)]['label'] for k in fold])).to_csv(dest/'oof.csv',index=False)
    metrics=dict(status='verified',samples=740,route=route,macro_f1=score,raw_invalid_predictions=sum(applied),
                 protocol='zero_shot_plus_outer_training_majority_fallback',classes=classes,
                 confusion_matrix=matrix,per_class_f1=per_class,fallback_policies=policies,
                 verifier_sha256=sha(Path(__file__)),fallback_source_sha256=sha(Path(__file__).with_name('valid_labels.py')),
                 original_verification_sha256=sha(prior/'verification.json'),oof_sha256=sha(dest/'oof.csv'),
                 parsed_metrics_sha256=source_hashes.get(route))
    (dest/'metrics.json').write_text(json.dumps(metrics,indent=2)+'\n')
    routes[route]=dict(macro_f1=score,raw_invalid_predictions=sum(applied))
    for name in ('oof.csv','metrics.json'):hashes[f'{route}/{name}']=sha(dest/name)
result=dict(status='verified',samples=740,routes=routes,verifier_sha256=sha(Path(__file__)),
            fallback_source_sha256=sha(Path(__file__).with_name('valid_labels.py')),
            checks=['all740 final predictions are seven known classes; raw answers retained',
                    'each fallback selected solely by592 outer-training counts; tie alphabetic',
                    'all strict/v1/v2 decoders reproduced from immutable response cache',
                    'all740 original IDs/labels/folds and manual7x7/macroF1 checked'],sha256=hashes)
(out/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
