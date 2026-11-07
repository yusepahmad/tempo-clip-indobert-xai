# Training CLIP–IndoBERT dengan data latih digandakan 2× di Kaggle

**Tanggal:** 2026-10-20
**Status:** done

## Tujuan
Menguji permintaan pengguna menggandakan dataset yang ada untuk training CLIP–IndoBERT, tanpa mengganti arsitektur ke Qwen dan tanpa membuat data test bocor. Membedakan hasil nyata dari dugaan kenaikan skor.

## Ruang Lingkup
- Eksperimen baru terpisah: CLIP-L14 beku + dua tail blok IndoBERT trainable + shared head tiga task, memakai cache E41 yang sudah diaudit.
- Source/protokol/tes/launcher/collector Kaggle baru di `01_notebook/next_research_20261017/` dan hasil pada folder eksperimen baru.
- Dokumen eksperimen dan `CHANGELOG.md`.
- Tidak mengubah 740 data asli, label, pemetaan fold, worker historis E41/E42, model web, checkpoint Qwen, atau delivery sebelumnya.

## Langkah
1. Audit cache, model, container/dependencies dan sumber data Kaggle yang tersedia.
2. Tetapkan duplikasi persis 2× hanya pada training setelah split berdasarkan ID asli; validation/test tidak digandakan.
3. Siapkan kontrol 1× dengan arsitektur/resep/seed/split yang sama. Pemilihan epoch hanya inner-validation, target utama Macro-F1 ketiga task, bukan confidence web.
4. Buat tes kebocoran, multiplicity, update gradien tiga task, serialisasi/checkpoint dan penghitungan metrik. Tetapkan presisi evaluasi sebelum hasil.
5. Jalankan smoke Kaggle; setelah lulus, kirim training lima fold sesuai kuota. Catat handle/status agar tidak mengirim ulang job ambigu.
6. Siapkan collector/verifier hasil dan laporan aktual; jangan menganggap training selesai hanya karena job terkirim.

## Risiko & Asumsi
- “Menggandakan” ditafsirkan sebagai salinan persis 2×, bukan tambahan sampel unik atau augmentasi label-preserving. Dataset tetap 740 ID unik.
- Pada outer-training 592 ID, 2× berarti 1.184 paparan per epoch. Test tetap 148 ID per fold; tidak pernah split setelah duplikasi.
- Duplikasi identik tidak menambah informasi dan dapat meningkatkan overfitting. Dengan epoch sama, jumlah update optimizer meningkat; kontrol dan jumlah update harus dilaporkan, bukan mengatribusikan semua kenaikan pada informasi baru.
- Korpus telah berulang dipakai. Hasil internal CV tidak dapat diklaim validasi eksternal independen atau jaminan mencapai Macro-F1≥0,70.
- Training GPU memerlukan kuota dan kompatibilitas container; tidak memakai layanan berbayar atau mengubah akun secara otomatis.
- Pengulangan seimbang tidak mengubah komposisi kelas; bukan oversampling khusus kelas minoritas.

## Verifikasi
- SHA dataset/cache/source dan split sesuai sumber asli; disjoint ID training/validation/test dan tepat dua salinan tiap ID latih.
- Kontrol/2× mulai dari checkpoint awal dan warm-head identik, menggunakan class weight dari ID unik training saja.
- Canonical evaluasi checkpoint CPU FP32 pada 740 OOF, GPU AMP hanya diagnosis; Macro-F1/Micro-F1/accuracy dihitung dari prediksi aktual.
- Source yang dikirim cocok manifest; smoke membuktikan tail/shared layer/ketiga head berubah. Hasil belum tersedia ditandai Not Evaluated.

