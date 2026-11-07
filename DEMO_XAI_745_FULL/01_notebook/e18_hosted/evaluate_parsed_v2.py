"""Evaluate second fixed explicit-answer parser on independently verified strict740 cache."""
import hashlib
import json
from pathlib import Path
import pandas as pd
from sklearn.metrics import f1_score
from parse_v2 import parse_answer

ROOT=Path(__file__).resolve().parents[2]
out=ROOT/'04_hasil_eksperimen/e18_hosted'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
verified=json.loads((out/'verification.json').read_text())
assert verified['status']=='verified' and verified['samples']==740
assert verified['verifier_sha256']==sha(Path(__file__).with_name('verify.py'))
for name,digest in verified['sha256'].items():assert sha(out/name)==digest
config=json.loads((out/'config.json').read_text());classes=config['classes']
strict=pd.read_csv(out/'oof.csv').fillna('')
assert len(strict)==740 and strict.sample_id.is_unique
truth=strict.truth.to_list(); predictions=[]; rows=[]; rules={}
for i,row in strict.iterrows():
    response=json.loads((out/'records'/f'{i:04d}.json').read_text())
    assert response['index']==i and response['sample_id']==row.sample_id
    content=response['response']['choices'][0]['message'].get('content')
    code,rule=parse_answer(content,classes)
    prediction=classes[ord(code)-ord('A')] if code!='INVALID' else 'INVALID'
    if response['code']!='INVALID':assert code==response['code']
    predictions.append(prediction);rules[rule]=rules.get(rule,0)+1
    rows.append(dict(sample_id=row.sample_id,truth=row.truth,prediction=prediction,fold=int(row.fold),
                     strict_prediction=row.prediction,parsing_rule=rule))
matrix=[[sum(t==label and pred==value for t,pred in zip(truth,predictions))
         for value in classes+['INVALID']] for label in classes]
f1=[]
for j in range(7):
    tp=matrix[j][j];fn=sum(matrix[j])-tp;fp=sum(r[j] for r in matrix)-tp
    f1.append(2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else 0.0)
score=sum(f1)/7
assert abs(score-f1_score(truth,predictions,labels=classes,average='macro',zero_division=0))<1e-12
parsed=out/'parsed_v2';parsed.mkdir(exist_ok=True)
pd.DataFrame(rows).to_csv(parsed/'oof.csv',index=False)
metrics=dict(status='verified',samples=740,macro_f1=score,strict_macro_f1=verified['macro_f1'],
             invalid_predictions=predictions.count('INVALID'),rules=rules,classes=classes,
             prediction_columns=classes+['INVALID'],confusion_matrix=matrix,per_class_f1=f1,
             parser_sha256=sha(Path(__file__).with_name('parse_v2.py')),evaluator_sha256=sha(Path(__file__)),
             strict_verification_sha256=sha(out/'verification.json'),oof_sha256=sha(parsed/'oof.csv'),
             limitation='Parsing change only; same hosted responses; no new model inference or fitting')
(parsed/'metrics.json').write_text(json.dumps(metrics,indent=2)+'\n')
print(json.dumps(metrics,indent=2))
