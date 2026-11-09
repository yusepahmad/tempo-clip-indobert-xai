# CI-D01 — CLIP–IndoBERT dengan training digandakan 2×

## Hasil final terverifikasi — 20 Oktober 2026

Job full version1 **COMPLETE**. Kedua arm mempunyai740 prediksi OOF unik dari
lima fold dan telah dikoleksi/VERIFIED. Ini tetap CLIP–IndoBERT, bukan Qwen.

| Task | Macro-F1 kontrol1× | Macro-F1 duplikasi2× | Selisih poin persentase |
|---|---:|---:|---:|
| Isu utama | 0,494619 | 0,495259 | +0,06 |
| Domain sumber metafora | 0,420814 | 0,390541 | −3,03 |
| Sasaran kritik | 0,385696 | 0,388486 | +0,28 |

Micro-F1/accuracy kontrol1× adalah0,527027/0,452703/0,502703; arm2× adalah
0,531081/0,424324/0,518919. Prediksi benar berturut-turut390/335/372 menjadi
393/314/384 dari740.

**Kesimpulan:** duplikasi persis2× memberi hasil campuran. Minimum Macro-F1
naik tipis0,385696→0,388486 (+0,28poin), tetapi rerata turun0,433709→0,424762
dan Task2 turun3,03poin. Ini tidak membuktikan peningkatan konsisten dan belum
menyelesaikan target Macro-F1≥0,70; semua task masih di bawah target. Tidak
disimpulkan signifikan secara statistik dan tidak dipromosikan ke web.

Verifier memeriksa split/multiplicity, label/probabilitas, hitung ulang metrics,
pemilihan epoch, inisialisasi dan hash. Audit stdlib Counter independen cocok
untuk precision/recall/F1 serta metrik per fold; delapan tes CPU lulus ulang.
Evaluasi canonical CPU FP32 memakai checkpoint reload di Kaggle, bukan replay
checkpoint besar lokal. Durasi worker317,567detik; antrean tidak termasuk.

Artefak: `08_ci_d01_duplicate2x/CI_D01_REPORT.md`, `full/verification.json`,
`full/raw/ci_d01_dup2/{result.json,oof_1x.csv,oof_2x.csv,fold1.json…fold5.json}`.
Source/protokol dan hasil historis tidak ditimpa. Result SHA256:
`a010cbb0625da82d9df0379aa35bedee271d4b3771a180f921009e4e9c1f189a`.

## Tujuan dan interpretasi permintaan

Eksperimen ini memakai **CLIP–IndoBERT**, bukan Qwen. Permintaan menggandakan
dataset diterapkan sebagai **salinan persis 2× hanya pada training**, setelah
split berdasarkan ID asli. Tidak membuat label, sampel independen atau gambar
baru. Dataset tetap740 sampel unik. Ini bukan augmentasi dan bukan oversampling
khusus kelas minoritas.

Salinan identik tidak menambah informasi. Dengan epoch sama, ia menambah
paparan/update optimizer sehingga hasil bisa membaik, tetap, atau memburuk.
Tidak ada janji mencapai Macro-F1≥0,70. Target penelitian tetap Macro-F1
ketiga task, bukan menggantinya dengan accuracy/Micro-F1.

## Arsitektur dan input

- CLIP ViT-L/14 beku, full image + crop historis E36.
- IndoBERT: frozen embedding/sepuluh blok awal, dua blok terakhir trainable.
- Representasi visual dan teks digabungkan ke shared layer256, dropout0,3,
  tiga head untuk isu utama, domain sumber metafora, dan sasaran kritik.
- Input teks hanya `headline_verified [SEP] supporting_text_verified`, max128.
  Tidak menggunakan Qwen, deskripsi Qwen, label sebagai fitur, atau model E14.
- Cache E41 telah diaudit sebagai ekstraksi tanpa label. Worker memeriksa
  checksum cache dan merekonstruksi fitur teks enam sampel sebelum training.
- Source model `tail_model.py` disalin byte-identik dari implementasi E42;
  worker/sampler/protokol eksperimen baru terpisah dari seluruh hasil lama.

## Rancangan perbandingan

| Bagian | Kontrol1× | Training2× |
|---|---:|---:|
| Sampel unik dataset | 740 | 740 |
| Outer-training unik/fold | 592 | 592 |
| Paparan joint-training/epoch | 592 | 1.184 |
| Outer-test unik/fold | 148 | 148 |
| Inner-training unik/split | 296 | 296 |
| Paparan inner-training/epoch | 296 | 592 |
| Inner-validation unik/split | 296 | 296 |

Fold luar sama persis dengan E42, lima fold. Dua inner fold stratifikasi Task2,
seed123. Tidak pernah membagi data setelah duplikasi, dan salinan ID latih
tidak boleh ada pada validation/test.

