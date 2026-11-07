# Demo Tempo MICRO-E14 pada Google Colab GPU

Training/refit tetap di Kaggle. Colab hanya untuk demo inferensi sementara.
Backend tetap bernama `micro-e14-qlora`, bukan CLIP–IndoBERT yang diganti label.

## Status

Lihat `PACKAGE_STATE.json` dalam ZIP dan `VALIDATION_REPORT.json` di folder
build. Jika `checkpoint_verified=false`, paket adalah **PREPARATION ONLY**:
notebook berhenti sebelum instalasi/model. Jangan menganggap web E14 sudah
berjalan. Job refit:
<https://www.kaggle.com/code/yusepmuhamadzazuli/tempo-micro-e14-deployment-refit>.

Jika checkpoint sudah terkumpul/verified, paket berisi adapter PEFT, bukan base
weights Qwen8B. Base weights diunduh dari Hugging Face saat startup pertama.
GPU Colab benar-benar diuji hanya jika hasil smoke/runtime tersimpan; validasi
lokal paket tidak membuktikan inferensi Colab berhasil.

## Cara pakai

1. Buka `TEMPO_MICRO_E14_COLAB_DEMO.ipynb` melalui **File → Upload notebook**
   di Google Colab.
2. Pada sel upload, pilih ZIP runtime dari build yang sama. Notebook berisi
   SHA256 yang tepat; ZIP delivery lengkap3GB bukan file yang dimaksud.
3. Jalankan gate checkpoint. Jika masih PREPARATION, berhenti dan tunggu paket
   baru setelah collector Kaggle berhasil; tidak perlu menghabiskan GPU.
4. Setelah checkpoint tersedia, pilih **Runtime → Change runtime type → GPU**.
   GPU sekitar16GB VRAM atau lebih disarankan; pemeriksaan awal menolak GPU
   di bawah14.000MiB. Driver/memori Colab bervariasi, ini bukan jaminan muat.
5. Sel instalasi membuat environment terpisah dan Torch2.11.0 CUDA12.8 dari
   index resmi PyTorch. Kernel/Torch bawaan Colab tidak di-upgrade. Paket ML
   mengikuti versi Kaggle E14. Bila `venv`/driver/paket gagal, berhenti dan
   simpan log; tidak menurunkan versi/protokol secara diam-diam.
6. Sel start memuat model GPU dan menguji smoke terhadap probabilitas checkpoint
   Kaggle. Hanya `ready=true` yang boleh menghasilkan prediksi.
7. Pilih `SAMPLE_ID` dari dataset, jalankan sel prediksi, lihat gambar dan tabel
   tiga task terurut. Worker tetap hidup sehingga model tidak dimuat ulang
   setiap sampel. Hasil numerik aktual disimpan ke `latest_prediction.json`.
8. Jalankan **Stop** dan disconnect/delete runtime bila selesai. Notebook tidak
   menjaga sesi tetap hidup secara artifisial dan tidak membatalkan job Kaggle.

Tidak perlu token Kaggle/Hugging Face untuk memakai paket lokal dan model
publik. Jangan menempelkan credential ke sel. Notebook tidak memasang Drive
secara otomatis dan tidak menyalin file akun lain.

## Opsi web terbaru

Mode utama adalah inferensi lewat sel notebook. Menurut
[FAQ Colab](https://research.google.com/colaboratory/faq.html), penggunaan yang
terutama melewati web UI dapat dibatasi pada runtime gratis/tanpa saldo compute
unit. Jangan memakai tunnel untuk menghindarinya. Opsi web hanya diaktifkan
setelah pengguna memeriksa bahwa akun memiliki compute unit positif dan
ketentuan mengizinkan penggunaan tersebut; tidak ada pembelian otomatis.

Sel web menghentikan worker native dahulu, memuat satu model yang sama, lalu
memeriksa `/api/models` sebelum menampilkan iframe dengan
`google.colab.output.serve_kernel_port_as_iframe`. Menggunakan proxy resmi
Colab, bukan ngrok/cloudflared/link publik. Jangan menyebarkan sesi runtime
sebagai hosting produksi. Iframe dapat bergantung pada izin browser; jika
tidak berfungsi, gunakan mode notebook, bukan bypass keamanan browser.

## Batas fungsi dan hasil

- Dataset740 ikut refit model: hasil demo **in-sample**, bukan OOF/benchmark baru.
- Unggahan baru belum tersedia karena konteks deskripsi/alasan visual E01
  belum dapat dibuat dengan pipeline setara. XAI gambar/kata E14 belum tersedia.
- Tidak mengklaim peta CLIP/atribusi IndoBERT sebagai XAI Qwen.
- Skor token kelas belum dikalibrasi. Bukan probabilitas jawaban benar.
- Macro-F1 historis E14 Task1/2/3: 0,673321/0,510282/0,595480, dari
  `historical_metrics.json`. Target0,70 ketiga task **belum tercapai**.
- Waktu/VRAM runtime Colab, prediksi GPU, atau acceptance yang belum dijalankan
  tetap **Not Evaluated**. Jangan mengisi dengan estimasi sebagai benchmark.
- Paket baru ini tidak menggantikan arsip riset/presentasi lengkap3GB; notebook
  dan hasil historis tetap ada pada delivery sebelumnya.

## Untuk pembangun paket

Dari workspace, setelah training selesai:

```sh
python DEMO_XAI_745_FULL/01_notebook/next_research_20261017/kaggle_micro_e14_deploy/manage.py collect
python scripts/build_colab_micro_e14.py --require-checkpoint
```

Jalankan dengan environment lokal yang memiliki dependencies analisis dan
nbformat. Tanpa `--require-checkpoint`, builder boleh menghasilkan paket
persiapan tetapi memberi nama PREPARATION dan menutup gate model. Setiap build
masuk folder baru; ZIP historis tidak ditimpa. Builder menyalin allowlist file
web,740 gambar,dataset,kontrak/helper; tidak menyertakan venv,token,cache job,
unggahan pengguna,atau seluruh history riset.

Rujukan teknis:
[Colab iframe API](https://github.com/googlecolab/colabtools/blob/main/google/colab/output/_util.py),
[PyTorch](https://pytorch.org/get-started/locally/),
[PEFT adapter](https://huggingface.co/docs/peft/en/package_reference/peft_model).
