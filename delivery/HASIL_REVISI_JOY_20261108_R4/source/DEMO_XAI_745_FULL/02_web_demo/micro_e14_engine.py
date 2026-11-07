"""True MICRO-E14 GPU inference; never serves CV predictions or baseline XAI."""
import hashlib
import json
from pathlib import Path

import pandas as pd
from PIL import Image

from label_display import nama_task, tampil

ROOT = Path(__file__).resolve().parent.parent
PACKAGE = ROOT / '06_models/micro-e14-qlora-v1'
VERSION = 'micro-e14-qlora-v1'
BACKEND = 'micro-e14-qlora'
TASKS = ('task1_issue', 'task2_domain_sumber', 'task3_primary_entity_type')


class E14Unavailable(RuntimeError):
    pass


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def build_prompt(contract, task, headline, supporting, context):
    """Byte-equivalent to locked CV worker, including truncation and ordering."""
    definitions = contract['definitions']
    classes = sorted(definitions[task])
    common = (
        'Analisis sampul majalah Tempo tanpa memakai label anotasi. '
        f'Judul: {headline}. Teks pendukung: {supporting}. '
        f"Deskripsi visual: {context['deskripsi'][:1000]}. "
        f"Observasi sumber visual: {(context.get('sumber_visual') or '')[:250]}. "
        f"Alasan visual: {(context.get('alasan') or '')[:500]}."
    )
    options = '\n'.join(f'{letter}: {label}: {definitions[task][label]}'
                        for letter, label in zip('ABCDEFGHIJ', classes))
    question = {
        'task1_issue': 'Pilih isu utama yang paling dominan.',
        'task2_domain_sumber': 'Pilih domain SUMBER metafora visual-verbal, bukan isu politiknya.',
        'task3_primary_entity_type': 'Pilih tipe entitas yang menjadi sasaran atau fokus kritik utama.',
    }[task]
    return f'{common}\n{question}\n{options}\nJawab tepat satu kode huruf:'


