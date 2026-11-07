#!/usr/bin/env python3
"""Create the common config/metrics/predictions/manifest/log contract."""
import hashlib,json,shutil
from pathlib import Path
import pandas as pd
from sklearn.metrics import f1_score

ROOT=Path(__file__).resolve().parents[3];P=ROOT/'DEMO_XAI_745_FULL';BASE=P/'04_hasil_eksperimen/next_research_20261017';TASKS=('task1_issue','task2_domain_sumber','task3_primary_entity_type')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write_json(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
def standardize(folder,result_path,oof_path,decision='See parent decision/report.'):
 folder.mkdir(parents=True,exist_ok=True);result=json.loads(result_path.read_text());d=pd.read_csv(oof_path);scores={t:float(f1_score(d[t+'_truth'],d[t+'_pred'],average='macro')) for t in TASKS};minimum=min(scores.values());mean=sum(scores.values())/3
 shutil.copyfile(oof_path,folder/'predictions.csv') if oof_path.resolve()!=(folder/'predictions.csv').resolve() else None
 config={k:v for k,v in result.items() if k in ('schema','model_id','joint_model','encoder','revision','configs','fold_details','training_only_auxiliary','label_metadata_used_at_inference','dataset_sha256','cache_sha256','protocol_sha256')};config.setdefault('source_result',str(result_path.relative_to(ROOT)));config.setdefault('protocol','fixed E42 5-fold OOF');write_json(folder/'config.json',config)
 write_json(folder/'metrics.json',{'samples':len(d),'unique_sample_ids':int(d.sample_id.nunique()),'macro_f1':scores,'minimum_macro_f1':minimum,'mean_macro_f1':mean,'all_tasks_at_least_0_70':minimum>=.70})
 if not (folder/'decision.md').exists():(folder/'decision.md').write_text(f'# Decision\n\n{decision}\n')
 (folder/'run.log').write_text(f'status=complete\nsamples={len(d)}\nminimum_macro_f1={minimum:.12f}\nsource_result={result_path}\n')
 files=['config.json','metrics.json','predictions.csv','decision.md','run.log'];write_json(folder/'manifest_sha256.json',{'schema':'tempo-experiment-manifest-v1','files':{x:sha(folder/x) for x in files}})
 return {'folder':str(folder.relative_to(ROOT)),'minimum':minimum}
def main():
 done=[]
 m00=BASE/'01_model_comparison/M00_e42_baseline';source=P/'04_hasil_eksperimen/e42_tail_grid';done.append(standardize(m00,source/'result.json',source/'oof.csv','Baseline remains the best candidate by minimum Macro-F1.'))
 for name in ('M01_clip_indobert','M02_siglip2_indobert','M03_dinov2_indobert','M04_siglip2_adapters'):
  f=BASE/'01_model_comparison'/name;done.append(standardize(f,f/'result.json',f/'oof.csv','Stopped because it does not beat E42 by minimum Macro-F1.'))
 j=BASE/'03_joint_optimization/J01_hierarchical_task2';done.append(standardize(j,j/'result.json',j/'oof.csv'))
 aug=json.loads((BASE/'02_augmentation/result.json').read_text())
 for variant,scores in aug['results'].items():
  f=BASE/'02_augmentation'/variant;f.mkdir(exist_ok=True);src=BASE/'02_augmentation'/f'{variant}_oof.csv';shutil.copyfile(src,f/'predictions.csv');write_json(f/'config.json',{'schema':aug['schema'],'variant':variant,'encoder':aug['encoder'],'revision':aug['revision'],'outer_test':'clean only','selection':'inner validation only'});write_json(f/'metrics.json',scores);(f/'run.log').write_text('status=complete\nsource=Kaggle tempo-sprint2-siglip-augmentation\n');(f/'decision.md').write_text(f"# Decision {variant}\n\nMinimum Macro-F1: `{scores['min']:.6f}`. See `../augmentation_ablation.md`.\n");files=['config.json','metrics.json','predictions.csv','run.log','decision.md'];write_json(f/'manifest_sha256.json',{'schema':'tempo-experiment-manifest-v1','files':{x:sha(f/x) for x in files}});done.append({'folder':str(f.relative_to(ROOT)),'minimum':scores['min']})
 write_json(BASE/'artifact_contract_report.json',{'schema':'tempo-artifact-contract-v1','status':'complete','experiments':done})
 files=sorted(p for p in BASE.rglob('*') if p.is_file() and p.name!='research_manifest_sha256.json')
 write_json(BASE/'research_manifest_sha256.json',{'schema':'tempo-research-manifest-v1','files':{str(p.relative_to(BASE)):sha(p) for p in files}})
 print(json.dumps({'standardized':len(done)},indent=2))
if __name__=='__main__':main()
