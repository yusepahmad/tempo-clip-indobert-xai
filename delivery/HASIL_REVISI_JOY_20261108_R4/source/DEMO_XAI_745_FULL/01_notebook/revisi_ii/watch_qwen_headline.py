"""Bounded collector for an existing submission; no training resubmission."""
import argparse
from datetime import datetime,timezone
import fcntl
import json
import os
from pathlib import Path
import time
import build_colab_followup
from build_full_delivery import seal
from build_technical_delivery import build
from evaluate import write_json
import manage_qwen_headline as jobs
from verify_full_archive import verify


def watch(source,destination,seconds=36000):
    destination=Path(destination).resolve()
    ledger=json.loads((jobs.OUT/'full/submission.json').read_text())
    assert ledger['state']=='submitted' and ledger['kernel']==jobs.REF+'full'
    state=jobs.OUT/'full/WATCH_STATE.json'
    lock=(jobs.OUT/'full/collector.lock').open('w')
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    started=time.monotonic();errors=0
    def record(status,**fields):
        write_json(state,dict(status=status,observed_at=datetime.now(timezone.utc).isoformat(),pid=os.getpid(),destination=str(destination),resubmission=False,timeout_seconds=seconds,**fields))
    record('monitoring')
    while time.monotonic()-started<seconds:
        try:
            remote=jobs.status('full');errors=0
        except Exception as exc:
            errors+=1;record('retrying_status',error=str(exc)[:1200],consecutive_errors=errors)
            if errors>=3:raise
            time.sleep(60);continue
        if remote in {'ERROR','CANCELLED','CANCEL_ACKNOWLEDGED'}:
            record('stopped_remote_failure',remote_status=remote);return
        if remote=='COMPLETE':
            record('collecting');jobs.collect('full')
            assert not destination.exists(),'Destination exists; inspect previous build first'
            record('building_verified_result_delivery')
            root,result=build(source,destination)
            assert result['state']['completed']==20 and result['r21']['literal_pending']==0
            archive=root.with_suffix('.zip');seal(root,archive)
            verification=verify(archive)
            write_json(root.parent/(root.name+'_EXTRACTED_VERIFICATION.json'),verification)
            portable=build_colab_followup.build(root,root.parent/(root.name+'_R32'))
            write_json(root.parent/(root.name+'_R32/PREPARATION.json'),portable)
            record('collected_built_and_verified',archive=str(archive),completed=20,open=8,colab_verified=False,human_evidence_complete=False)
            return
        record('monitoring',remote_status=remote);time.sleep(60)
    record('monitor_timeout_no_resubmission')


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path,required=True);ap.add_argument('--destination',type=Path,required=True);ap.add_argument('--seconds',type=int,default=36000)
    args=ap.parse_args()
    try:watch(args.source,args.destination,args.seconds)
    except Exception as exc:
        write_json(jobs.OUT/'full/WATCH_STATE.json',dict(status='collector_failed_no_resubmission',error=str(exc)[:2000],observed_at=datetime.now(timezone.utc).isoformat(),resubmission=False,pid=os.getpid()))
        raise
