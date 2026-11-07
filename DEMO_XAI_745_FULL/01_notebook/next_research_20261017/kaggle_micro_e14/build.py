"""Freeze E14 before submission and generate self-contained per-fold kernels."""
import base64
import csv
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
APP = REPO / 'DEMO_XAI_745_FULL'
SOURCE = HERE.parent / 'kaggle_micro_e07/worker.py'
PILOT = APP / '04_hasil_eksperimen/next_research_20261017/06_micro_f1/MICRO_E13_joint_qlora_inner_pilot/result.json'
FOLDS = APP / '04_hasil_eksperimen/e42_tail_grid/oof.csv'
OUT = APP / '04_hasil_eksperimen/next_research_20261017/06_micro_f1/MICRO_E14_joint_qlora_oof'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def replace_once(source, old, new):
    assert source.count(old) == 1, old[:150]
    return source.replace(old, new)


HELPERS = '''
def capture_adapter(model):
    return {name: value.detach().cpu().clone() for name, value in model.named_parameters() if value.requires_grad}


def restore_adapter(model, state):
    parameters = {name: value for name, value in model.named_parameters() if value.requires_grad}
    assert set(parameters) == set(state)
    with torch.no_grad():
        for name, value in state.items():
            parameter = parameters[name]
            assert parameter.shape == value.shape
            parameter.copy_(value.to(device=parameter.device, dtype=parameter.dtype))
    assert all(torch.equal(parameters[name].detach().cpu(), value) for name, value in state.items())


def save_checkpoint(phase, epoch, model, optimizer, scaler, rng, history):
    payload = {"phase": phase, "epoch": epoch, "adapter": capture_adapter(model),
               "optimizer": optimizer.state_dict(), "scaler": scaler.state_dict(),
               "numpy_rng": rng.bit_generator.state, "torch_rng": torch.get_rng_state(),
               "cuda_rng": torch.cuda.get_rng_state_all(), "python_rng": random.getstate(),
               "history": history, "protocol_sha256": sha(Path("/kaggle/working/protocol.json")),
               "source_sha256": sha(Path(__file__)), "fold": FOLD}
    temporary = OUT / f"{phase}_checkpoint.tmp"
    torch.save(payload, temporary)
    temporary.replace(OUT / f"{phase}_checkpoint.pt")
    (OUT / "progress.json").write_text(json.dumps({"phase":phase, "epoch":epoch, "fold":FOLD,
                                                  "history":history, "status":"running"},indent=2))


def prepare_reuse(frame, inner, validation, train, test, audits, model):
    protocol = json.loads(Path("/kaggle/working/protocol.json").read_text())
    assert sha(Path("/kaggle/working/protocol.json")) == os.environ["E14_PROTOCOL_SHA256"]
    assert sha(Path(__file__)) == os.environ["E14_WORKER_SHA256"]
    frozen = json.loads(Path("/kaggle/working/folds.json").read_text())
    for index in train:
        assert frozen[frame.sample_id.iloc[index]] != FOLD
    for index in test:
        assert frozen[frame.sample_id.iloc[index]] == FOLD
    split = {"inner_train_ids": frame.sample_id.iloc[inner].tolist(),
             "inner_validation_ids": frame.sample_id.iloc[validation].tolist(),
             "outer_train_ids": frame.sample_id.iloc[train].tolist(),
             "outer_test_ids": frame.sample_id.iloc[test].tolist()}
    (OUT/"split.json").write_text(json.dumps(split,indent=2))
    if FOLD != 1:
        return None
    matches = [p for p in Path("/kaggle/input").rglob("result.json") if p.parent.name=="e13_inner_pilot"]
    assert len(matches)==1
    path=matches[0]
    assert sha(path)==protocol["fold1_reuse"]["pilot_result_sha256"]
    pilot=json.loads(path.read_text())
    assert pilot["status"]=="complete" and not pilot["outer_test_evaluated"]
    assert pilot["source_sha256"]==protocol["fold1_reuse"]["pilot_worker_sha256"]
    assert set(split["inner_train_ids"])==set(pilot["split"]["inner_train_ids"])
    assert set(split["inner_validation_ids"])==set(pilot["split"]["inner_validation_ids"])
    assert set(split["outer_test_ids"])==set(pilot["split"]["untouched_outer_test_ids"])
    original=[json.loads(line) for line in (path.parent/"input_audit.jsonl").read_text().splitlines()]
    lookup={(row["sample_id"],row["task"]):row for row in audits}
    assert len(original)==len(train)*len(TASKS)
    for row in original:
        assert row==lookup[(row["sample_id"],row["task"])], row["sample_id"]
    initial=torch.load(path.parent/"initial_adapter_state.pt",map_location="cpu",weights_only=True)
    restore_adapter(model,initial)
    return [row for row in pilot["history"] if row["epoch"]<=MAX_EPOCHS]

'''


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    pilot=json.loads(PILOT.read_text())
    assert pilot['status']=='complete' and pilot['selected_epoch']==3
    with FOLDS.open() as handle:
        rows=list(csv.DictReader(handle))
    folds={r['sample_id']:int(r['fold']) for r in rows}
    assert len(folds)==740 and all(list(folds.values()).count(f)==148 for f in range(1,6))
    protocol={
        'schema':'tempo-micro-e14-protocol-v1', 'date':'2026-10-19',
        'model':'Qwen/Qwen3-VL-8B-Instruct','revision':'0c351dd01ed87e9c1b53cbc748cba10e6187ff3b',
        'tasks':['task1_issue','task2_domain_sumber','task3_primary_entity_type'],
        'dataset_sha256':'cba20f8250bcb59481ed2d3d7d5d42fb8242c96a7ba2d11a2cd02ad80862961a',
        'outer_split':'E42 StratifiedKFold5 seed42; same 740 sample IDs and 148 per test fold',
        'folds_source_sha256':sha(FOLDS.read_bytes()),'fold_mapping':folds,
        'inner_split':{'validation_fraction':.2,'stratify':'task1','seed':'42+fold'},
        'inner_epoch_candidates':[1,2,3],
        'epoch_selection':'maximum (minimum_micro_f1, mean_micro_f1); exact tie picks earliest',
        'refit':'reset exact initial adapter and optimizer/scaler; all 592 outer-training rows; selected epochs',
        'seed_initial_and_inner':'42+fold','seed_refit':'42000+fold',
        'optimizer':{'name':'AdamW','lr':.0001,'weight_decay':.01,'accumulation':8,'clip_grad_norm':1.0},
        'lora':{'rank':16,'alpha':32,'dropout':.05,'target_modules':['q_proj','k_proj','v_proj','o_proj']},
        'quantization':'NF4 double quant, FP16 compute; trainable LoRA FP32',
        'image':{'thumbnail':[384,384],'processor_min_pixels':16384,'processor_max_pixels':147456},
        'input':'original image, verified headline/supporting, label-free E01 description and visual reason',
        'prompt_and_loop_source_sha256':sha(SOURCE.read_bytes()),
        'dependencies':{'transformers':'5.17.0','peft':'0.21.2','bitsandbytes':'0.50.2','accelerate':'1.15.0'},
        'fold1_reuse':{'pilot_kernel':'yusepmuhamadzazuli/tempo-micro-e13-joint-qlora-inner-pilot',
                       'pilot_version':1,'pilot_result_sha256':sha(PILOT.read_bytes()),
                       'pilot_worker_sha256':pilot['source_sha256'],
                       'checks':['exact split','exact input audits','exact initial adapter','only epochs 1-3']},
        'acceptance':'each of the 3 micro-F1 scores >=0.70 across exactly 740 outer OOF rows',
        'limitations':'internal CV on repeatedly used corpus; prior pilot informed protocol; no new independent test set',
        'budget':{'initial_gpu_hours_remaining':21.86,'estimated_gpu_hours':[18,21],'max_concurrent_jobs':2},
    }
    protocol_bytes=(json.dumps(protocol,sort_keys=True,indent=2)+'\n').encode()
    frozen=OUT/'frozen_protocol.json'
    if frozen.exists():
        assert frozen.read_bytes()==protocol_bytes,'Frozen protocol changed; use a new experiment ID'
    else:
        frozen.write_bytes(protocol_bytes)
    source=SOURCE.read_text()
    source=source.replace('# training set. Twelve joint epochs equal about four effective passes/task.',
                          '# training set. E14 selects among three joint epochs (about one pass/task).')
    source=replace_once(source,'os.environ["HF_HOME"] = "/kaggle/working/.cache/huggingface"','os.environ["HF_HOME"] = "/tmp/tempo_hf_cache"')
    source=replace_once(source,'MAX_EPOCHS = 2 if SMOKE else 12','MAX_EPOCHS = 3')
    source=replace_once(source,'OUT.mkdir(exist_ok=True)','OUT = Path(f"/kaggle/working/e14_fold{FOLD}")\nOUT.mkdir(exist_ok=True)')
    source=replace_once(source,'def main():\n','def main():\n    seed_all(42 + FOLD)\n    run_started = time.monotonic()\n')
    source=replace_once(source,'    initial_state = {name: value.detach().cpu().clone() for name, value in model.state_dict().items() if "lora_" in name}',
        '    reused_history = prepare_reuse(frame, inner, validation, train, test, audits, model)\n    initial_state = capture_adapter(model)\n    torch.save(initial_state, OUT / "initial_adapter_state.pt")')
    source=replace_once(source,'best = -1.0','best = (-1.0, -1.0)')
    source=replace_once(source,'    history = []\n','    history = [] if reused_history is None else reused_history\n')
    source=replace_once(source,'    for epoch in range(1, MAX_EPOCHS + 1):',
        '    if reused_history is not None:\n        chosen = max(history, key=lambda r: (r["minimum"], r["mean"]))\n        selected_epoch = chosen["epoch"]\n        print("REUSED_INNER_HISTORY", selected_epoch, flush=True)\n    for epoch in ([] if reused_history is not None else range(1, MAX_EPOCHS + 1)):')
    source=replace_once(source,'score = min(scores.values())','score = (min(scores.values()), float(np.mean(list(scores.values()))))')
    source=replace_once(source,'"minimum": score,','"minimum": score[0], "mean": score[1],')
    source=replace_once(source,'if score > best + 1e-9:','if score > best:')
    source=replace_once(source,'best_state = {name: value.detach().cpu().clone() for name, value in model.state_dict().items() if "lora_" in name}',
        'best_state = capture_adapter(model)')
    source=replace_once(source,'        if stale >= 2:\n            break\n    assert best_state',
        '        save_checkpoint("inner", epoch, model, optimizer, scaler, rng, history)\n    assert len(history) == MAX_EPOCHS')
    old='''    named_parameters = dict(model.named_parameters())
    assert set(initial_state).issubset(named_parameters)
    with torch.no_grad():
        for name, value in initial_state.items():
            parameter = named_parameters[name]
            parameter.copy_(value.to(device=parameter.device, dtype=parameter.dtype))'''
    source=replace_once(source,old,'    restore_adapter(model, initial_state)\n    seed_all(42000 + FOLD)')
    source=replace_once(source,'        print("refit", json.dumps(record), flush=True)',
        '        print("refit", json.dumps(record), flush=True)\n        save_checkpoint("refit", epoch, model, optimizer, scaler, rng, refit_history)')
    source=replace_once(source,'final_state = {name: value.detach().cpu().clone() for name, value in model.state_dict().items() if "lora_" in name}',
        'final_state = capture_adapter(model)')
    source=replace_once(source,'        "status": "complete", "smoke": SMOKE, "fold": FOLD,',
        '''        "status": "complete", "smoke": SMOKE, "fold": FOLD,
        "schema": "tempo-e14-fold-v1", "protocol_sha256": sha(Path("/kaggle/working/protocol.json")),
        "source_sha256": sha(Path(__file__)), "split_sha256": sha(OUT / "split.json"),
        "initial_adapter_sha256": sha(OUT / "initial_adapter_state.pt"),
        "adapter_sha256": sha(OUT / "adapter_state.pt"),
        "outer_train_samples": len(train), "reused_pilot_inner_history": reused_history is not None,
        "seconds": time.monotonic()-run_started,''')
    source=source.replace('if __name__ == "__main__":\n    main()',HELPERS+'\nif __name__ == "__main__":\n    main()')
    compile(source,'e14_worker.py','exec')
    worker_bytes=source.encode()
    (HERE/'worker.py').write_bytes(worker_bytes)
    worker_sha=sha(worker_bytes)
    for fold in range(1,6):
        directory=HERE/f'fold{fold}'
        directory.mkdir(exist_ok=True)
        launcher=f'''import base64, hashlib, os, subprocess, sys
from pathlib import Path
os.environ['HF_HOME']='/tmp/tempo_hf_cache'
os.environ['E07_SMOKE']='0'
os.environ['E07_FOLD']='{fold}'
os.environ['E14_PROTOCOL_SHA256']='{sha(protocol_bytes)}'
os.environ['E14_WORKER_SHA256']='{worker_sha}'
protocol=base64.b64decode({base64.b64encode(protocol_bytes).decode()!r})
worker=base64.b64decode({base64.b64encode(worker_bytes).decode()!r})
assert hashlib.sha256(protocol).hexdigest()==os.environ['E14_PROTOCOL_SHA256']
assert hashlib.sha256(worker).hexdigest()==os.environ['E14_WORKER_SHA256']
Path('/kaggle/working/protocol.json').write_bytes(protocol)
Path('/kaggle/working/folds.json').write_text(__import__('json').dumps(__import__('json').loads(protocol)['fold_mapping']))
Path('/kaggle/working/e14_worker.py').write_bytes(worker)
subprocess.run([sys.executable,'-m','pip','install','transformers==5.17.0','peft==0.21.2','bitsandbytes==0.50.2','accelerate==1.15.0'],check=True,timeout=900)
subprocess.run([sys.executable,'-u','/kaggle/working/e14_worker.py'],check=True,timeout=20700)
'''
        (directory/'launch.py').write_text(launcher)
        metadata={'id':f'yusepmuhamadzazuli/tempo-micro-e14-joint-qlora-fold{fold}',
                  'title':f'Tempo Micro E14 Joint QLoRA Fold{fold}','code_file':'launch.py',
                  'language':'python','kernel_type':'script','is_private':True,
                  'enable_gpu':True,'enable_internet':True,
                  'docker_image':'gcr.io/kaggle-private-byod/python@sha256:2757e0c7d1e0a9cb43da657b97e223c321a98f5014bdf64f44f2f6b083ad2b2f',
                  'machine_shape':'NvidiaTeslaT4',
                  'dataset_sources':['yusepmuhamadzazuli/tempo-benchmark-20261005'],
                  'kernel_sources':['yusepmuhamadzazuli/tempo-e01-vlm','yusepmuhamadzazuli/tempo-micro-e13-joint-qlora-inner-pilot'],
                  'competition_sources':[],'model_sources':[]}
        (directory/'kernel-metadata.json').write_text(json.dumps(metadata,indent=2)+'\n')
    manifest={'protocol_sha256':sha(protocol_bytes),'worker_sha256':worker_sha,
              'files':{str(p.relative_to(HERE)):sha(p.read_bytes()) for p in sorted(HERE.rglob('*')) if p.is_file() and p.name!='build_manifest.json' and '__pycache__' not in p.parts}}
    (HERE/'build_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({'status':'frozen','protocol_sha256':sha(protocol_bytes),'worker_sha256':worker_sha,'folds':5},indent=2))


if __name__=='__main__':
    main()
