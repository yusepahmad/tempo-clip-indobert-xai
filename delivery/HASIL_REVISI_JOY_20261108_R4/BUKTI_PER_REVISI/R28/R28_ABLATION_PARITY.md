# Kontrak perbandingan ablasi

- Historical baseline family: CLIP-B32/IndoBERT CLS frozen, head256/dropout0.4/120 epoch. Weighted/unweighted/single-task/image/text berbagi input, seed, split dan anggaran yang dijelaskan dalam protokol.
- RII_TAIL family: CLIP-L14 full/crop + first10IndoBERT frozen + last2trainable, shared256/dropout0.3; LR2e-5/3e-4, fixed task loss1:2:2; epoch0/2/4/8 dipilih berdasarkan mean Macro-F1 inner2 fold. Canonical GPU FP32 reload diuji. Ini resep controlled baru, bukan grid E42 historis6 konfigurasi/24 epoch. Single-task terdiri dari tiga salinan independen dan memerlukan3×model/tuning head; biaya komputasi dicatat terpisah.
- E48 lama adalah LinearSVC dengan pencarian fitur/normalisasi/C, sehingga tetap diagnostik dan tidak dipakai sebagai bukti isolasi efek neural MTL. E49 routed-experts dan J01 hierarki dipertahankan sebagai varian arsitektur, bukan ablation yang hanya membedakan satu head.
- Frozen backbone controls baru memakai image768 + meantext768 sama, head/loss/seed/120 epoch sama; CLIP full-view, SigLIP2 dan DINOv2. M01lama memakai concatenationfull+crop2304 sementara M02/M03 memakai1536, sehingga klaim backbone lama bukan isolasi sempurna. Resolusi/pretraining encoder berbeda secara inheren dan dinyatakan.
- Tidak ada p-value yang diartikan sebagai ujiMacro-F1. Lihat paired bootstrap untuk selisihmacro dan exactMcNemar untuk akurasi.
