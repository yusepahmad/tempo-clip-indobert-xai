#!/usr/bin/env python3
"""Verify, rank, and document the micro-F1 research cycle."""
import hashlib,json
from pathlib import Path
import pandas as pd
from sklearn.metrics import f1_score

ROOT=Path(__file__).resolve().parents[3];P=ROOT/'DEMO_XAI_745_FULL';BASE=P/'04_hasil_eksperimen/next_research_20261017/06_micro_f1';HIST=P/'04_hasil_eksperimen';TASKS=('task1_issue','task2_domain_sumber','task3_primary_entity_type')
def stable(p):return p.name not in ('scheduler_state.json','scheduler.log','scheduler.lock') and p.suffix not in ('.tmp','.lock')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
def metrics(path):
 d=pd.read_csv(path);reference=pd.read_csv(P/'03_data/DATASET_740_TASK2_DOMAIN.csv').set_index('sample_id');folds=pd.read_csv(HIST/'e42_tail_grid/oof.csv').set_index('sample_id')
 assert len(d)==740 and d.sample_id.is_unique and set(d.sample_id)==set(reference.index),path
 for t in TASKS:assert d[t+'_truth'].tolist()==reference.loc[d.sample_id,t].tolist(),(path,t)
 assert d.fold.tolist()==folds.loc[d.sample_id,'fold'].tolist(),path
 return {t:float(f1_score(d[t+'_truth'],d[t+'_pred'],average='micro')) for t in TASKS}
