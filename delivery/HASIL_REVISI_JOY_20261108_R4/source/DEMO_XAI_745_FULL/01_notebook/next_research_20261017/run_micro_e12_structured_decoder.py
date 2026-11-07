#!/usr/bin/env python3
"""Fully nested three-task stack with a training-only joint label prior."""
import os
for key in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'):
    os.environ[key] = '1'

import csv
import hashlib
import itertools
import json
import time
from pathlib import Path

import numpy as np
from sklearn.ensemble import ExtraTreesClassifier
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import StratifiedKFold

import run_micro_e10_nested_vlm_stacking as e10

TASKS = e10.TASKS
OUT = e10.PROJECT / '04_hasil_eksperimen/next_research_20261017/06_micro_f1/MICRO_E12_structured_decoder'
FEATURES = (e10.CLASSIC, e10.SIGLIP, e10.E15, e10.E22, e10.BGE, e10.CLIP)


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def tree(seed):
    return ExtraTreesClassifier(n_estimators=300, max_features='sqrt',
                                min_samples_leaf=2, n_jobs=4, random_state=seed)


def load_data():
    rows, fold_rows = e10.read(e10.DATA), e10.read(e10.FOLDS)
    ids = np.array([r['sample_id'] for r in rows])
    assert len(ids) == len(set(ids)) == 740
    assert ids.tolist() == [r['sample_id'] for r in fold_rows]
    classic, siglip, vlm, caption, bge, clip = [np.load(p, allow_pickle=False) for p in FEATURES]
    assert ids.tolist() == classic['sample_ids'].tolist() == siglip['sample_ids'].tolist()
    for feature in (vlm, caption, bge):
        assert np.array_equal(ids, feature['sample_id'])
    views = {
        'classic': np.hstack([e10.l2(classic['visual']), e10.l2(siglip['image']), e10.l2(classic['base_mean'])]),
        'qwen_bge': np.hstack([e10.l2(vlm['last_token']), e10.l2(bge['combined'])]),
        'caption_bge': np.hstack([e10.l2(caption['caption_context']), e10.l2(bge['combined']), e10.l2(clip['img'])]),
    }
    assert all(x.shape[0] == 740 and np.isfinite(x).all() for x in views.values())
    names = {t: sorted({r[t] for r in rows}) for t in TASKS}
    truth = np.column_stack([[names[t].index(r[t]) for r in rows] for t in TASKS])
    folds = np.array([int(r['fold']) for r in fold_rows])
    return ids, names, truth, folds, views


def fit_stack(views, train_ids, train_targets, evaluation_ids, counts, individual, seed):
    """Only targets for train_ids are accepted, excluding all evaluation labels."""
    assert train_targets.shape == (len(train_ids), 3)
    assert not set(train_ids) & set(evaluation_ids)
    splits = list(StratifiedKFold(3, shuffle=True, random_state=seed).split(train_ids, train_targets[:, 0]))
    z_train, z_eval = [], []
    for ti, task in enumerate(TASKS):
        for vi, (view, x) in enumerate(views.items()):
            cross = np.zeros((len(train_ids), counts[ti]), dtype=np.float32)
            for si, (a, b) in enumerate(splits):
                assert not set(train_ids[a]) & set(train_ids[b])
                model = e10.base_model(view, seed + 100 * ti + 10 * vi + si)
                model.fit(x[train_ids[a]], train_targets[a, ti])
                cross[b] = e10.scores(model, x[train_ids[b]], counts[ti])
            model = e10.base_model(view, seed + 1000 + 100 * ti + vi)
            model.fit(x[train_ids], train_targets[:, ti])
            z_train.append(cross)
            z_eval.append(e10.scores(model, x[evaluation_ids], counts[ti]))
    z_train, z_eval = np.hstack(z_train), np.hstack(z_eval)
    flat = []
    for ti in range(3):
        model = tree(seed + 2000 + ti)
        model.fit(z_train, train_targets[:, ti])
        flat.append(e10.scores(model, z_eval, counts[ti]))
    binary = tree(seed + 3000)
    binary.fit(z_train, (train_targets[:, 2] == individual).astype(int))
    p_ind = e10.scores(binary, z_eval, 2)[:, 1]
    non_rows = np.where(train_targets[:, 2] != individual)[0]
    non_model = tree(seed + 4000)
    non_model.fit(z_train[non_rows], train_targets[non_rows, 2])
    p_non = e10.scores(non_model, z_eval, counts[2])
    hierarchical = p_non * (1 - p_ind[:, None])
    hierarchical[:, individual] = p_ind
    result = {'flat': flat, 'hierarchical': flat[:2] + [hierarchical]}
    for family in result.values():
        for p in family:
            assert np.isfinite(p).all() and np.allclose(p.sum(1), 1.0)
    return result


