# Deployment MICRO-E14 untuk Web

**Tanggal:** 2026-10-20
**Status:** in-progress

## Tujuan
Menyiapkan checkpoint deployment dan jalur prediksi web MICRO-E14 yang benar-benar menjalankan Qwen3-VL joint QLoRA, tanpa mengganti nama backend CLIP–IndoBERT secara kosmetik.

## Ruang Lingkup
- Backend dan status web di `DEMO_XAI_745_FULL/02_web_demo/`, pengujian, launcher dan dokumentasi deployment baru.
- Skrip deployment baru di `01_notebook/next_research_20261017/`, artefak dan audit deployment di `06_models/`/`04_hasil_eksperimen/`.
- Kaggle untuk refit deployment bila diperlukan; protokol evaluasi MICRO-E14 dan hasil OOF historis tidak diubah.
- Tidak menghapus delivery terdahulu, tidak mengklaim hasil refit sebagai benchmark baru, tidak menyamarkan cached prediction sebagai inferensi.

## Langkah
1. Audit checkpoint yang tersedia, kontrak API/XAI web, praproses, dan kemampuan perangkat.
2. Tentukan resep deployment dari hasil inner-validation yang sudah tersedia, dokumentasikan batasan dan status aktual.
3. Siapkan refit Kaggle dan backend inferensi dengan validasi identitas/checksum; gunakan input non-label yang sama dan bedakan ketersediaan fitur pada unggahan baru.
4. Integrasikan pemilihan backend, metadata kemampuan dan kegagalan eksplisit; jangan gunakan XAI model lama untuk mengklaim penjelasan model baru.
5. Jalankan pengujian CPU/kontrak, uji GPU jika tersedia, catat status pekerjaan remote dan batasan aktual.
6. Catat perubahan selesai di changelog dan laporkan apa yang sudah aktif versus masih menunggu GPU/checkpoint.

## Risiko & Asumsi
- Laptop tidak memiliki `nvidia-smi`; inferensi NF4 8B membutuhkan GPU kompatibel, bukan drop-in pengganti runtime CPU lama.
- Belum ada adapter refit seluruh 740 data. Adapter lima fold tidak boleh dipromosikan seolah model final seluruh data.
- Deskripsi visual dan observasi tambahan merupakan bagian input E14; unggahan baru tanpa fitur tersebut adalah pergeseran distribusi yang harus ditampilkan.
- Kaggle dapat mengantre atau autentikasi/kuota gagal; tidak menjanjikan aktivasi sebelum checkpoint dan GPU terverifikasi.
- Output skor belum dikalibrasi. Target Macro-F1 0,70 dan OCR 80% belum tercapai.

## Verifikasi
- Kesetaraan prompt/preprocessing dengan worker terkunci, unit test tanpa GPU, regresi web baseline.
- Hash adapter/protokol dan audit training final; smoke GPU jika pekerjaan Kaggle selesai.
- Status `/api/models` dan prediksi konsisten backend aktual; mode E14 tidak pernah fallback diam-diam ke CLIP atau hasil OOF.

## Hasil implementasi sementara
- Backend `micro_e14_engine.py` dan cabang `app.py` ditambahkan; UI status dinamis, HTTP503 eksplisit, dan panel XAI tidak memakai model lama. Default baseline/layanan7860 tidak diganti.
- Builder deployment terpisah menghasilkan worker refit740/tiga epoch (median pilihan inner `[3,1,3,2,3]`), kontrak, cache visual tanpa label, launcher Kaggle dan hash build. Worker/protokol CV terkunci tetap identik.
- Kaggle `research-account/tempo-micro-e14-deployment-refit` version1 dikirim sekali, terkonfirmasi RUNNING. Status observasi tersimpan pada `07_micro_e14_deployment/job_state.json`.
- Collector `manage.py collect` disiapkan untuk memverifikasi hasil, audit2220 input dan hash/config adapter sebelum install; belum dijalankan sampai job selesai.
- Lima tes derivasi/backend CPU, empat tes API/Chromium E14, enam skrip Node regresi, dua Chromium sorting, empat HTML5, dua tes MTL baseline dan lima tes protokol CV lulus. Tes fixture bukan benchmark GPU.
- Launcher Linux/Windows dan requirements GPU terpisah tersedia. Dokumentasi: `docs/DEPLOYMENT_MICRO_E14_2026-10-20.md`.

## Sisa pekerjaan / keputusan diperlukan
- Tunggu job selesai, koleksi dan verifikasi checkpoint; smoke GPU runtime belum dapat dijalankan di laptop tanpa CUDA.
- Pengguna memilih **Google Colab GPU untuk demo sementara**. Implementasi launcher/paket mengikuti `2026-10-20-colab-micro-e14-demo.md`; tidak deploy ke server10.12.1.31 atau membuka tunnel publik.
- E14 untuk unggahan baru dan XAI visual/kata belum tersedia; tidak mengklaim fitur lama otomatis kompatibel. Edit teks dataset ditandai memakai konteks visual historis, belum dievaluasi.
- ZIP delivery terdahulu tidak ditimpa; pembaruan delivery final menunggu checkpoint dan runtime terverifikasi.
- Status plan tetap **in-progress**, bukan selesai/tujuan akhir tercapai.
