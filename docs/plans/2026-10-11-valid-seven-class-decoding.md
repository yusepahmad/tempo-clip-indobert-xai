# Evaluasi decoding dengan tujuh kelas valid

**Tanggal:** 2026-10-11
**Status:** done

## Tujuan
Memastikan prediksi akhir OOF740 berada dalam tujuh kelas Task2; output INVALID pada evaluasi format adalah diagnostik abstention dan tidak cukup untuk klaim target0,70. Tetapkan fallback sebelum membaca skor/truth evaluasi hosted, supaya error decoding juga dapat menghasilkan false-positive kelas fallback secara sah.

## Ruang Lingkup
- Tambahkan `DEMO_XAI_745_FULL/01_notebook/e18_hosted/evaluate_valid.py`, output baru `e18_hosted/valid/` strict/v1/v2, recovery dan changelog.
- Update auditor E19 `01_notebook/e19_fewshot/verify.py` sebelum inference untuk menghasilkan finalprediction tujuhkelas dengan rawprediction tersimpan. Update gate E19 agar memakai hasil valid E18 saat memeriksa target; worker E19 tetap belum dijalankan.
- E18 worker/watch/strict/v1/v2 evaluator tetap dan skor diagnostik tetap terpisah. Tidak mengganti response, prompt, model, dataset atau label. E20 SVC selalu menghasilkan tujuh kelas dan fitur INVALID tetap sah sebagai input-only category; tidak diubah.

## Langkah
1. Bekukan fallback: untuk setiap outerfold, hitung jumlah setiapkelas hanya pada592outertraining, pilih terbesar; tie urutan kelas alfabetis. Hanya prediksi rawINVALID yang diganti fallback. Bukan memilih kelas fallback berdasarkan skor/testtruth.
2. E18 evaluator valid membutuhkan strict740 verified dan setiap parser yang dievaluasi punya metrik/hash/sumber verified. Rekonstruksi baseline outer5 dan decode740 dari rawresponses; simpan rawprediction, finalprediction, fallbackclass serta applied flag perID. Semua route strict/v1/v2 dipertahankan, tidak memilih dari skor outertest.
3. Auditor E19 output menerapkan aturan sama pada rawprediction parserv2, mencatat invalidraw dan fallbacktraincounts. Kode/label trace tetap dari raw response; OOF final selalu tujuh kelas. Gate E19 menunggu tiga hasil valid E18 dan tidak lanjut jika ada kandidat minimal0,70 sebelum audit root.
4. Hitung confusion matrix7x7 dan Macro-F1 manual/sklearn lengkap740. Verifikasi train/test disjoint, fallbackcountclass dan final schema. Root wajib copy/hash/cekmanual sebelum klaim target. Skor abstention lama tidak menjadi bukti target.
5. Kompilasi/hash/gate incomplete. Uji sintetis majority/tie/train-only dan penanganan INVALID tanpa dataset target. Catat perubahan aktual ke changelog dan perbarui plan E19.

## Risiko & Asumsi
- Fallback adalah komponen yang belajar prior label training; namai protokol zero-shot+training-majority fallback, bukan purezero-shot. Mayoritas pada trainingfold boleh berubah antar fold.
- Skor diagnostik dengan labelsprediksi INVALID dan macro7 berbeda dari schema deployable7kelas. Jangan mengklaim target berdasarkan skor diagnostik tersebut.
- Tidak ada jaminan fallback menaikkan skor; tujuannya evaluasi yang sesuai kontrak tujuh kelas.

## Verifikasi
740prediksi final hanya tujuhkelas,148/fold,592training priors, manualmatrix/F1 sama sklearn, rawresponses immutable/hashmatch, outputterpisah, no requests tambahan. Target hanya dengan finalpipeline valid + audit independen lengkap.

## Hasil persiapan
Uji sintetis majority/tie/heldout-label-invariance/preservasi prediksi valid lolos, kompilasi/hash server cocok. Gate menolak strict740 belumverified tanpa membuat metrik valid atau inference E19. Source:
- `e18_hosted/valid_labels.py`: `8aea05534122e682399ce422c59cd66fcd2f3ee115655280a6f6b4490a59b6b4`.
- `e18_hosted/evaluate_valid.py`: `bcb8754aa2c9f7b81487b748b102bc307097f076bb5d19b27931000dc501e051`.
- `e19_fewshot/run.py`: `86f7801e5cf87de3600fb12be7db689398ebf27a72109d3218eb13fec584211a`.
- `e19_fewshot/verify.py`: `ec4eec85d32b73b32ecdcfe8557eb342a113605b3b9ffce9016957e240eb17a1`.
Evaluasi valid belum berjalan; menunggu all740/audit strict/v1/v2. Tidak ada klaim skor baru.
