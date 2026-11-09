#!/usr/bin/env python3
"""Create deterministic, label-blind augmentation QA examples and manifest."""
from __future__ import annotations
import hashlib, io, json, random
from pathlib import Path
import numpy as np
import pandas as pd
from PIL import Image, ImageEnhance

ROOT=Path(__file__).resolve().parents[3];P=ROOT/'DEMO_XAI_745_FULL';DATA=P/'03_data/DATASET_740_TASK2_DOMAIN.csv';IMAGES=P/'05_gambar';OUT=P/'04_hasil_eksperimen/next_research_20261017/02_augmentation';EX=OUT/'augmentation_examples'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rng_for(sid,variant):return random.Random(int(hashlib.sha256(f'{sid}:{variant}:20261018'.encode()).hexdigest()[:16],16))
def apply(im,variant,r):
 im=im.convert('RGB')
 if variant=='A01_light':
  im=ImageEnhance.Brightness(im).enhance(r.uniform(.92,1.08));im=ImageEnhance.Contrast(im).enhance(r.uniform(.92,1.08));quality=r.randint(88,96)
 else:
  im=ImageEnhance.Brightness(im).enhance(r.uniform(.85,1.15));im=ImageEnhance.Contrast(im).enhance(r.uniform(.85,1.15));im=im.rotate(r.uniform(-2,2),resample=Image.Resampling.BICUBIC,expand=False,fillcolor=(255,255,255));quality=r.randint(78,90)
 buf=io.BytesIO();im.save(buf,'JPEG',quality=quality);buf.seek(0);im=Image.open(buf).convert('RGB')
 arr=np.asarray(im).astype(np.int16);noise=np.random.default_rng(r.randrange(2**32)).normal(0,1.5 if variant=='A01_light' else 3.0,arr.shape);return Image.fromarray(np.clip(arr+noise,0,255).astype(np.uint8))
def main():
 OUT.mkdir(parents=True,exist_ok=True);EX.mkdir(exist_ok=True);df=pd.read_csv(DATA,encoding='utf-8-sig');selected=df.sort_values('sample_id').groupby('task2_domain_sumber',sort=True).head(1);rows=[]
 for row in selected.itertuples():
  src=IMAGES/f'{row.sample_id}.jpg'
  with Image.open(src) as im:
   for variant in ('A01_light','A02_moderate'):
    dst=EX/f'{row.sample_id}_{variant}.jpg';apply(im,variant,rng_for(row.sample_id,variant)).save(dst,'JPEG',quality=95)
    rows.append({'sample_id':row.sample_id,'task2_class':row.task2_domain_sumber,'variant':variant,'source_sha256':sha(src),'output_sha256':sha(dst)})
 (OUT/'augmentation_examples_manifest.json').write_text(json.dumps({'schema':'tempo-augmentation-qa-v1','seed':20261018,'selection':'lexicographically first sample per Task2 class; labels used only for QA coverage, never transform parameters','examples':rows},indent=2)+'\n')
 print(json.dumps({'samples':len(selected),'outputs':len(rows),'classes':sorted(selected.task2_domain_sumber.unique())},indent=2))
if __name__=='__main__':main()
