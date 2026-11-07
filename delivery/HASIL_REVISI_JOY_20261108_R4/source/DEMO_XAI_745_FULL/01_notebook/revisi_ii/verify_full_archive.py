"""Extract, verify hashes, and Run all the FULL notebooks without altering files."""
import argparse
import json
import os
from pathlib import Path
import sys
import tempfile
import zipfile

import nbformat
from nbclient import NotebookClient
from evaluate import sha
from notebook_evidence import verify_full
from validate_package import validate


def verify(archive):
    archive=Path(archive).resolve()
    assert sha(archive)==archive.with_suffix('.zip.sha256').read_text().split()[0]
    with tempfile.TemporaryDirectory(prefix='joy-full-extraction-') as directory:
        directory=Path(directory)
        with zipfile.ZipFile(archive) as z:
            assert z.testzip() is None and len(z.namelist())==len(set(z.namelist()))
            for name in z.namelist():assert (directory/name).resolve().is_relative_to(directory)
            z.extractall(directory)
        root=directory/'joy_revisi_ii';canonical=validate(root);coverage=verify_full(root)
        reports=[];previous=os.environ.get('PATH','')
        os.environ['PATH']=str(Path(sys.executable).parent)+os.pathsep+previous
        try:
            for path in sorted((root/'notebooks').glob('0*.ipynb')):
                print('Run all extracted:',path.name,flush=True)
                nb=nbformat.read(path,as_version=4)
                NotebookClient(nb,timeout=900,kernel_name='python3',resources={'metadata':{'path':str(root)}}).execute()
                code=[c for c in nb.cells if c.cell_type=='code']
                assert all(c.execution_count is not None for c in code)
                assert not any(o.output_type=='error' for c in code for o in c.outputs)
                count=sum(len(c.metadata.get('full_evidence_paths',[])) for c in code)
                reports.append(dict(notebook=path.name,executed=True,errors=0,evidence_files=count))
        finally:os.environ['PATH']=previous
        # The in-memory executions do not overwrite notebook files. Analysis
        # reruns must still leave every manifested artifact byte-identical.
        final=validate(root)
        return dict(status='verified_extracted_run_all',archive_sha256=sha(archive),
                    bytes=archive.stat().st_size,hash_files_checked=final['hash_files_checked'],
                    metrics_verified=canonical['metric_rows_counter_verified'],coverage=coverage,
                    notebooks=reports,environment='local Linux, extracted ZIP; same analysis venv',
                    colab='Not Evaluated',training=False)


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('archive',type=Path);ap.add_argument('--report',type=Path,required=True)
    args=ap.parse_args();result=verify(args.archive)
    args.report.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