def main():
 BASE.mkdir(parents=True,exist_ok=True);items=[('E42',HIST/'e42_tail_grid/oof.csv',HIST/'e42_tail_grid/result.json')]
 for name in ('MICRO_E02_nested_stacking','MICRO_E03_classifier_chain','MICRO_E04_lexical','MICRO_E05_siglip_finetune','MICRO_E06_vlm_text','MICRO_E08_vlm_embeddings','MICRO_E10_nested_vlm_stacking','MICRO_E11_hierarchical_task3','MICRO_E12_structured_decoder','MICRO_E14_joint_qlora_oof'):
  f=BASE/name
  if (f/'result.json').exists():items.append((name,f/'predictions.csv',f/'result.json'))
 rows=[]
 for name,pred,result in items:
  s=metrics(pred);r=json.loads(result.read_text());reported=r.get('micro_f1')
  if reported:assert all(abs(s[t]-reported[t])<1e-12 for t in TASKS)
  row={'model_id':name,**s,'minimum':min(s.values()),'mean':sum(s.values())/3,'gate_passed':min(s.values())>=.7,'predictions':str(pred.relative_to(ROOT))};rows.append(row)
  if name!='E42':
   folder=pred.parent
   if not (folder/'config.json').exists():write(folder/'config.json',{k:v for k,v in r.items() if k not in ('fold_details','micro_f1','macro_f1_diagnostic','seconds','predictions_sha256')})
   if not (folder/'metrics.json').exists():write(folder/'metrics.json',row)
   if not (folder/'run.log').exists():(folder/'run.log').write_text(f"status=complete\nseconds={r.get('seconds')}\nminimum_micro_f1={row['minimum']:.12f}\n")
   if not (folder/'decision.md').exists():(folder/'decision.md').write_text(f"# Decision {name}\n\nMicro-F1: {s}. Minimum `{row['minimum']:.6f}`. Gate 0,70: **{'lulus' if row['gate_passed'] else 'gagal'}**.\n")
   files=sorted(x for x in folder.iterdir() if x.is_file() and x.name!='manifest_sha256.json' and stable(x));write(folder/'manifest_sha256.json',{'schema':'tempo-micro-experiment-manifest-v1','files':{x.name:sha(x) for x in files}})
 rank=sorted(rows,key=lambda x:(x['minimum'],x['mean']),reverse=True);pd.DataFrame(rank).to_csv(BASE/'micro_f1_comparison.csv',index=False)
 history={'E42':HIST/'e42_tail_grid/oof.csv','E44':HIST/'e44_focal_tail/oof.csv','E41':HIST/'e41_cached_tail/gpu/oof.csv','E49':HIST/'e49_task_routed_mtl/oof.csv','M02':HIST/'next_research_20261017/01_model_comparison/M02_siglip2_indobert/oof.csv','M04':HIST/'next_research_20261017/01_model_comparison/M04_siglip2_adapters/oof.csv','E02':BASE/'MICRO_E02_nested_stacking/predictions.csv'}
 history.update({name:pred for name,pred,_ in items})
 history=dict({path.resolve():(name,path) for name,path in history.items()}.values())
 dfs={k:pd.read_csv(v).sort_values('sample_id').reset_index(drop=True) for k,v in history.items() if v.exists()};oracle={}
 for d in dfs.values():
  assert len(d)==740 and d.sample_id.is_unique
  first=next(iter(dfs.values()));assert d.sample_id.tolist()==first.sample_id.tolist()
  for t in TASKS:assert d[t+'_truth'].tolist()==first[t+'_truth'].tolist()
 for t in TASKS:
  first=next(iter(dfs.values()));truth=first[t+'_truth'];correct=pd.concat([(d[t+'_pred']==truth) for d in dfs.values()],axis=1);oracle[t]={'candidate_count':len(dfs),'any_candidate_correct':float(correct.any(axis=1).mean()),'all_candidates_wrong':int((~correct.any(axis=1)).sum())}
 write(BASE/'oracle_diagnostic.json',{'eligible_result':False,'reason':'uses outer OOF truth to measure ceiling; cannot select predictions at inference','tasks':oracle})
 best=rank[0];lines=['# Laporan Target Micro-F1 0,70','', 'Untuk multiclass single-label, micro-F1 identik dengan accuracy. Semua skor berasal dari 740 OOF pada split E42.','', '| Model | Task 1 | Task 2 | Task 3 | Minimum | Gate |','| --- | ---: | ---: | ---: | ---: | --- |']
 for x in rank:lines.append(f"| {x['model_id']} | {x['task1_issue']:.4f} | {x['task2_domain_sumber']:.4f} | {x['task3_primary_entity_type']:.4f} | {x['minimum']:.4f} | {'Lulus' if x['gate_passed'] else 'Gagal'} |")
 lines+=['',f"Kandidat terbaik saat ini adalah **{best['model_id']}** dengan minimum micro-F1 **{best['minimum']:.4f}**.",'','Evaluasi ini internal. Pemilihan model berulang pada korpus sama menyebabkan bias seleksi tingkat penelitian; bukan hasil validasi independen baru.','']
 smoke=BASE/'MICRO_E07_joint_qlora_smoke/result.json'
 if smoke.exists():
  r=json.loads(smoke.read_text());lines+=['## MICRO-E07 smoke','',f"Selesai pada {r['samples']} sampel fold 1, Micro-F1: {r['micro_f1']}. Hanya diagnostic smoke; tidak masuk ranking 740 OOF. Training smoke 48 sampel belum cukup menyimpulkan QLoRA secara umum gagal. Pilot inner-training penuh MICRO-E13 menilai kelayakan selanjutnya.",'']
 pilot=BASE/'MICRO_E13_joint_qlora_inner_pilot/result.json'
 if pilot.exists():
  r=json.loads(pilot.read_text());v=json.loads((pilot.parent/'verification.json').read_text())
  lines+=['## MICRO-E13 inner-validation pilot','',f"Status {r['status']}; epoch terpilih {r['selected_epoch']} dari {len(r['history'])}. Micro-F1 pada {r['inner_validation_samples']} validation sampel: {r['validation_micro_f1']}. Kontrol pada split sama: {v['control_micro_f1']}. Kenaikan minimum {v['minimum_gain']*100:.2f} poin persentase; gate praktis pilot: {v['practical_pilot_gate']}.",'','Tidak masuk ranking OOF: epoch dipilih pada validation ini, outer-test belum dievaluasi. Ketiga skor berasal dari satu epoch/adapter yang sama. Target 0,70 pada 740 OOF belum terbukti.','']
 lines+=['Oracle hanya menunjukkan complementarity dan tidak eligible sebagai model. Tidak ada aturan yang boleh melihat truth outer-test untuk memilih prediksi.','']
 (BASE/'micro_f1_report.md').write_text('\n'.join(lines));files=sorted(p for p in BASE.rglob('*') if p.is_file() and p.name!='manifest_sha256_all.json' and stable(p));write(BASE/'manifest_sha256_all.json',{'schema':'tempo-micro-cycle-manifest-v1','files':{str(p.relative_to(BASE)):sha(p) for p in files}});print(json.dumps({'best':best,'experiments':len(rank)},indent=2))
if __name__=='__main__':main()
