# Model utama delivery — 12 Oktober2026

Keputusan pengguna: delivery harus sesuai judul eksperimen multi-task learning CLIP–IndoBERT berbasis XAI untuk dekoding metafora sampul majalah Tempo.

Model aktif `clip-indobert-mtl-v1`: CLIP ViT-B-32 pretrainedlaion2b_s34b_b79k + IndoBERTbasep1 beku → concat1280 → shared256 → tiga head joint loss. Ketiga task, unggahan baru dan XAI memakai model yang sama. Task2 Macro-F1 CV5fold0,3197261393; target0,70 belum tercapai. Hasil0,5663 adalah pembanding E14, bukan hasil model utama.

- Demo utama: http://10.12.1.31:7862
- Sumber lokal: `delivery/week34_clip_indobert_20261012/DEMO_XAI_745_FULL/`
- Sumber server: `/home/research-user/workspace/learn/delivery_week34_clip_indobert_20261012/DEMO_XAI_745_FULL/`
- tmux: `tempo-week34-ui`; log parentfolder `ui_main.log`.
- Interpreter yang sudah diuji: `/home/research-user/workspace/learn/delivery_week34_20261012/venv_clean_delivery/bin/python`; penggunaan environment ini tidak mengaktifkan kode E14.
- ZIP utama: `delivery/week34_clip_indobert_20261012/tempo-week34-clip-indobert-mtl-v1-linux.zip`, checksum dan bundle_verification.json di folder yang sama.
- Bukti baru: `07_delivery_evidence/release_verification.json`, CV, regresi dan HTTP/browser/deployment.
- Arsip pembanding E14: `delivery/week34_20261012/tempo-week34-e14-v1-linux.zip`, dipertahankan tanpa perubahan; tidak lagi layanan utama.
- Panduan lengkap: `DELIVERY.md` di paket baru. Upgrade selanjutnya harus mempertahankan arsitektur sesuai judul, dievaluasi dengan split/protokol yang sah dan diperbarui identitas/skornya secara transparan.

Rincian perubahan: [plan penyelarasan](plans/2026-10-12-align-delivery-clip-indobert-mtl.md) dan CHANGELOG root.85tesPython/4skripJS, reproduksiCVidentik, HTTP/browser desktop/mobile dan unggahan baru lulus. Environment bersih tersedia digunakan kembali. Windows/uji manusia/holdout eksternal belum dibuktikan.
