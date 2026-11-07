#!/usr/bin/env python3
"""Freeze second OCR holdout before diagnosing/tuning on first holdout failures."""
import csv, hashlib, json
from collections import defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'03_data/DATASET_740_TASK2_DOMAIN.csv'
OLD=ROOT/'04_hasil_eksperimen/revisi_week3/ocr_manifest.json'
DEV=ROOT/'04_hasil_eksperimen/revisi_week3/ocr_independent/manifest_frozen.json'
FIRST=ROOT/'04_hasil_eksperimen/revisi_week3/ocr_final_holdout/manifest_frozen.json'
OUT=ROOT/'04_hasil_eksperimen/revisi_week3/ocr_second_holdout'
MANIFEST=OUT/'manifest_frozen.json';SHA=OUT/'manifest_frozen.sha256'
SEED='tempo-ocr-second-holdout-v1-2026-10-17';PER_CLASS=10
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def image(sid):
    for ext in('.jpg','.jpeg','.png','.webp'):
        p=ROOT/'05_gambar'/f'{sid}{ext}'
        if p.exists():return p
    raise FileNotFoundError(sid)
if MANIFEST.exists():raise SystemExit('Second holdout already frozen; refusing overwrite.')
rows=list(csv.DictReader(DATA.open(encoding='utf-8-sig')))
excluded={x['sample_id'] for x in json.loads(OLD.read_text())}
excluded|={x['sample_id'] for x in json.loads(DEV.read_text())['items']}
excluded|={x['sample_id'] for x in json.loads(FIRST.read_text())['items']}
groups=defaultdict(list)
for row in rows:
    if row['sample_id'] not in excluded:
        groups[row['task1_issue']].append((hashlib.sha256(f"{SEED}:{row['sample_id']}".encode()).hexdigest(),row))
available={k:len(v) for k,v in groups.items()}
included=sorted(k for k,v in groups.items() if len(v)>=PER_CLASS)
omitted=sorted(set(row['task1_issue'] for row in rows)-set(included))
items=[]
for task in included:
    for _,row in sorted(groups[task])[:PER_CLASS]:
        p=image(row['sample_id']);items.append({'sample_id':row['sample_id'],'task1_issue':task,
            'headline_truth':row['headline_verified'],'supporting_truth':row['supporting_text_verified'],
            'image':str(p.relative_to(ROOT)),'image_sha256':digest(p)})
items.sort(key=lambda x:x['sample_id'])
manifest={'schema':'tempo-ocr-second-holdout-v1','frozen_at':'2026-10-17','do_not_run_until_candidate_locked':True,
 'selection':{'seed':SEED,'rule':'exclude all prior 170 OCR IDs; SHA-256 rank within Task1; first 10 for classes with >=10 unseen samples',
              'per_included_class':PER_CLASS,'included_classes':included,'omitted_classes':omitted,
              'available_after_exclusion':dict(sorted(available.items())),'count':len(items),'excluded_ids':len(excluded)},
 'limitation':'other_issue has no unseen samples and is omitted; report overall and per-class metrics, and do not claim ten-class coverage.',
 'dataset_sha256':digest(DATA),'prior_manifest_sha256':{'old30':digest(OLD),'dev60':digest(DEV),'first80':digest(FIRST)},'items':items}
payload=(json.dumps(manifest,ensure_ascii=False,indent=2,sort_keys=True)+'\n').encode();OUT.mkdir(parents=True,exist_ok=True);MANIFEST.write_bytes(payload)
h=hashlib.sha256(payload).hexdigest();SHA.write_text(f'{h}  {MANIFEST.name}\n');print(json.dumps({'status':'frozen-not-run','count':len(items),'included':included,'omitted':omitted,'sha256':h},indent=2))
