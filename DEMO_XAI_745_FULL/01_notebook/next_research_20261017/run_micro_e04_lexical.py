#!/usr/bin/env python3
"""Micro-E04: nested lexical word/character TF-IDF multitask bundle."""
import csv,hashlib,json,re,time
from pathlib import Path
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import FeatureUnion,make_pipeline
from sklearn.svm import LinearSVC
from sklearn.metrics import f1_score
from sklearn.model_selection import StratifiedKFold

ROOT=Path(__file__).resolve().parents[3];P=ROOT/'DEMO_XAI_745_FULL';DATA=P/'03_data/DATASET_740_TASK2_DOMAIN.csv';FOLDS=P/'04_hasil_eksperimen/e42_tail_grid/oof.csv';OUT=P/'04_hasil_eksperimen/next_research_20261017/06_micro_f1/MICRO_E04_lexical';TASKS=('task1_issue','task2_domain_sumber','task3_primary_entity_type')
CFG=[('word',dict(kind='word',C=.5,balanced=False)),('word_bal',dict(kind='word',C=.5,balanced=True)),('char',dict(kind='char',C=1.,balanced=False)),('union',dict(kind='union',C=.5,balanced=False)),('union_bal',dict(kind='union',C=.5,balanced=True)),('union_c1',dict(kind='union',C=1.,balanced=False))]
def read(p):
 with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def make(cfg,seed):
 word=TfidfVectorizer(ngram_range=(1,2),min_df=2,max_features=25000,sublinear_tf=True,strip_accents='unicode')
 char=TfidfVectorizer(analyzer='char_wb',ngram_range=(3,5),min_df=2,max_features=40000,sublinear_tf=True)
 vec=word if cfg['kind']=='word' else char if cfg['kind']=='char' else FeatureUnion([('word',word),('char',char)])
 return make_pipeline(vec,LinearSVC(C=cfg['C'],class_weight='balanced' if cfg['balanced'] else None,random_state=seed))
def main():
 start=time.time();OUT.mkdir(parents=True,exist_ok=True);rows,fr=read(DATA),read(FOLDS);ids=[r['sample_id'] for r in rows];assert ids==[r['sample_id'] for r in fr];text=np.array([(r['headline_verified']+' [SEP] '+r['supporting_text_verified']).strip() for r in rows]);folds=np.array([int(r['fold']) for r in fr]);labels={t:sorted({r[t] for r in rows}) for t in TASKS};y={t:np.array([{z:i for i,z in enumerate(labels[t])}[r[t]] for r in rows]) for t in TASKS};oof={t:np.full(740,-1) for t in TASKS};details=[]
 for fold in range(1,6):
  tr,te=np.where(folds!=fold)[0],np.where(folds==fold)[0];info={'fold':fold,'tasks':{}}
  for ti,t in enumerate(TASKS):
   splits=list(StratifiedKFold(3,shuffle=True,random_state=91000+fold*10+ti).split(tr,y[t][tr]));opts=[]
   for ci,(name,cfg) in enumerate(CFG):
    vals=[]
    for si,(a,b) in enumerate(splits):
     a,b=tr[a],tr[b];m=make(cfg,92000+fold*1000+ti*100+ci*10+si);m.fit(text[a],y[t][a]);vals.append(f1_score(y[t][b],m.predict(text[b]),average='micro'))
    opts.append({'candidate':name,'config':cfg,'inner_micro_f1':float(np.mean(vals))})
   chosen=max(opts,key=lambda z:z['inner_micro_f1']);m=make(chosen['config'],93000+fold*10+ti);m.fit(text[tr],y[t][tr]);oof[t][te]=m.predict(text[te]);info['tasks'][t]={'selected':chosen,'outer_micro_f1':float(f1_score(y[t][te],oof[t][te],average='micro'))};print(fold,t,info['tasks'][t],flush=True)
  details.append(info)
 fields=['sample_id','fold']+[z for t in TASKS for z in (t+'_truth',t+'_pred')]
 with (OUT/'predictions.csv').open('w',newline='') as h:
  w=csv.DictWriter(h,fieldnames=fields);w.writeheader()
  for i,sid in enumerate(ids):
   d={'sample_id':sid,'fold':int(folds[i])}
   for t in TASKS:d[t+'_truth']=labels[t][y[t][i]];d[t+'_pred']=labels[t][int(oof[t][i])]
   w.writerow(d)
 micro={t:float(f1_score(y[t],oof[t],average='micro')) for t in TASKS};macro={t:float(f1_score(y[t],oof[t],average='macro')) for t in TASKS};result={'schema':'tempo-micro-e04-v1','status':'complete','model_contract':'one lexical feature pipeline with three task heads','input':'headline_verified [SEP] supporting_text_verified','micro_f1':micro,'macro_f1_diagnostic':macro,'minimum_micro_f1':min(micro.values()),'all_tasks_at_least_0_70':min(micro.values())>=.7,'fold_details':details,'dataset_sha256':sha(DATA),'seconds':time.time()-start,'predictions_sha256':sha(OUT/'predictions.csv')};(OUT/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
