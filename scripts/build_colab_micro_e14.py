"""Create a credential-free Colab launcher/runtime snapshot; no GPU claims."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import sys
import zipfile

import nbformat as nbf

from colab_e14_support import sha, extract_verified, checkpoint_preflight

REPO=Path(__file__).resolve().parents[1]
APP=REPO/'DEMO_XAI_745_FULL'
OUT=REPO/'delivery/colab_micro_e14_20261020'
MODEL=APP/'06_models/micro-e14-qlora-v1'
RESEARCH=APP/'04_hasil_eksperimen/next_research_20261017'


def write(path, obj):
    path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')


def notebook(archive, digest, state):
    md=nbf.v4.new_markdown_cell
    code=nbf.v4.new_code_cell
    support=(REPO/'scripts/colab_e14_support.py').read_text()
    cells=[md(f'''# Tempo MICRO-E14 — demo Colab GPU sementara

## Objective
Menjalankan **inferensi** Qwen3-VL joint QLoRA pada GPU Colab. Training tetap di Kaggle.

Status snapshot paket: **{'CHECKPOINT VERIFIED — runtime Colab belum diuji' if state['checkpoint_verified'] else 'PREPARATION ONLY — checkpoint belum tersedia'}**.
Observasi Kaggle: `{state.get('kaggle_last_observation',{}).get('status','Not Evaluated')}`;
waktu `{state.get('kaggle_last_observation',{}).get('observed_at','Not Evaluated')}`.
Notebook ini belum dieksekusi pada GPU Colab; tidak ada output GPU palsu.

## Methodology
Adapter refit seluruh740/tiga epoch, token kelas A–J. Prompt/konteks E01 sama
dengan protokol CV. Dataset di sini **in-sample**, bukan pengujian independen.

## Changes
Backend E14 sebenarnya, bukan mengganti label CLIP–IndoBERT. Tidak ada fallback,
prediksi cached OOF, atau XAI CLIP untuk menjelaskan E14.

## Implementation
Jalankan sel secara berurutan. Pilih **Runtime → Change runtime type → GPU**
setelah checkpoint tersedia. Jangan menghabiskan kuota GPU hanya untuk paket persiapan.
Model dasar perlu internet dan unduhan beberapa GB. Memori GPU/CPU dan disk akan diperiksa.
Jangan unggah token Kaggle atau credential akun ke notebook ini.

Mode utama adalah interaksi sel notebook. Opsi web tertanam hanya untuk akun
dengan compute unit positif sesuai [FAQ Colab](https://research.google.com/colaboratory/faq.html).
Tidak membeli paket atau mengakali kuota; tidak ada tunnel publik.
'''), code(support), md('## 1. Unggah ZIP runtime pasangan notebook ini\nBukan ZIP delivery lengkap3GB. Pilih tepat satu berkas ZIP di bawah ini.'), code(f'''from pathlib import Path
import json, os, subprocess, sys, time, tempfile
from google.colab import files

EXPECTED_ZIP_SHA256 = {digest!r}
EXPECTED_ZIP_NAME = {archive.name!r}
ZIP_PATH = ''  # Isi path /content/... jika ZIP sudah diunggah; kosong = pilih file.
if not ZIP_PATH:
    uploaded = files.upload()
    if len(uploaded) != 1:
        raise RuntimeError('Pilih tepat satu ZIP runtime.')
    ZIP_PATH = next(iter(uploaded))
    del uploaded
RUNTIME = extract_verified(ZIP_PATH, EXPECTED_ZIP_SHA256, '/content')
APP = RUNTIME / 'DEMO_XAI_745_FULL'
PACKAGE_STATE = json.loads((RUNTIME/'PACKAGE_STATE.json').read_text())
print(json.dumps(PACKAGE_STATE, indent=2))
print('ZIP, CRC dan seluruh konten terverifikasi:', RUNTIME)
'''),md('## 2. Gate checkpoint\nSel berhenti di sini jika training belum selesai. Jangan lanjut ke instalasi/model.'),code('''checkpoint_preflight(RUNTIME)
print('Checkpoint VERIFIED tersedia; ini bukan hasil benchmark deployment baru.')
'''),md('## 3. Periksa GPU dan buat environment terpisah\nTidak mengganti Torch/kernel Colab yang sedang digunakan.'),code('''import shutil
gpu = subprocess.run(['nvidia-smi','--query-gpu=name,memory.total,driver_version',
                      '--format=csv,noheader'],capture_output=True,text=True,check=True)
print(gpu.stdout)
meminfo = dict(line.split(':',1) for line in Path('/proc/meminfo').read_text().splitlines())
ram_gib = int(meminfo['MemAvailable'].strip().split()[0]) / 1024**2
print('RAM CPU tersedia GiB:', round(ram_gib,2))
if ram_gib < 10:
    print('Peringatan: RAM CPU rendah untuk load8B. Gunakan high-RAM jika tersedia; jangan membeli otomatis.')
gpu_memory_mib = int(gpu.stdout.splitlines()[0].split(',')[1].strip().split()[0])
if gpu_memory_mib < 14000:
    raise RuntimeError('Gunakan GPU dengan VRAM sekitar16GB atau lebih; belum ada uji pada GPU ini.')
free_gb = shutil.disk_usage('/content').free / 1024**3
print('Disk tersedia GiB:',round(free_gb,2))
if free_gb < 30:
    raise RuntimeError('Sediakan setidaknya30GiB untuk environment dan base weights/cache.')
VENV = Path(tempfile.mkdtemp(prefix='tempo_e14_venv_',dir='/content'))
subprocess.run([sys.executable,'-m','venv',str(VENV)],check=True)
PYTHON = VENV/'bin/python'
subprocess.run([str(PYTHON),'-m','pip','install','--upgrade','pip'],check=True)
subprocess.run([str(PYTHON),'-m','pip','install','torch==2.11.0',
                '--index-url','https://download.pytorch.org/whl/cu128'],check=True)
subprocess.run([str(PYTHON),'-m','pip','install','-r',str(APP/'requirements-micro-e14.txt')],check=True)
probe = "import torch; print(torch.__version__, torch.version.cuda); assert torch.cuda.is_available(); print(torch.cuda.get_device_name(0)); print(torch.cuda.get_device_properties(0).total_memory)"
subprocess.run([str(PYTHON),'-c',probe],check=True)
'''),md('## 4. Muat GPU worker dan smoke model\nTunggu unduhan pertama. Log ada pada `gpu_runtime.log`. Stop worker sebelum mengulang sel.'),code('''if 'worker' in globals() and worker.poll() is None:
    raise RuntimeError('Worker masih hidup. Jalankan sel Stop dahulu.')
LOG = RUNTIME/'gpu_runtime.log'
worker, events, worker_log = start_native(PYTHON,APP,LOG)
try:
    ready = wait_event(worker,events,'ready',timeout=1800)
    print(json.dumps(ready['models'],indent=2))
    print('GPU E14 benar-benar ready; checksum dan smoke startup lulus.')
except Exception:
    stop_process(worker,worker_log)
    print(LOG.read_text()[-12000:])
    raise
'''),md('## 5. Pilih sampel dataset dan jalankan prediksi aktual\nTidak memakai label anotator sebagai input model. Hasil diurutkan dari skor tertinggi.'),code('''import pandas as pd
from IPython.display import display
from PIL import Image
dataset = pd.read_csv(APP/'03_data/DATASET_740_TASK2_DOMAIN.csv').fillna('')
display(dataset[['sample_id','headline_verified']].head(10))
SAMPLE_ID = str(dataset.sample_id.iloc[0])  # Ganti dengan ID pada tabel.
if SAMPLE_ID not in set(dataset.sample_id):
    raise ValueError('sample_id tidak ada pada dataset.')
worker.stdin.write(json.dumps({'action':'predict','sample_id':SAMPLE_ID})+'\\n')
worker.stdin.flush()
prediction = wait_event(worker,events,'prediction',timeout=600)['result']
rows = [{'Task':v.get('nama_task_mudah',t),'Prediksi':v['prediksi_tampil'],
         'Skor belum dikalibrasi (%)':100*v['probabilitas'],
         'Model':v['model_version']} for t,v in prediction['prediksi'].items()]
display(pd.DataFrame(rows).sort_values('Skor belum dikalibrasi (%)',ascending=False))
print(prediction['mode'])
print(prediction['xai']['limitation'])
row = dataset.set_index('sample_id').loc[SAMPLE_ID]
display(Image.open(APP/'05_gambar'/Path(row.image_path).name))
result_path=RUNTIME/'latest_prediction.json'
result_path.write_text(json.dumps(prediction,ensure_ascii=False,indent=2))
print('Output aktual tersimpan:',result_path)
'''), md('''## Benchmark Results & Visualization

Angka berikut **historis OOF740 dari log terverifikasi**, bukan output runtime
Colab atau skor checkpoint refit740. Target Macro-F1≥0,70 ketiga task belum tercapai.

| Metrik | Task1 | Task2 | Task3 |
|---|---:|---:|---:|
| MICRO-E14 Macro-F1 | 0,673321 | 0,510282 | 0,595480 |
| MICRO-E14 Micro-F1 | 0,720270 | 0,566216 | 0,667568 |
| Deployment refit740 | Not Evaluated | Not Evaluated | Not Evaluated |

Tabel prediksi sel5 berisi **skor kelas aktual**, bukan accuracy/F1. Tidak
menjadikan kecocokan label in-sample sebagai benchmark. File hasil historis asli
ada pada `historical_metrics.json` dan terikat manifest SHA.

## Analysis
Model memperbaiki hasil historis dibanding CLIP–IndoBERT, tetapi belum mencapai
target Macro-F1. Inferensi dataset refit tidak bisa membuktikan generalisasi.
Unggahan baru dan XAI E14 belum tersedia; deskripsi/alasan visual E01 hanya
tersedia untuk dataset740.

## Conclusion
Keberhasilan demo berarti model GPU terverifikasi menghasilkan prediksi, bukan
target kualitas sudah tercapai. Runtime Colab sementara; tutup sesi setelah demo.
'''),md('## 6. Stop / lepaskan proses\nJalankan setelah selesai, sebelum mengganti mode, atau bila ada timeout.'),code('''stop_process(globals().get('worker'),globals().get('worker_log'))
stop_process(globals().get('web_process'),globals().get('web_log'))
print('Proses milik notebook dihentikan. Disconnect/delete runtime lewat menu Colab bila sudah selesai.')
'''),md('''## 7. Opsional: web terbaru tertanam di notebook

Jalankan hanya bila akun memiliki **compute unit positif** dan penggunaan web
diizinkan ketentuan Colab. Gratis/tanpa saldo: tetap gunakan sel prediksi di atas.
Sel ini menghentikan worker native agar tidak memuat dua model8B sekaligus.
Tidak membuka link publik atau tunnel; iframe melalui proxy Colab resmi.
'''),code('''WEB_MODE_ALLOWED_POSITIVE_COMPUTE_BALANCE = False  # Ubah hanya setelah memeriksa akun Anda.
if not WEB_MODE_ALLOWED_POSITIVE_COMPUTE_BALANCE:
    print('Mode web tidak diaktifkan. Gunakan inferensi langsung dalam sel notebook.')
else:
    import urllib.request, urllib.error
    from google.colab import output
    stop_process(globals().get('worker'),globals().get('worker_log'))
    if 'web_process' in globals() and web_process.poll() is None:
        raise RuntimeError('Web sudah hidup; hentikan dulu sebelum mengulang.')
    web_log=(RUNTIME/'web_runtime.log').open('a')
    env=dict(os.environ,TEMPO_BACKEND='micro-e14-qlora',TEMPO_HOST='127.0.0.1',TEMPO_PORT='7861')
    web_process=subprocess.Popen([str(PYTHON),'-u',str(APP/'01_notebook/colab_micro_e14_runtime.py'),'web'],
                                 stdout=web_log,stderr=web_log,env=env)
    try:
        deadline=time.monotonic()+1800
        while True:
            if web_process.poll() is not None:
                raise RuntimeError('Server berhenti; periksa web_runtime.log')
            try:
                with urllib.request.urlopen('http://127.0.0.1:7861/api/models',timeout=3) as response:
                    model=json.load(response)
            except (urllib.error.URLError,TimeoutError):
                if time.monotonic()>deadline:raise TimeoutError('Web startup timeout')
                time.sleep(2)
                continue
            if not model.get('ready') or model.get('backend')!='micro-e14-qlora':
                raise RuntimeError('E14 belum ready: '+str(model.get('unavailable_reason')))
            break
        print('Model aktif terverifikasi:',model['version'])
        output.serve_kernel_port_as_iframe(7861,height=900,cache_in_notebook=False)
    except Exception:
        stop_process(web_process,web_log)
        print((RUNTIME/'web_runtime.log').read_text()[-12000:])
        raise
'''),md('''## Troubleshooting

- Paket PREPARATION: berhenti di gate checkpoint; gunakan paket baru setelah training Kaggle COMPLETE dan collect VERIFIED.
- CUDA tidak tersedia: pilih runtime GPU; jangan mengganti backend menjadi baseline untuk meloloskan gate.
- OOM: stop worker, disconnect/delete runtime lalu coba GPU/RAM yang mencukupi. Tidak otomatis menurunkan presisi/protokol.
- Checksum/smoke berbeda: model tidak diaktifkan; simpan log untuk investigasi.
- Iframe terblokir: gunakan mode native. Jangan menambahkan tunnel untuk melewati pembatasan.
- Runtime terputus: state/proses hilang. Unggah ZIP lagi; notebook ini tidak menyediakan hosting produksi.
- Stop worker hanya menghentikan proses demo, bukan membatalkan training Kaggle.

Referensi: [Colab FAQ](https://research.google.com/colaboratory/faq.html),
[API iframe Colab](https://github.com/googlecolab/colabtools/blob/main/google/colab/output/_util.py),
[PyTorch CUDA wheels](https://pytorch.org/get-started/locally/).
''')]
    nb=nbf.v4.new_notebook(cells=cells,metadata={'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'},
        'language_info':{'name':'python'},'colab':{'name':'TEMPO_MICRO_E14_COLAB_DEMO.ipynb','provenance':[]},'accelerator':'GPU',
        'tempo_validation':{'colab_gpu_executed':False,'snapshot_only':True,'zip_sha256':digest}})
    nbf.validate(nb)
    for i,c in enumerate(cells):
        if c.cell_type=='code':compile(c.source,f'colab-cell-{i}','exec')
    return nb


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--require-checkpoint',action='store_true')
    args=parser.parse_args()
    verified=False
    if (MODEL/'verification.json').exists():
        record=json.loads((MODEL/'verification.json').read_text())
        verified=record.get('status')=='verified' and record['result_sha256']==sha(MODEL/'result.json')
    if args.require_checkpoint and not verified:
        raise RuntimeError('Checkpoint belum verified; tidak membuat paket runtime siap model.')
    OUT.mkdir(parents=True,exist_ok=True)
    index=1
    while (OUT/f'build_{index:02}').exists():index+=1
    build=OUT/f'build_{index:02}'
    runtime=build/'tempo_colab_runtime'
    runtime.mkdir(parents=True)
    files={}
    def copy(source,relative):
        assert source.is_file() and not source.is_symlink(),source
        target=runtime/relative
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(source,target)
    for source in sorted((APP/'02_web_demo').iterdir()):
        if source.is_file() and source.suffix in ('.py','.html','.json'):
            copy(source,'DEMO_XAI_745_FULL/02_web_demo/'+source.name)
    copy(APP/'03_data/DATASET_740_TASK2_DOMAIN.csv','DEMO_XAI_745_FULL/03_data/DATASET_740_TASK2_DOMAIN.csv')
    import csv
    with (APP/'03_data/DATASET_740_TASK2_DOMAIN.csv').open(encoding='utf-8-sig') as handle:
        names={Path(row['image_path']).name for row in csv.DictReader(handle)}
    assert len(names)==740
    for name in sorted(names):copy(APP/'05_gambar'/name,'DEMO_XAI_745_FULL/05_gambar/'+name)
    for name in ('contract.json','visual_context.json','assets_manifest.json'):
        copy(MODEL/name,'DEMO_XAI_745_FULL/06_models/micro-e14-qlora-v1/'+name)
    if verified:
        result=json.loads((MODEL/'result.json').read_text())
        for name in ('result.json','input_audit.jsonl','verification.json',*result['artifacts']):
            copy(MODEL/name,'DEMO_XAI_745_FULL/06_models/micro-e14-qlora-v1/'+name)
    for name in ('requirements-micro-e14.txt','jalankan_micro_e14_linux.sh','jalankan_micro_e14_windows.bat'):
        copy(APP/name,'DEMO_XAI_745_FULL/'+name)
    copy(APP/'01_notebook/colab_micro_e14_runtime.py','DEMO_XAI_745_FULL/01_notebook/colab_micro_e14_runtime.py')
    copy(REPO/'scripts/colab_e14_support.py','tools/colab_e14_support.py')
    copy(REPO/'docs/DEPLOYMENT_MICRO_E14_2026-10-20.md','documentation/DEPLOYMENT_MICRO_E14_2026-10-20.md')
    copy(REPO/'docs/COLAB_MICRO_E14_DEMO_2026-10-20.md','README.md')
    copy(RESEARCH/'06_micro_f1/MICRO_E14_joint_qlora_oof/metrics.json','historical_metrics.json')
    state=dict(created_at=datetime.now(timezone.utc).isoformat(), checkpoint_verified=verified,
        stage='runtime_checkpoint_verified' if verified else 'preparation_only_checkpoint_pending',
        colab_gpu_execution='Not Evaluated', local_validation='static + archive checks only; see external VALIDATION_REPORT.json',
        limitations=['dataset740 in-sample','no upload feature generation','no E14 XAI','no calibrated confidence'],
        kaggle_last_observation=json.loads((RESEARCH/'07_micro_e14_deployment/job_state.json').read_text()))
    write(runtime/'PACKAGE_STATE.json',state)
    files={str(p.relative_to(runtime)):sha(p) for p in runtime.rglob('*') if p.is_file()}
    write(runtime/'MANIFEST_SHA256.json',dict(files=files))
    kind='RUNTIME' if verified else 'PREPARATION'
    archive=build/f'TEMPO_MICRO_E14_COLAB_{kind}_20261020.zip'
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6,strict_timestamps=False) as z:
        for p in sorted(runtime.rglob('*')):
            if p.is_file():z.write(p,str(p.relative_to(build)))
    digest=sha(archive)
    archive.with_suffix('.zip.sha256').write_text(digest+'  '+archive.name+'\n')
    nb=notebook(archive,digest,state)
    notebook_path=build/'TEMPO_MICRO_E14_COLAB_DEMO.ipynb'
    nbf.write(nb,notebook_path)
    # Full extraction/CRC/content hashing through the SAME bootstrap users run.
    with __import__('tempfile').TemporaryDirectory(prefix='tempo_colab_qa_') as tmp:
        extracted=extract_verified(archive,digest,tmp)
        try:checkpoint_preflight(extracted)
        except RuntimeError:
            if verified:raise
        else:
            assert verified
    report=dict(status='verified', archive=str(archive.relative_to(REPO)), zip_sha256=digest,
        bytes=archive.stat().st_size, files=len(files)+1, notebook=str(notebook_path.relative_to(REPO)),
        cells=len(nb.cells), checkpoint_verified=verified, colab_gpu_execution='Not Evaluated',
        checks=['nbformat schema','all code cells compile','CRC and all content hashes','safe extraction','checkpoint availability gate'],
        excluded=['credentials','environment/venv','job/upload caches','baseline feature/model data','large research history','base HF weights'])
    write(build/'VALIDATION_REPORT.json',report)
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
