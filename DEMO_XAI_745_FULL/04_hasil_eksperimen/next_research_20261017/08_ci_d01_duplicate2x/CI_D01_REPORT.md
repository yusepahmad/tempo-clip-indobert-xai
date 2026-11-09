# CI-D01 — hasil duplikasi training CLIP–IndoBERT 2×

Status: VERIFIED; dua arm, masing-masing740 prediksi OOF CPU FP32.

| Task | Macro-F1 1× | Macro-F1 2× | Delta pp | Micro-F1 1× | Micro-F1 2× |
|---|---:|---:|---:|---:|---:|
| Isu utama | 0.494619 | 0.495259 | +0.06 | 0.527027 | 0.531081 |
| Domain sumber metafora | 0.420814 | 0.390541 | -3.03 | 0.452703 | 0.424324 |
| Sasaran kritik | 0.385696 | 0.388486 | +0.28 | 0.502703 | 0.518919 |

Minimum Macro-F1 arm1×: **0.385696**. Semua task≥0,70: **False**.

Minimum Macro-F1 arm2×: **0.388486**. Semua task≥0,70: **False**.

Salinan persis, bukan1.480 sampel independen. Split berdasarkan ID sebelum duplikasi.
Kontrol berpasangan dengan resep tetap; tidak optimizer-step matched. Evaluasi internal pada korpus berulang, bukan test eksternal.
Canonical CPU checkpoint reload dijalankan worker Kaggle; checkpoint besar belum direplay lokal.
Tidak mengubah model web atau menganggap checkpoint CV sebagai model produksi.

Durasi worker tercatat: 317.567detik. RAM/VRAM/utilisasi: Not Recorded.
Result SHA256: `a010cbb0625da82d9df0379aa35bedee271d4b3771a180f921009e4e9c1f189a`.
Protokol SHA256: `404d4b233569250b8a1f9be1538615b863a12c39a58e4622787efee6d37eaf03`.
