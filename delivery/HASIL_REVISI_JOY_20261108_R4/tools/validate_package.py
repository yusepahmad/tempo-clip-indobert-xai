"""Independent Counter metrics and package-contract validation; no network."""
import argparse
from collections import Counter
import base64
import io
import json
from pathlib import Path
import nbformat
import pandas as pd
from PIL import Image
from evaluate import TASKS,discover_package,sha


def independent_metrics(truth,prediction,labels):
    a,b=Counter(truth),Counter(prediction);tp=Counter(x for x,y in zip(truth,prediction) if x==y)
    precision=sum(tp[x]/b[x] if b[x] else 0 for x in labels)/len(labels)
    recall=sum(tp[x]/a[x] if a[x] else 0 for x in labels)/len(labels)
    macro=sum(2*tp[x]/(a[x]+b[x]) if a[x]+b[x] else 0 for x in labels)/len(labels)
    n=len(truth);acc=sum(tp.values())/n;expected=sum(a[x]*b[x] for x in labels)/(n*n)
    kappa=(acc-expected)/(1-expected) if expected<1 else None
    return dict(accuracy=acc,precision_macro=precision,recall_macro=recall,macro_f1=macro,kappa=kappa)


def validate(root,check_notebooks=True):
    root=Path(root).resolve();reference,folds,frames,records,rejected=discover_package(root)
    b=pd.read_csv(root/'analysis/metrics.csv');assert len(b)==len(frames)*3
    checked=0
    for name,frame in frames.items():
        for t in TASKS:
            rows=b[(b.experiment==name)&(b.task==t)];assert len(rows)==1
            row=rows.iloc[0];calculated=independent_metrics(frame[t+'_truth'].tolist(),frame[t+'_pred'].tolist(),sorted(reference[t].unique()))
            for field,value in calculated.items():
                if value is not None:assert abs(float(row[field])-value)<1e-12,(name,t,field)
            assert 0<=row.macro_ci_low<=row.macro_ci_high<=1
            assert 0<=row.accuracy_ci_low<=row.accuracy_ci_high<=1
            checked+=1
    tracker=pd.read_csv(root/'documentation/REVISION_TRACKER_28.csv').fillna('')
    expected={f'R{i}' for i in range(18,37)}|{'R2','R4','R6','R8','R9','R12','R13','R16','R17'}
    assert len(tracker)==tracker.revision_id.nunique()==28 and set(tracker.revision_id)==expected
    state=json.loads((root/'PACKAGE_STATE.json').read_text())
    assert state['completed']==int((tracker.status=='Selesai').sum()) and state['open']==28-state['completed']
    assert state['all_revisions_complete']==(state['open']==0)
    assert not (tracker[(tracker.status!='Selesai')].remaining=='').any()
    assert len(pd.read_csv(root/'analysis/ranking_36_legacy.csv'))==36
    nb_reports=[]
    if check_notebooks:
        for path in sorted((root/'notebooks').glob('0*.ipynb')):
            nb=nbformat.read(path,as_version=4);nbformat.validate(nb)
            code=[c for c in nb.cells if c.cell_type=='code']
            assert code and all(c.execution_count is not None for c in code),path.name
            assert not any(o.output_type=='error' for c in code for o in c.outputs),path.name
            visuals=0
            if nb.metadata.get('tempo_revision',{}).get('screenshots_embedded'):
                text='\n'.join(c.source for c in nb.cells if c.cell_type=='markdown')
                assert 'Multi-Task Learning CLIP–IndoBERT dengan Joint Loss' in text
                assert 'e42_tail_grid' in text and '20 Oktober 2026' in text
                for cell in nb.cells:
                    for name,content in cell.get('attachments',{}).items():
                        assert f'attachment:{name}' in cell.source
                        blob=base64.b64decode(content['image/png'],validate=True)
                        with Image.open(io.BytesIO(blob)) as im:
                            assert im.width>=700 and im.height>=400
                            im.verify()
                        assert blob==(root/'screenshots'/name).read_bytes()
                        visuals+=1
                assert visuals>=1
            nb_reports.append(dict(notebook=path.name,code_cells=len(code),executed=True,errors=0,embedded_visuals=visuals))
        assert len(nb_reports)==3
    hash_count=0
    if (root/'MANIFEST_SHA256.json').exists():
        manifest=json.loads((root/'MANIFEST_SHA256.json').read_text())
        for name,expected in manifest['files'].items():
            path=(root/name).resolve()
            assert path.is_relative_to(root) and path.is_file(),name
            assert sha(path)==expected,name
            hash_count+=1
    return dict(status='verified',metric_rows_counter_verified=checked,sources=len(frames),revision_rows=28,
                completed=state['completed'],open=state['open'],all_revisions_complete=state['all_revisions_complete'],
                hash_files_checked=hash_count,notebooks=nb_reports,
                human_annotation='Not Evaluated',human_xai_ratings='Not Evaluated',
                note='Technical reproducibility verification does not certify missing human or external evidence')


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--root',required=True,type=Path);ap.add_argument('--skip-notebooks',action='store_true')
    a=ap.parse_args();print(json.dumps(validate(a.root,check_notebooks=not a.skip_notebooks),indent=2))
