"""Organize actual submission evidence per completed revision; no training."""
import argparse
import ast
import html
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from urllib.parse import unquote, urlsplit
import zipfile

from bs4 import BeautifulSoup
import pandas as pd
from evaluate import TASKS, sha, write_json

CSS='''body{font:16px/1.6 system-ui,sans-serif;color:#172b40;max-width:1120px;margin:32px auto;padding:24px}a{color:#075c9b}h1{line-height:1.25}.state{background:#eaf4ec;padding:16px;border-left:4px solid #39834e}.open{background:#fff5dd;padding:16px}table{border-collapse:collapse;width:100%;font-size:14px}th,td{padding:9px;border-bottom:1px solid #ddd;text-align:left;vertical-align:top;overflow-wrap:anywhere}.scroll{overflow:auto;max-height:500px}code{background:#eef2f6;padding:2px 5px}blockquote{border-left:4px solid #8096ad;margin-left:0;padding:10px 18px;background:#f4f7fb}img{max-width:100%;height:auto}.muted{color:#536675}'''


def page(title,body):
    return f'<!doctype html><html lang="id"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(title)}</title><style>{CSS}</style><main>{body}</main></html>'


def pdf_requirements(workspace):
    text=subprocess.check_output(['pdftotext','-layout',str(workspace/'revision/Daftar-Revisi-II-Pemeriksaan-Notebook-Joy.pdf'),'-'],text=True)
    heads=list(re.finditer(r'(?m)^[ \t\f]*R(\d+)\.[ \t]+[^\n]+',text));result={}
    for i,m in enumerate(heads):
        rid='R'+m[1]
        if not 18<=int(m[1])<=36:continue
        end=heads[i+1].start() if i+1<len(heads) else len(text)
        section=text[m.start():end].strip();pos=section.find('Bukti yang diserahkan.')
        evidence=section[pos:] if pos>=0 else 'Tidak ada paragraf Bukti yang diserahkan terpisah; rujuk tindakan bernomor pada bagian ini.'
        evidence=re.split(r'\n\s*Bagian [ABC]\.',evidence)[0]
        source_page=text.count('\f',0,m.start()+m[0].index(rid))+1
        result[rid]=dict(page=source_page,requirement=' '.join(evidence.split()),section=section)
    assert set(result)=={f'R{i}' for i in range(18,37)}
    return result


