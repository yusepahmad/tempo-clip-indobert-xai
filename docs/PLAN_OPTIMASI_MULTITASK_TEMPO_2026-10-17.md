# Plan Eksperimen Lanjutan — Klasifikasi Multitask Sampul Majalah Tempo

**Tanggal penyusunan:** 17 Oktober 2026  
**Status:** Proposed / belum dieksekusi  
**Acuan:** `BATASAN_MASALAH_DAN_PERBAIKAN.md` dan `tempo_experiment_context.zip`  
**Ruang lingkup:** Audit E42, model comparison, data augmentation, optimasi multitask, OCR, validasi independen, dan integrasi aplikasi.

> Dokumen ini adalah rencana kerja, bukan laporan bahwa eksperimen baru telah lulus. Hasil E42 serta OCR di bawah berasal dari artefak yang tersedia; perkiraan hasil eksperimen berikutnya belum diketahui.

## 1. Tujuan dan kriteria wajib

Sistem menerima sampul majalah Tempo, mengekstrak headline melalui OCR, memberi kesempatan pengguna mengoreksi teks, lalu memprediksi tiga label sekaligus melalui **satu model joint/multitask** dan menjelaskan prediksinya dengan XAI.

| Komponen | Baseline teraudit | Target wajib | Gap |
|---|---:|---:|---:|
| OCR headline exact match | 60/80 = **0,7500** | **≥0,8000** | Pada set lama setara 4 prediksi tambahan, tetapi set itu bukan lagi independen untuk tuning |
| Task 1 — `task1_issue` (10 kelas) | **0,5255** | **≥0,7000** | +0,1745 |
| Task 2 — `task2_domain_sumber` (7 kelas) | **0,3956** | **≥0,7000** | +0,3044 |
| Task 3 — `task3_primary_entity_type` (8 kelas) | **0,4034** | **≥0,7000** | +0,2966 |

**Aturan mutlak:** ketiga Macro-F1 berasal dari satu artefak joint, satu protokol evaluasi yang sama, dan prediksi per sampel yang dapat diaudit. Tidak boleh mengambil skor terbaik masing-masing task dari tiga model yang berbeda. Metrik utama untuk seleksi adalah `min(F1_Task1, F1_Task2, F1_Task3)`; rata-rata hanya tie-breaker.

**Baseline:** E42 dipilih dari ranking kandidat yang tervalidasi pada artefak yang dikirim. E42 belum lulus target dan belum menjadi model delivery. Ranking tersebut juga rentan *selection bias* akibat eksperimen berulang pada 740 sampul yang sama.

## 2. Kondisi awal dan hambatan

1. Dataset yang dikirim mempunyai **740 anotasi** dan **740 prediksi OOF E42**; ZIP hanya berisi **5 contoh gambar**. Augmentasi gambar pada keseluruhan korpus membutuhkan gambar asli 740 sampul beserta hash/pemetaan ID.
2. E42 menggunakan cache `front_cache.npz` dari jalur `e41_cached_tail` (CLIP visual + representasi IndoBERT sebelum dua tail layer trainable). `preprocessing/features.py` dalam ZIP membuat NPZ berbeda (`img`, `txt`); file tersebut **belum membuktikan cara mereproduksi cache E42**.
3. Kode E42 memakai 5 outer folds dan 2 inner folds; model/hyperparameter dipilih dalam inner folds. Pastikan semua kandidat baru menggunakan split pembanding yang valid dan sama setelah audit grup/duplikasi.
4. `SPRINT_ROADMAP.md` menyebut E48 dan E49, tetapi hasil lengkap dan kodenya tidak ada di ZIP. Cek keduanya sebelum mengulang single-task diagnostic atau MMoE.
5. Teks pada `preprocessing/features.py` berasal dari `headline_verified` dan `supporting_text_verified`, sedangkan aplikasi baru kemungkinan menggunakan OCR. **Asal teks dalam cache E42 masih harus diverifikasi**; jangan menyimpulkan adanya kebocoran input tanpa bukti.
6. OCR memiliki 60/80 exact match pada holdout yang sudah dibuka. Catatan roadmap juga menyebut holdout kedua 69/90 (76,67%); keduanya tetap belum mencapai 80%. Set yang telah dilihat untuk diagnosis tidak dapat digunakan lagi sebagai bukti independen pasca-tuning.
7. Kelas `other_issue` Task 1 berisi 14 sampel. Setelah 8 sampel kelas ini dipakai pada holdout 80 yang dibuka, **tidak mungkin membentuk lagi holdout 8-per-kelas yang benar-benar baru dari 740 sampul yang sama** tanpa mengulang sampel kelas tersebut. Dibutuhkan data prospektif baru atau revisi desain evaluasi yang disetujui peneliti; syarat exact match 80% tidak berubah.
8. Roadmap menyebut beberapa sprint dan paket Linux selesai secara administratif, tetapi **gate akademik OCR ≥80%, semua Macro-F1 ≥0,70, serta pembuktian clean install Windows/human test tetap harus dinilai terpisah**. Jangan menandai semuanya “lulus” hanya karena paket aplikasi sudah dibuat.

