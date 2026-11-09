"""Synthetic acceptance and corruption rejection; never a model quality score."""
import csv,json,hashlib,subprocess,sys,tempfile
from pathlib import Path
TASKS=('task1_issue','task2_domain_sumber','task3_primary_entity_type')
def main():
    with tempfile.TemporaryDirectory() as directory:
        out=Path(directory);rows=[]
        for i in range(740):
            row=dict(sample_id=str(i),fold=i//148+1)
            for t in TASKS:row.update({t+'_truth':str(i%2),t+'_pred':str(i%2),t+'_baseline':str(i%2)})
            rows.append(row)
        with (out/'oof.csv').open('w') as stream:
            writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
        result=dict(metrics={t:dict(macro_f1=1.) for t in TASKS},baseline={t:dict(macro_f1=1.) for t in TASKS},target_reached=True,minimum_task_macro_f1=1.)
        def write():
            (out/'result.json').write_text(json.dumps(result))
            root=Path(__file__).resolve().parents[2];source=Path(__file__).with_name('model.py')
            (out/'verification.json').write_text(json.dumps(dict(status='passed',inputs={str(source.relative_to(root)):hashlib.sha256(source.read_bytes()).hexdigest()},files={n:hashlib.sha256((out/n).read_bytes()).hexdigest() for n in ('oof.csv','result.json')})))
        def run():return subprocess.run([sys.executable,str(Path(__file__).with_name('root_verify.py')),str(out)],capture_output=True)
        write();assert run().returncode==0,'valid fixture rejected'
        result['target_reached']=False;write();assert run().returncode!=0,'false target accepted'
        result['target_reached']=True;result['metrics'][TASKS[2]]['macro_f1']=.99;write();assert run().returncode!=0,'incorrect task3 metric accepted'
        result['metrics'][TASKS[2]]['macro_f1']=1.;write()
        with (out/'oof.csv').open('a') as stream:stream.write('corruption\n')
        assert run().returncode!=0,'altered file accepted'
        write();audit=json.loads((out/'verification.json').read_text());audit['inputs']={n:'0'*64 for n in audit['inputs']};(out/'verification.json').write_text(json.dumps(audit))
        assert run().returncode!=0,'altered input provenance accepted'
    print('SYNTHETIC AUDIT CHECKS PASSED: valid fixture; rejects false target, wrong Task3 metric, altered OOF hash')
if __name__=='__main__':main()
