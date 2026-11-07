"""Versioned identity for the single joint three-task CLIP–IndoBERT model."""
import json
from pathlib import Path
from xai_core import XAIEngine, TASKS

class MTLDeliveryEngine(XAIEngine):
    def __init__(self):
        super().__init__()
        self.manifest=json.loads((Path(__file__).resolve().parent.parent/'06_models/clip-indobert-mtl-v1/manifest.json').read_text())
        self.evaluation_mode='all740 head refit'

    def set_context(self,image_path,headline,supporting,img_feat,sample_id=None,batch=False,cancel=None):
        if cancel: cancel()
        self.evaluation_mode=('dataset batch; all740 in-sample' if batch else 'dataset original/edit; leave-one-out head refit') if sample_id else 'new upload; all740 head refit; no reference label'

    def predict_vector(self,x):
        result=super().predict_vector(x)
        for task,pred in result.items():
            pred.update(backend=self.manifest['backend'], model_version=self.manifest['version'],
                score_kind='softmax_uncalibrated',score_label='Skor softmax (belum dikalibrasi)',
                evaluation_mode=self.evaluation_mode,
                evaluation={'protocol':self.manifest['evaluation']['protocol'],'samples':740,
                            'macro_f1':self.manifest['evaluation']['macro_f1'][task]})
        return result

    def description(self):
        return dict(self.manifest,ready=True,tasks=list(TASKS),upload_pipeline='CLIP image + IndoBERT headline/supporting -> one joint MTL model; no Qwen',
                    task2={'backend':self.manifest['backend'],'version':self.manifest['version'],
                           'evaluation':{'macro_f1':self.manifest['evaluation']['macro_f1']['task2_domain_sumber'],'samples':740}})

    def xai_contract(self,task):
        if task not in TASKS: raise ValueError('Unknown task')
        return dict(model_version=self.manifest['version'],task=task,
            visual_method='absolute CLIP patch gradient x activation, penultimate transformer block, through selected MTL head',
            text_method='IndoBERT LIME/occlusion; supporting text fixed',score_kind='softmax_uncalibrated',
            limitation='Peta menunjukkan sensitivitas model, bukan bukti kausal metafora. Peta gabungan adalah rata-rata peta tiga task yang dinormalisasi; encoder beku saat pelatihan head.')