## 3. Prinsip eksperimen (berlaku untuk semua sprint)

- **Data:** verifikasi `sample_id`, `image_sha256`, kelompok duplikasi/kemiripan visual, distribusi setiap kelas, serta anotasi ambigu. Jangan mengubah label semata untuk menaikkan skor.
- **Split:** kunci split sebelum eksperimen. Gunakan group-safe folds apabila ditemukan relasi/duplikasi; bila perlu merevisi fold, jalankan ulang baseline E42 pada fold baru untuk perbandingan yang adil.
- **Validasi:** training/augmentation/fit scaler/resampling hanya pada training partition. Pilih hyperparameter, augmentation, dan epoch memakai inner folds. Jangan melihat label outer test untuk memilih konfigurasi *di dalam* satu eksperimen.
- **Risiko multiple testing:** puluhan percobaan pada korpus yang sama menyebabkan pemilihan model tidak lagi independen walaupun OOF dilakukan dengan benar. Akhiri dengan sampel **baru, belum pernah digunakan untuk desain/tuning**, atau laporkan capaian sebagai hasil internal dengan batasan yang eksplisit.
- **Metrik:** Macro-F1 dan per-class precision/recall/F1 tiap task; minimum Macro-F1 sebagai skor seleksi; confusion matrix; deviasi antar-fold dan seed; waktu inferensi, peak CPU/RAM/VRAM, dan ukuran model.
- **Audit:** simpan versi source, manifest dataset, hashes, kelas, fold, seed, train settings, prediksi per sampel, dan checkpoint/manifest. Tidak boleh menghapus/mengganti hasil historis.
- **Eksperimen:** setiap perubahan memiliki hipotesis tunggal atau desain faktorial yang ditetapkan lebih dahulu, sehingga kontribusi model dan augmentation dapat dipisahkan.

## 4. Sprint 0 — Audit, provenance, dan reproduksi E42

**Prioritas:** P0 · **Estimasi:** 1–3 hari kerja aktif · **Dependency:** artefak cache/provenance E41.

### Checklist

- [ ] Terima `e41_cached_tail/README.md`, source pembuat `front_cache.npz`, `cache_manifest.json`, dan metadata encoder/transform.
- [ ] Terima hasil/kode E48 dan E49; catat apa yang benar-benar selesai, apa yang hanya smoke, dan mana yang mempunyai OOF terverifikasi.
- [ ] Audit kecocokan `labels.csv`, fitur cache, urutan `sample_id`, mapping kelas, dan 740 prediksi OOF.
- [ ] Bangun laporan distribusi dan *per-class* F1 ketiga task; fokus Task 2 `LAINNYA`, `KONSUMSI_TRANSAKSI`, `HEWAN_TUBUH` dan Task 3 `political_party`, `legislature`, `multiple_or_other`.
- [ ] Audit duplikasi identik lewat hash dan near-duplicates visual/edisi; dokumentasikan apakah split benar-benar group-safe.
- [ ] Audit input teks: teks OCR mentah, headline hasil koreksi, supporting text, dan field yang tersedia saat inferensi. Uji *train–serve parity*.
- [ ] Reproduksi evaluator E42: Macro-F1 `0,5255 / 0,3956 / 0,4034`; catat toleransi numerik dan hash artefak jika tersedia.
- [ ] Tetapkan protokol dan anggaran eksperimen sebelum melihat kandidat baru; bekukan konfigurasi metrik dan split.

