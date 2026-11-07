"""Evidence-based revision responses; missing human work stays visibly open."""
import json
from pathlib import Path
import pandas as pd
from evaluate import TASKS,write_json


REVISIONS={
 'R18':('P1','31 Oktober 2026','Identitas dan pemetaan kandidat','candidate_mapping_36.csv; MAIN_MODEL_DECISION.md'),
 'R19':('P1','3 November 2026','Pemeringkatan Macro-F1','analysis/ranking_36_legacy.csv; analysis/rank_correlation.json'),
 'R20':('P1','3 November 2026','Diagnosis Task3 dan weighting','analysis/task3_entropy.csv; analysis/class_distribution.csv; analysis/paired_tests.csv'),
 'R21':('P1','9 November 2026','Kesetaraan masukan dan Qwen zero-shot','INPUT_PARITY.md; analysis/metrics.csv'),
 'R22':('P1','31 Oktober 2026','Provenance fitur E01','FEATURE_PROVENANCE.json; feature_provenance_20_examples.csv'),
 'R23':('P1','9 November 2026','Agreement manusia dan riwayat korpus','CORPUS_HISTORY.md; HUMAN_EVIDENCE_SEARCH.json; human_inputs/annotation/'),
 'R24':('P2','10 November 2026','Macro-F1 utama, akurasi/kappa pendamping','analysis/metrics.csv; analysis/per_class.csv; tools/evaluate.py'),
 'R25':('P2','16 November 2026','CI dan perbandingan berpasangan','analysis/metrics.csv; analysis/paired_tests.csv; STATISTICAL_METHOD.md'),
 'R26':('P2','16 November 2026','Bias seleksi dan jumlah kandidat','analysis/ranking_36_legacy.csv; analysis/evaluation_verification.json; SELECTION_BIAS.md'),
 'R27':('P2','16 November 2026','MTL versus single-task dan loss aktual','analysis/metrics.csv; analysis/paired_tests.csv; source/; ABLATION_PARITY.md'),
 'R28':('P2','16 November 2026','Prediksi baseline/unimodal','inputs/predictions/; HISTORICAL_REPLAY.md'),
 'R29':('P2','23 November 2026','Backbone dan SigLIP2','analysis/metrics.csv; analysis/paired_tests.csv; ABLATION_PARITY.md'),
 'R30':('P2','23 November 2026','Augmentasi dan pemilihan inner','AUGMENTATION_AUDIT.md; analysis/metrics.csv; source/'),
 'R31':('P2','23 November 2026','Kelas penampung dan dekomposisi Task2','analysis/catchall_sensitivity.csv; analysis/task2_decomposed.csv; human_inputs/catchall_review_60.csv'),
 'R32':('P2','23 November 2026','Reproduksi mandiri dan Colab bersih','README.md; requirements.txt; tools/validate_package.py; qa/'),
 'R33':('P3','24 Desember 2026','Pembingkaian hasil penelitian','MANUSKRIP_DRAF.md; HASIL_DAN_TANGGAPAN.md'),
 'R34':('P3','7 Desember 2026','XAI dan penilai independen','xai_e42/; human_inputs/XAI_RUBRIC.md; human_inputs/xai/'),
 'R35':('P3','24 Desember 2026','Kriteria komparatif tanpa gate0.70','MAIN_MODEL_DECISION.md; STATISTICAL_METHOD.md; tools/evaluate.py'),
 'R36':('P3','24 Desember 2026','Keterbatasan, etika, sitasi','MANUSKRIP_DRAF.md; REFERENCES.md'),
 'R2':('Agustus','belum diperbarui','Codebook dan kelas penampung','CODEBOOK_REVISI.md; human_inputs/catchall_review_60.csv'),
 'R4':('Agustus','7 Desember 2026 terkaitR34','Kelayakan metode visual CLIP','XAI_METHOD.md; xai_e42/'),
 'R6':('Agustus','9 November 2026 terkaitR23','Adjudikasi dan eksklusi','CORPUS_HISTORY.md; human_inputs/annotation/'),
 'R8':('Agustus','16 November 2026 terkaitR28','Baseline dan ablasi','HISTORICAL_REPLAY.md; analysis/metrics.csv'),
 'R9':('Agustus','7 Desember 2026 terkaitR34','Lima penilai independen','human_inputs/XAI_RUBRIC.md; human_inputs/xai/'),
 'R12':('Agustus','10 November 2026 terkaitR24','Macro-F1 sebagai metrik utama','analysis/metrics.csv; tools/evaluate.py'),
 'R13':('Agustus','24 Desember 2026 terkaitR35','Justifikasi ulang target','STATISTICAL_METHOD.md; MANUSKRIP_DRAF.md'),
 'R16':('Agustus','24 Desember 2026 terkaitR36','Sitasi relevan dan terverifikasi','REFERENCES.md'),
 'R17':('Agustus','24 Desember 2026 terkaitR36','Etika dan penyalahgunaan','MANUSKRIP_DRAF.md'),
}


def markdown_table(frame,columns=None):
    table=frame[columns] if columns else frame
    table=table.copy()
    for col in table.select_dtypes(include='number').columns:
        if not pd.api.types.is_integer_dtype(table[col]):table[col]=table[col].map(lambda x:f'{x:.4f}' if pd.notna(x) else 'Not Evaluated')
    def safe(x):return str(x).replace('|','/').replace('\n',' ')
    return '| '+' | '.join(map(safe,table.columns))+' |\n| '+' | '.join('---' for _ in table.columns)+' |\n'+'\n'.join('| '+' | '.join(safe(x) for x in row)+' |' for row in table.itertuples(index=False,name=None))


