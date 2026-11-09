"""Portable analysis ZIP and a Colab launcher; never claim Colab was run locally."""
import json
from pathlib import Path
import shutil
import nbformat as nbf
from build_full_delivery import seal
from evaluate import sha

HERE=Path(__file__).resolve().parent


def build(source,destination):
    source=Path(source).resolve();destination=Path(destination).resolve();destination.mkdir(parents=True,exist_ok=True)
    root=destination/'R32_ANALISIS_PORTABEL';assert not root.exists()
    def ignore(folder,names):
        excluded={'__pycache__'}
        if Path(folder)==source:excluded|={'lampiran_model','coordinator_private','paket_untuk_manusia'}
        return set(names)&excluded
    shutil.copytree(source,root,ignore=ignore)
    shutil.copy2(HERE/'run_clean_notebooks.py',root/'tools/run_clean_notebooks.py')
    note='# R32 — paket analisis portabel\n\nTurunan paket revisi sumber untuk Run all analisis pada CPU. Semua notebook, prediksi, split, evaluator, bukti dan output tetap disertakan. Lampiran checkpoint/cache training, kunci privat koordinator dan ZIP pembagian penilai tidak disertakan karena tidak diperlukan untuk Run all analisis. Ini bukan paket untuk melatih ulang model.\n\nJalankan `python tools/run_clean_notebooks.py --root . --output /lokasi/hasil-baru`. Folder output harus belum ada. Untuk Colab, buka COLAB_RUN_ALL.ipynb pada paket tindak lanjut dan unggah ZIP analisis saat diminta; tidak memerlukan Drive atau GPU.\n\nBukti Colab belum ada sampai notebook benar-benar dijalankan pada Colab dan laporan RUNTIME_VERIFICATION.json mencatat colab_verified=true. Ambil screenshot sel ringkasan hasil pada Colab. Kelulusan lokal dicatat terpisah.\n'
    (root/'R32_ANALYSIS_ONLY.md').write_text(note)
    p=root/'README.md';p.write_text(note+'\n---\n\n'+p.read_text())
    archive=destination/'R32_ANALISIS_PORTABEL.zip';seal(root,archive);expected=sha(archive)
    md=nbf.v4.new_markdown_cell;code=nbf.v4.new_code_cell
    cells=[md('# Uji R32 — Run all tiga notebook pada Colab bersih\n\nPilih **Runtime → Run all**. Unggah `R32_ANALISIS_PORTABEL.zip` saat diminta. Runtime CPU cukup; tidak memakai Drive. File keluaran berisi notebook yang benar-benar dieksekusi dan laporan runtime. Setelah selesai, ambil screenshot tabel ringkasan untuk bukti pembimbing. Jangan menyatakan lulus sebelum seluruh sel selesai.'),
        code("import sys, os, json, hashlib, zipfile, subprocess, tempfile\nfrom pathlib import Path\nimport google.colab\nfrom google.colab import files\nassert os.environ.get('COLAB_RELEASE_TAG') or Path('/opt/google/colab').exists(), 'Jalankan pada runtime Google Colab asli'\nuploaded = files.upload()\narchive = next((Path(name) for name in uploaded if name.endswith('.zip')), None)\nassert archive is not None, 'Unggah ZIP analisis portabel'\ndel uploaded\nassert hashlib.sha256(archive.read_bytes()).hexdigest() == "+repr(expected)+", 'SHA256 ZIP tidak cocok'"),
        code("directory = Path(tempfile.mkdtemp(prefix='joy_r32_'))\nwith zipfile.ZipFile(archive) as z:\n    assert z.testzip() is None\n    for name in z.namelist():\n        assert (directory/name).resolve().is_relative_to(directory), 'Path ZIP tidak aman'\n    z.extractall(directory)\nROOT = directory/'joy_revisi_ii'\nsubprocess.run([sys.executable, '-m', 'pip', 'install', '-q', '-r', str(ROOT/'requirements-analysis-lock.txt')], check=True)\nprint('Paket diekstrak dan dependensi dipasang. Tidak ada training.')"),
        code("output = Path('/content/JOY_R32_HASIL_COLAB')\nassert not output.exists(), 'Gunakan runtime Colab baru atau simpan hasil sebelumnya lebih dahulu'\nsubprocess.run([sys.executable, str(ROOT/'tools/run_clean_notebooks.py'), '--root', str(ROOT), '--output', str(output)], check=True)\nresult = json.loads((output/'RUNTIME_VERIFICATION.json').read_text())\nassert result['status'] == 'verified' and result['colab_verified'] is True\nfrom IPython.display import display, HTML\nrows = ''.join('<tr><td>'+r['notebook']+'</td><td>'+str(r['errors'])+'</td><td>'+str(r['seconds'])+'</td></tr>' for r in result['notebooks'])\ndisplay(HTML('<h2>R32 — Run all Colab lulus</h2><p>'+result['created_at']+'</p><table><tr><th>Notebook</th><th>Error</th><th>Detik</th></tr>'+rows+'</table><p>Ambil screenshot sel ini dan simpan ZIP bukti berikut.</p>'))"),
        code("import shutil\narchive_result = shutil.make_archive('/content/JOY_R32_BUKTI_COLAB', 'zip', output)\nfiles.download(archive_result)")]
    nb=nbf.v4.new_notebook(cells=cells,metadata={'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'},'colab':{'name':'COLAB_RUN_ALL.ipynb','provenance':[]}})
    for c in nb.cells:
        if c.cell_type=='code':compile(c.source,'COLAB_RUN_ALL','exec')
    nbf.validate(nb);nbf.write(nb,destination/'COLAB_RUN_ALL.ipynb')
    (destination/'PANDUAN_R32.md').write_text(note)
    return dict(status='prepared_not_colab_executed',archive=archive.name,bytes=archive.stat().st_size,sha256=expected,
                excluded_optional=['lampiran_model','coordinator_private','paket_untuk_manusia'],colab_verified=False)
