"""Serving of the original RII_TAIL_RICH256 outer-fold checkpoints.

Dataset IDs select their held-out checkpoint. New uploads average probabilities
from the five checkpoints; this serving ensemble has no separate OOF score.
"""
from __future__ import annotations
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import numpy as np
import pandas as pd
import torch
from PIL import Image
from label_display import nama_task, tampil
from xai_core import XAIEngine, TASKS

ROOT = Path(__file__).resolve().parent.parent
BACKEND = 'clip-indobert-tail-rich256'
VERSION = 'clip-indobert-tail-rich256-v1'
FIELDS = ('description', 'source_visual', 'reason')

def sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(4 * 1024 * 1024), b''):
            h.update(b)
    return h.hexdigest()

class TailRichEngine(XAIEngine):
    def __init__(self):
        torch.set_num_threads(max(1,min(8,int(os.environ.get('TEMPO_CPU_THREADS','4')))))
        self.assets = Path(os.environ.get('TEMPO_TAIL_ASSET_DIR') or ROOT/'06_models'/VERSION)
        self.manifest = json.loads((ROOT/'06_models'/VERSION/'manifest.json').read_text())
        for name, digest in self.manifest['asset_sha256'].items():
            if sha(self.assets/name) != digest:
                raise ValueError('Artefak model tidak cocok: '+name)
        if sha(ROOT/'03_data/DATASET_740_TASK2_DOMAIN.csv') != self.manifest['dataset_sha256']:
            raise ValueError('Dataset tidak cocok dengan model')
        self.df = pd.read_csv(ROOT/'03_data/DATASET_740_TASK2_DOMAIN.csv').fillna('')
        self.tasks = list(TASKS)
        spec = importlib.util.spec_from_file_location('_tempo_tail_model', ROOT/'01_notebook/e42_tail_grid/tail_model.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self._tm = module
        self._models = {}
        self._fold_for_id = {}
        covered = set()
        for fold in range(1, 6):
            cp = torch.load(self.assets/f'fold{fold}_joint.pt', map_location='cpu', weights_only=True)
            if cp['arm'] != 'RII_TAIL_RICH256' or cp['protocol_sha256'] != self.manifest['protocol_sha256']:
                raise ValueError('Checkpoint bukan kandidat yang diminta')
            maps = cp['labels']
            if fold == 1:
                self.maps = maps
                self.ncls = {t:len(maps[t]) for t in self.tasks}
            if maps != self.maps or set(cp['active']) != set(TASKS):
                raise ValueError('Label/head checkpoint tidak konsisten')
            train, test = set(cp['train_indices']), set(cp['test_indices'])
            if train & test or train | test != set(range(len(self.df))) or covered & test:
                raise ValueError('Split outer-fold tidak sah')
            covered |= test
            for i in test:
                self._fold_for_id[str(self.df.iloc[i].sample_id)] = fold
            model = module.TailMTL(self.ncls, self.assets)
            model.load_state_dict(cp['state_dict'], strict=True)
            model.eval()
            for p in model.parameters():
                p.requires_grad_(False)
            self._models[fold] = model
        if covered != set(range(740)):
            raise ValueError('Cakupan model harus 740 ID unik')
        self.y = {t:self.df[t].map({c:i for i,c in enumerate(self.maps[t])}).to_numpy() for t in self.tasks}
        self.cache = dict(np.load(self.assets/'rich256_front_cache.npz', allow_pickle=False))
        if self.cache['sample_ids'].tolist() != self.df.sample_id.tolist():
            raise ValueError('Urutan fitur berbeda dari dataset')
        path = ROOT/'04_hasil_eksperimen/revisi_ii/text_inputs/label_blind_inputs.jsonl'
        if sha(path) != self.manifest['rich_inputs_sha256']:
            raise ValueError('Keterangan visual tidak cocok')
        self.rich_inputs = {r['sample_id']:r for r in map(json.loads,path.read_text().splitlines())}
        self._visual = self._front = self._tok = self._preprocess = None
        self._active = []
        self._context = None
        self.ready = False
        self.model = None
        self.dim_img = 1536
        self.X = np.hstack([self.cache['visual']*2, self.cache['base_mean']]).astype(np.float32)
        self._ensure_front()
        self._ensure_visual()
        self.ready = True

    def description(self):
        return dict(self.manifest, ready=self.ready, tasks=self.tasks, device='cpu',
                    dataset_protocol='original held-out outer-fold checkpoint, including edited text and batch',
                    upload_protocol='mean class probabilities from five outer-fold models; not separately evaluated',
                    upload_requires=list(FIELDS), batch_upload_supported=False,
                    text_xai='headline perturbations; supporting and visual descriptions fixed')

    def train(self, *args, **kwargs):
        raise RuntimeError('Backend checkpoint tidak melatih ulang head saat melayani web')

    @staticmethod
    def rich_text(headline, supporting, fields):
        return (f"{headline} [SEP] {supporting} [SEP] Deskripsi visual: {fields['description']}. "
                f"Observasi sumber visual: {fields['source_visual']}. Alasan visual: {fields['reason']}.")

    def _ensure_encoders(self):
        self._ensure_front()
        self._ensure_visual()

    def _ensure_front(self):
        if self._front is not None:
            return
        from transformers import AutoModel, AutoTokenizer
        from huggingface_hub import snapshot_download
        revision = self.manifest['indobert']['revision']
        snap = Path(snapshot_download(self.manifest['indobert']['repo'], revision=revision, local_files_only=True))
        for name,digest in self.manifest['indobert']['files'].items():
            if sha(snap/name) != digest:
                raise ValueError('Backbone IndoBERT berbeda: '+name)
        self._tok = AutoTokenizer.from_pretrained(snap, local_files_only=True)
        self._front = AutoModel.from_pretrained(snap, local_files_only=True).eval()
        self._front.encoder.layer = torch.nn.ModuleList(list(self._front.encoder.layer[:10]))
        for p in self._front.parameters():
            p.requires_grad_(False)

    def _ensure_visual(self):
        if self._visual is not None:
            return
        import open_clip
        from huggingface_hub import hf_hub_download
        pin = self.manifest['clip']
        weights = Path(hf_hub_download(pin['repo'],pin['file'],revision=pin['revision'],local_files_only=True))
        if sha(weights) != pin['sha256']:
            raise ValueError('Backbone CLIP berbeda')
        cfg = json.loads(Path(hf_hub_download(pin['repo'],'open_clip_config.json',revision=pin['revision'],local_files_only=True)).read_text())
        pre = cfg.get('preprocess_cfg',{})
        model, _, self._preprocess = open_clip.create_model_and_transforms('ViT-L-14',pretrained=str(weights),precision='fp32',image_mean=pre.get('mean'),image_std=pre.get('std'))
        self._visual = model.visual.eval()
        for p in self._visual.parameters():
            p.requires_grad_(False)

    def _images(self, image_path):
        self._ensure_visual()
        with Image.open(image_path) as image:
            image=image.convert('RGB');w,h=image.size
            crop=image.crop((0,int(.20*h),w,int(.94*h)))
            return torch.stack([self._preprocess(image),self._preprocess(crop)])

    def _front_inputs(self, texts):
        self._ensure_front()
        enc=self._tok(texts,return_tensors='pt',truncation=True,max_length=256,padding=True)
        attention=enc['attention_mask'].bool()
        pool=attention.clone()
        for sid in self._tok.all_special_ids:
            pool &= enc['input_ids'] != sid
        if not pool.any(dim=1).all():
            raise ValueError('Teks tidak memuat token yang bisa dianalisis')
        with torch.no_grad():
            hidden=self._front(**enc).last_hidden_state
        return hidden, attention, pool

    def prepare_analysis(self, image_path, headline, supporting, sample_id=None, fields=None, cancel=None):
        if cancel: cancel()
        if sample_id:
            if sample_id not in self._fold_for_id:
                raise ValueError('ID dataset tidak dikenal')
            index=int(self.df.index[self.df.sample_id==sample_id][0])
            if sha(image_path) != self.df.iloc[index].image_sha256:
                raise ValueError('Gambar dataset berbeda dari sumber evaluasi')
            self._active=[self._fold_for_id[sample_id]]
            base=self.rich_inputs[sample_id]
            visual=self.cache['visual'][index].copy()
            canonical=(headline==base['headline'] and supporting==base['supporting'] and all(fields[k]==base[k] for k in FIELDS))
            if canonical:
                ix=np.array([index]);h,attention,pool,_=self._tm.batch_tensors(self.cache,ix,'cpu')
            else:
                h,attention,pool=self._front_inputs([self.rich_text(headline,supporting,fields)])
            protocol=f'dataset outer-fold {self._active[0]}; held-out ID; '+('canonical rich input' if canonical else 'edited rich input; not a new benchmark')
        else:
            self._active=list(range(1,6))
            self._ensure_visual()
            with torch.no_grad():
                encoded=self._visual(self._images(image_path))
                encoded=torch.nn.functional.normalize(encoded.float(),p=2,dim=1)
                visual=encoded.reshape(-1).numpy()
            h,attention,pool=self._front_inputs([self.rich_text(headline,supporting,fields)])
            protocol='new upload; five-fold probability ensemble; Not Evaluated separately'
        with torch.no_grad():
            vectors={fold:self._models[fold].features(h,attention,pool,torch.tensor(visual).reshape(1,-1))[0].numpy() for fold in self._active}
        self._context=dict(image_path=Path(image_path),headline=headline,supporting=supporting,fields=dict(fields),visual=visual,vectors=vectors,protocol=protocol,sample_id=sample_id)
        self.model=self._models[self._active[0]].head
        if cancel:cancel()
        vec=vectors[self._active[0]]
        return visual,vec[1536:],vec

    def _result(self, probabilities):
        out={}
        for task in self.tasks:
            prob=probabilities[task];order=np.argsort(prob)[::-1];label=self.maps[task][int(order[0])]
            out[task]=dict(nama_task=TASKS[task],nama_task_mudah=nama_task(task),prediksi=label,prediksi_tampil=tampil(label),
                probabilitas=float(prob[order[0]]),semua=[dict(kelas=self.maps[task][int(j)],kelas_tampil=tampil(self.maps[task][int(j)]),prob=float(prob[j])) for j in order],
                backend=BACKEND,model_version=VERSION,score_kind='softmax_uncalibrated',score_label='Skor model (belum dikalibrasi)',
                evaluation_mode=self._context['protocol'],evaluation=dict(protocol=self.manifest['evaluation']['protocol'],samples=740,
                    macro_f1=self.manifest['evaluation']['macro_f1'][task],micro_f1=self.manifest['evaluation']['micro_f1'][task]))
        return out

    def predict_vector(self, x):
        if self._context is None:
            raise RuntimeError('Konteks model belum dipilih')
        values={t:[] for t in self.tasks}
        with torch.no_grad():
            for fold in self._active:
                outputs=self._models[fold].head(torch.tensor(self._context['vectors'][fold]).reshape(1,-1))
                for t in self.tasks:
                    values[t].append(torch.softmax(outputs[t][0],dim=0).numpy())
        return self._result({t:np.mean(values[t],axis=0) for t in self.tasks})

    def _prob_banyak_teks(self, img_feat, daftar_teks, supporting, task, ukuran_kelompok=8):
        result=[]
        for start in range(0,len(daftar_teks),ukuran_kelompok):
            headlines=list(daftar_teks[start:start+ukuran_kelompok])
            texts=[self.rich_text(t,supporting,self._context['fields']) for t in headlines]
            hidden,attention,pool=self._front_inputs(texts)
            visual=torch.tensor(np.repeat(self._context['visual'].reshape(1,-1),len(texts),axis=0))
            with torch.no_grad():
                probs=[torch.softmax(self._models[f](hidden,attention,pool,visual)[task],dim=1).numpy() for f in self._active]
            result.append(np.mean(probs,axis=0))
        return np.vstack(result)

    def atribusi_kata(self,img_feat,headline,supporting,task):
        words=headline.split();variants=[headline]+[' '.join(words[:i]+words[i+1:]) for i in range(len(words))]
        probabilities=self._prob_banyak_teks(img_feat,variants,supporting,task)
        k=int(probabilities[0].argmax())
        return [dict(kata=w,kontribusi=float(probabilities[0,k]-probabilities[i+1,k])) for i,w in enumerate(words)],self.maps[task][k],float(probabilities[0,k])

    @staticmethod
    def _normalize(cam):
        span=float(cam.max()-cam.min())
        return (cam-cam.min())/span if span>1e-12 else np.zeros_like(cam)

    def gradcam_terpadu(self,image_path,txt_feat):
        images=self._images(image_path).requires_grad_(True)
        saved={}
        handle=self._visual.transformer.resblocks[-2].register_forward_hook(lambda _m,_i,out:saved.update(activation=out))
        try:
            visual=torch.nn.functional.normalize(self._visual(images).float(),p=2,dim=1).reshape(1,-1)*2
            outputs={t:[] for t in self.tasks}
            for fold in self._active:
                text=torch.tensor(self._context['vectors'][fold][1536:]).reshape(1,-1)
                logits=self._models[fold].head(torch.cat([visual,text],dim=1))
                for t in self.tasks:outputs[t].append(torch.softmax(logits[t],dim=1))
            act=saved['activation'];per={}
            for task in self.tasks:
                probabilities=torch.stack(outputs[task]).mean(0)
                target=probabilities[0,int(probabilities.argmax(1)[0])]
                gradient=torch.autograd.grad(target,act,retain_graph=True)[0]
                a,g=act,gradient
                if a.shape[0]!=2 and a.shape[1]==2:a,g=a.transpose(0,1),g.transpose(0,1)
                if a.shape[0]!=2:raise RuntimeError('Bentuk aktivasi CLIP tidak sesuai')
                maps=(a[:,1:]*g[:,1:]).sum(-1).abs().detach().numpy()
                side=int(round(maps.shape[1]**.5))
                if side*side!=maps.shape[1] or not np.isfinite(maps).all() or not maps.any():
                    raise RuntimeError('Peta gradient CLIP tidak sah')
                full=np.asarray(Image.fromarray(maps[0].reshape(side,side)).resize((224,224),Image.Resampling.BILINEAR)).copy()
                crop=np.asarray(Image.fromarray(maps[1].reshape(side,side)).resize((224,166),Image.Resampling.BILINEAR))
                overlay=np.zeros((224,224),np.float32);overlay[44:210]=crop
                per[task]=self._normalize(full+overlay)
        finally:handle.remove()
        return self._normalize(np.mean(list(per.values()),axis=0)),per

    def xai_contract(self,task):
        return dict(model_version=VERSION,task=task,folds=self._active,evaluation_mode=self._context['protocol'],
                    visual_method='CLIP-L14 full/crop penultimate-block absolute gradient x activation through the same active checkpoint heads',
                    text_method='headline LIME/occlusion through pinned IndoBERT front and the same trained tail; supporting and visual descriptions fixed',
                    score_kind='softmax_uncalibrated',limitation='Sensitivitas model, bukan bukti kausal. Peta full/crop dijumlahkan pada koordinat sampul; peta terpadu merata-ratakan tiga task.')
