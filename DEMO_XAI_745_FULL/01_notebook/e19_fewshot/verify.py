"""Audit all740 few-shot responses against training-only input reconstruction and costs."""
import hashlib
import io
import json
from pathlib import Path
import sys
import numpy as np
import pandas as pd
from PIL import Image
from sklearn.metrics import f1_score
from verify_inputs import ROOT,check_inputs
sys.path.insert(0,str(ROOT/'01_notebook/e18_hosted'))
from parse_v2 import parse_answer
from valid_labels import training_majority_fallback

sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
folder=ROOT/'04_hasil_eksperimen/e19_fewshot'
prepared,inputs,df,fold=check_inputs()
config=json.loads((folder/'run_config.json').read_text())
assert config['worker_sha256']==sha(Path(__file__).with_name('run.py'))
assert config['input_verifier_sha256']==sha(Path(__file__).with_name('verify_inputs.py'))
assert config['parser_sha256']==sha(ROOT/'01_notebook/e18_hosted/parse_v2.py')
assert config['quota_source_sha256']==sha(ROOT/'01_notebook/e18_hosted/quota.py')
assert config['preparation_config_sha256']==sha(folder/'config.json')
assert config['inputs_sha256']==prepared['inputs_sha256'] and config['classes']==prepared['classes']
assert config['model']==prepared['model']=='google/gemini-3-flash-preview'
assert config['max_tokens']==4096 and config['budget_usd']==6 and config['max_image_side']==384
prior=ROOT/'04_hasil_eksperimen/e18_hosted'
assert config['prior_verification_sha256']==sha(prior/'verification.json')
assert config['prior_v2_metrics_sha256']==sha(prior/'parsed_v2/metrics.json')
assert config['fallback_source_sha256']==sha(ROOT/'01_notebook/e18_hosted/valid_labels.py')
assert config['prior_valid_verification_sha256']==sha(prior/'valid/verification.json')
files=sorted((folder/'records').glob('*.json'))
assert len(files)==740 and [p.name for p in files]==[f'{i:04d}.json' for i in range(740)]
classes=config['classes'];prediction=[];strict_prediction=[];costs=[];rules={};hashes={}
for i,(p,row) in enumerate(zip(files,inputs)):
    record=json.loads(p.read_text())
    assert record['status']=='complete' and record['index']==i and record['sample_id']==row['sample_id']
    assert record['fold']==row['fold']==int(fold[i]) and record['model']==config['model']
    assert record['config_sha256']==sha(folder/'run_config.json')
    assert record['prompt_sha256']==row['prompt_sha256'] and record['image_sha256']==row['image_sha256']
    image_path=ROOT/'05_gambar'/Path(df.image_path.iloc[i]).name
    with Image.open(image_path) as im:
        image=im.convert('RGB');image.thumbnail((384,384),Image.Resampling.LANCZOS)
        buffer=io.BytesIO();image.save(buffer,format='PNG')
    assert record['image_size']==list(image.size)
    assert record['transmitted_image_sha256']==hashlib.sha256(buffer.getvalue()).hexdigest()
    result=record['response'];assert result['model']==config['model'] and len(result['choices'])==1
    assert record['http_status']==200
    content=result['choices'][0]['message'].get('content') or ''
    code,rule=parse_answer(content,classes)
    answer=content.strip();strict=answer if len(answer)==1 and answer in 'ABCDEFG' else 'INVALID'
    value=classes[ord(code)-ord('A')] if code!='INVALID' else 'INVALID'
    assert record['code']==code and record['strict_code']==strict
    assert record['prediction']==value and record['parsing_rule']==rule
    assert record['finish_reason']==result['choices'][0].get('finish_reason')
    usage=result['usage'];c=usage['cost']
    cost=(c['input_tokens_cost_nanodollars']+c['output_tokens_cost_nanodollars'])/1e9
    assert usage['prompt_tokens']>0 and usage['completion_tokens']>=0
    assert abs(cost-record['cost_usd'])<1e-12 and 0<=cost<=0.05
    assert len(record['quota_before'])==len(record['quota_after'])==2
    for before,after in zip(record['quota_before'],record['quota_after']):
        assert before['period']==after['period']
        assert abs(after['used']-before['used']-cost)<1e-6 and after['remaining']>=0.1
    costs.append(cost);prediction.append(value)
    strict_prediction.append(classes[ord(strict)-ord('A')] if strict!='INVALID' else 'INVALID')
    rules[rule]=rules.get(rule,0)+1;hashes[str(p.relative_to(folder))]=sha(p)
