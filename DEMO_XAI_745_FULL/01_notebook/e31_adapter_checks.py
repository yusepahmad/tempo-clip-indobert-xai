"""E31 preparation: CPU determinism, heldout isolation and bounded runtime."""
from e31_adapter import *
import tempfile


def main():
    started=time.monotonic();params=list(ParameterGrid(GRID));assert len(params)==16
    rng=np.random.default_rng(42);x=rng.normal(size=(140,4096)).astype(np.float32)
    y=np.asarray(['CLASS_'+str(i%7) for i in range(140)]);y[:21]='CLASS_0'
    train=np.arange(112);test=np.arange(112,140)
    for index in [0,15]:
        options=dict(params[index],fusion__n_components=16)
        model=pipeline().set_params(**options).fit(x[train],y[train])
        other=pipeline().set_params(**options).fit(x[train],y[train])
        assert fit_metadata(model,x[train],y[train])==fit_metadata(other,x[train],y[train])
        assert np.array_equal(model.predict_proba(x[test]),other.predict_proba(x[test]))
        changed=x.copy();changed[test]*=100
        other=pipeline().set_params(**options).fit(changed[train],y[train])
        assert fit_metadata(model,x[train],y[train])==fit_metadata(other,x[train],y[train])
        if options['clf__alpha']==0:
            before=model.predict_proba(x[test]).copy()
            with torch.no_grad():
                for v in model.named_steps['clf'].adapter_.parameters():v.add_(1000)
            assert np.array_equal(before,model.predict_proba(x[test]))
    restricted=[{key:[value] for key,value in dict(params[index],fusion__n_components=16).items()} for index in [0,15]]
    cv=StratifiedKFold(3,shuffle=True,random_state=42)
    serial=GridSearchCV(pipeline(),restricted,scoring='f1_macro',cv=cv,n_jobs=1,error_score='raise').fit(x,y)
    parallel=GridSearchCV(pipeline(),restricted,scoring='f1_macro',cv=cv,n_jobs=4,error_score='raise').fit(x,y)
    for j in range(3):assert np.array_equal(serial.cv_results_[f'split{j}_test_score'],parallel.cv_results_[f'split{j}_test_score'])
    assert serial.best_params_==parallel.best_params_
    assert fit_metadata(serial.best_estimator_,x,y)==fit_metadata(parallel.best_estimator_,x,y)
    df,real,truth,labels,folds,signature=load_inputs()
    spec=importlib.util.spec_from_file_location('e31_missing_prior',Path(__file__).with_name('e31_adapter.py'))
    gate=importlib.util.module_from_spec(spec);spec.loader.exec_module(gate)
    with tempfile.TemporaryDirectory() as n:
        gate.ROOT=Path(n);gate.OUT=Path(n)/'output'
        gate.load_base=lambda:(df,real,truth,labels,folds,signature['reference'])
        try:gate.main()
        except FileNotFoundError:pass
        else:raise AssertionError('Missing prior accepted')
        assert not gate.OUT.exists()
    train,test=folds[0];began=time.monotonic()
    model=pipeline().set_params(**params[-1]).fit(real[train],truth[train])
    seconds=time.monotonic()-began
    fit_metadata(model,real[train],truth[train]);pred=model.predict(real[test])
    assert len(pred)==148 and set(pred)<=set(labels)
    estimate=seconds*260*1.5;assert estimate<=7200
    report=dict(status='preparation_verified',worker_sha256=sha(Path(__file__).with_name('e31_adapter.py')),
        verifier_sha256=sha(Path(__file__).with_name('e31_adapter_verify.py')),checks_source_sha256=sha(Path(__file__)),signature=signature,
        synthetic_samples=140,grid_points=16,expensive_fit_seconds=seconds,conservative_serial_seconds_260fits_1_5margin=estimate,
        seconds_total=time.monotonic()-started,full_oof_started=False,inference_requests=0,
        checks=['repeatfit/PCA/normalizer/adapterstate/probabilities exact','heldout perturbation leaves fitted state unchanged',
                'alpha0 control ignores adapterstate','imbalanced training-only classweights exact','serial/joblib4 all6scores/bestparams/state exact',
                'missing prior rejected before output','actual592/148smoke without outerquality score; conservative runtime <=2h'])
    target=ROOT/'04_hasil_eksperimen/e31_preparation.json';assert not target.exists()
    save(target,report);print(json.dumps(report,indent=2),flush=True)

if __name__=='__main__':main()
