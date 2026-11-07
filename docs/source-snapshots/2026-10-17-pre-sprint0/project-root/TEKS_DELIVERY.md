> Pembaruan Week 3 (2026-10-05): UI/input/XAI dan batch tersedia untuk review baseline. Lihat [panduan dan bukti Week 3](docs/DELIVERY_WEEK_3.md), termasuk cara batch/review/ekspor, diagnosis OCR dan penerimaan yang belum lengkap. Training baru belum diintegrasikan; definisi resmi lengkap belum terverifikasi.

# Teks Delivery — DEMO XAI TEMPO (Dataset Penuh 740 Sampul)

---

Halo,

Berikut hasil menjalankan ulang pipeline XAI dekoding metafora sampul Tempo,
kali ini dengan **dataset penuh (740 dari 745 sampul eligible)**, bukan lagi
subset 189 sampul di demo sebelumnya.

**Yang sudah dikerjakan:**
- Kategorisasi domain sumber metafora (Task 2) untuk 657 sampul bermetafora
  ke 6 domain (HEWAN_TUBUH, PERMAINAN_KONTES, MESIN_INFRASTRUKTUR,
  KONSUMSI_TRANSAKSI, BENCANA_JERAT, LAINNYA), konsisten dengan skema yang
  dipakai di dataset 189 sebelumnya.
- Ekstraksi fitur CLIP (visual) + IndoBERT (teks) untuk seluruh 740 sampul.
- Pelatihan model Multi-Task Learning + evaluasi 5-fold cross-validation
  untuk ketiga task.
- Analisis XAI: Grad-CAM (adaptasi untuk ViT), atribusi kata, dan analisis
  zona dominan (apakah model melihat ilustrasi atau logo/judul).

**Hasil Macro-F1 (naik dari versi 189 sampul):**

| Task | 189 sampul (lama) | 740 sampul (baru) |
|---|---|---|
| Task 1 — Isu utama | 0,316 | **0,438** |
| Task 2 — Domain sumber metafora | 0,191 | **0,320** |
| Task 3 — Tipe entitas sasaran | 0,213 | **0,276** |

Semua task tetap jauh melampaui majority baseline (baseline berkisar
0,036–0,075). Tidak ada kelas yang gagal total (recall 0 di semua kelas Task 2
pada versi 189 sudah tidak terjadi lagi di versi 740).

**Temuan XAI tetap konsisten dengan versi 189, bahkan menguat**: dari 25
sampul yang dianalisis (leave-one-out), 22 di antaranya model paling
bertumpu pada zona kepala sampul (logo dan judul kecil) — naik dari 19/25
pada versi 189 sampul. Intensitas rata-rata: kepala 0,180, ilustrasi tengah
0,086, kaki 0,060. Artinya kelemahan ini bukan artefak data kecil — penting
dilaporkan sebagai batasan, bukan disembunyikan.

**Isi paket (struktur sama seperti demo sebelumnya):**
```
01_notebook/      notebook asli + script Python yang dipakai untuk 740 sampul
02_web_demo/      aplikasi web (Flask), sudah diarahkan ke dataset 740
03_data/          CSV 740 sampul + cache fitur CLIP/IndoBERT
04_hasil_eksperimen/  metrik, recall per kelas, analisis zona, uji leave-one-out
05_gambar/        740 gambar sampul
```

**Sudah diuji end-to-end**: aplikasi web dijalankan, endpoint prediksi +
Grad-CAM + atribusi kata + penjelasan naratif dicoba langsung dengan sampul
dari dataset dan berjalan benar (heatmap PNG valid ter-generate, verifikasi
terhadap label anotator muncul).

Cara menjalankan sama seperti sebelumnya (lihat 01_TUTORIAL.md) — cukup
ganti nama file dataset ke versi 740 bila menjalankan manual.

Terima kasih.
