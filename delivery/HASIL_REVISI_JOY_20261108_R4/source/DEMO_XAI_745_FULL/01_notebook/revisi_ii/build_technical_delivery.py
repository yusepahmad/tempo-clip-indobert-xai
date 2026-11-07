"""Extend preserved R3 evidence with verified R21 results and human handoff."""
import argparse
from datetime import datetime, timezone
import html
import json
from pathlib import Path
import shutil
import subprocess

import pandas as pd

import build_notebooks
from build_full_delivery import reference_html, seal
from build_revision_evidence import page, verify as verify_evidence, pdf_requirements
import evaluate as ev
import followup_r21
from notebook_evidence import verify_full
import reports
from validate_package import validate

HERE=Path(__file__).resolve().parent
APP=HERE.parents[1]
REPO=APP.parent


def copy(source,target):
    target=Path(target);target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(source,target)


def import_results(root):
    inventory=json.loads((root/'inputs/sources.json').read_text())
    data=pd.read_csv(root/'inputs/DATASET_740_TASK2_DOMAIN.csv').fillna('')
    folds=pd.read_csv(root/'inputs/folds.csv').set_index('sample_id')['fold']
    imported=[]
    for name,job in [('RII_QWEN_QLORA_BASIC','qwen_basic_jobs'),('RII_QWEN_QLORA_HEADLINE_ONLY','qwen_headline_jobs')]:
        source=APP/'04_hasil_eksperimen/revisi_ii/experiments'/name
        verification=APP/'04_hasil_eksperimen/revisi_ii'/job/'full/verification.json'
        if not verification.exists():continue
        v=json.loads(verification.read_text());assert v['status']=='verified' and v['samples']==740
        result=json.loads((source/'result.json').read_text())
        assert result['status']=='complete' and result['samples']==740 and ev.sha(source/'predictions.csv')==result['predictions_sha256']
        frame=ev.validate_predictions(pd.read_csv(source/'predictions.csv'),data,folds)
        target=root/'inputs/predictions'/f'{name}.csv';frame.to_csv(target,index=False)
        record=dict(experiment=name,source=str((source/'predictions.csv').relative_to(REPO)),sha256=ev.sha(source/'predictions.csv'),
            samples=740,phase='revision_ii_new_740_oof',legacy_candidate=False,prediction_signature=ev.signature(frame),
            fold_meaning='canonical outer training/test fold',package_path=target.relative_to(root).as_posix(),package_sha256=ev.sha(target))
        inventory['sources']=[r for r in inventory['sources'] if r['experiment']!=name]+[record]
        copy(source/'result.json',root/'experiment_protocols/experiments'/name/'result.json')
        imported.append(name)
    assert 'RII_QWEN_QLORA_BASIC' in imported
    ev.write_json(root/'inputs/sources.json',inventory)
    for group in ['qwen_basic_jobs','qwen_headline_jobs']:
        folder=APP/'04_hasil_eksperimen/revisi_ii'/group
        for p in folder.rglob('*'):
            if p.is_file() and p.suffix in {'.json','.jsonl','.csv','.log'} and p.stat().st_size<3_000_000:
                copy(p,root/'experiment_protocols'/group/p.relative_to(folder))
    return imported


