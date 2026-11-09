"""Freeze CI-D01 payload; prior cache/CV sources are never modified."""
import csv
import hashlib
import json
from pathlib import Path
import shutil

HERE=Path(__file__).resolve().parent
APP=HERE.parents[2]
CACHE=APP/'04_hasil_eksperimen/e41_cached_tail/cache'
OUT=APP/'04_hasil_eksperimen/next_research_20261017/08_ci_d01_duplicate2x'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def write(path,obj):Path(path).write_text(json.dumps(obj,indent=2)+'\n')


def main():
    manifest=json.loads((CACHE/'cache_manifest.json').read_text())
    assert sha(CACHE/'cache_manifest.json')=='9773684278f995f2d2da4f4c12158568077372270157ca85a0a99a2427829040'
    for name,digest in manifest['files'].items():assert sha(CACHE/name)==digest,name
    with (APP/'04_hasil_eksperimen/e42_tail_grid/oof.csv').open() as handle:rows=list(csv.DictReader(handle))
    mapping={r['sample_id']:int(r['fold']) for r in rows}
    assert len(mapping)==740 and all(list(mapping.values()).count(k)==148 for k in range(1,6))
    config=dict(hidden=256,dropout=.3,visual_weight=2.,loss_weights=[1.,2.,2.],encoder_lr=2e-5,
                head_lr=3e-4,weight_decay=.01,batch=32,epoch_candidates=[0,2,4,8,12,24],seed=42)
    protocol=dict(schema='tempo-ci-d01-protocol-v1',date='2026-10-20',experiment='CI_D01_CLIP_INDoBERT_DUP2',
        architecture='frozen CLIP-L14 full/crop + frozen IndoBERT front + two trainable IndoBERT blocks + shared three-task head',
        qwen_used=False,unique_original_samples=740,duplication_factors=[1,2],
        intervention='exact np.tile copies only AFTER ID-based split; joint tail/head minibatch phase',
        warm_head='120 full-batch warmup steps on UNIQUE training IDs; identical weights reused across both arms',
        class_weights='computed from unique training IDs only',
        inner='Task2 stratified 2-fold seed123; maximize minimum across tasks of mean inner Macro-F1; exact tie earliest epoch',
        epoch_selection='independent per arm on inner validation only; NO outer-test selection',
        comparison='paired same recipe, seeds and outer IDs; not optimizer-step matched',
        canonical_evaluation='CPU FP32 reloaded saved checkpoint; GPU AMP diagnostic only',
        threshold={'metric':'macro_f1','all_tasks_at_least':.70},config=config,
        wall_seconds_limit=7200,
        dataset_sha256=manifest['files']['DATASET_740_TASK2_DOMAIN.csv'],
        cache_manifest_sha256=sha(CACHE/'cache_manifest.json'),cache_sha256=manifest['files']['front_cache.npz'],
        cache_origin='E41 audited label-free frozen-front extraction; verified headline/supporting only',
        fold_source_sha256=sha(APP/'04_hasil_eksperimen/e42_tail_grid/oof.csv'),fold_mapping=mapping,
        limitations=['no new information from copies','not class balancing','same-epoch extra optimizer updates',
                     'repeated internal CV on existing corpus; no external test','not a deployment checkpoint or web update'])
    frozen=HERE/'frozen_protocol.json'
    if frozen.exists():assert json.loads(frozen.read_text())==protocol,'Frozen protocol differs; use a NEW experiment'
    else:write(frozen,protocol)
    # Byte-identical original model implementation; only worker sampling changes.
    original=APP/'01_notebook/e42_tail_grid/tail_model.py'
    shutil.copyfile(original,HERE/'tail_model.py')
    payload={name:sha(HERE/name) for name in ('worker.py','tail_model.py','protocol_utils.py','frozen_protocol.json')}
    build_manifest=dict(payload=payload,model_origin_sha256=sha(original),kernel_files={})
    metadata=json.loads((APP/'01_notebook/e42_tail_grid/full/kernel-metadata.json').read_text())
    metadata['docker_image']='gcr.io/kaggle-private-byod/python@sha256:2757e0c7d1e0a9cb43da657b97e223c321a98f5014bdf64f44f2f6b083ad2b2f'
    for mode in ('smoke','full'):
        folder=HERE/mode;folder.mkdir(exist_ok=True)
        launch="import os,sys,subprocess,hashlib,json\nfrom pathlib import Path\nos.environ['HF_HUB_OFFLINE']='1'\nos.environ['TOKENIZERS_PARALLELISM']='false'\n"
        launch+=f"os.environ['CI_D01_SMOKE']={'1' if mode=='smoke' else '0'!r}\n"
        launch+="wheel=next(Path('/kaggle/input').rglob('transformers-5.17.0-*.whl'))\nsubprocess.run([sys.executable,'-m','pip','install','--no-index','--find-links',str(wheel.parent),'transformers==5.17.0'],check=True)\n"
        for name,digest in payload.items():
            source=(HERE/name).read_text()
            launch+=f"data={source!r}\nassert hashlib.sha256(data.encode()).hexdigest()=={digest!r}\nPath('/kaggle/working/{name}').write_text(data)\n"
        launch+=f"Path('/kaggle/working/build_manifest.json').write_text({json.dumps({'payload':payload})!r})\n"
        launch+="subprocess.run([sys.executable,'-u','/kaggle/working/worker.py'],check=True,timeout=7500)\n"
        (folder/'launch.py').write_text(launch)
        info=dict(metadata,id=f'research-account/tempo-ci-d01-clip-indobert-dup2-{mode}',
                  title=f'Tempo CI D01 CLIP IndoBERT Dup2 {mode.title()}')
        write(folder/'kernel-metadata.json',info)
        for name in ('launch.py','kernel-metadata.json'):
            build_manifest['kernel_files'][f'{mode}/{name}']=sha(folder/name)
        compile(launch,str(folder/'launch.py'),'exec')
    write(HERE/'build_manifest.json',build_manifest)
    OUT.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(frozen,OUT/'frozen_protocol.json')
    print(json.dumps(dict(status='frozen',experiment=protocol['experiment'],payload=payload)))


if __name__=='__main__':main()
