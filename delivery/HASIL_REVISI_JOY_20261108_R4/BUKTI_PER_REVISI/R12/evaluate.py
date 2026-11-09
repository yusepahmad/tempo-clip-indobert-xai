"""Revisi II: deterministic, label-safe evaluation of preserved OOF predictions.

No training, remote calls, source-result overwrites, or imputation of missing scores.
Bootstrap samples the empirical joint distribution of observations, keeping all
classes fixed; paired comparisons sample (truth, before, after) jointly.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import binomtest, entropy, spearmanr, pearsonr
from sklearn.metrics import (accuracy_score, cohen_kappa_score, confusion_matrix,
                             precision_recall_fscore_support)

TASKS = ('task1_issue', 'task2_domain_sumber', 'task3_primary_entity_type')
SEED = 20261101
RESAMPLES = 2000
CATCHALL = dict(zip(TASKS, ('other_issue', 'LAINNYA', 'multiple_or_other')))


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def write_json(path, value):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n')


def metrics(y, p, labels):
    pr, re, f1, _ = precision_recall_fscore_support(
        y, p, labels=labels, average='macro', zero_division=0)
    kappa = cohen_kappa_score(y, p, labels=labels)
    return dict(accuracy=float(accuracy_score(y, p)), precision_macro=float(pr),
                recall_macro=float(re), macro_f1=float(f1),
                kappa=float(kappa) if np.isfinite(kappa) else None)


def wilson(correct, n):
    if n <= 0 or not 0 <= correct <= n:
        raise ValueError('Invalid binomial counts')
    z = 1.959963984540054
    p = correct / n
    denom = 1 + z*z/n
    mid = (p + z*z/(2*n))/denom
    width = z*np.sqrt(p*(1-p)/n + z*z/(4*n*n))/denom
    return max(0., float(mid-width)), min(1., float(mid+width))


def matrix_macro(matrix):
    tp = np.diagonal(matrix, axis1=-2, axis2=-1)
    denom = matrix.sum(axis=-1) + matrix.sum(axis=-2)
    return np.divide(2*tp, denom, out=np.zeros_like(tp, dtype=float), where=denom>0).mean(axis=-1)


def bootstrap_macro(y, p, labels, samples=RESAMPLES, seed=SEED):
    cm = confusion_matrix(y, p, labels=labels)
    n = int(cm.sum())
    if n == 0 or samples < 2000:
        raise ValueError('Require observations and at least 2000 resamples')
    draw = np.random.default_rng(seed).multinomial(n, cm.ravel()/n, size=samples)
    values = matrix_macro(draw.reshape(samples, len(labels), len(labels)))
    return tuple(float(v) for v in np.quantile(values, [.025, .975]))


def paired_comparison(y, before, after, labels, samples=RESAMPLES, seed=SEED):
    if len(y) != len(before) or len(y) != len(after) or not len(y):
        raise ValueError('Paired observations must have identical nonzero lengths')
    enc = {v: i for i, v in enumerate(labels)}
    yi, bi, ai = (np.array([enc[v] for v in values]) for values in (y, before, after))
    k = len(labels)
    counts = np.bincount((yi*k+bi)*k+ai, minlength=k**3)
    draw = np.random.default_rng(seed).multinomial(len(y), counts/len(y), size=samples).reshape(samples, k, k, k)
    delta = matrix_macro(draw.sum(axis=2)) - matrix_macro(draw.sum(axis=3))
    before_correct, after_correct = np.array(y)==np.array(before), np.array(y)==np.array(after)
    b = int((before_correct & ~after_correct).sum())
    c = int((~before_correct & after_correct).sum())
    raw_p = float(binomtest(b, b+c, p=.5).pvalue) if b+c else 1.
    lo, hi = (float(v) for v in np.quantile(delta, [.025, .975]))
    return dict(before_only_correct=b, after_only_correct=c, discordant=b+c,
                mcnemar_exact_p=raw_p, accuracy_delta=float(after_correct.mean()-before_correct.mean()),
                macro_f1_delta=float(matrix_macro(confusion_matrix(y, after, labels=labels))-
                                     matrix_macro(confusion_matrix(y, before, labels=labels))),
                macro_delta_ci_low=lo, macro_delta_ci_high=hi,
                macro_delta_ci_excludes_zero=bool(lo>0 or hi<0),
                inference_scope='conditional saved OOF predictions; no equivalence or external generalization claim')


def holm(pvalues):
    values = np.asarray(pvalues, dtype=float)
    order = np.argsort(values, kind='stable')
    adjusted = np.minimum(1., np.maximum.accumulate((len(values)-np.arange(len(values)))*values[order]))
    result = np.empty_like(adjusted)
    result[order] = adjusted
    return result


def validate_predictions(frame, reference, folds, allow_subset=False):
    if 'sample_id' not in frame or frame.sample_id.isna().any() or not frame.sample_id.is_unique:
        raise ValueError('sample_id missing, empty or duplicated')
    if not set(frame.sample_id).issubset(reference.sample_id):
        raise ValueError('Unknown sample ID')
    if not allow_subset and set(frame.sample_id)!=set(reference.sample_id):
        raise ValueError('Incomplete OOF IDs')
    aligned = reference.set_index('sample_id').loc[frame.sample_id]
    if 'fold' not in frame or not np.array_equal(frame.fold.to_numpy(), folds.loc[frame.sample_id].to_numpy()):
        raise ValueError('Missing/mismatched canonical outer fold')
    for task in TASKS:
        if not all(task+s in frame for s in ('_truth','_pred')):
            raise ValueError('Missing task fields: '+task)
        if frame[task+'_truth'].isna().any() or frame[task+'_pred'].isna().any():
            raise ValueError('Missing truth/prediction')
        if frame[task+'_truth'].tolist()!=aligned[task].tolist():
            raise ValueError('Truth differs from immutable dataset: '+task)
        if not set(frame[task+'_pred']).issubset(set(reference[task])):
            raise ValueError('Prediction outside frozen codebook: '+task)
    return frame.sort_values('sample_id').reset_index(drop=True)


def signature(frame):
    columns=['sample_id','fold']+[t+s for t in TASKS for s in ('_truth','_pred')]
    return hashlib.sha256(frame.sort_values('sample_id')[columns].to_csv(index=False).encode()).hexdigest()


def normalize_new_predictions(raw,reference,folds,no_training=False):
    raw=raw.copy()
    if no_training is True and 'fold' not in raw:
        raw['fold']=folds.loc[raw.sample_id].to_numpy()
    return validate_predictions(raw,reference,folds)


def discover(workspace):
    app=workspace/'DEMO_XAI_745_FULL'
    reference=pd.read_csv(app/'03_data/DATASET_740_TASK2_DOMAIN.csv').fillna('')
    folds=pd.read_csv(app/'04_hasil_eksperimen/e42_tail_grid/oof.csv').set_index('sample_id')['fold']
    inventory=pd.read_csv(workspace/'delivery/experiment_final_20261020/experiment_final/benchmarks/benchmark_results.csv')
    sources=[]
    for name,group in inventory.groupby('experiment',sort=False):
        row=group.iloc[0]
        if str(row['metric_origin'])!='recomputed_from_saved_predictions':
            continue
        source=workspace/str(row.source).removeprefix('project/')
        sources.append(dict(experiment=name,path=source,phase=row.phase,
                            suffix='_baseline' if name=='BASELINE_CLIP_INDoBERT' else '_pred',
                            legacy_candidate=str(row.comparison_eligible).lower()=='true'))
    for arm in ('1x','2x'):
        source=app/f'04_hasil_eksperimen/next_research_20261017/08_ci_d01_duplicate2x/full/raw/ci_d01_dup2/oof_{arm}.csv'
        if source.exists():sources.append(dict(experiment='CI_D01_'+arm,path=source,phase='paired_control_duplication_740_oof',suffix='_pred',legacy_candidate=False))
    frames={};records=[];rejected=[]
    for spec in sources:
        raw=pd.read_csv(spec['path'])
        frame=raw[['sample_id']+(['fold'] if 'fold' in raw else [])].copy()
        if 'fold' not in frame:frame['fold']=folds.loc[frame.sample_id].to_numpy()
        complete=all(t+'_truth' in raw and t+spec['suffix'] in raw for t in TASKS)
        if not complete:
            rejected.append(dict(experiment=spec['experiment'],reason='not all three task predictions present',source=str(spec['path'].relative_to(workspace))))
            continue
        for t in TASKS:
            frame[t+'_truth']=raw[t+'_truth'];frame[t+'_pred']=raw[t+spec['suffix']]
        try:frame=validate_predictions(frame,reference,folds,allow_subset=True)
        except ValueError as e:
            note='Not included in canonical OOF tables; this does not invalidate its original inner-validation scope.' if spec['phase'].startswith('inner_validation') else 'Contract mismatch requires inspection.'
            rejected.append(dict(experiment=spec['experiment'],reason=str(e),source=str(spec['path'].relative_to(workspace)),interpretation=note))
            continue
        frames[spec['experiment']]=frame
        records.append(dict(experiment=spec['experiment'],source=str(spec['path'].relative_to(workspace)),
                            sha256=sha(spec['path']),samples=len(frame),phase=spec['phase'],
                            legacy_candidate=bool(spec['legacy_candidate']),prediction_signature=signature(frame)))
    majority=reference[['sample_id']].copy();majority['fold']=folds.loc[majority.sample_id].to_numpy()
    for t in TASKS:
        majority[t+'_truth']=reference[t];majority[t+'_pred']=''
        for fold in sorted(folds.unique()):
            train=reference[~reference.sample_id.isin(folds[folds==fold].index)]
            counts=train[t].value_counts()
            label=sorted(counts[counts==counts.max()].index)[0]
            majority.loc[majority.fold==fold,t+'_pred']=label
    frames['MAJORITY_TRAIN_FOLD']=validate_predictions(majority,reference,folds)
    records.append(dict(experiment='MAJORITY_TRAIN_FOLD',source='derived from training partition per canonical fold',
                        sha256=sha(app/'03_data/DATASET_740_TASK2_DOMAIN.csv'),samples=len(majority),phase='fold_training_majority',
                        legacy_candidate=False,prediction_signature=signature(frames['MAJORITY_TRAIN_FOLD'])))
    # New locally produced experiments are separate from the historical ranking.
    new=app/'04_hasil_eksperimen/revisi_ii/experiments'
    for path in sorted(new.glob('*/predictions.csv')):
        name=path.parent.name
        result=json.loads((path.parent/'result.json').read_text())
        raw=pd.read_csv(path)
        # A zero-shot model has no training folds. Attach the canonical ID
        # partition only for grouped diagnostics; never call it trained OOF.
        frame=normalize_new_predictions(raw,reference,folds,no_training=result.get('no_training',False))
        frames[name]=frame
        phase='zero_shot_740_no_training' if result.get('no_training') else 'revision_ii_new_740_oof'
        records.append(dict(experiment=name,source=str(path.relative_to(workspace)),sha256=sha(path),samples=len(frame),
                            phase=phase,legacy_candidate=False,prediction_signature=signature(frame),
                            fold_meaning='canonical evaluation group only; no training' if result.get('no_training') else 'canonical outer training/test fold'))
    return reference,folds,frames,records,rejected


def discover_package(package):
    package=Path(package).resolve()
    reference=pd.read_csv(package/'inputs/DATASET_740_TASK2_DOMAIN.csv').fillna('')
    folds=pd.read_csv(package/'inputs/folds.csv').set_index('sample_id')['fold']
    inventory=json.loads((package/'inputs/sources.json').read_text())
    frames={};records=[]
    for record in inventory['sources']:
        path=(package/record['package_path']).resolve()
        if not path.is_relative_to(package) or sha(path)!=record['package_sha256']:
            raise ValueError('Packaged prediction path/hash mismatch')
        frame=validate_predictions(pd.read_csv(path),reference,folds,allow_subset=True)
        if signature(frame)!=record['prediction_signature']:raise ValueError('Normalized prediction signature mismatch')
        frames[record['experiment']]=frame;records.append({k:v for k,v in record.items() if not k.startswith('package_')})
    return reference,folds,frames,records,inventory.get('rejected_sources',[])


def run(workspace, output, resamples=RESAMPLES, packaged=False):
    workspace=Path(workspace).resolve();output=Path(output).resolve()
    reference,folds,frames,records,rejected=(discover_package if packaged else discover)(workspace)
    output.mkdir(parents=True,exist_ok=True);(output/'predictions').mkdir(exist_ok=True)
    labels={t:sorted(reference[t].unique()) for t in TASKS}
    metric_rows=[];per_class=[];sensitivities=[];distribution=[];binary=[];foldstats=[]
    meta={r['experiment']:r for r in records}
    cached={}
    for name,frame in frames.items():
        frame.to_csv(output/'predictions'/f'{name}.csv',index=False)
        for ti,t in enumerate(TASKS):
            y,p=frame[t+'_truth'].to_numpy(),frame[t+'_pred'].to_numpy()
            key=(signature(frame),t)
            if key not in cached:
                values=metrics(y,p,labels[t]);lo,hi=wilson(int((y==p).sum()),len(y))
                flo,fhi=bootstrap_macro(y,p,labels[t],samples=resamples,seed=SEED+ti)
                cached[key]={**values,'accuracy_ci_low':lo,'accuracy_ci_high':hi,'macro_ci_low':flo,'macro_ci_high':fhi}
            metric_rows.append(dict(experiment=name,task=t,samples=len(frame),correct=int((y==p).sum()),**cached[key],
                                    phase=meta[name]['phase'],source=meta[name]['source'],source_sha256=meta[name]['sha256']))
            pc,rc,fc,sup=precision_recall_fscore_support(y,p,labels=labels[t],zero_division=0)
            for label,pr,re,f,s in zip(labels[t],pc,rc,fc,sup):
                per_class.append(dict(experiment=name,task=t,label=label,precision=float(pr),recall=float(re),f1=float(f),support=int(s),predicted=int((p==label).sum())))
            catch=CATCHALL[t];keep=[v for v in labels[t] if v!=catch]
            mask=y!=catch
            sensitivities.append(dict(experiment=name,task=t,full_macro_f1=cached[key]['macro_f1'],
                excluded_class=catch,macro_without_catchall_label=float(precision_recall_fscore_support(y,p,labels=keep,average='macro',zero_division=0)[2]),
                macro_on_noncatchall_truth=float(precision_recall_fscore_support(y[mask],p[mask],labels=keep,average='macro',zero_division=0)[2]),
                remaining_truth_samples=int(mask.sum()),note='two explicit sensitivity definitions; primary retains every class and sample'))
            for label in labels[t]:
                distribution.append(dict(experiment=name,task=t,label=label,gold_count=int((y==label).sum()),prediction_count=int((p==label).sum()),
                                         gold_proportion=float((y==label).mean()),prediction_proportion=float((p==label).mean())))
            if t==TASKS[1]:
                yb=np.where(y=='NON_METAFORA','literal','metaphor');pb=np.where(p=='NON_METAFORA','literal','metaphor')
                bd=metrics(yb,pb,['literal','metaphor']);domain=y!='NON_METAFORA'
                p1,r1,f1,_=precision_recall_fscore_support(yb,pb,labels=['metaphor'],average=None,zero_division=0)
                domlabels=[x for x in labels[t] if x!='NON_METAFORA']
                binary.append(dict(experiment=name,**{'binary_'+k:v for k,v in bd.items()},
                                   metaphor_precision=float(p1[0]),metaphor_recall=float(r1[0]),metaphor_f1=float(f1[0]),
                                   domain_samples=int(domain.sum()),domain_accuracy=float((y[domain]==p[domain]).mean()),
                                   domain_macro_f1=float(precision_recall_fscore_support(y[domain],p[domain],labels=domlabels,average='macro',zero_division=0)[2]),
                                   note='gold-metaphor subset; predicted NON_METAFORA remains an error, not dropped'))
            for fold in sorted(frame.fold.unique()):
                ff=frame[frame.fold==fold]
                foldstats.append(dict(experiment=name,task=t,fold=int(fold),samples=len(ff),**metrics(ff[t+'_truth'],ff[t+'_pred'],labels[t])))
        print('evaluated',name,len(frame),flush=True)
    tables={'metrics':pd.DataFrame(metric_rows),'per_class':pd.DataFrame(per_class),
            'catchall_sensitivity':pd.DataFrame(sensitivities),'class_distribution':pd.DataFrame(distribution),
            'task2_decomposed':pd.DataFrame(binary),'fold_metrics':pd.DataFrame(foldstats)}
    summary=tables['metrics'].pivot(index='experiment',columns='task',values='macro_f1')
    ranking=summary.rename(columns={t:f'macro_f1_{i+1}' for i,t in enumerate(TASKS)}).copy()
    ranking['mean_macro_f1']=summary.mean(axis=1);ranking['minimum_macro_f1']=summary.min(axis=1)
    ar=tables['metrics'].pivot(index='experiment',columns='task',values='accuracy')
    for i,t in enumerate(TASKS):ranking[f'accuracy_{i+1}']=ar[t]
    ranking['minimum_accuracy']=ar.min(axis=1)
    legacy=[r['experiment'] for r in records if r['legacy_candidate'] and 'vlm' not in r['experiment'].lower() and 'qlora' not in r['experiment'].lower()]
    old=ranking.loc[legacy].reset_index()
    old['rank_minimum_accuracy']=old.minimum_accuracy.rank(method='min',ascending=False).astype(int)
    old['rank_minimum_macro']=old.minimum_macro_f1.rank(method='min',ascending=False).astype(int)
    old['rank_mean_macro']=old.mean_macro_f1.rank(method='min',ascending=False).astype(int)
    old['rank_shift_macro_minus_accuracy']=old.rank_minimum_macro-old.rank_minimum_accuracy
    old['prediction_signature']=old.experiment.map(lambda n:meta[n]['prediction_signature'])
    old['alias_of']=old.groupby('prediction_signature')['experiment'].transform('first')
    old['legacy_subset_definition']='name excludes vlm/qlora; not proof of architecture or input provenance'
    tables['ranking_36_legacy']=old.sort_values(['rank_minimum_macro','experiment'])
    allrank=ranking.reset_index();allrank['samples']=allrank.experiment.map(lambda n:len(frames[n]))
    allrank['phase']=allrank.experiment.map(lambda n:meta[n]['phase'])
    tables['ranking_all']=allrank.sort_values('mean_macro_f1',ascending=False)
    correlations={
        'candidate_rows':len(old),'unique_prediction_signatures':old.prediction_signature.nunique(),
        'pearson_minima':float(pearsonr(old.minimum_accuracy,old.minimum_macro_f1).statistic),
        'spearman_minima':float(spearmanr(old.minimum_accuracy,old.minimum_macro_f1).statistic),
        'spearman_mean_macro_vs_minimum_accuracy':float(spearmanr(old.minimum_accuracy,old.mean_macro_f1).statistic),
        'rank_method':'competition rank, ties share minimum rank; aliases retained for document audit',
        'subset_warning':'36-name historical filter is not a count of independent architectures; VLM-derived stacking can remain under non-vlm names',
    }
    write_json(output/'rank_correlation.json',correlations)
    focus=['BASELINE_CLIP_INDoBERT','e42_tail_grid','MICRO_E11_hierarchical_task3','MICRO_E14_joint_qlora_oof']
    erows=[]
    for name in focus:
        fr=frames[name];t=TASKS[2];counts=confusion_matrix(fr[t+'_truth'],fr[t+'_pred'],labels=labels[t])
        pd.DataFrame(counts,index=labels[t],columns=labels[t]).rename_axis('gold').to_csv(output/f'confusion_task3_{name}.csv')
        gold=counts.sum(axis=1);pred=counts.sum(axis=0)
        erows.append(dict(experiment=name,task=t,gold_entropy_bits=float(entropy(gold,base=2)),prediction_entropy_bits=float(entropy(pred,base=2)),
                          individual_gold_proportion=float((fr[t+'_truth']=='individual').mean()),individual_prediction_proportion=float((fr[t+'_pred']=='individual').mean())))
        fig,ax=plt.subplots(figsize=(10,8));im=ax.imshow(counts,cmap='Blues');ax.set_xticks(range(len(labels[t])),labels[t],rotation=65,ha='right');ax.set_yticks(range(len(labels[t])),labels[t]);ax.set(xlabel='Predicted',ylabel='Gold',title=f'Task 3 — {name}')
        for i in range(len(labels[t])):
            for j in range(len(labels[t])):ax.text(j,i,str(counts[i,j]),ha='center',va='center',color='white' if counts[i,j]>counts.max()/2 else '#182330',fontsize=9)
        fig.colorbar(im,ax=ax);fig.tight_layout();fig.savefig(output/f'confusion_task3_{name}.png',dpi=150);plt.close(fig)
    tables['task3_entropy']=pd.DataFrame(erows)
    pairs=[('MAJORITY_TRAIN_FOLD',n) for n in focus]
    pairs += [('BASELINE_CLIP_INDoBERT','e42_tail_grid'),('MICRO_E11_hierarchical_task3','MICRO_E12_structured_decoder'),
              ('MICRO_E11_hierarchical_task3','MICRO_E14_joint_qlora_oof'),('M01_clip_indobert','M02_siglip2_indobert'),
              ('A00_none','A01_light'),('A00_none','A02_moderate'),('A01_light','AUG_SELECTED'),
              ('e42_tail_grid','e48_single_task_diagnostic'),('e42_tail_grid','e49_task_routed_mtl'),
              ('e42_tail_grid','J01_hierarchical_task2'),('CI_D01_1x','CI_D01_2x')]
    newnames=[n for n in frames if n.startswith('RII_')]
    if 'RII_FROZEN_MTL_WEIGHTED' in frames:
        pairs += [('RII_FROZEN_MTL_WEIGHTED',n) for n in newnames if n!='RII_FROZEN_MTL_WEIGHTED']
    if 'RII_TAIL_MTL_WEIGHTED' in frames:
        pairs += [('RII_TAIL_MTL_WEIGHTED',n) for n in newnames if n.startswith('RII_TAIL_') and n!='RII_TAIL_MTL_WEIGHTED']
    if all(n in frames for n in ['RII_QWEN_ZERO_BASIC','RII_QWEN_ZERO_RICH']):
        pairs += [('RII_QWEN_ZERO_BASIC','RII_QWEN_ZERO_RICH')]
    if all(n in frames for n in ['RII_BACKBONE_CLIP_FULL','RII_BACKBONE_SIGLIP2','RII_BACKBONE_DINOV2']):
        pairs += [('RII_BACKBONE_CLIP_FULL',n) for n in ['RII_BACKBONE_SIGLIP2','RII_BACKBONE_DINOV2']]
    if 'RII_A00_CLEAN' in frames:
        pairs += [('RII_A00_CLEAN',n) for n in ['RII_A01_LIGHT','RII_A02_MODERATE_NO_ROTATION','RII_A03_LIGHT_SAMPLER','RII_AUG_SELECTED_INNER'] if n in frames]
    if 'RII_QWEN_QLORA_BASIC' in frames:
        pairs += [('RII_QWEN_QLORA_BASIC','MICRO_E14_joint_qlora_oof')]
    comparison=[]
    for before,after in pairs:
        if before not in frames or after not in frames:continue
        a,b=frames[before],frames[after]
        if set(a.sample_id)!=set(b.sample_id):raise ValueError('Paired ID sets differ')
        a=a.set_index('sample_id').sort_index();b=b.set_index('sample_id').loc[a.index]
        for ti,t in enumerate(TASKS):
            assert a[t+'_truth'].equals(b[t+'_truth'])
            comparison.append(dict(before=before,after=after,task=t,samples=len(a),
                                   **paired_comparison(a[t+'_truth'],a[t+'_pred'],b[t+'_pred'],labels[t],samples=resamples,seed=SEED+ti)))
    cp=pd.DataFrame(comparison)
    zero_pairs=cp.before.str.startswith('RII_QWEN_ZERO_')|cp.after.str.startswith('RII_QWEN_ZERO_')
    cp.loc[zero_pairs,'inference_scope']='conditional saved predictions including zero-shot (no training); no equivalence or external generalization claim'
    cp['mcnemar_holm_p']=holm(cp.mcnemar_exact_p)
    cp['holm_family']='all listed pair-task accuracy tests; fixed family in evaluation source'
    tables['paired_tests']=cp
    for name,table in tables.items():table.to_csv(output/f'{name}.csv',index=False)
    fig,axes=plt.subplots(1,2,figsize=(13,5))
    selected=tables['metrics'][tables['metrics'].experiment.isin(focus)]
    for ax,metric in zip(axes,['macro_f1','accuracy']):
        view=selected.pivot(index='experiment',columns='task',values=metric).reindex(focus)
        view.plot.bar(ax=ax,ylim=(0,.85),rot=35);ax.set_title('Macro-F1 (primary)' if metric=='macro_f1' else 'Accuracy (supporting)');ax.set_xlabel('');ax.legend(['Task 1','Task 2','Task 3'],fontsize=8)
    fig.tight_layout();fig.savefig(output/'primary_results.png',dpi=150);plt.close(fig)
    stats=dict(status='verified_saved_prediction_analysis',models=len(frames),full_740_models=sum(len(f)==740 for f in frames.values()),
               legacy_subset_rows=len(old),metric_rows=len(tables['metrics']),per_class_rows=len(tables['per_class']),
               bootstrap_resamples=resamples,seed=SEED,ci_scope='IID observation bootstrap conditional on fixed OOF predictions; does not remove adaptive-selection bias or CV training dependence',
               source_records=records,rejected_sources=rejected,rank_correlation=correlations,
               all_revisions_complete=False,human_annotation='Not Evaluated',human_xai_ratings='Not Evaluated',
               clean_colab='Not Evaluated',clean_windows='Not Evaluated')
    write_json(output/'evaluation_verification.json',stats)
    return stats


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--workspace',type=Path,required=True);ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--package',action='store_true',help='Read self-contained inputs/sources.json, never search external workspace')
    args=ap.parse_args();report=run(args.workspace,args.output,packaged=args.package)
    print(json.dumps({k:v for k,v in report.items() if k not in {'source_records','rejected_sources'}},indent=2))
