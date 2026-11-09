"""Derive a separate all-data deployment refit; never edit frozen CV workers."""
import ast
import base64
import hashlib
import json
from pathlib import Path
import statistics

HERE = Path(__file__).resolve().parent
APP = HERE.parents[2]
REPO = APP.parent
SOURCE = HERE.parent / 'kaggle_micro_e14/worker.py'
OOF = APP / '04_hasil_eksperimen/next_research_20261017/06_micro_f1/MICRO_E14_joint_qlora_oof'
PACKAGE = APP / '06_models/micro-e14-qlora-v1'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')


def once(source, old, new):
    assert source.count(old) == 1, old[:100]
    return source.replace(old, new)


def main():
    assert sha(SOURCE) == 'cb09acda21117f0acba38233fca382ec9916b08c5c73f297fa0f70c9469003ed'
    assert sha(OOF / 'frozen_protocol.json') == '7b1eb1fdaf8547e842df793726e106b1d29b222b16ef3d9b672388d9d46ec65e'
    results = [json.loads((OOF / f'fold{i}/result.json').read_text()) for i in range(1, 6)]
    # Only inner-selected epochs; no optimization on outer-test predictions.
    epochs = int(statistics.median(r['selected_epoch'] for r in results))
    assert epochs == 3
    original = SOURCE.read_text()
    definitions = next(ast.literal_eval(n.value) for n in ast.parse(original).body
                       if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'DEFINITIONS' for t in n.targets))
    protocol = dict(schema='tempo-micro-e14-deployment-v1', version='micro-e14-qlora-v1',
                    backend='micro-e14-qlora', model='Qwen/Qwen3-VL-8B-Instruct',
                    revision='0c351dd01ed87e9c1b53cbc748cba10e6187ff3b',
                    cv_worker_sha256=sha(SOURCE), cv_protocol_sha256=sha(OOF/'frozen_protocol.json'),
                    dataset_sha256='cba20f8250bcb59481ed2d3d7d5d42fb8242c96a7ba2d11a2cd02ad80862961a',
                    train_samples=740, epochs=epochs, seed_initial=43, seed_refit=42001,
                    epoch_rule='median of five inner-validation-selected epochs; no outer-score selection',
                    inner_selected_epochs=[r['selected_epoch'] for r in results],
                    evaluation='Not Evaluated: all-data deployment refit is not an OOF model',
                    definitions=definitions,
                    sources={f'fold{i}/result.json': sha(OOF/f'fold{i}/result.json') for i in range(1, 6)})
    write(HERE/'deployment_protocol.json', protocol)
    source = once(original, 'OUT = Path(f"/kaggle/working/e14_fold{FOLD}")', 'OUT = Path("/kaggle/working/e14_deploy")')
    start = source.index('    task1 = truth["task1_issue"]')
    end = source.index('    assert torch.cuda.is_available()', start)
    source = source[:start] + '    train = np.arange(len(frame))\n    test = np.array([0], dtype=int)\n    validation = np.array([], dtype=int)\n' + source[end:]
    source = once(source, '    reused_history = prepare_reuse(frame, inner, validation, train, test, audits, model)\n', '')
    start = source.index('    seed_all(42 + FOLD)\n    optimizer = ')
    end = source.index('    refit_history = []', start)
    source = source[:start] + '''    selected_epoch = 3
    seed_all(42001)
    optimizer = torch.optim.AdamW(trainable, lr=1e-4, weight_decay=0.01)
    scaler = torch.amp.GradScaler("cuda", init_scale=128)
    criterion = nn.CrossEntropyLoss()
    rng = np.random.default_rng(42001)
''' + source[end:]
    start = source.index('    final_state = capture_adapter(model)')
    end = source.index('\n\n\ndef capture_adapter', start)
    source = source[:start] + '''    # In-sample smoke only: confirms persistence/reload, NOT accuracy.
    from peft import PeftModel
    before = predict(test)
    model.save_pretrained(OUT / "adapter", safe_serialization=True)
    del optimizer, scaler, model, base, trainable, initial_state
    gc.collect()
    torch.cuda.empty_cache()
    base = AutoModelForImageTextToText.from_pretrained(MODEL, revision=REVISION, quantization_config=quant, dtype=torch.float16, device_map={"": 0}, attn_implementation="sdpa")
    base = prepare_model_for_kbit_training(base, use_gradient_checkpointing=False)
    model = PeftModel.from_pretrained(base, OUT / "adapter", is_trainable=False)
    after = predict(test)
    differences = {task: float(np.max(np.abs(before[task] - after[task]))) for task in TASKS}
    assert all(value <= 1e-4 for value in differences.values()), differences
    artifact_hashes = {str(p.relative_to(OUT)): sha(p) for p in sorted((OUT / "adapter").iterdir()) if p.is_file()}
    result = dict(schema="tempo-micro-e14-deployment-result-v1", status="complete", version="micro-e14-qlora-v1",
        train_samples=len(train), epochs=selected_epoch, refit_history=refit_history,
        seconds=time.monotonic()-run_started, data_sha256=sha(csv_path),
        protocol_sha256=sha(Path("/kaggle/working/deployment_protocol.json")), source_sha256=sha(Path(__file__)),
        input_audit_sha256=sha(OUT / "input_audit.jsonl"),
        artifacts=artifact_hashes, classes=classes, deployment_benchmark="Not Evaluated",
        smoke=dict(kind="in-sample persistence/reload parity only, NOT benchmark", samples=len(test),
                   max_probability_difference=differences, probabilities={t: after[t].tolist() for t in TASKS}),
        gpu_name=torch.cuda.get_device_name(0), peak_cuda_allocated_bytes=torch.cuda.max_memory_allocated(0))
    (OUT / "result.json").write_text(json.dumps(result, indent=2) + "\\n")
    print("DEPLOYMENT_COMPLETE", json.dumps(result), flush=True)
''' + source[end:]
    # No CV split helpers are called; remove unused CV-only helpers entirely.
    start = source.index('\ndef prepare_reuse(')
    source = source[:start] + '\nif __name__ == "__main__":\n    main()\n'
    source = source.replace('sha(Path("/kaggle/working/protocol.json"))', 'sha(Path("/kaggle/working/deployment_protocol.json"))')
    source = once(source, '"fold": FOLD}', '"deployment": True}')
    compile(source, 'deployment_worker.py', 'exec')
    (HERE/'deployment_worker.py').write_text(source)
    # Reuse the exact pinned dependency installer/container used by CV.
    launch_original = (HERE.parent/'kaggle_micro_e14/fold5/launch.py').read_text()
    pip_line = next(line for line in launch_original.splitlines() if "'-m','pip'" in line)
    launch = 'import base64, hashlib, os, subprocess, sys\nfrom pathlib import Path\n'
    launch += "os.environ['E07_SMOKE']='0'\nos.environ['E07_FOLD']='1'\n"
    for name in ('deployment_protocol.json', 'deployment_worker.py'):
        data = (HERE/name).read_bytes()
        launch += f"data=base64.b64decode({base64.b64encode(data).decode()!r})\nassert hashlib.sha256(data).hexdigest()=={hashlib.sha256(data).hexdigest()!r}\nPath('/kaggle/working/{name}').write_bytes(data)\n"
    launch += pip_line + '\n'
    launch += "subprocess.run([sys.executable,'-u','/kaggle/working/deployment_worker.py'],check=True,timeout=20700)\n"
    (HERE/'launch.py').write_text(launch)
    metadata = json.loads((HERE.parent/'kaggle_micro_e14/fold5/kernel-metadata.json').read_text())
    metadata.update(id='research-account/tempo-micro-e14-deployment-refit', title='Tempo Micro E14 Deployment Refit')
    metadata['kernel_sources'] = ['research-account/tempo-e01-vlm']
    write(HERE/'kernel-metadata.json', metadata)
    PACKAGE.mkdir(parents=True, exist_ok=True)
    write(PACKAGE/'contract.json', protocol)
    e01 = REPO/'docs/server-recovery/2026-10-10/e01-full-terbaru/e01_vlm'
    assert sha(e01/'deskripsi.jsonl') == 'c75e8df3f9b71d6786462f8d0f1187ebe4234fb8dd079924f3f35707ff1b8cd2'
    assert sha(e01/'zeroshot.jsonl') == '10c07b06b13fbbf647f2b1ed12a722d9bff8f97caa6b621430d8bc0429ab38c9'
    descriptions = {r['sample_id']:r for r in map(json.loads, (e01/'deskripsi.jsonl').read_text().splitlines())}
    reasons = {r['sample_id']:r for r in map(json.loads, (e01/'zeroshot.jsonl').read_text().splitlines())}
    assert len(descriptions) == len(reasons) == 740 and descriptions.keys() == reasons.keys()
    write(PACKAGE/'visual_context.json', {k:dict(deskripsi=descriptions[k]['deskripsi'], sumber_visual=reasons[k].get('sumber_visual') or '', alasan=reasons[k].get('alasan') or '') for k in descriptions})
    write(PACKAGE/'assets_manifest.json', dict(files={name:sha(PACKAGE/name) for name in ('contract.json','visual_context.json')},
          visual_context_sources={name:sha(e01/name) for name in ('deskripsi.jsonl','zeroshot.jsonl')}))
    files = ['deployment_protocol.json', 'deployment_worker.py', 'launch.py', 'kernel-metadata.json']
    write(HERE/'build_manifest.json', dict(files={name:sha(HERE/name) for name in files}, package_files={name:sha(PACKAGE/name) for name in ('contract.json','visual_context.json')}))
    print(json.dumps(dict(epochs=epochs, train_samples=740, kernel=metadata['id'], files=files)))


if __name__ == '__main__':
    main()
