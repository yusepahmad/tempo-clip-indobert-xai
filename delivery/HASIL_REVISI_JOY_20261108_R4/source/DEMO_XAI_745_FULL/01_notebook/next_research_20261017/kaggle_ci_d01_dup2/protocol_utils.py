"""Train-only duplication and predeclared inner-selection helpers."""
import hashlib
import json
from collections import Counter
from pathlib import Path

import numpy as np

TASKS=('task1_issue','task2_domain_sumber','task3_primary_entity_type')


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as handle:
        for data in iter(lambda:handle.read(1024*1024),b''):h.update(data)
    return h.hexdigest()


def write(path,value):
    Path(path).write_text(json.dumps(value,indent=2)+'\n')


def duplicate_train(train, forbidden, factor):
    train=np.asarray(train,dtype=np.int64)
    assert factor in (1,2) and train.ndim==1 and len(train)>0
    assert len(set(train.tolist()))==len(train), 'Split unique originals BEFORE duplication'
    assert not set(train.tolist()) & set(map(int,forbidden)), 'Held-out ID in training'
    expanded=np.tile(train,factor)
    assert Counter(expanded.tolist())==Counter({int(i):factor for i in train})
    return expanded


def select_epoch(traces,candidates):
    assert len(traces)==2
    scores={int(e):min(float(np.mean([trace['epochs'][str(e)][t] for trace in traces])) for t in TASKS) for e in candidates}
    # Iteration order implements earliest-epoch exact tie break.
    chosen=max(candidates,key=lambda e:scores[int(e)])
    return int(chosen),scores


def split_audit(ids,train,validation,test,factor):
    a,b,c=map(lambda values:set(map(int,values)),(train,validation,test))
    assert not a&b and not a&c and not b&c
    expanded=duplicate_train(train,b|c,factor)
    return dict(train_ids=[str(ids[i]) for i in train],validation_ids=[str(ids[i]) for i in validation],
                test_ids=[str(ids[i]) for i in test],unique_train_samples=len(train),
                train_exposures_per_epoch=len(expanded),factor=factor,
                multiplicity={str(ids[i]):factor for i in train})