class Evidence:
    def __init__(self,package,workspace):
        self.root=Path(package).resolve();self.workspace=Path(workspace).resolve()
        self.base=self.root/'BUKTI_PER_REVISI';assert not self.base.exists()
        self.base.mkdir();self.tracker=pd.read_csv(self.root/'documentation/REVISION_TRACKER_28.csv').fillna('')
        self.done=set(self.tracker.loc[self.tracker.status.eq('Selesai'),'revision_id']);assert len(self.done)==19
        self.items={rid:[] for rid in self.done};self.notes={rid:[] for rid in self.done}
        self.requests=pdf_requirements(self.workspace)
        for rid in self.done:(self.base/rid).mkdir()
        for path in (self.root/'notebook_html').glob('*.html'):
            target=self.base/'REFERENSI_NOTEBOOK'/path.name;target.parent.mkdir(exist_ok=True);shutil.copy2(path,target)
        target=self.base/'SUMBER/Daftar-Revisi-II-Pemeriksaan-Notebook-Joy.pdf';target.parent.mkdir()
        shutil.copy2(self.workspace/'revision'/target.name,target)

    def record(self,rid,target,purpose,**extra):
        assert rid in self.done and target.is_file()
        item=dict(file=str(target.relative_to(self.base/rid)),purpose=purpose,sha256=sha(target),**extra)
        self.items[rid].append(item);return target

    def copy(self,rid,source,name,purpose):
        p=self.root/source;assert p.is_file(),p
        target=self.base/rid/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
        return self.record(rid,target,purpose,kind='copy',source=source,source_sha256=sha(p))

    def doc(self,rid,name,purpose):
        destination=name if name.startswith(rid+'_') else rid+'_'+name
        return self.copy(rid,'documentation/'+name,destination,purpose)

    def table(self,rid,source,name,purpose,experiments=None,task=None,pairs=None):
        full=pd.read_csv(self.root/source);frame=full
        selector={}
        if experiments is not None:selector['experiments']=experiments;frame=frame[frame.experiment.isin(experiments)]
        if task is not None:selector['task']=task;frame=frame[frame.task.eq(task)]
        if pairs is not None:
            selector['pairs']=pairs;chosen={tuple(p) for p in pairs}
            frame=frame[[pair in chosen for pair in zip(frame.before,frame.after)]]
        assert len(frame)>0,(rid,name,selector)
        target=self.base/rid/name;frame.to_csv(target,index=False)
        self.record(rid,target,purpose,kind='table_subset',source=source,source_sha256=sha(self.root/source),selector=selector,rows=len(frame))
        return frame

    def text(self,rid,name,text,purpose,source=None):
        target=self.base/rid/name;target.write_text(text)
        return self.record(rid,target,purpose,kind='excerpt' if source else 'explanatory_note',**({'source':source,'source_sha256':sha(self.root/source)} if source else {}))

    def source(self,rid,name,purpose):
        source='source/DEMO_XAI_745_FULL/01_notebook/'+name
        return self.copy(rid,source,Path(name).name,purpose)

    def metrics(self,rid,models,name=None):
        return self.table(rid,'analysis/metrics.csv',name or rid+'_metrik_per_task.csv','Macro-F1 utama, akurasi, precision/recall, kappa, CI dan scope per task',experiments=models)

    def paired(self,rid,pairs):
        return self.table(rid,'analysis/paired_tests.csv',rid+'_uji_berpasangan.csv','Exact McNemar/Holm untuk akurasi dan CI bootstrap selisih Macro-F1; arah before→after dipertahankan',pairs=pairs)

    def fill(self):
        self.copy('R18','documentation/candidate_mapping_36.csv','R18_pemetaan_36_kandidat.csv','Tabel pemetaan 36 kandidat yang diminta PDF')
        for name in ['MAIN_MODEL_DECISION.md','R18_ARSITEKTUR_JOINT_LOSS.md','R18_ARCHITECTURE_AUDIT.json']:
            self.doc('R18',name,'Penetapan model, arsitektur/Joint Loss dan konfigurasi checkpoint per fold')
        for name in ['current_20261102_r18_notebook02.png','current_20261102_joint_loss.png','r18_source_page_05.png']:
            self.copy('R18','screenshots/'+name,name,'Bukti visual permintaan/perbaikan R18; bukan bukti Run all Colab')
        rank=self.table('R19','analysis/ranking_36_legacy.csv','R19_peringkat_ganda_36_kandidat.csv','Peringkat akurasi minimum, Macro-F1 minimum dan mean Macro-F1 untuk 36 nama')
        self.copy('R19','analysis/ranking_all.csv','R19_peringkat_seluruh_sumber.csv','Seluruh comparator/kontrol dengan samples dan phase tetap terlihat')
        self.copy('R19','analysis/rank_correlation.json','R19_korelasi_peringkat.json','Pearson dan Spearman yang dihitung ulang dengan ties')
        worst=rank.loc[rank.rank_shift_macro_minus_accuracy.idxmax()]
        self.text('R19','R19_analisis_pembalikan_peringkat.md',f'''# Analisis pembalikan peringkat

Pada 36 nama kandidat historis, {worst.experiment} berada di peringkat {int(worst.rank_minimum_accuracy)} menurut minimum akurasi, tetapi menjadi peringkat {int(worst.rank_minimum_macro)} menurut minimum Macro-F1: turun {int(worst.rank_shift_macro_minus_accuracy)} posisi. Ini menunjukkan akurasi dan Macro-F1 dapat mengarahkan keputusan berbeda pada kelas timpang. Minimum dipertahankan untuk audit PDF; keputusan utama revisi memakai per-task dan mean Macro-F1 kandidat CLIP–IndoBERT yang layak. E42 dipilih post-hoc pada korpus berulang, sehingga bukan validasi eksternal. Tabel memuat alias/signature; 36 nama bukan 36 eksperimen independen. Spearman dihitung dengan tied ranks dan berbeda dari angka 0,050 dalam PDF; nilai aktual ada pada R19_korelasi_peringkat.json.
'''.replace('Pada36','Pada 36').replace('peringkat1','peringkat 1').replace('peringkat32','peringkat 32').replace('turun31posisi','turun 31 posisi').replace('; 36 nama bukan 36 eksperimen','; 36 nama bukan 36 eksperimen').replace('angka 0,050','angka 0,050'),'Paragraf interpretasi pembalikan peringkat berdasarkan CSV aktual')
        diag=['BASELINE_CLIP_INDoBERT','MICRO_E11_hierarchical_task3','e42_tail_grid']
        for model in diag:
            for ext in ['png','csv']:self.copy('R20',f'analysis/confusion_task3_{model}.{ext}',f'R20_confusion_{model}.{ext}','Confusion matrix Task 3 untuk diagnosis baseline/E11 dan pembanding model utama E42')
        self.table('R20','analysis/class_distribution.csv','R20_distribusi_gold_prediksi_task3.csv','Jumlah/proporsi gold versus prediksi',experiments=diag,task=TASKS[2])
        self.table('R20','analysis/task3_entropy.csv','R20_entropi_task3.csv','Entropi dan proporsi kelas mayoritas',experiments=diag)
        weighted=['RII_FROZEN_MTL_WEIGHTED','RII_FROZEN_MTL_UNWEIGHTED','RII_TAIL_MTL_WEIGHTED','RII_TAIL_MTL_UNWEIGHTED']
        self.metrics('R20',weighted,'R20_perbandingan_class_weighting.csv')
        self.paired('R20',[[weighted[0],weighted[1]],[weighted[2],weighted[3]]])
        self.doc('R20','ABLATION_PARITY.md','Batas parity: frozen dan tail adalah dua keluarga kontrol terpisah')

        for rid in ['R24','R25']:
            self.copy(rid,'analysis/metrics.csv',rid+'_seluruh_metrik_dan_ci.csv','Tabel lengkap 231 baris; phase dan samples membedakan OOF 740, subset dan zero-shot')
            self.doc(rid,'STATISTICAL_METHOD.md','Definisi metrik, CI dan scope statistik')
        self.copy('R24','analysis/per_class.csv','R24_metrik_per_kelas.csv','Metrik per kelas dengan codebook tetap')
        self.copy('R24','tools/evaluate.py','evaluate.py','Evaluator revisi canonical; pengganti peran results.py/analysis.py pada paket lama')
        self.copy('R25','analysis/paired_tests.csv','R25_seluruh_uji_berpasangan.csv','Seluruh 156 uji task/pasangan, koreksi Holm untuk akurasi dan bootstrap macro')
        self.doc('R26','SELECTION_BIAS.md','Pernyataan pilihan jalan: disclosure penggunaan ulang korpus, jumlah artefak/trial dan alasannya')
        self.copy('R26','inputs/sources.json','R26_inventaris_sumber_dan_signature.json','Daftar sumber, hash, phase, alias dan signature prediksi')
        self.text('R26','R26_keputusan_validasi.md','# Pilihan penanganan bias seleksi\n\nJalan yang dipilih adalah disclosure terbuka pada metode/abstrak/keterbatasan. Tidak dipilih klaim validasi eksternal baru. Karena itu tidak ada tabel hasil set eksternal yang dibuat atau diisi. Inventaris signature adalah jumlah artefak yang ditemukan, bukan jumlah pasti seluruh trial gagal/historis.\n','Keputusan eksplisit atas alternatif yang diminta R26')

        tail=['RII_TAIL_MTL_WEIGHTED','RII_TAIL_SINGLE_TASK'];frozen=['RII_FROZEN_MTL_WEIGHTED','RII_FROZEN_SINGLE_TASK']
        self.metrics('R27',tail+frozen)
        self.paired('R27',[tail,frozen])
        for name in ['ABLATION_PARITY.md','R18_ARSITEKTUR_JOINT_LOSS.md']:self.doc('R27',name,'Kontrak shared MTL versus tiga model independen dan definisi loss')
        worker=self.source('R27','e42_tail_grid/worker.py','Source worker E42 historis lengkap, tidak ditulis ulang sebagai training baru')
        self.source('R27','revisi_ii/tail_ablation_worker.py','Source controlled rerun MTL/single-task yang benar-benar menghasilkan prediksi baru')
        original=worker.read_text();node=next(n for n in ast.walk(ast.parse(original)) if isinstance(n,ast.FunctionDef) and n.name=='epoch')
        self.text('R27','R27_joint_loss_yang_dijalankan.py.txt',f'# Kutipan verbatim worker.py, mulai baris {node.lineno}; SHA256 {sha(worker)}\n'+ast.get_source_segment(original,node)+'\n','Potongan fungsi epoch/Joint Loss aktual',source='source/DEMO_XAI_745_FULL/01_notebook/e42_tail_grid/worker.py')

        baseline=[('01_majority','MAJORITY_TRAIN_FOLD'),('02_image_only','RII_FROZEN_IMAGE_ONLY'),('03_text_supporting','RII_FROZEN_TEXT_SUPPORTING'),('04_multimodal','RII_FROZEN_MTL_WEIGHTED')]
        for folder,model in baseline:self.copy('R28',f'inputs/predictions/{model}.csv',folder+'/predictions.csv','Satu dari empat prediksi canonical baseline; 740 ID × tiga task, model='+model)
        for folder,model in [('01_multimodal','RII_TAIL_MTL_WEIGHTED'),('02_image_only','RII_TAIL_IMAGE_ONLY'),('03_text_supporting','RII_TAIL_TEXT_SUPPORTING'),('04_majority','MAJORITY_TRAIN_FOLD')]:
            self.copy('R28',f'inputs/predictions/{model}.csv','kontrol_tail_tambahan/'+folder+'/predictions.csv','Kontrol E42-family pada resep baru yang diberi label terpisah; model='+model)
        self.copy('R28','inputs/predictions/e42_tail_grid.csv','model_utama_historis/predictions.csv','Referensi OOF model utama historis E42; bukan hasil ablation resep baru')
        self.metrics('R28',[m for _,m in baseline]+['RII_TAIL_MTL_WEIGHTED','RII_TAIL_IMAGE_ONLY','RII_TAIL_TEXT_SUPPORTING'])
        self.paired('R28',[[baseline[3][1],baseline[1][1]],[baseline[3][1],baseline[2][1]],['RII_TAIL_MTL_WEIGHTED','RII_TAIL_IMAGE_ONLY'],['RII_TAIL_MTL_WEIGHTED','RII_TAIL_TEXT_SUPPORTING']])
        for name in ['HISTORICAL_REPLAY.md','ABLATION_PARITY.md']:self.doc('R28',name,'Baseline direplay identik; keluarga frozen dan E42-tail tidak disamakan')

        backbones=['RII_BACKBONE_CLIP_FULL','RII_BACKBONE_SIGLIP2','RII_BACKBONE_DINOV2']
        self.metrics('R29',backbones+['M01_clip_indobert','M02_siglip2_indobert','M03_dinov2_indobert','M04_siglip2_adapters'])
        self.paired('R29',[[backbones[0],backbones[1]],[backbones[0],backbones[2]],['M01_clip_indobert','M02_siglip2_indobert']])
        for name in ['ABLATION_PARITY.md','MAIN_MODEL_DECISION.md']:self.doc('R29',name,'Varian CLIP ViT-L14 utama dan perbedaan parity antar keluarga')
        self.source('R29','revisi_ii/train_backbone_controls.py','Source kontrol backbone dengan dimensi head/input yang setara')

        for name in ['AUGMENTATION_AUDIT.md','ABLATION_PARITY.md']:self.doc('R30',name,'Alasan pemilihan AUG_SELECTED memakai inner fold dan batas perbandingan')
        for name in ['protocol.json','completion.json']:
            self.copy('R30','experiment_protocols/augmentation/'+name,'R30_'+name,'Protokol/status rerun tanpa rotasi yang tersimpan')
        legacy=self.source('R30','next_research_20261017/kaggle_a01_a03/launch.py','Worker augmentasi historis sebagai sumber transform dan perbandingan rotasi')
        self.source('R30','revisi_ii/augmentation_controls.py','Source ekstraksi ulang dan pemilihan pipeline inner pada revisi')
        proto=json.loads((self.root/'experiment_protocols/augmentation/protocol.json').read_text())
        actual=self.workspace/'DEMO_XAI_745_FULL/04_hasil_eksperimen/revisi_ii/augmentation/moderate_no_rotation.py'
        assert sha(legacy)==proto['legacy_augmentation_source_sha256'] and sha(actual)==proto['transform_source_sha256']
        target=self.base/'R30/moderate_no_rotation.py';shutil.copy2(actual,target)
        self.record('R30',target,'Fungsi transform aktual pada rerun, hash cocok dengan protocol.json',kind='verified_workspace_copy',source=str(actual.relative_to(self.workspace)),source_sha256=sha(actual))
        self.text('R30','R30_parameter_dan_back_translation.md','''# Parameter augmentasi dan catatan pemeriksaan

| Arm baru | Brightness | Contrast | JPEG quality | Noise Gaussian σ | Rotasi | Sampling |
|---|---|---|---|---|---|---|
| A00 clean | tidak diubah | tidak diubah | tidak direkompresi augmentasi | 0 | 0 | n training draws |
| A01 light | Uniform(0.92,1.08) | Uniform(0.92,1.08) | integer 88–96 | 1.5 | 0 | n draws, 50% clean/50% fixed augmentation |
| A02 moderate no rotation | Uniform(0.85,1.15) | Uniform(0.85,1.15) | integer 78–90 | 3.0 | 0; draw RNG lama tetap dikonsumsi | n draws, 50% clean/50% fixed augmentation |
| A03 light sampler | sama dengan light | sama dengan light | sama dengan light | 1.5 | 0 | replacement n draws, joint inverse-sqrt sampler |

Seluruh arm baru 35 epoch, batch 32, head 192/LN/GELU/dropout0.25 dan optimizer sama; validation/test bersih. Tidak ada geometric crop pada transform augmentasi. Resize/preprocessing encoder dibedakan dari augmentasi. Worker lama moderate memakai rotasi ±2 derajat; file moderate_no_rotation.py adalah fungsi aktual setelah rotasi dinolkan, dengan hash cocok protokol.

Pemilihan pipeline memakai mean Macro-F1 pada dua inner folds, bukan skor outer tertinggi. Karena itu AUG_SELECTED boleh lebih rendah dari A01 pada outer. Mengganti pemenang setelah melihat outer akan menggunakan test untuk seleksi. Rerun juga menyamakan jumlah update/paparan; selisih lama versus baru bukan efek rotasi tunggal.

## Status permintaan 30 contoh back-translation
**Tidak berlaku pada pipeline yang dijalankan: back-translation tidak digunakan.** Tidak ada 30 hasil back-translation untuk dinilai. Source/protokol disertakan supaya keputusan ini dapat diperiksa. Tidak dibuat terjemahan baru dan tidak diklaim sebagai 30 pemeriksaan manusia historis. Jika back-translation ditambahkan pada versi berikutnya, audit manusia harus dilakukan sebelum hasilnya dipakai.
''','Parameter aktual tiap arm dan penjelasan eksplisit tidak berlakunya pemeriksaan back-translation')
        aug=['RII_A00_CLEAN','RII_A01_LIGHT','RII_A02_MODERATE_NO_ROTATION','RII_A03_LIGHT_SAMPLER','RII_AUG_SELECTED_INNER']
        self.metrics('R30',aug+['A00_none','A01_light','A02_moderate','A03_light_sampler','AUG_SELECTED'])
        self.paired('R30',[[aug[0],n] for n in aug[1:]])
        self.copy('R30','experiment_protocols/experiments/RII_AUG_SELECTED_INNER/result.json','R30_seleksi_inner_per_fold.json','Keputusan pipeline dan seluruh metadata fold aktual')

        for name in ['MANUSKRIP_DRAF.md','HASIL_DAN_TANGGAPAN.md','MAIN_MODEL_DECISION.md','SELECTION_BIAS.md']:
            self.doc('R33',name,'Draf pembingkaian, hasil aktual dan disclosure keterbatasan; belum persetujuan jurnal')
        self.metrics('R33',['e42_tail_grid','BASELINE_CLIP_INDoBERT','MAJORITY_TRAIN_FOLD','MICRO_E14_joint_qlora_oof'])
        for name in ['STATISTICAL_METHOD.md','MAIN_MODEL_DECISION.md','MANUSKRIP_DRAF.md']:
            self.doc('R35',name,'Kriteria komparatif dan target proposal historis; tanpa gate 0,70 dalam keputusan baru')
        for name in ['MANUSKRIP_DRAF.md','REFERENCES.md','SELECTION_BIAS.md']:self.doc('R36',name,'Keterbatasan, etika dan sitasi primer yang tersedia dalam draf')
        for name in ['CODEBOOK_REVISI.md','TASK_DEFINITIONS.json']:self.doc('R2',name,'Definisi operasional label tiga task dan kelas penampung; bukan hasil adjudikasi manusia baru')
        self.table('R2','analysis/catchall_sensitivity.csv','R2_sensitivitas_kelas_penampung.csv','Sensitivitas eksplisit; primary tetap semua kelas',experiments=['e42_tail_grid','BASELINE_CLIP_INDoBERT','MICRO_E14_joint_qlora_oof'])
        self.notes['R2'].append('Definisi codebook selesai secara teknis. Audit 60 sampul dan adjudikasi manusia tetap tercatat pada R31 yang terbuka.')
        for name in ['XAI_METHOD.md','MAIN_MODEL_DECISION.md']:self.doc('R4',name,'Kelayakan attention rollout untuk CLIP ViT-L14 dan sifat class-agnostic')
        self.source('R4','revisi_ii/explain_e42.py','Implementasi actual E42 rollout, LIME kondisional dan deletion')
        for p in sorted((self.root/'xai_e42').iterdir()):
            if p.is_file():self.copy('R4',str(p.relative_to(self.root)),'xai_e42/'+p.name,'Bukti actual XAI delapan outerfold-sample, parity, hasil negatif dan kontrol')
        self.notes['R4'].append('Bukti kelayakan/implementasi metode visual tersedia. Skor lima manusia dan agreement pada R34/R9 belum tersedia. Peta rollout bukan Grad-CAM atau bukti sebab spesifik kelas.')
        self.doc('R12','STATISTICAL_METHOD.md','Penetapan Macro-F1 utama dan akurasi/kappa pendamping')
        self.copy('R12','analysis/metrics.csv','R12_seluruh_hasil_macro.csv','Seluruh tabel macro dengan scope/CI')
        self.copy('R12','tools/evaluate.py','evaluate.py','Source evaluator yang menentukan metrik')
        for name in ['STATISTICAL_METHOD.md','MAIN_MODEL_DECISION.md']:self.doc('R13',name,'Justifikasi target komparatif dan pelaporan target 0,70 sebagai sejarah proposal')
        self.doc('R16','REFERENCES.md','Daftar referensi primer beserta metadata dan hubungan dengan metode aktual')
        self.doc('R17','MANUSKRIP_DRAF.md','Etika/pembatasan penggunaan dalam konteks draf lengkap')
        draft=(self.root/'documentation/MANUSKRIP_DRAF.md').read_text()
        for rid,heading in [('R36','## Keterbatasan'),('R17','## Etika dan pembatasan penggunaan')]:
            start=draft.index(heading);end=draft.find('\n## ',start+len(heading));part=draft[start:end if end>=0 else len(draft)]
            self.text(rid,rid+'_bagian_naskah.md',part+'\n','Potongan bagian naskah untuk pemeriksaan langsung',source='documentation/MANUSKRIP_DRAF.md')

    def notebook(self,rid):
        mapping={
            'R18':('02_experiments','R18 — Arsitektur'),'R19':('03_final_comparison','Peringkat ganda'),
            'R20':('02_experiments','Task 3: distribusi'),'R24':('01_baseline','Metode evaluasi dan pelaporan'),
            'R25':('03_final_comparison','Statistik berpasangan'),'R26':('03_final_comparison','Pemakaian ulang korpus'),
            'R27':('02_experiments','MTL versus single-task'),'R28':('01_baseline','Pemulihan prediksi mentah'),
            'R29':('02_experiments','Backbone dan augmentasi'),'R30':('02_experiments','Audit augmentasi'),
            'R33':('03_final_comparison','Pembahasan, etika'),'R35':('03_final_comparison','Hasil Revisi II dan Koreksi'),
            'R36':('03_final_comparison','Keterbatasan'),'R2':('01_baseline','Codebook operasional'),
            'R4':('02_experiments','XAI model utama E42'),'R12':('01_baseline','Metode evaluasi dan pelaporan'),
            'R13':('03_final_comparison','Hasil Revisi II dan Koreksi'),'R16':('03_final_comparison','Referensi primer yang diperiksa'),
            'R17':('03_final_comparison','Etika dan pembatasan penggunaan')}
        stem,keyword=mapping[rid];p=self.base/'REFERENSI_NOTEBOOK'/f'{stem}.html'
        soup=BeautifulSoup(p.read_text(),'html.parser')
        heading=next(h for h in soup.find_all(['h1','h2','h3']) if h.get('id') and keyword in h.get_text(' ',strip=True))
        return dict(notebook=stem+'.ipynb',heading=heading.get_text(' ',strip=True).rstrip(' ¶'),
                    html='../REFERENSI_NOTEBOOK/'+p.name+'#'+heading['id'])

    def finish(self):
        related={'R2':'R31','R4':'R34','R12':'R24','R13':'R35','R16':'R36','R17':'R36'}
        index=[]
        for row in self.tracker.itertuples(index=False):
            if row.revision_id not in self.done:
                index.append(dict(revision_id=row.revision_id,title=row.title,status=row.status,folder='',files=0,remaining=row.remaining));continue
            rid=row.revision_id;items=self.items[rid];assert items
            request=self.requests.get(rid)
            if request is None:
                target=related[rid];request=dict(page=self.requests[target]['page'],requirement=f'Butir Agustus: {row.title}. Rujukan permintaan pada tabel/ringkasan Revisi II dan bagian terkait {target}; bukan kutipan dokumen Agustus asli.',section='')
            note=self.notebook(rid)
            overview=dict(revision_id=rid,title=row.title,status='Selesai teknis sesuai tracker; menunggu penilaian pembimbing',pdf_page=request['page'],requested_evidence=request['requirement'],notebook=note,notes=self.notes[rid],files=items)
            write_json(self.base/rid/'BUKTI_MANIFEST.json',overview)
            file_rows='';md_rows=[]
            for item in items:
                name=item['file'];file_rows+=f'<tr><td><a href="{html.escape(name)}">{html.escape(name)}</a></td><td>{html.escape(item["purpose"])}</td></tr>'
                md_rows.append(f'- [{name}]({name}) — {item["purpose"]}')
            notes=''.join('<p class="open">'+html.escape(n)+'</p>' for n in self.notes[rid])
            body=f'<p><a href="../INDEX.html">← Indeks semua revisi</a></p><h1>{rid} — {html.escape(row.title)}</h1><p class="state">Selesai secara teknis sesuai tracker. Materi yang tersedia bukan persetujuan pembimbing.</p><h2>Bukti yang diminta</h2><blockquote>{html.escape(request["requirement"])}</blockquote><p><a href="../SUMBER/Daftar-Revisi-II-Pemeriksaan-Notebook-Joy.pdf#page={request["page"]}">PDF sumber, halaman {request["page"]}</a></p><h2>Berkas bukti yang diserahkan</h2><table><thead><tr><th>Berkas</th><th>Kegunaan</th></tr></thead><tbody>{file_rows}</tbody></table>{notes}<h2>Lokasi pada notebook</h2><p><a href="{html.escape(note["html"])}">{html.escape(note["notebook"])} — {html.escape(note["heading"])}</a></p><p class="muted">Salinan bukti dan source/hash tercatat pada BUKTI_MANIFEST.json. File asli dalam paket lengkap dipertahankan. HTML notebook dapat dibaca tanpa training; Run all memakai paket lengkap.</p>'
            (self.base/rid/'BUKA_BUKTI.html').write_text(page(rid+' — '+row.title,body))
            (self.base/rid/'README.md').write_text(f'# {rid} — {row.title}\n\n**Status: selesai teknis sesuai tracker; bukan persetujuan pembimbing.**\n\n## Bukti yang diminta\n\n{request["requirement"]}\n\nSumber: PDF Revisi II halaman {request["page"]}.\n\n## Berkas nyata yang diserahkan\n\n'+'\n'.join(md_rows)+'\n\n## Lokasi notebook\n\n'+note['notebook']+' — '+note['heading']+'\n\n'+'\n\n'.join(self.notes[rid])+'\n\nBuka BUKA_BUKTI.html untuk navigasi. BUKTI_MANIFEST.json mencatat asal, selector CSV dan SHA256.\n')
            index.append(dict(revision_id=rid,title=row.title,status=row.status,folder=rid,files=len(items),remaining=''))
        pd.DataFrame(index).to_csv(self.base/'INDEKS_28_REVISI.csv',index=False)
        body='<h1>Bukti per revisi — Joy</h1><p class="state"><strong>19 folder bukti selesai teknis · 9 butir masih terbuka.</strong> Klik nomor R untuk melihat berkas nyata, permintaan PDF dan lokasi notebook.</p><p>Untuk pemeriksaan Joy/pembimbing. Penilaian manusia tetap memakai paket penilai terpisah. Data hasil tidak diubah dalam penataan folder ini.</p><table><thead><tr><th>Butir</th><th>Permintaan</th><th>Status</th><th>Berkas</th></tr></thead><tbody>'
        for r in index:
            link=r['folder']+'/BUKA_BUKTI.html' if r['folder'] else 'BELUM_SELESAI.md#'+r['revision_id'].lower()
            body+=f'<tr><td><a href="{link}">{r["revision_id"]}</a></td><td>{html.escape(r["title"])}</td><td>{r["status"]}</td><td>{r["files"]}</td></tr>'
        body+='</tbody></table><p><a href="BELUM_SELESAI.md">Rincian bukti yang belum tersedia</a> · <a href="INDEKS_28_REVISI.csv">Indeks CSV</a></p>'
        (self.base/'INDEX.html').write_text(page('Bukti per revisi Joy',body))
        (self.base/'BELUM_SELESAI.md').write_text('# Butir yang belum ditutup\n\nSembilan butir ini tidak diberi folder seolah buktinya sudah lengkap. Status dan alasan mengikuti tracker canonical.\n\n'+'\n\n'.join(f'## {r.revision_id}\n\n{r.title}\n\n{r.remaining}' for r in self.tracker.itertuples() if r.status!='Selesai')+'\n')
        (self.base/'README.md').write_text('# Bukti per revisi\n\nBuka **INDEX.html**, lalu folder R18, R19, dan seterusnya. Ada 19 folder untuk 19 butir selesai teknis. Setiap folder memuat file bukti nyata, README, BUKA_BUKTI.html dan BUKTI_MANIFEST.json. INDEKS_28_REVISI.csv juga mencantumkan 9 butir terbuka beserta alasannya.\n\nREFERENSI_NOTEBOOK berisi tiga HTML notebook dengan output tersimpan, dan SUMBER berisi PDF revisi asli. ZIP bukti ini untuk membaca/memeriksa hasil; menjalankan ulang analisis atau model memakai paket lengkap. Hash/asal file dan selector tabel disertakan supaya bukti bisa ditelusuri.\n\nStatus Selesai berarti materi teknis tersedia, bukan persetujuan pembimbing atau penilaian manusia baru. Untuk R30, permintaan 30 back-translation dijawab dengan penjelasan tidak berlaku karena metode tidak digunakan; tidak ada 30 contoh buatan. R23 mengikuti klarifikasi Joy: alasan kualitas citra sudah disampaikan, sedangkan kappa tetap membutuhkan dua anotasi independen.\n')
        return index


