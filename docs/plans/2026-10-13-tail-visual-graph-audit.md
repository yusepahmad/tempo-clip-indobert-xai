# Audit jalur visual CLIP trained-tail MTL

**Tanggal:** 2026-10-13
**Status:** done

## Tujuan
Memeriksa rekonstruksi visual encoder E41 dari gambar dan gradien3task ke tensor piksel preprocessing, melanjutkan audit jalur teks.

## Ruang Lingkup
Utility `01_notebook/tail_graph_audit/visual_audit.py`, hasil audit/recovery dan changelog. Tidak mengubah source/checkpoint/cache E41/E42, data/label atau delivery. Satu heldout fold1 sebagai pemeriksaan awal; bukan sertifikasi XAI/fidelity.

## Langkah
1. Verifikasi hash bobot pinned CLIP E36, CSV/gambar/checkpoint E41.
2. Encode full dan crop dengan transform asli; bandingkan fitur dan logits terhadap cache.
3. Gradient ketiga task ke tensor2view piksel, finite/nonzero; classifier randomization sensitivity Task1. Simpan bukti dengan scope eksplisit.

## Risiko & Asumsi
Gradient pada224×224preprocessedviews tidak sama dengan raw image coords; overlay crop/resize alignment dan fidelity memerlukan pekerjaan tambahan. Text memakai tail cache untuk mengisolasi jalur visual. Audit satu sampel tidak membuktikan semua740 XAI.

## Verifikasi
Feature/logit tolerance2e-5,3task pixelgradients finite/nonzero, randomization sensitivity, model/image/source/checkpoint hashes. Tidak mengklaim quality0,70 atau finaldelivery.

## Hasil
Server CPU audit passed: satu heldout fold1, featuremaxabs1,64e-7 dan logitmaxabs1,52e-6; gradien3task padafull/crop finite/nonzero. Randomisasi classifierTask1 mengubah gradien. Bukti `04_hasil_eksperimen/e41_cached_tail/gpu/visual_graph_verification.json`. Rawcoordinateoverlay/fidelity tetap belum diaudit.
