# Fine-Tuning Penuh Encoder CLIP+IndoBERT via Google Colab

**Tanggal:** 2026-09-29
**Status:** in-progress — notebook siap, menunggu dijalankan di Colab

## Tujuan

Dosen sudah meng-ACC Opsi B dari proposal Minggu 3
(`docs/plans/2026-09-22-timeline-3-minggu.md`): fine-tuning encoder
CLIP+IndoBERT, bukan lagi dibekukan sepenuhnya seperti sekarang. Tujuannya
menguji apakah performa model (Macro-F1 Task 2 saat ini 0,320) dan bias
zona logo (22/25 sampul bertumpu ke kepala sampul) membaik setelah encoder
ikut dilatih pada domain sampul Tempo, bukan hanya head MTL 330 ribu
parameter di atasnya.

Keputusan teknis yang sudah dikonfirmasi:
- **Full fine-tune** — seluruh ~276 juta parameter CLIP ViT-B/32 (termasuk
  text tower bawaan CLIP yang ikut termuat meski tidak dipakai) + IndoBERT
  dibuka, bukan partial unfreeze. Dikonfirmasi lewat dry-run CPU (lihat
  Verifikasi).
- **5-fold cross-validation penuh** — sama seperti evaluasi model beku
  sekarang, supaya Macro-F1 sebelum/sesudah bisa dibandingkan apel-ke-apel.
- **120 epoch per fold** — dipertahankan sama dengan model beku untuk
  perbandingan yang adil, walau risiko sesi Colab free tier (GPU T4, batas
  ±12 jam per sesi) terputus di tengah jalan diterima sebagai risiko yang
  harus diulang, bukan dihindari dengan checkpoint per-fold.
- **Dijalankan di Google Colab**, bukan di mesin lokal ini — mesin lokal
  hanya CPU 8-core tanpa GPU, tidak layak untuk full fine-tune 198M
  parameter × 5 fold × 120 epoch.

Dua sampul yang belum bisa diverifikasi karena filenya tidak ada di korpus
740 ("GULA-GULA DEMO BURUH" dan "CUKAI ABAL-ABAL ROKOK ILEGAL") akan
diminta dari dosen dan diuji ulang **setelah** model hasil fine-tuning
selesai dan diverifikasi — bukan sebelumnya, karena hasilnya baru berarti
kalau modelnya sudah final.

## Ruang Lingkup

**Disentuh (dibuat baru):**
- `01_notebook/finetune_encoder_colab.ipynb` — notebook baru khusus Colab:
  memuat data dari Google Drive, full fine-tune CLIP+IndoBERT dengan
  5-fold CV, menyimpan model per fold + metrik ke Drive
- `docs/plans/2026-09-29-fine-tuning-encoder-colab.md` — plan ini
- `docs/DELIVERY_WEEK_3_FINETUNE.md` — laporan hasil, dibuat setelah
  training selesai dan hasilnya ada

**Disentuh (menunggu hasil training dari Colab):**
- `04_hasil_eksperimen/hasil_mtl_740_finetuned.json` — hasil 5-fold CV
  model fine-tuned, ditaruh di sini setelah diunduh dari Colab
- `02_BATASAN_TEKNIS.md` — bagian performa model diperbarui dengan
  perbandingan sebelum/sesudah fine-tuning, setelah hasil ada
- `02_web_demo/xai_core.py`, `app.py` — **hanya jika** fine-tuning terbukti
  membaik: ganti pemuatan bobot encoder dari checkpoint fine-tuned. Bila
  tidak membaik, encoder beku tetap dipakai dan hasil dilaporkan sebagai
  eksperimen yang sah namun tidak diadopsi.

**Tidak disentuh:**
- `03_data/` — dataset 740 sampul tidak diubah
- Arsitektur `KepalaMTL` (shared layer + 3 head) — tetap sama, yang
  berubah hanya apakah encoder di bawahnya beku atau tidak
- Notebook demo `01_notebook/DEMO_XAI_TEMPO.ipynb` — tidak diubah sampai
  keputusan adopsi diambil
- Mode batch, dokumentasi Minggu 3 lainnya — dikerjakan terpisah

## Langkah

1. **Siapkan notebook Colab** (`finetune_encoder_colab.ipynb`):
   - Sel pemasangan pustaka (torch+cuda, transformers, open_clip_torch,
     scikit-learn) — dicek otomatis apakah GPU tersedia, berhenti dengan
     pesan jelas bila runtime bukan GPU
   - Sel mount Google Drive, load dataset 740 sampul + 740 gambar (perlu
     diunggah manual ke Drive oleh user sebelum menjalankan — didokumentasikan
     di sel markdown)
   - Definisikan ulang arsitektur: CLIP ViT-B/32 + IndoBERT + head MTL yang
     SAMA dengan `xai_core.py`, tapi `requires_grad=True` untuk seluruh
     encoder
   - Loop 5-fold CV: tiap fold, fine-tune 120 epoch, evaluasi, simpan bobot
     encoder+head ke Drive (`fold_{i}_model.pt`) dan metrik ke JSON
   - Sel ringkasan: bandingkan Macro-F1 tiap fold vs baseline beku
     (`hasil_mtl_740_task2domain.json`)
   - Sel opsional: re-run analisis zona Grad-CAM (22/25 kepala sampul) pada
     model fine-tuned, untuk lihat apakah bias logo berkurang