**Output:** `audit_e42.md`, `data_distribution.csv`, `per_class_metrics.csv`, `leakage_report.md`, `frozen_protocol.json`, daftar eksperimen historis yang tidak boleh diulang.

**Gate keluar:** provenance E42 jelas, input model diketahui, split dapat dipertanggungjawabkan, baseline dapat dihitung ulang, dan kandidat baru belum mengulang E48/E49.

## 5. Sprint 1 — Perbandingan model alternatif (*model comparison*)

**Prioritas:** P0 · **Estimasi:** 3–6 hari kerja aktif, sangat bergantung GPU.

### Hipotesis

Representasi visual dan/atau teks yang berbeda mungkin lebih mampu membedakan sumber metafora dan jenis sasaran kritik dibanding E42. Arsitektur joint tetap perlu digunakan untuk keputusan model final.

### Desain dua tahap

**Tahap 1A — Ablation / diagnostik, bukan kandidat delivery:**

- D0: visual-only, dengan tiga output head.
- D1: headline-only (teks terverifikasi), dengan tiga output head.
- D2: visual + headline terverifikasi.
- D3: visual + headline + supporting text; hanya apabila supporting text serupa benar-benar tersedia saat inferensi.
- D4: visual + teks OCR aktual dan visual + teks yang dikoreksi pengguna; mengukur *train–serve gap*.

**Tahap 1B — Kandidat model yang dibandingkan:**

| ID | Encoder visual | Encoder teks | Classifier | Tujuan |
|---|---|---|---|---|
| M00 | CLIP existing | IndoBERT existing | Joint E42 | Baseline yang dihitung ulang jika split berubah |
| M01 | CLIP existing | IndoBERT existing | Shared MLP + 3 heads | Kontrol arsitektur sederhana/frozen |
| M02 | SigLIP2 | IndoBERT | Shared MLP + 3 heads | Alternatif visual representation |
| M03 | DINOv2 | IndoBERT | Shared MLP + 3 heads | Alternatif visual representation |
| M04 (opsional) | Encoder visual terbaik dari M01–M03 | IndoBERT | Task-specific adapter/head | Jika ada bukti *negative transfer* |

Implementasikan semua encoder pada input gambar mentah dan preprocessing native masing-masing checkpoint. Pada fase pertama gunakan frozen encoder + head sebanding untuk menekan biaya dan mengisolasi kontribusi representasi. Fine-tuning sebagian encoder hanya untuk 1–2 kandidat teratas setelah penyaringan.

### Aturan pembandingan

- [ ] Evaluasi dengan kelas, fold, dan evaluator yang sama; tuning dan pemilihan epoch dilakukan di inner folds.
- [ ] Catat `Macro-F1_task1`, `Macro-F1_task2`, `Macro-F1_task3`, `minimum`, `mean`, runtime, peak memory, ukuran checkpoint.
- [ ] Jalankan pilot satu seed; untuk kandidat menjanjikan, ulangi beberapa seed (contoh 42, 123, 3407), hanya jika anggaran komputasi memungkinkan.
- [ ] Pilih maksimal dua kandidat untuk augmentation berdasarkan minimum Macro-F1 dan stabilitas, **tanpa** melihat hasil set evaluasi final.

**Output:** `model_comparison.csv`, grafik per-task/per-class, log konfigurasi, manifest fitur per encoder, prediksi OOF, ringkasan keputusan go/no-go.

## 6. Sprint 2 — Data augmentation dan sampling

