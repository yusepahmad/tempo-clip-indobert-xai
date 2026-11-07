# E17 jumlah kernel per modalitas

**Tanggal:** 2026-10-10
**Status:** done

## Tujuan
Menguji gabungan kemiripan per blok sebagai alternatif RBF pada konkatenasi E14. Jumlah kernel dapat memakai kedekatan salah satu modalitas tanpa mensyaratkan kedekatan bersama seluruh blok. Target tetap OOF Macro-F1 minimal0,70.

## Ruang Lingkup
- `DEMO_XAI_745_FULL/01_notebook/e17_additive_kernel.py`, auditor terpisah, output `04_hasil_eksperimen/e17_additive_kernel/`, recovery, plan/changelog.
- Input asli terverifikasi E14 (E5/BGE/CLIP), transformer E14 tanpa perubahan. Tidak memakai prediksi OOF sebagai fitur, anotasi deskripsi/mapping, atau mengubah data/label/produksi.
- Persiapan saat E16 aktif; full baru dijalankan setelah E16 terminal. Satu CPU/BLAS1, tidak menyentuh GPU atau penjadwal E12/E15.

## Langkah
1. Fit StandardScaler dan L2 per blok melalui pipeline hanya pada training; semua bobot transformer1.
2. Kernel K=(wE5*RBF(E5)+RBF(BGE)+wCLIP*RBF(CLIP))/(wE5+1+wCLIP). Gamma bersama[0,1;1;10], wE5[0,5;2], wCLIP[0,5;1;2]. SVC precomputed C[1;10;100], class_weight[None;balanced];108kombinasi dipilih inner3 Task2 seed42, outerbaseline5.
3. Simpan semua skor grid/argmax, split/prediksi/checkpoint/protocol dengan lock dan signature. Refit outer-training kemudian prediksi outer-test sekali, total740 OOF.
4. Auditor menghitung ulang inner-CV parameter terpilih dan mereproduksi740 prediksi, memeriksa argmax grid/split/hash/ID/label dan Macro-F1 manual. Salinan hash cocok sebelum klaim.

## Risiko & Asumsi
- Penjumlahan kernel berbobot positif mempertahankan kernel valid, tetapi dapat menambah noise. Tidak menjamin skor meningkat.
- Ukuran kernel740 kuadrat cukup kecil; n_jobs/BLAS dibatasi1. Tidak ada normalisasi dataset penuh sebelum inner-CV.
- Pemilihan antar eksperimen tetap membawa bias riset. Skor outer tidak dipakai memilih parameter/ambang di fold yang sama.

## Verifikasi
Kompilasi, clone dan kernel simetris/finite/diagonal1/PSD toleransi numerik pada subset teknis; prediksi train/test dalam jalur precomputed konsisten. Hash input aktual; audit lima fold/740 OOF, manualF1 dan salinan.

## Persiapan
- Worker/auditor dibuat, dikompilasi dan disalin; SHA256 lokal/server cocok: worker `4df108144085009a1ecbbe332a9ea724165218a39eb5f106e9966fdca78da7f5`, auditor `afa9b6c51f835f8365fe536c78f5660d495fb72afe11ab1f15852a7e1ddb6bc4`.
- Uji70 sampel dari fitur asli terverifikasi lolos clone, kernel simetris/finite/diagonal1/PSD toleransi1e-8 dan prediksi pipeline identik jalur precomputed langsung. Tidak menilai kualitas dari subset teknis.
- Belum launch full, menunggu E16 terminal. Tidak ada skor OOF E17 atau tambahan GPU.

## Eksekusi
- E16 sudah terminal dengan audit lengkap sebelum launch E17. E17 aktif di server`.31`, tmux `tempo-e17`, worker PID3189634, satu CPU/BLAS1. Worker exit0 diteruskan ke auditor otomatis; log audit berada di luar folder manifest hasil.
- Protocol aktual sesuai source hash/inner3/outer5/n_jobs1; seluruh input diverifikasi sebelum pencarian. Belum ada OOF lengkap atau skor E17.

## Hasil akhir
- Kelima fold selesai dalam41,83/40,45/40,63/40,54/40,83s. Macro-F1 OOF **0,5342455302949545**, di bawah E14 dan target0,70.
- Auditor actual mengulang inner-CV parameter terpilih, memeriksa seluruh108 parameter/argmax yang tercatat, mereproduksi740 prediksi refit outer-training, menguji kernel subset finite/simetris/diagonal1/PSD dan menghitung TP/FP/FN/confusion matrix secara manual. Tidak mengulang keseluruhan grid.
- Bukti `docs/server-recovery/2026-10-10/e17_additive_kernel/verification.json`, SHA256 `2d46e235e66f31bcf5b43e8531958b3962eb4aa6a629ab0418ea231533e21002`. Sembilan hash salinan cocok; stdlib lokal mengonfirmasi740 ID unik dan Macro-F1.
- Hasil terbaik tetap E14 keluarga fusi0,5662691391. E12 masih aktif dan E15 menunggu slot, goal keseluruhan tetap aktif. Dataset/label/produksi tidak berubah.