## Hasil implementasi dan verifikasi — 20 Oktober 2026
- Source baru: `01_notebook/next_research_20261017/kaggle_ci_d01_dup2/` (`worker.py`, model historis byte-identik, helper split, builder, dua launcher, tes dan collector/ledger).
- Protokol beku SHA256 `404d4b233569250b8a1f9be1538615b863a12c39a58e4622787efee6d37eaf03`; worker `6fe0481282ee4d1ca71b0adee6f8b87a0f46acdacf8bfe3d6555946eac439ad0`.
- Delapan tes lokal lulus: semua nested split/multiplicity, penolakan kebocoran, seleksi Macro-F1/tie, payload/hash, warm-head heldout invariance, gradien model nyata, presisi canonical, dan penolakan smoke evidence yang dimanipulasi.
- Kaggle smoke version1 COMPLETE dan VERIFIED: Torch2.11.0+cu128, Transformers5.17.0, TeslaT4. Arm1× mengonsumsi40 sampel/2update, arm2×80paparan/3update; tidak ada skipped update. Dua tail, shared layer dan semuahead berubah; save/reload CPU FP32 identik.
- Smoke adalah uji teknis, **bukan benchmark kualitas**. Output: `08_ci_d01_duplicate2x/smoke/`.
- Job full `yusepmuhamadzazuli/tempo-ci-d01-clip-indobert-dup2-full` version1 dikirim sekali pada20Okt17.30WIB; status pertama QUEUED. Observasi terkini ada di `08_ci_d01_duplicate2x/job_state.json`.
- Collector full memeriksa kedua740OOF, label/probabilitas/metrik, sepuluh inner-split/arm, epoch/jumlahpaparan/update dan hash; laporan aktual dihasilkan hanya setelah koleksi/verifikasi berhasil. Tidak ada watcher latar belakang otomatis.
- Dokumentasi: `docs/EKSPERIMEN_CLIP_INDOBERT_DUPLIKASI_2X_2026-10-20.md`.

## Hasil final — 20 Oktober 2026, verifikasi pukul18.13WIB
- Job full version1 **COMPLETE**, kedua arm **VERIFIED**. Metadata lima fold, dua CSV740OOF, result/runtime dan log Kaggle telah dikoleksi; tidak mengirim ulang training.
- Macro-F1 kontrol1×: `0,494618894 / 0,420813574 / 0,385695629`.
- Macro-F1 duplikasi2×: `0,495259402 / 0,390541143 / 0,388486439`.
- Delta Macro-F1 Task1/2/3: **+0,06 / −3,03 / +0,28 poin persentase**.
- Micro-F1/accuracy kontrol1×: `0,527027027 / 0,452702703 / 0,502702703`; duplikasi2×: `0,531081081 / 0,424324324 / 0,518918919`.
- Minimum Macro-F1 naik tipis0,385696→0,388486, tetapi rerata turun0,433709→0,424762. Tidak ada task mencapai Macro-F1≥0,70; tidak mempromosikan duplikasi sebagai solusi utama atau model web baru.
- Delapan tes lokal lulus ulang. Verifier memeriksa ID/split/multiplicity, label, probabilitas, metrics, epoch/update, inisialisasi berpasangan dan hash. Audit tambahan independen memakai stdlib Counter juga cocok untuk precision/recall/F1 seluruh740 dan Macro-F1 per fold.
- Hasil CPU FP32 canonical dari reload checkpoint dijalankan worker Kaggle. Checkpoint besar hanya hash tercatat remote, belum diunduh/replay lokal; audit trace inner bersifat struktural, bukan reproduksi seluruh training.
- Laporan aktual: `08_ci_d01_duplicate2x/CI_D01_REPORT.md`; verifikasi: `full/verification.json`; data mentah: `full/raw/ci_d01_dup2/`.
- Result SHA256 `a010cbb0625da82d9df0379aa35bedee271d4b3771a180f921009e4e9c1f189a`; keduaCSV SHA terverifikasi. Durasi worker317,567detik (sekitar5menit18detik), tidak termasuk antrean; tidak mengarang telemetri RAM/VRAM.
- Plan selesai untuk training/perbandingan ini, **bukan** target kualitas penelitian tercapai. Dataset, label, web, checkpoint E14 dan ZIP terdahulu tetap tidak berubah.