**Prioritas:** P0 · **Estimasi:** 2–4 hari kerja aktif · **Dependency:** tersedia gambar asli seluruh sampel dan pipeline extraction yang dapat diulang.

### Hipotesis

Augmentasi yang menjaga headline, karakter, dan makna visual bisa meningkatkan robustness dan mengurangi overfitting. Namun, pada klasifikasi metafora perubahan visual yang terlalu agresif dapat menghilangkan sumber metafora, sehingga tidak boleh dianggap otomatis memperbaiki Task 2.

| ID | Varian | Transform training yang diuji | Kontrol |
|---|---|---|---|
| A00 | No augmentation | Transform bawaan encoder saja | Baseline |
| A01 | Light image | Brightness/contrast kecil, JPEG compression ringan, noise ringan | Label tidak berubah |
| A02 | Moderate image | Intensitas lebih besar tetapi tetap menjaga teks dan simbol, rotasi kecil | Visual QA sampel hasil |
| A03 | Light + class-balanced sampling | A01 ditambah sampler training | Ukur dampak sampling secara terpisah; jalankan A01 dan sampler-only jika anggaran memungkinkan |
| A04 (opsional) | Text robustness | Simulasi kesalahan OCR yang realistis atau token dropout terbatas | Jangan mengubah istilah/semantik yang menentukan label |

### Langkah wajib

- [ ] Kumpulkan seluruh 740 gambar, periksa hash, dan kaitkan dengan `sample_id`.
- [ ] Buat transform deterministik dengan pencatatan seed/probability/intensity. Tinjau visual sampel augmented setiap kelas, terutama kelas metafora yang sensitif.
- [ ] Terapkan augmentation **hanya di training fold**; validation/test tetap memakai gambar asli yang bersih.
- [ ] Jika encoder memakai cache embedding, regenerate fitur gambar augmented per training fold atau lakukan encoding on-the-fly. Jangan berharap fitur CLIP/SigLIP/DINOv2 dari cache lama berubah tanpa ekstraksi ulang.
- [ ] Pisahkan eksperimen sampler/weighted loss agar tidak mengatribusi kenaikan skor pada augmentation secara keliru.
- [ ] Bandingkan A00–A03 pada model sama, split sama, budget sebanding; periksa penurunan per-class F1 dan kestabilan antarseed.
- [ ] Hentikan varian yang merusak teks/headline atau menyebabkan penurunan konsisten pada task kritis.

**Output:** `augmentation_config.yaml`, `augmentation_examples/`, `augmentation_results.csv`, `augmentation_ablation.md`, manifest cache/fitur baru.

**Gate keluar:** ditemukan konfigurasi terbaik **menurut validasi**, atau dinyatakan secara eksplisit bahwa augmentation tidak membantu. Jangan mengklaim target 0,70 tercapai dari pilot semata.

## 7. Sprint 3 — Optimasi joint multitask dan Task 2/3

**Prioritas:** P0 · **Estimasi:** 3–6 hari kerja aktif.

Urutan pengujian (jangan menjalankan semua kombinasi secara buta):

1. **Diagnostik negative transfer:** bandingkan single-task diagnostic dengan joint menggunakan representasi/split identik; catat gap per task. Single-task **tidak** memenuhi syarat model final.
2. **Regularisasi:** tuning kapasitas head, dropout, weight decay, early stopping, freeze/unfreeze secara terbatas pada inner folds.
3. **Imbalance-aware training:** uji weighted CE versus sampler yang sesuai, periksa kelas minoritas dan trade-off kelas lain.
4. **Loss balancing:** mulai dari bobot existing `1:2:2`, lalu uji alternatif yang dibenarkan confusion matrix; dynamic methods seperti GradNorm/PCGrad hanya jika bukti konflik/imbalance gradien mendukung.
5. **Task-specific representation:** adapter/gating/MMoE hanya jika hasil E48/E49 dan diagnostik menunjukkan alasan kuat. Hindari mengulang E49 tanpa hipotesis baru.
6. **Task 2 hierarchical head (opsional):** pelajari deteksi `NON_METAFORA` vs metafora sebagai sinyal bantu lalu domain metafora, tetapi hasil final harus tetap **7 kelas Task 2** dari satu joint model. Cegah label tambahan dari metadata anotator dipakai sebagai input saat inferensi.

