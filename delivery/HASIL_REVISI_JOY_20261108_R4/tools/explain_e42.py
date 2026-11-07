"""Actual held-out E42 explanations: attention rollout + conditional text LIME.

Rollout is class-agnostic visual attention flow (Abnar & Zuidema, ACL2020).
It is neither Grad-CAM nor an assertion of class-conditional faithfulness.
Deletion comparisons measure actual E42 class-score changes separately.
"""
import argparse
import json
from pathlib import Path
import sys
import time

import numpy as np
import pandas as pd
from PIL import Image
import torch
from torch.nn import functional as F
from transformers import AutoModel,AutoTokenizer
from huggingface_hub import hf_hub_download,snapshot_download
import open_clip
from lime.lime_text import LimeTextExplainer
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from evaluate import TASKS,SEED,sha,write_json


def rollout_from_attention(attentions):
    if not attentions:raise ValueError('No visual attention captured')
    n=attentions[0].shape[-1];result=torch.eye(n)
    for attention in attentions:
        a=attention.detach().float().cpu()
        if a.ndim!=2 or a.shape!=(n,n) or not torch.isfinite(a).all():raise ValueError('Invalid attention matrix')
        a=a+torch.eye(n);a=a/a.sum(-1,keepdim=True)
        result=a@result
    return result[0,1:].numpy()


def inverse_center_map(values,width,height,roi=None):
    grid=int(np.sqrt(len(values)))
    if grid*grid!=len(values):raise ValueError('Non-square patch layout')
    x0,y0,x1,y1=roi or (0,0,width,height)
    rw,rh=x1-x0,y1-y0;side=min(rw,rh)
    # Match CLIP resize-shortest then center crop. Rounding is within 1 source
    # pixel; the displayed mask is an attention interpolation, not segmentation.
    resized=np.asarray(Image.fromarray(values.reshape(grid,grid).astype('float32'),mode='F').resize((side,side),Image.Resampling.BILINEAR))
    result=np.zeros((height,width),dtype='float32');left=x0+(rw-side)//2;top=y0+(rh-side)//2
    result[top:top+side,left:left+side]=resized
    return result


def normalize(values):
    a=np.asarray(values,dtype='float32');low=float(a.min());high=float(a.max())
    return (a-low)/(high-low) if high>low else np.zeros_like(a)


