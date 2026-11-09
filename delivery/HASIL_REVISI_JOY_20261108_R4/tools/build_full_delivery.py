"""Create R3 FULL from preserved R2 evidence; no training or relabeling."""
import argparse
import html
import json
from pathlib import Path
import shutil
from urllib.parse import quote, unquote, urlsplit
import os
import zipfile

from bs4 import BeautifulSoup
import pandas as pd

import build_notebooks
from build_revision_evidence import page, verify
from evaluate import sha, write_json
from notebook_evidence import verify_full
from validate_package import validate

HERE=Path(__file__).resolve().parent


def refresh_evidence(root):
    base=root/'BUKTI_PER_REVISI'
    path=base/'R20/BUKTI_MANIFEST.json';m=json.loads(path.read_text())
    for ext in ['png','csv']:
        source=f'analysis/confusion_task3_MICRO_E14_joint_qlora_oof.{ext}'
        name=f'R20_confusion_MICRO_E14_joint_qlora_oof.{ext}'
        shutil.copy2(root/source,base/'R20'/name)
        m['files'].append(dict(file=name,purpose='Confusion matrix Task 3 pembanding E14 QLoRA; melengkapi baseline, E11 dan E42.',
                               sha256=sha(root/source),kind='copy',source=source,source_sha256=sha(root/source)))
    m['notes'].append('Versi FULL menampilkan empat confusion matrix: baseline, E11, E42, dan pembanding E14 tambahan. Distribusi/entropi semua empat model juga tersedia di notebook 02 dan analysis/.')
    write_json(path,m)
    tracker=pd.read_csv(root/'documentation/REVISION_TRACKER_28.csv').fillna('')
    index=[]
    for row in tracker.to_dict('records'):
        rid=row['revision_id'];path=base/rid/'BUKTI_MANIFEST.json';done=path.exists()
        if done:
            m=json.loads(path.read_text());stem=Path(m['notebook']['notebook']).stem
            m['notebook']['heading']=f'{rid} — '+m['title']
            m['notebook']['html']=f'../REFERENSI_NOTEBOOK/{stem}.html#full-{rid.lower()}'
            write_json(path,m)
            rows=''.join(f'<tr><td><a href="{quote(i["file"],safe="/")}">{html.escape(i["file"])}</a></td><td>{html.escape(i["purpose"])}</td></tr>' for i in m['files'])
            body=f'<p><a href="../INDEX.html">← Semua revisi</a></p><h1>{rid} — {html.escape(m["title"])}</h1><p class="state">Selesai teknis; menunggu penilaian pembimbing.</p><h2>Bukti yang diminta</h2><blockquote>{html.escape(m["requested_evidence"])}</blockquote><p><a href="../SUMBER/Daftar-Revisi-II-Pemeriksaan-Notebook-Joy.pdf#page={m["pdf_page"]}">PDF sumber halaman {m["pdf_page"]}</a></p><p><a href="{m["notebook"]["html"]}"><strong>Baca seluruh bukti langsung di notebook FULL</strong></a></p><table><thead><tr><th>File</th><th>Kegunaan</th></tr></thead><tbody>{rows}</tbody></table>'
            body+=''.join('<p>'+html.escape(n)+'</p>' for n in m.get('notes',[]))
            (base/rid/'BUKA_BUKTI.html').write_text(page(rid+' — '+m['title'],body))
            (base/rid/'README.md').write_text(f'# {rid} — {m["title"]}\n\nStatus: selesai teknis; menunggu penilaian pembimbing.\n\n## Bukti yang diminta\n\n'+m['requested_evidence']+'\n\n## Semua berkas\n\n'+'\n'.join(f'- [{i["file"]}]({i["file"]}) — {i["purpose"]}' for i in m['files'])+f'\n\n## Notebook FULL\n\n[{m["notebook"]["notebook"]}]({m["notebook"]["html"]})\n\n'+'\n\n'.join(m.get('notes',[]))+'\n')
        index.append(dict(revision_id=rid,title=row['title'],status=row['status'],folder=rid if done else '',files=len(m['files']) if done else 0,remaining=row['remaining']))
    pd.DataFrame(index).to_csv(base/'INDEKS_28_REVISI.csv',index=False)
    body='<h1>Versi FULL — bukti seluruh revisi</h1><p class="state">19 butir selesai teknis · 9 masih terbuka. Seluruh bukti yang tersedia telah dimasukkan ke tiga notebook.</p><table><thead><tr><th>Butir</th><th>Permintaan</th><th>Status</th><th>Berkas</th></tr></thead><tbody>'
    for r in index:
        link=r['folder']+'/BUKA_BUKTI.html' if r['folder'] else 'BELUM_SELESAI.md#'+r['revision_id'].lower()
        body+=f'<tr><td><a href="{link}">{r["revision_id"]}</a></td><td>{html.escape(r["title"])}</td><td>{r["status"]}</td><td>{r["files"]}</td></tr>'
    body+='</tbody></table><p><a href="REFERENSI_NOTEBOOK/01_baseline.html">Notebook 01 FULL</a> · <a href="REFERENSI_NOTEBOOK/02_experiments.html">Notebook 02 FULL</a> · <a href="REFERENSI_NOTEBOOK/03_final_comparison.html">Notebook 03 FULL</a></p>'
    (base/'INDEX.html').write_text(page('Bukti FULL — Joy',body))
    (base/'README.md').write_text('# Bukti FULL\n\nBuka INDEX.html. Semua 141 berkas bukti pada 19 butir selesai teknis ditampilkan langsung di notebook FULL. Sembilan butir terbuka tetap memuat status dan kekurangan. REFERENSI_NOTEBOOK dapat dibaca tanpa training. LAMPIRAN_BERSAMA menyertakan target tautan lokal supaya ZIP bukti tetap mandiri untuk dibaca. Run all memakai paket lengkap.\n')


