"""Independent stdlib metric/hash/split audit and exploratory paired bootstrap."""
import csv,json,hashlib,random,sys,collections
from pathlib import Path
TASKS=('task1_issue','task2_domain_sumber','task3_primary_entity_type');TARGET=TASKS[1]
def macro(rows,t,key):
    labels=sorted({r[t+'_truth'] for r in rows});tp=collections.Counter();truth=collections.Counter();pred=collections.Counter()
    for r in rows:
        a,b=r[t+'_truth'],r[t+key];truth[a]+=1;pred[b]+=1
        if a==b:tp[a]+=1
    return sum(2*tp[c]/(truth[c]+pred[c]) if truth[c]+pred[c] else 0 for c in labels)/len(labels)
def main():
    out=Path(sys.argv[1]);root=Path(__file__).resolve().parents[2]
    result=json.loads((out/'result.json').read_text());audit=json.loads((out/'verification.json').read_text());assert audit['status']=='passed'
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    for name,digest in audit['files'].items():assert sha(out/name)==digest,name
    protocol=json.loads((out/'protocol.json').read_text())
    for name,digest in protocol['inputs'].items():assert sha(root/name)==digest,name
    rows=list(csv.DictReader((out/'oof.csv').open()));assert len(rows)==len({r['sample_id'] for r in rows})==740
    assert collections.Counter(r['fold'] for r in rows)==dict.fromkeys(['1','2','3','4','5'],148)
    scores={}
    for t in TASKS:
        scores[t]=dict(candidate=macro(rows,t,'_pred'),baseline=macro(rows,t,'_baseline'))
        assert abs(scores[t]['candidate']-result['metrics'][t]['macro_f1'])<1e-12
        assert abs(scores[t]['baseline']-result['baseline'][t]['macro_f1'])<1e-12
    rng=random.Random(42);differences=[]
    for _ in range(2000):
        resampled=rng.choices(rows,k=740);differences.append(macro(resampled,TARGET,'_pred')-macro(resampled,TARGET,'_baseline'))
    differences.sort();diagnosis={}
    for label,rs in __import__('itertools').groupby(sorted(rows,key=lambda r:r[TARGET+'_truth']),key=lambda r:r[TARGET+'_truth']):
        group=list(rs);diagnosis[label]=dict(count=len(group),correct=sum(r[TARGET+'_truth']==r[TARGET+'_pred'] for r in group))
    report=dict(status='passed',metrics_stdlib=scores,delta_task2=scores[TARGET]['candidate']-scores[TARGET]['baseline'],paired_bootstrap=dict(replicates=2000,seed=42,interval_95=[differences[50],differences[1949]],limitation='Exploratory only: overlapping fold training sets and repeated experiment selection are not accounted for'),diagnosis=diagnosis,target_reached=scores[TARGET]['candidate']>=.7)
    (out/'root_verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
