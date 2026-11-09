"""Reuse training-only RBF kernels across the unchanged612-parameter search."""
import fcntl
import json
from pathlib import Path
import time
from evaluate import (ROOT, GRID, CaptionFusion, load_inputs as load_reference, sha, save,
                      np, pd, f1_score, classification_report, confusion_matrix)
from sklearn.metrics.pairwise import rbf_kernel
from sklearn.model_selection import ParameterGrid, StratifiedKFold
from sklearn.svm import SVC

OUT = ROOT / '04_hasil_eksperimen/e22_oof_cached'


def load_inputs():
    df, x, y, labels, folds, reference = load_reference()
    signature = dict(cached_worker_sha256=sha(Path(__file__)), reference_signature=reference,
                     backend='same float64 training projection/gamma; cached RBF Gram and precomputed SVC')
    return df, x, y, labels, folds, signature


def prepare(x, train, test):
    assert not set(train) & set(test)
    blocks = [(0, 1536), (1536, 2560), (2560, 3072), (3072, 4096), (4096, 5120)]
    from sklearn.preprocessing import StandardScaler, normalize
    from evaluate import digest
    training, testing, fits = [], [], []
    for a, b in blocks:
        scaler = StandardScaler().fit(x[train, a:b])
        training.append(normalize(scaler.transform(x[train, a:b])))
        testing.append(normalize(scaler.transform(x[test, a:b])))
        fits.append(dict(start=a, stop=b, mean_sha256=digest(scaler.mean_), scale_sha256=digest(scaler.scale_)))
    return dict(train=training, test=testing, fit=fits, kernels={})


def selected_blocks(options):
    mode = options['fusion__mode']
    view = 4 if mode in ('caption_context_only', 'fusion_context') else 3
    if mode.endswith('_only'):
        return [(view, 1)]
    return [(0, options['fusion__e5_weight']), (1, 1), (2, options['fusion__clip_weight']),
            (view, options['fusion__caption_weight'])]


def projection(cache, options, test=False):
    blocks = cache['test' if test else 'train']
    return np.asarray(np.hstack([blocks[index] * weight for index, weight in selected_blocks(options)]), dtype=np.float64)


def metadata(cache, options):
    return [dict(cache['fit'][index], weight=weight) for index, weight in selected_blocks(options)]


def kernels(cache, options):
    key = tuple(sorted((key, str(value)) for key, value in options.items()
                       if key not in ('clf__C', 'clf__class_weight')))
    if key not in cache['kernels']:
        train = projection(cache, options); test = projection(cache, options, True)
        gamma = options['clf__gamma']
        if gamma == 'scale':
            variance = train.var()
            gamma = 1 / (train.shape[1] * variance) if variance else 1.0
        cache['kernels'][key] = (rbf_kernel(train, train, gamma=gamma), rbf_kernel(test, train, gamma=gamma))
    return cache['kernels'][key]


def predict(cache, options, y_train):
    train, test = kernels(cache, options)
    model = SVC(kernel='precomputed', C=options['clf__C'], class_weight=options['clf__class_weight'])
    model.fit(train, y_train)
    return model.predict(test)


def main():
    df, x, y, labels, folds, signature = load_inputs()
    OUT.mkdir(exist_ok=True)
    lock = (OUT / 'run.lock').open('a'); fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    protocol = OUT / 'protocol.json'
    if protocol.exists():
        assert json.loads(protocol.read_text()) == signature
    else:
        save(protocol, signature)
    parameters = list(ParameterGrid(GRID)); assert len(parameters) == 612
    prediction = np.empty(740, object); fold_ids = np.zeros(740, int)
    for k, (train, test) in enumerate(folds, 1):
        path = OUT / f'fold_{k}.json'
        if path.exists():
            r = json.loads(path.read_text())
            assert r['signature'] == signature and r['train_indices'] == train.tolist() and r['test_indices'] == test.tolist()
            assert r['sample_ids'] == df.sample_id.iloc[test].to_list()
        else:
            started = time.monotonic()
            inner = list(StratifiedKFold(3, shuffle=True, random_state=42).split(np.zeros(len(train)), y[train]))
            caches = [prepare(x, train[a], train[b]) for a, b in inner]
            scores = [[float(f1_score(y[train[b]], predict(cache, options, y[train[a]]), average='macro', zero_division=0))
                       for (a, b), cache in zip(inner, caches)] for options in parameters]
            means = np.mean(scores, axis=1); best = int(np.argmax(means))
            outer_cache = prepare(x, train, test)
            pred = predict(outer_cache, parameters[best], y[train])
            r = dict(signature=signature, fold=k, train_indices=train.tolist(), test_indices=test.tolist(),
                     sample_ids=df.sample_id.iloc[test].to_list(), predictions=pred.tolist(),
                     grid_params=parameters, inner_fold_scores=scores, best_index=best, best_params=parameters[best],
                     inner_macro_f1=float(means[best]),
                     selected_inner_fit=[metadata(cache, parameters[best]) for cache in caches],
                     outer_fit=metadata(outer_cache, parameters[best]), seconds=time.monotonic() - started)
            save(path, r)
            print(json.dumps(dict(fold=k, params=parameters[best], inner_macro_f1=float(means[best]),
                                  seconds=r['seconds'])), flush=True)
        prediction[test] = r['predictions']; fold_ids[test] = k
    assert set(prediction) <= set(labels)
    pd.DataFrame(dict(sample_id=df.sample_id, truth=y, prediction=prediction, fold=fold_ids)).to_csv(OUT / 'oof.csv', index=False)
    save(OUT / 'metrics.json', dict(samples=740, macro_f1=float(f1_score(y, prediction, average='macro', zero_division=0)),
         confusion_matrix=confusion_matrix(y, prediction, labels=labels).tolist(),
         classification=classification_report(y, prediction, labels=labels, output_dict=True, zero_division=0),
         signature=signature, oof_sha256=sha(OUT / 'oof.csv')))
    print('CACHED OOF COMPLETE; raw pipeline audit required', flush=True)


if __name__ == '__main__':
    main()
