"""Publish an honest snapshot of pending work and ready-to-use materials."""
import csv
import html
from datetime import datetime,timedelta,timezone
import json
from pathlib import Path
import shutil
import zipfile
from zoneinfo import ZoneInfo

import pandas as pd
from evaluate import TASKS,sha,write_json

HERE=Path(__file__).resolve().parent;REPO=HERE.parents[2]


def finish():
    source=REPO/'delivery/HASIL_REVISI_JOY_20261102_R3_FULL'
    root=REPO/'delivery/TINDAK_LANJUT_REVISI_20261102';root.mkdir(exist_ok=True)
    job=REPO/'DEMO_XAI_745_FULL/04_hasil_eksperimen/revisi_ii/qwen_basic_jobs/full'
    for name in ['status.json','submission.json','preflight_20261102.json','protocol.json','WATCH_STATE.json']:
        shutil.copy2(job/name,root/'R21'/name)
    live=json.loads((job/'status.json').read_text());preflight=json.loads((job/'preflight_20261102.json').read_text())
    start=datetime.fromisoformat(preflight['observed_at']).astimezone(ZoneInfo('Asia/Jakarta'))
    low=(start+timedelta(hours=5)).strftime('%H.%M');high=(start+timedelta(hours=9)).strftime('%H.%M')
    human=root/'PAKET_MANUSIA';human.mkdir(exist_ok=True)
    for path in (source/'paket_untuk_manusia').iterdir():
        if path.is_file():shutil.copy2(path,human/path.name)
    checked=[]
    for path in sorted(human.glob('*.zip')):
        assert sha(path)==path.with_suffix('.zip.sha256').read_text().split()[0]
        with zipfile.ZipFile(path) as z:
            assert z.testzip() is None
            assert not any('PRIVATE' in name or 'COORDINATOR_KEY' in name for name in z.namelist())
            if path.stem.startswith('ANOTATOR_'):
                name=next(n for n in z.namelist() if n.endswith('/annotator_'+path.stem[-1]+'.csv'))
                frame=pd.read_csv(z.open(name),keep_default_na=False);assert len(frame)==150 and frame[list(TASKS)].eq('').all().all()
            if path.stem.startswith('PENILAI_'):
                name=next(n for n in z.namelist() if n.endswith('/ratings.csv'))
                frame=pd.read_csv(z.open(name),keep_default_na=False);assert len(frame)==48 and frame.score.eq('').all()
            if path.stem=='ADJUDIKASI_60':
                name=next(n for n in z.namelist() if n.endswith('/catchall_review_60.csv'))
                frame=pd.read_csv(z.open(name),keep_default_na=False);assert len(frame)==60 and frame.proposed_label.eq('').all()
        checked.append(dict(archive=path.name,sha256=sha(path),human_answers_blank=True))
    assert len(checked)==8
    write_json(root/'HUMAN_PACKET_VERIFICATION.json',dict(status='verified',archives=checked,answers_fabricated=False))
    with (human/'REGISTRASI_PARTISIPAN.csv').open('w',newline='') as stream:
        writer=csv.writer(stream);writer.writerow(['role','participant_code','consent_date','real_human_confirmed','independent_confirmed','not_annotation_team_for_xai','coordinator_note'])
        for role,identifier in [('annotator','A'),('annotator','B')]+[('xai_rater','R'+str(i)) for i in range(1,6)]:writer.writerow([role,identifier,'','','','',''])
    metrics=pd.read_csv(source/'analysis/metrics.csv');comparison=[]
    for task in TASKS:
        a=metrics[metrics.experiment.eq('e42_tail_grid')&metrics.task.eq(task)].iloc[0]
        b=metrics[metrics.experiment.eq('MICRO_E14_joint_qlora_oof')&metrics.task.eq(task)].iloc[0]
        comparison.append(dict(task=task,human_cohen_kappa='',human_samples='',main_e42_kappa=a.kappa,comparator_e14_kappa=b.kappa,human_status='Not Evaluated'))
    pd.DataFrame(comparison).to_csv(root/'R23_KAPPA_MANUSIA_VS_MODEL_TEMPLATE.csv',index=False)
    shutil.copy2(source/'documentation/CORPUS_HISTORY.md',root/'R23_R6_RIWAYAT_YANG_TERSEDIA.md')
    readme='''# Tindak lanjut revisi — 2 November 2026

**Belum semua dapat ditutup hari ini.** Ada sembilan nomor terbuka, setara tujuh kelompok pekerjaan karena R23/R6 dan R34/R9 saling terkait. Pengguna mengonfirmasi belum memiliki dokumen Agustus, dua hasil anotator, atau lima hasil penilai. Status utama tetap 19/28 selesai teknis; bahan tambahan ini tidak mengubahnya secara otomatis.

| Butir | Yang sudah saya kerjakan sekarang | Yang masih diperlukan | Estimasi dari kondisi sekarang |
|---|---|---|---|
| R21 | Smoke lulus; full lima fold privat sudah dikirim dan RUNNING; tabel 2×2 + zero-shot dan CI kappa tersedia; collector otomatis aktif | Job selesai, verifikasi 740 prediksi dan tinjauan batas kesetaraan input | 5–9 jam sejak mulai, tanpa jaminan; collector/tabel beberapa menit setelah COMPLETE |
| R22 | 740 input tanpa kolom label, 742 file berhash, generator asli lengkap dan wrapper pembatas baca; uji menolak CSV berlabel | Bukti isolasi/timestamp runtime historis yang memang tidak direkam tidak dapat dibuat sekarang | Materi teknis tambahan selesai; regenerasi baru diperkirakan 2,5–4 jam dari log lama, lalu rerun model yang memakai fitur baru terpisah. Tidak dijalankan otomatis karena tidak akan membuktikan runtime lama |
| R23 + R6 | Paket A/B masing-masing 150 sampul, codebook, kalkulator kappa teruji, tabel pembanding kappa dan klarifikasi riwayat korpus | Dua anotator independen; catatan korpus awal/300 eksklusi per ID bila ada | Perkiraan 5–10 jam per anotator (dapat paralel), lalu 30–60 menit perhitungan/laporan setelah file lengkap; dokumentasi korpus bergantung pemilik data |
| R31 | Tabel sensitivitas/dekomposisi sudah ada; paket audit 30 LAINNYA + 30 multiple_or_other siap | Pemeriksaan dan alasan/adjudikasi manusia | Perkiraan 3–6 jam manusia, lalu 30–60 menit rekap; perubahan kelas dapat menuntut eksperimen lanjutan |
| R32 | ZIP analisis portabel; peluncur Colab; Run all dari ekstraksi pada venv baru lulus tiga notebook | Jalankan COLAB_RUN_ALL.ipynb pada Colab asli dan ambil screenshot sel ringkasan. Browser tidak terhubung pada sesi ini | Sekitar 20–40 menit setelah ada akses, termasuk upload/pip; bergantung koneksi/runtime |
| R34 + R9 | XAI aktual, kontrol buta, rubrik dan lima ZIP penilai siap; kalkulator ICC teruji | Lima penilai independen yang tidak ikut anotasi; skor dan dokumentasi partisipasi nyata | Perkiraan 1–2 jam per penilai, dapat paralel setelah orang tersedia; 30–60 menit rekap. Waktu rekrutmen belum diketahui |
| R8 | Bukti baseline/ablasi sudah tersedia di R3 FULL | Dokumen revisi Agustus asli untuk mencocokkan setiap tuntutan | Sekitar 15–30 menit pencocokan setelah dokumen diterima; waktu mendapat dokumen belum diketahui |

## Yang dapat kamu pakai sekarang

1. **R21/R21_TABEL_2X2.md** dan CSV: angka aktual; tiga sel QLoRA basic per task masih kosong sampai hasil full lulus. Basic saat ini citra + headline + supporting; CLIP rich 256 vs basic 128 token tidak disebut efek fitur murni.
2. **COLAB_RUN_ALL.ipynb** dan **R32_ANALISIS_PORTABEL.zip**: buka launcher pada Colab CPU baru, Run all, unggah ZIP saat diminta, simpan ZIP bukti runtime dan screenshot hasil. Tanpa Drive/GPU. Uji Linux baru ada pada R32_CLEAN_ENV_VERIFICATION.json dan tidak diberi label Colab.
3. **PAKET_MANUSIA/**: bagikan hanya ANOTATOR_A/B masing-masing ke dua orang berbeda; PENILAI_XAI_R1–R5 masing-masing ke lima orang di luar tim anotasi; ADJUDIKASI_60 ke pemeriksa kelas. Jangan memberi penilai paket analisis/kunci kontrol. Koordinator mencatat persetujuan dan independensi secara privat.
4. **R22_INPUT_TANPA_LABEL/** dan **tools/label_blind_bundle.py**: bahan input untuk pembangkitan versi baru. Generator lama disalin utuh; timestamp manifest adalah waktu ekspor baru, bukan timestamp E01 asli. Guard Python bukan sandbox OS. Tidak ada fitur/model lama diganti.

## Pengolahan setelah hasil manusia masuk

Letakkan jawaban asli dalam folder terpisah. Dari folder paket tambahan ini, gunakan:

```sh
python tools/human_agreement.py annotation --a /path/annotator_A.csv --b /path/annotator_B.csv --protocol /path/protocol.json --output /path/agreement.json
python tools/human_agreement.py xai --ratings /path/lima_penilai_digabung.csv --expected-template PAKET_MANUSIA/ratings_template.csv --output /path/xai_agreement.json
```

Gunakan protocol.json dari paket anotator. Gabungkan lima ratings.csv dengan rater_id tetap. Semua item/dimensi harus terisi untuk seluruh penilai. Identitas manusia/independensi tidak dapat dibuktikan hanya dari nilai CSV; koordinator harus mendokumentasikannya. File kosong ditolak dan tidak diganti nol. Template kappa manusia tidak berisi angka buatan.

## Job yang sedang berjalan

Kernel: https://www.kaggle.com/code/research-account/tempo-revisi-ii-qwen-basic-full

Pemantau berjalan pada workspace asli, mengecek berkala dan tidak melakukan submission ulang. Jika selesai dan terverifikasi, hasil serta tabel dibuat di `delivery/R21_HASIL_FULL_20261102/`. Jika ERROR atau validasi gagal, hasil tidak dipromosikan. Snapshot job dalam paket ini tidak berubah otomatis; status live ada di workspace `DEMO_XAI_745_FULL/04_hasil_eksperimen/revisi_ii/qwen_basic_jobs/full/`.

## Batas pekerjaan

Saya dapat menjalankan eksperimen, memeriksa file, menghitung statistik, membuat tabel/naskah dan memvalidasi paket. Anotasi/penilaian manusia harus dikerjakan manusia; dokumen asli dan timestamp historis yang tidak tersedia tidak dapat saya ciptakan. Menutup seluruh sembilan butir hari ini belum realistis dari kondisi bukti saat ini.
'''
    readme+=f'\nSnapshot status: **{live["status"]}**, diamati {live["observed_at"]}. Awal preflight {start.strftime("%H.%M WIB")}; rentang perkiraan selesai {low}–{high} WIB pada 2 November bila berjalan normal, ditambah antrean/overhead yang belum tercakup. Ini estimasi, bukan janji.\n'
    (root/'MULAI_DI_SINI.md').write_text(readme)
    from nbconvert.filters.markdown import markdown2html
    links=[('R21/R21_TABEL_2X2.md','Tabel R21'),('R21/R21_MATRIX_DAN_ZERO_SHOT.csv','CSV R21'),
           ('COLAB_RUN_ALL.ipynb','Peluncur Colab'),('R32_ANALISIS_PORTABEL.zip','ZIP analisis portabel'),
           ('R32_CLEAN_ENV_VERIFICATION.json','Bukti uji Linux bersih'),('R22_AUDIT_INPUT.json','Audit input R22')]
    links.extend(('PAKET_MANUSIA/'+p.name,p.stem) for p in sorted(human.glob('*.zip')))
    menu=''.join(f'<a href="{html.escape(path)}">{html.escape(label)}</a> ' for path,label in links)
    page='<!doctype html><html lang="id"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Tindak lanjut revisi Joy</title><style>body{font:16px/1.6 system-ui;max-width:1200px;margin:32px auto;padding:20px;color:#172b40}nav{display:flex;flex-wrap:wrap;gap:14px;padding:20px;background:#eef3f8}table{border-collapse:collapse;width:100%;font-size:14px}th,td{padding:10px;border:1px solid #ddd;text-align:left;vertical-align:top}pre{overflow:auto;background:#f2f5f8;padding:15px}a{color:#075c9b}</style><nav>'+menu+'</nav><main>'+str(markdown2html(readme))+'</main></html>'
    (root/'MULAI_DI_SINI.html').write_text(page)
    tracker=pd.read_csv(source/'documentation/REVISION_TRACKER_28.csv').fillna('')
    tracker[tracker.status.ne('Selesai')].to_csv(root/'SEMBILAN_BUTIR_TERBUKA.csv',index=False)
    tools=root/'tools';tools.mkdir(exist_ok=True)
    for name in ['label_blind_bundle.py','human_agreement.py','evaluate.py','run_clean_notebooks.py','notebook_evidence.py','validate_package.py']:
        shutil.copy2(HERE/name,tools/name)
    shutil.copy2(source/'human_inputs/xai/ratings_template.csv',human/'ratings_template.csv')
    reference=root/'source_reference';reference.mkdir(exist_ok=True)
    for name in ['manage_qwen_basic.py','watch_qwen_basic.py','followup_r21.py','build_colab_followup.py','finish_open_followup.py','test_open_followup.py']:
        shutil.copy2(HERE/name,reference/name)
    write_json(root/'FOLLOWUP_STATE.json',dict(created_at=datetime.now(timezone.utc).isoformat(),completed_revisions=19,open_revisions=9,
              qwen_full_status=live['status'],qwen_full_source_sha256=preflight['source_sha256'],gpu_quota_preflight=preflight['quota'],
              human_results_available=False,colab_verified=False,linux_clean_run_all=True,original_r3_unchanged=True))
    return root


if __name__=='__main__':print(finish())
