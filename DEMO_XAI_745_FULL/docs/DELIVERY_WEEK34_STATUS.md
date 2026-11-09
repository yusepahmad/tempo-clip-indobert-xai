# Status Week3/4 — penyelarasan CLIP–IndoBERT MTL

Tanggal12Oktober2026. Model utama `clip-indobert-mtl-v1`; satu shared representation dan tiga head dilatih bersama dengan encoder CLIP/IndoBERT beku. E14 hanya pembanding historis terpisah.

- Week3: alur OCR/koreksi teks, prediksi tiga task, XAI gambar/kata, narasi berbasis bukti dan batch dipertahankan.
- Week4: penyelarasan arsitektur, identitas/protokol seluruh task, paket delivery baru dan verifikasi E2E.
- Evaluasi fusion lima fold dijalankan ulang di server dan identik dengan sumber historis: Macro-F1 Task1 0,4380318985; Task2 0,3197261393; Task3 0,2763519250. Bukti `07_delivery_evidence/cv_reproduction.json`.
-85tesPython (termasuk dua tes joint MTL) dan empat skripJavaScript lulus. Bukti tersimpan di `07_delivery_evidence`.
- HTTP tiga task, unggahan baru, edit, LIME/occlusion, OCR, batch/review/ekspor, isolasi galat dan pembatalan lulus. Browser Chromium desktop/mobile lima tab dan unggahan foto dosen→OCR→koreksi→MTL→LIME→heatmap lulus tanpa page error. Layanan utama `.31:7862` sudah dipindahkan dan diverifikasi. Semua bukti baru ada di `07_delivery_evidence`, bukan diwarisi dari E14.

Target0,70 belum tercapai. Fine-tuning Kaggle bukan checkpoint aktif. Evaluasi pengguna manusia, instalasi bersih Windows, browser selain Chromium, dan holdout performa eksternal belum dibuktikan. Lihat [DELIVERY.md](../DELIVERY.md).