def joint_correction(targets, counts, pseudocount):
    marginals = [(np.bincount(targets[:, i], minlength=c) + 1) / (len(targets) + c)
                 for i, c in enumerate(counts)]
    independent = marginals[0][:, None, None] * marginals[1][None, :, None] * marginals[2][None, None, :]
    joint = np.zeros(counts, dtype=float)
    np.add.at(joint, tuple(targets.T), 1)
    joint = (joint + pseudocount * independent) / (len(targets) + pseudocount)
    return np.log(joint / independent)


def decode(probabilities, correction, strength, mode):
    if strength == 0:
        return np.column_stack([p.argmax(1) for p in probabilities])
    logs = [np.log(np.clip(p, 1e-9, 1.0)) for p in probabilities]
    logits = logs[0][:, :, None, None] + logs[1][:, None, :, None] + logs[2][:, None, None, :]
    logits += strength * correction[None]
    if mode == 'map':
        indices = logits.reshape(len(logits), -1).argmax(1)
        return np.column_stack(np.unravel_index(indices, correction.shape))
    logits -= logits.max(axis=(1, 2, 3), keepdims=True)
    joint = np.exp(logits)
    return np.column_stack([joint.sum(axis=axes).argmax(1) for axes in ((2, 3), (1, 3), (1, 2))])


def candidates():
    result = []
    for head in ('flat', 'hierarchical'):
        result.append(dict(head=head, strength=0.0, pseudocount=50, mode='marginal'))
        for strength, pseudocount, mode in itertools.product((0.25, 0.5, 1.0, 2.0), (10, 50, 200), ('marginal', 'map')):
            result.append(dict(head=head, strength=strength, pseudocount=pseudocount, mode=mode))
    return result


def task_scores(truth, predicted):
    return {t: float(accuracy_score(truth[:, i], predicted[:, i])) for i, t in enumerate(TASKS)}


def write_predictions(path, ids, folds, names, truth, predicted):
    fields = ['sample_id', 'fold'] + [t + suffix for t in TASKS for suffix in ('_truth', '_pred')]
    with path.open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for i, sample_id in enumerate(ids):
            row = dict(sample_id=sample_id, fold=int(folds[i]))
            for ti, task in enumerate(TASKS):
                row[task + '_truth'] = names[task][truth[i, ti]]
                row[task + '_pred'] = names[task][predicted[i, ti]]
            writer.writerow(row)