class MicroE14Engine:
    def __init__(self, package=PACKAGE):
        self.package = Path(package)
        self.contract = json.loads((self.package/'contract.json').read_text())
        self.df = pd.read_csv(ROOT/'03_data/DATASET_740_TASK2_DOMAIN.csv').fillna('')
        self.maps = {t:sorted(self.contract['definitions'][t]) for t in TASKS}
        self.contexts = json.loads((self.package/'visual_context.json').read_text())
        self.model = None
        self.ready = False
        self.reason = 'Checkpoint deployment belum dikumpulkan dan diverifikasi.'
        self._load()

    def _load(self):
        try:
            # Integrity validation is required before importing/loading large GPU code.
            result_path = self.package/'result.json'
            if not result_path.exists():
                raise E14Unavailable(self.reason)
            result = json.loads(result_path.read_text())
            if result.get('status') != 'complete' or result.get('version') != VERSION:
                raise E14Unavailable('Identitas checkpoint deployment tidak sah.')
            if result['protocol_sha256'] != sha(self.package/'contract.json'):
                raise E14Unavailable('Checksum kontrak deployment tidak cocok.')
            if result['data_sha256'] != sha(ROOT/'03_data/DATASET_740_TASK2_DOMAIN.csv'):
                raise E14Unavailable('Checksum dataset deployment tidak cocok.')
            assets = json.loads((self.package/'assets_manifest.json').read_text())
            for name in ('contract.json', 'visual_context.json'):
                if sha(self.package/name) != assets['files'][name]:
                    raise E14Unavailable('Checksum input visual/kontrak tidak cocok.')
            if set(self.contexts) != set(self.df.sample_id) or result['classes'] != self.maps:
                raise E14Unavailable('Identitas sampel/kelas deployment tidak cocok.')
            if result['train_samples'] != 740 or result['epochs'] != self.contract['epochs']:
                raise E14Unavailable('Resep refit deployment tidak cocok.')
            audit_path = self.package/'input_audit.jsonl'
            if sha(audit_path) != result['input_audit_sha256']:
                raise E14Unavailable('Checksum audit input tidak cocok.')
            audits = [json.loads(line) for line in audit_path.read_text().splitlines()]
            if len(audits) != 2220 or {(r['sample_id'],r['task']) for r in audits} != {(sid,t) for sid in self.df.sample_id for t in TASKS}:
                raise E14Unavailable('Audit 740 sampel/tiga task tidak lengkap.')
            self.image_hashes = {r['sample_id']:r['image_sha256'] for r in audits}
            for name, expected in result['artifacts'].items():
                path = self.package/name
                if path.resolve().parent != (self.package/'adapter').resolve() or sha(path) != expected:
                    raise E14Unavailable('Checksum adapter deployment tidak cocok.')
            for name in ('adapter/adapter_config.json', 'adapter/adapter_model.safetensors'):
                if name not in result['artifacts']:
                    raise E14Unavailable('Manifest adapter tidak lengkap.')
            import torch
            if not torch.cuda.is_available():
                raise E14Unavailable('CUDA GPU tidak tersedia; Qwen3-VL 8B NF4 belum dapat dijalankan di perangkat ini.')
            from transformers import AutoModelForImageTextToText, AutoProcessor, BitsAndBytesConfig
            from peft import PeftModel, prepare_model_for_kbit_training
            self.torch = torch
            model, revision = self.contract['model'], self.contract['revision']
            self.processor = AutoProcessor.from_pretrained(model, revision=revision,
                                                           min_pixels=128*128, max_pixels=384*384)
            self.processor.tokenizer.padding_side = 'left'
            quant = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type='nf4',
                                      bnb_4bit_use_double_quant=True, bnb_4bit_compute_dtype=torch.float16)
            base = AutoModelForImageTextToText.from_pretrained(model, revision=revision,
                       quantization_config=quant, dtype=torch.float16, device_map={'':0}, attn_implementation='sdpa')
            base = prepare_model_for_kbit_training(base, use_gradient_checkpointing=False)
            self.model = PeftModel.from_pretrained(base, self.package/'adapter', is_trainable=False)
            self.model.eval()
            self.code_ids = {}
            for t in TASKS:
                ids = [self.processor.tokenizer.encode(c, add_special_tokens=False) for c in 'ABCDEFGHIJ'[:len(self.maps[t])]]
                if not all(len(v) == 1 for v in ids) or len({v[0] for v in ids}) != len(ids):
                    raise E14Unavailable('Pemetaan token kelas tidak sah.')
                self.code_ids[t] = torch.tensor([v[0] for v in ids], device='cuda:0')
            self.ready, self.reason = True, ''
            # "ready" requires an actual prediction, not just successful imports.
            sample = self.df.iloc[0]
            smoke = self.predict_image(ROOT/'05_gambar'/Path(sample.image_path).name,
                                       sample.headline_verified, sample.supporting_text_verified, sample.sample_id)
            for task in TASKS:
                actual = {p['kelas']:p['prob'] for p in smoke[task]['semua']}
                expected = result['smoke']['probabilities'][task][0]
                if max(abs(actual[label]-value) for label,value in zip(self.maps[task],expected)) > 1e-3:
                    raise E14Unavailable('Smoke inferensi runtime berbeda dari checkpoint Kaggle; model tidak diaktifkan.')
        except Exception as e:
            self.model = None
            self.ready = False
            self.reason = str(e) if isinstance(e, E14Unavailable) else f'Pemuatan model gagal ({type(e).__name__}); periksa log server.'
            if not isinstance(e, E14Unavailable):
                import traceback
                traceback.print_exc()

    def description(self):
        return dict(backend=BACKEND, version=VERSION, ready=self.ready, unavailable_reason=self.reason,
                    architecture={'model':self.contract['model'], 'encoder_training':'shared joint LoRA; three prompted objectives'},
                    tasks=list(TASKS), capabilities={'prediction':self.ready, 'visual_xai':False, 'text_xai':False,
                    'new_upload':False, 'dataset_prediction':self.ready},
                    evaluation={'protocol':'MICRO-E14 historical five-fold OOF, NOT all-data deployment benchmark',
                    'samples':740, 'macro_f1':dict(zip(TASKS, [.6733214996531947,.5102816959701791,.5954802971709425])),
                    'micro_f1':dict(zip(TASKS, [.7202702702702702,.5662162162162162,.6675675675675675])),
                    'deployment':'Not Evaluated'},
                    limitation='Dataset refit seluruh 740: in-sample, bukan OOF. Edit teks memakai konteks visual E01 historis, belum dievaluasi. XAI E14 belum diimplementasikan. Unggahan baru ditolak karena fitur visual E01 belum tersedia; tidak ada fallback CLIP.')

    def predict_image(self, image_path, headline, supporting, sample_id, cancel=lambda:None):
        if not self.ready:
            raise E14Unavailable(self.reason)
        if sample_id not in self.contexts:
            raise E14Unavailable('Unggahan baru belum didukung E14: deskripsi dan alasan visual E01 belum tersedia. Tidak memakai input kosong/fallback.')
        if sha(image_path) != self.image_hashes[sample_id]:
            raise E14Unavailable('Gambar berbeda dari input dataset E14 terverifikasi.')
        torch = self.torch
        with Image.open(image_path) as original:
            image = original.convert('RGB')
            image.thumbnail((384,384))
        results = {}
        for task in TASKS:
            cancel()
            prompt = build_prompt(self.contract, task, headline, supporting, self.contexts[sample_id])
            messages = [{'role':'user', 'content':[{'type':'image', 'image':image}, {'type':'text','text':prompt}]}]
            inputs = self.processor.apply_chat_template(messages, tokenize=True, add_generation_prompt=True,
                                                         return_dict=True, return_tensors='pt')
            if inputs['input_ids'].shape[1] > 2048:
                raise E14Unavailable('Input melebihi batas 2048 token protokol E14; pendekkan teks.')
            inputs = {k:v.to('cuda:0') for k,v in inputs.items()}
            with torch.inference_mode(), torch.autocast('cuda', dtype=torch.float16):
                out = self.model(**inputs, logits_to_keep=1, use_cache=False, return_dict=True)
            scores = out.logits[:,-1,:].index_select(-1,self.code_ids[task]).float()
            if not torch.isfinite(scores).all():
                raise E14Unavailable('Model menghasilkan skor tidak finite.')
            probabilities = scores.softmax(-1).cpu().numpy()[0]
            order = probabilities.argsort()[::-1]
            label = self.maps[task][int(order[0])]
            results[task] = dict(nama_task=nama_task(task), nama_task_mudah=nama_task(task),
                prediksi=label, prediksi_tampil=tampil(label), probabilitas=float(probabilities[order[0]]),
                semua=[dict(kelas=self.maps[task][int(i)], kelas_tampil=tampil(self.maps[task][int(i)]), prob=float(probabilities[i])) for i in order],
                backend=BACKEND, model_version=VERSION, score_kind='class_token_softmax_uncalibrated',
                score_label='Softmax token kelas (belum dikalibrasi)', evaluation_mode='dataset all740 deployment refit; in-sample, not OOF',
                evaluation=self.description()['evaluation'], prompt_sha256=hashlib.sha256(prompt.encode()).hexdigest())
        return results
