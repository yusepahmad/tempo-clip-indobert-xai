"""Run in a new lean virtualenv against a ZIP extraction, no project env reuse."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import zipfile


def main(archive,destination,report):
    archive=Path(archive).resolve();destination=Path(destination).resolve();report=Path(report).resolve()
    destination.mkdir(parents=True,exist_ok=True);report.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        for name in z.namelist():
            p=(destination/name).resolve();assert p.is_relative_to(destination)
        z.extractall(destination)
    root=destination/'joy_revisi_ii';sys.path.insert(0,str(root/'tools'))
    os.environ['PATH']=str(Path(sys.executable).parent)+os.pathsep+os.environ.get('PATH','')
    os.environ['JUPYTER_DATA_DIR']=str(report/'jupyter_data')
    os.environ['JUPYTER_PATH']=str(Path(sys.prefix)/'share/jupyter')
    os.environ['IPYTHONDIR']=str(report/'ipython')
    os.environ['JUPYTER_RUNTIME_DIR']=str(report/'jupyter_runtime')
    for key in ['JUPYTER_DATA_DIR','IPYTHONDIR','JUPYTER_RUNTIME_DIR']:Path(os.environ[key]).mkdir(exist_ok=True)
    import nbformat
    from nbclient import NotebookClient
    from jupyter_client.kernelspec import KernelSpecManager
    from evaluate import sha,write_json
    from validate_package import validate
    before=validate(root)
    tests=subprocess.run([sys.executable,'-m','unittest','-v','test_evaluate.py','test_human_agreement.py'],cwd=root/'tools',capture_output=True,text=True,timeout=120)
    (report/'unit_tests.log').write_text(tests.stdout+tests.stderr);assert tests.returncode==0
    spec=KernelSpecManager().get_kernel_spec('python3')
    kernel_python=shutil.which(spec.argv[0]) if not Path(spec.argv[0]).is_absolute() else spec.argv[0]
    # Symlinks may resolve to the same base interpreter. Ensure launch path
    # belongs to this virtualenv rather than only comparing resolved binaries.
    assert Path(kernel_python).parent==Path(sys.executable).parent,(spec.argv,kernel_python,sys.executable)
    records=[]
    for path in sorted((root/'notebooks').glob('0*.ipynb')):
        nb=nbformat.read(path,as_version=4);start=time.monotonic()
        print('CLEAN RUN ALL',path.name,flush=True)
        NotebookClient(nb,timeout=900,kernel_name='python3',resources={'metadata':{'path':str(root)}}).execute()
        assert all(o.output_type!='error' for c in nb.cells if c.cell_type=='code' for o in c.outputs)
        nbformat.write(nb,report/('executed_'+path.name))
        records.append(dict(notebook=path.name,source_sha256=sha(path),executed=True,seconds=time.monotonic()-start,
                            errors=0,code_cells=sum(c.cell_type=='code' for c in nb.cells)))
    after=validate(root)
    freeze=subprocess.run([sys.executable,'-m','pip','freeze'],capture_output=True,text=True)
    if freeze.returncode==0:(report/'requirements-clean-lock.txt').write_text(freeze.stdout)
    value=dict(status='verified',archive_sha256=sha(archive),python=sys.executable,sys_prefix=sys.prefix,
               kernel_spec_argv=spec.argv,isolated_virtualenv=sys.prefix!=sys.base_prefix,
               before=before,after=after,notebooks=records,network_needed_for_analysis=False,
               colab='Not Evaluated',windows='Not Evaluated')
    write_json(report/'CLEAN_ENV_VERIFICATION.json',value);print(json.dumps(value,indent=2))


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--archive',required=True,type=Path);ap.add_argument('--destination',required=True,type=Path);ap.add_argument('--report',required=True,type=Path)
    a=ap.parse_args();main(a.archive,a.destination,a.report)
