# Goal completion gates — joint MTL CLIP–IndoBERT XAI

Tanggal2026-10-12. Goal aktif; belum selesai. Scope asli: ketiga task Macro-F1≥0,70 dan finaldeliverybersih/reproducible/XAI. Batas operasional terakhir tetap740sampul asli dan Kagglegratis, tanpa pembelian layanan otomatis.

| Persyaratan | Bukti yang diperlukan | Status saat ini |
|---|---|---|
| Task1 Macro-F1≥0,70 | PrediksiOOF seluruh740 + manualF1 + split/source/hash audit | Belum; best batchE33–E39 E37≈0,4851 |
| Task2 Macro-F1≥0,70 | BuktiOOF modelkandidat yangSAMA | Belum; best batchE33–E39 E39≈0,4348 |
| Task3 Macro-F1≥0,70 | BuktiOOF modelkandidat yangSAMA | Belum; E38≈0,3747 |
| Satu jointMTL CLIP–IndoBERT | Traininggraph sharednetwork/experts,3head,positivejointloss dan gradients | EksperimenE33–E40 memenuhi desain; checkpointcandidate perlu finaldipilih |
| XAI konsisten model | Visual/text explanations semua3task; perturbation/sanitychecks, modelhash matchesprediction | Baseline delivery ada; kandidatbaru belum terintegrasi |
| Unggahanbaru E2E | OCR/edit→preprocess→sameencoder/checkpoint→3prediksi→XAI→export; fixtures nyata | Baseline ada; kandidatbaru belum |
| Clean delivery | Pinnedenv, offline/publicweight strategy, install/run testedfresh, desktop/mobileQA, source/archive SHA | Baseline ZIP ada; model0,70 belum |
| Eksperimen jelas | Plans, changelog, code, config/splits, model/datahash, rawOOF, audit dan keterbatasan | E33–E43 audit lengkap; E43 0,4673/0,4246/0,3675; target belum |
| Resource/accountability | CPU/GPU provenance, quota status, no unintended paidcalls | Pay-to-scalefalse; E36GPU kini tidakditemukan, snapshot kuota terbaru6,51jam |

Tidak boleh menggabungkan bestscoreper-task dari modelberbeda lalu mengklaim satu model lulus. Pemilihan eksperimen berulang pada korpus sama harus dilaporkan; nestedCV bukan independentexternalholdout. Tidak mengubah label/split demi ambang0,70.

Finalcompletion hanya setelah SEMUA baris lulus dengan artefak/modelrelease yang sama. E40 menggunakan minimum across-task innerF1 sebagai objektif agar optimasi tidak mengorbankan task lain demiTask2.
