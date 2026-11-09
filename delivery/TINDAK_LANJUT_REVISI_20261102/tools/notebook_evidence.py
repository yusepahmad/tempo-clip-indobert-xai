"""Render and verify every available revision artifact in saved notebook outputs."""
import base64
import hashlib
import html
import json
from pathlib import Path
import re
from urllib.parse import quote, unquote, urlsplit

from bs4 import BeautifulSoup
import nbformat as nbf
import pandas as pd
from IPython.display import HTML, Image, Markdown, display
from nbconvert.filters.markdown import markdown2html


BASELINE='01_baseline.ipynb'
EXPERIMENTS='02_experiments.ipynb'
COMPARISON='03_final_comparison.ipynb'
OPEN_LOCATION={'R21':EXPERIMENTS,'R22':EXPERIMENTS,'R23':BASELINE,
               'R31':EXPERIMENTS,'R32':COMPARISON,'R34':EXPERIMENTS,
               'R6':BASELINE,'R8':BASELINE,'R9':EXPERIMENTS}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_catalog(root):
    root=Path(root)
    return json.loads((root/'documentation/NOTEBOOK_FULL_COVERAGE.json').read_text())


def prepare_catalog(root):
    root=Path(root);items=[];represented=set();locations={}
    for path in sorted((root/'BUKTI_PER_REVISI').glob('R*/BUKTI_MANIFEST.json'),key=lambda p:int(p.parent.name[1:])):
        m=json.loads(path.read_text());rid=m['revision_id'];nb=m['notebook']['notebook'];locations[rid]=nb
        for file in m['files']:
            relative=f"BUKTI_PER_REVISI/{rid}/{file['file']}"
            assert digest(root/relative)==file['sha256'],relative
            items.append(dict(revision_id=rid,notebook=nb,path=relative,sha256=file['sha256'],purpose=file['purpose']))
            if file['kind']=='copy':represented.add(file['source'])
    # A filtered subset does not cover its entire canonical table.
    for folder in ['analysis','documentation']:
        for path in sorted((root/folder).iterdir()):
            if not path.is_file() or path.name.startswith('NOTEBOOK_FULL_'):continue
            relative=path.relative_to(root).as_posix()
            if relative in represented:continue
            if folder=='analysis':
                nb=EXPERIMENTS if any(s in path.name for s in ['confusion','entropy','class_distribution','catchall','task2_']) else COMPARISON
            else:
                nb=BASELINE if any(s in path.name for s in ['CORPUS','HUMAN_EVIDENCE','R23_']) else EXPERIMENTS if any(s in path.name for s in ['INPUT_PARITY','FEATURE_PROVENANCE','feature_provenance','PROMPT_GOLD','XAI_']) else COMPARISON
            items.append(dict(revision_id='LAMPIRAN',notebook=nb,path=relative,sha256=digest(path),purpose='Lampiran canonical lengkap; data tersedia tanpa pemotongan baris.'))
    tracker=pd.read_csv(root/'documentation/REVISION_TRACKER_28.csv').fillna('')
    revisions=[]
    for row in tracker.to_dict('records'):
        row['notebook']=locations.get(row['revision_id'],OPEN_LOCATION.get(row['revision_id'],COMPARISON))
        row['available_files']=[]
        for token in row['evidence'].split(';'):
            token=token.strip();relative=token if (root/token).exists() else 'documentation/'+token
            if (root/relative).exists():row['available_files'].append(relative.rstrip('/'))
        revisions.append(row)
    result=dict(schema='joy-notebook-full-v1',items=items,revisions=revisions,
                completed_evidence_files=sum(i['revision_id']!='LAMPIRAN' for i in items),
                canonical_extra_files=sum(i['revision_id']=='LAMPIRAN' for i in items))
    (root/'documentation/NOTEBOOK_FULL_COVERAGE.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
    return result


def local_link(relative):
    return '../'+quote(relative,safe='/')


def render_file(root,item):
    root=Path(root);path=root/item['path'];actual=digest(path)
    assert actual==item['sha256'],item['path']
    relative=item['path'];escaped=html.escape(relative);suffix=path.suffix.lower()
    display(HTML(f'<div class="full-evidence-file" data-file="{escaped}" data-sha256="{actual}">'
                 f'<h4>{escaped}</h4><p>{html.escape(item["purpose"])}</p>'
                 f'<p><a href="{local_link(relative)}">Buka berkas asli</a></p></div>'))
    if suffix in {'.png','.jpg','.jpeg'}:
        display(Image(filename=str(path)))
    elif suffix=='.csv':
        data=pd.read_csv(path).fillna('')
        display(HTML(f'<p>{len(data)} baris × {len(data.columns)} kolom; seluruh baris ditampilkan.</p>'
                     f'<div class="full-evidence-table" data-file="{escaped}" data-rows="{len(data)}" '
                     'style="max-height:520px;overflow:auto;max-width:100%">'
                     +data.to_html(index=False,max_rows=None,max_cols=None,border=0)+'</div>'))
    elif suffix=='.md':
        soup=BeautifulSoup(str(markdown2html(path.read_text())), 'html.parser')
        for tag in soup.find_all(['a','img']):
            attribute='href' if tag.name=='a' else 'src';value=tag.get(attribute,'');u=urlsplit(value)
            if not value or u.scheme or value.startswith('#'):continue
            # Source docs sometimes use workspace paths. Only rewrite paths that
            # actually exist in this release; the verifier checks all local links.
            candidates=[path.parent/unquote(u.path),root/'documentation'/unquote(u.path),root/unquote(u.path)]
            target=next((p.resolve() for p in candidates if p.exists() and p.resolve().is_relative_to(root.resolve())),None)
            if target:
                tag[attribute]=local_link(target.relative_to(root.resolve()).as_posix())+('#'+u.fragment if u.fragment else '')
        display(HTML(str(soup)))
    elif suffix in {'.json','.py','.txt'}:
        value=path.read_text()
        if suffix=='.json':value=json.dumps(json.loads(value),ensure_ascii=False,indent=2)
        label='JSON lengkap' if suffix=='.json' else 'Source lengkap'
        display(HTML(f'<details><summary>{label} — {html.escape(path.name)}</summary>'
                     '<pre style="max-height:520px;overflow:auto;white-space:pre-wrap;overflow-wrap:anywhere">'
                     +html.escape(value)+'</pre></details>'))
    else:
        raise AssertionError('Unsupported evidence format: '+relative)


def render_group(root,group,notebook):
    items=[i for i in load_catalog(root)['items'] if i['revision_id']==group and i['notebook']==notebook]
    assert items,(group,notebook)
    for item in items:render_file(root,item)


def append_full_evidence(root,cells):
    catalog=prepare_catalog(root);md=nbf.v4.new_markdown_cell;code=nbf.v4.new_code_cell
    for name,body in cells.items():
        rows=[r for r in catalog['revisions'] if r['notebook']==name]
        toc='## Versi FULL — peta bukti\n\nSeluruh berkas bukti yang sudah tersedia ditampilkan pada lampiran notebook ini, termasuk seluruh baris CSV dan semua gambar XAI. Status terbuka tetap memuat bukti yang tersedia serta pekerjaan tersisa.\n\n'
        toc+='[Indeks seluruh 28 revisi](../BUKTI_PER_REVISI/INDEX.html) · [Daftar cakupan lengkap](../documentation/NOTEBOOK_FULL_COVERAGE.json)\n\n| Butir | Bagian | Status |\n|---|---|---|\n'
        for row in rows:
            rid=row['revision_id'];toc+=f"| {rid} | [{row['title']}](#full-{rid.lower()}) | {row['status']} |\n"
        toc+='\n[Lampiran canonical lengkap](#full-lampiran)\n'
        body.insert(1,md(toc))
        body.append(md('## Lampiran FULL — bukti per revisi\n\nFile asli tetap disertakan. Tabel besar dapat digulir; JSON dan source lengkap dapat dibuka melalui panel. Gambar historis diberi tanggal pada nama/sumbernya.'))
        body.append(code('from notebook_evidence import render_group'))
        for row in rows:
            rid=row['revision_id']
            text=f'<a id="full-{rid.lower()}"></a>\n\n## {rid} — {row["title"]}\n\n**Status: {row["status"]}.**\n\n'
            selected=[i for i in catalog['items'] if i['revision_id']==rid]
            if selected:
                manifest=json.loads((Path(root)/f'BUKTI_PER_REVISI/{rid}/BUKTI_MANIFEST.json').read_text())
                text+='Permintaan bukti: '+manifest['requested_evidence']+'\n\n'
                text+=f"[Navigasi bukti {rid}](../BUKTI_PER_REVISI/{rid}/BUKA_BUKTI.html)\n\n"
                text+='\n\n'.join(manifest.get('notes',[]))
            else:
                text+='**Yang belum selesai:** '+row['remaining']+'\n\n**Penanggung jawab:** '+row['owner']+'\n\nBukti/instrumen yang sudah tersedia:\n\n'
                text+='\n'.join(f'- [{p}]({local_link(p)})' for p in row['available_files'])
                text+='\n\nInstrumen kosong bukan hasil penilaian manusia. Materi analisis/provenance yang tersedia ditampilkan pada bagian utama atau lampiran canonical.\n'
            body.append(md(text))
            if selected:
                c=code(f'render_group(ROOT, {rid!r}, {name!r})')
                c.metadata['full_evidence_paths']=[i['path'] for i in selected];body.append(c)
        body.append(md('<a id="full-lampiran"></a>\n\n## Lampiran canonical lengkap\n\nTabel dan dokumen berikut melengkapi bukti per revisi. CSV ditampilkan seluruhnya; inventaris JSON lengkap tersedia di panel.'))
        extras=[i for i in catalog['items'] if i['revision_id']=='LAMPIRAN' and i['notebook']==name]
        if extras:
            c=code(f'render_group(ROOT, "LAMPIRAN", {name!r})')
            c.metadata['full_evidence_paths']=[i['path'] for i in extras];body.append(c)


def verify_full(root):
    root=Path(root).resolve();catalog=load_catalog(root);found={};image_hashes=set();tables=0;links=0
    for path in sorted((root/'notebooks').glob('0*.ipynb')):
        nb=nbf.read(path,as_version=4);assert nb.metadata.tempo_revision.full_evidence
        for c in nb.cells:
            expected=c.metadata.get('full_evidence_paths',[]);actual=[]
            if c.cell_type!='code':continue
            assert c.execution_count is not None
            for o in c.outputs:
                assert o.output_type!='error'
                data=o.get('data',{})
                for mime in ['image/png','image/jpeg']:
                    if mime in data:image_hashes.add(hashlib.sha256(base64.b64decode(data[mime])).hexdigest())
                if 'text/html' not in data:continue
                soup=BeautifulSoup(data['text/html'],'html.parser')
                for marker in soup.select('.full-evidence-file'):
                    rel=marker['data-file'];assert marker['data-sha256']==digest(root/rel)
                    assert rel not in found,rel
                    found[rel]=path.name;actual.append(rel)
                for table in soup.select('.full-evidence-table'):
                    rel=table['data-file'];rows=len(pd.read_csv(root/rel))
                    assert int(table['data-rows'])==len(table.select('tbody tr'))==rows,rel;tables+=1
            assert actual==expected,(path.name,expected,actual)
    assert set(found)=={i['path'] for i in catalog['items']}
    for i in catalog['items']:
        assert found[i['path']]==i['notebook']
        if Path(i['path']).suffix.lower() in {'.png','.jpg','.jpeg'}:assert i['sha256'] in image_hashes,i['path']
    nb2=nbf.read(root/'notebooks'/EXPERIMENTS,as_version=4)
    diagnosis=next(c for c in nb2.cells if c.cell_type=='code' and "plot('confusion_task3_BASELINE_CLIP_INDoBERT.png')" in c.source)
    assert sum('image/png' in o.get('data',{}) for o in diagnosis.outputs)==4
    html_paths=list((root/'notebook_html').glob('*.html'))+list((root/'BUKTI_PER_REVISI/REFERENSI_NOTEBOOK').glob('*.html'))
    cached_ids={}
    def ids(path,soup=None):
        if path not in cached_ids:
            if soup is None:soup=BeautifulSoup(path.read_text(),'html.parser')
            cached_ids[path]={t['id'] for t in soup.find_all(id=True)}
        return cached_ids[path]
    for path in html_paths:
        soup=BeautifulSoup(path.read_text(),'html.parser');ids(path,soup)
        for tag in soup.find_all(['a','img']):
            value=tag.get('href' if tag.name=='a' else 'src','');u=urlsplit(value)
            if not value or u.scheme or u.netloc:continue
            target=(path.parent/unquote(u.path)).resolve() if u.path else path
            assert target.is_relative_to(root) and target.exists(),(path,value)
            if u.fragment and target.suffix=='.html':
                target_ids=ids(target,soup if target==path else None)
                assert u.fragment in target_ids or unquote(u.fragment) in target_ids,(path,value)
            links+=1
    for row in catalog['revisions']:
        for folder in ['notebook_html','BUKTI_PER_REVISI/REFERENSI_NOTEBOOK']:
            path=root/folder/(Path(row['notebook']).stem+'.html')
            assert 'full-'+row['revision_id'].lower() in ids(path),row['revision_id']
    represented={i['path'] for i in catalog['items']}
    for mpath in (root/'BUKTI_PER_REVISI').glob('R*/BUKTI_MANIFEST.json'):
        for i in json.loads(mpath.read_text())['files']:
            if i['kind']=='copy':represented.add(i['source'])
    for folder in ['analysis','documentation']:
        for path in (root/folder).iterdir():
            if path.is_file() and not path.name.startswith('NOTEBOOK_FULL_'):
                assert path.relative_to(root).as_posix() in represented,path
    return dict(status='verified',revision_rows=len(catalog['revisions']),completed_evidence_files=catalog['completed_evidence_files'],
                canonical_extra_files=catalog['canonical_extra_files'],rendered_files=len(found),full_csv_tables=tables,
                embedded_image_hashes=len(image_hashes),diagnostic_matrices_notebook02=4,html_local_links_checked=links,
                missing_evidence_files=0,missing_revision_sections=0,unrendered_canonical_files=0,
                scope='All available evidence; open human/GPU/Colab requirements remain open.')
