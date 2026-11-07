"""E31: frozen multimodal features, training-only PCA and small residual adapter."""
import os
for key in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'):
    os.environ[key] = '1'
from pathlib import Path
import hashlib
PINNED = Path(__file__).with_name('e29_pca_boosting.py')
assert hashlib.sha256(PINNED.read_bytes()).hexdigest() == '7eea9c1ec7f491353f1f64408eb258e7782b1fe49200872f3d8c14cf192cbeb8'
from e29_pca_boosting import *
from e29_pca_boosting import load_inputs as load_base
from sklearn.base import ClassifierMixin
import torch
from torch import nn
assert torch.__version__ == '2.14.1+cpu'
torch.set_num_threads(1)
torch.use_deterministic_algorithms(True)
OUT = ROOT / '04_hasil_eksperimen/e31_adapter'
GRID = dict(fusion__mode=['semantic', 'caption_fusion'], fusion__n_components=[64],
            clf__alpha=[0, .2], clf__weight_decay=[.01, .1], clf__class_weight=[None, 'balanced'])

class ResidualClassifier(ClassifierMixin, BaseEstimator):
    def __init__(self, alpha=.2, weight_decay=.01, class_weight=None, epochs=200):
        self.alpha=alpha; self.weight_decay=weight_decay; self.class_weight=class_weight; self.epochs=epochs

    def project(self, x):
        return np.ascontiguousarray(normalize(self.scaler_.transform(x)) * np.sqrt(x.shape[1]), dtype=np.float32)

    def fit(self, x, y):
        self.classes_, target = np.unique(y, return_inverse=True)
        assert len(self.classes_) == 7 and self.class_weight in (None, 'balanced')
        self.n_features_in_=x.shape[1]; self.samples_=len(x)
        self.scaler_=StandardScaler().fit(x)
        data=torch.from_numpy(self.project(x)); truth=torch.tensor(target, dtype=torch.long)
        torch.manual_seed(42)
        self.adapter_=nn.Sequential(nn.Linear(x.shape[1], 32), nn.ReLU(), nn.Linear(32, x.shape[1]))
        self.head_=nn.Linear(x.shape[1], 7)
        self.weights_=(len(y)/(7*np.bincount(target, minlength=7))).astype(np.float32) if self.class_weight=='balanced' else np.ones(7,dtype=np.float32)
        criterion=nn.CrossEntropyLoss(weight=torch.from_numpy(self.weights_))
        params=list(self.head_.parameters()) + (list(self.adapter_.parameters()) if self.alpha else [])
        optimizer=torch.optim.AdamW(params,lr=.01,weight_decay=self.weight_decay,foreach=False)
        self.losses_=[]
        for epoch in range(self.epochs):
            optimizer.zero_grad(set_to_none=True)
            features=data+self.alpha*self.adapter_(data) if self.alpha else data
            loss=criterion(self.head_(features),truth)
            assert torch.isfinite(loss)
            if epoch in (0,self.epochs-1): self.losses_.append(float(loss.detach()))
            loss.backward(); optimizer.step()
        self.adapter_.eval(); self.head_.eval()
        assert all(torch.isfinite(v).all() for m in (self.adapter_,self.head_) for v in m.state_dict().values())
        return self

    def predict_proba(self,x):
        data=torch.from_numpy(self.project(x))
        with torch.no_grad():
            features=data+self.alpha*self.adapter_(data) if self.alpha else data
            prob=torch.softmax(self.head_(features),dim=1).numpy()
        assert np.isfinite(prob).all() and np.allclose(prob.sum(axis=1),1,atol=1e-6)
        return prob

    def predict(self,x):
        return self.classes_[self.predict_proba(x).argmax(axis=1)]


def pipeline():
    return Pipeline([('fusion',BlockPCA(n_components=64)),('clf',ResidualClassifier())])


def fit_metadata(model,x,y):
    clf=model.named_steps['clf']; assert clf.epochs==200 and clf.samples_==len(y)
    counts=np.asarray([sum(y==c) for c in clf.classes_])
    expected=(len(y)/(7*counts)).astype(np.float32) if clf.class_weight=='balanced' else np.ones(7,dtype=np.float32)
    assert np.array_equal(expected,clf.weights_)
    states={prefix+'.'+name:digest(v.detach().numpy()) for prefix,m in [('adapter',clf.adapter_),('head',clf.head_)] for name,v in m.state_dict().items()}
    return dict(fusion=model.named_steps['fusion'].metadata(),classifier=dict(classes=clf.classes_.tolist(),
        samples=clf.samples_,epochs=clf.epochs,dimension=clf.n_features_in_,alpha=clf.alpha,
        normalizer_mean_sha256=digest(clf.scaler_.mean_),normalizer_scale_sha256=digest(clf.scaler_.scale_),
        state_sha256=states,class_weights=clf.weights_.tolist(),loss_endpoints=clf.losses_,
        training_probability_sha256=digest(model.predict_proba(x))))


