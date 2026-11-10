# Changelog

Semua perubahan penting pada project ini dicatat di file ini.
Format mengikuti [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

### Removed

- Nama pribadi, username akun eksternal, alamat home personal asli, URL akun pribadi, dan metadata author lama dikeluarkan dari seluruh artefak client. Riwayat Git diganti dengan snapshot bersih ber-author netral; nilai penelitian tidak diubah (plan: [sanitasi identitas delivery](docs/plans/2026-11-10-sanitasi-identitas-delivery.md)).

### Fixed

- URL kompatibilitas paket R3 kini membuka indeks bukti R4 sehingga R18–R36 dapat diakses. Web demo memakai checkpoint E42 asli sebagai backend default; lima fold, cache, manifest, dan tes replay 740 sampel disertakan dalam clone (plan: [sanitasi identitas delivery](docs/plans/2026-11-10-sanitasi-identitas-delivery.md)).

- Perbaikan indeks revisi dan aset E42 dipublikasikan pada commit `7f08c605f6e6116f6db6477283d3e29962941523`; remote memuat lima checkpoint dan cache E42 yang diverifikasi (plan: [sanitasi identitas delivery](docs/plans/2026-11-10-sanitasi-identitas-delivery.md)).

- Delivery `delivery/HASIL_REVISI_JOY_20261102_R3_FULL/` melengkapi output
  tiga notebook: confusion matrix baseline yang terlewat, pembanding E14,
  seluruh gambar XAI, tabel distribusi/weighting/statistik dan lampiran
  canonical. `build_notebooks.py`, `notebook_evidence.py`,
  `build_full_delivery.py`, `check_full_omissions.py` dan
  `verify_full_archive.py` menyediakan generator, audit cakupan,
  uji kelalaian dan pemeriksaan arsip. Seluruh 141 berkas bukti dan
  21 lampiran ditampilkan; 46 CSV tanpa pemotongan baris, empat matrix Task 3,
  28 bagian revisi dan 1.008 tautan HTML diperiksa. Run all tiga notebook,
  10 tes evaluator dan tiga uji penghilangan/pemotongan bukti lulus lokal;
  499 file data/prediksi/analisis/model/instrumen/protokol/XAI identik R2.
  Ekstraksi ZIP lengkap lulus Run all ulang tiga notebook, 1.808 hash dan
  231 baris metrik. ZIP bukti mandiri lulus 474 hash dan 733 tautan HTML.
  Sembilan revisi terbuka tetap terbuka; paket R2 dipertahankan (plan:
  [notebook full dan audit bukti](docs/plans/2026-11-02-notebook-full-audit-bukti.md)).

### Changed

- R22, R23/R6, dan R31 ditutup berdasarkan hasil manusia tervalidasi dan keputusan konservatif: R22 dibatasi sebagai verifikasi prospektif, disagreement R23/R6 mempertahankan label kanonik, dan 41 usulan R31 disimpan sebagai sensitivitas tanpa mengubah gold/codebook atau menjalankan ulang eksperimen. Tracker/status kini menyisakan R8, R32, dan R34/R9; hasil dipublikasikan pada commit `25ece2d838e9babd1c50b176a48cafa4457766f5` (plan: [penutupan R22, R23/R6, dan R31](docs/plans/2026-11-10-penutupan-r22-r23-r6-r31.md)).

- Integrasi hasil manusia dan audit independensi R34/R9 dipublikasikan fast-forward ke `main` pada commit `8117a10dccd645151e76d571809f4097b6496daa` (plan: [push integrasi hasil manusia](docs/plans/2026-11-10-push-integrasi-hasil-manusia.md)).

- Addendum R21 literal dan status sisa teknis dipublikasikan fast-forward ke `main` pada commit `bc727eabd38bd167b12941816f43feb025b7bc5b` (plan: [push sisa teknis R21](docs/plans/2026-11-10-push-sisa-teknis-r21.md)).

- Status server `.31` diberi addendum R21 10 November; delapan ZIP manusia lulus CRC/checksum, paket R32 449.939.083 byte lulus CRC dan notebook lulus schema/compile, sementara R4 tetap immutable dan validatornya lulus 2.431 hash/234 metrik/28 revisi. Status manusia dan Colab asli tetap `Not Evaluated` (plan: [tuntaskan sisa teknis revisi](docs/plans/2026-11-10-tuntaskan-sisa-teknis-revisi.md)).

- Dokumentasi perbedaan E42 dan bukti model dipublikasikan fast-forward ke branch `main` repository `project-owner/tempo-clip-indobert-xai` pada commit `2caee2788fb68a887fda98673fae63737ec444d1` (plan: [push dokumentasi E42](docs/plans/2026-11-10-push-dokumentasi-e42-github.md)).

- Dokumen R18 `docs/revisi-ii/R18_ARSITEKTUR_JOINT_LOSS.md` kini menautkan tabel perbedaan eksperimen, addendum daftar R, dan screenshot bukti per komponen (plan: [perbedaan E42 dan bukti model](docs/plans/2026-11-10-perbedaan-e42-dan-bukti-model.md)).

### Added

- Integrasi hasil manusia di `delivery/ADDENDUM_HASIL_MANUSIA_20261110/`: R22 review 20/20, R23 dua anotator × 150 dengan Cohen’s κ 0,5721/0,9498/0,9430, dan R31 audit 60/60 tervalidasi. Script `tools/integrate_human_results.py`, disagreement table, ringkasan adjudikasi, tracker addendum, provenance, dan manifest ditambahkan. R34/R9 tetap terbuka karena lima file memiliki skor dan alasan identik pada seluruh 48 baris; ICC tidak dilaporkan (plan: [integrasi hasil isian manusia](docs/plans/2026-11-10-integrasi-hasil-isian-manusia.md)).

- Addendum R21 literal `delivery/ADDENDUM_R21_LITERAL_20261110/` mengoleksi hasil Kaggle Qwen QLoRA citra+judul setelah job versi 2 diamati live `COMPLETE`: 740 ID unik/lima fold tervalidasi, prediksi/probabilitas/audit prompt/protokol lulus collector, dan metrik Macro-F1 Task 1/2/3 sebesar 0,5486/0,4779/0,5029 disertai CI bootstrap. `docs/revisi-ii/STATUS_SISA_TEKNIS_20261110.md` memisahkan pekerjaan agent yang selesai dari bukti manusia yang tetap menunggu (plan: [tuntaskan sisa teknis revisi](docs/plans/2026-11-10-tuntaskan-sisa-teknis-revisi.md)).

- Addendum daftar R untuk R18/R27/R29/R30/R34, tabel audit perbedaan E36–E49 terhadap E42, dan tiga screenshot bukti aktual CLIP, IndoBERT, serta XAI ditambahkan di `docs/revisi-ii/`. Dokumentasi menegaskan epoch checkpoint E42 per fold, membedakan E48 sebagai diagnostik single-task `LinearSVC`, dan membatasi XAI sebagai attention rollout class-agnostic + LIME kondisional, bukan Grad-CAM. Paket R4 asli tidak diubah agar manifest integritas tetap valid (plan: [perbedaan E42 dan bukti model](docs/plans/2026-11-10-perbedaan-e42-dan-bukti-model.md)).

- Artefak terbaru dari server `.31` ditarik sebagai file baru dan diverifikasi: arsip analisis R4 `delivery/R4_SERVER31_ANALISIS/HASIL_REVISI_JOY_20261108_R4_ANALISIS.zip` beserta ekstraksi `delivery/HASIL_REVISI_JOY_20261108_R4_ANALISIS/`, termasuk hasil Kaggle R21 supporting-740, provenance, tabel, dan paket bukti 19/28 selesai teknis.
- Checkpoint web rich256 hasil Kaggle `delivery/RICH256_KAGGLE_20261108/TEMPO_WEB_RICH256_MODEL_20261108.zip` serta paket reproduksi Colab R32 `delivery/R32_COLAB_20261108/R32_ANALISIS_PORTABEL.zip` dan metadata status/panduan ditambahkan; seluruh checksum dan struktur ZIP lulus verifikasi. Status revisi terbaru dari server disalin ke `docs/server31/` (plan: [audit GitHub, Kaggle, dan server .31](docs/plans/2026-11-09-audit-github-kaggle-server31.md)).

- Tindak lanjut sembilan revisi pada `delivery/TINDAK_LANJUT_REVISI_20261102/`:
  tabel R21 2×2/zero-shot dan CI kappa bootstrap (15 baris tersedia, 3 menunggu),
  ekspor R22 740 input tanpa label/742 hash beserta probe pembatas baca,
  ZIP analisis portabel dan peluncur Colab R32, delapan ZIP instrumen manusia
  yang tetap kosong, serta matriks estimasi dan tanggung jawab. Run all dari
  ekstraksi pada venv baru lulus tiga notebook/1.791 hash/231 metrik; enam tes
  tambahan dan lima tes agreement lulus. `human_agreement.py` mendukung
  validasi kunci item/rater/dimensi dan skor Likert utuh terhadap template.
  Full QLoRA basic privat v1 sudah RUNNING setelah smoke/source/kuota diverifikasi
  (sisa 28,18 jam-GPU, batas 9 jam wall); collector baru memeriksa ID/truth/fold,
  split, probabilitas dan input audit sebelum publikasi, dengan pemantau tanpa
  resubmit. Hasil 740 belum diklaim tersedia dan status tetap 19 selesai/9 terbuka;
  tidak ada rating manusia, timestamp historis atau kelulusan Colab buatan
  (plan: [tuntaskan revisi terbuka](docs/plans/2026-11-02-tuntaskan-revisi-terbuka.md)).

- Folder `BUKTI_PER_REVISI/` pada delivery R2 menyediakan 19 folder bernama
  langsung R18, R19, dst untuk butir selesai teknis, dengan 139 berkas bukti,
  README/HTML per R, manifest source/hash dan indeks 28 butir. Tabel pemetaan
  R18 dan peringkat R19 masing-masing 36 baris; empat prediksi utama R28
  masing-masing 740 ID; 15 tabel subset dan 226 tautan lokal diperiksa.
  ZIP bukti ringan dapat dibaca terpisah karena menyertakan PDF sumber dan
  HTML notebook. Sembilan butir terbuka tetap tercatat; R30 menjelaskan
  back-translation tidak digunakan. Script `build_revision_evidence.py`,
  ZIP bukti dan delivery lengkap R2 ditambahkan tanpa mengubah data, metrik,
  notebook atau model R1 (plan:
  [folder bukti per revisi](docs/plans/2026-11-02-folder-bukti-per-revisi.md)).

- Delivery satu folder `delivery/HASIL_REVISI_JOY_20261102/`: tiga notebook
  memuat jawaban R18 secara langsung, arsitektur MTL CLIP–IndoBERT, rumus Joint
  Loss dan konfigurasi lima fold yang dicocokkan dengan source/protocol/hash
  checkpoint. Tiga screenshot delivery 20 Oktober dan halaman 5 PDF sumber
  disertakan sebagai attachment notebook dengan provenance; dua screenshot
  browser aktual R18/Joint Loss tersedia pada folder `screenshots/`. Paket
  menyatukan hasil analisis 77 sumber, kontrol zero-shot Qwen basic/rich 740 sampel yang sudah
  diverifikasi, delapan ZIP instrumen manusia dan lampiran checkpoint E42.
  Normalisasi zero-shot hanya menambahkan kelompok evaluasi canonical tanpa
  mengklaim training OOF; tes regresi menolak fold/truth salah. Sembilan belas
  tes dan Run all tiga notebook pada ekstraksi ZIP/venv terpisah lulus
  (231 baris metrik/77 sumber dan 1.296 hash kandidat); bagian manusia/QLoRA basic full/Colab
  tetap terbuka (plan: [revisi langsung notebook dan screenshot](docs/plans/2026-11-02-revisi-langsung-notebook-dan-screenshot.md)).

- Implementasi evaluasi Revisi II di `DEMO_XAI_745_FULL/01_notebook/revisi_ii/`
  dan hasil baru `04_hasil_eksperimen/revisi_ii/`: Macro-F1 utama, akurasi/kappa,
  CI Wilson/bootstrap 2.000 replikasi, exact McNemar/Holm, peringkat 36 nama,
  deduplikasi signature dan diagnosis kelas. Penetapan E42 post-hoc dan bukti
  provenance/inventaris 507 header CSV serta 18 indeks ZIP tersedia di
  `docs/revisi-ii/`. Sembilan tes evaluator, empat tes agreement, empat tes
  invariansi training/rollout dan audit prompt 740 baris lulus. Prediksi baseline
  direplay identik pada seluruh740 untuk ketiga task; kontrol frozen dan
  backbone, lima arm tail GPU serta augmentasi tanpa rotasi menghasilkan OOF
  baru terpisah. Delapan XAI E42 outer-fold direplay sesuai model, disertai
  LIME/deletion aktual dengan hasil campuran, bukan klaim faithfulness universal.
  Paket kandidat B01 (73 sumber/219 baris metrik/1.186 hash file) dan tiga
  notebook lulus Run all Linux lokal serta environment Python baru dari
  ekstraksi. Template150 anotasi/60 audit kasus/lima penilai disediakan tanpa
  skor buatan; kontrol input/Qwen dan QA Colab masih dalam pengerjaan.
  Source/hasil/ZIP historis tidak ditimpa (plan:
  [implementasi Revisi II](docs/plans/2026-11-01-revisi-ii-evaluasi-delivery.md)).
- Plan pengerjaan 28 butir Revisi II dan tindak lanjut Agustus pada
  [plan revisi notebook](docs/plans/2026-11-01-pengerjaan-revisi-ii-notebook.md):
  audit bukti/provenance, pemeringkatan Macro-F1, identitas model, statistik,
  ablasi, anotasi/XAI, reproduksi dan delivery berversi. Plan memuat pemetaan
  seluruh ID, dependensi, target sampai Desember, kebutuhan manusia dan kriteria
  verifikasi. Hasil awal E48/E49 dan implementasi XAI dicatat sebagai bahan audit;
  belum ada perubahan source/notebook, training atau delivery baru pada task ini.
- Pembacaan seluruh 26 halaman `revision/Daftar-Revisi-II-Pemeriksaan-Notebook-Joy.pdf`
  dan pemetaan 19 revisi R18–R36, keluaran wajib, tenggat, butir Agustus serta
  perbedaan konteks paket yang diterima dosen versus arsip lokal. Ringkasan dan
  catatan verifikasi disimpan pada [plan pembacaan Revisi II](docs/plans/2026-11-01-baca-revisi-ii-notebook.md).
  Notebook, source, PDF dan delivery tidak diubah; implementasi revisi serta
  pengujian ulang klaim teknis/statistik belum dilakukan.
- Pemeriksaan delivery lokal terakhir pada 1 November 2026: SHA-256, CRC dan
  seluruh hash konten manifest lulus untuk ZIP Colab PREPARATION (765 file),
  eksperimen final (6.547 file), dan Windows R3 (798 file). Colab terbaru belum
  memiliki checkpoint E14 terverifikasi; paket final tetap CLIP–IndoBERT dan
  belum memuat CI-D01; laporan R3 masih snapshot E14 parsial. Hasil dan batas
  verifikasi dicatat pada [plan pemeriksaan delivery](docs/plans/2026-11-01-cek-delivery-terakhir.md).
  Source, model dan arsip delivery tidak diubah; runtime Windows/Colab dan
  status Kaggle live tidak diuji ulang.
- Hasil final CI-D01 Kaggle version1 COMPLETE/VERIFIED pada20Okt2026:
  dua arm masing-masing740OOF dari lima fold dikoleksi ke
  `08_ci_d01_duplicate2x/full/raw/ci_d01_dup2/`, dengan `full/verification.json`
  dan `CI_D01_REPORT.md`. Macro-F1 kontrol1× `0,494619/0,420814/0,385696`
  versus duplikasi2× `0,495259/0,390541/0,388486`: delta Task1/2/3
  `+0,06/−3,03/+0,28`poin persentase. Minimum naik tipis tetapi rerata turun;
  target0,70 seluruh task belum tercapai, tidak ada promosi ke web.
  Audit split/ID/multiplicity, label/probabilitas/metrics, epoch/update,
  inisialisasi dan hash lulus; hitung ulang stdlib Counter dan delapan tes
  lokal juga lulus. Canonical CPU checkpoint reload dijalankan di Kaggle;
  checkpoint besar belum direplay lokal. Dataset/label, hasil lama dan ZIP
  tidak ditimpa. Dokumentasi hasil diperbarui pada
  [eksperimen duplikasi2×](docs/EKSPERIMEN_CLIP_INDOBERT_DUPLIKASI_2X_2026-10-20.md)
  (plan selesai: [training CLIP–IndoBERT 2×](docs/plans/2026-10-20-clip-indobert-train-duplicate2x.md)).
- Eksperimen Kaggle CI-D01 CLIP–IndoBERT paired control1× versus duplikasi
  training2× pada `01_notebook/next_research_20261017/kaggle_ci_d01_dup2/`:
  builder/protokol berhash, worker cached-tail, audit split/multiplicity,
  delapan tes lokal, launcher smoke/full dan collector dengan ledger anti
  duplikasi submission. Data740/label/fold asli tidak berubah; hanya training
  digandakan setelah split, test/validation tetap unik. Warm-head sama dan
  pemilihan epoch inner-only; evaluasi canonical CPU FP32 dari checkpoint.
  Smoke GPU version1 COMPLETE/VERIFIED (dua tail/shared/tiga head berubah,
  multiplicity1×/2× dan checkpoint roundtrip lulus). Job full lima fold
  `tempo-ci-d01-clip-indobert-dup2-full` version1 terkirim20Okt17.30WIB,
  status pertama QUEUED; hasil kualitas baru masih Not Evaluated. Tidak
  mengubah web, source/hasil E41/E42/E14 atau ZIP historis. Dokumentasi:
  [eksperimen duplikasi2×](docs/EKSPERIMEN_CLIP_INDOBERT_DUPLIKASI_2X_2026-10-20.md)
  (plan in-progress: [training CLIP–IndoBERT 2×](docs/plans/2026-10-20-clip-indobert-train-duplicate2x.md)).
- Jalur deployment MICRO-E14 joint QLoRA di `02_web_demo/micro_e14_engine.py`,
  pemilihan backend/API/status UI pada `app.py`/`index.html`, launcher GPU
  Linux/Windows dan `requirements-micro-e14.txt`. Backend baru memvalidasi
  checkpoint/input dan smoke GPU startup sebelum `ready`; tidak memakai CSV
  OOF, fallback CLIP, atau mengklaim XAI CLIP/IndoBERT sebagai XAI E14.
  Unggahan baru ditolak eksplisit sampai fitur visual E01 tersedia. Baseline
  tetap default dan layanan lama tidak dialihkan. Lima tes derivasi/prompt,
  empat tes API/Chromium E14 serta regresi baseline/UI/protokol lulus lokal;
  GPU runtime/clean Windows belum diuji. Builder/collector baru terpisah di
  `01_notebook/next_research_20261017/kaggle_micro_e14_deploy/`, kontrak dan
  konteks visual berhash di `06_models/micro-e14-qlora-v1/`. Job Kaggle
  `tempo-micro-e14-deployment-refit` version1 dikirim sekali dan RUNNING:
  refit740/tiga epoch dari median pilihan inner, bukan benchmark baru.
  Checkpoint belum dikoleksi; aktivasi menunggu selesai/verifikasi dan pilihan
  GPU serving. Dokumentasi: [deployment E14](docs/DEPLOYMENT_MICRO_E14_2026-10-20.md).
  Delivery/historis/protokol CV tidak ditimpa (plan masih in-progress:
  [deployment MICRO-E14 web](docs/plans/2026-10-20-deployment-micro-e14-web.md)).
- Materi final riset/presentasi pada `delivery/experiment_final_20261020/`:
  tiga notebook baseline/eksperimen/perbandingan final yang dieksekusi lokal
  dengan tabel/grafik tersimpan; sembilan CSV termasuk 159 baris benchmark,
  85 perbandingan dan 1.249 metrik per kelas; tujuh grafik PNG/SVG. Sebelas
  salinan notebook asli/snapshot, 417 inventaris source dan diff notebook
  17→19 Oktober dipertahankan. Dokumentasi membedakan perubahan Markdown
  notebook historis dari source training E12/E13/E14, pilot 119 validation
  dari 740 OOF, hasil aktual dari Not Evaluated, serta dampak yang tidak diuji.
  Source/data/hasil penelitian dan web terbaru disalin tanpa perubahan model;
  skill spreadsheets digunakan untuk penataan/provenance CSV, validasi angka,
  minimum dan delta; tiga HTML notebook diuji offline Chromium. ZIP final
  `delivery/experiment_final_20261020/TEMPO_EXPERIMENT_FINAL_20261020.zip`
  berisi 6.547 file (sekitar 3,13 GB) dan lulus CRC, hash seluruh konten serta
  runtime dari ekstraksi. Wrapper Windows CRLF disertakan; source asli,
  notebook historis, dan paket lama tidak ditimpa. Timestamp arsip sebelum
  1980 dinormalisasi hanya pada metadata ZIP. Eksekusi Colab akun/GPU dan
  clean Windows belum diklaim diuji
  (plan: [final Colab, benchmark dan web](docs/plans/2026-10-20-final-colab-benchmark-web.md)).
- Catatan startup demo lokal 20 Oktober 2026 pada `127.0.0.1:7860` untuk uji
  pengguna: pemeriksaan delivery, HTTP halaman/model dan 740 sampel lulus;
  UI persentase terurut terbaru termuat. Backend tetap CLIP–IndoBERT,
  tanpa perubahan source/model/training (plan:
  [jalankan demo lokal](docs/plans/2026-10-20-jalankan-demo-lokal.md)).
- Evaluasi final MICRO-E14 lima fold selesai dan VERIFIED pada 20 Oktober
  2026 pukul 00.00 WIB: fold 3/5 diambil dari Kaggle, tepat 740 prediksi OOF,
  Micro-F1 `0,720270/0,566216/0,667568` dan Macro-F1
  `0,673321/0,510282/0,595480`. Hanya Task 1 lulus Micro-F1 ≥0,70;
  target ketiga task belum tercapai. Label, split, epoch/refit, probabilitas,
  source/protokol/prediksi, 740 gambar serta seluruh manifest diverifikasi
  ulang; lima tes CPU protokol lulus. Ledger complete dan ranking siklus
  diperbarui tanpa training/push baru atau perubahan model aplikasi/ZIP.
  Hasil: `next_research_20261017/06_micro_f1/MICRO_E14_joint_qlora_oof/`;
  ringkasan: [hasil final E14](docs/HASIL_FINAL_MICRO_E14_2026-10-20.md)
  (plan: [verifikasi final E14](docs/plans/2026-10-19-verifikasi-final-e14-oof.md)).
- Scheduler MICRO-E14 diaktifkan kembali pada 19 Oktober pukul 19.41 WIB
  memakai ledger/lock yang sama, tanpa perubahan training atau duplikasi
  job. Hasil fold 4 diambil dan VERIFIED (148 outer-test, Micro-F1
  `0,709459/0,554054/0,709459`); fold 5 dikirim version 1 dan terkonfirmasi
  RUNNING di Kaggle pada 19.42 WIB. Fold 1–4 tidak dipush ulang; protokol dan
  hash launcher tetap sama. Log runtime:
  `MICRO_E14_joint_qlora_oof/scheduler.log`; evaluasi lima fold belum final
  (plan: [aktifkan kembali scheduler E14](docs/plans/2026-10-19-aktifkan-kembali-scheduler-e14.md)).
- Delivery Windows R3 dengan UI prediksi terurut di
  `delivery/update_20261019/clean_windows_r3/TEMPO_WINDOWS_UPDATE_20261019_R3.zip`
  (101.521.865 byte, 798 file), laporan terbaru, checksum dan verifikasi.
  Hasil parsial E14 fold 1–2 ikut dikemas sebagai bukti, bukan 740 OOF final.
  Snapshot pukul 18.45 WIB: fold 1–2 COMPLETE/verified, fold 3 QUEUED, fold 4
  RUNNING, fold 5 PENDING; scheduler lokal tidak terdeteksi aktif. Builder
  `delivery/update_20261019/build_latest_windows.py` kini menyajikan status
  dinamis dan membedakan observasi live dari fallback ledger. Paket R2 tetap
  dipertahankan. CRC, SHA-256, source UI, provenance dan runtime ekstraksi
  lulus; clean Windows belum diuji (plan:
  [sorting UI dan delivery R3](docs/plans/2026-10-19-sort-persentase-ui-delivery-r3.md)).
- Tes sorting numerik, stabilitas skor sama, input immutable dan kecocokan
  task/kelas/bar skor di `01_notebook/test_prediction_sort.js`, serta dua tes
  Chromium desktop/mobile dan escaping di
  `01_notebook/test_prediction_sort_browser.py`; seluruhnya lulus (plan:
  [sorting UI dan delivery R3](docs/plans/2026-10-19-sort-persentase-ui-delivery-r3.md)).
- Delivery Windows clean R2 dan laporan terbaru tanggal 19 Oktober 2026 pada
  `delivery/update_20261019/clean_windows_latest/`: ZIP
  `TEMPO_WINDOWS_UPDATE_20261019_R2.zip` (101.151.685 byte, 786 file), laporan
  `LAPORAN_TERBARU_TEMPO_20261019.md`, bukti E11/E12/E13 dan OCR, serta snapshot
  E14 pukul 14.16 WIB (fold 1–2 RUNNING; 3–5 PENDING). Model runtime tidak
  diganti, paket lama dan job Kaggle tetap dipertahankan. Metrik dihitung ulang;
  CRC, SHA-256, provenance data, kesamaan laporan luar/dalam ZIP dan pemeriksaan
  runtime dari ekstraksi lulus. Clean Windows belum diuji. Builder:
  `delivery/update_20261019/build_latest_windows.py` (plan:
  [delivery dan laporan terbaru](docs/plans/2026-10-19-delivery-windows-laporan-terbaru.md)).
- MICRO-E14 joint QLoRA lima fold dengan protokol terkunci, seleksi inner epoch
  1–3 per fold, reset adapter persis/refit pada 592 training sampel, checkpoint
  per epoch, generator launcher ber-hash, scheduler dua slot dan verifier 740
  OOF di `01_notebook/next_research_20261017/kaggle_micro_e14/`. Fold 1–2 version
  1 sudah dikirim dan terkonfirmasi RUNNING di Kaggle; Fold 3–5 menunggu slot
  pada antrean lokal. Hasil evaluasi belum tersedia (plan:
  `docs/plans/2026-10-19-e14-qlora-five-fold.md`).
- Hasil MICRO-E13 joint QLoRA pilot version 1 COMPLETE dan diverifikasi pada
  119 inner-validation sampel: epoch 3 terpilih, Micro-F1
  `0,7227/0,5882/0,6807`, minimum naik 9,24 poin persentase dari kontrol split
  sama. Lulus gate praktis pilot; belum eligible sebagai 740 OOF dan belum
  membuktikan target 0,70. Prediksi, log, hasil, verifier dan keputusan tersimpan
  di `next_research_20261017/06_micro_f1/MICRO_E13_joint_qlora_inner_pilot/`
  (plan: `docs/plans/2026-10-19-e12-decoder-dan-qlora-pilot.md`).
- MICRO-E12 structured decoder di
  `01_notebook/next_research_20261017/run_micro_e12_structured_decoder.py`:
  nesting penuh pada base/meta model, kontrol tanpa prior, prior kombinasi tiga
  label training-only, serta audit split dan verifier hasil independen.
  Lima fold/740 OOF selesai dan terverifikasi: Micro-F1
  `0,5784/0,5446/0,5108`, minimum di bawah kontrol tanpa prior `0,5122` dan E11
  `0,5324`; tidak dipromosikan (plan:
  `docs/plans/2026-10-19-e12-decoder-dan-qlora-pilot.md`).
- Pilot Kaggle MICRO-E13 joint QLoRA inner-only, maksimum enam epoch dan enam
  jam GPU, checkpoint/prediksi validation tiap epoch. Kontrol pada split yang
  sama (473 training, 119 validation) menghasilkan Micro-F1
  `0,5546/0,4958/0,5546`; hasil ini bukan 740 OOF (plan:
  `docs/plans/2026-10-19-e12-decoder-dan-qlora-pilot.md`).
- Delivery Windows clean terbaru di
  `delivery/update_20261019/clean_windows/TEMPO_WINDOWS_UPDATE_20261019.zip`
  (101 MB, 761 file): hanya runtime, data/gambar, launcher Windows, panduan
  singkat dan ringkasan E11/E07. Riwayat eksperimen dan dokumen lama dikeluarkan
  dari paket; hash provenance data dipertahankan. CRC, hash dan pemeriksaan
  runtime dari ekstraksi lulus (plan:
  `docs/plans/2026-10-19-clean-delivery-windows.md`).
- Full Windows release v2 tanggal 19 Oktober di
  `delivery/update_20261019/tempo-final-release-v2-windows-20261019.zip` dengan
  1.813 entry, 935 file teks CRLF, skrip setup/launcher Windows, manifest,
  checksum, security scan, serta verifikasi CRC dan hash konten (plan:
  `docs/plans/2026-10-19-delivery-update-windows.md`).
- Full Linux release v2 tanggal 19 Oktober di
  `delivery/update_20261019/tempo-final-release-v2-linux-20261019.zip`, lengkap
  dengan manifest 1.816 entry, checksum SHA-256, security scan, serta verifikasi
  CRC dan hash konten (plan:
  `docs/plans/2026-10-19-delivery-update-terbaru.md`).
- Artefak lengkap smoke test MICRO-E07 Kaggle version 4 di
  `next_research_20261017/06_micro_f1/MICRO_E07_joint_qlora_smoke/`: adapter,
  24 prediksi fold 1, input audit, log, konfigurasi, hasil, keputusan, dan
  manifest. Micro-F1 Task1/2/3 `0,6250/0,5417/0,4583`; minimum `0,4583`,
  sehingga diputuskan no-go untuk full five-fold (plan:
  `docs/plans/2026-10-18-target-micro-f1-070.md`).
- Siklus optimasi micro-F1 multitask di `next_research_20261017/06_micro_f1/`: nested stacking E02, classifier chain E03, lexical E04, partial fine-tune SigLIP E05, dan VLM-text E06 dengan 740 prediksi OOF serta manifest; minimum terbaik sementara `0,5041` pada E02 (plan: `docs/plans/2026-10-18-target-micro-f1-070.md`).
- Implementasi dan smoke job Kaggle `MICRO_E07` untuk satu adapter Qwen3-VL bersama dengan tiga objective klasifikasi; packaging worker, inner epoch selection, reset adapter, dan refit outer-training disiapkan sebelum lima fold penuh (plan: `docs/plans/2026-10-18-target-micro-f1-070.md`).
- Audit QLoRA E12 Task 2 lengkap pada 740 OOF: micro-F1 `0,5919` dan Macro-F1 `0,5534`, menjadi bukti jalur VLM generatif lebih kuat untuk bottleneck Task 2 (plan: `docs/plans/2026-10-18-target-micro-f1-070.md`).
- Eksperimen MICRO-E08 menggabungkan embedding frozen Qwen3-VL E15, caption-context E22, BGE-M3, dan CLIP dengan seleksi nested tiga-head; micro-F1 Task1/2/3 `0,5554/0,5378/0,4824`, sehingga tidak menggantikan E02 menurut skor minimum (plan: `docs/plans/2026-10-18-target-micro-f1-070.md`).
- MICRO-E10 nested multimodal stacking membuat ulang base prediction klasik/VLM hanya dari outer-training dan menaikkan micro-F1 Task1/2/3 menjadi `0,5811/0,5595/0,5270`; minimum `0,5270` menjadi hasil terbaik sementara tetapi belum lulus `0,70` (plan: `docs/plans/2026-10-18-target-micro-f1-070.md`).
- MICRO-E11 menambahkan head Task 3 hierarkis nested (`individual` vs non-individual lalu tujuh tipe lain) dan menaikkan Task 3 ke `0,5324`; skor joint menjadi `0,5811/0,5595/0,5324`, masih belum mencapai target (plan: `docs/plans/2026-10-18-target-micro-f1-070.md`).
- Paket audit Sprint 0 penelitian lanjutan di `DEMO_XAI_745_FULL/04_hasil_eksperimen/next_research_20261017/`: reproduksi E42, distribusi/per-class metrics, audit leakage dan train–serve parity, registry, frozen protocol, findings, serta manifest SHA-256 (plan: `docs/plans/2026-10-17-implementasi-optimasi-multitask-tempo.md`).
- Eksperimen kontrol M01 shared MLP di `DEMO_XAI_745_FULL/01_notebook/next_research_20261017/run_m01_shared_mlp.py` beserta OOF, result, dan keputusan stop; Macro-F1 Task1/2/3 `0,4426/0,3592/0,3581` (plan: `docs/plans/2026-10-17-implementasi-optimasi-multitask-tempo.md`).
- Model comparison joint M02 SigLIP2 dan M03 DINOv2 melalui Kaggle, lengkap dengan embedding ber-hash, OOF, manifest, dan verifikasi lokal. M02 memperoleh `0,4904/0,4213/0,3749`; M03 `0,4163/0,3928/0,2859` (plan: `docs/plans/2026-10-17-implementasi-optimasi-multitask-tempo.md`).
- M04 SigLIP2 task-specific adapters menghasilkan `0,5038/0,4222/0,3805`; lebih baik dari M02 menurut minimum tetapi masih di bawah E42, sehingga dihentikan (plan: `docs/plans/2026-10-17-implementasi-optimasi-multitask-tempo.md`).
- Eksperimen J01 hierarchical auxiliary Task 2 menghasilkan `0,5050/0,3858/0,3707` dan dihentikan karena minimum Macro-F1 di bawah E42 (plan: `docs/plans/2026-10-17-implementasi-optimasi-multitask-tempo.md`).
- Konfigurasi augmentation A00–A03, contoh QA deterministik per kelas Task 2, serta job Kaggle SigLIP2 training-fold-only di `next_research_20261017/02_augmentation/` (plan: `docs/plans/2026-10-17-implementasi-optimasi-multitask-tempo.md`).
- Hasil augmentation A00–A03 dan pipeline pilihan inner-fold telah diverifikasi; minimum terbaik varian tunggal `0,3663` (A01), pipeline pilihan `0,3564`, sehingga tidak mengalahkan E42 (plan: `docs/plans/2026-10-17-implementasi-optimasi-multitask-tempo.md`).
- Evaluasi kanonik, prediksi final internal OOF, model manifest, kontrak artefak 11 eksperimen, dan audit penyelesaian Sprint 0–4 ditambahkan di `next_research_20261017/` (plan: `docs/plans/2026-10-17-implementasi-optimasi-multitask-tempo.md`).
- Ringkasan OCR read-only dengan exact match, CER, token-F1, dan latensi untuk dua holdout serta set independen di `next_research_20261017/04_ocr/ocr_final_report.md` (plan: `docs/plans/2026-10-17-implementasi-optimasi-multitask-tempo.md`).
- Release QA penelitian lanjutan di `next_research_20261017/05_final_evaluation/release_qa.md`; 63 test non-frontend dan 13/13 test Playwright Chromium lulus (plan: `docs/plans/2026-10-17-implementasi-optimasi-multitask-tempo.md`).

### Changed

- Klarifikasi R23/R6 berdasarkan keterangan Joy yang diteruskan pengguna pada
  2 November 2026: penyusutan korpus disebabkan banyak citra sampul berkualitas
  buruk sehingga tidak dapat dilabeli; menurut Joy alasan tersebut sudah pernah
  disampaikan. `CORPUS_HISTORY.md`, catatan sumber `R23_KLARIFIKASI_JOY.json`,
  generator audit/report, tracker dan draf naskah diperbarui. Penjelasan umum
  dipisahkan dari keterlacakan per ID dan kebutuhan agreement dua anotator;
  angka perkiraan pada pesan tidak diperlakukan sebagai audit rinci 300 ID.
  Delivery R1 dibuat terpisah tanpa mengubah versi yang sudah diserahkan
  (plan: [klarifikasi R23](docs/plans/2026-11-02-klarifikasi-r23-kualitas-citra.md)).

- `docs/CANONICAL_SOURCE.md`, `docs/DELIVERY_MAIN_MODEL.md` dan
  `docs/WORKSPACE_INDEX.md` membedakan model penelitian E42, runtime web
  CLIP-B32 historis, arsip20Oktober dan kandidat Revisi II, serta mengganti
  kriteria keputusan baru ke pelaporan komparatif Macro-F1. Alamat/status
  layanan lama diberi konteks tanggal; tidak diklaim diverifikasi live (plan:
  [implementasi Revisi II](docs/plans/2026-11-01-revisi-ii-evaluasi-delivery.md)).
- Tabel Prediksi tiga task di `DEMO_XAI_745_FULL/02_web_demo/index.html` kini
  menampilkan persentase tertinggi ke terendah. Label task/kelas, bar dan
  runner-up mengikuti prediksinya; skor/model tidak berubah. Skor sama tetap
  stabil, skor tidak valid tampil terakhir sebagai tanda pisah. Urutan panel
  XAI tidak berubah (plan:
  [sorting UI dan delivery R3](docs/plans/2026-10-19-sort-persentase-ui-delivery-r3.md)).
- Reset adapter MICRO-E07 kini menyalin hanya tensor LoRA trainable, sehingga
  metadata kuantisasi bitsandbytes tidak lagi dimuat ulang sebagai key model;
  smoke test terkoreksi telah dipush sebagai Kaggle version 4
  (`kaggle_micro_e07/worker.py`, `kaggle_micro_e07/launch.py`; plan:
  `docs/plans/2026-10-18-target-micro-f1-070.md`).
- Plan implementasi direkonsiliasi dengan artefak aktual: E49 dan OCR holdout kedua sudah selesai, sehingga keduanya tidak dijalankan ulang (plan: `docs/plans/2026-10-17-implementasi-optimasi-multitask-tempo.md`).

## [1.0.0] — 2026-10-17 (Final Release)

Rilis final aplikasi Demo XAI — Dekoding Metafora Sampul Majalah Tempo.
Mencakup Sprint 0 (konsolidasi workspace), Sprint 1 (acceptance aplikasi & OCR),
Sprint 2 (keputusan model & target penelitian), dan Sprint 3 (final release & delivery).

### Added

#### Paket Delivery
- Paket rilis final **Windows** `tempo-final-release-v1-windows.zip` (1,63 GB, 5.423 file) di `delivery/final_release_20261017/`: file teks dikonversi CRLF (4.229 file), 3 file Linux-only dieksklusi. ZIP CRC & SHA-256 verified, security scan passed. Gunakan `setup_windows.bat` lalu `jalankan_windows.bat` (plan: [Delivery Windows ZIP](docs/plans/2026-10-17-delivery-windows-zip.md)).
- Paket rilis final **Linux** `tempo-final-release-v1-linux.zip` (1,71 GB, 5.429 file) di `delivery/final_release_20261017/`: source canonical, web demo R5, selector OCR, data 740 sampul, panduan pengguna, dan dokumentasi batasan. ZIP CRC & SHA-256 verified (plan: [Sprint 3 Final Release](docs/plans/2026-10-17-sprint-3-final-release-delivery.md)).
- Paket delivery Week 3/4 **CLIP–IndoBERT MTL** `tempo-week34-clip-indobert-mtl-v1-linux.zip` dengan satu model joint untuk ketiga task. 85 tes Python, 4 skrip JS, HTTP dan browser lulus (plan: [penyelarasan CLIP–IndoBERT MTL](docs/plans/2026-10-12-align-delivery-clip-indobert-mtl.md)).
- Paket delivery Week 3/4 **E14** `tempo-week34-e14-v1-linux.zip` dengan parity 740 OOF, clean install, 83 regresi lulus (plan: [delivery E14](docs/plans/2026-10-12-week34-e14-delivery.md)).
- Paket delivery **Minggu 1** `DEMO_XAI_TEMPO_W1_2026-09-22.zip` (96,3 MB) (plan: `docs/plans/2026-09-22-timeline-3-minggu.md`).

#### Dokumentasi
- Manifest `docs/CANONICAL_SOURCE.md`: model aktif `clip-indobert-mtl-v1`, metrik ketiga task, SHA-256 runtime, ruang lingkup sinkronisasi (plan: [Sprint 0](docs/plans/2026-10-17-sprint-0-konsolidasi-workspace.md)).
- Indeks workspace `docs/WORKSPACE_INDEX.md` dan roadmap Sprint 0–3 `docs/SPRINT_ROADMAP.md` (plan: [rapikan workspace dan sprint](docs/plans/2026-10-17-rapikan-workspace-dan-sprint.md)).
- Dokumen batasan `docs/BATASAN_MASALAH_DAN_PERBAIKAN.md`: batasan objek, dataset, OCR, klasifikasi, XAI, deployment; gap target; perbaikan P0–P2 (plan: [batasan masalah dan perbaikan](docs/plans/2026-10-17-batasan-masalah-dan-perbaikan.md)).
- Keputusan model `docs/MODEL_CANDIDATE_DECISION.md`: ranking 13 model joint, E42 kandidat utama (plan: [Sprint 2](docs/plans/2026-10-17-sprint-2-keputusan-model.md)).
- Status plan lama diaudit di `docs/PLAN_STATUS_AUDIT.md` (plan: [Sprint 0](docs/plans/2026-10-17-sprint-0-konsolidasi-workspace.md)).
- `docs/DELIVERY_WEEK_1.md` — laporan lengkap Minggu 1.
- `02_BATASAN_TEKNIS.md` — dokumen batasan teknis.
- `docs/2026-09-22-keputusan-ocr.md` — dasar pemilihan EasyOCR vs TrOCR.
- `docs/2026-09-22-pemahaman-demo-dan-revisi.md` — pemahaman sistem + inventaris revisi pembimbing.
- Timeline 3 minggu `docs/plans/2026-09-22-timeline-3-minggu.md`.

#### Ranking Model & Eksperimen Penelitian
- Ranking reproducible 13 model joint via `01_notebook/rank_joint_candidates.py` dan `04_hasil_eksperimen/joint_candidate_ranking.json`. Hasil terbaik:
  - **E42** (Rank 1): Macro-F1 Task1 `0,5255` / Task2 `0,3956` / Task3 `0,4034`
  - **E49 MMoE** (Rank 7): Macro-F1 Task1 `0,4949` / Task2 `0,3977` / Task3 `0,3695`
  - Target Macro-F1 ≥ 0,70 belum tercapai; limitasi saturasi korpus 740 sampel didokumentasikan.
- E48 single-task diagnostic: Macro-F1 Task1/2/3 `0,4861/0,4185/0,3883`; mendukung task-specific routing, tidak eligible sebagai model joint (plan: [eksekusi target](docs/plans/2026-10-17-eksekusi-target-ocr-dan-model.md)).
- E44 focal tail: Macro-F1 `0,5255/0,3937/0,4038`; weightedCE terpilih seluruh fold (plan: [E44](docs/plans/2026-10-13-e44-focal-tail.md)).
- E47 task relations: Macro-F1 `0,4565/0,4248/0,3759` (plan: [E47](docs/plans/2026-10-13-e47-task-relations.md)).
- E46 label smoothing: Macro-F1 `0,4575/0,4178/0,3534` (plan: [E46](docs/plans/2026-10-13-e46-label-smoothing.md)).
- E43 spatial attention: Macro-F1 `0,4673/0,4246/0,3675` (plan: [E43](docs/plans/2026-10-13-e43-spatial-cross-attention.md)).
- E41 cached tail: Macro-F1 `0,4957/0,4207/0,3857` (plan: [E41](docs/plans/2026-10-12-e41-cached-tail-indobert.md)).
- E40 balanced MMoE: Macro-F1 `0,4617/0,4183/0,3736` (plan: [E40](docs/plans/2026-10-12-e40-balanced-mmoe-mtl.md)).
- E39 feature norm: Task2 best `0,4348` (plan: [E39](docs/plans/2026-10-12-e39-train-only-feature-normalization.md)).
- E36 CLIP-L14: Task2 `0,4315`; E38 L14 token: Task2 `0,4055` (plans: [E36](docs/plans/2026-10-12-e36-clip-l14-multiview-mtl.md), [E38](docs/plans/2026-10-12-e38-l14-token-fusion.md)).
- E37 IndoBERT token pooling: Macro-F1 `0,4851/0,3692/0,3443` (plan: [E37](docs/plans/2026-10-12-e37-indobert-token-pooling.md)).
- E33 joint MTL: Task2 `0,3530` (plan: [E33](docs/plans/2026-10-12-e33-joint-mtl-optimization.md)); E34 partial fine-tune: `0,3533` (plan: [E34](docs/plans/2026-10-12-e34-partial-finetune-mtl.md)); E35 PCGrad: `0,3435` (plan: [E35](docs/plans/2026-10-12-e35-pcgrad-joint-mtl.md)).
- E32 illustration crop: Macro-F1 `0,5632` (plan: [E32](docs/plans/2026-10-12-e32-illustration-crop.md)).
- E31 fast adapter: Macro-F1 `0,4748` (plan: [E31](docs/plans/2026-10-12-e31-fast-adapter.md)).
- E30 shrinkage LDA: Macro-F1 `0,5580` (plan: [E30](docs/plans/2026-10-11-e30-shrinkage-lda.md)).
- E29 PCA boosting: Macro-F1 `0,4848` (plan: [E29](docs/plans/2026-10-11-e29-pca-boosting.md)).
- E28 grounded mapping: Macro-F1 `0,5453` (plan: [E28](docs/plans/2026-10-11-e28-grounded-mapping.md)).
- E27 nested stacking: Macro-F1 `0,4952` (plan: [E27](docs/plans/2026-10-11-e27-nested-stacking.md)).
- E26 caption lexical: Macro-F1 `0,5386` (plan: [E26](docs/plans/2026-10-11-e26-caption-lexical.md)).
- E25 DINOv2 visual: Macro-F1 `0,5382` (plan: [E25](docs/plans/2026-10-11-e25-dinov2-visual.md)).
- E24 semantic MLP: Macro-F1 `0,5358` (plan: [E24](docs/plans/2026-10-11-e24-semantic-mlp.md)).
- E23 SigLIP2 visual: Macro-F1 `0,5574` (plan: [E23](docs/plans/2026-10-11-e23-siglip2-visual.md)).
- E22 grounded caption: Macro-F1 `0,5576` (plan: [E22](docs/plans/2026-10-11-e22-grounded-caption.md)).
- Baseline delivery (aktif): Macro-F1 Task1 `0,4380` / Task2 `0,3197` / Task3 `0,2764`.

#### OCR & Evaluasi
- Evaluator holdout 2 `01_notebook/evaluate_ocr_second_holdout.py`: 90 sampel, exact match `69/90 (76,67%)`, usabilitas manusia `81,25%` (plan: [peningkatan selector OCR](docs/plans/2026-10-17-peningkatan-selector-ocr-holdout2.md)).
- Holdout OCR pertama (80 sampel): exact match `60/80 (75%)` (plan: [Sprint 1](docs/plans/2026-10-17-sprint-1-acceptance-ocr.md)).
- Holdout OCR kedua dibekukan: 90 sampel, 10 per kelas, SHA-256 manifest `f3cdc963...125aae` (plan: [eksekusi target](docs/plans/2026-10-17-eksekusi-target-ocr-dan-model.md)).
- Evaluator independen `01_notebook/evaluate_ocr_independent.py`: 60 sampel, headline exact match `43/60 (71,67%)`, token-F1 `0,8373` (plan: [Sprint 1](docs/plans/2026-10-17-sprint-1-acceptance-ocr.md)).
- Validasi manusia 20 kegagalan OCR: 5 valid, 12 invalid, 3 ambigu (plan: [eksekusi target](docs/plans/2026-10-17-eksekusi-target-ocr-dan-model.md)).
- Audit reproducible 740 sampel via `01_notebook/audit_targets_20261017.py` (plan: [eksekusi target](docs/plans/2026-10-17-eksekusi-target-ocr-dan-model.md)).
- `01_notebook/uji_banding_ocr.py`: EasyOCR F1 `0,895` vs OCR mentah `0,204`.
- Modul OCR headline `02_web_demo/ocr_headline.py` + endpoint `POST /api/ocr`.

#### XAI & Fitur Aplikasi
- Peta panas terpadu tiga task (`gradcam_terpadu()` di `xai_core.py`) — peta gabungan rata-rata sebagai peta utama (revisi R5).
- Atribusi kata LIME (`atribusi_kata_lime()` di `xai_core.py`) — 120 varian, metode baku; occlusion sebagai cadangan (revisi R4).
- Uji banding LIME vs occlusion `01_notebook/uji_banding_atribusi.py`: gejala "semua negatif" 1/25 (LIME) vs 2/25 (occlusion), korelasi `0,851`.
- Pemetaan nama kelas awam `02_web_demo/label_display.py` (revisi R2).

#### Infrastruktur
- Audit graph CLIP–IndoBERT E41: text, visual, dan joint lulus parity logit, gradien, randomisasi.
- Diagnosis generalisasi E42: mean train-heldout gap Task1 `0,4279` / Task2 `0,6035` / Task3 `0,5796`.
- `setup_windows.bat`, `jalankan_windows.bat`, `jalankan_linux.sh` — launcher multi-platform.
- `MULAI_DARI_SINI.md` — halaman pertama paket delivery.
- Aturan kerja project di `AGENTS.md`.
- `CHANGELOG.md` dan `docs/plans/` sebagai sistem dokumentasi.

### Changed

#### Sprint 0 — Konsolidasi Workspace
- `DEMO_XAI_745_FULL/` ditetapkan sebagai source canonical: runtime CLIP–IndoBERT MTL, kontrak R5, model manifest, launcher, requirements, dan onboarding disinkronkan dari snapshot Week 3–4 (plan: [Sprint 0](docs/plans/2026-10-17-sprint-0-konsolidasi-workspace.md)).
- Root workspace dirapikan: 6 paket ZIP historis dipindahkan ke `delivery/archive/`, dokumen dosen ke `docs/references/` (plan: [rapikan root workspace](docs/plans/2026-10-17-rapikan-root-workspace.md)).
- Timeline tiga minggu dan plan induk Week 3 ditutup sebagai dokumen historis (plan: [rapikan workspace dan sprint](docs/plans/2026-10-17-rapikan-workspace-dan-sprint.md)).

#### Sprint 1 — OCR & Aplikasi
- Selector OCR di `02_web_demo/ocr_headline.py` disempurnakan: deteksi banner rubrik rusak, proteksi kata independen, filtering deck liputan, penggabungan subbaris kapital, dan second-pass crop lokal. Unit test 16/16, JS test, backend 33/33 lulus (plan: [peningkatan selector OCR](docs/plans/2026-10-17-peningkatan-selector-ocr-holdout2.md)).
- Gate formal OCR 80% dan Macro-F1 0,70 ditetapkan pengguna sebagai wajib; limitasi tipografi dekoratif diterima eksplisit, peran OCR sebagai asisten pengisi awal (plans: [Sprint 1](docs/plans/2026-10-17-sprint-1-acceptance-ocr.md), [Sprint 2](docs/plans/2026-10-17-sprint-2-keputusan-model.md)).

#### Sprint 2 — Keputusan Model
- E42 ditetapkan sebagai kandidat riset terbaik; E14 baseline delivery tetap aktif; target 0,70 belum tercapai dan didokumentasikan sebagai limitasi saturasi 740 sampul.
- Model delivery Week 3/4 diselaraskan ke satu joint MTL CLIP–IndoBERT untuk ketiga task (plan: [penyelarasan CLIP–IndoBERT MTL](docs/plans/2026-10-12-align-delivery-clip-indobert-mtl.md)).

#### Dokumentasi & UI
- Jumlah varian LIME diturunkan dari 200 ke 120 (waktu analisis turun ~60 → ~12-23 detik).
- `02_BATASAN_TEKNIS.md` ditulis ulang: perbandingan LIME vs occlusion dengan angka.
- Teks usang UI diperbarui: "Macro-F1 0,174" → `0,320`, "189 tersedia" → `740`.

### Fixed

#### Keamanan & Stabilitas
- Celah path traversal pada `/api/heatmap/<token>` dan `/api/unggahan/<token>`: token dibatasi huruf, angka, garis bawah.
- Folder cache tidak dibersihkan (menumpuk ratusan MB): kini 400 file terbaru saja (`bersihkan_cache()`).
- Jawaban OCR terlambat menimpa gambar baru: ditangani dengan penomoran permintaan.

#### Peta Panas & XAI
- Source utama menampilkan `heatmap_padu_url` sebagai peta gabungan tiga task, `heatmap_url` sebagai bukti task pilihan (plan: [Sprint 0](docs/plans/2026-10-17-sprint-0-konsolidasi-workspace.md)).
- Tanda kontribusi kata tercetak `+-0.023` pada negatif: diformat via `_tanda()`.
- Kata negatif tidak lagi disebut "paling menopang keputusan"; bila semua negatif, dinyatakan terus terang.
- Blok `GABUNGAN` kini selalu tampil selama ada peta panas.

#### OCR & Input
- Logo "TEMPO" rusak terpilih sebagai headline: penyaringan dua lapis, skor gabungan tinggi × posisi × keyakinan × penalti panjang.
- Paragraf deskripsi mengalahkan headline karena panjang tidak diperhitungkan.
- Headline berpenggal tanda hubung tersambung spasi ("ANCANG- ANCANG" → "ANCANG-ANCANG").
- Mengganti gambar tidak memperbarui teks OCR: isi dari OCR kini ditimpa saat gambar berganti.
- Teks lama tertinggal ketika OCR gagal: kolom dikosongkan dulu.
- Berpindah tab meninggalkan data unggahan sebelumnya: kini dibersihkan.

#### Data & Format
- `str.lower()` merusak akronim ("BUMN" → "bumn"): ditangani `_huruf_kecil_aman()`.
- NaN sebagai string `"nan"` pada 83 sampul: disaring via `_bersih()`.
- Prediksi tanpa peringatan saat judul rusak: muncul blok peringatan bila < 2 kata atau < 8 karakter.
- Dokumen merujuk path venv yang tidak ada: diperbaiki.

#### Kaggle & Server
- Job GPU Kaggle macet tanpa output dan menguras kuota: dihentikan manual, kuota direkonsiliasi.
- Akses monitoring Kaggle dipulihkan setelah refresh kredensial resmi.
- Auditor E24 thread mismatch: hash weight berbeda 64 vs 1 thread diperbaiki.
