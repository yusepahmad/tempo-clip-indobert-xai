"""Bounded collector for the already-authorized private QLoRA job; never resubmits."""
import argparse
from datetime import datetime,timezone
import json
import os
from pathlib import Path
import shutil
import tempfile
import time

import pandas as pd
import evaluate as ev
import followup_r21
import manage_qwen_basic as jobs


def publish(package,destination):
    package=Path(package);destination=Path(destination);assert not destination.exists()
    source=jobs.APP/'04_hasil_eksperimen/revisi_ii/experiments/RII_QWEN_QLORA_BASIC'
    with tempfile.TemporaryDirectory(prefix='joy-r21-tables-') as temp:
        root=Path(temp);shutil.copytree(package/'inputs',root/'inputs');(root/'analysis').mkdir()
        frame=pd.read_csv(source/'predictions.csv');name='RII_QWEN_QLORA_BASIC';rows=[]
        reference=pd.read_csv(root/'inputs/DATASET_740_TASK2_DOMAIN.csv')
        folds=pd.read_csv(root/'inputs/folds.csv').set_index('sample_id')['fold']
        ev.validate_predictions(frame,reference,folds)
        shutil.copy2(source/'predictions.csv',root/f'inputs/predictions/{name}.csv')
        for i,task in enumerate(ev.TASKS):
            labels=sorted(reference[task].unique());truth=frame[task+'_truth'];prediction=frame[task+'_pred']
            low,high=ev.bootstrap_macro(truth,prediction,labels,seed=ev.SEED+i)
            rows.append(dict(experiment=name,task=task,samples=740,macro_ci_low=low,macro_ci_high=high,
                             **ev.metrics(truth,prediction,labels)))
        metrics=pd.concat([pd.read_csv(package/'analysis/metrics.csv'),pd.DataFrame(rows)],ignore_index=True)
        metrics.to_csv(root/'analysis/metrics.csv',index=False)
        destination.mkdir(parents=True);followup_r21.build(root,destination)
        shutil.copy2(source/'predictions.csv',destination/'RII_QWEN_QLORA_BASIC_predictions.csv')
        shutil.copy2(source/'result.json',destination/'RII_QWEN_QLORA_BASIC_result.json')
        rich=pd.read_csv(package/'inputs/predictions/MICRO_E14_joint_qlora_oof.csv').set_index('sample_id').sort_index()
        basic=frame.set_index('sample_id').loc[rich.index];paired=[]
        for i,task in enumerate(ev.TASKS):
            paired.append(dict(before=name,after='MICRO_E14_joint_qlora_oof',task=task,
                **ev.paired_comparison(basic[task+'_truth'],basic[task+'_pred'],rich[task+'_pred'],sorted(reference[task].unique()),seed=ev.SEED+i)))
        adjusted=ev.holm([r['mcnemar_exact_p'] for r in paired])
        for row,pvalue in zip(paired,adjusted):
            row['mcnemar_holm_p_three_tasks']=float(pvalue)
            row['family']='three R21 task comparisons; accuracy inference only'
        pd.DataFrame(paired).to_csv(destination/'R21_PAIRED_BASIC_VS_RICH.csv',index=False)
        ev.write_json(destination/'VERIFICATION.json',dict(status='verified_740_predictions_and_tables',created_at=datetime.now(timezone.utc).isoformat(),
                      samples=740,folds=5,training_results_real=True,comparison_caveats='See R21_TABEL_2X2.md; original review status is not automatically closed.'))


def watch(package,destination,seconds=36000):
    assert json.loads((jobs.OUT/'full/submission.json').read_text())['state']=='submitted'
    import fcntl
    lock=(jobs.OUT/'full/collector.lock').open('w')
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    if (Path(destination)/'VERIFICATION.json').exists():
        assert json.loads((Path(destination)/'VERIFICATION.json').read_text())['status']=='verified_740_predictions_and_tables'
        return
    ev.write_json(jobs.OUT/'full/WATCH_STATE.json',dict(status='monitoring',started_at=datetime.now(timezone.utc).isoformat(),
                  timeout_seconds=seconds,destination=str(destination),resubmission=False,pid=os.getpid()))
    start=time.monotonic();errors=0
    while time.monotonic()-start<seconds:
        try:
            status=jobs.status('full');errors=0
            if status=='COMPLETE':
                jobs.collect('full');publish(package,destination)
                ev.write_json(jobs.OUT/'full/WATCH_STATE.json',dict(status='collected_and_verified',destination=str(destination)));return
            if status in {'ERROR','CANCEL_ACKNOWLEDGED','CANCELLED'}:
                ev.write_json(jobs.OUT/'full/WATCH_STATE.json',dict(status='stopped_remote_failure',remote_status=status));return
        except Exception as exc:
            errors+=1;ev.write_json(jobs.OUT/'full/WATCH_STATE.json',dict(status='retrying_read_or_collection',error=str(exc)[:1000],consecutive_errors=errors))
            if errors>=3:raise
        # The script is bounded, runs in its own process and never submits jobs.
        for _ in range(10):time.sleep(30)
    ev.write_json(jobs.OUT/'full/WATCH_STATE.json',dict(status='monitor_timeout_no_resubmission',seconds=seconds))


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--package',required=True,type=Path);ap.add_argument('--destination',required=True,type=Path)
    ap.add_argument('--seconds',type=int,default=36000);a=ap.parse_args();watch(a.package,a.destination,a.seconds)