def r21_tables(root):
    doc=root/'documentation';matrix=followup_r21.build(root,doc)
    ev.write_json(doc/'R21_TABLE_VERIFICATION.json',matrix)
    paired=pd.read_csv(root/'analysis/paired_tests.csv')
    paired=paired[paired.before.eq('RII_QWEN_QLORA_BASIC') & paired.after.eq('MICRO_E14_joint_qlora_oof')].copy()
    assert len(paired)==3
    paired['mcnemar_holm_p_three_tasks']=ev.holm(paired.mcnemar_exact_p)
    paired.to_csv(doc/'R21_PAIRED_BASIC_VS_RICH.csv',index=False)
    metrics=pd.read_csv(root/'analysis/metrics.csv');data=pd.read_csv(root/'inputs/DATASET_740_TASK2_DOMAIN.csv')
    arms=[('CLIP-IndoBERT','citra+judul','RII_TAIL_HEADLINE_ONLY',128),('CLIP-IndoBERT','rich','RII_TAIL_RICH256',256),
          ('Qwen3-VL QLoRA','citra+judul','RII_QWEN_QLORA_HEADLINE_ONLY',2048),('Qwen3-VL QLoRA','rich','MICRO_E14_joint_qlora_oof',2048)]
    rows=[]
    for architecture,scope,name,tokens in arms:
        for task in ev.TASKS:
            selected=metrics[metrics.experiment.eq(name)&metrics.task.eq(task)]
            row=dict(architecture=architecture,input_scope=scope,experiment=name,task=task,max_text_tokens=tokens,status='Not Evaluated',samples=0)
            if len(selected):
                r=selected.iloc[0];frame=pd.read_csv(root/f'inputs/predictions/{name}.csv')
                row.update(status='Available',samples=int(r.samples),macro_f1=float(r.macro_f1),macro_ci_low=float(r.macro_ci_low),macro_ci_high=float(r.macro_ci_high),
                    **followup_r21.kappa_ci(frame[task+'_truth'],frame[task+'_pred'],sorted(data[task].unique())))
            rows.append(row)
    pd.DataFrame(rows).to_csv(doc/'R21_LITERAL_2X2.csv',index=False)
    pending=sum(r['status']!='Available' for r in rows)
    text='# R21 — citra dan judul literal\n\n'
    text+='Tabel ini mengikuti definisi citra+judul pada PDF; supporting text tidak masuk arm basic literal. Hasil basic lama yang memuat supporting text tetap tersedia sebagai kontrol terpisah, bukan pengganti arm literal.\n\n'
    text+='| Arsitektur | Task | Citra+judul: Macro-F1 [CI]; kappa [CI] | Rich: Macro-F1 [CI]; kappa [CI] |\n|---|---|---|---|\n'
    for architecture in ['CLIP-IndoBERT','Qwen3-VL QLoRA']:
        for task in ev.TASKS:
            cells=[]
            for scope in ['citra+judul','rich']:
                r=next(r for r in rows if r['architecture']==architecture and r['task']==task and r['input_scope']==scope)
                cells.append('Not Evaluated — menunggu lima fold/740 prediksi' if r['status']!='Available' else
                    f"{r['macro_f1']:.4f} [{r['macro_ci_low']:.4f}, {r['macro_ci_high']:.4f}]; {r['kappa']:.4f} [{r['kappa_ci_low']:.4f}, {r['kappa_ci_high']:.4f}]")
            text+=f'| {architecture} | {task} | '+ ' | '.join(cells)+' |\n'
    text+='\nRich CLIP128/256 dan QLoRA2048 memiliki kapasitas konteks berbeda. Resep epoch QLoRA diwarisi dari pilihan inner rich historis, bukan dituning ulang pada basic. Selisih mencampur konteks, pretraining dan input; tidak disebut efek fitur murni. Zero-shot rich/basic lama ada pada R21_MATRIX_DAN_ZERO_SHOT.csv dan bukan training OOF.\n'
    text+=f'\nStatus: {len(rows)-pending}/{len(rows)} baris literal tersedia. Tidak ada nilai smoke yang digunakan sebagai angka penelitian.\n'
    (doc/'R21_LITERAL_2X2.md').write_text(text)
    summary='# R21 — hasil aktual QLoRA basic dengan supporting text\n\n'
    summary+='Lima fold telah dikoleksi dan diverifikasi pada 7 November 2026: tepat740ID unik, label/fold canonical, split, probabilitas, source/protocol dan hash input audit. Tidak ada training ulang untuk angka pada tabel ini. Bobot checkpoint tidak direplay lokal.\n\n'
    focus=metrics[metrics.experiment.isin(['RII_QWEN_QLORA_BASIC','MICRO_E14_joint_qlora_oof'])]
    summary+=reports.markdown_table(focus,['experiment','task','macro_f1','macro_ci_low','macro_ci_high','accuracy','kappa'])
    summary+='\n\n## Perbandingan berpasangan: basic supporting → rich\n\n'+reports.markdown_table(paired,['task','macro_f1_delta','macro_delta_ci_low','macro_delta_ci_high','mcnemar_exact_p','mcnemar_holm_p_three_tasks'])
    summary+='\n\nDelta adalah rich dikurangi basic; Macro-F1CI bersifat pointwise eksploratif. McNemar/Holm menguji akurasi, bukan Macro-F1. Tidak signifikan tidak berarti setara. Family tiga task R21 dilaporkan terpisah dari family seluruh uji pada analysis/paired_tests.csv.\n\n'
    summary+='Arm ini memuat citra+judul+supporting text. Untuk tuntutan literal citra+judul, lihat R21_LITERAL_2X2.md dan tracker. Tabel supporting18/18lengkap tidak otomatis menutup R21.\n'
    for a,b in [('pada8November2026','pada 8 November 2026'),('tepat740ID','tepat 740 ID'),('Macro-F1CI','CI Macro-F1'),('supporting18/18lengkap','supporting 18/18 lengkap')]:summary=summary.replace(a,b)
    (doc/'R21_HASIL_TERKINI.md').write_text(summary)
    p=doc/'INPUT_PARITY.md';p.write_text(p.read_text()+'\n\n## Pembaruan 8 November 2026\n\n'+text+'\n\n'+summary)
    return dict(supporting=matrix,literal_rows=len(rows),literal_pending=pending)


