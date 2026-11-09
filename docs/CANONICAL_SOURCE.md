# Source Canonical

**Diperbarui untuk Revisi II:** 1 November 2026  
**Basis sinkronisasi historis:** 17 Oktober 2026  
**Source kerja:** `DEMO_XAI_745_FULL/`  
**Snapshot basis sinkronisasi 17 Oktober:**
`delivery/week34_clip_indobert_20261012/DEMO_XAI_745_FULL/`

## Model penelitian Revisi II dan runtime historis

- Model utama penelitian: `e42_tail_grid` (alias prediksi M00), CLIP-L14
  full/crop beku, IndoBERT first10 beku dan last2 trainable, shared256 dan tiga
  head dengan Joint Loss berbobot tetap. Macro-F1 Task1/2/3:
  `0,525483 / 0,395560 / 0,403398`; rerata `0,441480`.
- Penetapan dilakukan post-hoc pada korpus yang dipakai berulang, berdasarkan
  rerata Macro-F1 kandidat yang memenuhi arsitektur proposal. Minimum hanya
  diagnostik; akurasi dan kappa menjadi pendamping. Tidak memakai gate absolut
  0,70 untuk keputusan revisi baru.
- Bukti dan batas penetapan: `docs/revisi-ii/MAIN_MODEL_DECISION.md` serta
  `MAIN_MODEL_DECISION.json`. Sumber evaluator baru:
  `DEMO_XAI_745_FULL/01_notebook/revisi_ii/`; hasil turunan dan rerun:
  `DEMO_XAI_745_FULL/04_hasil_eksperimen/revisi_ii/`.
- Model web di bawah tetap runtime historis. Belum ada promosi E42 ke layanan
  aktif atau klaim skor CV sebagai akurasi demo refit. Qwen adalah pembanding.

## Runtime web historis yang tetap aktif menurut dokumentasi

- ID: `clip-indobert-mtl-v1`
- Arsitektur: CLIP ViT-B/32 + IndoBERT beku, fitur gabungan 1280 dimensi,
  shared layer 256, dan tiga head yang dilatih bersama.
- Task 1 Macro-F1: `0.4380318985`
- Task 2 Macro-F1: `0.3197261393`
- Task 3 Macro-F1: `0.2763519250`
- Protokol angka: historical five-fold CV pada 740 sampul.
- Target proposal historis 0,70: belum tercapai; kriteria revisi baru bersifat
  komparatif. Status layanan live tidak disimpulkan hanya dari dokumen ini.

Manifest model berada di
`DEMO_XAI_745_FULL/06_models/clip-indobert-mtl-v1/manifest.json`.

## Sinkronisasi Sprint 0

Lapisan runtime/release berikut dipindahkan secara identik dari snapshot
terverifikasi ke source canonical:

- `02_web_demo/app.py`
- `02_web_demo/batch_jobs.py`
- `02_web_demo/explanation_evidence.py`
- `02_web_demo/index.html`
- `02_web_demo/mtl_engine.py`
- `02_web_demo/ocr_headline.py`
- `02_web_demo/xai_core.py`
- `06_models/clip-indobert-mtl-v1/manifest.json`
- launcher, requirements, dokumen onboarding, dan test/verifikator release.

Eksperimen E02–E47 yang hanya terdapat pada source utama dipertahankan. Folder
evidence dan snapshot delivery tidak disalin menjadi source kerja.

Source runtime sebelum sinkronisasi disimpan di
`docs/source-snapshots/2026-10-17-pre-sprint0/` agar perubahan dapat diaudit dan
dipulihkan tanpa menyentuh release historis.

## Kontrak R5

Peta utama UI adalah `heatmap_padu_url`, yaitu gabungan peta ternormalisasi
ketiga task. `heatmap_url` tetap ditampilkan terpisah sebagai bukti untuk task
dan kelas yang sedang dijelaskan. Peta task pilihan tidak boleh diberi label
sebagai peta gabungan.

## SHA-256 runtime canonical

```text
bdf8b0878c89653f11b63a6b30b81f5dcf7924cfbecd1016b84b6aa59dea00ee  02_web_demo/app.py
2587a01c8987f39b6f0bff3de76fe64f44477f3cf794d61704677e5031cbed03  02_web_demo/batch_jobs.py
c463c9ca62f663fcaed3ae89218d6c873861b86119ef24d2a6d03b441ba70864  02_web_demo/explanation_evidence.py
a1538c7ff68b3c9da2d1f95d9887e8db7a1bd121058c92a331d5f9d11d40ef7d  02_web_demo/index.html
9b69377dbf25411135e4306ef480eeaeab35c4eb2f9fe74967ec10bb6d84000d  02_web_demo/mtl_engine.py
e29a38200b0d9126a3c9c320c5bc27f1e977a335092ecafd72fbdd328e233175  02_web_demo/ocr_headline.py
66ad4451d0943740c6c5ba3a61a690d8f98d8414afea75b045fd2e3cd07e7fac  02_web_demo/xai_core.py
df07f5be9d04a7bd6ce1f208db6682fcbae2c81e7ca6b1637a3207411959bb3d  06_models/clip-indobert-mtl-v1/manifest.json
```

## Verifikasi Sprint 0

- Paket/model: `check_delivery.py` lulus.
- Joint MTL: 2 test lulus.
- Batch error: 2 test lulus.
- Narasi: 10 test lulus.
- OCR ordering: 16 test lulus.
- Regresi Week 3: 4 test lulus setelah test lama diselaraskan dengan kontrak
  release.
- Audit backend: 33 test lulus.
- HTML5: 4 test lulus.
- Training audit fixture: 1 test lulus.
- JavaScript R5, loading/state, dan workspace navigation: lulus.
- HTTP R5 model nyata: lulus; peta gabungan identik antar pilihan task dan peta
  task berbeda untuk ketiga head.

Suite browser Python belum dijalankan ulang karena modul `playwright` tidak
terpasang pada environment lokal. Bukti browser desktop/mobile release lama
tetap tersedia di snapshot delivery, tetapi tidak diklaim sebagai run baru
Sprint 0.