**Skor pemilihan:** `S = min(MacroF1_T1, MacroF1_T2, MacroF1_T3)`. Gunakan mean sebagai tie-breaker, dan laporkan interval variasi skor. Prioritaskan kenaikan Task 2/3 tetapi jangan “mengorbankan” Task 1 untuk mengangkat minimum sesaat.

**Output:** `joint_optimization_report.md`, hasil ablation, prediksi OOF, manifest checkpoint/kode, rekomendasi satu kandidat terkunci.

## 8. Sprint 4 — OCR, evaluasi baru, XAI, dan delivery

**Prioritas:** P0 untuk OCR + target klasifikasi; P1 untuk QA aplikasi · **Estimasi:** 3–5 hari kerja aktif setelah kandidat terkunci.

### OCR

- [ ] Klasifikasikan kegagalan: text detection, line grouping, pemilihan headline vs teaser, dan character recognition.
- [ ] Audit `ocr_headline.py` aktual dan review kasus kegagalan yang telah diputuskan manusia.
- [ ] Uji crop adaptif, deskew, contrast, multi-pass OCR, dan candidate ranking tanpa lookup `image_id`/ground truth pada inference.
- [ ] Bandingkan exact match, CER/token-F1 sebagai metrik diagnostik, durasi P50/P95, dan confidence/risk flag.
- [ ] Lakukan evaluasi penerimaan baru pada data yang belum dipakai untuk diagnosis maupun tuning, dengan manifest dan selector terkunci sebelum read-once evaluation.
- [ ] **Hambatan data:** karena hanya ada 14 `other_issue` dan 8 sudah terlihat pada holdout 80, syarat 8 sampel baru per kelas tidak dapat dipenuhi seluruhnya dari 740 sampul yang sama. Cari gambar prospektif baru atau sepakati desain lain yang sah dan laporkan keterbatasannya.

### Evaluasi model dan aplikasi

- [ ] Kunci satu konfigurasi joint dan latih ulang dengan prosedur training-only yang ditentukan sebelum evaluasi final.
- [ ] Ukur pada data independen yang belum dilibatkan dalam perancangan model jika tersedia; bila tidak tersedia, tulis jujur sebagai internal OOF/CV, bukan klaim external holdout.
- [ ] Pastikan ketiga Task Macro-F1 `≥0,70` **secara masing-masing**, dari satu model dan protokol yang sama. Simpan seluruh prediksi.
- [ ] Uji input gambar baru → OCR → koreksi → fitur sesuai training → joint prediction → XAI visual/teks → batch/ekspor.
- [ ] Verifikasi XAI benar-benar berasal dari encoder, checkpoint, dan input model aktif; jangan hanya menyamakan tampilannya.
- [ ] Uji clean install Windows, browser Chromium + satu browser lainnya, uji pengguna manusia, dan regresi test (jika merupakan gate release).
- [ ] Buat manifest SHA-256, source/model/runtime dependency lock, dan laporan hasil maupun keterbatasan.

**Output:** `ocr_final_report.md`, `canonical_model_evaluation.json`, `oof_or_holdout_predictions.csv`, `release_qa.md`, `model_manifest.json`, `CHANGELOG.md` sesuai struktur repositori sebenarnya.

## 9. Jadwal kerja (estimasi, bukan janji selesai)

| Fase | Fokus | Estimasi aktif | Kondisi lanjut |
|---|---|---|---|
| Sprint 0 | Audit + provenance E42 | 1–3 hari | Baseline dan split dapat diaudit |
| Sprint 1 | Model alternatif + fitur | 3–6 hari | Kandidat teratas dipilih berdasarkan validasi |
| Sprint 2 | Augmentation + sampling | 2–4 hari | Hasil augmentation dibanding kontrol secara fair |
| Sprint 3 | Joint optimization | 3–6 hari | Kandidat joint terkunci atau batas kemampuan didokumentasi |
| Sprint 4 | OCR + independent acceptance + QA | 3–5 hari | Seluruh gate dinilai tanpa mengubah acceptance |