def main(workspace,samples=8):
    repo=Path(workspace).resolve();app=repo/'DEMO_XAI_745_FULL';out=app/'04_hasil_eksperimen/revisi_ii/xai_e42'
    out.mkdir(parents=True,exist_ok=True)
    if (out/'verification.json').exists():
        report=json.loads((out/'verification.json').read_text())
        for name,h in report['files'].items():assert sha(out/name)==h
        print('Preserved verified XAI E42 evidence');return
    torch.set_num_threads(2);started=time.monotonic()
    df=pd.read_csv(app/'03_data/DATASET_740_TASK2_DOMAIN.csv').fillna('')
    outer=pd.read_csv(app/'04_hasil_eksperimen/e42_tail_grid/oof.csv').set_index('sample_id')
    cache=app/'04_hasil_eksperimen/e41_cached_tail/cache';z=dict(np.load(cache/'front_cache.npz'))
    manifest=json.loads((app/'04_hasil_eksperimen/e36_clip_l14/features_manifest.json').read_text());pin=manifest['model']
    weights=Path(hf_hub_download(pin['repo'],pin['file'],revision=pin['revision'],token=False));assert sha(weights)==pin['sha256']
    pre=manifest['model_cfg'].get('preprocess_cfg',{})
    clip,_,transform=open_clip.create_model_and_transforms('ViT-L-14',pretrained=str(weights),precision='fp32',image_mean=pre.get('mean'),image_std=pre.get('std'))
    visual=clip.visual.eval();del clip
    for p in visual.parameters():p.requires_grad=False
    text_manifest=json.loads((app/'04_hasil_eksperimen/e37_token_pool/features_manifest.json').read_text())
    snap=Path(snapshot_download('indobenchmark/indobert-base-p1',revision=text_manifest['model_snapshot'],local_files_only=True))
    tokenizer=AutoTokenizer.from_pretrained(snap,local_files_only=True);bert=AutoModel.from_pretrained(snap,local_files_only=True).eval()
    for p in bert.parameters():p.requires_grad=False
    sys.path.insert(0,str(app/'01_notebook/e42_tail_grid'))
    import tail_model as tm
    labels={t:sorted(df[t].unique()) for t in TASKS};nc={t:len(labels[t]) for t in TASKS}
    tm.CFG['visual_weight']=2.
    tail=tm.TailMTL(nc,cache).eval()
    attention=[]

    def hook(module,args,kwargs):
        q=args[0] if args else kwargs['query'];k=args[1] if len(args)>1 else kwargs.get('key',q)
        # OpenCLIP uses packed self-attention in_proj weights. Capture exactly
        # the normalized input entering nn.MultiheadAttention.
        if not module.batch_first:q=q.transpose(0,1);k=k.transpose(0,1)
        if q.shape[0]!=1:raise ValueError('Rollout capture requires one image at a time')
        dim=module.embed_dim;heads=module.num_heads;head_dim=dim//heads
        qb=module.in_proj_bias[:dim] if module.in_proj_bias is not None else None
        kb=module.in_proj_bias[dim:2*dim] if module.in_proj_bias is not None else None
        qt=F.linear(q,module.in_proj_weight[:dim],qb).reshape(1,-1,heads,head_dim).transpose(1,2)
        kt=F.linear(k,module.in_proj_weight[dim:2*dim],kb).reshape(1,-1,heads,head_dim).transpose(1,2)
        a=((qt@kt.transpose(-2,-1))/np.sqrt(head_dim)).softmax(-1).mean(dim=1)[0]
        attention.append(a.cpu())

    @torch.inference_mode()
    def encode_image(image,capture=False):
        w,h=image.size;roi=(0,int(.20*h),w,int(.94*h));vectors=[];maps=[]
        for view,box in [(image,None),(image.crop(roi),roi)]:
            attention.clear();handles=[]
            if capture:
                handles=[block.attn.register_forward_pre_hook(hook,with_kwargs=True) for block in visual.transformer.resblocks]
            try:
                v=visual(transform(view).unsqueeze(0)).float();vectors.append(F.normalize(v,p=2,dim=1).numpy()[0])
                if capture:maps.append(inverse_center_map(rollout_from_attention(attention),w,h,box))
            finally:
                for handle in handles:handle.remove()
        return np.hstack(vectors),normalize(np.mean([normalize(a) for a in maps],axis=0)) if capture else None

    @torch.inference_mode()
    def text_features(texts):
        result=[]
        for off in range(0,len(texts),8):
            enc=tokenizer(texts[off:off+8],return_tensors='pt',truncation=True,max_length=128,padding='max_length')
            mask=enc['attention_mask'].bool()
            for sid in tokenizer.all_special_ids:mask &= enc['input_ids']!=sid
            hidden=bert(**enc).last_hidden_state
            pooled=(hidden*mask.unsqueeze(-1)).sum(1)/mask.sum(1,keepdim=True).clamp_min(1)
            result.append(F.normalize(pooled.float(),p=2,dim=1).numpy())
        return np.vstack(result)

    @torch.inference_mode()
    def scores(v,t):
        x=torch.tensor(np.hstack([np.atleast_2d(v)*2,np.atleast_2d(t)]),dtype=torch.float32)
        return {task:p.softmax(1).numpy() for task,p in tail.head(x).items()}

    selected=df.sort_values('sample_id').sample(n=samples,random_state=SEED)
    protocol=dict(schema='revisi-ii-e42-xai-v1',seed=SEED,samples=samples,selection='uniform random from sorted IDs, before explanation',
                  sample_ids=selected.sample_id.tolist(),model='E42 actual held-out fold checkpoint',visual_method='attention rollout, mean heads + residual identity, layer matrix product',
                  class_specific_visual=False,visual_view_composition='normalize full and crop inverse center maps, equal mean then normalize',
                  text_method='LIME conditional on fixed actual CLIP features; 256 local samples, positional whitespace tokens',
                  deletion_fraction=.20,random_controls_per_sample=3,scope='exploratory eight samples; not full-corpus or human acceptance',
                  source_sha256=sha(__file__),clip_weight_sha256=pin['sha256'],bert_revision=text_manifest['model_snapshot'],
                  reference='https://aclanthology.org/2020.acl-main.385/')
    write_json(out/'protocol.json',protocol)
    tests=[];faith=[];lime_rows=[];items=[];coordinator=[]
    for index,row in enumerate(selected.itertuples()):
        print('E42 XAI',index+1,samples,row.sample_id,flush=True)
        fold=int(outer.loc[row.sample_id,'fold']);cp=app/f'04_hasil_eksperimen/e42_tail_grid/fold{fold}.pt'
        checkpoint=torch.load(cp,map_location='cpu',weights_only=True)
        assert row.sample_id not in set(df.iloc[checkpoint['train_indices']].sample_id)
        assert labels==checkpoint['classes'];tail.load_state_dict(checkpoint['state_dict']);tail.eval()
        for li in range(2):bert.encoder.layer[10+li].load_state_dict({k.removeprefix(f'tail.{li}.'):v for k,v in checkpoint['state_dict'].items() if k.startswith(f'tail.{li}.')})
        position=int(df.index[df.sample_id==row.sample_id][0])
        with Image.open(app/'05_gambar'/Path(row.image_path).name) as im:image=im.convert('RGB')
        v,heat=encode_image(image,True)
        visual_error=float(np.max(np.abs(v-z['visual'][position])))
        if visual_error>3e-5:raise ValueError('CLIP visual features differ from E42 cache: '+str(visual_error))
        original=f'{row.headline_verified} [SEP] {row.supporting_text_verified}'.strip()
        text=text_features([original]);base=scores(v,text)
        with torch.inference_mode():
            cached_text=tail.features(*tm.batch_tensors(z,np.array([position]),'cpu')).numpy()[:,-768:]
        text_error=float(np.max(np.abs(text-cached_text)))
        if text_error>3e-5:raise ValueError('E42 text replay differs from cache/tail: '+str(text_error))
        predicted={t:labels[t][int(base[t].argmax())] for t in TASKS}
        assert all(predicted[t]==outer.loc[row.sample_id,t+'_pred'] for t in TASKS)
        tests.append(dict(sample_id=row.sample_id,fold=fold,checkpoint_sha256=sha(cp),visual_max_abs=visual_error,
                          text_max_abs=text_error,prediction_matches_oof=True))
        heatfile=out/f'{row.sample_id}_rollout.png'
        fig,ax=plt.subplots(figsize=(5,7));ax.imshow(image);ax.imshow(heat,cmap='magma',alpha=.48,vmin=0,vmax=1)
        ax.set_title('E42 visual attention rollout\nClass-agnostic, not Grad-CAM',fontsize=10);ax.axis('off');fig.tight_layout();fig.savefig(heatfile,dpi=110);plt.close(fig)
        image.save(out/f'{row.sample_id}_original.jpg',quality=90)
        # Deletion on a coarse8x8 grid avoids interpolation pixels selecting a
        # thin outline. Real and random remove the same number of grid cells.
        h,w=heat.shape;grid=8;cell=[]
        for gy in range(grid):
            for gx in range(grid):cell.append((heat[gy*h//grid:(gy+1)*h//grid,gx*w//grid:(gx+1)*w//grid].mean(),gy,gx))
        top=[(y,x) for _,y,x in sorted(cell,reverse=True)[:int(np.ceil(grid*grid*.2))]]
        rng=np.random.default_rng(SEED+index);controls=[]
        for _ in range(3):controls.append([divmod(int(i),grid) for i in rng.choice(grid*grid,len(top),replace=False)])
        deleted=[]
        for coords in [top]+controls:
            array=np.array(image).copy();fill=array.mean(axis=(0,1)).astype('uint8')
            for gy,gx in coords:array[gy*h//grid:(gy+1)*h//grid,gx*w//grid:(gx+1)*w//grid]=fill
            altered,_=encode_image(Image.fromarray(array));deleted.append(scores(altered,text))
        for t in TASKS:
            cls=int(base[t].argmax());real_drop=float(base[t][0,cls]-deleted[0][t][0,cls]);random_drops=[float(base[t][0,cls]-d[t][0,cls]) for d in deleted[1:]]
            faith.append(dict(sample_id=row.sample_id,task=t,predicted_label=labels[t][cls],original_score=float(base[t][0,cls]),
                             rollout_top20_drop=real_drop,random20_mean_drop=float(np.mean(random_drops)),
                             drop_difference=real_drop-float(np.mean(random_drops)),random_replicates=3,mask='8x8 coarse cells, mean image color',
                             interpretation='positive difference favors rollout locally; negative/zero is retained'))
        embedding_cache={original:text[0]}
        for ti,t in enumerate(TASKS):
            def predict_strings(strings):
                missing=list(dict.fromkeys(s for s in strings if s not in embedding_cache))
                if missing:
                    values=text_features(missing)
                    for s,val in zip(missing,values):embedding_cache[s]=val
                features=np.vstack([embedding_cache[s] for s in strings]);vv=np.repeat(v[None,:],len(strings),axis=0)
                return scores(vv,features)[t]
            explainer=LimeTextExplainer(class_names=labels[t],random_state=SEED,split_expression=r'\s+',bow=False)
            label=int(base[t].argmax());exp=explainer.explain_instance(original,predict_strings,labels=[label],num_features=12,num_samples=256)
            for word,weight in exp.as_list(label=label):lime_rows.append(dict(sample_id=row.sample_id,task=t,predicted_label=labels[t][label],token=word,
                                                   weight=float(weight),local_r2=float(exp.score),conditional_visual='fixed actual E42 CLIP full/crop features',samples=256))
        # Controls are intentionally random maps for blinded human evaluation.
        random_heat=rng.random((16,16)).astype('float32');random_heat=np.asarray(Image.fromarray(random_heat,mode='F').resize((w,h),Image.Resampling.BILINEAR))
        controlfile=out/f'{row.sample_id}_random_control.png'
        fig,ax=plt.subplots(figsize=(5,7));ax.imshow(image);ax.imshow(random_heat,cmap='magma',alpha=.48,vmin=0,vmax=1);ax.axis('off');fig.tight_layout();fig.savefig(controlfile,dpi=110);plt.close(fig)
        for actual in [True,False]:
            values=heat if actual else random_heat
            color=(plt.get_cmap('magma')(values)[...,:3]*255).astype('float32')
            overlay=np.clip(np.asarray(image).astype('float32')*.52+color*.48,0,255).astype('uint8')
            neutral=out/f'{row.sample_id}_{"rollout" if actual else "random"}_blind.png'
            Image.fromarray(overlay).save(neutral)
            coordinator.append(dict(sample_id=row.sample_id,source=neutral.name,kind='rollout' if actual else 'random_control'))
        print('E42 XAI DONE',row.sample_id,'seconds',round(time.monotonic()-started,1),flush=True)
    pd.DataFrame(tests).to_csv(out/'heldout_replay.csv',index=False)
    pd.DataFrame(faith).to_csv(out/'deletion_faithfulness.csv',index=False)
    pd.DataFrame(lime_rows).to_csv(out/'conditional_lime.csv',index=False)
    # Copy neutral, unlabeled map assets to reviewer packets: no file/title
    # leaks the control key to raters. Re-render without method-specific titles.
    human=repo/'docs/revisi-ii/human_inputs/xai';human.mkdir(parents=True,exist_ok=True)
    order=np.random.default_rng(SEED).permutation(len(coordinator));key=[];rating=[]
    for i,j in enumerate(order):
        item=coordinator[j];item_id=f'XAI-{i+1:03d}';p=human/f'{item_id}.png'
        with Image.open(out/item['source']) as source:source.save(p)
        key.append(dict(item_id=item_id,**item))
        for rater in range(1,6):
            for dimension in ['visual_clarity','visual_relevance','decision_understanding']:
                rating.append(dict(item_id=item_id,rater_id=f'R{rater}',dimension=dimension,score=''))
    pd.DataFrame(key).to_csv(repo/'docs/revisi-ii/XAI_COORDINATOR_KEY_PRIVATE.csv',index=False)
    pd.DataFrame(rating).to_csv(human/'ratings_template.csv',index=False)
    write_json(out/'verification.json',dict(status='verified_actual_e42_explanations',samples=samples,heldout_replay=True,
        source_sha256=sha(__file__),protocol_sha256=sha(out/'protocol.json'),seconds=time.monotonic()-started,
        faithfulness='exploratory actual deletion score changes; inspect all signs, not automatically faithful',
        human_ratings='Not Evaluated',visual_method_class_specific=False,
        files={p.name:sha(p) for p in out.iterdir() if p.is_file()}))
    print('E42 XAI VERIFIED',samples,round(time.monotonic()-started,1),flush=True)


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--workspace',type=Path,required=True);ap.add_argument('--samples',type=int,default=8)
    args=ap.parse_args();main(args.workspace,args.samples)
