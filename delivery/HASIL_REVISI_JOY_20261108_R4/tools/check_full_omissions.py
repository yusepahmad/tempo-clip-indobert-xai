"""Inject three realistic omissions in memory; the release must reject each."""
import json
from pathlib import Path
import sys
from unittest.mock import patch

from bs4 import BeautifulSoup
import nbformat

from notebook_evidence import verify_full


def run(root):
    root=Path(root).resolve();original=nbformat.read;results=[]
    baseline='BUKTI_PER_REVISI/R20/R20_confusion_BASELINE_CLIP_INDoBERT.png'
    for fault in ['missing_baseline_output','missing_evidence_marker','truncated_csv']:
        changed=[]
        def read(path,*args,**kwargs):
            nb=original(path,*args,**kwargs)
            for cell in nb.cells:
                if cell.cell_type!='code':continue
                if fault=='missing_baseline_output' and "plot('confusion_task3_BASELINE_CLIP_INDoBERT.png')" in cell.source:
                    index=next(i for i,o in enumerate(cell.outputs) if 'image/png' in o.get('data',{}))
                    del cell.outputs[index];changed.append(fault)
                if fault=='missing_evidence_marker' and baseline in cell.metadata.get('full_evidence_paths',[]):
                    for out in cell.outputs:
                        content=out.get('data',{}).get('text/html','')
                        if 'class="full-evidence-file"' in content and baseline in content:
                            out['data']['text/html']='';changed.append(fault);break
                if fault=='truncated_csv' and cell.metadata.get('full_evidence_paths') and not changed:
                    for out in cell.outputs:
                        content=out.get('data',{}).get('text/html','')
                        if 'class="full-evidence-table"' in content:
                            soup=BeautifulSoup(content,'html.parser');soup.select_one('tbody tr').decompose()
                            out['data']['text/html']=str(soup);changed.append(fault);break
            return nb
        try:
            with patch('notebook_evidence.nbf.read',side_effect=read):verify_full(root)
        except AssertionError:
            assert changed,fault
            results.append(dict(fault=fault,rejected=True))
        else:raise AssertionError('Verifier accepted omitted evidence: '+fault)
    return dict(status='passed',faults=results,files_modified=False)


if __name__=='__main__':
    print(json.dumps(run(sys.argv[1]),indent=2))
