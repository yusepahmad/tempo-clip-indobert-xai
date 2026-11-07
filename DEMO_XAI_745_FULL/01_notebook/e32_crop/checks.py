"""E32 feature-independent preparation, then actualfeatures smoke once verified."""
import argparse,tempfile
from evaluate import *


def synthetic_checks():
    rng=np.random.default_rng(42);x=rng.normal(size=(140,4608)).astype(np.float32);y=np.asarray(['C'+str(i%7) for i in range(140)])
    params=list(ParameterGrid(GRID));assert len(params)==64
    for i in [0,63]:
        options=params[i];a=pipeline().set_params(**options).fit(x[:112],y[:112]);b=pipeline().set_params(**options).fit(x[:112],y[:112])
        assert fit_metadata(a,x[:112],y[:112])==fit_metadata(b,x[:112],y[:112])
        changed=x.copy();changed[112:]*=100;b=pipeline().set_params(**options).fit(changed[:112],y[:112])
        assert fit_metadata(a,x[:112],y[:112])==fit_metadata(b,changed[:112],y[:112])
        if options['fusion__crop_weight']==0:
            changed=x.copy();changed[:,3840:]*=100
            b=pipeline().set_params(**options).fit(changed[:112],y[:112])
            assert np.array_equal(a.predict(x[112:]),b.predict(changed[112:]))
            assert np.array_equal(a.decision_function(x[112:]),b.decision_function(changed[112:]))
    # Missing feature audit must fail before producing OOF.
    import evaluate as module
    old=module.EMB;oldout=module.OUT
    with tempfile.TemporaryDirectory() as name:
        module.EMB=Path(name)/'missing';module.OUT=Path(name)/'output'
        try:module.main()
        except FileNotFoundError:pass
        else:raise AssertionError('Missing feature gate accepted')
        assert not module.OUT.exists()
    module.EMB=old;module.OUT=oldout
    print('PASS syntheticrepeat/heldout/zero-crop isolation/missingfeatures gate',flush=True)


def main(synthetic_only=False):
    synthetic_checks()
    if synthetic_only:return
    df,x,y,labels,folds,signature=load_inputs();train,test=folds[0];params=list(ParameterGrid(GRID))
    began=time.monotonic();model=pipeline().set_params(**params[-1]).fit(x[train],y[train]);seconds=time.monotonic()-began
    fit_metadata(model,x[train],y[train]);pred=model.predict(x[test]);assert len(pred)==148 and set(pred)<=set(labels)
    estimate=seconds*980*1.5;assert estimate<3600
    report=dict(status='preparation_verified',worker_sha256=sha(Path(__file__).with_name('evaluate.py')),
       verifier_sha256=sha(Path(__file__).with_name('verify.py')),checks_source_sha256=sha(Path(__file__)),signature=signature,
       expensive_fit_seconds=seconds,conservative_980fits_seconds=estimate,full_oof_started=False,inference_requests=0,
       checks=['syntheticrepeat/heldout/zero-crop-isolation/missingfeature gate','actual592/148smoke without outerqualityscore','original currentfeature/source/modelpins and grid64'])
    target=ROOT/'04_hasil_eksperimen/e32_evaluator_preparation.json';assert not target.exists();save(target,report);print(json.dumps(report,indent=2),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--synthetic-only',action='store_true');main(parser.parse_args().synthetic_only)
