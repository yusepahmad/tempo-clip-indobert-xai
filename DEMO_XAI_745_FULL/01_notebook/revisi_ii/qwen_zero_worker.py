"""Qwen8B zero-shot, two explicit input scopes, no training or LoRA."""
import os
for name in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'):os.environ[name]='1'
import hashlib
import json
from pathlib import Path
import time
import numpy as np
import pandas as pd
from PIL import Image
import torch
from transformers import AutoModelForImageTextToText,AutoProcessor,BitsAndBytesConfig


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p,v):Path(p).write_text(json.dumps(v,indent=2)+'\n')


def main():
    start=time.monotonic();smoke=os.environ.get('RII_ZERO_SMOKE','1')=='1'
    out=Path('/kaggle/working/revisi_ii_qwen_zero_smoke' if smoke else '/kaggle/working/revisi_ii_qwen_zero');out.mkdir(exist_ok=True)
    protocol_path=Path('/kaggle/working/protocol.json');protocol=json.loads(protocol_path.read_text())
    definitions=protocol['definitions'];tasks=tuple(definitions)
    csv=next(Path('/kaggle/input').rglob('DATASET_740_TASK2_DOMAIN.csv'));assert sha(csv)==protocol['dataset_sha256']
    df=pd.read_csv(csv).fillna('');images=csv.parents[1]/'05_gambar'
    descpath=next(Path('/kaggle/input').rglob('deskripsi.jsonl'));zeropath=next(Path('/kaggle/input').rglob('zeroshot.jsonl'))
    assert sha(descpath)==protocol['description_sha256'];assert sha(zeropath)==protocol['zeroshot_sha256']
    desc={r['sample_id']:r for r in map(json.loads,descpath.read_text().splitlines())}
    zero={r['sample_id']:r for r in map(json.loads,zeropath.read_text().splitlines())}
    selected=np.arange(len(df)) if not smoke else np.array([0,147,443,739])
    processor=AutoProcessor.from_pretrained(protocol['model'],revision=protocol['revision'],min_pixels=128*128,max_pixels=384*384)
    processor.tokenizer.padding_side='left'
    model=AutoModelForImageTextToText.from_pretrained(protocol['model'],revision=protocol['revision'],
        quantization_config=BitsAndBytesConfig(load_in_4bit=True,bnb_4bit_quant_type='nf4',bnb_4bit_use_double_quant=True,bnb_4bit_compute_dtype=torch.float16),
        dtype=torch.float16,device_map={'':0},attn_implementation='sdpa').eval()
    for p in model.parameters():p.requires_grad=False
    classes={t:sorted(definitions[t]) for t in tasks}
    code={t:[processor.tokenizer.encode(letter,add_special_tokens=False) for letter in 'ABCDEFGHIJ'[:len(classes[t])]] for t in tasks}
    assert all(all(len(ids)==1 for ids in code[t]) for t in tasks)
    code={t:torch.tensor([ids[0] for ids in values],device='cuda') for t,values in code.items()}
    rows={scope:[] for scope in ['BASIC','RICH']};audits=[]
    for n,index in enumerate(selected):
        r=df.iloc[index]
        imagepath=images/Path(r.image_path).name
        with Image.open(imagepath) as im:image=im.convert('RGB');image.thumbnail((384,384))
        basic=f'Analisis sampul majalah Tempo tanpa memakai label anotasi. Judul: {r.headline_verified}. Teks pendukung: {r.supporting_text_verified}. '
        rich=basic+f"Deskripsi visual: {desc[r.sample_id]['deskripsi'][:1000]}. Observasi sumber visual: {(zero[r.sample_id].get('sumber_visual') or '')[:250]}. Alasan visual: {(zero[r.sample_id].get('alasan') or '')[:500]}."
        for scope,common in [('BASIC',basic),('RICH',rich)]:
            record={'sample_id':r.sample_id}
            for task in tasks:
                options='\n'.join(f'{letter}: {label}: {definitions[task][label]}' for letter,label in zip('ABCDEFGHIJ',classes[task]))
                question={tasks[0]:'Pilih isu utama yang paling dominan.',tasks[1]:'Pilih domain SUMBER metafora visual-verbal, bukan isu politiknya.',tasks[2]:'Pilih tipe entitas yang menjadi sasaran atau fokus kritik utama.'}[task]
                prompt=f'{common}\n{question}\n{options}\nJawab tepat satu kode huruf:'
                messages=[{'role':'user','content':[{'type':'image','image':image},{'type':'text','text':prompt}]}]
                inputs=processor.apply_chat_template(messages,tokenize=True,add_generation_prompt=True,return_dict=True,return_tensors='pt').to('cuda')
                assert inputs['input_ids'].shape[1]<=2048
                with torch.inference_mode(),torch.autocast('cuda',dtype=torch.float16):
                    logits=model(**inputs,logits_to_keep=1,use_cache=False,return_dict=True).logits[:,-1,:].index_select(-1,code[task]).float()
                assert torch.isfinite(logits).all();prob=logits.softmax(-1).cpu().numpy()[0]
                record[task+'_truth']=r[task];record[task+'_pred']=classes[task][int(prob.argmax())]
                for label,p in zip(classes[task],prob):record[f'{task}_p_{label}']=float(p)
                audits.append(dict(sample_id=r.sample_id,scope=scope,task=task,prompt_sha256=hashlib.sha256(prompt.encode()).hexdigest(),image_sha256=sha(imagepath),tokens=int(inputs['input_ids'].shape[1])))
                if time.monotonic()-start>protocol['wall_seconds_limit']:raise RuntimeError('Zero-shot wall-time budget exceeded')
            rows[scope].append(record)
        if (n+1)%20==0 or smoke:
            print('ZERO',n+1,len(selected),round(time.monotonic()-start,1),flush=True)
            for scope in rows:pd.DataFrame(rows[scope]).to_csv(out/f'partial_{scope.lower()}.csv',index=False)
    for scope in rows:pd.DataFrame(rows[scope]).to_csv(out/f'predictions_{scope.lower()}.csv',index=False)
    (out/'input_audit.jsonl').write_text(''.join(json.dumps(a)+'\n' for a in audits))
    dump(out/'result.json',dict(status='complete',smoke=smoke,samples=len(selected),scopes=['BASIC','RICH'],
         no_training=True,model=protocol['model'],revision=protocol['revision'],protocol_sha256=sha(protocol_path),source_sha256=sha(__file__),
         predictions_sha256={s:sha(out/f'predictions_{s.lower()}.csv') for s in rows},input_audit_sha256=sha(out/'input_audit.jsonl'),
         seconds=time.monotonic()-start,gpu=torch.cuda.get_device_name(0),torch=torch.__version__))
    print('QWEN_ZERO_COMPLETE',len(selected),flush=True)


if __name__=='__main__':main()
