"""Compute agreement only from complete external human rating files.

Blank preparation templates deliberately fail validation. The caller is
responsible for documenting real rater identity/independence and consent.
"""
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.metrics import cohen_kappa_score
from evaluate import TASKS,sha,write_json


def annotation(a,b,protocol):
    meta=json.loads(Path(protocol).read_text());aa=pd.read_csv(a,keep_default_na=False);bb=pd.read_csv(b,keep_default_na=False)
    expected=set(meta['sample_ids'])
    for frame in [aa,bb]:
        if not frame.sample_id.is_unique or set(frame.sample_id)!=expected:raise ValueError('Expected exact 150 unique prespecified sample IDs')
        for t in TASKS:
            if t not in frame or not set(frame[t]).issubset(meta['labels'][t]):raise ValueError('Missing/invalid human labels; blank templates cannot be scored')
    aa=aa.set_index('sample_id').sort_index();bb=bb.set_index('sample_id').loc[aa.index]
    rows=[]
    for t in TASKS:
        value=cohen_kappa_score(aa[t],bb[t],labels=meta['labels'][t])
        if not np.isfinite(value):raise ValueError('Kappa undefined for degenerate ratings; report unidentifiable, not zero')
        rows.append(dict(task=t,samples=len(aa),agreement=float((aa[t]==bb[t]).mean()),cohen_kappa=float(value)))
    return dict(status='computed_from_supplied_labels',source_a_sha256=sha(a),source_b_sha256=sha(b),tasks=rows,
                caveat='Computes agreement, does not independently authenticate human identity or independence; adjudicated gold must be separate')


def icc_absolute(matrix):
    values=np.asarray(matrix,dtype=float)
    if values.ndim!=2 or values.shape[0]<2 or values.shape[1]<5 or not np.isfinite(values).all():
        raise ValueError('Need at least two fully scored items and five raters, no missing scores')
    if not ((values>=1)&(values<=5)).all():raise ValueError('Rubric scores must be between 1 and 5')
    n,k=values.shape;grand=values.mean();row=values.mean(axis=1);column=values.mean(axis=0)
    msr=k*np.sum((row-grand)**2)/(n-1)
    msc=n*np.sum((column-grand)**2)/(k-1)
    mse=np.sum((values-row[:,None]-column[None,:]+grand)**2)/((n-1)*(k-1))
    denom=msr+(k-1)*mse+k*(msc-mse)/n
    if abs(denom)<1e-12:raise ValueError('ICC undefined: no identifiable rating variance')
    return float((msr-mse)/denom)


def xai(path,expected_template=None):
    frame=pd.read_csv(path,keep_default_na=False)
    required={'item_id','rater_id','dimension','score'}
    if not required.issubset(frame):raise ValueError('Require item_id,rater_id,dimension,score')
    if frame[list(required)].eq('').any().any():raise ValueError('Blank XAI templates cannot be scored')
    if frame.rater_id.nunique()<5:raise ValueError('At least five distinct real independent raters required')
    if frame.duplicated(['item_id','rater_id','dimension']).any():raise ValueError('Duplicate rating keys')
    if expected_template is not None:
        expected=pd.read_csv(expected_template,keep_default_na=False)
        keys=['item_id','rater_id','dimension']
        if set(map(tuple,frame[keys].to_numpy()))!=set(map(tuple,expected[keys].to_numpy())):
            raise ValueError('Expected exactly all prespecified item/rater/dimension keys; no missing or invented items')
        values=pd.to_numeric(frame.score,errors='coerce').to_numpy()
        if not np.isfinite(values).all() or not np.equal(values,np.floor(values)).all():
            raise ValueError('Protocol requires complete integer Likert scores')
    results=[]
    for dimension,group in frame.groupby('dimension'):
        mat=group.pivot(index='item_id',columns='rater_id',values='score').apply(pd.to_numeric,errors='coerce')
        results.append(dict(dimension=dimension,items=len(mat),raters=len(mat.columns),
                            mean=float(mat.to_numpy().mean()),icc_2_1_absolute_single=icc_absolute(mat.to_numpy())))
    return dict(status='computed_from_supplied_ratings',source_sha256=sha(path),dimensions=results,
                design='two-way random raters, absolute agreement, single-measure ICC(2,1)',
                caveat='Human recruitment/independence and blind-control protocol must be documented separately; no automatic authenticity claim')


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('mode',choices=['annotation','xai']);ap.add_argument('--a',type=Path)
    ap.add_argument('--b',type=Path);ap.add_argument('--protocol',type=Path);ap.add_argument('--ratings',type=Path);ap.add_argument('--expected-template',type=Path);ap.add_argument('--output',type=Path,required=True)
    args=ap.parse_args()
    value=annotation(args.a,args.b,args.protocol) if args.mode=='annotation' else xai(args.ratings,args.expected_template)
    write_json(args.output,value);print(json.dumps(value,indent=2))
