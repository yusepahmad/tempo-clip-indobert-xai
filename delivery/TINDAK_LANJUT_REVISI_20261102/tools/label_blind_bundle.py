"""Export prospective E01 inputs without gold; preserve historical features."""
import argparse
import csv
from datetime import datetime,timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys

FIELDS=['sample_id','image_path','headline_verified','supporting_text_verified']


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify(bundle):
    bundle=Path(bundle).resolve();meta=json.loads((bundle/'MANIFEST_INPUT.json').read_text())
    actual={p.relative_to(bundle).as_posix() for p in bundle.rglob('*') if p.is_file()}
    assert actual==set(meta['files'])|{'MANIFEST_INPUT.json'},'Unexpected input files'
    for name,digest in meta['files'].items():
        p=(bundle/name).resolve();assert p.is_relative_to(bundle) and sha(p)==digest,name
    with (bundle/'inputs.csv').open(newline='') as stream:
        reader=csv.DictReader(stream);assert reader.fieldnames==FIELDS,'Only four allowlisted columns allowed'
        rows=list(reader)
    assert len(rows)==meta['samples']==740
    assert len({r['sample_id'] for r in rows})==740
    for row in rows:
        p=(bundle/row['image_path']).resolve();assert p.is_relative_to(bundle/'images') and p.is_file()
        assert p.name==row['sample_id']+'.jpg'
    return dict(status='verified_label_blind_input',samples=len(rows),columns=FIELDS,
                files_checked=len(meta['files']),manifest_sha256=sha(bundle/'MANIFEST_INPUT.json'),
                historical_features_regenerated=False,historical_process_isolation_proved=False)


def export(workspace,destination):
    workspace=Path(workspace).resolve();bundle=Path(destination).resolve();assert not bundle.exists()
    source=workspace/'DEMO_XAI_745_FULL/03_data/DATASET_740_TASK2_DOMAIN.csv'
    with source.open(newline='',encoding='utf-8-sig') as stream:rows=list(csv.DictReader(stream))
    assert len(rows)==740 and len({r['sample_id'] for r in rows})==740
    (bundle/'images').mkdir(parents=True)
    with (bundle/'inputs.csv').open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=FIELDS);writer.writeheader()
        for row in rows:
            source_image=workspace/'DEMO_XAI_745_FULL/05_gambar'/Path(row['image_path']).name
            name=row['sample_id']+'.jpg';shutil.copy2(source_image,bundle/'images'/name)
            writer.writerow({**{k:row[k] for k in FIELDS},'image_path':'images/'+name})
    generator=workspace/'docs/server-recovery/2026-10-10/01_notebook/kaggle_e01/full/e01_vlm.py'
    shutil.copy2(generator,bundle/'generator_e01_original.py')
    meta=dict(schema='prospective-label-blind-e01-v1',created_at=datetime.now(timezone.utc).isoformat(),samples=740,
              input_columns=FIELDS,source_dataset_sha256=sha(source),generator_sha256=sha(generator),
              historical_features_replaced=False,model='Qwen/Qwen3-VL-8B-Instruct',revision='0c351dd01ed87e9c1b53cbc748cba10e6187ff3b',
              warning='Timestamp is export time today, not original E01 generation time. This bundle does not certify historical runtime isolation.',
              files={p.relative_to(bundle).as_posix():sha(p) for p in sorted(bundle.rglob('*')) if p.is_file()})
    (bundle/'MANIFEST_INPUT.json').write_text(json.dumps(meta,indent=2)+'\n')
    return verify(bundle)


def guard(bundle,output,workspace):
    """Python-level read guard; explicitly not an OS/container attestation."""
    bundle=Path(bundle).resolve();output=Path(output).resolve();workspace=Path(workspace).resolve()
    assert not output.is_relative_to(bundle)
    def audit(event,args):
        if event in {'subprocess.Popen','os.system'}:raise PermissionError('Child processes disabled in guarded generator')
        if event!='open' or isinstance(args[0],int):return
        p=Path(args[0]).resolve();flags=args[2] or 0
        writing=bool(flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC))
        if writing:
            if p.is_relative_to(bundle):raise PermissionError('Inputs are read-only')
            if p.is_relative_to(workspace) and not p.is_relative_to(output):raise PermissionError('Original workspace is read-only')
            return
        if p.suffix.lower()=='.csv' and p!=bundle/'inputs.csv':raise PermissionError('Non-allowlisted CSV')
        if p.is_relative_to(workspace) and not p.is_relative_to(bundle) and not p.is_relative_to(output):
            raise PermissionError('Original workspace is outside generator input scope')
    sys.addaudithook(audit)


def probe(bundle,workspace):
    result=verify(bundle);bundle=Path(bundle).resolve();workspace=Path(workspace).resolve()
    guard(bundle,bundle.parent/'future_generation_output',workspace)
    denied=False
    try:(workspace/'DEMO_XAI_745_FULL/03_data/DATASET_740_TASK2_DOMAIN.csv').read_bytes()
    except PermissionError:denied=True
    assert denied
    with (bundle/'inputs.csv').open() as stream:assert len(list(csv.DictReader(stream)))==740
    result.update(original_labelled_csv_read_blocked=True,guard='Python audit hook; not OS sandbox; full model generation not executed')
    return result


def generate(bundle,output,workspace,limit):
    verify(bundle);bundle=Path(bundle).resolve();output=Path(output).resolve();assert not output.exists()
    output.mkdir(parents=True);sys.dont_write_bytecode=True
    spec=importlib.util.spec_from_file_location('prospective_e01',bundle/'generator_e01_original.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    module.KAGGLE=False;module.RESUME_SOURCE=''
    manifest=json.loads((bundle/'MANIFEST_INPUT.json').read_text())
    sys.argv=['e01_guarded','--data-csv',str(bundle/'inputs.csv'),'--gambar',str(bundle/'images'),
              '--out',str(output),'--model',manifest['model'],'--revision',manifest['revision'],'--limit',str(limit)]
    guard(bundle,output,workspace);module.main()
    meta=json.loads((output/'meta.json').read_text())
    assert meta['status']=='selesai' and meta.get('selesai') is True,'Generation incomplete; outputs must not be promoted'


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['export','verify','probe','generate'])
    ap.add_argument('--workspace',type=Path,required=True);ap.add_argument('--bundle',type=Path,required=True)
    ap.add_argument('--output',type=Path);ap.add_argument('--limit',type=int,default=0)
    a=ap.parse_args()
    if a.action=='export':value=export(a.workspace,a.bundle)
    elif a.action=='probe':value=probe(a.bundle,a.workspace)
    elif a.action=='generate':value=generate(a.bundle,a.output,a.workspace,a.limit)
    else:value=verify(a.bundle)
    if value is not None:print(json.dumps(value,indent=2))
