"""Generate an auditable, self-contained inner-only QLoRA Kaggle pilot."""
import base64
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / 'kaggle_micro_e07/worker.py'


def replace_once(source, old, new):
    assert source.count(old) == 1, old[:100]
    return source.replace(old, new)


def main():
    source = SOURCE.read_text()
    source = replace_once(source, 'def main():\n', 'def main():\n    seed_all(43)\n    pilot_started = time.monotonic()\n')
    source = replace_once(source, 'MAX_EPOCHS = 2 if SMOKE else 12', 'MAX_EPOCHS = 6\nPILOT_BUDGET_SECONDS = 5.5 * 3600')
    source = replace_once(source, 'OUT.mkdir(exist_ok=True)', 'OUT = Path("/kaggle/working/e13_inner_pilot")\nOUT.mkdir(exist_ok=True)')
    source = replace_once(source, 'required = sorted(set(train) | set(test) | set(validation))',
                          'required = sorted(set(inner) | set(validation))\n    assert not set(required) & set(test)')
    source = replace_once(source, 'initial_state = {name: value.detach().cpu().clone() for name, value in model.state_dict().items() if "lora_" in name}',
                          'initial_state = {name: value.detach().cpu().clone() for name, value in model.named_parameters() if value.requires_grad}\n    torch.save(initial_state, OUT / "initial_adapter_state.pt")')
    source = replace_once(source, 'best = -1.0', 'best = (-1.0, -1.0)\n    best_probabilities = None')
    source = replace_once(source, 'score = min(scores.values())', 'score = (min(scores.values()), float(np.mean(list(scores.values()))))')
    source = replace_once(source, '"minimum": score,', '"minimum": score[0], "mean": score[1],')
    source = replace_once(source, 'if score > best + 1e-9:', 'if score > best:')
    source = replace_once(source,
        'best_state = {name: value.detach().cpu().clone() for name, value in model.state_dict().items() if "lora_" in name}',
        'best_state = {name: value.detach().cpu().clone() for name, value in model.named_parameters() if value.requires_grad}\n            best_probabilities = probabilities\n            torch.save(best_state, OUT / "best_adapter_state.pt")')
    source = replace_once(source, 'if stale >= 2:',
        '''write_pilot_status(OUT, frame, truth, classes, inner, validation, test,
                           selected_epoch, best_probabilities, history, "running", pilot_started)
        if stale >= 3 or time.monotonic() - pilot_started >= PILOT_BUDGET_SECONDS:''')
    cut = source.index('    assert best_state\n')
    source = source[:cut] + '''    assert best_state and best_probabilities is not None
    write_pilot_status(OUT, frame, truth, classes, inner, validation, test,
                       selected_epoch, best_probabilities, history, "complete", pilot_started)
    print("COMPLETE_INNER_PILOT", json.dumps(history), flush=True)


def write_pilot_status(out, frame, truth, classes, inner, validation, outer_test,
                       selected_epoch, probabilities, history, status, started):
    predictions = pd.DataFrame({"sample_id": frame.sample_id.iloc[validation].to_numpy(),
                                "index": validation, "fold": FOLD})
    metrics, macro = {}, {}
    for task in TASKS:
        predicted = probabilities[task].argmax(1)
        predictions[task + "_truth"] = np.asarray(classes[task])[truth[task][validation]]
        predictions[task + "_pred"] = np.asarray(classes[task])[predicted]
        for ci, label in enumerate(classes[task]):
            predictions[f"{task}_p_{label}"] = probabilities[task][:, ci]
        metrics[task] = float(f1_score(truth[task][validation], predicted, average="micro"))
        macro[task] = float(f1_score(truth[task][validation], predicted, average="macro"))
    predictions.to_csv(out / "validation_predictions.csv", index=False)
    record = {"schema": "tempo-micro-e13-inner-pilot-v1", "status": status,
              "eligible_as_oof": False, "outer_test_evaluated": False,
              "model_contract": "one Qwen3-VL shared LoRA adapter with three prompted objectives",
              "model": MODEL, "revision": REVISION,
              "inner_train_samples": len(inner), "inner_validation_samples": len(validation),
              "selected_epoch": selected_epoch, "validation_micro_f1": metrics,
              "minimum_validation_micro_f1": min(metrics.values()),
              "validation_macro_f1": macro, "history": history,
              "split": {"inner_train_ids": frame.sample_id.iloc[inner].tolist(),
                        "inner_validation_ids": frame.sample_id.iloc[validation].tolist(),
                        "untouched_outer_test_ids": frame.sample_id.iloc[outer_test].tolist()},
              "seconds": time.monotonic()-started,
              "source_sha256": sha(Path(__file__)),
              "predictions_sha256": sha(out / "validation_predictions.csv")}
    (out / "result.json").write_text(json.dumps(record, indent=2) + "\\n")


if __name__ == "__main__":
    main()
'''
    compile(source, 'e13_worker.py', 'exec')
    (HERE/'worker.py').write_text(source)
    encoded = base64.b64encode(source.encode()).decode()
    launcher = '''import base64
import os
from pathlib import Path
import subprocess
import sys

# /tmp prevents model download caches being exported as multi-GB job output.
os.environ['HF_HOME'] = '/tmp/tempo_hf_cache'
os.environ['E07_SMOKE'] = '0'
os.environ['E07_FOLD'] = '1'
subprocess.run([sys.executable, '-m', 'pip', 'install', 'transformers==5.17.0',
                'peft==0.21.2', 'bitsandbytes==0.50.2', 'accelerate==1.15.0'], check=True, timeout=900)
worker = base64.b64decode(ENCODED_WORKER)
Path('/kaggle/working/e13_worker.py').write_bytes(worker)
subprocess.run([sys.executable, '-u', '/kaggle/working/e13_worker.py'], check=True, timeout=21000)
'''.replace('ENCODED_WORKER', repr(encoded))
    # Override the worker's original cache path as well.
    source = source.replace('os.environ["HF_HOME"] = "/kaggle/working/.cache/huggingface"',
                            'os.environ["HF_HOME"] = "/tmp/tempo_hf_cache"')
    (HERE/'worker.py').write_text(source)
    launcher = launcher.replace(repr(encoded), repr(base64.b64encode(source.encode()).decode()))
    (HERE/'launch.py').write_text(launcher)
    print(json.dumps({'worker_sha256':hashlib.sha256(source.encode()).hexdigest(),
                      'parent_worker_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
                      'max_epochs':6, 'outer_test_evaluated':False}, indent=2))


if __name__ == '__main__':
    main()
