#!/usr/bin/env python3
"""Validate and freeze the user's decisions for the 20 OCR failures."""
import csv, hashlib, json, re, unicodedata
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT.parent/'docs/OCR_LABEL_VALIDATION_20.csv'
RESULT=ROOT/'04_hasil_eksperimen/revisi_week3/ocr_final_holdout/results.json'
OUT=ROOT/'04_hasil_eksperimen/revisi_week3/ocr_final_holdout/human_validation.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def norm(s):
 s=unicodedata.normalize('NFKC',s or '').upper();return re.sub(r'\s+',' ',re.sub(r'[^0-9A-ZÀ-ÖØ-Ý\s]',' ',s)).strip()
if OUT.exists():raise SystemExit('Human validation already frozen; refusing overwrite.')
rows=list(csv.DictReader(SOURCE.open(encoding='utf-8-sig')));result=json.loads(RESULT.read_text());failed={x['sample_id']:x for x in result['results'] if not x['exact']}
assert len(rows)==len(failed)==20 and {x['sample_id'] for x in rows}==set(failed)
allowed={'valid','invalid','ambiguous'}
for x in rows:
 x['decision_valid_invalid_ambiguous']=x['decision_valid_invalid_ambiguous'].strip().lower();assert x['decision_valid_invalid_ambiguous'] in allowed
 assert x['correct_headline_if_needed'].strip()
 assert norm(x['correct_headline_if_needed'])==norm(failed[x['sample_id']]['headline_truth']),x['sample_id']
counts=Counter(x['decision_valid_invalid_ambiguous'] for x in rows);human_accepted=result['exact_correct']+counts['valid']
payload={'schema':'tempo-ocr-human-validation-v1','recorded_at':'2026-10-17','source_csv_sha256':sha(SOURCE),'ocr_result_sha256':sha(RESULT),
 'exact_match':{'correct':result['exact_correct'],'count':result['count'],'accuracy':result['exact_accuracy']},
 'review_counts':dict(sorted(counts.items())),'human_accepted_usability':{'correct':human_accepted,'count':result['count'],'accuracy':human_accepted/result['count']},
 'caveat':'Human-accepted usability is separate from exact match; ambiguous cases are not counted accepted and the exact-match gate remains failed.',
 'ground_truth_change_required':False,'items':rows}
OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2,sort_keys=True)+'\n');print(json.dumps({k:payload[k] for k in ('review_counts','human_accepted_usability','ground_truth_change_required')},indent=2))