Warmup head120 full-batch steps memakai **ID training unik** dan dipakai bersama
untuk menginisialisasi kedua arm secara identik. Intervensi duplikasi hanya
pada fase minibatch joint fine-tuning dua blok IndoBERT/shared/heads. Class
weight dihitung dari training unik saja; validation/test tidak dipakai.

Resep tetap: encoder LR2e-5, head LR3e-4, AdamW weight decay0,01, batch32,
loss weights Task1/2/3 =1:2:2, seed42. Ini kontrol berpasangan baru dengan satu
resep tetap, **bukan** mengulang seluruh grid enam konfigurasi E42.

Kandidat epoch `[0,2,4,8,12,24]`; pilih per arm menggunakan maksimum minimum
antartask dari mean Macro-F1 dua inner fold, exact tie epoch paling awal.
Kemudian reset model/warmup/optimizer dan refit592 ID outer-training sesuai
epoch terpilih. Epoch0 berarti warm-head saja terpilih; kandidat lain tetap
dilatih pada inner, tetapi overfitting tidak dipaksakan menjadi hasil akhir.

Perbandingan ini **tidak menyamakan jumlah update optimizer**. Jumlah batch,
update berhasil/skipped, paparan dan durasi dicatat setiap epoch agar efek
duplikasi tidak disamarkan sebagai tambahan data independen.

## Evaluasi dan keluaran

- Inner selection menggunakan GPU AMP FP16, sama kerangka lama.
- **CPU FP32 dari checkpoint yang dimuat ulang** adalah evaluasi canonical
  outer-test, ditetapkan sebelum hasil. GPU AMP hanya diagnosis; selisih
  prediksi dicatat, tidak memilih presisi yang skornya lebih baik.
- Dua CSV OOF masing-masing740 ID unik: `oof_1x.csv`, `oof_2x.csv`.
- Macro-F1, Micro-F1, accuracy, macro precision/recall ketiga task, delta2×−1×
  dan ambang0,70 dari prediksi aktual. Tidak menggabungkan skor terbaik
  antarmodel/arm seolah satu model.
- `fold1.json`…`fold5.json`: split, jumlah salinan, inner trace, epoch terpilih,
  hash inisialisasi, history training, hash checkpoint dan diagnosis presisi.
- Checkpoint sepuluh model CV tersimpan pada output Kaggle, bukan otomatis
  checkpoint deployment seluruh740. Collector kecil tidak mengunduh semua
  checkpoint besar; verifikasi lokal menandai batas ini secara eksplisit.
- RAM/VRAM/utilisasi yang tidak diukur tidak diisi dengan angka dugaan.

## Source, job dan pengoperasian

Source:
`DEMO_XAI_745_FULL/01_notebook/next_research_20261017/kaggle_ci_d01_dup2/`.

Hasil:
`DEMO_XAI_745_FULL/04_hasil_eksperimen/next_research_20261017/08_ci_d01_duplicate2x/`.

Job privat Kaggle:

- [Smoke GPU](https://www.kaggle.com/code/research-account/tempo-ci-d01-clip-indobert-dup2-smoke).
- [Training lima fold](https://www.kaggle.com/code/research-account/tempo-ci-d01-clip-indobert-dup2-full), hanya dikirim setelah smoke VERIFIED.

Periksa `job_state.json` untuk status observasi terbaru; tautan saja tidak
membuktikan job full telah dikirim. Tidak ada scheduler latar belakang otomatis.
Wrapper mencatat submission intent sebelum push dan menolak repush ambigu.

```sh
python manage.py status smoke
python manage.py collect smoke
python manage.py submit full
python manage.py status full
python manage.py collect full
```

Jalankan dari folder source dengan environment analisis/Kaggle project.
Full submit mempunyai gate smoke; jangan menghapus ledger untuk melewatinya.
Kaggle memakai dataset/cache yang sudah tersedia di akun, container pinned,
wheel Transformers5.17.0 offline, GPU T4. Tidak memakai GPU berbayar/menambah
dataset baru atau membeli kuota. Batas wall runtime7200detik; job yang terhenti
tidak boleh dianggap sebagai evaluasi lima fold lengkap.

## Batas kesimpulan

E42 historis memiliki Macro-F1 `0,525483 / 0,395560 / 0,403398`, tetapi kontrol
utama CI-D01 adalah **arm1× baru**, bukan angka E42 karena grid/resepnya berbeda.
Korpus sudah berulang dipakai untuk eksperimen, sehingga hasil CV internal
bukan bukti generalisasi eksternal atau signifikansi statistik.

Tidak mengubah model web, ZIP delivery, label atau hasil E14. Ini eksperimen
training baru sesuai permintaan; hasil baru tetap **Not Evaluated** sampai
training/pengumpulan/verifikasi selesai.

Rujukan prinsip split/leakage:
[scikit-learn common pitfalls](https://scikit-learn.org/stable/common_pitfalls.html).
Seed saja bukan jaminan identik lintas platform:
[PyTorch reproducibility](https://docs.pytorch.org/docs/stable/notes/randomness.html).