def load_inputs():
    df,x,y,labels,folds,reference=load_base()
    prior=ROOT/'04_hasil_eksperimen/e30_shrinkage_lda/verification.json'
    assert sha(prior)=='28f3a4938be36f52b2930d7c3e031852b3108819c9e675c29a764c17d79e79e4'
    audit=json.loads(prior.read_text());assert audit['status']=='verified' and audit['samples']==740
    assert audit['verifier_sha256']==sha(Path(__file__).with_name('e30_shrinkage_lda_verify.py'))
    for name,value in audit['sha256'].items():assert sha(prior.parent/name)==value
    signature=dict(worker_sha256=sha(Path(__file__)),transformation_loader_sha256=sha(PINNED),reference=reference,
        prior_verification_sha256=sha(prior),features_sha256=digest(x),grid=GRID,
        outer='Task1 baseline5 seed42',inner='Task2 stratified3 seed42',sklearn=sklearn.__version__,torch=torch.__version__,
        fixed=dict(search_processes=4,threads=1,seed=42,bottleneck=32,epochs=200,lr=.01,
                   optimizer='AdamW foreachFalse',normalization='training-only StandardScaler/L2 sqrtD after BlockPCA64',
                   early_stopping=False,dropout=False,encoder_training=False))
    return df,x,y,labels,folds,signature


def selected_inner(x, y, train, options):
    scores, metadata = [], []
    splits = list(StratifiedKFold(3, shuffle=True, random_state=42).split(np.zeros(len(train)), y[train]))
    for a, b in splits:
        model = pipeline().set_params(**options).fit(x[train[a]], y[train[a]])
        pred = model.predict(x[train[b]])
        scores.append(float(f1_score(y[train[b]], pred, average='macro', zero_division=0)))
        metadata.append(fit_metadata(model, x[train[a]], y[train[a]]))
    return scores, metadata


def main():
    df, x, y, labels, folds, signature = load_inputs()
    OUT.mkdir(exist_ok=True)
    lock = (OUT / 'run.lock').open('a'); fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    protocol = OUT / 'protocol.json'
    if protocol.exists():
        assert json.loads(protocol.read_text()) == signature
    else:
        save(protocol, signature)
    parameters = list(ParameterGrid(GRID)); assert len(parameters) == 16
    predictions = np.empty(740, object); fold_ids = np.zeros(740, int)
    for k, (train, test) in enumerate(folds, 1):
        checkpoint = OUT / f'fold_{k}.json'
        if checkpoint.exists():
            record = json.loads(checkpoint.read_text())
            assert record['signature'] == signature and record['train_indices'] == train.tolist() and record['test_indices'] == test.tolist()
            assert record['sample_ids'] == df.sample_id.iloc[test].to_list()
        else:
            started = time.monotonic()
            search = GridSearchCV(pipeline(), GRID, scoring='f1_macro', n_jobs=4, error_score='raise',
                                  cv=StratifiedKFold(3, shuffle=True, random_state=42))
            search.fit(x[train], y[train]); best = int(search.best_index_)
            assert search.cv_results_['params'] == parameters
            scores = np.column_stack([search.cv_results_[f'split{j}_test_score'] for j in range(3)])
            assert best == int(np.argmax(scores.mean(axis=1)))
            reproduced, fits = selected_inner(x, y, train, parameters[best])
            assert np.allclose(reproduced, scores[best], rtol=0, atol=1e-12)
            pred = search.predict(x[test])
            record = dict(signature=signature, fold=k, train_indices=train.tolist(), test_indices=test.tolist(),
                          sample_ids=df.sample_id.iloc[test].to_list(), predictions=pred.tolist(),
                          grid_params=parameters, inner_fold_scores=scores.tolist(), best_index=best,
                          best_params=parameters[best], inner_macro_f1=float(search.best_score_),
                          selected_inner_fit=fits, outer_fit=fit_metadata(search.best_estimator_, x[train], y[train]),
                          seconds=time.monotonic() - started)
            save(checkpoint, record)
            print(json.dumps(dict(fold=k, params=parameters[best], inner_macro_f1=record['inner_macro_f1'],
                                  seconds=record['seconds'])), flush=True)
        predictions[test] = record['predictions']; fold_ids[test] = k
    assert set(predictions) <= set(labels)
    pd.DataFrame(dict(sample_id=df.sample_id, truth=y, prediction=predictions, fold=fold_ids)).to_csv(OUT / 'oof.csv', index=False)
    save(OUT / 'metrics.json', dict(samples=740, macro_f1=float(f1_score(y, predictions, average='macro', zero_division=0)),
         confusion_matrix=confusion_matrix(y, predictions, labels=labels).tolist(),
         classification=classification_report(y, predictions, labels=labels, output_dict=True, zero_division=0),
         signature=signature, oof_sha256=sha(OUT / 'oof.csv')))
    print('OOF COMPLETE; independent audit required', flush=True)


if __name__ == '__main__':
    main()
