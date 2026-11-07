"""Prepare separate, blinded human packets; never fill human judgments."""
import argparse
import html
import json
from pathlib import Path
import shutil
import zipfile
import pandas as pd
from evaluate import TASKS, sha, write_json

HERE = Path(__file__).resolve().parent
APP = HERE.parents[1]
REPO = APP.parent


def copy(source, target):
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)


def seal(root, output):
    assert not output.exists(), 'Use a new packet build; never replace delivered ZIPs'
    write_json(root/'MANIFEST_SHA256.json', {'files': {
        str(p.relative_to(root)): sha(p) for p in sorted(root.rglob('*')) if p.is_file()}})
    with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as z:
        for p in sorted(root.rglob('*')):
            if p.is_file(): z.write(p, Path(root.name)/p.relative_to(root))
    with zipfile.ZipFile(output) as z: assert z.testzip() is None
    output.with_suffix('.zip.sha256').write_text(f'{sha(output)}  {output.name}\n')
    return {'file': str(output), 'sha256': sha(output), 'bytes': output.stat().st_size}


def page(title, body):
    return ('<!doctype html><html lang="id"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            '<style>body{font:16px/1.6 system-ui;max-width:1050px;margin:30px auto;padding:20px;color:#183247}article{border-top:1px solid #ccc;padding:20px 0}img{max-width:45%;max-height:650px;object-fit:contain}code{background:#eef2f6}table{border-collapse:collapse}td,th{padding:8px;border:1px solid #ddd}</style>'
            f'<title>{html.escape(title)}</title><h1>{html.escape(title)}</h1>'+body+'</html>')


def codebook():
    definitions=json.loads((REPO/'docs/revisi-ii/TASK_DEFINITIONS.json').read_text())['definitions']
    out=['# Codebook untuk anotasi independen\n\nPilih satu label per task. Tulis alasan/keyakinan jika ambigu. Jangan berdiskusi sampai kedua file dikunci. Kappa dihitung sebelum adjudikasi. Label bukan penilaian hukum atau kebenaran objektif.\n']
    for task, values in definitions.items():
        out.append('\n## '+task+'\n\n| Kode | Definisi |\n|---|---|\n')
        out.extend(f'| {label} | {meaning} |\n' for label,meaning in values.items())
    out.append('\nNON_METAFORA berarti tidak ada pemetaan sumber–sasaran, bukan ragu. LAINNYA memerlukan pemetaan metaforis di luar lima domain positif. multiple_or_other: tulis apakah beberapa sasaran dominan atau tipe tidak tercakup. government menunjuk institusi eksekutif; individual menunjuk orang tertentu sebagai fokus kritik. Jangan menghapus kasus sengketa; adjudikator mencatat keputusan dalam file baru.\n')
    return ''.join(out)


def build(destination):
    dest=Path(destination).resolve()
    assert not dest.exists(), 'Choose new human packet build directory'
    dest.mkdir(parents=True)
    human=REPO/'docs/revisi-ii/human_inputs'
    records=[]
    for annotator in ['A','B']:
        packet=dest/f'ANOTATOR_{annotator}'
        packet.mkdir()
        frame=pd.read_csv(human/f'annotation/annotator_{annotator}.csv',keep_default_na=False)
        assert len(frame)==150 and frame[list(TASKS)].eq('').all().all()
        copy(human/f'annotation/annotator_{annotator}.csv',packet/f'annotator_{annotator}.csv')
        copy(human/'annotation/protocol.json',packet/'protocol.json')
        (packet/'CODEBOOK.md').write_text(codebook())
        body=f'<p>Isi <code>annotator_{annotator}.csv</code> setelah membaca <a href="CODEBOOK.md">codebook</a>. Tiga kolom task, keyakinan dan komentar masih kosong. Penilaian harus independen.</p>'
        for row in frame.itertuples():
            source=human/'annotation'/row.image_path
            assert source.is_file()
            copy(source,packet/row.image_path)
            body+=f'<article><h2>{row.sample_id}</h2><img src="{row.image_path}" alt="Sampul"><p>{html.escape(row.headline_verified)}</p><p>{html.escape(row.supporting_text_verified)}</p></article>'
        (packet/'MULAI_DI_SINI.html').write_text(page(f'Anotasi independen — {annotator}',body))
        assert not any('PRIVATE' in p.name for p in packet.rglob('*'))
        records.append(seal(packet,dest/f'ANOTATOR_{annotator}.zip'))

    data=pd.read_csv(APP/'03_data/DATASET_740_TASK2_DOMAIN.csv').fillna('').set_index('sample_id')
    key=pd.read_csv(REPO/'docs/revisi-ii/XAI_COORDINATOR_KEY_PRIVATE.csv')
    ratings=pd.read_csv(human/'xai/ratings_template.csv',keep_default_na=False)
    assert len(key)==16 and ratings.score.eq('').all()
    for rater in range(1,6):
        packet=dest/f'PENILAI_XAI_R{rater}';packet.mkdir()
        subset=ratings[ratings.rater_id==f'R{rater}']
        assert len(subset)==48
        subset.to_csv(packet/'ratings.csv',index=False)
        copy(human/'XAI_RUBRIC.md',packet/'RUBRIK.md')
        body='<p>Nilai sendiri tanpa mendiskusikan skor. Isi <code>ratings.csv</code> dengan bilangan 1–5 menurut <a href="RUBRIK.md">rubrik</a>. Ada 16 item dan tiga dimensi per item. Jangan menebak atau mencari identitas metode/kontrol. Simpan file asli setelah selesai.</p><p>Peta bersifat visual umum, bukan bukti sebab untuk kelas tertentu. Nilai keterbacaan, relevansi dan bantuan memahami representasi; jangan menganggap area terang membuktikan model benar. Warna lebih terang menandai bobot peta lebih tinggi.</p>'
        for row in key.itertuples():
            copy(human/f'xai/{row.item_id}.png',packet/f'images/{row.item_id}.png')
            copy(APP/f'05_gambar/{row.sample_id}.jpg',packet/f'images/{row.item_id}_original.jpg')
            sample=data.loc[row.sample_id]
            body+=f'<article><h2>{row.item_id}</h2><img src="images/{row.item_id}_original.jpg" alt="Citra asli"><img src="images/{row.item_id}.png" alt="Peta yang dinilai"><p>{html.escape(sample.headline_verified)}</p><p>{html.escape(sample.supporting_text_verified)}</p></article>'
        (packet/'MULAI_DI_SINI.html').write_text(page(f'Penilaian XAI — R{rater}',body))
        # Never copy original sample IDs, predictions or the control key.
        forbidden={'source','kind','sample_id'}
        assert not forbidden.intersection(subset.columns)
        records.append(seal(packet,dest/f'PENILAI_XAI_R{rater}.zip'))

    packet=dest/'ADJUDIKASI_60';packet.mkdir()
    audit=pd.read_csv(human/'catchall_review_60.csv',keep_default_na=False)
    assert len(audit)==60 and audit.proposed_label.eq('').all()
    audit['image_path']=['images/'+Path(p).name for p in audit.image_path]
    audit.to_csv(packet/'catchall_review_60.csv',index=False)
    (packet/'CODEBOOK.md').write_text(codebook())
    body='<p>Audit manusia 30 LAINNYA + 30 multiple_or_other. Label saat ini adalah bahan audit dan boleh dilihat adjudikator; paket ini tidak digunakan untuk menghitung agreement buta. Isi subgroup, usulan dan alasan. Jangan mengubah gold sumber.</p>'
    for row in audit.itertuples():
        copy(APP/'05_gambar'/Path(row.image_path).name,packet/row.image_path)
        sample=data.loc[row.sample_id]
        body+=f'<article><h2>{row.sample_id} — {row.task}: {row.current_label}</h2><img src="{row.image_path}" alt="Sampul"><p>{html.escape(sample.headline_verified)}</p><p>{html.escape(sample.supporting_text_verified)}</p></article>'
    (packet/'MULAI_DI_SINI.html').write_text(page('Audit kelas penampung — 60 kasus',body))
    records.append(seal(packet,dest/'ADJUDIKASI_60.zip'))
    write_json(dest/'PACKET_VERIFICATION.json',dict(status='verified_blank_human_packets',annotation_samples=150,adjudication_rows=60,xai_items=16,xai_raters=5,ratings_per_rater=48,private_key_excluded=True,archives=records))
    (dest/'PANDUAN_KOORDINATOR.md').write_text('# Pembagian paket manusia\n\nKirim ANOTATOR_A.zip dan ANOTATOR_B.zip kepada dua orang berbeda, masing-masing hanya paketnya. Kirim PENILAI_XAI_R1.zip sampai R5 kepada lima penilai independen yang tidak ikut anotasi. Jangan sertakan paket analisis, kunci privat, atau file hasil model kepada anotator/penilai. ADJUDIKASI_60.zip untuk adjudikator, bukan input agreement buta.\n\nMinta persetujuan partisipasi dan catat identitas berkode, tanggal, keahlian, independensi dan versi file secara privat. Tidak ada skor manusia di paket ini. Gabungkan lima ratings.csv tanpa mengubah rater_id setelah diterima; gunakan tools/human_agreement.py pada paket analisis. Jangan mengganti skor kosong dengan nol.\n')
    print(json.dumps({'status':'verified','archives':len(records),'root':str(dest)},indent=2))


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--destination',type=Path,required=True)
    build(ap.parse_args().destination)
