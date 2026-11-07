"""Label-blind, pinned IndoBERT extraction for headline and rich text controls.

Only explicit input fields reach the encoder. Gold is not used for extraction.
Saved h10 inputs allow later E42-family training without re-encoding documents.
"""
import argparse
import json
from pathlib import Path
import time
import numpy as np
import pandas as pd
import torch
from transformers import AutoTokenizer,AutoModel
from huggingface_hub import snapshot_download
from evaluate import sha,write_json


def main(workspace):
    repo=Path(workspace).resolve();app=repo/'DEMO_XAI_745_FULL'
    out=app/'04_hasil_eksperimen/revisi_ii/text_inputs';out.mkdir(parents=True,exist_ok=True)
    if (out/'manifest.json').exists():
        manifest=json.loads((out/'manifest.json').read_text())
        for name,digest in manifest['files'].items():assert sha(out/name)==digest
        print('Preserved completed label-blind text extraction');return
    started=time.monotonic();torch.set_num_threads(2)
    csv=app/'03_data/DATASET_740_TASK2_DOMAIN.csv'
    frame=pd.read_csv(csv,usecols=['sample_id','headline_verified','supporting_text_verified']).fillna('')
    source=repo/'docs/server-recovery/2026-10-10/e01-full-terbaru/e01_vlm'
    desc={r['sample_id']:r['deskripsi'] for r in map(json.loads,(source/'deskripsi.jsonl').read_text().splitlines())}
    zero={r['sample_id']:{k:r.get(k) or '' for k in ['sumber_visual','alasan']} for r in map(json.loads,(source/'zeroshot.jsonl').read_text().splitlines())}
    items=[]
    for r in frame.itertuples():
        items.append(dict(sample_id=r.sample_id,headline=r.headline_verified,
                    supporting=r.supporting_text_verified,description=desc[r.sample_id][:1000],
                    source_visual=zero[r.sample_id]['sumber_visual'][:250],reason=zero[r.sample_id]['alasan'][:500]))
    (out/'label_blind_inputs.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in items))
    model_meta=json.loads((app/'04_hasil_eksperimen/e37_token_pool/features_manifest.json').read_text())
    revision=model_meta['model_snapshot']
    snap=Path(snapshot_download('indobenchmark/indobert-base-p1',revision=revision,local_files_only=True))
    for name,digest in model_meta['model_hashes'].items():assert sha(snap/name)==digest
    tokenizer=AutoTokenizer.from_pretrained(snap,local_files_only=True)
    model=AutoModel.from_pretrained(snap,local_files_only=True).eval()
    for p in model.parameters():p.requires_grad=False
    model.config._attn_implementation='sdpa'
    visual=np.load(app/'04_hasil_eksperimen/e41_cached_tail/cache/front_cache.npz')['visual']
    reports=[]
    for variant in ['headline','rich']:
        texts=[r['headline'] if variant=='headline' else
               f"{r['headline']} [SEP] {r['supporting']} [SEP] Deskripsi visual: {r['description']}. Observasi sumber visual: {r['source_visual']}. Alasan visual: {r['reason']}." for r in items]
        hidden=[];masks=[];pools=[];mean=[];cls=[];lengths=[]
        for off in range(0,len(texts),8):
            segment=texts[off:off+8]
            lengths.extend([len(tokenizer.encode(t,add_special_tokens=True,truncation=False)) for t in segment])
            enc=tokenizer(segment,return_tensors='pt',truncation=True,max_length=128,padding='max_length')
            mask=enc['attention_mask'].bool();pool=mask.clone()
            for special in tokenizer.all_special_ids:pool &= enc['input_ids']!=special
            assert pool.any(dim=1).all()
            with torch.inference_mode():
                value=model(**enc,output_hidden_states=True);h10=value.hidden_states[10].clone();h10[~mask]=0
                hidden.append(h10.numpy());masks.append(mask.numpy().astype('uint8'));pools.append(pool.numpy().astype('uint8'))
                v=(value.last_hidden_state*pool.unsqueeze(-1)).sum(1)/pool.sum(1,keepdim=True)
                mean.append(torch.nn.functional.normalize(v.float(),p=2,dim=1).numpy())
                cls.append(torch.nn.functional.normalize(value.last_hidden_state[:,0,:].float(),p=2,dim=1).numpy())
            if off%96==0:print(variant,min(off+8,740),'seconds',round(time.monotonic()-started,1),flush=True)
        path=out/f'{variant}_front_cache.npz'
        np.savez_compressed(path,sample_ids=frame.sample_id.to_numpy(dtype=str),h10=np.concatenate(hidden),attention=np.vstack(masks),
                            pool_mask=np.vstack(pools),base_mean=np.vstack(mean),cls=np.vstack(cls),visual=visual)
        reports.append(dict(variant=variant,samples=740,max_length=128,truncated_samples=sum(n>128 for n in lengths),
                            original_tokens_min=min(lengths),original_tokens_max=max(lengths),sha256=sha(path)))
    write_json(out/'manifest.json',dict(schema='revisi-ii-text-inputs-v1',status='complete',model='indobenchmark/indobert-base-p1',revision=revision,
        model_hashes=model_meta['model_hashes'],source_sha256=sha(__file__),input_fields=['sample_id','headline_verified','supporting_text_verified','deskripsi','sumber_visual','alasan'],
        prohibited_fields=['task1_issue','task2_domain_sumber','task3_primary_entity_type','domain','task2_source_description','task2_mapping_note'],
        label_csv_columns_read=['sample_id','headline_verified','supporting_text_verified'],dataset_sha256=sha(csv),
        e01_hashes={name:sha(source/name) for name in ['deskripsi.jsonl','zeroshot.jsonl']},variants=reports,
        files={p.name:sha(p) for p in out.iterdir() if p.is_file()},seconds=time.monotonic()-started))
    print('TEXT EXTRACTION COMPLETE',round(time.monotonic()-started,1),flush=True)


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--workspace',required=True,type=Path);main(ap.parse_args().workspace)
