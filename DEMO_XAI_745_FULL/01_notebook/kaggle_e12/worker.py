"""Task2 QLoRA classifier: frozen VLM, train-only adapters, one outer fold per run."""
import os
for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'):
    os.environ[key]='1'
os.environ['HF_HOME']='/kaggle/working/.cache/huggingface'
import gc
import hashlib
import importlib.metadata
import json
from pathlib import Path
import random
import time
import numpy as np
import pandas as pd
from PIL import Image
import torch
from torch import nn
from sklearn.metrics import f1_score,classification_report,confusion_matrix
from sklearn.model_selection import StratifiedKFold,train_test_split
from transformers import AutoProcessor,AutoModelForImageTextToText,BitsAndBytesConfig
from peft import (LoraConfig,TaskType,get_peft_model,prepare_model_for_kbit_training,
                  get_peft_model_state_dict,set_peft_model_state_dict)
from safetensors.torch import load_file

MODEL='Qwen/Qwen3-VL-8B-Instruct'
REVISION='0c351dd01ed87e9c1b53cbc748cba10e6187ff3b'
SMOKE=os.environ.get('E12_SMOKE','1')=='1'
FOLD=int(os.environ.get('E12_FOLD','1'));assert 1<=FOLD<=5
OUT=Path('/kaggle/working/e12_smoke' if SMOKE else f'/kaggle/working/e12_fold{FOLD}')
OUT.mkdir(exist_ok=True)
MAX_EPOCHS=2 if SMOKE else 6
ACCUM=8
DEFINITIONS={
    'BENCANA_JERAT':'ancaman, bencana, perangkap, jerat atau keadaan terjepit sebagai kiasan',
    'HEWAN_TUBUH':'hewan, anatomi, deformasi atau perilaku biologis sebagai kiasan',
    'KONSUMSI_TRANSAKSI':'makanan, jamuan, selera, jual-beli atau pertukaran nilai sebagai kiasan',
    'LAINNYA':'metafora dengan domain sumber selain lima domain metaforis yang disebut',
    'MESIN_INFRASTRUKTUR':'mesin, alat, kendaraan, bangunan atau mekanisme buatan sebagai kiasan',
    'NON_METAFORA':'adegan literal tanpa pemetaan metaforis; benda biasa bukan otomatis metafora',
    'PERMAINAN_KONTES':'permainan, pertandingan, kompetisi atau pertunjukan sebagai kiasan'}

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def seed(value):
    random.seed(value);np.random.seed(value);torch.manual_seed(value);torch.cuda.manual_seed_all(value)

def build_prompt(index,df,descriptions,reasons,classes):
    rules='\n'.join(f'{code}: {label}: {DEFINITIONS[label]}.' for code,label in zip('ABCDEFG',classes))
    row=df.iloc[index]
    text=('Klasifikasikan domain SUMBER metafora sampul Tempo, bukan isu politiknya.\n'+rules+
        '\nLihat ilustrasi dan konteks berikut.\nDeskripsi: '+descriptions[index]['deskripsi'][:1200]+
        '\nSumber dan alasan: '+((reasons[index].get('sumber_visual') or '')+' '+
        (reasons[index].get('alasan') or ''))[:800]+
        '\nJudul dan teks: '+(row.headline_verified+' '+row.supporting_text_verified)[:400]+
        '\nJawab satu kode A sampai G:')
    return text

def state_hash(state):
    digest=hashlib.sha256()
    for name,value in sorted(state.items()):
        digest.update(name.encode());digest.update(value.detach().float().cpu().contiguous().numpy().tobytes())
    return digest.hexdigest()

