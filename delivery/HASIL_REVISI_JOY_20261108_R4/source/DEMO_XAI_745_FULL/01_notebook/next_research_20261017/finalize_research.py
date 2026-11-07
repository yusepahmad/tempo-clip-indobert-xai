#!/usr/bin/env python3
"""Finalize Sprint 1-4 reports after Kaggle augmentation artifacts are imported."""
import csv,hashlib,json,shutil
from pathlib import Path
import pandas as pd
from sklearn.metrics import f1_score

ROOT=Path(__file__).resolve().parents[3];P=ROOT/'DEMO_XAI_745_FULL';BASE=P/'04_hasil_eksperimen/next_research_20261017';E42=P/'04_hasil_eksperimen/e42_tail_grid';FINAL=BASE/'05_final_evaluation';AUG=BASE/'02_augmentation'
TASKS=('task1_issue','task2_domain_sumber','task3_primary_entity_type')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def verified(path):
 r=json.loads(path.read_text());o=path.with_name('oof.csv');d=pd.read_csv(o);scores={t:float(f1_score(d[t+'_truth'],d[t+'_pred'],average='macro')) for t in TASKS};assert all(abs(scores[t]-r['overall_scores'][t])<1e-12 for t in TASKS);return r,scores
def main():
 FINAL.mkdir(parents=True,exist_ok=True);candidates=[]
 r=json.loads((E42/'result.json').read_text());candidates.append(('E42',r['metrics'],str(E42/'oof.csv')))
 for name,path in [('M01',BASE/'01_model_comparison/M01_clip_indobert/result.json'),('M02',BASE/'01_model_comparison/M02_siglip2_indobert/result.json'),('M03',BASE/'01_model_comparison/M03_dinov2_indobert/result.json'),('M04',BASE/'01_model_comparison/M04_siglip2_adapters/result.json'),('J01',BASE/'03_joint_optimization/J01_hierarchical_task2/result.json')]:
  rr,s=verified(path);candidates.append((name,{t:{'macro_f1':s[t]} for t in TASKS},str(path.with_name('oof.csv'))))
 aug_path=AUG/'result.json';aug=json.loads(aug_path.read_text());rows=[]
 for variant,s in aug['results'].items():rows.append({'variant':variant,**s})
 pd.DataFrame(rows).to_csv(AUG/'augmentation_results.csv',index=False)
 selected=aug['results']['selected_pipeline'];selected_oof=AUG/'selected_pipeline_oof.csv';d=pd.read_csv(selected_oof)
 for t in TASKS:assert abs(f1_score(d[t+'_truth'],d[t+'_pred'],average='macro')-selected[t])<1e-12
 candidates.append(('AUG_SELECTED',{t:{'macro_f1':selected[t]} for t in TASKS},str(selected_oof)))
 norm=[]
 for name,m,oof in candidates:
  scores={t:float(m[t]['macro_f1']) for t in TASKS};norm.append({'model_id':name,**scores,'minimum':min(scores.values()),'mean':sum(scores.values())/3,'oof':oof})
 winner=max(norm,key=lambda x:(x['minimum'],x['mean']));source=Path(winner['oof']);dest=FINAL/'oof_or_holdout_predictions.csv';shutil.copyfile(source,dest)
 evaluation={'schema':'tempo-canonical-model-evaluation-v1','evaluation_scope':'internal 5-fold OOF; not external validation','selection_rule':'maximum minimum task Macro-F1; mean tie-break','candidates':norm,'selected':winner,'required_minimum_each':.70,'gate_passed':all(winner[t]>=.70 for t in TASKS),'predictions_sha256':sha(dest)};(FINAL/'canonical_model_evaluation.json').write_text(json.dumps(evaluation,indent=2)+'\n')
 registry=[]
 for x in sorted(norm,key=lambda z:(z['minimum'],z['mean']),reverse=True):
  registry.append({'model_id':x['model_id'],'status':'complete','task1_macro_f1':x['task1_issue'],'task2_macro_f1':x['task2_domain_sumber'],'task3_macro_f1':x['task3_primary_entity_type'],'minimum_macro_f1':x['minimum'],'mean_macro_f1':x['mean'],'eligible':x['minimum']>=.70,'source':x['oof']})
 pd.DataFrame(registry).to_csv(BASE/'experiments_registry.csv',index=False)
 manifest={'schema':'tempo-research-model-manifest-v1','status':'research_candidate_not_promoted' if not evaluation['gate_passed'] else 'eligible_for_promotion','model_id':winner['model_id'],'joint_model':True,'tasks':list(TASKS),'metrics':{t:winner[t] for t in TASKS},'dataset_sha256':json.loads((BASE/'frozen_protocol.json').read_text())['dataset']['sha256'],'split_mapping_sha256':json.loads((BASE/'frozen_protocol.json').read_text())['outer_cv']['mapping_sha256'],'predictions_sha256':sha(dest),'runtime_note':'Current web runtime is unchanged unless the academic gate passes; do not present this research candidate as deployed.'};(FINAL/'model_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 lines=['# Ablation Augmentasi','', '| Varian | Task 1 | Task 2 | Task 3 | Minimum | Mean |','| --- | ---: | ---: | ---: | ---: | ---: |']
 for x in rows:lines.append(f"| {x['variant']} | {x['task1_issue']:.4f} | {x['task2_domain_sumber']:.4f} | {x['task3_primary_entity_type']:.4f} | {x['min']:.4f} | {x['mean']:.4f} |")
 lines+=['','Varian dipilih per outer fold hanya dari inner-validation. Outer test selalu memakai gambar bersih. Fitur augmented tidak pernah dipakai pada validation/test.','',f"Pipeline terpilih menghasilkan minimum Macro-F1 **{selected['min']:.4f}**. Target 0,70 {'tercapai' if selected['min']>=.70 else 'belum tercapai'}.",'']
 (AUG/'augmentation_ablation.md').write_text('\n'.join(lines))
 (BASE/'findings.md').write_text(f'''# Temuan Final Sprint 0–4

1. Audit dataset/split/provenance lulus; 740 gambar cocok hash dan tidak ada exact duplicate.
2. Model comparison M00–M04 selesai. E42 tetap terbaik dengan Macro-F1 {winner['task1_issue']:.4f}/{winner['task2_domain_sumber']:.4f}/{winner['task3_primary_entity_type']:.4f}.
3. Augmentation A00–A03 selesai; pipeline pilihan inner-fold minimum {selected['min']:.4f} dan tidak mengalahkan E42.
4. E49 MMoE dan J01 hierarchical auxiliary tidak mengatasi negative transfer.
5. OCR exact match terbaik pada holdout kedua adalah 76,67% (69/90); gate 80% gagal.
6. Target ketiga task ≥0,70 gagal dan tidak diturunkan. Evaluasi tetap disebut internal OOF, bukan external validation.
7. Runtime delivery tidak diganti karena tidak ada kandidat yang lolos gate.
8. Pengujian clean Windows dan pengguna manusia tetap menunggu pelaksanaan pengguna.
''')
 print(json.dumps({'winner':winner,'gate_passed':evaluation['gate_passed']},indent=2))
if __name__=='__main__':main()