def human_handoff(root):
    human=root/'UNTUK_MANUSIA';human.mkdir(exist_ok=True)
    if (root/'paket_untuk_manusia').exists():
        shutil.move(str(root/'paket_untuk_manusia'),human/'PAKET_PENILAI')
    else:
        assert (human/'PAKET_PENILAI').is_dir(), 'Human packet source is missing'
    followup=REPO/'delivery/TINDAK_LANJUT_REVISI_20261102'
    if not (human/'REGISTRASI_PARTISIPAN.csv').exists():
        copy(followup/'PAKET_MANUSIA/REGISTRASI_PARTISIPAN.csv',human/'REGISTRASI_PARTISIPAN.csv')
    examples=pd.read_csv(REPO/'docs/revisi-ii/feature_provenance_20_examples.csv',keep_default_na=False)
    for c in ['human_reviewer_id','human_review_date','sumber_visual_observasi_bebas_ya_tidak','memuat_kode_task2_di_sumber_visual_ya_tidak','human_notes']:examples[c]=''
    if not (human/'R22_REVIEW_MANUSIA_20.csv').exists():
        examples.to_csv(human/'R22_REVIEW_MANUSIA_20.csv',index=False)
    if not (human/'RIWAYAT_KORPUS_PER_ID.csv').exists():
        pd.DataFrame(columns=['sample_id_asli','file_gambar_asli','keputusan_dipakai_dikeluarkan','alasan','tanggal_keputusan_asli_jika_ada','sumber_bukti','pemeriksa']).to_csv(human/'RIWAYAT_KORPUS_PER_ID.csv',index=False)
    note='''# Tugas manusia — mulai di sini

Paket teknis terbaru sudah memuat hasil Qwen basic supporting740. Arm citra+judul literal berjalan terpisah dan tetap menjadi pekerjaan otomatis. Isian manusia berikut tidak diganti AI. Buka/ekstrak hanya ZIP masing-masing penerima; folder analisis dan kunci koordinator tidak dibagikan kepada penilai.

| Urutan | Revisi | Pelaksana dan yang dikerjakan | Berkas yang dikembalikan |
|---|---|---|---|
| 1 | R23/R6, tenggat9November | Dua anotator berbeda. Bagikan PAКET_PENILAI/ANOTATOR_A.zip dan ANOTATOR_B.zip secara terpisah. Masing-masing membuka MULAI_DI_SINI.html, membaca CODEBOOK.md dan melabeli150sampul pada ketiga task. Kerjakan independen; jangan berdiskusi atau melihat hasil model sebelum kedua file dikunci. | annotator_A.csv dan annotator_B.csv; isi tiga kolom task, confidence_1_to_5 dan comment bila ambigu. Jangan mengganti ID/urutan sampel, header atau kode kelas. |
| 2 | R23/R6 | Joy/pemilik korpus: cari daftar dan citra korpus awal, log seleksi serta alasan perID. Angka proposal1040 dan data canonical740 diketahui; selisih300 bukan bukti300 eksklusi terverifikasi. Alasan umum citra buruk telah disampaikan Joy; jangan menebak tanggal atau alasan tiap sampel. | RIWAYAT_KORPUS_PER_ID.csv beserta file/log asli. Jika tidak ada, tulis informasi mana yang tidak tersedia dalam RIWAYAT_KORPUS.md. Jangan isi300ID buatan. |
| 3 | R22 | Joy/peneliti memeriksa20contoh fitur historis, terutama apakah sumber_visual berisi observasi benda/adegan atau kode task2. Kolom generated_domain memang prediksi model dan berbeda dari sumber_visual. Catat penilaian nyata pada lima kolom human_* dan dua kolom ya/tidak. | R22_REVIEW_MANUSIA_20.csv. Jika sumber_visual memuat kode kategori atau ada bukti gold masuk prompt, tandai dan sampaikan ke pembimbing. |
| 4 | R22 | Pemilik data/pembimbing menilai bukti historis. Source menunjukkan CSV berlabel dibaca ke proses, walaupun field gold tidak masuk prompt; isolasi proses literal dan timestamp penciptaan asli tidak dapat dibuktikan. Pilih tindak lanjut berdasarkan bukti: terima batas field-flow, atau minta regenerasi versi baru dan eksperimen terkait. | Catatan/bukti timestamp asli bila ada dan keputusan pembimbing. Regenerasi hari ini tidak membuktikan sejarah. Draf isu ada pada CATATAN_UNTUK_PEMBIMBING.md; belum dikirim otomatis. |
| 5 | R31, tenggat23November | Adjudikator meninjau30LAINNYA dan30multiple_or_other melalui PAKET_PENILAI/ADJUDIKASI_60.zip. Isi subgroup, usulan label dan alasan per item. Paket ini memuat label saat ini dan tidak dipakai menghitung agreement buta. Jangan mengubah gold sumber. | catchall_review_60.csv: proposed_label, coherent_subgroup, adjudication_reason, reviewer_id. Jika hendak membuat kelas baru, catat keputusan dahulu; perubahan label memerlukan eksperimen terpisah. |
| 6 | R34/R9, tenggat7Desember | Rekrut lima penilai independen yang tidak ikut anotasi. Masing-masing menerima hanya PAKET_PENILAI/PENILAI_XAI_R1.zip s.d.R5.zip, membuka HTML dan RUBRIK.md. Ada16item ×3dimensi =48skor per penilai. Isi bilangan bulat1–5 secara mandiri; jangan mengungkap identitas metode/kontrol. | Lima ratings.csv dari folder penilai masing-masing. Simpan dalam subfolder R1…R5 agar tidak saling menimpa. Jangan mengubah item_id, rater_id atau dimension. |
| 7 | R8, tenggat16November | Joy/pembimbing mencari dokumen revisi Agustus asli untuk memastikan tuntutan lengkap, bukan hanya ringkasan yang ditemukan pada RevisiII. | Dokumen asli atau konfirmasi tertulis butirR8. |
| 8 | R32, tenggat23November | Pengguna membuka Google Colab baru tanpa Drive, pilih runtimeCPU. Unggah COLAB_RUN_ALL.ipynb dan jalankan Runtime→Run all; saat diminta unggah R32_ANALISIS_PORTABEL.zip yang berpasangan dengannya. Browser tidak tersedia dalam sesi Codex ini sehingga saya belum dapat menjalankan akun Colab. | JOY_R32_BUKTI_COLAB.zip dan screenshot sel ringkasan. Laporan RUNTIME_VERIFICATION.json harus status verified dan colab_verified=true; jika error, kirim traceback apa adanya. |

Catat kode partisipan, tanggal, keahlian, independensi dan persetujuan pada REGISTRASI_PARTISIPAN.csv secara privat. Jangan menyamakan tanggal pengisian baru dengan tanggal anotasi historis. Kunci kontrol privat hanya untuk koordinator.

Setelah file asli dikembalikan, agent dapat memvalidasi kelengkapan, menghitung Cohen kappa per task, tabel manusia/model, ICC antarpenilai, analisis kontrol dan pembaruan naskah. Hasil anotasi sebelum adjudikasi harus dipertahankan; jangan menimpa dengan kesepakatan setelah diskusi. Sensitivitas pada sampul dikeluarkan baru bisa dihitung bila citra/ID/gold yang diperlukan tersedia.

Jika ada file manusia yang belum bisa diselesaikan, laporkan sebagai belum tersedia; jangan mengisi nol, tebakan atau skor AI. Simpan hasil pada folder baru HASIL_ISIAN agar instrumen asli tetap utuh.
'''
    replacements={'supporting740':'supporting 740','tenggat9November':'tenggat 9 November','tenggat23November':'tenggat 23 November','tenggat7Desember':'tenggat 7 Desember','tenggat16November':'tenggat 16 November','melabeli150sampul':'melabeli 150 sampul','perID':'per ID','proposal1040':'proposal 1040','canonical740':'canonical 740','selisih300':'selisih 300','bukti300':'bukti 300','isi300ID':'isi 300 ID','memeriksa20contoh':'memeriksa 20 contoh','meninjau30LAINNYA dan30multiple_or_other':'meninjau 30 LAINNYA dan 30 multiple_or_other','s.d.R5':'s.d. R5','Ada16item ×3dimensi =48skor':'Ada 16 item × 3 dimensi = 48 skor','bulat1–5':'bulat 1–5','RevisiII':'Revisi II','butirR8':'butir R8','runtimeCPU':'runtime CPU','PAКET':'PAKET'}
    for a,b in replacements.items():note=note.replace(a,b)
    (human/'MULAI_DI_SINI.md').write_text(note)
    if not (human/'RIWAYAT_KORPUS.md').exists():
        (human/'RIWAYAT_KORPUS.md').write_text('# Riwayat korpus — informasi yang perlu dilengkapi pemilik\n\nDiketahui: proposal menyebut 1.040; dataset canonical berisi 740 ID unik. Joy menjelaskan banyak citra berkualitas buruk sehingga tidak dapat dilabeli, dan alasan umum ini pernah disampaikan. Tanggal komunikasi, daftar awal lengkap, daftar keputusan per ID dan riwayat 300 sampel belum tersedia.\n\nLengkapi hanya berdasarkan berkas/ingatan yang diberi sumber dan tingkat kepastian. Jangan membuat ID, tanggal atau alasan per sampel tanpa bukti. Lampirkan log, folder citra awal, catatan anotasi dan daftar seleksi yang masih ada. Tandai tidak tersedia jika memang hilang.\n')
    if not (human/'CATATAN_UNTUK_PEMBIMBING.md').exists():
        (human/'CATATAN_UNTUK_PEMBIMBING.md').write_text('# Bahan konfirmasi kepada pembimbing — belum dikirim\n\n1. R22: generator historis membaca CSV berlabel secara penuh; pemeriksaan source tidak menemukan interpolasi gold ke prompt. Hash fitur cocok, tetapi isolasi proses literal dan timestamp penciptaan asli tidak dapat dibuktikan. Apakah bukti field-flow beserta pengungkapan batas ini dapat diterima, atau perlu regenerasi fitur versi baru dan pengulangan eksperimen terkait?\n2. R21: supporting-text basic dan rich kini mempunyai 740 prediksi; arm citra+judul literal dikerjakan terpisah. Resep epoch QLoRA diwarisi dari inner rich historis, CLIP basic128/rich256, QLoRA2048. Kesimpulan tidak mengklaim efek fitur murni.\n3. R8: mohon dokumen revisi Agustus asli atau konfirmasi tuntutan lengkap butir baseline/ablasi.\n\nCatatan ini hanya bahan pengguna. Tidak ada email atau pesan yang dikirim agent.\n')
    return dict(annotation_samples=150,annotators=2,adjudication_samples=60,xai_raters=5,xai_items=16,scores_per_rater=48,e01_manual_examples=20,human_ratings_generated_by_agent=False,existing_return_files_preserved=True)