def create(package):
    root=Path(package);doc=root/'documentation';doc.mkdir(exist_ok=True)
    b=pd.read_csv(root/'analysis/metrics.csv');pairs=pd.read_csv(root/'analysis/paired_tests.csv')
    rank=pd.read_csv(root/'analysis/ranking_36_legacy.csv');state=json.loads((root/'analysis/evaluation_verification.json').read_text())
    decision=json.loads((doc/'MAIN_MODEL_DECISION.json').read_text())
    models=set(b.experiment);rows=[]
    for rid,(priority,date,title,evidence) in REVISIONS.items():
        status='Selesai';missing='';owner='Paket teknis'
        if rid in {'R22'}:
            status='Berjalan';missing='Generator/hash/prompt tersedia; tuntutan isolasi proses historis dan timestamp penciptaan asli belum dapat dibuktikan.';owner='Peneliti/pembimbing: terima bukti field-flow atau minta regenerasi fitur versi baru'
        if rid in {'R23','R6'}:
            status='Berjalan';missing='Alasan umum eksklusi sudah diklarifikasi Joy: kualitas citra buruk sehingga tidak dapat dilabeli, dan menurut Joy pernah disampaikan. Yang belum tersedia: dua set anotasi independen untuk kappa; dokumentasi korpus awal/keputusan per ID dan sensitivitas belum dapat direkonstruksi.';owner='Dua anotator; pemilik data untuk dokumentasi rinci bila tersedia'
        if rid in {'R31'}:
            status='Berjalan';missing='Tabel/codebook/sensitivitas selesai; audit manusia60 sampul dan adjudikasi codebook belum diisi.';owner='Joy/anotator'
        if rid in {'R34','R9'}:
            status='Berjalan';missing='XAI aktual/tes/model replay/rubrik/kontrol tersedia; skor nyata minimal5 penilai independen dan agreement belum tersedia.';owner='Joy/lima penilai independen'
        if rid=='R21':
            required={'RII_TAIL_RICH256','RII_TAIL_MTL_WEIGHTED','RII_TAIL_HEADLINE_ONLY','RII_QWEN_ZERO_BASIC','RII_QWEN_ZERO_RICH','RII_QWEN_QLORA_BASIC','RII_QWEN_QLORA_HEADLINE_ONLY'}
            absent=sorted(required-models)
            if absent:status='Berjalan';missing='Hasil belum lengkap: '+', '.join(absent)+'. Arm basic sebelumnya memuat supporting text sehingga bukan citra+judul literal yang diminta PDF.';owner='Eksperimen GPU/collector'
        if rid=='R27' and 'RII_TAIL_SINGLE_TASK' not in models:status='Berjalan';missing='Ablasi tail single-task belum lengkap.'
        if rid=='R30' and 'RII_A02_MODERATE_NO_ROTATION' not in models:status='Berjalan';missing='Rerun moderate tanpa rotasi masih berlangsung.'
        if rid=='R32':
            qa=root/'qa/COLAB_VERIFICATION.json'
            if not qa.exists() or json.loads(qa.read_text()).get('status')!='verified':
                status='Berjalan';missing='Paket dan uji lokal disediakan; bukti Run all Colab bersih belum terverifikasi.';owner='Uji Colab melalui akun pengguna'
        if rid=='R8':
            status='Berjalan';missing='Ablasi/prediksi tersedia; wording lengkap dokumen Agustus asli belum ditemukan, jadi penutupan R8 lama belum dapat dipastikan.';owner='Joy/pembimbing: dokumenAgustus'
        rows.append(dict(revision_id=rid,priority=priority,original_deadline=date,title=title,status=status,
                         evidence=evidence,remaining=missing,owner=owner))
    tracker=pd.DataFrame(rows);assert len(tracker)==tracker.revision_id.nunique()==28
    tracker.to_csv(doc/'REVISION_TRACKER_28.csv',index=False)
    complete=int((tracker.status=='Selesai').sum());open_count=len(tracker)-complete
    package_state=dict(schema='joy-revisi-ii-package-v1',ready_for_technical_review=True,all_revisions_complete=open_count==0,
                       completed=complete,open=open_count,total=28,primary_model=decision['model_id'],
                       primary_metric='macro_f1',historical_web='CLIP-B32 demo, separate from E42',
                       human_agreement='Not Evaluated',human_xai_ratings='Not Evaluated',
                       release_claim='Paket bukti revisi untuk diperiksa Joy; bukan pernyataan seluruh28butir selesai')
    write_json(root/'PACKAGE_STATE.json',package_state)
    open_rows=tracker[tracker.status!='Selesai']
    responses=['# Tanggapan 28 Revisi\n',f'Status paket: **{complete} butir selesai secara teknis; {open_count} masih terbuka**. '
               'Setiap butir terbuka tetap memerlukan tindakan/bukti di bawah. Status Selesai pada draf naskah berarti materi revisi tersedia, bukan persetujuan pembimbing atau publikasi.\n']
    for row in tracker.itertuples():
        responses.append(f'## {row.revision_id} — {row.title}\n\nStatus: **{row.status}**. Prioritas: {row.priority}. Tenggat asli: {row.original_deadline}.\n\n'
                         f'Bukti: `{row.evidence}`.\n\n'+(f'Yang tersisa: {row.remaining}\n\nPenanggung jawab: {row.owner}.\n' if row.remaining else 'Bukti teknis dan penjelasan tersedia dalam paket; hasil tetap dibatasi oleh protokol dan data yang tersedia.\n'))
    (doc/'TANGGAPAN_28_REVISI.md').write_text('\n'.join(responses))
    (doc/'TINDAK_LANJUT_JOY.md').write_text('# Tindakan yang masih perlu diselesaikan Joy\n\n'+markdown_table(open_rows,['revision_id','title','remaining','owner'])+
        '\n\nAnotasi/penilaian belum dilakukan oleh manusia tidak boleh diganti keluaran AI. Gunakan paket terpisah untuk anotator/penilai; jangan kirim kunci privat koordinator ke penilai. '
        'Untuk metadata sumber yang tidak tersedia, konfirmasi ke pemilik data/pembimbing dengan bukti spesifik; jangan mengarang alasan eksklusi.\n')
    focus=['BASELINE_CLIP_INDoBERT','e42_tail_grid','MICRO_E11_hierarchical_task3','MICRO_E12_structured_decoder','MICRO_E14_joint_qlora_oof']
    primary=b[b.experiment.isin(focus)]
    (doc/'HASIL_DAN_TANGGAPAN.md').write_text('# Hasil Revisi II dan Koreksi Penafsiran\n\n'
      'Model utama penelitian ditetapkan E42, bukan baseline web historis dan bukan Qwen. Pemilihan post-hoc berdasarkan rerata Macro-F1 kandidat proposal yang layak dinyatakan terbuka.\n\n'+
      markdown_table(primary,['experiment','task','macro_f1','macro_ci_low','macro_ci_high','accuracy','accuracy_ci_low','accuracy_ci_high','kappa'])+
      '\n\nAngka dalam tabel menggunakan fraksi; CSV menyimpan presisi penuh. Perbedaan poin persentase =100×selisih fraksi. Tidak ada gate kelulusan absolut0,70 dalam keputusan baru.\n\n'
      f'Ranking36nama mereproduksi Pearson {state["rank_correlation"]["pearson_minima"]:.6f} dan Spearman '
      f'{state["rank_correlation"]["spearman_minima"]:.6f} untuk minimum akurasi versus minimum macro. '
      'Spearman berbeda dari0,050 di PDF; ties ditangani sebagai tied ranks, bukan ordinal berdasarkan urutan baris. Kesimpulan kualitatif korelasi lemah tetap berlaku.\n\n'
      'Filter nama non-vlm/non-qlora bukan bukti backbone: E11/E12 tetap mengandung fitur turunan VLM. '
      'M00/E42 dan representasi A00/A01/selected mempunyai salinan prediksi; jumlah nama bukan jumlah eksperimen independen.\n\n'
      'Baselinehistoris memang lebih rendah dari majority pada akurasi Task3, tetapi diagnosis itu tidak boleh otomatis dipindahkan ke E42 terpilih. '
      'Kenaikan E11→E14 Task2 tidak didukung bukti selisih akurasi signifikan pada prediksi yang tersedia; tidak signifikan juga bukan pembuktian equivalence. '
      'E12 dinilai per task dan metrik, bukan sekadar diberi label gagal dari minimum micro.\n\n'
      'Source extractorbaseline sudah memakai headline_verified + supporting_text_verified, dan source training sudah memakai class weighting. '
      'Permintaan menambahkan supporting/weighting dijawab dengan bukti aktual dan kontrol yang benar, bukan mengulang asumsi bahwa keduanya tidak pernah ada.\n')
    (doc/'STATISTICAL_METHOD.md').write_text('# Metode evaluasi dan statistik\n\n'
       'Metrik utama Macro-F1 dengan codebook label tetap (zero_division=0), disajikan per task. Rerata tiga Macro-F1 berbobot sama hanya ringkasan; minimum diagnostik. '
       'Akurasi, macro-precision/recall, Cohen kappa dan metrik per kelas disertakan. Micro-F1 single-label identik dengan akurasi dan tidak dipakai untuk memberi kesan metrik berbeda.\n\n'
       'CI akurasi: Wilson95%. CI Macro-F1: percentile bootstrap2000 replikasi atas pasangan gold/prediksi, seed20261101+indeks task. '
       'Selisih macro memakai bootstrap berpasangan atas triple gold/before/after. Implementasi multinomial histogram joint ekuivalen terhadap resampling IID pengamatan, dengan kelas yang tidak muncul di replikasi tetap berada pada denominator macro.\n\n'
       'McNemar exact dua sisi menguji selisih benar/salah, yaitu akurasi, bukan Macro-F1. Holm diterapkan ke seluruh pasangan-task yang dicantumkan dalam satu keluarga. '
       'Pasangan di keluarga baru ditetapkan dalam source evaluator sebelum tabel baru dihasilkan. CI bootstrap selisih bersifat pointwise eksploratif; jangan menganggapnya sudah terkoreksi family-wise. '
       'Tidak signifikan bukan bukti kesetaraan, dan besar selisih tidak boleh diberi p hanya dari jumlah sampel benar yang tidak berpasangan.\n\n'
       'Seluruh inference bersyarat pada prediksi OOF tersimpan: overlap data training lintasfold, adaptive selection pada korpus sama, annotator uncertainty dan variability seed baru belum seluruhnya tercakup. '
       'Tidak ada holdout baru yang diklaim dari fold yang pernah dipakai seleksi. Kriteria keberhasilan adalah perbandingan yang terukur terhadap majority/unimodal/single-task, bukan angka0,70 tunggal. '
       'Target proposal historis tetap disebut sebagai target lama yang belum tercapai, bukan dihapus dari sejarah.\n\n'
       'Sumber metode: [SciPy binomtest](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.binomtest.html), '
       '[SciPy paired bootstrap](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.bootstrap.html), '
       '[Dietterich1998](https://doi.org/10.1162/089976698300017197).\n')
    nfull=state['full_740_models'];nunique=len({r['prediction_signature'] for r in state['source_records'] if r['samples']==740})
    (doc/'SELECTION_BIAS.md').write_text('# Pemakaian ulang korpus dan hitungan eksperimen\n\n'
       f'Inventaris saat build memuat {nfull} nama sumber evaluasi lengkap740 dan {nunique} signature prediksi lengkap yang berbeda. '
       'Ini hitungan artefak prediksi yang terdaftar, bukan jumlah pasti seluruh trial optimasi historis; prediksi identik dapat berasal dari alias maupun kebetulan. '
       'Tabel khusus mempertahankan36nama dari filter notebook lama untuk menjawab PDF.\n\n'
       'E42 sendiri menguji6konfigurasi LR/loss ×6kandidat epoch pada inner folds; ini tidak boleh disamakan dengan6eksperimen outer independen. '
       'Daftar source, konfigurasi, fold dan signature disertakan supaya pembaca dapat menghitung unit perbandingan yang tepat. '
       'Jumlah trial yang gagal/tidak meninggalkan artefak tidak dapat dibuktikan dari workspace ini dan tidak diisi sebagai nol.\n\n'
       'Pilihan penanganan bias: disclosure terbuka pada abstrak/metode/keterbatasan. Hasil final adalah seleksi post-hoc pada korpus yang digunakan berulang, sehingga dapat optimistis. '
       'Belum ada validasi eksternal yang dapat diklaim. Sampel2026baru hanya dapat menjadi validasi eksternal jika benar-benar di luar korpus dan belum dipakai untuk seleksi, disertai anotasi nyata.\n')
    (doc/'HISTORICAL_REPLAY.md').write_text('# Pemulihan prediksi baseline\n\n'
       'RII_FROZEN_MTL_WEIGHTED mereplikasi120epoch full-batch, seed42, shared256/ReLU/dropout0.4, AdamW1e-3/wd1e-4, '
       'class weights training-only, CLIP-B32+IndoBERT CLS beku, dan lima fold yang sama. '
       'Prediksi ketiga task identik terhadap kolom baseline E42 pada seluruh740sampel (0perbedaan). '
       'Image-only dan text-only juga menghasilkan metrik historis yang sama, kini dengan prediksi mentah lengkap. '
       'Single-task/tanpa weighting/headline-only/rich128 adalah kontrol baru yang diberi nama terpisah, bukan angka historis yang ditulis ulang. '
       'Text-only supporting sebenarnya sudah ada pada extractor lama; headline-only ditambahkan sebagai kontras input yang jelas.\n\n'
       'Keluarga ini adalah ablation baseline CLIP-B32 beku, bukan ablasi E42 yang memiliki CLIP-L14 dan tail teks trainable. '
       'Ablasi E42-family baru berada pada RII_TAIL_*. Semua sumber/seed/fold/OOF dipertahankan.\n')
    (doc/'ABLATION_PARITY.md').write_text('# Kontrak perbandingan ablasi\n\n'
       '- Historical baseline family: CLIP-B32/IndoBERT CLS frozen, head256/dropout0.4/120epoch. '
       'Weighted/unweighted/single-task/image/text berbagi input, seed, split dan anggaran yang dijelaskan dalam protokol.\n'
       '- RII_TAIL family: CLIP-L14 full/crop + first10IndoBERT frozen + last2trainable, shared256/dropout0.3; LR2e-5/3e-4, '
       'fixed task loss1:2:2; epoch0/2/4/8 dipilih berdasarkan meanMacro-F1 inner2fold. Canonical GPU FP32 reload diuji. '
       'Ini resep controlled baru, bukan grid E42 historis6konfigurasi/24epoch. Single-task terdiri dari tiga salinan independen dan memerlukan3×model/tuning head; biaya komputasi dicatat terpisah.\n'
       '- E48 lama adalah LinearSVC dengan pencarian fitur/normalisasi/C, sehingga tetap diagnostik dan tidak dipakai sebagai bukti isolasi efek neural MTL. '
       'E49 routed-experts dan J01 hierarki dipertahankan sebagai varian arsitektur, bukan ablation yang hanya membedakan satu head.\n'
       '- Frozen backbone controls baru memakai image768 + meantext768 sama, head/loss/seed/120epoch sama; CLIP full-view, SigLIP2 dan DINOv2. '
       'M01lama memakai concatenationfull+crop2304 sementara M02/M03 memakai1536, sehingga klaim backbone lama bukan isolasi sempurna. '
       'Resolusi/pretraining encoder berbeda secara inheren dan dinyatakan.\n'
       '- Tidak ada p-value yang diartikan sebagai ujiMacro-F1. Lihat paired bootstrap untuk selisihmacro dan exactMcNemar untuk akurasi.\n')
    (doc/'INPUT_PARITY.md').write_text('# Arsitektur dan kekayaan masukan\n\n'
       'Basic yang benar untuk model utama adalah citra + headline_verified + supporting_text_verified. '
       'Rich menambah description1000char, sumber_visual250char dan alasan500char dari E01. Label gold dan domain prediksi tidak dialirkan menjadi field fitur.\n\n'
       '| Arsitektur | Basic | Rich |\n|---|---|---|\n'
       '| CLIP–IndoBERT tail controlled | RII_TAIL_MTL_WEIGHTED (128token) | RII_TAIL_RICH256 (256token) |\n'
       '| Qwen3-VL QLoRA | RII_QWEN_QLORA_BASIC | MICRO_E14_joint_qlora_oof historis |\n\n'
       'Zero-shot Qwen basic/rich adalah kontrol tambahan tanpa training, bukan OOF model terlatih. '
       'RII_FROZEN_MTL_RICH adalah kontrol CLS128 terpisah:736/740teks terpotong. Cache rich256 meliputi seluruh input pada data ini, tetapi tokenisasi/input efektif tetap berbeda antarmodel. '
       'Pada tail, nilai max-length ikut berubah agar rich tidak terpotong; perbandingan ini menilai konfigurasi input praktis, bukan isolasi panjang token.\n\n'
       'Basic QLoRA memakai epoch per fold yang sama dengan pilihan inner rich historis[3,1,3,2,3], seed/refit/protokol sama; '
       'fold1 mengembalikan adapter awal pilot yang sama. Ini kontras input bersyarat pada resep rich, bukan tuningbasic independen berbasisMacro. '
       'Hanya tabel hasil yang benar-benar tersedia boleh dipakai; sel kosong tetap Not Evaluated dan R21terbuka sampai740prediksi diverifikasi.\n')
    (doc/'AUGMENTATION_AUDIT.md').write_text('# Audit augmentasi\n\n'
       'AUG_SELECTED historis dipilih pada inner fold, bukan berdasarkan pemenang outer. Karena itu boleh kalah dari A01 pada outer; '
       'menggantinya setelah melihat outer justru memperkenalkan pemilihan pada test. A00/A01/A02/A03 lama dipertahankan.\n\n'
       'Source lama memang memakai rotasi±2derajat pada moderate. Revisi baru menghapus rotasi dengan tetap mengonsumsi draw RNG yang sama, '
       'sehingga brightness/contrast/JPEG/noise tidak ikut berubah akibat pergeseran RNG. Tidak ada cropgeometris pada transform augmentasi baru. '
       'Model/resize-native SigLIP2 tetap dicatat terpisah dari augmentasi.\n\n'
       'Kontrol baru menggunakan35epoch/head192 sama, tepatntrainingdraws/epoch, pilihan50%clean/50%fixedaugmented, '
       'samplerjointinverse-sqrt hanya pada training; semua validation/test bersih. Pemilihan pipeline memakai innermeanMacro-F1. '
       'Protokol baru memperbaiki juga jumlah paparan/update yang sebelumnya bertambah karena clean+aug diduplikasi. '
       'Karena lebih dari satu perbaikan protokol, perbandingan legacy versus baru bukan isolasi rotasi tunggal.\n\n'
       'Tidak ditemukan back-translation dalam pipeline augmentasi yang benar-benar dijalankan; audit30contoh tidak berlaku pada metode yang tidak digunakan. '
       'Jangan membuat 30 terjemahan baru seolah-olah bukti historis.\n')
    xai=root/'xai_e42'
    if (xai/'deletion_faithfulness.csv').exists():
        fd=pd.read_csv(xai/'deletion_faithfulness.csv');lm=pd.read_csv(xai/'conditional_lime.csv')
        evidence=markdown_table(fd.groupby('task',as_index=False)[['rollout_top20_drop','random20_mean_drop','drop_difference']].mean())
        lime=markdown_table(lm.groupby('task',as_index=False).local_r2.agg(['min','mean','max']).reset_index())
    else:evidence='Not Evaluated';lime='Not Evaluated'
    (doc/'XAI_METHOD.md').write_text('# XAI model utama E42\n\n'
       'Delapan ID dipilih acak dengan seed sebelum penjelasan. Setiap sampel dijelaskan dengan checkpoint outer fold yang tidak melatih sampel tersebut. '
       'Fitur CLIP, teks, dan prediksi direplay terhadap cache/OOF. Source, checkpoint dan hasil parity ada pada heldout_replay.csv.\n\n'
       'Visual: attention rollout Abnar–Zuidema, mean heads, residualidentity dan matrix product lintas layer. '
       'Peta bersifat class-agnostic, bukan Grad-CAM dan bukan bukti keputusan kelas secara otomatis. '
       'Dua viewCLIP full/crop dipetakan kembali melalui area center-crop preprocessing sebelum digabung. '
       'Tidak mengganti backbone ke ResNet untuk memudahkan penjelasan.\n\n'
       'Teks: LIME untuk skor kelas prediksi head yang sama dengan visual aktual ditahan tetap, 256 perturbasi lokal, seed tetap. '
       'Koefisien adalah atribusi kondisional terhadap citra dan surrogate lokal; localR² disertakan, sehingga contoh dengan kecocokan rendah tetap terlihat.\n\n'
       'Faithfulness eksploratif: hapus20%sel grid8×8 bernilai rollout tertinggi, bandingkan penurunan skor kelas asal dengan rata-rata3maskacak berukuran sama. '
       'Skor dapat naik setelah deletion; nilai negatif tidak dibuang. Hanya8sampel, bukan evaluasi seluruh korpus atau model refit deployment.\n\n'+evidence+
       '\n\nHasil campuran tidak mendukung klaim universal bahwa rollout menjelaskan kelas dengan faithful. '
       'Peta tersedia sebagai attention-flow diagnostic; faithfulness yang belum kuat adalah hasil negatif yang harus dilaporkan.\n\n'
       'Kecocokan surrogate LIME:\n\n'+lime+
       '\n\nPenilaian manusia: paket berkode dan kontrolacak sudah disiapkan. Belum ada skor lima penilai dan belum ada agreement manusia. '
       'Instrumen menilai kejelasan/relevansi/keterpahaman, sedangkan faithfulness model diuji terpisah. '
       'Jangan menyebut persepsi manusia sebagai pengujian kausal perilaku model.\n\n'
       'Metode rujukan: [Abnar & Zuidema2020](https://aclanthology.org/2020.acl-main.385/), '
       '[LIME](https://aclanthology.org/N16-3020/). [Chefer dkk.ICCV2021](https://openaccess.thecvf.com/content/ICCV2021/html/Chefer_Generic_Attention-Model_Explainability_for_Interpreting_Bi-Modal_and_Encoder-Decoder_Transformers_ICCV_2021_paper.html) '
       'merupakan alternatif khusus transformer, bukan nama metode yang diklaim sudah diimplementasikan dalam paket ini.\n')
    (doc/'REFERENCES.md').write_text('''# Referensi primer yang diperiksa

Metadata di bawah diperiksa terhadap halaman penerbit/penulis, 1 November2026. Referensi hanya mendukung metode yang disebut; tidak mengubah hasil internal menjadi validasi eksternal.

1. Abnar, S., & Zuidema, W. (2020). *Quantifying Attention Flow in Transformers*. ACL, 4190–4197. DOI: [10.18653/v1/2020.acl-main.385](https://aclanthology.org/2020.acl-main.385/). Metode rollout yang diimplementasikan.
2. Ribeiro, M., Singh, S., & Guestrin, C. (2016). *“Why Should I Trust You?”: Explaining the Predictions of Any Classifier*. NAACL Demonstrations, 97–101. DOI: [10.18653/v1/N16-3020](https://aclanthology.org/N16-3020/). Ini publikasi demonstrasi ACL; jangan mencampur metadata dengan versi KDD yang berbeda.
3. Chefer, H., Gur, S., & Wolf, L. (2021). *Generic Attention-Model Explainability for Interpreting Bi-Modal and Encoder-Decoder Transformers*. ICCV, 397–406. [Halaman penerbit](https://openaccess.thecvf.com/content/ICCV2021/html/Chefer_Generic_Attention-Model_Explainability_for_Interpreting_Bi-Modal_and_Encoder-Decoder_Transformers_ICCV_2021_paper.html). Alternatif metode, tidak diimplementasikan di paket ini.
4. Kendall, A., Gal, Y., & Cipolla, R. (2018). *Multi-Task Learning Using Uncertainty to Weigh Losses for Scene Geometry and Semantics*. CVPR. [Halaman penerbit](https://openaccess.thecvf.com/content_cvpr_2018/html/Kendall_Multi-Task_Learning_Using_CVPR_2018_paper.html). Related work saja: E42 memakai bobot loss tetap, bukan learned uncertainty.
5. Dietterich, T. G. (1998). *Approximate Statistical Tests for Comparing Supervised Classification Learning Algorithms*. Neural Computation, 10(7), 1895–1923. [DOI10.1162/089976698300017197](https://doi.org/10.1162/089976698300017197). Uji berpasangan tetap memiliki batas ketergantungan CV/seleksi.
6. Dettmers, T., Pagnoni, A., Holtzman, A., & Zettlemoyer, L. (2023). *QLoRA: Efficient Finetuning of Quantized LLMs*. [arXiv2305.14314](https://arxiv.org/abs/2305.14314). Dasar pembanding QLoRA, bukan arsitektur model utama.
7. Qwen Team. *Qwen3-VL-8B-Instruct model card*. [Sumber resmi model](https://huggingface.co/Qwen/Qwen3-VL-8B-Instruct). Revisi eksperimen dikunci `0c351dd01ed87e9c1b53cbc748cba10e6187ff3b`; jangan menganggap model main yang berubah otomatis sama dengan pin eksperimen.
8. Koo, T. K., & Li, M. Y. (2016). *A Guideline of Selecting and Reporting Intraclass Correlation Coefficients for Reliability Research*. Journal of Chiropractic Medicine, 15(2), 155–163. DOI10.1016/j.jcm.2016.02.012. [Artikel](https://pmc.ncbi.nlm.nih.gov/articles/PMC4913118/) dan [erratum](https://pmc.ncbi.nlm.nih.gov/articles/PMC5731844/). Desain yang disiapkan: two-way random, absolute agreement, single measure ICC(2,1); belum ada angka manusia.
9. SciPy contributors. Dokumentasi resmi [binomtest](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.binomtest.html) dan [bootstrap](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.bootstrap.html). Versi lokal yang diuji tercantum pada requirements dan QA, bukan diasumsikan sama dengan versi dokumentasi daring.
''')
    codebook=json.loads((doc/'FEATURE_PROVENANCE.json').read_text())['prompt_b_template']
    definitions=json.loads((doc/'TASK_DEFINITIONS.json').read_text())['definitions']
    definition_tables='\n\n'.join('### '+task+'\n\n'+markdown_table(pd.DataFrame([dict(label=label,definition=meaning) for label,meaning in values.items()])) for task,values in definitions.items())
    (doc/'CODEBOOK_REVISI.md').write_text('# Codebook operasional dan adjudikasi\n\n'
       'Label canonical tetap. Tidak ada relabeling otomatis berdasarkan kesalahan model. Definisi tiga task dan daftar label bersumber dari source/protokol yang disertakan. '
       'Task1: isu utama paling dominan; Task2: domain sumber pemetaan metaforis, berbeda dari isu sasaran; Task3: tipe entitas yang menjadi fokus kritik, bukan setiap objek yang tampak.\n\n'
       'Kelas penampung harus dipakai dengan alasan tertulis. `other_issue`: isu dapat diidentifikasi tetapi berada di luar sembilan kategori utama. '
       '`LAINNYA`: ada pemetaan metaforis yang dapat dijelaskan, tetapi sumber tidak termasuk lima domain positif; jangan dipakai hanya karena penilai ragu. '
       '`NON_METAFORA`: tidak ditemukan pemetaan sumber–sasaran yang dapat dipertanggungjawabkan; berbeda dari metafora yang sumbernya di luar taxonomy. '
       '`multiple_or_other`: catat terpisah alasan “beberapa sasaran dominan” atau “tipe tidak tercakup”, bukan menyatukan semua ketidakpastian.\n\n'
       'Prosedur: dua anotator menilai independen, menyimpan label/tingkat keyakinan/alasan; kappa dihitung sebelum diskusi; adjudikator menulis keputusan dan alasan di file baru. '
       'Sampel sengketa tidak dihapus hanya untuk menaikkan metrik. Pemecahan kelas memerlukan dataset/codebook versi baru dan tabel pemetaan; hasil lama tetap dipertahankan.\n\n'
       'Audit 60 contoh disiapkan untuk memastikan apakah ada subgroup koheren. Belum ada keputusan manusia yang dapat dijadikan dasar perubahan gold. '
       'Template anotasi150 tidak memuat gold/model prediction. Daftar kategori yang diperbolehkan ada di protocol.json.\n\n'
       'Definisi seluruh label sesuai taxonomy yang dipakai, tanpa perubahan gold:\n\n'+definition_tables+'\n\n'
       'Jika beberapa isu/sasaran sama dominannya, anotator menuliskan pilihan dan alasan untuk adjudikasi; jangan menyamakan ketidakpastian dengan NON_METAFORA atau membuang kasus sengketa. '
       'Bedakan kritik orang tertentu (`individual`) dari institusi eksekutif (`government`) berdasarkan fokus kritik, bukan semata-mata ada gambar manusia.\n\n'
       'Definisi sumber Task2 yang digunakan pada generator historis (sebagai bukti prompt, bukan hasil adjudikasi baru):\n\n```text\n'+codebook+'\n```\n')
    main_rows=b[b.experiment=='e42_tail_grid'];main_table=markdown_table(main_rows,['task','macro_f1','macro_ci_low','macro_ci_high','accuracy','kappa'])
    comparison=b[b.experiment.isin(['RII_TAIL_MTL_WEIGHTED','RII_TAIL_SINGLE_TASK','RII_TAIL_MTL_UNWEIGHTED','RII_TAIL_IMAGE_ONLY','RII_TAIL_TEXT_SUPPORTING'])]
    new_table=markdown_table(comparison,['experiment','task','macro_f1','accuracy','kappa'])
    (doc/'MANUSKRIP_DRAF.md').write_text('''# Kelayakan MTL CLIP–IndoBERT untuk Dekoding Metafora Sampul Tempo: Evaluasi Macro-F1 dan Batas Penjelasan Model

**Status:** draf materi penelitian untuk diperiksa Joy/pembimbing; belum mengikuti template jurnal tertentu, belum melalui penilaian manusia tambahan, dan belum disubmit. Bagian yang memerlukan bukti manusia dinyatakan terbuka.

## Abstrak
Penelitian ini mengevaluasi arsitektur multi-task learning CLIP–IndoBERT untuk klasifikasi isu, domain sumber metafora, dan tipe entitas sasaran pada740sampul majalah Tempo. Evaluasi menggunakan lima outerfold dan pemilihan konfigurasi pada innerfold. Audit ulang menggunakan Macro-F1 menunjukkan bahwa peringkat kandidat bergantung kuat pada metrik dan dapat berbeda dari peringkat akurasi. Model E42, yang dipilih post-hoc dari kandidat arsitektur yang memenuhi spesifikasi, menghasilkan Macro-F1 sekitar0,525/0,396/0,403. Angka merupakan seleksi pada korpus yang digunakan berulang dan berpotensi optimistis; belum merupakan validasi eksternal. Ablasi terkontrol dan pengujian XAI memperlihatkan keterbatasan yang tidak dapat diringkas sebagai keberhasilan universal MTL. Nilai kesepakatan anotator dan penilaian XAI independen belum tersedia dan tidak diestimasi sebagai pengganti data manusia.

## Pendahuluan dan kontribusi
Sampul pers menggabungkan ilustrasi dan tulisan untuk menyampaikan kritik dan hubungan metaforis yang tidak selalu dapat dipahami dari satu modalitas saja. Penelitian ini menguji kelayakan arsitektur multimodal dengan representasi visual CLIP dan teks IndoBERT yang dilatih dengan tiga objective. Fokus pertanyaannya adalah kinerja per task, kontribusi pembelajaran bersama dibanding kontrol, dan batas interpretasi penjelasan model.

Kontribusi yang dapat didukung adalah penataan korpus dan evaluasi tiga task, audit empiris perubahan seleksi ketika metrik diganti, serta pemetaan keterbatasan arsitektur/protokol dan penjelasannya. Klaim bahwa korpus merupakan yang pertama di dunia tidak dibuat tanpa kajian pembanding. Qwen3-VL QLoRA digunakan sebagai pembanding berskala lebih besar dengan konteks input yang dijelaskan, bukan sebagai pengganti diam-diam arsitektur utama.

## Data dan anotasi
Dataset canonical berisi740ID dengan10kelas isu,7kelas domain sumber dan8kelas tipe entitas. Jumlah dan distribusi per kelas dapat direproduksi dari dataset paket. Label merupakan interpretasi anotasi, bukan kebenaran objektif tunggal. Kolom keyakinan anotator bukan ukuran agreement antar dua manusia.

Menurut klarifikasi Joy yang diteruskan pengguna pada 2 November 2026, korpus berkurang karena banyak citra sampul berkualitas buruk sehingga tidak dapat dilabeli; menurut Joy alasan ini telah disampaikan sebelumnya. Dengan demikian alasan umum penyusutan telah dijelaskan. Pesan menyebut sekitar 1.000 ke 700-an; angka spesifik 1.040 berasal dari dokumen revisi/proposal dan 740 ID terverifikasi pada dataset. Riwayat keputusan per ID belum dapat direkonstruksi dari berkas yang tersedia, sehingga distribusi eksklusi dan analisis sensitivitas tetap terbatas. Kualitas citra tidak disamakan dengan sengketa label atau kesulitan interpretasi semantik. Anotasi independen dua penilai masih diperlukan untuk kappa, terpisah dari penjelasan penyusutan. Paket menyediakan subsampel acak150sampul untuk anotasi ganda serta60kasus kelas penampung untuk adjudikasi. Sampai diisi manusia, kappa antaranotator tetap Not Evaluated. Lihat CORPUS_HISTORY.md dan R23_KLARIFIKASI_JOY.json.

## Metode model dan evaluasi
E42 menggunakan CLIP ViT-L/14 beku pada viewfull/crop, IndoBERT dengan sepuluh blok awal beku serta dua blok terakhir trainable, sharedlayer256 dan tiga head. JointLoss berupa CE berbobot kelas dari training dan bobot task tetap; learned uncertainty weighting Kendall tidak diimplementasikan. Variasi LR/loss dan epoch dipilih pada innerfold historis. Outerfold ditetapkan menurut stratifikasi Task1; keseimbangan Task2/3 perlu dibaca dari distribusi per fold.

Model utama dipilih setelah kandidat dievaluasi pada korpus yang sama, berdasarkan rerata Macro-F1 per task dengan bobot sama di antara kandidat yang memenuhi arsitektur proposal. Ini seleksi post-hoc, bukan keputusan yang telah dipreregistrasikan sebelum melihat seluruh hasil. Alias dan salinan prediksi didokumentasikan, dan kandidat yang memakai SigLIP2/DINOv2/stacking tidak diberi identitas arsitektur CLIP–IndoBERT utama.

Metrik utama adalah Macro-F1; precision/recall macro, akurasi, kappa model dan metrik per kelas melengkapi laporan. Wilson95%dipakai untuk akurasi, bootstrap2000replikasi untuk macro dan selisih macro berpasangan. ExactMcNemar/Holm menguji selisih akurasi, bukan macro. CI bersyarat pada prediksi OOF dan tidak menghilangkan bias seleksi atau ketergantungan training lintasfold. Kriteria keberhasilan berupa perbandingan terukur dengan kontrol, bukan ambang0,70universal.

## Hasil utama
'''+main_table+'''

Hasil menunjukkan kemampuan yang terbatas dan tidak merata antar task. Domain sumber tetap lebih sulit daripada isu utama. Tidak ada alasan mengganti Macro-F1 dengan akurasi ketika keduanya memberi gambaran berbeda. Kegagalan baseline web historis terhadap majority pada akurasi Task3 dilaporkan sebagai temuan baseline itu; kesimpulan tersebut tidak otomatis berlaku pada E42 yang dipilih kemudian.

## Ablasi dan pembanding
'''+new_table+'''

Resep controlledtail baru memakai backbone/representasi yang sama, fixedLR dan seleksi epoch inner menurut meanMacro, tetapi bukan reproduksi grid6konfigurasi E42 historis. MTL dan single-task harus dibandingkan per task dan CI; tidak dibuat klaim semua task selalu memperoleh manfaat. E48 lama memakai SVM dan bukan ablation neural murni. Prediksi baseline/unimodal yang dahulu hilang direkonstruksi dan kecocokan baseline740dibuktikan.

Kontrol backbone baru mempertahankan dimensi visual768, teks768, head/loss/split yang sama. Hasil SigLIP2/DINOv2 diposisikan sebagai pembanding backbone pada keluarga frozen yang dinyatakan; tidak disamakan dengan varian E42 yang menyesuaikan tail. Augmentasi moderate historis mengandung rotasi. Rerun baru menghapus rotasi dan menyeimbangkan paparan training, dengan pemilihan pipeline hanya pada innerfold. Pipeline tidak dipilih ulang berdasarkan skor outer.

Konteks input Qwen lebih kaya pada eksperimen historis. Tabel arsitektur×masukan, zero-shot tanpa training, dan refitbasic dengan epoch yang diwarisi dari pilihan inner rich digunakan untuk memeriksa kontribusi input. Sel yang belum memiliki740prediksi valid tetap terbuka. Perbedaan ukuran model/pretraining/token budget dan sejarah pemilihan epoch membatasi atribusi selisih hanya kepada arsitektur.

## Analisis kelas penampung dan penjelasan
Macro lengkap mempertahankan seluruh kelas dan sampel. Sensitivitas tanpa label penampung serta subset gold non-penampung disajikan dengan definisi yang berbeda dan eksplisit. Task2dipisahkan menjadi deteksi metafora dan klasifikasi domain pada sampel gold bermetafora; prediksi NON_METAFORA tetap dihitung sebagai kesalahan domain. Kelas tidak dihapus untuk menaikkan angka utama.

XAI E42 direplay pada delapan sampel outertest. Attentionrollout menunjukkan aliran perhatian visual yang class-agnostic dan tidak disebut Grad-CAM. LIME menjelaskan headkelas dengan citra ditahan tetap dan menyertakan kecocokan surrogate. Deletion top20%versus kontrolacak memberikan hasil campuran; peta menarik secara visual tidak otomatis faithful. Rubrik/kontrol dan paket lima penilai sudah disiapkan, tetapi skor serta agreement manusia belum tersedia. Karena itu belum ada klaim acceptance manusia atas kualitas penjelasan.

## Keterbatasan
Korpus dipakai berulang untuk pemilihan banyak konfigurasi; kandidat terpilih dapat optimistis. Data berasal dari satu penerbit sehingga kerangka editorialnya tidak mewakili seluruh pers Indonesia. Label adalah interpretasi manusia; agreement belum terukur. Riwayat penyusutan belum lengkap. Crop/resize pada encoder dapat membuang teks/komposisi, dan pembanding Qwen dibatasi citra384piksel. Opsi jawaban Qwen tetap dalam urutan yang sama sehingga bias posisi belum dikontrol. Fold1rich E14 memakai reuseinnerpilot dan batas3epoch ditentukan setelah riwayat6epoch; outertest tidak dipakai, tetapi keputusan pilot tetap menjadi keterbatasan desain. Semua temuan adalah internal repeated-corpus evaluation, bukan independent acceptance.

## Etika dan pembatasan penggunaan
Sistem ditujukan untuk analisis deskriptif hubungan visual-verbal dan sasaran kritik dalam korpus penelitian. Prediksinya bukan penetapan kebenaran, kewajaran, atau kelayakan kritik pers dan tidak boleh dipakai untuk menilai seseorang secara otomatis.

Kemampuan mengelompokkan sasaran kritik dapat disalahgunakan untuk memantau, membungkam, atau menekan kritik pers. Penggunaan di luar riset memerlukan penilaian dampak dan pemeriksaan manusia; laporan perlu mengungkap kesalahan, ketimpangan kelas, dan keterbatasan penerbit/korpus secara terbuka.

Paket ini disiapkan untuk penyerahan privat kepada peneliti/pemilik proyek. Paket tidak memberikan lisensi publik atas citra sampul, dataset, atau bobot pihak ketiga. Kebijakan akses riset melalui permintaan tertulis merupakan usulan yang perlu disahkan pemilik data/pembimbing sebelum distribusi lebih lanjut. Model publik dasar tetap mengikuti lisensi penyedianya; tidak ada klaim kepemilikan atas karya sampul.

## Kesimpulan
Evaluasi ulang mendukung pelaporan Macro-F1 per task, pemisahan arsitektur utama dan pembanding, serta pengungkapan seleksi post-hoc. Penelitian menghasilkan bukti kemampuan sekaligus batas MTL CLIP–IndoBERT, dengan hasil negatif/trade-off yang dipertahankan. Validasi eksternal, agreement manusia, adjudikasi codebook dan evaluasi XAI independen merupakan pekerjaan yang masih perlu dituntaskan sebelum mengklaim generalisasi dan acceptance penuh. Target proposal historis yang belum terpenuhi dilaporkan tanpa mengubah hasil atau menetapkan ambang pengganti setelah melihat skor.

## Referensi
Lihat REFERENCES.md. Sitasi model/metode harus mengikuti implementasi aktual, bukan menjadikan related work sebagai klaim modul yang telah digunakan.
''')
    replacements={'740sampul':'740 sampul','740sampel':'740 sampel','740prediksi':'740 prediksi','740ID':'740 ID',
                  '120epoch':'120 epoch','120full':'120 full','35epoch':'35 epoch','36nama':'36 nama','28butir':'28 butir',
                  '5penilai':'5 penilai','limaouter':'lima outer','innerfold':'inner fold','outerfold':'outer fold',
                  'outertest':'outer test','viewfull':'view full','sharedlayer':'shared layer','JointLoss':'Joint Loss',
                  'Task1':'Task 1','Task2':'Task 2','Task3':'Task 3','8sampel':'8 sampel','8×8':'8 × 8',
                  '20%sel':'20% sel','20%versus':'20% versus','3maskacak':'3 mask acak','kontrolacak':'kontrol acak',
                  'attentionrollout':'attention rollout','Attentionrollout':'Attention rollout','localR²':'local R²',
                  'headkelas':'head kelas','frozenyang':'frozen yang','6konfigurasi':'6 konfigurasi','24epoch':'24 epoch',
                  '256token':'256 token','128token':'128 token','128teks':'128 teks','4kandidat':'4 kandidat',
                  '2fold':'2 fold','3fold':'3 fold','scoremanusia':'score manusia','tahapR':'tahap R',
                  'minimum micro':'minimum akurasi','baselinehistoris':'baseline historis',
                  'Fold1rich':'Fold 1 rich','384piksel':'384 piksel','Wilson95%':'Wilson 95%',
                  '2000replikasi':'2000 replikasi','bootstrap2000':'bootstrap 2000','ExactMcNemar':'Exact McNemar',
                  'Macro-F1berbasis':'Macro-F1 berbasis','meanMacro':'mean Macro','microtarget':'micro target',
                  '3epoch':'3 epoch','6epoch':'6 epoch','0,70universal':'0,70 universal',
                  '1.040dan':'1.040 dan','penyusutan300':'penyusutan 300','150sampul':'150 sampul','60kasus':'60 kasus',
                  '10kelas':'10 kelas','7kelas':'7 kelas','8kelas':'8 kelas','November2026':'November 2026'}
    for path in doc.glob('*.md'):
        text=path.read_text()
        for old,new in replacements.items():text=text.replace(old,new)
        path.write_text(text)
    return package_state
