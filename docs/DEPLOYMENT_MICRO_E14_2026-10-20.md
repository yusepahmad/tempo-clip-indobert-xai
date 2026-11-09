# Deployment MICRO-E14 joint QLoRA — 20 Oktober 2026

## Status dan batas klaim

Integrasi source web sudah tersedia dengan backend `micro-e14-qlora` dan versi
`micro-e14-qlora-v1`. **Belum aktif sebagai model prediksi di laptop.** Backend
default tetap `clip-indobert-mtl`; tidak ada fallback diam-diam atau penggantian
nama model lama. Laptop tidak memiliki CUDA GPU yang terdeteksi.

Refit deployment dikirim sekali ke Kaggle, version 1:
<https://www.kaggle.com/code/research-account/tempo-micro-e14-deployment-refit>.
Status terakhir dicatat dalam
`DEMO_XAI_745_FULL/04_hasil_eksperimen/next_research_20261017/07_micro_e14_deployment/job_state.json`.
Itu observasi job, **bukan bukti model sudah siap dipakai web**.

Checkpoint baru belum tersedia saat implementasi/pengujian CPU. Pengujian
runtime GPU/clean Windows dan hasil refit deployment adalah **Not Evaluated**.
Pilihan server GPU untuk melayani web masih perlu dikonfirmasi pengguna.

## Resep deployment, bukan eksperimen CV tambahan

- Qwen/Qwen3-VL-8B-Instruct, revision
  `0c351dd01ed87e9c1b53cbc748cba10e6187ff3b`.
- Satu adapter LoRA bersama untuk tiga pertanyaan klasifikasi; bukan CLIP–IndoBERT.
- NF4 double quantization, FP16 compute, trainable LoRA FP32; rank16, alpha32,
  dropout0,05, target q/k/v/o projections.
- Seluruh 740 sampel untuk training, tiga epoch. Pilihan epoch berasal dari
  median **hasil pilihan inner-validation** `[3,1,3,2,3]`, bukan pencarian pada
  skor test. Seed initial43/refit42001, optimizer/refit loop sama dengan E14 CV.
- Input gambar thumbnail384, verified headline/supporting, deskripsi/alasan
  visual E01 tanpa memasukkan label anotator. Label dipakai untuk loss training;
  saat inferensi tidak dikirim dalam prompt.
- Tidak mengubah worker/protokol CV terkunci. Builder deployment terpisah
  memvalidasi SHA sumber dan menurunkan worker baru dengan refit seluruh data.
- Checkpoint disimpan dalam format PEFT safetensors/config. Kaggle harus
  memuat ulang checkpoint dan membandingkan probabilitas sebelum/sesudah save
  (selisih maksimum ≤0,0001) sebelum menulis `status=complete`.
- Smoke satu sampel **in-sample**, hanya uji persistensi; tidak dihitung sebagai
  accuracy/Macro-F1 baru. Durasi/GPU peak dicatat jika job benar-benar selesai.

## Sebelum dan sesudah perubahan

| Bagian | Sebelum | Implementasi baru |
|---|---|---|
| Pilihan backend web | CLIP–IndoBERT/baseline saja | Tambahan MICRO-E14 eksplisit via environment |
| Prediksi E14 | Belum ada runtime | GPU inference langsung logits token kelas A–J, bukan CSV OOF |
| Checkpoint final | Lima adapter outer-fold, belum refit740 | Job refit740 terpisah; belum dianggap tersedia sebelum terkumpul/verified |
| Status UI | Kalimat CLIP hardcoded | Identitas sesuai backend, `ready=false` dibaca “diminta, belum aktif” |
| Ketika E14 tidak tersedia | Belum ada jalur | HTTP503 dengan alasan; tidak menjalankan model lama |
| XAI | CLIP gradient dan IndoBERT LIME/occlusion | Sengaja tidak dipakai untuk E14; panel mengaku belum tersedia |
| Unggahan baru | Pipeline CLIP–IndoBERT | E14 menolak hingga generator fitur E01 setara tersedia |

## Benchmark yang tetap berlaku

| Metrik historis | Task1 | Task2 | Task3 | Cakupan |
|---|---:|---:|---:|---|
| CLIP–IndoBERT Macro-F1 | 0,438032 | 0,319726 | 0,276352 | CV historis740 |
| MICRO-E14 Macro-F1 | 0,673321 | 0,510282 | 0,595480 | OOF740, lima fold |
| MICRO-E14 Micro-F1 | 0,720270 | 0,566216 | 0,667568 | OOF740, lima fold |
| Checkpoint deployment | Not Evaluated | Not Evaluated | Not Evaluated | Refit seluruh740, bukan OOF |

