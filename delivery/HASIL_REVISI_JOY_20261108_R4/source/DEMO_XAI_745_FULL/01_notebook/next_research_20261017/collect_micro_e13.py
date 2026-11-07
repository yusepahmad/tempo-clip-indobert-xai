"""Check the exact E13 job, download only its artifacts, and verify the pilot."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess

import run_micro_e12_structured_decoder as e12
from verify_micro_e12_e13 import verify_e13

KERNEL = 'yusepmuhamadzazuli/tempo-micro-e13-joint-qlora-inner-pilot'
OUT = e12.OUT.parent / 'MICRO_E13_joint_qlora_inner_pilot'


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--include-checkpoints', action='store_true',
                        help='Also download the large adapter weight files.')
    args=parser.parse_args()
    status = subprocess.run(['kaggle','kernels','status',KERNEL], capture_output=True, text=True)
    if status.returncode:
        raise RuntimeError(status.stderr or status.stdout)
    print(status.stdout.strip(), flush=True)
    if 'KernelWorkerStatus.COMPLETE' not in status.stdout:
        print('No completed result downloaded. The existing job must not be restarted based on an observation timeout.')
        return
    raw = OUT / 'raw_kaggle'
    raw.mkdir(exist_ok=True)
    pattern=('^e13_inner_pilot/' if args.include_checkpoints else
             '^e13_inner_pilot/(result\\.json|validation_predictions\\.csv|input_audit\\.jsonl)$')
    subprocess.run(['kaggle','kernels','output',KERNEL,'-p',str(raw),'--force',
                    '--file-pattern',pattern],check=True)
    for path in (raw/'e13_inner_pilot').iterdir():
        if path.is_file():
            shutil.copyfile(path, OUT/path.name)
    result=verify_e13()
    print(json.dumps(result,indent=2))
    files=sorted(p for p in OUT.iterdir() if p.is_file() and p.name!='manifest_sha256.json')
    e12.write_json(OUT/'manifest_sha256.json',{'schema':'tempo-e13-artifacts-v1',
                    'files':{p.name:e12.e10.sha(p) for p in files}})


if __name__=='__main__':
    main()