def verify(package):
    root=Path(package).resolve();base=root/'BUKTI_PER_REVISI'
    tracker=pd.read_csv(root/'documentation/REVISION_TRACKER_28.csv').fillna('')
    done=set(tracker.loc[tracker.status.eq('Selesai'),'revision_id'])
    assert done=={p.name for p in base.iterdir() if p.is_dir() and re.fullmatch(r'R\d+',p.name)}
    index=pd.read_csv(base/'INDEKS_28_REVISI.csv').fillna('')
    assert len(index)==index.revision_id.nunique()==28 and set(index[index.status.eq('Selesai')].revision_id)==done
    file_count=0;subsets=0
    for rid in done:
        m=json.loads((base/rid/'BUKTI_MANIFEST.json').read_text())
        for item in m['files']:
            target=(base/rid/item['file']).resolve();assert target.is_relative_to(base/rid) and target.is_file()
            assert sha(target)==item['sha256'];file_count+=1
            if item['kind']=='copy':assert sha(root/item['source'])==item['source_sha256']==item['sha256']
            if item['kind']=='table_subset':
                src=root/item['source'];assert sha(src)==item['source_sha256'];expect=pd.read_csv(src);sel=item['selector']
                if 'experiments' in sel:expect=expect[expect.experiment.isin(sel['experiments'])]
                if 'task' in sel:expect=expect[expect.task.eq(sel['task'])]
                if 'pairs' in sel:
                    pairs={tuple(p) for p in sel['pairs']};expect=expect[[p in pairs for p in zip(expect.before,expect.after)]]
                actual=pd.read_csv(target)
                pd.testing.assert_frame_equal(actual.reset_index(drop=True),expect.reset_index(drop=True),check_exact=False,rtol=1e-12,atol=1e-14)
                assert len(actual)==item['rows']>0;subsets+=1
    for rid,name in [('R18','R18_pemetaan_36_kandidat.csv'),('R19','R19_peringkat_ganda_36_kandidat.csv')]:
        d=pd.read_csv(base/rid/name);assert len(d)==d.experiment.nunique()==36
    baseline=sorted((base/'R28').glob('0*/predictions.csv'));assert len(baseline)==4
    reference=pd.read_csv(root/'inputs/DATASET_740_TASK2_DOMAIN.csv').set_index('sample_id')
    folds=pd.read_csv(root/'inputs/folds.csv').set_index('sample_id')['fold']
    for p in (base/'R28').rglob('predictions.csv'):
        d=pd.read_csv(p);assert len(d)==d.sample_id.nunique()==740
        assert set(d.sample_id)==set(reference.index) and d.fold.tolist()==folds.loc[d.sample_id].tolist()
        for t in TASKS:assert d[t+'_truth'].tolist()==reference.loc[d.sample_id,t].tolist()
    links=0
    for p in [base/'INDEX.html',*[base/r/'BUKA_BUKTI.html' for r in done]]:
        soup=BeautifulSoup(p.read_text(),'html.parser')
        for tag in soup.find_all(['a','img']):
            value=tag.get('href') if tag.name=='a' else tag.get('src')
            if not value:continue
            url=urlsplit(value)
            if url.scheme:continue
            target=(p.parent/unquote(url.path)).resolve();assert target.is_relative_to(base) and target.is_file(),(p,value)
            if url.fragment and target.suffix=='.html':
                ids={n.get('id') for n in BeautifulSoup(target.read_text(),'html.parser').find_all(id=True)}
                assert url.fragment in ids or unquote(url.fragment) in ids,(target,url.fragment)
            links+=1
    result=dict(status='verified',completed_folders=len(done),open_revisions=int((tracker.status!='Selesai').sum()),index_rows=28,evidence_files=file_count,canonical_subset_tables=subsets,local_links_checked=links,r18_mapping_rows=36,r19_ranking_rows=36,r28_primary_prediction_files=4,r28_samples_per_file=740,metrics_or_labels_changed=False)
    write_json(base/'VERIFIKASI_BUKTI.json',result)
    return result


