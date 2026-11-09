"""Five heldout joint input graph checks; not explanation fidelity certification."""
import sys,json,hashlib,importlib
from pathlib import Path
import numpy as np,pandas as pd,torch,open_clip
from PIL import Image
from huggingface_hub import hf_hub_download,snapshot_download
from transformers import AutoModel,AutoTokenizer
ROOT=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    source,out=map(Path,sys.argv[1:3]);sys.path.insert(0,str(source));tm=importlib.import_module('tail_model');torch.set_num_threads(8)
    vf=ROOT/'04_hasil_eksperimen/e36_clip_l14';manifest=json.loads((vf/'features_manifest.json').read_text());pin=manifest['model']
    weights=Path(hf_hub_download(pin['repo'],pin['file'],revision=pin['revision'],local_files_only=True));assert sha(weights)==pin['sha256']
    pre=manifest['model_cfg'].get('preprocess_cfg',{})
    clip,_,transform=open_clip.create_model_and_transforms('ViT-L-14',pretrained=str(weights),precision='fp32',image_mean=pre.get('mean'),image_std=pre.get('std'))
    visual=clip.visual.eval();del clip
    for p in visual.parameters():p.requires_grad=False
    cache=ROOT/'04_hasil_eksperimen/e41_cached_tail/cache';cm=json.loads((cache/'cache_manifest.json').read_text())
    for n,h in cm['files'].items():assert sha(cache/n)==h
    snap=Path(snapshot_download('indobenchmark/indobert-base-p1',revision=cm['model_snapshot'],local_files_only=True))
    for n,h in cm['model_hashes'].items():assert sha(snap/n)==h
    tok=AutoTokenizer.from_pretrained(snap,local_files_only=True)
    bert=AutoModel.from_pretrained(snap,local_files_only=True).eval();bert.config._attn_implementation='sdpa'
    for p in bert.parameters():p.requires_grad=False
    df=pd.read_csv(cache/'DATASET_740_TASK2_DOMAIN.csv').fillna('');z=dict(np.load(cache/'front_cache.npz'));reports=[]
    for k in range(1,6):
        cp=torch.load(out/f'fold{k}.pt',map_location='cpu',weights_only=True);info=json.loads((out/f'fold{k}.json').read_text());assert sha(out/f'fold{k}.pt')==info['checkpoint_sha256']
        assert not set(cp['train_indices'])&set(cp['test_indices'])
        tm.CFG.clear();tm.CFG.update(cp['config']);model=tm.TailMTL({t:len(cp['classes'][t]) for t in tm.TASKS},cache);model.load_state_dict(cp['state_dict']);model.eval()
        for p in model.parameters():p.requires_grad=False
        for j in range(2):bert.encoder.layer[10+j].load_state_dict(model.tail[j].state_dict())
        ix=cp['test_indices'][0];row=df.iloc[ix];image=ROOT/'05_gambar'/Path(row.image_path).name;assert sha(image)==row.image_sha256
        im=Image.open(image).convert('RGB');w,h=im.size
        pixels=torch.stack([transform(im),transform(im.crop((0,int(.20*h),w,int(.94*h))))]).requires_grad_(True)
        features=torch.nn.functional.normalize(visual(pixels).float(),dim=1).reshape(1,-1)
        error=float((features-torch.tensor(z['visual'][[ix]])).abs().max().detach());assert error<2e-5,error
        text=f'{row.headline_verified} [SEP] {row.supporting_text_verified}'.strip()
        enc=tok(text,return_tensors='pt',max_length=128,padding='max_length',truncation=True);pm=enc['attention_mask'].bool()
        for sid in tok.all_special_ids:pm &= enc['input_ids']!=sid
        assert pm.any()
        embedding=bert.get_input_embeddings()(enc['input_ids']).detach().requires_grad_(True)
        hidden=bert(inputs_embeds=embedding,attention_mask=enc['attention_mask'],token_type_ids=enc.get('token_type_ids')).last_hidden_state
        pooled=torch.nn.functional.normalize((hidden*pm.unsqueeze(-1)).sum(1)/pm.sum(1,keepdim=True),dim=1)
        x=torch.cat([features*tm.CFG['visual_weight'],pooled],1);pred=model.head(x)
        with torch.no_grad():cached=model(*tm.batch_tensors(z,np.array([ix]),'cpu'))
        errors={t:float((pred[t]-cached[t]).abs().max().detach()) for t in tm.TASKS}
        with torch.no_grad():
            ct=model.features(*tm.batch_tensors(z,np.array([ix]),'cpu'))[:,-768:]
            vp=model.head(torch.cat([features.detach()*tm.CFG['visual_weight'],ct],1))
            tp=model.head(torch.cat([torch.tensor(z['visual'][[ix]])*tm.CFG['visual_weight'],pooled.detach()],1))
        per_modality={name:{t:float((v[t]-cached[t]).abs().max()) for t in tm.TASKS} for name,v in [('visual',vp),('text',tp)]}
        assert all(torch.allclose(v[t],cached[t],rtol=1e-5,atol=2e-5) for v in [vp,tp,pred] for t in tm.TASKS),(per_modality,errors)
        assert all(int(pred[t].argmax(1))==int(cached[t].argmax(1)) for t in tm.TASKS)
        norms={};gradients={};targets={}
        for t in tm.TASKS:
            targets[t]=int(pred[t].argmax(1));gp,gt=torch.autograd.grad(pred[t][0,targets[t]],(pixels,embedding),retain_graph=True)
            assert torch.isfinite(gp).all() and torch.isfinite(gt).all()
            pn=[float(v.norm()) for v in gp];tn=float(gt[pm].norm());assert all(v>0 for v in pn) and tn>0
            norms[t]=dict(pixel_full_crop=pn,token_embedding=tn);gradients[t]=(gp.detach(),gt.detach())
        t=tm.TASKS[0];torch.manual_seed(42);torch.nn.init.normal_(model.head.heads[t].weight)
        rp,rt=torch.autograd.grad(model.head(x)[t][0,targets[t]],(pixels,embedding))
        assert not torch.allclose(rp,gradients[t][0],atol=1e-8)
        assert not torch.allclose(rt,gradients[t][1],atol=1e-8)
        reports.append(dict(fold=k,sample_id=row.sample_id,index=ix,feature_max_abs=error,logit_max_abs=errors,per_modality_logit_max_abs=per_modality,argmax_matches_cached=True,gradient_norms=norms,targets=targets,randomized_same_class_sensitive_both_modalities=True,image_sha256=sha(image),checkpoint_sha256=sha(out/f'fold{k}.pt')))
        del pred,x,hidden,pooled,features,pixels,embedding,model
    report=dict(status='passed',scope='5 heldout joint full image/text graphs; gradients to preprocessed pixel views and word embeddings; not raw-coordinate overlay, perturbation fidelity or production upload certification',parity_rtol=1e-5,parity_atol=2e-5,checks=reports,clip_weights_sha256=sha(weights),cache_manifest_sha256=sha(cache/'cache_manifest.json'),source_sha256=sha(Path(__file__)),model_source_sha256=sha(source/'tail_model.py'))
    (out/'joint_graph_verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
