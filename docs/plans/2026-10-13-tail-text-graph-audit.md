# Audit rekonstruksi full text graph tail IndoBERT

**Tanggal:** 2026-10-13
**Status:** done

## Tujuan
Membuktikan checkpoint tail MTL dapat direkonstruksi dari teks asli dan gradien ketiga task mencapai embedding token, sebagai langkah konkret menuju XAI delivery.

## Ruang Lingkup
- Utility baru `01_notebook/tail_graph_audit/`, hasil/recovery audit, changelog.
- Tidak mengubah source/weights/hasil E41/E42, data/label, aplikasi delivery.
- Audit teks saja; full pixel graph CLIP, fidelity explanation dan QA delivery tetap gate terpisah.

## Langkah
1. Muat snapshot IndoBERT pinned E41, verifikasi SHA; muat checkpoint terlatih dan gantikan dua layer terakhir.
2. Rekonstruksi teks asli, attention/special mask/mean/L2norm/shared3head; bandingkan logits fullgraph vs cached tail pada satu outer-heldout per fold.
3. Autograd sampai word embedding input untuk setiap task; finite/nonzero dan sanity randomisasi head pada sampel. Semua eval FP32 CPU.
4. Simpan checkpoint/model/source hash serta error/gradient checks. Laporkan ruang lingkup bukti dan keterbatasan.

## Risiko & Asumsi
Token embedding gradient belum berarti explanationfaithfulness; frozenweights tetap boleh mempropagasi gradient input. Visual cache tidak membuktikan pixelXAI. Audit kecil tidak membuktikan semua740 parity; audit OOF terpisah sudah tersedia.

## Verifikasi
Pinnedmodel/source/checkpoint SHA,5heldout logits tolerance2e-5,finite/nonzero token gradients3task dan randomized-head sensitivity. Hasil tidak dipakai memilih model.

## Hasil
Lulus5heldout (satu per fold) E41: maxlogitabs7,15256e-7. Gradien embedding token ketiga task finite/nonzero. Randomisasi classifierTask1 mengubah gradien pada5sample. SHA checkpoint/source/cache dipin. Bukti `04_hasil_eksperimen/e41_cached_tail/gpu/text_graph_verification.json`. Tidak membuktikan pixelXAI atau explanation fidelity.
