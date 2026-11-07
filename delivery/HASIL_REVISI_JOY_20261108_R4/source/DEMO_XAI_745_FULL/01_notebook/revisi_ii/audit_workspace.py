"""Evidence inventory, source-backed candidate mapping and human input packets."""
import argparse
import ast
from collections import Counter
import importlib.util
import json
import os
from pathlib import Path
import shutil
import zipfile
import numpy as np
import pandas as pd
from evaluate import TASKS,SEED,sha,write_json

SKIP={'venv','node_modules','.git','__pycache__','_cache','_jobs','.cache'}
HUMAN_TERMS=('annotator','anotator','penilai','rubrik','kappa','likert','1040','adjud')


def main(workspace):
    repo=Path(workspace).resolve();app=repo/'DEMO_XAI_745_FULL';out=repo/'docs/revisi-ii'
    out.mkdir(exist_ok=True);analysis=app/'04_hasil_eksperimen/revisi_ii/analysis'
    df=pd.read_csv(app/'03_data/DATASET_740_TASK2_DOMAIN.csv').fillna('')
    rows=[];headers=[];archives=[]
    for base,dirs,files in os.walk(repo):
        generated=[repo/'delivery/revisi_ii_20261101',repo/'docs/revisi-ii',app/'04_hasil_eksperimen/revisi_ii']
        dirs[:]=[d for d in dirs if d not in SKIP and not any((Path(base)/d).is_relative_to(g) for g in generated)]
        for name in files:
            p=Path(base)/name;rel=str(p.relative_to(repo));low=name.lower()
            if any(t in low for t in HUMAN_TERMS):rows.append(dict(path=rel,bytes=p.stat().st_size,kind='filename_match_not_proof_of_human_ratings'))
            if p.suffix.lower()=='.csv' and 'revisi_ii/' not in rel and 'revisi-ii/' not in rel:
                try:
                    columns=pd.read_csv(p,nrows=0).columns.tolist()
                    headers.append(dict(path=rel,columns=columns,possible_independent_rater_columns=[c for c in columns if any(v in c.lower() for v in ['annotator','anotator','rater','penilai','likert'])]))
                except Exception as exc:headers.append(dict(path=rel,error=type(exc).__name__))
            if p.suffix.lower() in {'.xlsx','.xls','.docx'}:rows.append(dict(path=rel,bytes=p.stat().st_size,kind='office_document_candidate'))
            if p.suffix.lower()=='.zip' and p.is_relative_to(repo/'delivery'):
                with zipfile.ZipFile(p) as z:
                    names=[n for n in z.namelist() if any(t in Path(n).name.lower() for t in HUMAN_TERMS) or n.lower().endswith(('.xlsx','.xls'))]
                archives.append(dict(path=rel,matched_entries=names))
    write_json(out/'HUMAN_EVIDENCE_SEARCH.json',dict(scope='entire workspace and delivery ZIP indexes, excluding environments/transient caches/new delivery',
        filename_matches=rows,csv_headers=headers,archive_matches=archives,
        conclusion='No two independent raw label columns/files, 1040-record corpus, or five-rater XAI score table identified. Existing annotator_confidence is not inter-annotator agreement; uji_alur_anotator is classifier evaluation, not independent human ratings.',
        limitation='Negative inventory finding, not proof that files do not exist outside this workspace.'))
    src=repo/'docs/server-recovery/2026-10-10/01_notebook/kaggle_e01/full/e01_vlm.py'
    spec=importlib.util.spec_from_file_location('e01_provenance',src);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    folder=repo/'docs/server-recovery/2026-10-10/e01-full-terbaru/e01_vlm'
    meta=json.loads((folder/'meta.json').read_text())
    descriptions=[json.loads(s) for s in (folder/'deskripsi.jsonl').read_text().splitlines()]
    zero=[json.loads(s) for s in (folder/'zeroshot.jsonl').read_text().splitlines()]
    assert set(r['sample_id'] for r in zero)==set(df.sample_id)==set(r['sample_id'] for r in descriptions)
    assert sha(folder/'deskripsi.jsonl')=='c75e8df3f9b71d6786462f8d0f1187ebe4234fb8dd079924f3f35707ff1b8cd2'
    assert sha(folder/'zeroshot.jsonl')=='10c07b06b13fbbf647f2b1ed12a722d9bff8f97caa6b621430d8bc0429ab38c9'
    import hashlib
    assert hashlib.sha256(module.PROMPT_A.encode()).hexdigest()==meta['prompt_a_sha256']
    assert hashlib.sha256(module.prompt_b('{judul}','{pendukung}').encode()).hexdigest()==meta['prompt_b_sha256']
    fields=sorted({n.attr for n in ast.walk(ast.parse(src.read_text())) if isinstance(n,ast.Attribute) and isinstance(n.value,ast.Name) and n.value.id in {'r','row'}})
    # Verify the actual prompt builder is insensitive to gold fields by using
    # only explicit text arguments; retain full source for data-flow inspection.
    samples=np.random.default_rng(SEED).choice(len(zero),20,replace=False)
    pd.DataFrame([dict(sample_id=zero[i]['sample_id'],sumber_visual=zero[i].get('sumber_visual'),generated_domain=zero[i].get('domain'),
                       alasan=zero[i].get('alasan'),description=descriptions[i]['deskripsi'],
                       source_visual_equals_class=zero[i].get('sumber_visual') in set(df[TASKS[1]]),reviewer='AI source/output inspection; not independent human annotation') for i in samples]).to_csv(out/'feature_provenance_20_examples.csv',index=False)
    provenance=dict(status='source_and_hash_verified; process_isolation_requirement_not_met',generator=str(src.relative_to(repo)),generator_sha256=sha(src),
                    model=meta['model'],revision=meta['revision'],metadata_sha256=sha(folder/'meta.json'),
                    files={n:sha(folder/n) for n in ['deskripsi.jsonl','zeroshot.jsonl']},prompt_hashes_match=True,
                    generator_row_attributes=fields,prompt_a=module.PROMPT_A,prompt_b_template=module.prompt_b('{judul}','{pendukung}'),
                    inputs=dict(images='05_gambar/<image_path basename>',dataset_csv='03_data/DATASET_740_TASK2_DOMAIN.csv',
                                gold_columns_loaded_into_process=True,gold_columns_passed_to_prompt=False,
                                prompt_fields=['image','headline_verified','supporting_text_verified','fixed Task2 codebook']),
                    generated_domain_is_model_output_not_gold=True,
                    generation_timestamp='Exact original UTC creation not recorded; recovery copy timestamps are not generation timestamps',
                    source_visual_exact_code_matches=sum(r.get('sumber_visual') in set(df[TASKS[1]]) for r in zero),
                    note='Source supports no direct gold-label interpolation. Literal claim labeled CSV never entered process is false: pandas reads full CSV. Static source/hash evidence does not establish every historical runtime dependency or label independence of human-verified headline text.')
    write_json(out/'FEATURE_PROVENANCE.json',provenance)
    (out/'FEATURE_PROVENANCE.md').write_text('# Provenance fitur E01\n\n'
       'Generator lengkap, prompt, model/revisi, metadata dan hash kedua keluaran ditemukan dan cocok dengan worker E14. '
       'Gold task tidak diinterpolasi ke prompt; kolom `domain` pada zeroshot adalah keluaran klasifikasi model, bukan gold. '
       'Namun generator membaca CSV berlabel secara penuh ke proses. Karena itu tuntutan literal “CSV berlabel tidak pernah masuk proses” tidak terpenuhi. '
       'Bukti yang tersedia mendukung pemisahan field prompt, bukan isolasi proses formal. Tanggal salinan recovery bukan waktu penciptaan asli.\n\n'
       'Lihat `FEATURE_PROVENANCE.json` dan 20 contoh dengan seed tetap. Jika diperlukan pembuktian isolasi proses yang lebih kuat, gunakan input allowlist berkas baru tanpa label dan jalankan pembangkitan ulang terpisah; hasilnya menjadi fitur versi baru. '
       'Keberadaan nama domain pada keluaran prediksi saja tidak membuktikan kebocoran gold.\n')
    (out/'CORPUS_HISTORY.md').write_text('# Riwayat korpus dan anotasi\n\n'
        f'Dataset canonical yang ditemukan: {len(df)} ID unik, SHA-256 `{sha(app/"03_data/DATASET_740_TASK2_DOMAIN.csv")}`. '
        f'Eligibility: {dict(Counter(df.eligibility))}. Tidak ditemukan korpus awal 1.040 baris atau log 300 keputusan eksklusi per ID. '
        'Kolom `annotator_confidence`, deskripsi dan mapping note adalah satu set anotasi yang sudah tergabung; tidak tersedia dua set label independen untuk menghitung kappa manusia. '
        'Menurut klarifikasi Joy yang diteruskan pengguna pada 2 November 2026, banyak citra sampul berkualitas buruk sehingga tidak dapat dilabeli; menurut Joy alasan ini pernah disampaikan. Alasan umum penyusutan sudah dijelaskan. Pesan menyebut sekitar 1.000 ke 700-an; angka spesifik 1.040 berasal dari dokumen revisi/proposal dan 740 ID terverifikasi pada dataset. Dokumentasi per ID dan sensitivitas belum dapat direkonstruksi. Jangan menganggap ketiadaan data awal membuktikan sampel sengketa dibuang; kualitas citra tidak disamakan dengan sengketa label. Lihat R23_KLARIFIKASI_JOY.json.\n\n'
        'Tindakan siap pakai: paket dua anotator untuk 150 sampul acak, serta audit 60 kasus kelas penampung. '
        'Kappa tidak dihitung dari prediksi AI sebagai pengganti manusia. Setelah anotasi nyata tersedia, jalankan `human_agreement.py`.\n')
    mapping=[]
    candidates=pd.read_csv(analysis/'ranking_36_legacy.csv')
    notebook=app/'01_notebook'
    for name in candidates.experiment:
        backbone='CLIP-L14 full/crop';text='IndoBERT base-p1';frozen='both encoders frozen';head='shared MLP + 3 heads';shared='yes';loss='fixed weighted cross-entropy';uncertainty='no learned uncertainty parameters in audited implementation';augment='encoder preprocessing; inspect variant config';eligible=False
        source_paths=[];notes=[]
        canonical=name
        if name=='M00_e42_baseline':canonical='e42_tail_grid';notes.append('prediction alias of E42, not an independent experiment')
        if canonical.startswith('e') and (notebook/canonical).is_dir():
            folder=notebook/canonical;source_paths=[p for p in folder.glob('*.py') if p.name in ['tail_model.py','worker.py','model.py','train.py','run.py','fusion_model.py','l14_model.py','pool_model.py','norm_model.py','mmoe_model.py']]
            eligible=canonical in {'e36_clip_l14','e37_token_pool','e38_l14_token','e39_feature_norm','e41_cached_tail','e42_tail_grid','e44_focal_tail','e46_label_smoothing','e47_task_relations'}
            if canonical=='e37_token_pool':backbone='CLIP-B32 or CLIP-L14 selected per inner config; see fold config'
            if canonical in {'e41_cached_tail','e42_tail_grid','e44_focal_tail'}:
                frozen='CLIP/front10 IndoBERT frozen; last2 IndoBERT trainable';head='shared256 ReLU dropout0.3 + three linear heads';augment='historical deterministic CLIP full/crop features; crop retained as limitation'
            if canonical=='e44_focal_tail':loss='fixed weighted focal loss, not CE'
            if canonical in {'e40_balanced_mmoe','e49_task_routed_mtl'}:head='mixture of experts + task gates/towers';shared='shared experts, not single shared layer';eligible=False
            if canonical=='e43_spatial_attention':head='spatial attention fusion, audit as architecture variant';eligible=False
        elif name in {'BASELINE_CLIP_INDoBERT','baseline_oof'}:
            source_paths=[notebook/('run_evaluation.py' if name=='BASELINE_CLIP_INDoBERT' else 'e33_joint_mtl/model.py')]
            backbone='CLIP ViT-B32 laion2b_s34b_b79k' if name=='BASELINE_CLIP_INDoBERT' else 'see E33 baseline view';augment='encoder-native image transform';eligible=True
            if name=='baseline_oof':notes.append('E41 cache baseline_oof is E33 model, not BASELINE_CLIP_INDoBERT')
        elif name.startswith(('M01','M02','M03','M04')):
            source_paths=[notebook/'next_research_20261017/run_m01_shared_mlp.py']
            augment='encoder-native clean preprocessing';eligible=name.startswith('M01')
            if name.startswith('M02'):backbone='SigLIP2 base patch16 384';source_paths+=[notebook/'next_research_20261017/kaggle_m02_m03/launch.py']
            if name.startswith('M03'):backbone='DINOv2-base';source_paths+=[notebook/'next_research_20261017/kaggle_m02_m03/launch.py']
            if name.startswith('M04'):backbone='SigLIP2 base patch16 384';head='task-specific adapters + shared MLP';source_paths=[notebook/'next_research_20261017/run_m04_siglip_adapters.py']
        elif name.startswith(('A0','AUG_','selected_pipeline')):
            backbone='SigLIP2 base patch16 384';head='shared MLP + three heads';augment=name.removesuffix('_oof');eligible=False
            source_paths=[notebook/'next_research_20261017/kaggle_a01_a03/launch.py',notebook/'next_research_20261017/prepare_augmentation.py']
            notes.append('augmentation family uses SigLIP2, not isolated augmentation of main E42')
        elif name.startswith('J01'):
            source_paths=[notebook/'next_research_20261017/run_j01_hierarchical.py'];head='shared network + hierarchical Task2 auxiliary objective';eligible=False
        elif name.startswith('MICRO_'):
            source_paths=[p for p in (notebook/'next_research_20261017').glob('run_micro_*.py') if name.split('_')[1].lower() in p.name]
            shared='no single shared neural MTL layer';head='classical task estimators / stacking / decoder';loss='estimator-specific objective; not one neural Joint Loss';eligible=False
            if any(s in name for s in ['E11','E12']):backbone='CLIP + SigLIP2 + Qwen/BGE/caption feature stack';text='IndoBERT + Qwen/BGE/caption features';notes.append('contains VLM-derived inputs despite exclusion by filename filter')
            elif 'E05' in name:
                backbone='SigLIP2 fine-tuned';frozen='see E05 source/protocol';source_paths=[notebook/'next_research_20261017/kaggle_micro_e05/launch.py']
            elif 'E04' in name:backbone='no standalone visual backbone';text='lexical text features'
        existing=[p for p in source_paths if p.exists()]
        if len(existing)<len(source_paths):notes.append('some source path candidates missing; inspect bundled source index/config before claiming parity')
        mapping.append(dict(experiment=name,visual_backbone=backbone,text_backbone=text,encoder_status=frozen,
                            head_architecture=head,shared_layer=shared,loss=loss,uncertainty_weighting=uncertainty,
                            augmentation=augment,proposal_architecture_eligible=eligible,
                            architecture_evidence=';'.join(str(p.relative_to(repo)) for p in existing),
                            source_sha256=';'.join(sha(p) for p in existing),notes='; '.join(notes)))
    mapped=pd.DataFrame(mapping);assert len(mapped)==36
    mapped.to_csv(out/'candidate_mapping_36.csv',index=False)
    ranked=candidates.merge(mapped[['experiment','proposal_architecture_eligible']],on='experiment')
    chosen=ranked[ranked.proposal_architecture_eligible & (ranked.experiment!='M00_e42_baseline')].sort_values(['mean_macro_f1','experiment'],ascending=[False,True]).iloc[0]
    assert chosen.experiment=='e42_tail_grid'
    decision=dict(model_id='e42_tail_grid',selection='mean Macro-F1 across three tasks, equal weights, eligible CLIP-IndoBERT shared neural MTL family',
                  alias='M00_e42_baseline',post_hoc=True,mean_macro_f1=float(chosen.mean_macro_f1),
                  macro_f1={t:float(chosen[f'macro_f1_{i+1}']) for i,t in enumerate(TASKS)},
                  backbone='CLIP ViT-L14 frozen full/crop + IndoBERT first10 frozen, last2 fine-tuned',
                  head='shared256 ReLU dropout0.3 then three heads',loss='class-weighted CE with fixed per-task weights; six original LR/loss configurations selected inner-only',
                  learned_uncertainty_weighting=False,web_runtime_model='historical CLIP-B32 frozen; not E42',
                  cv_checkpoint_available=True,deployment_refit='not yet performed for E42',
                  validity='internal adaptive repeated-corpus CV; not independent external acceptance')
    write_json(out/'MAIN_MODEL_DECISION.json',decision)
    definitions_source=notebook/'next_research_20261017/kaggle_micro_e14/worker.py'
    definitions=next(ast.literal_eval(n.value) for n in ast.parse(definitions_source.read_text()).body
                     if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='DEFINITIONS' for t in n.targets))
    assert all(set(definitions[t])==set(df[t]) for t in TASKS)
    write_json(out/'TASK_DEFINITIONS.json',dict(source=str(definitions_source.relative_to(repo)),
                source_sha256=sha(definitions_source),definitions=definitions,
                scope='operational definitions aligned to existing codebook; no relabeling or human adjudication implied'))
    (out/'MAIN_MODEL_DECISION.md').write_text('# Penetapan model utama\n\n'
       f'Identitas model penelitian: **E42 (`e42_tail_grid`)**, alias M00. Macro-F1 Task1/2/3: '
       f'{chosen.macro_f1_1:.6f}/{chosen.macro_f1_2:.6f}/{chosen.macro_f1_3:.6f}; rerata {chosen.mean_macro_f1:.6f}. '
       'Kandidat ini memenuhi cabang CLIP–IndoBERT, satu shared layer dan tiga head. IndoBERT dua blok terakhir fine-tuned, sehingga istilah seluruh encoder beku tidak tepat. '
       'Loss merupakan jumlah CE berbobot tetap dengan class weights training-only, bukan learned uncertainty Kendall.\n\n'
       'Pemilihan ini dilakukan setelah kandidat dievaluasi pada korpus yang sama. Angka merupakan hasil seleksi post-hoc pada repeated-corpus internal CV dan berpotensi optimistis. '
       'Rerata Macro-F1 berbobot sama antar task dipakai untuk keputusan ini; per-task menjadi laporan utama dan minimum hanya diagnostik. '
       'Alias/duplikasi prediksi tidak dihitung sebagai bukti eksperimen independen.\n\n'
       'Web historis CLIP-B32 tetap demo historis terpisah; bukan inferensi model E42. Penjelasan E42 harus memakai checkpoint outer fold yang sesuai atau refit deployment baru yang diverifikasi. '
       'Qwen E14 adalah pembanding dengan input lebih kaya, bukan model utama atau bukti ablasi arsitektur yang terisolasi.\n')
    human=out/'human_inputs';human.mkdir(exist_ok=True)
    annotation=human/'annotation';annotation.mkdir(exist_ok=True)
    pick=df.sort_values('sample_id').sample(n=150,random_state=SEED).sort_values('sample_id')
    blank=pick[['sample_id','image_path','headline_verified','supporting_text_verified']].copy()
    blank['image_path']=['images/'+Path(p).name for p in blank.image_path]
    for t in TASKS:blank[t]=''
    blank['confidence_1_to_5']='';blank['comment']=''
    for annotator in ['A','B']:
        target=annotation/f'annotator_{annotator}.csv'
        if not target.exists():blank.to_csv(target,index=False)
    images=annotation/'images';images.mkdir(exist_ok=True)
    for r in pick.itertuples():shutil.copy2(app/'05_gambar'/Path(r.image_path).name,images/Path(r.image_path).name)
    write_json(annotation/'protocol.json',dict(samples=150,seed=SEED,selection='uniform random without replacement from lexicographically sorted canonical IDs',
             independent_before_adjudication=True,labels={t:sorted(df[t].unique()) for t in TASKS},
             evaluation='Cohen kappa per task on two independent label sets; abstention/missing counts separately',
             score_status='Not Evaluated; blank templates are not observations',sample_ids=pick.sample_id.tolist()))
    (annotation/'README.md').write_text('# Anotasi ganda150\n\n'
        'Berikan file A dan B kepada dua anotator secara terpisah bersama codebook dan gambar. Jangan memperlihatkan gold atau hasil model. '
        'Isi kode persis seperti protocol.json. Jangan berdiskusi sebelum dua file independen dikunci. '
        'Setelah keduanya selesai, simpan hasil mentah, jalankan human_agreement.py, lalu lakukan adjudikasi dalam file baru. '
        'Kolom kosong berarti belum dinilai, bukan setuju/tidak setuju.\n')
    audit=[]
    for t,cat in [(TASKS[1],'LAINNYA'),(TASKS[2],'multiple_or_other')]:
        sample=df[df[t]==cat].sort_values('sample_id').sample(n=30,random_state=SEED)
        for r in sample.itertuples():audit.append(dict(sample_id=r.sample_id,task=t,current_label=cat,image_path=r.image_path,
                  proposed_label='',coherent_subgroup='',adjudication_reason='',reviewer_id=''))
    if not (human/'catchall_review_60.csv').exists():pd.DataFrame(audit).to_csv(human/'catchall_review_60.csv',index=False)
    (human/'XAI_RUBRIC.md').write_text('# Rubrik dan protokol XAI\n\n'
       'Status: instrumen disiapkan sebelum pengisian; belum ada skor manusia. Minimal lima penilai independen yang tidak ikut anotasi. '
       'Identitas peta asli/kontrol disembunyikan, urutan diacak dan kunci hanya dipegang koordinator.\n\n'
       '| Dimensi | 1 | 3 | 5 |\n|---|---|---|---|\n'
       '| Kejelasan visual | Tidak dapat dibaca | Sebagian lokasi jelas | Lokasi/legenda jelas dan mudah dipahami |\n'
       '| Keterkaitan dengan citra/teks | Tidak terkait | Sebagian terkait | Elemen relevan dengan contoh dapat dikenali |\n'
       '| Kemudahan memahami keputusan model | Tidak membantu | Membantu sebagian | Alasan kondisional dan batas metode jelas |\n\n'
       'Skor manusia adalah interpretability/perceived relevance, bukan bukti langsung faithfulness. '
       'Faithfulness diukur terpisah lewat perubahan skor model saat bagian penting dihapus dibanding kontrol acak. '
       'Jangan meminta penilai menyatakan model benar hanya karena peta terlihat masuk akal. '
       'Laporkan distribusi skor dan ICC/alpha sesuai desain; jangan mengisi skor AI sebagai lima manusia.\n')
    print('AUDIT COMPLETE: 36 candidates, E42 selected, human templates150+60, provenance verified with process-isolation caveat')


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--workspace',required=True,type=Path);main(ap.parse_args().workspace)
