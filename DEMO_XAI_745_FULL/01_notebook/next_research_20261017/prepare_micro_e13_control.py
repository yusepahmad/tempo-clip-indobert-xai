"""Freeze an independent training-only stack control on the E13 inner split."""
import json
import time
from pathlib import Path

import numpy as np
from sklearn.model_selection import train_test_split

import run_micro_e12_structured_decoder as e12

OUT = e12.OUT.parent / 'MICRO_E13_joint_qlora_inner_pilot'


def main():
    started = time.monotonic()
    OUT.mkdir(exist_ok=True)
    ids, names, truth, folds, views = e12.load_data()
    train, test = np.where(folds != 1)[0], np.where(folds == 1)[0]
    inner, validation = train_test_split(train, test_size=.2, stratify=truth[train, 0], random_state=43)
    assert len(inner) == 473 and len(validation) == 119
    counts = tuple(len(names[t]) for t in e12.TASKS)
    probabilities = e12.fit_stack(views, inner, truth[inner], validation, counts,
                                  names[e12.TASKS[2]].index('individual'), 251000)
    control = np.column_stack([p.argmax(1) for p in probabilities['flat']])
    scores = e12.task_scores(truth[validation], control)
    e12.write_predictions(OUT/'control_validation_predictions.csv', ids[validation],
                           folds[validation], names, truth[validation], control)
    result = dict(schema='tempo-e13-inner-control-v1', eligible_as_oof=False,
                  outer_test_evaluated=False, validation_micro_f1=scores,
                  minimum_validation_micro_f1=min(scores.values()),
                  inner_train_ids=ids[inner].tolist(), validation_ids=ids[validation].tolist(),
                  untouched_outer_test_ids=ids[test].tolist(), seconds=time.monotonic()-started,
                  decision_rule={'minimum_gain_required':.03, 'maximum_per_task_drop':.03,
                                 'alternative':'all three validation task scores >= .70',
                                 'limitation':'practical pilot gate only; not statistical proof of generalization'})
    e12.write_json(OUT/'control.json', result)
    print(json.dumps({k:result[k] for k in ('validation_micro_f1','minimum_validation_micro_f1','seconds')},indent=2))


if __name__ == '__main__':
    main()