**Total indikatif:** 12–24 hari kerja aktif, belum termasuk waktu memperoleh dataset independen, memperoleh izin, menyiapkan environment/komputasi, dan memperbaiki blocker. Waktu riil tidak dapat dipastikan dari artefak yang tersedia.

## 10. Definisi selesai dan keputusan gagal

- [ ] Ketiga Macro-F1 minimal **0,70** pada satu joint model dengan evaluasi yang sah dan prediksi dapat direproduksi.
- [ ] OCR headline exact match minimal **80%** pada set penerimaan baru yang valid.
- [ ] Audit label, kelas minoritas, duplikasi, leakage, dan parity train–serve lengkap.
- [ ] Eksperimen model comparison dan data augmentation memiliki baseline, ablation, konfigurasi, prediksi, serta kesimpulan (termasuk hasil negatif).
- [ ] Model final, OCR selector, source, dataset/split, dan dependency tercatat beserta hash.
- [ ] XAI, alur aplikasi, clean install, browser, dan user test lulus sesuai gate release.
- [ ] Dokumentasi penelitian tidak mengklaim hasil yang belum diverifikasi.

Jika target tidak tercapai setelah anggaran eksperimen yang disepakati habis: **jangan menurunkan ambang 0,70 atau 80% secara diam-diam**. Hentikan grid search, analisis learning curve/error, ajukan tambahan data atau redefinisi ruang lingkup untuk persetujuan peneliti/dosen, dan pisahkan laporan keterbatasan dari klaim penerimaan.

## 11. Artefak yang belum tersedia dan diperlukan

**Blokir Sprint 0:** `e41_cached_tail/` (source pembuat cache, `README`, manifest), hasil/kode lengkap E48–E49, source predictor model aktif.  
**Blokir Sprint 2:** 740 gambar asli, bukan lima contoh sampul, beserta manifest/hash, serta informasi CPU/RAM/GPU/VRAM.  
**Blokir Sprint 4:** `02_web_demo/ocr_headline.py` versi terbaru, seluruh keputusan review OCR, dan tambahan sampul independen untuk pengujian final.

## 12. Struktur output eksperimen yang disarankan

```text
04_hasil_eksperimen/
  next_research_20261017/
    00_audit/
    01_model_comparison/
      M00_e42_baseline/
      M01_clip_indobert/
      M02_siglip2_indobert/
      M03_dinov2_indobert/
    02_augmentation/
      A00_none/
      A01_light/
      A02_moderate/
      A03_light_sampler/
    03_joint_optimization/
    04_ocr/
    05_final_evaluation/
    experiments_registry.csv
    frozen_protocol.json
    findings.md
```

Setiap eksperimen minimal menghasilkan `config.json`, `metrics.json`, `predictions.csv`, `manifest_sha256.json`, `run.log`, dan `decision.md`. Jangan menimpa artefak historis E01–E49.

## 13. Urutan tindakan pertama

1. **Baca E41 cache-generation + E48/E49.** Tutup ketidakpastian provenance dan cegah eksperimen duplikat.
2. **Bangun baseline audit otomatis** dari 740 OOF E42, confusion matrix dan laporan kelas sulit.
3. **Bekukan protocol penelitian berikutnya**, termasuk dataset/split, metrik, batas GPU, serta aturan seleksi.
4. **Siapkan seluruh gambar asli dan pipeline per-encoder** untuk memungkinkan augmentasi sah.
5. **Jalankan perbandingan model paling murah dahulu**, baru augmentation dan joint optimization.

**Keputusan inti:** target dipertahankan; kualitas bukti lebih penting daripada skor tertinggi dari eksperimen yang tidak sebanding.
