#!/usr/bin/env python3
"""Render the model-comparison and per-class figures required by Sprint 1."""
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.metrics import precision_recall_fscore_support

ROOT=Path(__file__).resolve().parents[3];B=ROOT/'DEMO_XAI_745_FULL/04_hasil_eksperimen/next_research_20261017';OUT=B/'01_model_comparison';TASKS=('task1_issue','task2_domain_sumber','task3_primary_entity_type')
def main():
 df=pd.read_csv(OUT/'model_comparison.csv');x=range(len(df));fig,ax=plt.subplots(figsize=(10,5))
 for i,(col,label) in enumerate((('task1_macro_f1','Task 1'),('task2_macro_f1','Task 2'),('task3_macro_f1','Task 3'))):ax.bar([v+(i-1)*.24 for v in x],df[col],width=.24,label=label)
 ax.axhline(.7,color='crimson',linestyle='--',label='Gate 0.70');ax.set_xticks(list(x),df.model_id);ax.set_ylim(0,.8);ax.set_ylabel('Macro-F1');ax.set_title('Perbandingan Model Joint pada Split E42');ax.legend(ncol=4,fontsize=8);fig.tight_layout();fig.savefig(OUT/'model_comparison.png',dpi=160);plt.close(fig)
 rows=[]
 sources={'M00':OUT/'M00_e42_baseline/predictions.csv','M01':OUT/'M01_clip_indobert/predictions.csv','M02':OUT/'M02_siglip2_indobert/predictions.csv','M03':OUT/'M03_dinov2_indobert/predictions.csv','M04':OUT/'M04_siglip2_adapters/predictions.csv'}
 for model,path in sources.items():
  d=pd.read_csv(path)
  for task in TASKS:
   labels=sorted(set(d[task+'_truth'])|set(d[task+'_pred']));p,r,f,s=precision_recall_fscore_support(d[task+'_truth'],d[task+'_pred'],labels=labels,zero_division=0)
   for a,b,c,e,n in zip(labels,p,r,f,s):rows.append({'model_id':model,'task':task,'class':a,'support':int(n),'precision':b,'recall':c,'f1':e})
 pc=pd.DataFrame(rows);pc.to_csv(OUT/'per_class_comparison.csv',index=False);e42=pc[pc.model_id=='M00'];fig,axes=plt.subplots(3,1,figsize=(11,12))
 for ax,task in zip(axes,TASKS):
  z=e42[e42.task==task].sort_values('f1');ax.barh(z['class'],z['f1']);ax.axvline(.7,color='crimson',linestyle='--');ax.set_xlim(0,1);ax.set_title(task);ax.set_xlabel('F1')
 fig.tight_layout();fig.savefig(OUT/'per_class_e42.png',dpi=160,bbox_inches='tight');plt.close(fig);print({'per_class_rows':len(pc)})
if __name__=='__main__':main()
