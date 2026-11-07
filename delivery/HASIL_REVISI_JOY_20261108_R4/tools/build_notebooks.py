"""Three runnable research notebooks; all analysis inputs ship with the ZIP."""
from pathlib import Path
import base64
import csv
import os
import sys
import nbformat as nbf
from nbclient import NotebookClient
from nbconvert import HTMLExporter


SETUP='''from pathlib import Path
import sys, json
import pandas as pd
from IPython.display import display, Image, Markdown, Code

# Reading saved outputs requires no setup. To Run all, first extract the ZIP.
locations = [Path.cwd(), *Path.cwd().parents, Path('/content/joy_revisi_ii')]
ROOT = next((p for p in locations if (p/'inputs/sources.json').is_file() and (p/'tools/evaluate.py').is_file()), None)
if ROOT is None:
    raise RuntimeError('Paket belum diekstrak. Ekstrak ZIP sehingga joy_revisi_ii/inputs dan joy_revisi_ii/tools tersedia, lalu buka notebook dari folder notebooks. Output tersimpan tetap dapat dibaca tanpa menjalankan sel.')
sys.path.insert(0, str(ROOT/'tools'))
import evaluate
verification = evaluate.run(ROOT, ROOT/'analysis', packaged=True)
B = pd.read_csv(ROOT/'analysis/metrics.csv')
P = pd.read_csv(ROOT/'analysis/paired_tests.csv')
TRACKER = pd.read_csv(ROOT/'documentation/REVISION_TRACKER_28.csv').fillna('')
print('Recomputed saved prediction analysis; no training, credential, Drive mount, API call, or invented human rating.')
print('Verified models:', verification['models'], '| bootstrap:', verification['bootstrap_resamples'])
def table(names):
    view = B[B.experiment.isin(names)]
    display(view[['experiment','phase','samples','task','macro_f1','macro_ci_low','macro_ci_high','accuracy','accuracy_ci_low','accuracy_ci_high','kappa','precision_macro','recall_macro']].style.format(precision=4))
    missing = sorted(set(names)-set(view.experiment))
    if missing:
        print('Not Evaluated / pending evidence:', ', '.join(missing))
def report(name):
    display(Markdown((ROOT/'documentation'/name).read_text()))
def plot(name):
    display(Image(filename=str(ROOT/'analysis'/name)))
'''


