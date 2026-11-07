"""Independent stdlib metrics and paired-bootstrap comparisons with E33/baseline."""
import csv,json,hashlib,random,collections,sys
from pathlib import Path
TASKS=('task1_issue','task2_domain_sumber','task3_primary_entity_type');TARGET=TASKS[1]
def macro(rows,t,key):
    labels=sorted({r[t+'_truth'] for r in rows});tp=collections.Counter();a=collections.Counter();b=collections.Counter()
    for r in rows:
        truth,pred=r[t+'_truth'],r[t+key];a[truth]+=1;b[pred]+=1
        if truth==pred:tp[truth]+=1
    return sum(2*tp[c]/(a[c]+b[c]) if a[c]+b[c] else 0 for c in labels)/len(labels)
def main():
    out=Path(sys.argv[1]);e33=Path(sys.argv[2]);audit=json.loads((out/'verification.json').read_text());assert audit['status']=='passed'
    for name,digest in audit['files'].items():assert hashlib.sha256((out/name).read_bytes()).hexdigest()==digest,name
    assert json.loads((out/'forward_verification.json').read_text())['status']=='passed'
    r=json.loads((out/'result.json').read_text());rows=list(csv.DictReader((out/'oof.csv').open()));older={x['sample_id']:x for x in csv.DictReader((e33/'oof.csv').open())}
    assert len(rows)==len({x['sample_id'] for x in rows})==740 and set(older)=={x['sample_id'] for x in rows}
    for row in rows:
        b=older[row['sample_id']];assert b['fold']==row['fold']
        for t in TASKS:
            assert b[t+'_truth']==row[t+'_truth'];row[t+'_baseline']=b[t+'_baseline'];row[t+'_e33']=b[t+'_pred']
    metrics={t:macro(rows,t,'_pred') for t in TASKS}
    for t in TASKS:assert abs(metrics[t]-r['metrics'][t]['macro_f1'])<1e-12
    rng=random.Random(42);diff_base=[];diff_e33=[]
    for _ in range(2000):
        sample=rng.choices(rows,k=740);a=macro(sample,TARGET,'_pred');diff_base.append(a-macro(sample,TARGET,'_baseline'));diff_e33.append(a-macro(sample,TARGET,'_e33'))
    def interval(values):values.sort();return [values[50],values[1949]]
    report=dict(status='passed',samples=740,metrics_stdlib=metrics,delta_task2_baseline=metrics[TARGET]-macro(rows,TARGET,'_baseline'),delta_task2_e33=metrics[TARGET]-macro(rows,TARGET,'_e33'),
        bootstrap_exploratory=dict(replicates=2000,seed=42,baseline_interval95=interval(diff_base),e33_interval95=interval(diff_e33),limits='Ignores overlapping training sets and repeated model selection'),checkpoint_sampled_forward_passed=True,target_reached=metrics[TARGET]>=.7)
    (out/'root_verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
