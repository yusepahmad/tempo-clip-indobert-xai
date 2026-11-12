# Delivery Week 3/4 — CLIP–IndoBERT Multi-Task Learning + XAI

Model utama seluruh task adalah **satu model joint MTL**, sesuai judul penelitian. E14 disimpan sebagai pembanding historis terpisah dan tidak diaktifkan oleh aplikasi ini.

## Default produksi E42

Backend `e42-tail-grid`, versi `e42-tail-grid-v1`: CLIP ViT-L/14 full/crop (2 × 768), IndoBERT front 10 blok frozen dan tail 2 blok terlatih, fusi 2304 → shared 256/ReLU/Dropout 0,3 → head 10/7/8 kelas. Lima checkpoint asli diverifikasi SHA-256; startup tidak melatih head. Dataset memakai fold held-out; unggahan merata-ratakan probabilitas lima fold. XAI memakai fold yang sama. Detail source dan deployment: [referensi HTML](../docs/e42_source_code_documentation.html) dan [Linux/Gunicorn E42](../docs/e42_production_deployment.md).

Bagian historis berikut khusus backend eksplisit `clip-indobert-mtl`; bukan perilaku default E42.

## Arsitektur baseline historis
- Gambar: CLIP ViT-B-32, pretrained `laion2b_s34b_b79k`, embedding 512 dimensi.
- Teks: `indobenchmark/indobert-base-p1`, CLS 768 dimensi dari headline [SEP] supporting, maksimum128token.
- Kedua embedding dinormalisasi L2 dan digabungkan (1280dimensi).
- Shared Linear1280→256/ReLU/Dropout0.4, lalu tiga head: isu10kelas, domain sumber7kelas, tipe entitas8kelas.
- **Encoder beku saat pelatihan; shared layer dan tiga head dilatih bersama**, bukan tiga classifier terpisah. AdamW lr0.001/weight_decay0.0001,120epoch,seed42. Loss rata-rata tiga cross-entropy dengan bobot kelas dihitung dari data latih.
- Identitas rilis `clip-indobert-mtl-v1`; metadata di `06_models/clip-indobert-mtl-v1/manifest.json`. Head dilatih ulang secara deterministik saat runtime; tidak mengklaim checkpoint fine-tuning encoder telah diintegrasikan.

## Hasil dan protokol baseline historis
| Task | Macro-F1 CV historis5fold |
|---|---:|
| Isu utama |0,4380|
| Domain sumber metafora |0,3197|
| Tipe entitas |0,2764|

Sumber `04_hasil_eksperimen/hasil_mtl_740_task2domain.json`,740sampul, stratifikasiTask1 dengan kelas langka digabung untuk split,seed42. Target0,70 belum tercapai. Angka0,5663 adalah hasil E14 (Qwen/E5/BGE/CLIP→SVC), **bukan skor model utama ini**. Arsip E14 lama dipertahankan terpisah di folder `week34_20261012`.

Analisis satu sampul dataset memakai leave-one-out head refit. Batch dataset memakai seluruh740sampul sebagai data latih (in-sample, eksplorasi). Unggahan baru juga memakai refit740 tanpa label pembanding. Ketiganya tidak boleh dilaporkan sebagai CV lima fold. Skor softmax belum dikalibrasi sebagai peluang benar. Metrik historis bisa berbeda saat dijalankan ulang pada versi/perangkat lain; bukti reproduksi disimpan terpisah.

## XAI dan alur aplikasi
Peta gambar mengambil |gradient×activation| token patch blok CLIP kedua dari belakang, diteruskan melalui head task pilihan. Ini bukan Grad-CAM CNN yang identik. Peta gabungan adalah rata-rata peta ketiga task yang dinormalisasi. LIME (120varian) atau occlusion mengubah headline melalui IndoBERT dengan supporting tetap. Semua XAI mengacu pada model MTL yang menghasilkan prediksi. Peta sensitivitas bukan bukti kausal atau bukti kebenaran tafsir metafora.

OCR EasyOCR mengisi headline/supporting untuk dikoreksi pengguna. Analisis menggunakan teks final yang dikonfirmasi. Narasi memakai templat bukti dengan asal MODEL/CODEBOOK/ANOTATOR. Batch unggahan menunggu review teks; CSV/JSON memuat versi model/protokol.

## Menjalankan Linux CPU

Untuk produksi E42/Gunicorn ikuti [panduan E42](../docs/e42_production_deployment.md). Launcher Linux memakai E42 bila `TEMPO_BACKEND` belum diatur; preflight OOF berjalan hanya untuk backend E42. `serve_tail.py` memilih E42 secara default, menjaga override dan mode Hugging Face offline. Satu worker menjaga satu pemilik model.

Instruksi instalasi berikut berasal dari lingkungan delivery historis; lihat versi aktual yang diverifikasi di panduan E42.
Python3.10.12 adalah lingkungan server yang diuji. Buat virtualenv, lalu:
```bash
python -m venv venv
venv/bin/python -m pip install torch==2.14.1+cpu torchvision==0.29.1+cpu --index-url https://download.pytorch.org/whl/cpu
venv/bin/python -m pip install -r requirements-delivery.txt
bash jalankan_linux.sh
```
Launcher default `127.0.0.1:7860`; gunakan `TEMPO_HOST`/`TEMPO_PORT` bila perlu. Environment `TEMPO_PYTHON` dapat menunjuk interpreter lain. Bobot publik CLIP/IndoBERT/EasyOCR diunduh saat pertama dibutuhkan; paket ZIP tidak menyertakan bobot encoder atau cache. Tidak memerlukan Qwen, E5, BGE, Kaggle, maupun API AI berbayar. Windows launcher tersedia tetapi belum diverifikasi dengan instalasi bersih.

## Pemeriksaan
`01_notebook/check_delivery.py` memeriksa data/metadata/inferensi head. Regresi Python/JS dan bukti inferensi/browser baru ada di `07_delivery_evidence`. Evaluasi fusion dapat direproduksi dengan `01_notebook/verify_mtl_cv.py`, hasil baru tidak menimpa metrik historis. Upgrade berikutnya harus mempertahankan CLIP–IndoBERT, joint loss tiga task dan XAI; versi dan skor harus diperbarui dari evaluasi yang sah, bukan substitusi model di luar judul.