def refresh_evidence(root,release='R4'):
    base=root/'BUKTI_PER_REVISI'
    tracker=pd.read_csv(root/'documentation/REVISION_TRACKER_28.csv').fillna('')
    if tracker.set_index('revision_id').loc['R21','status']=='Selesai':
        folder=base/'R21';folder.mkdir();request=pdf_requirements(REPO)['R21']
        files=[]
        for rel in ['documentation/R21_LITERAL_2X2.csv','documentation/R21_LITERAL_2X2.md','documentation/R21_MATRIX_DAN_ZERO_SHOT.csv','documentation/R21_HASIL_TERKINI.md','analysis/paired_tests.csv']:
            target=folder/Path(rel).name;copy(root/rel,target)
            files.append(dict(file=target.name,purpose='Bukti R21 aktual, scope dan batas perbandingan',kind='copy',source=rel,source_sha256=ev.sha(root/rel),sha256=ev.sha(target)))
        ev.write_json(folder/'BUKTI_MANIFEST.json',dict(revision_id='R21',title='Kesetaraan masukan dan Qwen zero-shot',pdf_page=request['page'],requested_evidence=request['requirement'],notebook=dict(notebook='02_experiments.ipynb'),notes=['Arm literal citra+judul tersedia. Batas konteks dan resep epoch tetap diungkapkan; selesai teknis bukan persetujuan akademik.'],files=files))
    index=[]
    for row in tracker.to_dict('records'):
        rid=row['revision_id'];folder=base/rid;mp=folder/'BUKTI_MANIFEST.json'
        if mp.exists():
            m=json.loads(mp.read_text());stem=Path(m['notebook']['notebook']).stem
            m['notebook'].update(heading=f'{rid} — '+m['title'],html=f'../REFERENSI_NOTEBOOK/{stem}.html#full-{rid.lower()}')
            for item in m['files']:
                target=folder/item['file']
                if item['kind']=='copy':copy(root/item['source'],target)
                elif item['kind']=='table_subset':
                    table=pd.read_csv(root/item['source']);sel=item['selector']
                    if 'experiments' in sel:table=table[table.experiment.isin(sel['experiments'])]
                    if 'task' in sel:table=table[table.task.eq(sel['task'])]
                    if 'pairs' in sel:
                        chosen={tuple(p) for p in sel['pairs']};table=table[[p in chosen for p in zip(table.before,table.after)]]
                    assert len(table)>0;table.to_csv(target,index=False);item['rows']=len(table)
                item['sha256']=ev.sha(target)
                if item.get('source') and (root/item['source']).is_file():item['source_sha256']=ev.sha(root/item['source'])
            ev.write_json(mp,m)
            links=''.join(f'<li><a href="{html.escape(i["file"])}">{html.escape(i["file"])}</a> — {html.escape(i["purpose"])}</li>' for i in m['files'])
            body=f'<a href="../INDEX.html">← Indeks</a><h1>{rid} — {html.escape(m["title"])}</h1><p>Selesai teknis; menunggu pemeriksaan pembimbing.</p><blockquote>{html.escape(m["requested_evidence"])}</blockquote><a href="../SUMBER/Daftar-Revisi-II-Pemeriksaan-Notebook-Joy.pdf#page={m["pdf_page"]}">PDF sumber</a><p><a href="{m["notebook"]["html"]}">Notebook FULL</a></p><ul>{links}</ul>'
            (folder/'BUKA_BUKTI.html').write_text(page(rid,body))
            (folder/'README.md').write_text(f'# {rid} — {m["title"]}\n\nSelesai teknis; menunggu pemeriksaan pembimbing.\n\n'+m['requested_evidence']+'\n\n'+'\n'.join(f'- [{i["file"]}]({i["file"]}) — {i["purpose"]}' for i in m['files'])+'\n\n'+'\n\n'.join(m.get('notes',[]))+'\n')
        index.append(dict(revision_id=rid,title=row['title'],status=row['status'],folder=rid if mp.exists() else '',files=len(m['files']) if mp.exists() else 0,remaining=row['remaining']))
    pd.DataFrame(index).to_csv(base/'INDEKS_28_REVISI.csv',index=False)
    completed=sum(r['status']=='Selesai' for r in index);open_count=28-completed
    body=f'<h1>Bukti per revisi — {release}</h1><p>{completed} selesai teknis · {open_count} terbuka.</p><table><tr><th>Butir</th><th>Judul</th><th>Status</th></tr>'
    for r in index:
        link=r['folder']+'/BUKA_BUKTI.html' if r['folder'] else 'BELUM_SELESAI.md#'+r['revision_id'].lower()
        body+=f'<tr><td><a href="{link}">{r["revision_id"]}</a></td><td>{html.escape(r["title"])}</td><td>{r["status"]}</td></tr>'
    (base/'INDEX.html').write_text(page('Bukti per revisi '+release,body+'</table>'))
    (base/'BELUM_SELESAI.md').write_text('# Butir yang masih terbuka\n\n'+'\n\n'.join(f'## {r["revision_id"]}\n\n{r["title"]}\n\n{r["remaining"]}' for r in index if r['status']!='Selesai')+'\n')
    (base/'README.md').write_text(f'# Bukti per revisi\n\nBuka INDEX.html. {completed} folder selesai teknis dan {open_count} butir terbuka mengikuti tracker {release}. Semua bukti tersedia ditampilkan pada tiga notebook. Selesai teknis bukan persetujuan pembimbing.\n')


