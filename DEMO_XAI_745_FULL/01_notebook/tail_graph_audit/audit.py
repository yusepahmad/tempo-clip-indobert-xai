"""Text graph reconstruction evidence; not full multimodal XAI certification."""
import sys,json,hashlib,importlib
from pathlib import Path
import numpy as np,pandas as pd,torch
from transformers import AutoModel,AutoTokenizer
from huggingface_hub import snapshot_download
ROOT=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    source,out=map(Path,sys.argv[1:3]);sys.path.insert(0,str(source));tm=importlib.import_module('tail_model');torch.set_num_threads(8)
    cache=ROOT/'04_hasil_eksperimen/e41_cached_tail/cache';manifest=json.loads((cache/'cache_manifest.json').read_text())
    for n,h in manifest['files'].items():assert sha(cache/n)==h
    snap=Path(snapshot_download('indobenchmark/indobert-base-p1',revision=manifest['model_snapshot'],local_files_only=True))
    for n,h in manifest['model_hashes'].items():assert sha(snap/n)==h
    tok=AutoTokenizer.from_pretrained(snap,local_files_only=True);bert=AutoModel.from_pretrained(snap,local_files_only=True).eval();bert.config._attn_implementation='sdpa'
    df=pd.read_csv(cache/'DATASET_740_TASK2_DOMAIN.csv').fillna('');z=dict(np.load(cache/'front_cache.npz'));reports=[]
    for k in range(1,6):
        cp=torch.load(out/f'fold{k}.pt',map_location='cpu',weights_only=True);info=json.loads((out/f'fold{k}.json').read_text());assert sha(out/f'fold{k}.pt')==info['checkpoint_sha256']
        tm.CFG.clear();tm.CFG.update(cp['config']);model=tm.TailMTL({t:len(cp['classes'][t]) for t in tm.TASKS},cache);model.load_state_dict(cp['state_dict']);model.eval()
        for j in range(2):bert.encoder.layer[10+j].load_state_dict(model.tail[j].state_dict())
        for p in bert.parameters():p.requires_grad=False
        for p in model.parameters():p.requires_grad=False
        ix=cp['test_indices'][0];row=df.iloc[ix];text=f'{row.headline_verified} [SEP] {row.supporting_text_verified}'.strip()
        enc=tok(text,return_tensors='pt',max_length=128,padding='max_length',truncation=True);pm=enc['attention_mask'].bool()
        for sid in tok.all_special_ids:pm &= enc['input_ids']!=sid
        assert pm.any()
        embedding=bert.get_input_embeddings()(enc['input_ids']).detach().requires_grad_(True)
        hidden=bert(inputs_embeds=embedding,attention_mask=enc['attention_mask'],token_type_ids=enc.get('token_type_ids')).last_hidden_state
        pooled=torch.nn.functional.normalize((hidden*pm.unsqueeze(-1)).sum(1)/pm.sum(1,keepdim=True),dim=1)
        full=model.head(torch.cat([torch.tensor(z['visual'][[ix]])*tm.CFG['visual_weight'],pooled],1))
        with torch.no_grad():cached=model(*tm.batch_tensors(z,np.array([ix]),'cpu'))
        errors={t:float((full[t]-cached[t]).abs().max().detach()) for t in tm.TASKS};assert max(errors.values())<2e-5,errors
        grads={};norms={}
        for t in tm.TASKS:
            target=int(full[t].argmax(1));g=torch.autograd.grad(full[t][0,target],embedding,retain_graph=True)[0]
            assert torch.isfinite(g).all() and g[pm].abs().sum()>0
            grads[t]=g.detach();norms[t]=float(g[pm].norm())
        # Randomized classifier must change input gradients; no model score used.
        t=tm.TASKS[0];torch.manual_seed(42);torch.nn.init.normal_(model.head.heads[t].weight)
        randomized=model.head(torch.cat([torch.tensor(z['visual'][[ix]])*tm.CFG['visual_weight'],pooled],1))
        rg=torch.autograd.grad(randomized[t][0,0],embedding)[0];assert not torch.allclose(rg,grads[t],atol=1e-8)
        reports.append(dict(fold=k,sample_id=row.sample_id,index=ix,checkpoint_sha256=sha(out/f'fold{k}.pt'),logit_max_abs=errors,token_gradient_norm=norms,randomized_head_sensitive=True))
    report=dict(status='passed',scope='5heldout full text graph + gradients; visual features cached, pixelXAI not audited; not explanation fidelity certification',source_sha256=sha(Path(__file__)),model_source_sha256=sha(source/'tail_model.py'),cache_manifest_sha256=sha(cache/'cache_manifest.json'),checks=reports)
    (out/'text_graph_verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
