"""Run FULL notebooks from an extracted analysis package and save genuine evidence."""
import argparse
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import sys
import time
from datetime import datetime,timezone

import nbformat
from nbclient import NotebookClient
from validate_package import validate
from notebook_evidence import verify_full


def run(root,output):
    root=Path(root).resolve();output=Path(output).resolve();output.mkdir(parents=True,exist_ok=False)
    environment='local Linux'
    try:
        import google.colab
        if os.environ.get('COLAB_RELEASE_TAG') or Path('/opt/google/colab').exists():environment='Google Colab'
    except ImportError:pass
    before=validate(root);reports=[];previous=os.environ.get('PATH','')
    os.environ['PATH']=str(Path(sys.executable).parent)+os.pathsep+previous
    try:
        for path in sorted((root/'notebooks').glob('0*.ipynb')):
            started=time.monotonic();print('Run all:',path.name,flush=True)
            nb=nbformat.read(path,as_version=4)
            NotebookClient(nb,timeout=900,kernel_name='python3',resources={'metadata':{'path':str(root)}}).execute()
            code=[c for c in nb.cells if c.cell_type=='code'];assert all(c.execution_count is not None for c in code)
            assert not any(o.output_type=='error' for c in code for o in c.outputs)
            nbformat.write(nb,output/('executed_'+path.name))
            reports.append(dict(notebook=path.name,executed=True,errors=0,seconds=round(time.monotonic()-started,2)))
    finally:os.environ['PATH']=previous
    result=dict(status='verified',environment=environment,created_at=datetime.now(timezone.utc).isoformat(),python=sys.version,
                platform=platform.platform(),colab_release_tag=os.environ.get('COLAB_RELEASE_TAG'),
                dependencies={p:importlib.metadata.version(p) for p in ['numpy','pandas','scipy','scikit-learn','matplotlib','nbformat','nbclient','nbconvert','ipykernel','Pillow']},
                before=before,after=validate(root),coverage=verify_full(root),notebooks=reports,
                colab_verified=environment=='Google Colab',training=False)
    (output/'RUNTIME_VERIFICATION.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2),flush=True);return result


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--root',required=True,type=Path);ap.add_argument('--output',required=True,type=Path)
    a=ap.parse_args();run(a.root,a.output)
