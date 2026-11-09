"""One heldout visual graph audit; gradients address preprocessed view pixels."""
import sys,json,hashlib,importlib
from pathlib import Path
import numpy as np,pandas as pd,torch,open_clip
from PIL import Image
from huggingface_hub import hf_hub_download
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
    cp=torch.load(out/'fold1.pt',map_location='cpu',weights_only=True);info=json.loads((out/'fold1.json').read_text());assert sha(out/'fold1.pt')==info['checkpoint_sha256']
    tm.CFG.clear();tm.CFG.update(cp['config']);model=tm.TailMTL({t:len(cp['classes'][t]) for t in tm.TASKS},cache);model.load_state_dict(cp['state_dict']);model.eval()
    for p in model.parameters():p.requires_grad=False
    ix=cp['test_indices'][0];df=pd.read_csv(cache/'DATASET_740_TASK2_DOMAIN.csv').fillna('');row=df.iloc[ix];image=ROOT/'05_gambar'/Path(row.image_path).name;assert sha(image)==row.image_sha256
    z=dict(np.load(cache/'front_cache.npz'));im=Image.open(image).convert('RGB');w,h=im.size
    pixels=torch.stack([transform(im),transform(im.crop((0,int(.20*h),w,int(.94*h))))]).requires_grad_(True)
    features=torch.nn.functional.normalize(visual(pixels).float(),dim=1).reshape(1,-1)
    error=float((features-torch.tensor(z['visual'][[ix]])).abs().max().detach());assert error<2e-5,error
    with torch.no_grad():
        text=model.features(*tm.batch_tensors(z,np.array([ix]),'cpu'))[:,-768:];cached=model(*tm.batch_tensors(z,np.array([ix]),'cpu'))
    x=torch.cat([features*tm.CFG['visual_weight'],text],1);pred=model.head(x)
    errors={t:float((pred[t]-cached[t]).abs().max().detach()) for t in tm.TASKS};assert max(errors.values())<2e-5
    norms={};gradients={}
    for t in tm.TASKS:
        g=torch.autograd.grad(pred[t][0,int(pred[t].argmax(1))],pixels,retain_graph=True)[0];assert torch.isfinite(g).all()
        norms[t]=[float(v.norm()) for v in g];assert all(v>0 for v in norms[t]);gradients[t]=g.detach()
    t=tm.TASKS[0];torch.manual_seed(42);torch.nn.init.normal_(model.head.heads[t].weight)
    rg=torch.autograd.grad(model.head(x)[t][0,0],pixels)[0];assert not torch.allclose(rg,gradients[t],atol=1e-8)
    report=dict(status='passed',scope='one fold1 heldout; CLIP full/crop preprocessed pixel gradients; text cached; not raw-coordinate overlay or explanation fidelity certification',sample_id=row.sample_id,index=ix,feature_max_abs=error,logit_max_abs=errors,pixel_gradient_norm_full_crop=norms,randomized_task1_head_sensitive=True,image_sha256=sha(image),checkpoint_sha256=sha(out/'fold1.pt'),clip_weights_sha256=sha(weights),source_sha256=sha(Path(__file__)),model_source_sha256=sha(source/'tail_model.py'))
    (out/'visual_graph_verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