assert sum(costs)<=6.0
truth=df.task2_domain_sumber.to_list()
raw_prediction=prediction.copy();raw_strict_prediction=strict_prediction.copy()
prediction,applied,policies=training_majority_fallback(raw_prediction,truth,fold.tolist(),classes)
strict_prediction,strict_applied,strict_policies=training_majority_fallback(raw_strict_prediction,truth,fold.tolist(),classes)
assert policies==strict_policies and all(p['training_samples']==592 and p['test_samples']==148 for p in policies.values())
def manual(values):
    matrix=[[sum(t==label and p==value for t,p in zip(truth,values))
             for value in classes] for label in classes]
    scores=[]
    for j in range(7):
        tp=matrix[j][j];fn=sum(matrix[j])-tp;fp=sum(row[j] for row in matrix)-tp
        scores.append(2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else 0.0)
    result=sum(scores)/7
    assert abs(result-f1_score(truth,values,labels=classes,average='macro',zero_division=0))<1e-12
    return result,matrix,scores
score,matrix,scores=manual(prediction);strict_score,_,_=manual(strict_prediction)
oof=pd.DataFrame(dict(sample_id=df.sample_id,truth=truth,prediction=prediction,fold=fold,strict_prediction=strict_prediction,
                     raw_prediction=raw_prediction,raw_strict_prediction=raw_strict_prediction,fallback_applied=applied,
                     fallback_class=[policies[str(k)]['label'] for k in fold]))
oof.to_csv(folder/'oof.csv',index=False)
metrics=dict(status='verified',samples=740,macro_f1=score,strict_macro_f1=strict_score,
             protocol='fixed14_outer_training_fewshot5fold_no_tuning_training_majority_fallback',cost_usd=sum(costs),
             invalid_predictions=prediction.count('INVALID'),raw_invalid_predictions=sum(applied),
             fallback_policies=policies,rules=rules,classes=classes,
             prediction_columns=classes,confusion_matrix=matrix,per_class_f1=scores,
             fold_macro_f1={str(k):float(f1_score(np.array(truth)[fold==k],np.array(prediction)[fold==k],
                 labels=classes,average='macro',zero_division=0)) for k in range(1,6)},
             verifier_sha256=sha(Path(__file__)),oof_sha256=sha(folder/'oof.csv'))
(folder/'metrics.json').write_text(json.dumps(metrics,indent=2)+'\n')
verification=dict(status='verified',samples=740,macro_f1=score,verifier_sha256=sha(Path(__file__)),
                  checks=['independent reconstruction of all740 prompts/rankings/training memberships',
                          'all740 image hashes and cached response parsing; rawINVALID retained in trace',
                          'all740 final predictions seven-class; fallback uses only592 training counts per fold',
                          'all740 usage costs match quota deltas; budget6USD',
                          'original labels/IDs/outer folds; manual F1 matches sklearn',
                          'hosted inference not independently reproduced'],
                  sha256={'inputs.jsonl':sha(folder/'inputs.jsonl'),'config.json':sha(folder/'config.json'),
                          'run_config.json':sha(folder/'run_config.json'),'oof.csv':sha(folder/'oof.csv'),
                          'metrics.json':sha(folder/'metrics.json'),**hashes})
(folder/'verification.json').write_text(json.dumps(verification,indent=2)+'\n')
print(json.dumps(metrics,indent=2))