def seal_evidence(base,archive):
    assert not archive.exists()
    files={str(p.relative_to(base)):sha(p) for p in sorted(base.rglob('*')) if p.is_file() and p.name!='MANIFEST_SHA256.json'}
    write_json(base/'MANIFEST_SHA256.json',dict(files=files))
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in sorted(base.rglob('*')):
            if p.is_file():z.write(p,Path('BUKTI_PER_REVISI')/p.relative_to(base))
    with zipfile.ZipFile(archive) as z:assert z.testzip() is None
    archive.with_suffix('.zip.sha256').write_text(f'{sha(archive)}  {archive.name}\n')


def verify_standalone_zip(archive):
    """Check the lightweight archive after extraction, without the full package."""
    archive=Path(archive).resolve()
    assert sha(archive)==archive.with_suffix('.zip.sha256').read_text().split()[0]
    with tempfile.TemporaryDirectory(prefix='joy-evidence-zip-') as folder:
        directory=Path(folder)
        with zipfile.ZipFile(archive) as z:
            assert len(z.namelist())==len(set(z.namelist())) and z.testzip() is None
            for name in z.namelist():assert (directory/name).resolve().is_relative_to(directory)
            z.extractall(directory)
        base=directory/'BUKTI_PER_REVISI'
        manifest=json.loads((base/'MANIFEST_SHA256.json').read_text())['files']
        for name,digest in manifest.items():assert sha(base/name)==digest,name
        folders=[p for p in base.iterdir() if p.is_dir() and re.fullmatch(r'R\d+',p.name)]
        assert len(folders)==19
        links=0
        for p in [base/'INDEX.html',*[r/'BUKA_BUKTI.html' for r in folders]]:
            for tag in BeautifulSoup(p.read_text(),'html.parser').find_all(['a','img']):
                value=tag.get('href') if tag.name=='a' else tag.get('src')
                if not value:continue
                url=urlsplit(value)
                if url.scheme:continue
                target=(p.parent/unquote(url.path)).resolve()
                assert target.is_relative_to(base) and target.is_file(),value
                if url.fragment and target.suffix=='.html':
                    ids={n.get('id') for n in BeautifulSoup(target.read_text(),'html.parser').find_all(id=True)}
                    assert url.fragment in ids or unquote(url.fragment) in ids
                links+=1
        return dict(status='verified_standalone_extraction',archive_sha256=sha(archive),bytes=archive.stat().st_size,
                    completed_folders=len(folders),hash_files=len(manifest),local_links_checked=links,requires_full_package_for_reading=False)


