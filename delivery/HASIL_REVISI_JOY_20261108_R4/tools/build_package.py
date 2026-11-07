"""Build a new self-contained Joy revision package; never replace legacy ZIPs."""
import argparse
import html
import importlib.metadata
import json
from pathlib import Path
import shutil
import zipfile
from evaluate import TASKS,discover,run,sha,write_json
import reports
import build_notebooks
import r18_material

HERE=Path(__file__).resolve().parent;APP=HERE.parents[1];REPO=APP.parent


def copy(source,target):
    target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)


def build(destination,execute=True):
    r18_material.create()
    root=Path(destination).resolve();root.mkdir(parents=True,exist_ok=True)
    inputs=root/'inputs';(inputs/'predictions').mkdir(parents=True,exist_ok=True)
    reference,folds,frames,records,rejected=discover(REPO)
    copy(APP/'03_data/DATASET_740_TASK2_DOMAIN.csv',inputs/'DATASET_740_TASK2_DOMAIN.csv')
    folds.rename_axis('sample_id').reset_index().to_csv(inputs/'folds.csv',index=False)
    normalized=[]
    for record in records:
        name=record['experiment'];target=inputs/'predictions'/f'{name}.csv'
        frames[name].to_csv(target,index=False)
        normalized.append({**record,'package_path':str(target.relative_to(root)),'package_sha256':sha(target)})
    write_json(inputs/'sources.json',dict(sources=normalized,rejected_sources=rejected,
         note='Source paths/hashes refer to preserved original artifacts; package_path/hash identifies normalized local input. Prediction signatures are ID-sorted.'))
    tools=root/'tools';tools.mkdir(exist_ok=True)
    for p in HERE.glob('*.py'):
        if '_preflight_' not in p.name:copy(p,tools/p.name)
    doc=root/'documentation';doc.mkdir(exist_ok=True)
    source_docs=REPO/'docs/revisi-ii'
    for p in source_docs.glob('*'):
        if p.is_file() and p.suffix in {'.md','.csv','.json'} and 'PRIVATE' not in p.name:copy(p,doc/p.name)
    if (source_docs/'notebook_evidence').exists():
        shutil.copytree(source_docs/'notebook_evidence',root/'screenshots',dirs_exist_ok=True)
    if (source_docs/'human_inputs').exists():shutil.copytree(source_docs/'human_inputs',root/'human_inputs',dirs_exist_ok=True)
    private=source_docs/'XAI_COORDINATOR_KEY_PRIVATE.csv'
    if private.exists():copy(private,root/'coordinator_private'/private.name)
    (root/'coordinator_private').mkdir(exist_ok=True)
    (root/'coordinator_private/README.md').write_text('# Kunci kontrol XAI\n\nHanya untuk koordinator penelitian. Jangan sertakan folder ini saat membagikan paket kepada penilai. Gunakan ZIP penilai terpisah.\n')
    xai=APP/'04_hasil_eksperimen/revisi_ii/xai_e42'
    if xai.exists():shutil.copytree(xai,root/'xai_e42',dirs_exist_ok=True)
    # Preserve source and small audit/config artifacts in their original relative
    # tree. Large pretrained/model/cache files are explicitly optional annexes.
    source=root/'source'
    for folder in [APP/'01_notebook',APP/'02_web_demo']:
        for p in folder.rglob('*'):
            if not p.is_file() or any(v in p.parts for v in ['__pycache__','_cache','_jobs','venv','node_modules']):continue
            if p.suffix in {'.py','.js','.html','.md','.yaml','.yml'} and p.stat().st_size<3_000_000:
                copy(p,source/p.relative_to(REPO))
    for base in [APP/'04_hasil_eksperimen',REPO/'docs/server-recovery']:
        for p in base.rglob('*'):
            if not p.is_file() or 'revisi_ii' in p.parts or any(v in p.parts for v in ['__pycache__','package','raw_kaggle','cancelled_v1']):continue
            if p.name in {'result.json','metrics.json','protocol.json','frozen_protocol.json','config.json','features_manifest.json','manifest_sha256.json','root_verification.json','worker.py','e01_vlm.py'} and p.stat().st_size<3_000_000:
                copy(p,source/p.relative_to(REPO))
    e01=REPO/'docs/server-recovery/2026-10-10/e01-full-terbaru/e01_vlm'
    for name in ['deskripsi.jsonl','zeroshot.jsonl','meta.json','tahap.log']:copy(e01/name,source/e01.relative_to(REPO)/name)
    for p in (APP/'04_hasil_eksperimen/revisi_ii').glob('*protocol.json'):copy(p,root/'experiment_protocols'/p.name)
    for p in (APP/'04_hasil_eksperimen/revisi_ii/experiments').rglob('*.json'):
        if p.stat().st_size<3_000_000:
            copy(p,root/'experiment_protocols/experiments'/p.relative_to(APP/'04_hasil_eksperimen/revisi_ii/experiments'))
    for group in ['gpu_jobs','tail_input_jobs','qwen_zero_jobs','qwen_basic_jobs','augmentation']:
        folder=APP/'04_hasil_eksperimen/revisi_ii'/group
        if folder.exists():
            for p in folder.rglob('*.json'):
                if p.stat().st_size<1_500_000:copy(p,root/'experiment_protocols'/group/p.relative_to(folder))
    requirements=['numpy','pandas','scipy','scikit-learn','matplotlib','nbformat','nbclient','nbconvert','ipykernel','Pillow']
    (root/'requirements.txt').write_text('\n'.join(f'{p}=={importlib.metadata.version(p)}' for p in requirements)+'\n')
    copy(HERE/'requirements-analysis-lock.txt',root/'requirements-analysis-lock.txt')
    ml=['torch','transformers','open_clip_torch','lime','Flask']
    (root/'requirements-ml-reference.txt').write_text('# Historical local ML versions; optional GPU/Kaggle environments have their own pins.\n'+'\n'.join(f'{p}=={importlib.metadata.version(p)}' for p in ml)+'\n')
    run(root,root/'analysis',packaged=True)
    state=reports.create(root)
    (root/'README.md').write_text(f'''# Revisi II Notebook Joy — paket penelitian

Status saat build: **{state['completed']} dari28butir selesai secara teknis; {state['open']} masih terbuka**. Paket siap untuk diperiksa Joy dan berisi bukti yang tersedia, bukan klaim seluruh revisi telah ditutup. Lihat `documentation/TINDAK_LANJUT_JOY.md` sebelum meneruskan sebagai hasil final.

## Mulai membaca
1. Buka `MULAI_DI_SINI.html` untuk ringkasan, lalu `notebook_html/03_final_comparison.html` atau notebook di `notebooks/`.
2. Ketiga notebook memiliki output tersimpan setelah pengujian lokal. Membaca hasil tidak memerlukan GPU, model dasar, atau library Python.
3. Model utama penelitian adalah E42. Demo web historis pada source memakai CLIP-B32 dan tidak boleh dilabeli sebagai inferensi E42. Tidak ada klaim web Qwen menjadi model utama.

## Menjalankan ulang analisis
Ekstrak ZIP utuh sehingga folder `joy_revisi_ii/` tersedia. Gunakan Python3.10 atau versi yang kompatibel dengan requirements terkunci, lalu:

```sh
python -m venv .venv
# Linux/macOS: source .venv/bin/activate
# Windows: .venv\\Scripts\\activate
python -m pip install -r requirements-analysis-lock.txt
python tools/evaluate.py --package --workspace . --output analysis
python tools/validate_package.py --root .
```

Untuk Colab: unggah/ekstrak paket analisis ke `/content/joy_revisi_ii`, pasang requirements bila diperlukan, lalu buka salah satu notebook. Notebook mendeteksi folder paket tanpa path komputer pengembang. Run all menghitung ulang metrik/CI dari prediksi, tidak menjalankan training atau meminta credential. Bukti Colab hanya dianggap ada jika `qa/COLAB_VERIFICATION.json` berstatus verified.

## Isi dan batas reproduksi
- `inputs/`: dataset canonical, fold, seluruh prediksi ternormalisasi dan sumber/hash asli.
- `analysis/`: metrik per task/per kelas, CI, paired tests, peringkat, diagnosis dan grafik.
- `tools/`: evaluator, validator, source build, tes dan worker revisi.
- `source/`: source historis dan konfigurasi/audit kecil untuk keterlacakan.
- `experiment_protocols/`: source/protocol/job state dari eksperimen nyata. Status yang masih running bukan hasil final.
- `xai_e42/`: delapan contoh E42 outerfold, replay parity, rollout, LIME dan deletion.
- `documentation/`: tanggapan28butir, draf naskah, provenance, codebook dan tindak lanjut.
- `human_inputs/`: template kosong150sampul anotasi,60kasus adjudikasi dan penilaianXAI. Kosong berarti belum dilakukan.
- `coordinator_private/`: kunci kontrol untuk koordinator; jangan bagikan kepada penilai.

Paket analisis dapat dihitung ulang tanpa bobot encoder. Menjalankan ulang training/XAI memerlukan fitur/checkpoint/libraries ML yang dicantumkan di protokol dan lampiran model bila disediakan; pretrained weights publik harus diunduh dari pin resminya. Source Kaggle historis memakai path `/kaggle/input` dan bukan bagian Run all analisis CPU ini. Akses dataset/kernel privat bukan otomatis diberikan kepada penerima ZIP.

## Yang belum boleh diklaim
Anotasi ganda, riwayat1040→740 dan lima penilai XAI belum ditemukan. Skor manusia tidak diisi AI. Sel input-parity yang belum memiliki740prediksi tetap Not Evaluated. Validasi eksternal, clean Windows dan Colab yang belum dijalankan tidak dianggap lulus hanya karena pengujian Linux lokal berhasil.

Ini penyerahan privat penelitian. Hak cipta citra/bobot mengikuti pemilik/penyedia; paket bukan lisensi distribusi publik.
'''.replace('dari28','dari 28').replace('Python3','Python 3').replace('tanggapan28','tanggapan 28').replace('kosong150','kosong 150').replace(',60kasus',', 60 kasus').replace('penilaianXAI','penilaian XAI').replace('riwayat1040','riwayat 1040').replace('memiliki740prediksi','memiliki 740 prediksi'))
    rows=''.join(f'<tr><td>{html.escape(str(r.revision_id))}</td><td>{html.escape(str(r.title))}</td><td>{html.escape(str(r.status))}</td></tr>' for r in __import__('pandas').read_csv(doc/'REVISION_TRACKER_28.csv').itertuples())
    page=f'''<!doctype html><html lang="id"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Revisi II — Joy</title><style>body{{font:16px/1.6 system-ui,sans-serif;color:#172b40;background:#f3f6fa;margin:0}}main{{max-width:1050px;margin:40px auto;padding:32px;background:white;border-radius:16px}}h1{{line-height:1.2}}a{{color:#075c9b}}.state{{background:#fff4d4;border-left:4px solid #d39720;padding:18px}}nav{{display:flex;flex-wrap:wrap;gap:14px;margin:24px 0}}table{{border-collapse:collapse;width:100%;font-size:14px}}td,th{{padding:10px;text-align:left;border-bottom:1px solid #ddd}}img{{max-width:100%;height:auto}}code{{background:#eef2f6;padding:2px 5px}}</style><main><p>REVISI II · 1 NOVEMBER2026</p><h1>Notebook, bukti eksperimen<br>dan tanggapan untuk Joy</h1><p class="state"><strong>{state['completed']} butir selesai secara teknis · {state['open']} masih terbuka.</strong><br>Model utama: E42 CLIP–IndoBERT MTL. Metrik utama: Macro-F1. Bukti manusia yang belum tersedia tetap dinyatakan terbuka.</p><nav><a href="notebook_html/01_baseline.html">01 Baseline dan data</a><a href="notebook_html/02_experiments.html">02 Eksperimen dan XAI</a><a href="notebook_html/03_final_comparison.html">03 Hasil dan revisi</a><a href="README.md">Panduan reproduksi</a><a href="documentation/TINDAK_LANJUT_JOY.md">Tindakan Joy</a></nav><img src="analysis/primary_results.png" alt="Macro-F1 utama dan akurasi pendamping"><h2>Status28revisi</h2><table><thead><tr><th>Butir</th><th>Permintaan</th><th>Status</th></tr></thead><tbody>{rows}</tbody></table><p>Seluruh tabel berasal dari prediksi tersimpan atau eksperimen baru yang diverifikasi. Tidak ada training tersembunyi pada Run all. Paket ini tidak menyatakan semua revisi selesai sebelum buktinya tersedia.</p></main></html>'''
    (root/'MULAI_DI_SINI.html').write_text(page.replace('1 NOVEMBER2026','2 NOVEMBER 2026').replace('Status28revisi','Status 28 revisi'))
    # Notebooks are generated before sealing; validation inside notebook3 does
    # not attempt to verify notebook outputs that are still being authored.
    report=build_notebooks.create(root,execute=execute)
    write_json(root/'qa/LOCAL_NOTEBOOK_VERIFICATION.json',dict(status='verified' if execute else 'not_executed',notebooks=report,
               environment='local Linux Python, independent of Colab/Windows',training=False))
    return root,state


def seal(root,archive):
    root=Path(root).resolve();archive=Path(archive).resolve()
    if archive.exists():raise RuntimeError('Refuse replacing existing delivery ZIP; choose next build version')
    paths=[p for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name!='MANIFEST_SHA256.json']
    write_json(root/'MANIFEST_SHA256.json',dict(schema='joy-revisi-ii-manifest-v1',files={str(p.relative_to(root)):sha(p) for p in sorted(paths)}))
    archive.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6,strict_timestamps=False) as z:
        for p in sorted(root.rglob('*')):
            if p.is_file() and '__pycache__' not in p.parts:z.write(p,Path('joy_revisi_ii')/p.relative_to(root))
    with zipfile.ZipFile(archive) as z:assert z.testzip() is None
    archive.with_suffix('.zip.sha256').write_text(f'{sha(archive)}  {archive.name}\n')
    return archive


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--destination',required=True,type=Path);ap.add_argument('--skip-execution',action='store_true');ap.add_argument('--archive',type=Path)
    a=ap.parse_args();root,state=build(a.destination,execute=not a.skip_execution)
    if a.archive:seal(root,a.archive)
    print(json.dumps(dict(root=str(root),state=state),indent=2))