Sumber aktual: `hasil_mtl_740_task2domain.json` dan
`next_research_20261017/06_micro_f1/MICRO_E14_joint_qlora_oof/metrics.json`.
Target **Macro-F1 ≥0,70 ketiga task belum tercapai**. Skor softmax token kelas
bukan probabilitas benar terkalibrasi. Refit740 tidak menjanjikan peningkatan
angka historis. MICRO-E14 berbeda dari comparator historis juga bernama E14
(Qwen/E5/BGE/CLIP + SVC).

## Cakupan fungsional

- Dataset740: prediksi baru dari model GPU, bukan playback prediksi OOF. Karena
  semua740 masuk training, kecocokan label pada web adalah **in-sample**.
- Edit headline/supporting: konteks visual E01 tidak diregenerasi; pergeseran
  input ini ditandai belum dievaluasi.
- Unggahan/batch unggahan baru: **belum didukung E14**. Tidak mengisi deskripsi
  dengan string kosong karena itu bukan input setara benchmark. Baseline tetap
  mendukung unggahan, tetapi harus dijalankan secara eksplisit sebagai baseline.
- Batch dataset menggunakan core E14 yang sama, tanpa retrain/leave-one-out.
- XAI visual/kata E14 belum diimplementasikan; catatan label referensi hanya
  untuk pembandingan, tidak dipakai sebagai bukti alasan model.

## Kumpulkan checkpoint setelah selesai

Dari root workspace, gunakan Python environment yang memiliki Kaggle CLI dan
dependencies analisis project:

```sh
python DEMO_XAI_745_FULL/01_notebook/next_research_20261017/kaggle_micro_e14_deploy/manage.py status
python DEMO_XAI_745_FULL/01_notebook/next_research_20261017/kaggle_micro_e14_deploy/manage.py collect
```

Collector **tidak mengirim ulang job**. Hanya jika COMPLETE, unduh hasil, audit
dan adapter, verifikasi source/protokol/data/config/artefak serta 2.220 record
input identik dengan CV; baru install ke `06_models/micro-e14-qlora-v1/`.
Checkpoint berbeda yang sudah terpasang tidak ditimpa.

## Jalankan pada GPU

Jangan upgrade environment baseline yang sedang dipakai. Buat environment
terpisah; instal CUDA-enabled Torch yang sesuai platform, lalu dependencies
`DEMO_XAI_745_FULL/requirements-micro-e14.txt`. Keberhasilan pada clean Windows
belum diuji. Versi paket dipertahankan dari Kaggle E14, bukan klaim universal
kompatibilitas driver. Base weights Hugging Face perlu diunduh sekali; adapter
saja bukan paket model offline lengkap.

Linux, dari folder aplikasi:

```sh
bash jalankan_micro_e14_linux.sh
```

Windows: `jalankan_micro_e14_windows.bat` (default environment `venv-e14`).
Default port7861 agar tidak menggantikan baseline port7860 secara diam-diam.
Variabel `TEMPO_PYTHON`, `TEMPO_PORT`, `TEMPO_HOST` dapat disesuaikan.

Server E14 boleh membuka halaman dengan status belum aktif, tetapi tidak akan
melayani prediksi sebelum adapter/checksum, CUDA dan smoke GPU startup lulus.
Runtime membandingkan prediksi sampel pertama dengan hasil smoke checkpoint
Kaggle (maksimum selisih probabilitas0,001). Belum menyediakan endpoint publik
atau tunnel; pilihan mesin/akses perlu disepakati sebelum deployment eksternal.

## Verifikasi lokal

- Lima tes derivasi: 2.220 prompt SHA sesuai CV, refit loop identik AST, resep
  epoch, missing checkpoint tidak ready, unggahan/cache/fallback tidak dipakai.
- Empat tes web: metadata/HTTP503, penolakan unggahan, kontrak prediksi fixture
  tanpa XAI baseline, Chromium status ready/not-ready dan render hasil.
- Tes tersebut **CPU/fixture**, bukan bukti berhasil memuat GPU E14.
- Regresi baseline/UI dan protokol CV diperiksa terpisah; hasil terperinci
  dicatat dalam plan. Delivery ZIP lama tetap snapshot lama, tidak ditimpa.

Rujukan API implementasi:
[PEFT save/load adapter](https://huggingface.co/docs/peft/en/package_reference/peft_model),
[Transformers multimodal chat templates](https://huggingface.co/docs/transformers/chat_templating_multimodal).
