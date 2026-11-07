"""Finalize review artifacts only after full740 audit passed; run from repo root."""
import json, shutil, time, zipfile
from pathlib import Path
root=Path(__file__).resolve().parents[2]
package=root/'DEMO_XAI_745_FULL'
audit=package/'04_hasil_eksperimen/revisi_week3/scale740_verification.json'
while not audit.exists(): time.sleep(30)
result=json.loads(audit.read_text(encoding='utf-8'))
assert result['status']=='passed' and result['samples']==740
p=root/'docs/DELIVERY_WEEK_3.md'
s=p.read_text(encoding='utf-8').replace('Batch penuh 740 sedang diverifikasi; hasil akhir dicatat pada `scale740_verification.json` setelah selesai.','Batch penuh 740 lulus: 740 berhasil, nol gagal, 740 pemeriksaan HTTP heatmap, 3.700 aset dan CSV 741 baris termasuk header. Bukti: `scale740_verification.json`.')
s+='\nVerifikasi skala: seluruh snapshot/input/task/kelas/evidence dan probabilitas valid; ekspor JSON berisi 740 item. Ini uji alur in-sample, bukan evaluasi akurasi. Job asli dan aset berada di `_jobs/` lokal dan dikecualikan dari ZIP; URL ekspor bukan aset portabel paket.\n'
p.write_text(s,encoding='utf-8')
p=root/'docs/plan-revisi-demo-xai-tempo.md';s=p.read_text(encoding='utf-8').replace('Batch 740 berjalan untuk penutupan skala, bukan benchmark akurasi.','Batch 740 lulus untuk penutupan skala, bukan benchmark akurasi.');p.write_text(s,encoding='utf-8')
p=root/'docs/plans/2026-10-05-penutupan-teknis-week3.md';s=p.read_text(encoding='utf-8').replace('**Status:** in-progress','**Status:** done');s+='\n## Hasil\nUji skala 740, Windows dan regresi lulus. UTF-8 diperbaiki. Kandidat OCR dievaluasi dan ditolak untuk produksi; 11 usulan visual dibuat. Dokumentasi dan paket review disinkronkan. Sasaran OCR 80% serta penerimaan semantik manusia tetap terbuka sebagai batas penelitian, tidak diklaim selesai.\n';p.write_text(s,encoding='utf-8')
for target in [root/'CHANGELOG.md',package/'CHANGELOG.md']:
 s=target.read_text(encoding='utf-8');s=s.replace('## [Unreleased]\n','## [Unreleased]\n\n### Added\n- Audit HTTP seluruh 740 sampel lulus, 3.700 aset/740 URL heatmap/snapshot diperiksa, CSV/JSON lengkap; bukti `revisi_week3/scale740_verification.json`. Paket review dibangun ulang dengan docs/status terbaru, tanpa cache/job/environment lokal (plan: [docs/plans/2026-10-05-penutupan-teknis-week3.md](docs/plans/2026-10-05-penutupan-teknis-week3.md)).\n',1);target.write_text(s,encoding='utf-8')
for src in (root/'docs').rglob('*.md'):
 dest=package/src.relative_to(root);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dest)
excluded={'venv','_cache','_jobs','__pycache__','finetuned_kaggle','kaggle_benchmark','kaggle_full_smoke','.git'}
archive=root/'DEMO_XAI_745_WEEK3_REVIEW.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for f in package.rglob('*'):
  if f.is_file() and not excluded.intersection(f.relative_to(package).parts) and f.name!='windows_source.zip': z.write(f,f.relative_to(root))
with zipfile.ZipFile(archive) as z: assert z.testzip() is None
print(json.dumps({'status':'passed','zip_bytes':archive.stat().st_size,'audit':result}),flush=True)