def main():
    started = time.monotonic()
    OUT.mkdir(parents=True, exist_ok=True)
    ids, names, truth, folds, views = load_data()
    counts = tuple(len(names[t]) for t in TASKS)
    individual = names[TASKS[2]].index('individual')
    configs = candidates()
    config = dict(schema='tempo-micro-e12-v1', candidates=configs, meta_head='ExtraTrees300_leaf2',
                  inner_splits=3, stack_crossfit_splits=3,
                  leakage_control='rebuild the entire stack inside every inner training partition',
                  selection='max minimum inner accuracy; mean tie-breaker; prefer strength=0 on exact tie',
                  dataset_sha256=e10.sha(e10.DATA), folds_sha256=e10.sha(e10.FOLDS),
                  source_sha256=e10.sha(Path(__file__)),
                  feature_sha256={str(p.relative_to(e10.ROOT)): e10.sha(p) for p in FEATURES},
                  limitation='internal CV; repeated model selection on this corpus introduces research-level selection bias')
    write_json(OUT / 'config.json', config)
    predictions = np.full_like(truth, -1)
    control = np.full_like(truth, -1)
    details, audit = [], []
    for fold in range(1, 6):
        train, test = np.where(folds != fold)[0], np.where(folds == fold)[0]
        inner_pred = [np.full((len(train), 3), -1) for _ in configs]
        inner = list(StratifiedKFold(3, shuffle=True, random_state=131000 + fold).split(train, truth[train, 0]))
        for si, (a, b) in enumerate(inner):
            print(f'fold={fold} inner={si+1} fit_stack train={len(a)} validation={len(b)}', flush=True)
            probabilities = fit_stack(views, train[a], truth[train[a]], train[b], counts, individual, 132000 + fold*10000 + si*5000)
            priors = {v: joint_correction(truth[train[a]], counts, v) for v in (10, 50, 200)}
            for ci, candidate in enumerate(configs):
                inner_pred[ci][b] = decode(probabilities[candidate['head']], priors[candidate['pseudocount']], candidate['strength'], candidate['mode'])
            audit.append(dict(outer_fold=fold, inner_split=si+1,
                              train_ids=ids[train[a]].tolist(), validation_ids=ids[train[b]].tolist(),
                              outer_test_ids=ids[test].tolist()))
        evaluations = []
        for candidate, predicted in zip(configs, inner_pred):
            assert (predicted >= 0).all()
            scores = task_scores(truth[train], predicted)
            evaluations.append(dict(config=candidate, micro_f1=scores, minimum=min(scores.values()), mean=float(np.mean(list(scores.values())))))
        selected = max(evaluations, key=lambda r: (r['minimum'], r['mean'], -r['config']['strength']))
        chosen = selected['config']
        print(f'fold={fold} selected={chosen} inner_min={selected["minimum"]:.6f}; refit stack', flush=True)
        probabilities = fit_stack(views, train, truth[train], test, counts, individual, 200000 + fold*10000)
        prior = joint_correction(truth[train], counts, chosen['pseudocount'])
        predictions[test] = decode(probabilities[chosen['head']], prior, chosen['strength'], chosen['mode'])
        control[test] = decode(probabilities['flat'], prior, 0, 'marginal')
        scores = task_scores(truth[test], predictions[test])
        details.append(dict(fold=fold, selected=selected, candidates=evaluations,
                            outer_micro_f1=scores, control_micro_f1=task_scores(truth[test], control[test])))
        write_json(OUT / f'fold{fold}_selection.json', details[-1])
        print(f'fold={fold} outer={scores}', flush=True)
    assert (predictions >= 0).all() and (control >= 0).all()
    write_predictions(OUT/'predictions.csv', ids, folds, names, truth, predictions)
    write_predictions(OUT/'control_predictions.csv', ids, folds, names, truth, control)
    micro = task_scores(truth, predictions)
    result = dict(schema='tempo-micro-e12-v1', status='complete',
                  model_contract='one fully nested multimodal stack and joint label decoder',
                  micro_f1=micro, macro_f1_diagnostic={t:float(f1_score(truth[:, i], predictions[:, i], average='macro')) for i,t in enumerate(TASKS)},
                  minimum_micro_f1=min(micro.values()), all_tasks_at_least_0_70=min(micro.values()) >= .70,
                  control_micro_f1=task_scores(truth,control), fold_details=details,
                  seconds=time.monotonic()-started, predictions_sha256=e10.sha(OUT/'predictions.csv'))
    write_json(OUT/'result.json', result)
    write_json(OUT/'split_audit.json', audit)
    write_json(OUT/'metrics.json', {k:result[k] for k in ('micro_f1','macro_f1_diagnostic','minimum_micro_f1','all_tasks_at_least_0_70','control_micro_f1')})
    decision = ('lulus' if result['all_tasks_at_least_0_70'] else 'belum lulus')
    (OUT/'decision.md').write_text(f'# MICRO-E12\n\nGate 0,70: {decision}.\n\nMicro-F1: {micro}.\n\nKontrol tanpa prior: {result["control_micro_f1"]}.\n\nEvaluasi internal; tidak menjadi validasi independen akibat penggunaan korpus berulang.\n')
    print(json.dumps({k:result[k] for k in ('micro_f1','minimum_micro_f1','control_micro_f1','seconds')},indent=2), flush=True)


if __name__ == '__main__':
    main()