def build(source,destination,workspace,archive):
    source=Path(source).resolve();root=Path(destination).resolve();assert source!=root and not root.exists()
    shutil.copytree(source,root,ignore=shutil.ignore_patterns('__pycache__'))
    (root/'MANIFEST_SHA256.json').rename(root/'qa/MANIFEST_R1_REFERENCE.json')
    (root/'qa/RELEASE_QA_SCOPE.json').rename(root/'qa/RELEASE_QA_SCOPE_R1_REFERENCE.json')
    obj=Evidence(root,Path(workspace).resolve());obj.fill();obj.finish();result=verify(root)
    seal_evidence(obj.base,Path(archive).resolve())
    p=root/'BUKA_DULU.md';p.write_text(p.read_text()+'\n## R2 — bukti per revisi\n\nBuka `BUKTI_PER_REVISI/INDEX.html` untuk folder R18, R19, dan seterusnya. Setiap folder berisi bukti nyata sesuai permintaan PDF, panduan dan lokasi notebook. 19 folder mengikuti 19 butir selesai teknis; 9 butir terbuka tetap terdaftar dengan alasan dan tidak diberi status selesai.\n')
    p=root/'MULAI_DI_SINI.html';s=p.read_text().replace('<h1>Notebook, bukti eksperimen','<p><a href="BUKTI_PER_REVISI/INDEX.html"><strong>R2 — buka folder bukti untuk setiap revisi: R18, R19, dan seterusnya</strong></a></p><h1>Notebook, bukti eksperimen',1);p.write_text(s)
    checked=[]
    for folder in ['inputs','analysis','notebooks','notebook_html','lampiran_model']:
        for p in (source/folder).rglob('*'):
            if p.is_file():assert sha(p)==sha(root/p.relative_to(source)),str(p);checked.append(str(p.relative_to(source)))
    result['unchanged_core_files']=len(checked)
    result['previous_release']=str(source)
    result['note']='R2 changes evidence organization only; R1 notebook Run all evidence applies to byte-identical notebooks/data/analysis. No new Colab or human evaluation claim.'
    write_json(root/'qa/EVIDENCE_FOLDER_VERIFICATION.json',result)
    write_json(root/'qa/RELEASE_QA_SCOPE.json',result)
    print(json.dumps(result,indent=2));return root


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--source-package',required=True,type=Path);ap.add_argument('--destination',required=True,type=Path);ap.add_argument('--workspace',required=True,type=Path);ap.add_argument('--evidence-archive',required=True,type=Path)
    args=ap.parse_args();build(args.source_package,args.destination,args.workspace,args.evidence_archive)