2. **Serahkan ke user untuk dijalankan di Colab** — saya tidak punya akses
   eksekusi Colab langsung dari sesi ini. User menjalankan, mengunduh hasil
   (`hasil_mtl_740_finetuned.json` + bobot model terbaik), lalu menaruhnya
   kembali di `04_hasil_eksperimen/` dan `02_web_demo/` (folder baru,
   misal `02_web_demo/model_finetuned/`)

3. **Setelah hasil ada**, saya:
   - Tulis `docs/DELIVERY_WEEK_3_FINETUNE.md` — bandingkan Macro-F1, recall
     per kelas, dan zona Grad-CAM sebelum/sesudah, dengan kesimpulan jujur
     (membaik / tidak membaik / campuran)
   - Perbarui `02_BATASAN_TEKNIS.md` bagian performa model
   - **Keputusan adopsi**: bila Macro-F1 Task 2 membaik signifikan tanpa
     overfitting parah (val loss tidak terus naik), integrasikan bobot
     fine-tuned ke `02_web_demo/`. Bila tidak, laporkan sebagai eksperimen
     negatif yang sah dan tetap pakai encoder beku di aplikasi

4. **Baru setelah itu**, minta dua sampul spesifik dosen ("GULA-GULA DEMO
   BURUH", "CUKAI ABAL-ABAL ROKOK ILEGAL") dan uji dengan model final
   (fine-tuned bila diadopsi, beku bila tidak)

## Risiko & Asumsi

| Risiko | Penanganan |
|---|---|
| Full fine-tune pada 740 sampul overfitting parah | 5-fold CV akan menunjukkannya lewat gap train/val yang besar; dilaporkan apa adanya, bukan disembunyikan |
| Sesi Colab free tier terputus sebelum 5 fold selesai | Diterima sebagai risiko (keputusan eksplisit: tidak pakai checkpoint per-fold). User perlu mengulang fold yang belum selesai secara manual bila terjadi |
| Hasil fine-tuning lebih buruk dari model beku | Tetap dilaporkan sebagai temuan sah — skripsi berbasis XAI menilai kejujuran pelaporan, bukan hanya angka akhir. Encoder beku tetap dipakai di aplikasi |
| Waktu training di Colab tidak dapat dipastikan dari sini (saya tidak menjalankannya langsung) | Notebook diberi estimasi kasar di sel markdown, tapi angka pasti hanya diketahui setelah user mencoba |
| Perubahan performa mengubah seluruh dokumen yang sudah dilaporkan (batasan teknis, delivery Minggu 2) | Dokumen Minggu 2 **tidak diubah retroaktif** — perbandingan sebelum/sesudah ditulis di laporan baru (`DELIVERY_WEEK_3_FINETUNE.md`), supaya jejak keputusan tetap runut |

**Asumsi:**
- User (Anda) yang menjalankan notebook di Colab, karena sesi ini tidak
  punya akses eksekusi GPU cloud
- Dataset (`03_data/`, `05_gambar/`) akan diunggah manual ke Google Drive
  oleh user sebelum menjalankan notebook
- ACC dosen mencakup risiko bahwa hasil fine-tuning bisa jadi tidak
  membaik — ini bukan jaminan sukses, melainkan eksperimen yang disetujui

## Verifikasi

1. Notebook Colab dapat dijalankan tanpa error pada runtime GPU T4 gratis.
   **Dilakukan sebelum diserahkan:** dry-run di CPU lokal memakai 4 sampul
   nyata dari dataset (bukan data sintetis) — dataset, dataloader, model
   `ModelFineTuned`, dan satu forward+backward pass dijalankan dengan kode
   yang identik dengan isi notebook. Hasilnya: shape cocok di semua titik
   (dim_img=512, dim_txt=768, gabungan=1280 — sama dengan model beku),
   logits per task benar (10/7/8 kelas sesuai), loss terhitung, dan gradien
   terbukti mengalir ke kedua encoder (total |grad| CLIP=3819,
   BERT=1017 — bukan nol, membuktikan full fine-tune benar-benar aktif,
   bukan cuma head yang terlatih). Total parameter terukur 276 juta
   (bukan 198 juta seperti estimasi awal — CLIP ViT-B/32 dari `open_clip`
   ikut memuat text tower bawaan yang tidak dipakai forward pass). Eksekusi
   penuh 5-fold × 120 epoch tetap harus dijalankan oleh user di Colab
   karena butuh GPU dan waktu berjam-jam.
2. Output 5-fold CV menghasilkan Macro-F1 per task, dapat dibandingkan
   langsung dengan `hasil_mtl_740_task2domain.json`
3. Ada laporan tertulis (`DELIVERY_WEEK_3_FINETUNE.md`) dengan kesimpulan
   jujur soal membaik/tidak, disertai angka pendukung
4. Keputusan adopsi (pakai bobot fine-tuned atau tetap beku) didasarkan
   pada data, bukan asumsi