def reference_html(root):
    """Rebase references and include dependencies so the evidence ZIP stands alone."""
    base=root/'BUKTI_PER_REVISI';support=base/'LAMPIRAN_BERSAMA'
    for source in (root/'notebook_html').glob('*.html'):
        target=base/'REFERENSI_NOTEBOOK'/source.name
        soup=BeautifulSoup(source.read_text(),'html.parser')
        for tag in soup.find_all(['a','img']):
            attribute='href' if tag.name=='a' else 'src';value=tag.get(attribute,'');u=urlsplit(value)
            if not value or u.scheme or u.netloc or not u.path:continue
            original=(source.parent/unquote(u.path)).resolve()
            assert original.is_relative_to(root) and original.exists(),(source,value)
            if original.is_relative_to(base):destination=original
            else:
                destination=support/original.relative_to(root)
                if original.is_dir():shutil.copytree(original,destination,dirs_exist_ok=True,ignore=shutil.ignore_patterns('__pycache__'))
                else:destination.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(original,destination)
            tag[attribute]=quote(os.path.relpath(destination,target.parent),safe='/')+('#'+u.fragment if u.fragment else '')
        target.write_text(str(soup))


def unchanged(source,root):
    checked=[]
    for folder in ['inputs','analysis','lampiran_model','human_inputs','experiment_protocols','xai_e42']:
        old={p.relative_to(source).as_posix():sha(p) for p in (source/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts}
        new={p.relative_to(root).as_posix():sha(p) for p in (root/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts}
        assert old==new,{'folder':folder,'different':[p for p in old.keys()|new.keys() if old.get(p)!=new.get(p)]}
        checked.extend(old)
    return dict(status='verified',previous_release=source.name,unchanged_files=len(checked),folders=['inputs','analysis','lampiran_model','human_inputs','experiment_protocols','xai_e42'],training=False,metrics_or_labels_changed=False)


def build(source,destination):
    source=Path(source).resolve();root=Path(destination).resolve()
    assert source.exists() and not root.exists()
    shutil.copytree(source,root,ignore=shutil.ignore_patterns('__pycache__'))
    prior=root/'qa/previous_R2';prior.mkdir()
    for path in list((root/'qa').iterdir()):
        if path!=prior:shutil.move(str(path),prior/path.name)
    shutil.move(str(root/'MANIFEST_SHA256.json'),prior/'PACKAGE_MANIFEST_R2.json')
    (root/'BUKTI_PER_REVISI/MANIFEST_SHA256.json').unlink()
    for name in ['build_notebooks.py','notebook_evidence.py','build_full_delivery.py','check_full_omissions.py','verify_full_archive.py']:
        shutil.copy2(HERE/name,root/'tools'/name)
        shutil.copy2(HERE/name,root/'source/DEMO_XAI_745_FULL/01_notebook/revisi_ii'/name)
    refresh_evidence(root)
    local=build_notebooks.create(root,execute=True,full_evidence=True)
    return finalize(source,root,local)


def finalize(source,root,local):
    source=Path(source).resolve();root=Path(root).resolve()
    reference_html(root)
    results=dict(notebooks=local,full_coverage=verify_full(root),evidence=verify(root),canonical=validate(root),unchanged=unchanged(source,root))
    write_json(root/'qa/FULL_NOTEBOOK_VERIFICATION.json',results)
    write_json(root/'qa/LOCAL_NOTEBOOK_VERIFICATION.json',dict(status='verified',notebooks=local,environment='local Linux Python; Run all',colab='Not Evaluated'))
    write_json(root/'qa/RELEASE_QA_SCOPE.json',dict(status='verified',release='R3_FULL',coverage=results['full_coverage'],completed=19,open=9,training=False,colab='Not Evaluated',previous_qa='previous_R2/'))
    summary='# Versi R3 FULL — hasil audit\n\n'
    summary+='Ketiga notebook berisi output tersimpan dan seluruh bukti yang tersedia. Empat confusion matrix Task 3 (baseline, E42, E11, E14), tabel distribusi/entropi/weighting, seluruh gambar XAI, tabel lengkap dan source bukti telah dimasukkan.\n\n'
    summary+=f"- {results['full_coverage']['completed_evidence_files']} berkas bukti per revisi dan {results['full_coverage']['canonical_extra_files']} lampiran canonical ditampilkan.\n- Seluruh 28 butir memiliki bagian notebook; 19 selesai teknis, 9 masih terbuka.\n- Semua tiga notebook lulus Run all lokal; bukti Colab dan penilaian manusia tetap sesuai status.\n- {results['unchanged']['unchanged_files']} file data/prediksi/analisis/model/instrumen/protokol/XAI identik dengan R2.\n\n"
    summary+='Mulai dari **MULAI_DI_SINI.html**. Notebook di **notebooks/**, HTML di **notebook_html/**. Rincian pemeriksaan ada di **qa/FULL_NOTEBOOK_VERIFICATION.json** dan cakupan per file di **documentation/NOTEBOOK_FULL_COVERAGE.json**.\n'
    (root/'VERSI_FULL.md').write_text(summary)
    for name in ['README.md','BUKA_DULU.md']:
        p=root/name;p.write_text(summary+'\n---\n\n'+p.read_text())
    p=root/'MULAI_DI_SINI.html';soup=BeautifulSoup(p.read_text(),'html.parser')
    soup.title.string='Revisi II — Joy — R3 FULL'
    main=soup.find('main');banner=BeautifulSoup('<p class="state"><strong>R3 FULL — seluruh bukti tersedia dimasukkan ke notebook.</strong><br>4 confusion matrix Task 3 · seluruh gambar XAI · tabel lengkap · 28 bagian revisi.<br><a href="VERSI_FULL.md">Hasil audit kelengkapan</a></p>','html.parser');main.insert(0,banner)
    p.write_text(str(soup))
    return root,results


def seal(root,archive):
    """Hash nested evidence manifests too; only exclude the manifest itself."""
    root=Path(root).resolve();archive=Path(archive).resolve();assert not archive.exists()
    paths=[p for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p!=root/'MANIFEST_SHA256.json']
    write_json(root/'MANIFEST_SHA256.json',dict(schema='joy-revisi-ii-manifest-v1',files={p.relative_to(root).as_posix():sha(p) for p in sorted(paths)}))
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in sorted(root.rglob('*')):
            if p.is_file() and '__pycache__' not in p.parts:z.write(p,Path('joy_revisi_ii')/p.relative_to(root))
    with zipfile.ZipFile(archive) as z:assert z.testzip() is None
    archive.with_suffix('.zip.sha256').write_text(f'{sha(archive)}  {archive.name}\n')
    return archive


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--source',required=True,type=Path);ap.add_argument('--destination',required=True,type=Path)
    args=ap.parse_args();root,results=build(args.source,args.destination);print(json.dumps(results,indent=2))
