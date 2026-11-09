"""Create a credential-free Colab launcher for the immutable public R4 ZIP."""
import argparse
from pathlib import Path
import nbformat as nbf

URL = 'https://github.com/project-owner/tempo-clip-indobert-xai/releases/download/v2026.11.08-r4/TEMPO_REVISI_II_R4_PUBLIC_20261108.zip'
SHA256 = 'a2c9a67f7ee02472f76a0581b364dfc96b6c7bd6584cb71a3cac5a090a8d2035'


def build(destination):
    cells = [nbf.v4.new_markdown_cell(
        '# R32 — Run all dari Release R4 publik\n\n'
        'Pilih runtime CPU lalu **Runtime → Run all**. Arsip ekspor diunduh otomatis '
        'dan diperiksa checksum. Jika repository private, unduh ZIP R4 lewat akun GitHub '
        'yang memiliki akses lalu unggah saat diminta. Tidak membutuhkan token di notebook, Drive atau GPU. '
        'Ini pengujian analisis tiga notebook dari prediksi tersimpan, bukan training ulang. '
        'Simpan ZIP keluaran dan screenshot sel hasil untuk bukti. '
        'Notebook yang belum dijalankan tidak membuktikan kelulusan Colab.'),
        nbf.v4.new_code_cell(
            'import hashlib, json, os, subprocess, sys, tempfile, urllib.error, urllib.request, zipfile\n'
            'from pathlib import Path\n'
            'import google.colab\n'
            'from google.colab import files\n'
            "assert os.environ.get('COLAB_RELEASE_TAG') or Path('/opt/google/colab').exists(), 'Gunakan runtime Colab asli'\n"
            "directory = Path(tempfile.mkdtemp(prefix='tempo_public_r32_'))\n"
            "archive = directory/'R4.zip'\n"
            'try:\n'
            f'    urllib.request.urlretrieve({URL!r}, archive)\n'
            'except urllib.error.HTTPError as error:\n'
            '    if error.code not in (401, 403, 404):\n'
            '        raise\n'
            "    print('Repository mungkin private. Unduh ZIP Release R4 dari akun GitHub berizin, lalu pilih ZIP tersebut:')\n"
            '    uploaded = files.upload()\n'
            "    candidates = [name for name in uploaded if name.endswith('.zip')]\n"
            "    assert len(candidates) == 1, 'Pilih tepat satu ZIP R4'\n"
            '    archive.write_bytes(uploaded[candidates[0]])\n'
            '    del uploaded\n'
            'digest = hashlib.sha256()\n'
            "with archive.open('rb') as stream:\n"
            '    for chunk in iter(lambda: stream.read(4*1024*1024), b\'\'):\n'
            '        digest.update(chunk)\n'
            f"assert digest.hexdigest() == {SHA256!r}, 'Checksum arsip berbeda'\n"
            'with zipfile.ZipFile(archive) as bundle:\n'
            '    for name in bundle.namelist():\n'
            "        assert (directory/name).resolve().is_relative_to(directory), 'Path ZIP tidak aman'\n"
            '    bundle.extractall(directory)\n'
            "ROOT = directory/'joy_revisi_ii'\n"
            "subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', '-r', str(ROOT/'requirements-analysis-lock.txt')], check=True)"),
        nbf.v4.new_code_cell(
            "output = directory/'hasil_colab'\n"
            "subprocess.run([sys.executable, str(ROOT/'tools/run_clean_notebooks.py'), '--root', str(ROOT), '--output', str(output)], check=True)\n"
            "result = json.loads((output/'RUNTIME_VERIFICATION.json').read_text())\n"
            "assert result['status'] == 'verified' and result['colab_verified'] is True\n"
            "assert len(result['notebooks']) == 3 and all(r['errors'] == 0 for r in result['notebooks'])\n"
            "print('R32 — Run all Colab LULUS; ambil screenshot sel ini')\n"
            "print(json.dumps(result, indent=2))"),
        nbf.v4.new_code_cell(
            'import shutil\n'
            "evidence = shutil.make_archive(str(directory/'R32_BUKTI_COLAB'), 'zip', output)\n"
            'files.download(evidence)')]
    notebook = nbf.v4.new_notebook(cells=cells, metadata={
        'kernelspec':{'display_name':'Python 3', 'language':'python', 'name':'python3'},
        'colab':{'name':'COLAB_PUBLIC_R4.ipynb', 'provenance':[]}})
    for cell in notebook.cells:
        if cell.cell_type == 'code':
            compile(cell.source, 'COLAB_PUBLIC_R4', 'exec')
    nbf.validate(notebook)
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    nbf.write(notebook, destination)
    return destination


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--destination', type=Path, required=True)
    print(build(parser.parse_args().destination))
