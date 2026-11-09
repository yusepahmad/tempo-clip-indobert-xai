"""Package actual E42 checkpoints and inputs separately from analysis notebooks."""
import argparse
import json
from pathlib import Path
import shutil
import zipfile
from evaluate import sha,write_json

HERE=Path(__file__).resolve().parent;APP=HERE.parents[1];REPO=APP.parent


def build(destination):
    root=Path(destination).resolve();assert not root.exists();root.mkdir(parents=True)
    files=[]
    for folder in ['01_notebook/e42_tail_grid','04_hasil_eksperimen/e41_cached_tail/cache','04_hasil_eksperimen/e42_tail_grid','05_gambar']:
        files.extend(p for p in (APP/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts)
    for group in ['e36_clip_l14','e37_token_pool']:
        files.append(APP/f'04_hasil_eksperimen/{group}/features_manifest.json')
    files.append(APP/'03_data/DATASET_740_TASK2_DOMAIN.csv')
    for name in ['explain_e42.py','evaluate.py','replay_e42.py']:
        files.append(HERE/name)
    for p in files:
        target=root/p.relative_to(REPO);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
    (root/'README.md').write_text('''# Lampiran model penelitian E42

Lima checkpoint outerfold, cache front IndoBERT/CLIP, 740 citra dan source historis disertakan agar inferensi OOF E42 dapat direplay tanpa akses Kaggle privat. Ini bukan model refit deployment untuk sampul baru. Demo web CLIP-B32 terpisah.

## Replay CPU tanpa unduhan encoder
Gunakan environment ML yang kompatibel dengan requirements-ml-reference.txt di paket analisis (torch, transformers, numpy, pandas, scipy, scikit-learn, matplotlib), lalu dari folder ini:

```sh
python DEMO_XAI_745_FULL/01_notebook/revisi_ii/replay_e42.py --workspace . --output qa/REPLAY_E42.json
```

Replay memverifikasi seluruh hash lampiran, lima checkpoint/split dan prediksi740×3 dari cache. Tidak melatih model, mengubah checkpoint, atau memilih ulang precision berdasarkan skor. Jangan menjalankan verifier historis yang menulis ulang hasil bila hanya ingin mengaudit; gunakan replay di atas.

## Regenerasi XAI opsional
Source explain_e42.py dan 740 citra tersedia. Dibutuhkan open_clip_torch, lime, Pillow, dan model publik yang dipin dalam e36_clip_l14/e37_token_pool/features_manifest.json. Unduh IndoBERT snapshot c2cd0b51ddce6580eb35263b39b0a1e5fb0a39e2 lebih dahulu melalui huggingface_hub.snapshot_download karena source XAI memakai local_files_only=True. CLIP diunduh source dari repo/file/revision pin dan diperiksa SHA256. Bobot dasar publik berukuran besar tidak disalin ke ZIP ini. Tidak diperlukan token akun peneliti untuk repo publik.

```sh
python DEMO_XAI_745_FULL/01_notebook/revisi_ii/explain_e42.py --workspace . --samples 8
```

Regenerasi menulis direktori hasil revisi baru, bukan hasil historis. Penjelasan visual adalah attention rollout class-agnostic, bukan Grad-CAM atau bukti sebab spesifik kelas. Hasil XAI aktual yang telah dibuat ada di paket analisis. Grid training historis tidak dijalankan ulang dalam QA lampiran.

Penggunaan privat penelitian; hak cipta sampul dan lisensi bobot tetap mengikuti pemiliknya. Jangan mengunggah lampiran ini ke repositori publik tanpa izin distribusi yang sesuai.
''')
    write_json(root/'MANIFEST_SHA256.json',{'files':{str(p.relative_to(root)):sha(p) for p in sorted(root.rglob('*')) if p.is_file()}})
    archive=root.parent/'TEMPO_REVISI_II_MODEL_E42_ANNEX_B01.zip';assert not archive.exists()
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(root.rglob('*')):
            if p.is_file():z.write(p,Path('joy_model_e42')/p.relative_to(root))
    with zipfile.ZipFile(archive) as z:assert z.testzip() is None
    archive.with_suffix('.zip.sha256').write_text(f'{sha(archive)}  {archive.name}\n')
    print(json.dumps(dict(archive=str(archive),bytes=archive.stat().st_size,sha256=sha(archive)),indent=2))


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--destination',required=True,type=Path)
    build(ap.parse_args().destination)
