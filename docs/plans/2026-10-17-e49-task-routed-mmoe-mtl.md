# E49 Task-Routed MMoE Joint Multi-Task Model

**Tanggal:** 2026-10-17  
**Status:** done  

## Tujuan
Mengatasi masalah *negative transfer* antar-task pada model joint CLIP–IndoBERT (terutama Task 2 domain metafora dan Task 3 entitas yang tertekan di bawah 0,43 pada E42) dengan merancang dan menguji model joint baru berbasis **Multi-Gate Mixture of Experts (MMoE)** dan **Task-Specific Towers**, dengan tujuan meningkatkan Macro-F1 ketiga task menuju target wajib $\ge 0,70$.

## Ruang Lingkup
- **File/modul yang dibuat dan disentuh:**
  - `docs/plans/2026-10-17-e49-task-routed-mmoe-mtl.md` (dokumen plan ini)
  - `DEMO_XAI_745_FULL/01_notebook/e49_task_routed_mtl/model.py` (arsitektur MMoE + task-specific towers + adaptive routing)
  - `DEMO_XAI_745_FULL/01_notebook/e49_task_routed_mtl/train.py` (nested cross-validation 5 outer folds, pemilihan konfigurasi inner fold berbasis $\max \min(\text{Macro-F1})$)
  - `DEMO_XAI_745_FULL/01_notebook/e49_task_routed_mtl/verify.py` (audit deterministik OOF 740 sampel, metrik per task, dan pengecekan integritas)
  - `DEMO_XAI_745_FULL/04_hasil_eksperimen/e49_task_routed_mtl/` (direktori penyimpanan artefak OOF, metrik, dan verifikasi)
  - `CHANGELOG.md` dan dokumen roadmap terkait setelah eksperimen selesai.
- **Yang eksplisit TIDAK disentuh:**
  - Dataset `03_data/DATASET_740_TASK2_DOMAIN.csv` (label dan data sampul asli tidak diubah).
  - Outer fold E42 (pembagian 5 fold tetap identik demi keterbandingan yang sah).
  - Snapshot `delivery/` dan model aktif `clip-indobert-mtl-v1` di web demo (tidak ada promosi otomatis sebelum seluruh gate lulus).

## Langkah
1. Tulis plan ke `docs/plans/2026-10-17-e49-task-routed-mmoe-mtl.md`.
2. Buat direktori dan modul arsitektur `DEMO_XAI_745_FULL/01_notebook/e49_task_routed_mtl/model.py`:
   - Shared Multimodal Input: Visual multi-view (1536 dim) + IndoBERT text representation (768 dim).
   - Shared Experts: Kumpulan representasi nonlinear bersama.
   - Task-Specific Gating: Gate softmax terpisah untuk Task 1, Task 2, dan Task 3 yang mengatur proporsi kontribusi tiap expert secara dinamis.
   - Task-Specific Towers: Layer adaptasi lanjutan per task sebelum masuk ke classifier head.
   - Loss Function: Multi-task cross-entropy dengan *effective class-weighting* (square-root inverse frequency) dan label smoothing untuk menstabilkan kelas minoritas.
3. Buat script training `train.py` yang membaca cache `front_cache.npz`, menjalankan 5 outer folds dengan 3-fold inner cross-validation, serta memilih konfigurasi terbaik berdasarkan maksimasi nilai minimum Macro-F1 ketiga task.
4. Eksekusi training dan hasilkan OOF 740 sampel di `DEMO_XAI_745_FULL/04_hasil_eksperimen/e49_task_routed_mtl/oof.csv`.
5. Buat dan jalankan script audit `verify.py` untuk memverifikasi SHA-256 data, integritas OOF 740 sampel, dan menghitung Macro-F1 resmi per task.
6. Perbarui ranking kandidat model jika relevan, catat hasil aktual pada `CHANGELOG.md`, dan laporkan ringkasan ke pengguna.

## Risiko & Asumsi
- Pelatihan dijalankan pada CPU lokal; representasi cache `front_cache.npz` digunakan agar pelatihan efisien dan konvergen dalam waktu terukur.
- Gap menuju target 0,70 cukup besar (terutama Task 2 dan 3); eksperimen ini bertujuan memberikan lompatan arsitektural terarah berdasarkan bukti E48. Hasil dilaporkan apa adanya sesuai angka evaluasi OOF.
- Model tetap mematuhi kontrak Joint MTL: single end-to-end model, 3 heads, positive joint loss, gradien mengalir ke shared experts dari seluruh task.

## Verifikasi
- 740 sampel OOF terprediksi lengkap tanpa leakage (prediksi fold $k$ hanya berasal dari model yang dilatih pada fold $\ne k$).
- Metrik Macro-F1 dihitung ulang menggunakan `sklearn.metrics.f1_score(average='macro')`.
- Artefak `oof.csv`, `result.json`, dan hash tercatat di direktori eksperimen.