def main():
    paths=list(Path('/kaggle/input').rglob('DATASET_740_TASK2_DOMAIN.csv'));assert len(paths)==1
    csv=paths[0];root=csv.parents[1]
    assert sha(csv)=='cba20f8250bcb59481ed2d3d7d5d42fb8242c96a7ba2d11a2cd02ad80862961a'
    df=pd.read_csv(csv).fillna('');assert len(df)==740 and df.sample_id.is_unique
    files={}
    def aligned(name):
        candidates=list(Path('/kaggle/input').rglob(name));assert len(candidates)==1
        files[name]=candidates[0]
        rows=[json.loads(s) for s in candidates[0].read_text().splitlines()]
        mapping={r['sample_id']:r for r in rows}
        assert len(rows)==len(mapping)==740 and set(mapping)==set(df.sample_id)
        return [mapping[sid] for sid in df.sample_id]
    descriptions,reasons=aligned('deskripsi.jsonl'),aligned('zeroshot.jsonl')
    assert sha(files['deskripsi.jsonl'])=='c75e8df3f9b71d6786462f8d0f1187ebe4234fb8dd079924f3f35707ff1b8cd2'
    assert sha(files['zeroshot.jsonl'])=='10c07b06b13fbbf647f2b1ed12a722d9bff8f97caa6b621430d8bc0429ab38c9'
    classes=sorted(set(df.task2_domain_sumber));assert classes==sorted(DEFINITIONS)
    y=pd.Categorical(df.task2_domain_sumber,categories=classes).codes.astype(np.int64)
    issues=pd.Categorical(df.task1_issue,categories=sorted(set(df.task1_issue))).codes
    counts=np.bincount(issues);strat=np.array([i if counts[i]>=5 else -1 for i in issues])
    folds=list(StratifiedKFold(5,shuffle=True,random_state=42).split(np.zeros(740),strat))
    tr,te=folds[FOLD-1]
    inner,validation=train_test_split(tr,test_size=.2,stratify=y[tr],random_state=42+FOLD)
    assert not set(inner)&set(validation) and set(inner)|set(validation)==set(tr) and not set(tr)&set(te)
    if SMOKE:
        inner,_=train_test_split(inner,train_size=32,stratify=y[inner],random_state=42)
        validation,_=train_test_split(validation,train_size=16,stratify=y[validation],random_state=42)
        tr=np.concatenate([inner,validation]);te=te[:16]
    assert torch.cuda.is_available();device=torch.device('cuda:0')
    processor=AutoProcessor.from_pretrained(MODEL,revision=REVISION,
        min_pixels=128*128,max_pixels=384*384)
    processor.tokenizer.padding_side='left'
    letter_ids=[processor.tokenizer.encode(letter,add_special_tokens=False) for letter in 'ABCDEFG']
    assert all(len(ids)==1 for ids in letter_ids) and len({ids[0] for ids in letter_ids})==7
    code_ids=torch.tensor([ids[0] for ids in letter_ids],device=device)
    cached=[];audit=[]
    # Pure pretrained processing on all inputs; no target labels enter any prompt.
    for index in range(740):
        prompt=build_prompt(index,df,descriptions,reasons,classes)
        image_path=root/'05_gambar'/Path(df.image_path.iloc[index]).name
        with Image.open(image_path) as original:
            image=original.convert('RGB');image.thumbnail((384,384))
        messages=[{'role':'user','content':[{'type':'image','image':image},{'type':'text','text':prompt}]}]
        inputs=processor.apply_chat_template(messages,tokenize=True,add_generation_prompt=True,
            return_dict=True,return_tensors='pt')
        assert inputs['input_ids'].shape[0]==1 and inputs['input_ids'].shape[1]<=2048
        assert int(inputs['image_grid_thw'][:,1:].prod(1).max())*256<=384*384*1.2
        cached.append({name:value.cpu() for name,value in inputs.items()})
        audit.append({'sample_id':df.sample_id.iloc[index],'index':index,
            'prompt_sha256':hashlib.sha256(prompt.encode()).hexdigest(),'image_sha256':sha(image_path),
            'tokens':int(inputs['input_ids'].shape[1]),
            'token_ids_sha256':hashlib.sha256(inputs['input_ids'].numpy().tobytes()).hexdigest()})
        if (index+1)%100==0:print('preprocessed',index+1,flush=True)
    (OUT/'input_audit.jsonl').write_text(''.join(json.dumps(row)+'\n' for row in audit))
    seed(42)
    quant=BitsAndBytesConfig(load_in_4bit=True,bnb_4bit_quant_type='nf4',
        bnb_4bit_use_double_quant=True,bnb_4bit_compute_dtype=torch.float16)
    base=AutoModelForImageTextToText.from_pretrained(MODEL,revision=REVISION,
        quantization_config=quant,dtype=torch.float16,device_map={'':0},attn_implementation='sdpa')
    base.config.use_cache=False
    base=prepare_model_for_kbit_training(base,use_gradient_checkpointing=True,
        gradient_checkpointing_kwargs={'use_reentrant':False})
    adapter=LoraConfig(r=16,lora_alpha=32,lora_dropout=.05,
        target_modules=['q_proj','k_proj','v_proj','o_proj'],bias='none',
        task_type=TaskType.CAUSAL_LM,revision=REVISION)
    model=get_peft_model(base,adapter)
    named=[(name,p) for name,p in model.named_parameters() if p.requires_grad]
    assert named and all('lora_' in name and '.visual.' not in name for name,_ in named)
    for _,p in named:p.data=p.data.float()
    trainable=[p for _,p in named]
    initial={name:value.detach().cpu().clone() for name,value in
        get_peft_model_state_dict(model,save_embedding_layers=False).items()}
    initial_hash=state_hash(initial)
    frozen_name,frozen=next((name,p) for name,p in model.named_parameters() if not p.requires_grad and p.numel()>1024)
    frozen_probe=frozen.data.reshape(-1)[:1024].detach().cpu().clone()
    visual=[module for name,module in model.named_modules() if name.endswith('.visual')]
    assert visual
    config={'model':MODEL,'revision':REVISION,'smoke':SMOKE,'fold':FOLD,'classes':classes,
        'data_sha256':sha(csv),'worker_sha256':sha(Path(__file__)),
        'e01_hashes':{name:sha(p) for name,p in files.items()},'input_audit_sha256':sha(OUT/'input_audit.jsonl'),
        'initial_adapter_sha256':initial_hash,'letter_token_ids':code_ids.cpu().tolist(),
        'quantization':'NF4 doublequant float16','device':'cuda0 single T4',
        'lora':{'r':16,'alpha':32,'dropout':.05,'targets':adapter.target_modules and sorted(adapter.target_modules)},
        'trainable_parameters':sum(p.numel() for p in trainable),'frozen_probe':frozen_name,
        'microbatch':1,'accumulation':ACCUM,'lr':1e-4,'weighted_loss':'sum per microbatch, average accumulation group',
        'max_epochs':MAX_EPOCHS,'patience':2,'max_image_side':384,'max_input_tokens':2048,
        'epoch_selection':'inner20percent Task2 stratification seed42+fold; reset adapter and optimizer for refit',
        'versions':{name:importlib.metadata.version(name) for name in
            ('torch','transformers','peft','bitsandbytes','accelerate')},
        'gpu':torch.cuda.get_device_name(0),'seed':42}
    (OUT/'config.json').write_text(json.dumps(config,indent=2))
    print('model ready trainable',config['trainable_parameters'],flush=True)

    def logits(index):
        inputs={name:value.to(device) for name,value in cached[int(index)].items()}
        with torch.autocast('cuda',dtype=torch.float16):
            result=model(**inputs,logits_to_keep=1,use_cache=False,return_dict=True)
        selected=result.logits[:,-1,:].index_select(-1,code_ids).float()
        assert selected.shape==(1,7) and torch.isfinite(selected).all()
        return selected

    def predict(indices):
        model.eval();rows=[]
        with torch.inference_mode():
            for index in indices:rows.append(logits(index).softmax(-1).cpu().numpy()[0])
        values=np.array(rows);assert np.isfinite(values).all() and np.allclose(values.sum(1),1,atol=1e-5)
        return values

    def fit(indices,val,epochs,phase):
        set_peft_model_state_dict(model,initial)
        assert state_hash(get_peft_model_state_dict(model,save_embedding_layers=False))==initial_hash
        seed(42+FOLD);rng=np.random.default_rng(42+FOLD)
        optimizer=torch.optim.AdamW(trainable,lr=1e-4,weight_decay=.01)
        scaler=torch.amp.GradScaler('cuda',init_scale=128)
        counts=np.bincount(y[indices],minlength=7);assert (counts>0).all()
        class_weight=torch.tensor(len(indices)/(7*counts),dtype=torch.float32,device=device)
        criterion=nn.CrossEntropyLoss(weight=class_weight,reduction='sum')
        best=-1;chosen=1;stale=0;history=[];torch.cuda.reset_peak_memory_stats()
        for epoch in range(1,epochs+1):
            model.train()
            for module in visual:module.eval()
            torch.cuda.synchronize();started=time.monotonic();total=0.0
            order=rng.permutation(indices)
            for step,index in enumerate(order):
                if step%ACCUM==0:optimizer.zero_grad(set_to_none=True)
                targets=torch.tensor([y[index]],device=device)
                loss=criterion(logits(index),targets);assert torch.isfinite(loss)
                group_start=step//ACCUM*ACCUM;group_size=min(ACCUM,len(order)-group_start)
                scaler.scale(loss/group_size).backward();total+=float(loss.detach())
                if (step+1)%ACCUM==0 or step+1==len(order):
                    scaler.unscale_(optimizer)
                    norm=nn.utils.clip_grad_norm_(trainable,1.0,error_if_nonfinite=True)
                    assert torch.isfinite(norm)
                    scaler.step(optimizer);scaler.update()
            torch.cuda.synchronize();seconds=time.monotonic()-started
            value=None
            if val is not None:
                value=float(f1_score(y[val],predict(val).argmax(1),labels=list(range(7)),average='macro',zero_division=0))
                if value>best+1e-9:best=value;chosen=epoch;stale=0
                else:stale+=1
            row={'fold':FOLD,'phase':phase,'epoch':epoch,'weighted_loss':total/len(indices),
                'validation_macro_f1':value,'seconds':seconds,'samples':len(indices),
                'peak_cuda_bytes':torch.cuda.max_memory_allocated()}
            history.append(row)
            with (OUT/'history.jsonl').open('a') as f:f.write(json.dumps(row)+'\n')
            print(json.dumps(row),flush=True)
            if val is not None and stale>=2:break
        changed=state_hash(get_peft_model_state_dict(model,save_embedding_layers=False))!=initial_hash
        assert changed and torch.equal(frozen_probe,frozen.data.reshape(-1)[:1024].detach().cpu())
        assert all(not p.requires_grad for name,p in model.named_parameters() if 'lora_' not in name)
        del optimizer,scaler;gc.collect();torch.cuda.empty_cache()
        return chosen,{'adapter_changed':changed,'base_frozen':True,'reset_exact':True,'history':history}

    chosen,inner_info=fit(inner,validation,MAX_EPOCHS,'inner')
    _,refit_info=fit(tr,None,chosen,'refit')
    probabilities=predict(te);predicted=probabilities.argmax(1)
    adapter_path=OUT/f'fold_{FOLD}_adapter'
    model.save_pretrained(adapter_path,safe_serialization=True,save_embedding_layers=False)
    reload_matches=None
    if SMOKE:
        set_peft_model_state_dict(model,initial)
        assert state_hash(get_peft_model_state_dict(model,save_embedding_layers=False))==initial_hash
        set_peft_model_state_dict(model,load_file(str(adapter_path/'adapter_model.safetensors')))
        reloaded=predict(te)
        assert np.allclose(probabilities,reloaded,atol=1e-5,rtol=1e-4)
        assert np.array_equal(predicted,reloaded.argmax(1));reload_matches=True
    report={'status':'complete','smoke':SMOKE,'fold':FOLD,'samples':len(te),'selected_epoch':chosen,
        'inner_train_indices':inner.tolist(),'inner_validation_indices':validation.tolist(),
        'train_indices':tr.tolist(),'test_indices':te.tolist(),
        'inner_checks':{k:v for k,v in inner_info.items() if k!='history'},
        'refit_checks':{k:v for k,v in refit_info.items() if k!='history'},
        'checkpoint_reload_matches':reload_matches,
        'macro_f1':float(f1_score(y[te],predicted,labels=list(range(7)),average='macro',zero_division=0)),
        'classification':classification_report(y[te],predicted,labels=list(range(7)),output_dict=True,zero_division=0),
        'confusion_matrix':confusion_matrix(y[te],predicted,labels=list(range(7))).tolist()}
    rows=pd.DataFrame({'sample_id':df.sample_id.iloc[te].to_numpy(),'index':te,'fold':FOLD,
        'truth':np.array(classes)[y[te]],'prediction':np.array(classes)[predicted],
        **{'p_'+label:probabilities[:,i] for i,label in enumerate(classes)}})
    assert len(rows)==(16 if SMOKE else 148) and rows.sample_id.is_unique
    rows.to_csv(OUT/'oof.csv',index=False);(OUT/'metrics.json').write_text(json.dumps(report,indent=2))
    print('COMPLETE',report['macro_f1'],flush=True)

if __name__=='__main__':main()