def build(source,destination):
    source=Path(source).resolve();root=Path(destination).resolve();assert source.exists() and not root.exists()
    previous_manifest=ev.sha(source/'MANIFEST_SHA256.json')
    def ignore(folder,names):
        omit={'__pycache__'}
        if Path(folder)==source:omit|={'qa','MANIFEST_SHA256.json'}
        if Path(folder)==source/'BUKTI_PER_REVISI':omit|={'LAMPIRAN_BERSAMA','MANIFEST_SHA256.json'}
        return set(names)&omit
    shutil.copytree(source,root,ignore=ignore)
    copy(source/'MANIFEST_SHA256.json',root/'qa/previous_R3/PACKAGE_MANIFEST.json')
    for name in ['inputs/DATASET_740_TASK2_DOMAIN.csv','inputs/folds.csv']:
        assert ev.sha(root/name)==ev.sha(source/name)
    for p in HERE.glob('*.py'):
        if '_preflight_' not in p.name:
            copy(p,root/'tools'/p.name);copy(p,root/'source/DEMO_XAI_745_FULL/01_notebook/revisi_ii'/p.name)
    imported=import_results(root)
    print('Recomputing R4 analysis',flush=True);analysis=ev.run(root,root/'analysis',packaged=True)
    state=reports.create(root);r21=r21_tables(root);human=human_handoff(root)
    audit=subprocess.run([str(APP/'venv/bin/python'),str(HERE/'label_blind_bundle.py'),'probe','--workspace',str(REPO),
        '--bundle',str(REPO/'delivery/TINDAK_LANJUT_REVISI_20261102/R22_INPUT_TANPA_LABEL')],capture_output=True,text=True,check=True)
    ev.write_json(root/'documentation/R22_PROSPECTIVE_INPUT_AUDIT.json',json.loads(audit.stdout))
    provenance='\n\n## Pembaruan 8 November 2026\n\nAudit input allowlist tanpa gold dijalankan ulang: 740 ID dan 742 hash lulus; guard Python menolak pembacaan CSV gold asli. Ini bukti prospektif, bukan isolasi OS atau bukti proses historis. Regenerasi fitur tidak dijalankan: tanpa keputusan metodologis, mengganti fitur akan mengubah eksperimen dan tidak memulihkan timestamp lama. Pemeriksaan 20 contoh oleh manusia disediakan pada UNTUK_MANUSIA/R22_REVIEW_MANUSIA_20.csv.\n'
    p=root/'documentation/FEATURE_PROVENANCE.md';p.write_text(p.read_text()+provenance)
    release='R5' if '_R5' in root.name else 'R4'
    refresh_evidence(root,release)
    (root/'README.md').write_text(f'''# Revisi II Joy — R4, 8 November 2026

**{state['completed']}/28 selesai teknis; {state['open']} masih terbuka.** R21 basic supporting telah dikoleksi: lima fold,740 prediksi nyata. Permintaan literal citra+judul ditampilkan terpisah; nilainya tidak diisi dari arm supporting atau smoke. Model utama tetap E42, metrik utama Macro-F1.

- Buka MULAI_DI_SINI.html, notebook_html/ atau notebooks/. Tiga notebook berisi output tersimpan; Run all hanya menghitung analisis prediksi pada CPU, tanpa training/API.
- Tugas manusia dan berkas pengembalian: UNTUK_MANUSIA/MULAI_DI_SINI.md. ZIP individual hanya untuk penerima masing-masing. Jangan membagikan coordinator_private kepada penilai.
- Tabel R21: documentation/R21_HASIL_TERKINI.md, R21_TABEL_2X2.md dan R21_LITERAL_2X2.md. Batas konteks dan resep inner rich tetap diungkapkan.
- Ulang analisis: buat venv Python3.10 kompatibel, pasang requirements-analysis-lock.txt; jalankan `python tools/evaluate.py --package --workspace . --output analysis`, lalu `python tools/validate_package.py --root .`.
- Colab: gunakan COLAB_RUN_ALL.ipynb dan R32_ANALISIS_PORTABEL.zip yang berpasangan dari folder R32 pendamping. Bukti Colab masih Not Evaluated sampai laporan runtime nyata serta screenshot tersedia. Akses browser Colab tidak tersedia pada sesi ini.
- Source, split, hasil, protokol dan hash disertakan. Menjalankan ulang training/XAI memerlukan bobot/cache dan lingkungan ML tersendiri. Demo web historis CLIP-B32 bukan inferensi E42.
- Seluruh paket R3 dan arsip lama dipertahankan. Tidak ada label, rating manusia, timestamp historis atau keputusan pembimbing yang dibuat agent.
'''.replace('fold,740','fold, 740').replace('Python3.10','Python 3.10'))
    copy(root/'README.md',root/'BUKA_DULU.md');copy(root/'README.md',root/'VERSI_FULL.md')
    (root/'MULAI_DI_SINI.html').write_text(page('Revisi II Joy — R4',f'<h1>Revisi II Joy — R4</h1><p>8 November 2026 · {state["completed"]} selesai teknis / {state["open"]} terbuka.</p><p>R21 supporting: 740 prediksi terverifikasi. Lihat tabel literal untuk citra+judul.</p><ul><li><a href="notebook_html/01_baseline.html">01 Baseline</a></li><li><a href="notebook_html/02_experiments.html">02 Eksperimen dan XAI</a></li><li><a href="notebook_html/03_final_comparison.html">03 Hasil dan status</a></li><li><a href="BUKTI_PER_REVISI/INDEX.html">Bukti per revisi</a></li><li><a href="UNTUK_MANUSIA/MULAI_DI_SINI.md">Tugas manusia dan berkas isian</a></li><li><a href="documentation/R21_LITERAL_2X2.md">R21 citra+judul literal</a></li><li><a href="README.md">Reproduksi dan batas bukti</a></li></ul>'))
    for name in ['README.md','BUKA_DULU.md','VERSI_FULL.md','MULAI_DI_SINI.html']:
        path=root/name;path.write_text(path.read_text().replace('R4',release))
    local=build_notebooks.create(root,execute=True,full_evidence=True)
    reference_html(root)
    evidence=verify_evidence(root)
    canonical=validate(root);coverage=verify_full(root)
    assert ev.sha(source/'MANIFEST_SHA256.json')==previous_manifest
    unchanged=[]
    for folder in ['lampiran_model','human_inputs','xai_e42']:
        for p in (source/folder).rglob('*'):
            if p.is_file():assert ev.sha(p)==ev.sha(root/p.relative_to(source));unchanged.append(p.relative_to(source).as_posix())
    result=dict(status='verified',created_at=datetime.now(timezone.utc).isoformat(),release=root.name,imported_results=imported,
        analysis_models=analysis['models'],metric_rows=analysis['metric_rows'],state=state,r21=r21,human_handoff=human,notebooks=local,
        canonical=canonical,coverage=coverage,evidence=evidence,unchanged_model_human_xai_files=len(unchanged),
        previous_release_manifest_sha256=previous_manifest,colab_verified=False,browser_access='No browsers available; iab unavailable',
        labelled_dataset_changed=False,training_in_run_all=False)
    ev.write_json(root/'qa/TECHNICAL_VERIFICATION.json',result)
    ev.write_json(root/'qa/LOCAL_NOTEBOOK_VERIFICATION.json',dict(status='verified',notebooks=local,environment='local Linux Python',colab='Not Evaluated'))
    return root,result


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path,required=True);ap.add_argument('--destination',type=Path,required=True);ap.add_argument('--archive',type=Path)
    args=ap.parse_args();root,result=build(args.source,args.destination)
    if args.archive:seal(root,args.archive)
    print(json.dumps(result,indent=2,ensure_ascii=False))