def create(root,execute=True,full_evidence=False):
    root=Path(root).resolve();folder=root/'notebooks';folder.mkdir(exist_ok=True)
    html=root/'notebook_html';html.mkdir(exist_ok=True)
    md=nbf.v4.new_markdown_cell;code=nbf.v4.new_code_cell
    cells={
      '01_baseline.ipynb':[
        md('# 01 — Data, baseline dan evaluasi Macro-F1\n\nRevisi II. Model penelitian utama E42; baseline web historis CLIP-B32 dipisahkan. Seluruh tabel dihitung ulang dari input paket, tanpa training terselubung.'),
        md('## Tujuan dan batas bukti\nMacro-F1 utama, akurasi/kappa/precision/recall pendamping. Data manusia yang belum tersedia tetap Not Evaluated. Baca README dan PACKAGE_STATE untuk butir yang masih terbuka.'),
        code(SETUP),
        code("data = pd.read_csv(ROOT/'inputs/DATASET_740_TASK2_DOMAIN.csv').fillna('')\nprint('Dataset:', len(data), 'unique IDs:', data.sample_id.nunique())\ndisplay(pd.concat([data[t].value_counts().rename_axis('label').reset_index(name='count').assign(task=t) for t in evaluate.TASKS], ignore_index=True))"),
        md('## Metode evaluasi dan pelaporan\nSeluruh kelas canonical tetap berada dalam denominator Macro-F1. Akurasi identik dengan Micro-F1 pada tugas single-label ini. CI bootstrap bersyarat pada prediksi yang tersimpan dan tidak menghapus bias seleksi.'),
        code("report('STATISTICAL_METHOD.md')"),
        md('## Baseline, majority dan model utama'),
        code("table(['MAJORITY_TRAIN_FOLD','BASELINE_CLIP_INDoBERT','e42_tail_grid'])"),
        code("display(pd.read_csv(ROOT/'analysis/per_class.csv').query(\"experiment in ['BASELINE_CLIP_INDoBERT','e42_tail_grid']\").style.format(precision=4))"),
        md('## Pemulihan prediksi mentah\nKontrol baseline weighted mereplay seluruh 740 prediksi baseline secara identik. Image-only/text-only kini mempunyai prediksi mentah untuk statistik berpasangan.'),
        code("report('HISTORICAL_REPLAY.md')\ntable(['RII_FROZEN_MTL_WEIGHTED','RII_FROZEN_MTL_UNWEIGHTED','RII_FROZEN_IMAGE_ONLY','RII_FROZEN_TEXT_SUPPORTING','RII_FROZEN_TEXT_HEADLINE'])"),
        code("plot('primary_results.png')"),
        md('## Anotasi, codebook dan korpus'),
        code("report('CORPUS_HISTORY.md')\nreport('CODEBOOK_REVISI.md')"),
        md('## Kesimpulan\nBaseline lama dan E42 adalah dua model berbeda. Kinerja rendah/tinggi dilaporkan per task, bersama ketidakpastiannya. Anotasi ganda dan riwayat eksklusi masih memerlukan bukti manusia; keduanya tidak disimpulkan dari nama file atau keyakinan anotator tunggal.'),
      ],
      '02_experiments.ipynb':[
        md('# 02 — Ablasi, input, label dan XAI\n\nEksperimen historis dan controlled rerun baru diberi nama terpisah. Semua angka berasal dari prediksi aktual, bukan hasil yang diharapkan.'),
        code(SETUP),
        md('## Kontrak arsitektur dan Joint Loss'),
        code("report('ABLATION_PARITY.md')\nsource = ROOT/'source/DEMO_XAI_745_FULL/01_notebook/e42_tail_grid/tail_model.py'\nprint('Historical E42 source (fixed task weights; no Kendall uncertainty):')\ndisplay(Code(source.read_text(), language='python'))"),
        md('## MTL versus single-task dan class weighting\nAblasi RII_TAIL menggunakan resep baru yang sama antarmode dan pemilihan epoch inner. Ini berbeda dari grid E42 historis. E48 SVM dipertahankan sebagai diagnostik.'),
        code("table(['RII_TAIL_MTL_WEIGHTED','RII_TAIL_SINGLE_TASK','RII_TAIL_MTL_UNWEIGHTED','RII_TAIL_IMAGE_ONLY','RII_TAIL_TEXT_SUPPORTING','e48_single_task_diagnostic','e49_task_routed_mtl','J01_hierarchical_task2'])"),
        code("display(P[P.before.eq('RII_TAIL_MTL_WEIGHTED')].style.format(precision=4))"),
        md('## Backbone dan augmentasi'),
        code("table(['M01_clip_indobert','M02_siglip2_indobert','M03_dinov2_indobert','M04_siglip2_adapters','RII_BACKBONE_CLIP_FULL','RII_BACKBONE_SIGLIP2','RII_BACKBONE_DINOV2'])\nreport('AUGMENTATION_AUDIT.md')\ntable(['RII_A00_CLEAN','RII_A01_LIGHT','RII_A02_MODERATE_NO_ROTATION','RII_A03_LIGHT_SAMPLER','RII_AUG_SELECTED_INNER'])"),
        md('## Input basic/rich dan pembanding Qwen'),
        code("report('INPUT_PARITY.md')\ntable(['RII_TAIL_MTL_WEIGHTED','RII_TAIL_HEADLINE_ONLY','RII_TAIL_RICH256','RII_QWEN_ZERO_BASIC','RII_QWEN_ZERO_RICH','RII_QWEN_QLORA_BASIC','MICRO_E14_joint_qlora_oof'])\nreport('FEATURE_PROVENANCE.md')"),
        md('## Task 3: distribusi dan confusion matrix'),
        code("display(pd.read_csv(ROOT/'analysis/task3_entropy.csv').style.format(precision=4))\ndisplay(Markdown('### Baseline CLIP–IndoBERT'))\nplot('confusion_task3_BASELINE_CLIP_INDoBERT.png')\ndisplay(Markdown('### E42 — model utama'))\nplot('confusion_task3_e42_tail_grid.png')\ndisplay(Markdown('### E11 — pembanding hierarkis'))\nplot('confusion_task3_MICRO_E11_hierarchical_task3.png')\ndisplay(Markdown('### E14 — pembanding QLoRA'))\nplot('confusion_task3_MICRO_E14_joint_qlora_oof.png')\ndisplay(pd.read_csv(ROOT/'analysis/class_distribution.csv').query(\"task == 'task3_primary_entity_type'\").style.format(precision=4))"),
        md('## Kelas penampung dan dekomposisi Task 2'),
        code("display(pd.read_csv(ROOT/'analysis/catchall_sensitivity.csv').query(\"experiment in ['e42_tail_grid','MICRO_E14_joint_qlora_oof']\").style.format(precision=4))\ndisplay(pd.read_csv(ROOT/'analysis/task2_decomposed.csv').query(\"experiment in ['e42_tail_grid','MICRO_E14_joint_qlora_oof']\").style.format(precision=4))"),
        md('## XAI model utama: parity, rollout dan LIME kondisional'),
        code("report('XAI_METHOD.md')\ndisplay(pd.read_csv(ROOT/'xai_e42/heldout_replay.csv'))\ndisplay(pd.read_csv(ROOT/'xai_e42/conditional_lime.csv').head(36).style.format(precision=4))\nexample = sorted((ROOT/'xai_e42').glob('*_rollout.png'))[0]\ndisplay(Image(filename=str(example)))"),
        md('## Kesimpulan\nMTL, backbone dan augmentasi tidak diberi klaim keberhasilan universal. Faithfulness dan interpretability manusia adalah bukti berbeda. Hasil negatif serta bagian yang belum dinilai tetap terlihat.'),
      ],
      '03_final_comparison.ipynb':[
        md('# 03 — Model utama, peringkat dan tanggapan revisi\n\nKeputusan model, statistik, keterbatasan dan status 28 butir berasal dari bukti yang disertakan. Tidak ada klaim seluruh revisi selesai bila data manusia/komputasi belum lengkap.'),
        code(SETUP),
        md('## Identitas model utama dan pemilihan post-hoc'),
        code("report('MAIN_MODEL_DECISION.md')\ndisplay(pd.read_csv(ROOT/'documentation/candidate_mapping_36.csv'))"),
        md('## Peringkat ganda: audit minimum, keputusan per-task/mean Macro-F1'),
        code("rank = pd.read_csv(ROOT/'analysis/ranking_36_legacy.csv')\ndisplay(rank.style.format(precision=4))\nprint(json.dumps(json.loads((ROOT/'analysis/rank_correlation.json').read_text()),indent=2))\nreport('SELECTION_BIAS.md')"),
        md('## Hasil utama dan pembanding'),
        code("table(['e42_tail_grid','BASELINE_CLIP_INDoBERT','MICRO_E11_hierarchical_task3','MICRO_E12_structured_decoder','MICRO_E14_joint_qlora_oof','CI_D01_1x','CI_D01_2x'])\nplot('primary_results.png')"),
        md('## Statistik berpasangan\nMcNemar/Holm adalah untuk akurasi. CI selisih Macro-F1 berasal dari bootstrap berpasangan dan bersifat pointwise eksploratif. Tidak signifikan tidak membuktikan model setara.'),
        code("display(P.style.format(precision=4))"),
        md('## Ringkasan status seluruh revisi'),
        code("display(TRACKER)\nprint('Status paket:')\nprint(json.dumps(json.loads((ROOT/'PACKAGE_STATE.json').read_text()),indent=2))\nreport('TINDAK_LANJUT_JOY.md')"),
        md('## Pembahasan, etika dan referensi'),
        code("report('HASIL_DAN_TANGGAPAN.md')\nreport('MANUSKRIP_DRAF.md')\nreport('REFERENCES.md')"),
        md('## Verifikasi reproduksi'),
        code("import validate_package\ncheck = validate_package.validate(ROOT, check_notebooks=False)\nprint(json.dumps(check,indent=2))"),
        md('## Kesimpulan\nPaket memungkinkan audit dan perhitungan ulang dari prediksi nyata. Kesimpulan dibatasi oleh penggunaan ulang korpus dan bukti yang tersedia. File anotasi/penilaian kosong disediakan sebagai pekerjaan berikutnya, bukan hasil evaluasi manusia.'),
      ],
    }
    identity = '''## R18 — Identitas model utama yang dibekukan

**Model utama penelitian adalah E42 (`e42_tail_grid`, alias `M00_e42_baseline`): arsitektur Multi-Task Learning CLIP–IndoBERT dengan Joint Loss.** CLIP ViT-L/14 frozen mengekstraksi full/crop; IndoBERT memiliki 10 blok awal frozen dan 2 blok terakhir trainable. Fitur gabungan 2.304 dimensi masuk ke shared layer 256/ReLU/dropout0,3, lalu tiga head: isu10, domain7 dan entitas8.

Joint Loss adalah jumlah weighted cross entropy ketiga task, dibobot dan dinormalisasi dengan jumlah bobot task. Class weights dihitung hanya dari training. Bobot task tetap per run, bukan learned uncertainty Kendall. Detail formula dan konfigurasi lima fold tersedia langsung pada notebook02, bagian **R18 — Arsitektur Multi-Task Learning CLIP–IndoBERT dengan Joint Loss**.

Baseline CLIP-B32, varian backbone dan Qwen adalah pembanding. Demo web historis belum memakai E42. Penetapan E42 pada audit ini dinyatakan post-hoc; tidak mengubah protokol seleksi inner historis.
'''
    for name,body in cells.items():
        body.insert(1,md(identity))
    cells['02_experiments.ipynb'].insert(2,md((root/'documentation/R18_ARSITEKTUR_JOINT_LOSS.md').read_text()))

    def visual(relative,caption):
        path=root/relative;key=path.name
        return nbf.v4.new_markdown_cell(f'![{caption}](attachment:{key})\n\n{caption}',
            attachments={key:{'image/png':base64.b64encode(path.read_bytes()).decode()}})

    # Screenshots are notebook attachments, not paths on the author's machine.
    # The historical originals remain unchanged in screenshots/ with hashes.
    for name,body in cells.items():
        stem=Path(name).stem
        body.append(md('## Screenshot delivery sebelumnya dan perubahan sekarang\n\n'
            'Gambar berikut disalin utuh dari bukti delivery **20 Oktober 2026**. Ini catatan versi sebelumnya; hasil terbaru ada di tabel dan output notebook ini. '
            'Screenshot historis tidak menjadi bukti kelulusan Colab atau deployment E42. Sumber/hash tersedia di `screenshots/EVIDENCE_MANIFEST.json`.'))
        body.append(visual(f'screenshots/historical_20261020_{stem}.png',f'Screenshot historis {stem} — delivery 20 Oktober 2026.'))
    cells['03_final_comparison.ipynb'].append(md('## Kutipan visual permintaan R18\n\nHalaman5 PDF revisi asli disertakan untuk mencocokkan permintaan arsitektur dan Joint Loss dengan jawaban notebook02. Ini render sumber asli, tanpa merekonstruksi lingkaran atau highlight pada gambar pengguna.'))
    cells['03_final_comparison.ipynb'].append(visual('screenshots/r18_source_page_05.png','Sumber permintaan R18 — halaman5 Daftar Revisi II, 27 Oktober 2026.'))
    tracker=list(csv.DictReader((root/'documentation/REVISION_TRACKER_28.csv').open()))
    location={rid:'02_experiments.ipynb' for rid in ['R18','R20','R21','R22','R27','R29','R30','R31','R34','R4','R8','R9']}
    location.update({rid:'01_baseline.ipynb' for rid in ['R23','R24','R28','R2','R6','R12']})
    index='## Peta seluruh revisi di dalam tiga notebook\n\nStatus berikut berasal dari bukti saat build. Bagian yang menunggu manusia tetap terbuka.\n\n| Butir | Permintaan | Notebook utama | Status |\n|---|---|---|---|\n'
    for row in tracker:
        name=location.get(row['revision_id'],'03_final_comparison.ipynb')
        index+=f"| {row['revision_id']} | {row['title']} | {name} | {row['status']} |\n"
    cells['03_final_comparison.ipynb'].insert(2,md(index))
    cells['03_final_comparison.ipynb'].append(md('## Jawaban langsung setiap butir\n\n'+(root/'documentation/TANGGAPAN_28_REVISI.md').read_text()))
    if full_evidence:
        from notebook_evidence import append_full_evidence
        append_full_evidence(root,cells)
    old_path=os.environ.get('PATH','');os.environ['PATH']=str(Path(sys.executable).parent)+os.pathsep+old_path
    reports=[]
    try:
        for name,body in cells.items():
            nb=nbf.v4.new_notebook(cells=body,metadata={'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'},
                 'language_info':{'name':'python','version':'3.10'},'colab':{'name':name,'provenance':[]},
                 'tempo_revision':{'primary_metric':'macro_f1','training_in_run_all':False,'human_ratings_imputed':False,
                                   'r18_identity_inline':True,'screenshots_embedded':True,
                                   'full_evidence':full_evidence}})
            nbf.validate(nb)
            for i,c in enumerate(nb.cells):
                if c.cell_type=='code':compile(c.source,f'{name}:{i}','exec')
            if execute:
                print('Executing notebook',name,flush=True)
                NotebookClient(nb,timeout=900,kernel_name='python3',resources={'metadata':{'path':str(root)}}).execute()
            nbf.write(nb,folder/name)
            if execute:
                exporter=HTMLExporter(template_name='lab');exporter.embed_images=True
                rendered,_=exporter.from_notebook_node(nb);(html/(Path(name).stem+'.html')).write_text(rendered)
            errors=[o for c in nb.cells if c.cell_type=='code' for o in c.outputs if o.output_type=='error']
            assert not errors
            reports.append(dict(notebook=name,executed=execute,code_cells=sum(c.cell_type=='code' for c in nb.cells),errors=len(errors)))
    finally:os.environ['PATH']=old_path
    return reports
