# E16 gerbang NON_METAFORA dan klasifikasi domain

**Tanggal:** 2026-10-10
**Status:** done

## Tujuan
Menguji apakah pemisahan keputusan literal/metaforis membantu klasifikasi tujuh kelas, setelah fusi E14 mencapai OOF0,5663. Target keseluruhan tetap Macro-F1 minimal0,70.

## Ruang Lingkup
- `DEMO_XAI_745_FULL/01_notebook/e16_hierarchical.py`, auditor `e16_hierarchical_verify.py`, hasil `04_hasil_eksperimen/e16_hierarchical/`, bukti recovery, plan/changelog.
- Input beku E5 description+reason, BGE combined, CLIP asli; transformer BlockFusion E14 dipakai tanpa perubahan. Satu CPU/BLAS1 di server learn; tidak menggunakan GPU atau mengubah E12/E15.
- Dataset, label, anotasi dan produksi tidak diubah. Deskripsi/mapping anotator bukan input.

## Langkah
1. Validasi hash sumber/data/fitur E14 yang sudah diaudit dan ID740; gunakan split outer baseline5 dan inner3 Task2 seed42.
2. Pipeline BlockFusion fit scaler hanya pada training; bobot BGE1/CLIP1 tetap, E5[0,5;2] dipilih inner.
3. Estimator hierarkis melatih SVC biner NON_METAFORA vs lainnya dan SVC enam domain hanya pada sampel metafora training. Gerbang memakai decision_function biner dengan ambang[-0,5;0;0,5]. C[1;10], gamma[scale;0,1], class_weight[None;balanced] bersama kedua head, total48 kombinasi. Seluruh parameter/ambang dipilih inner berdasarkan Macro-F1 tujuh kelas.
4. Refit outer-training dan prediksi outer-test sekali. Simpan semua skor grid inner, parameter/split/prediksi/checkpoint, lalu740 OOF dan laporan lengkap. Lock satu instance, resume hanya signature sama.
5. Auditor menghitung ulang inner-CV parameter terpilih dan mereproduksi seluruh prediksi refit; periksa argmax seluruh skor grid yang tercatat, split/ID/label/hash dan TP/FP/FN manual. Salinan bukti harus cocok hash sebelum klaim.

## Risiko & Asumsi
- Gerbang salah dapat memblokir domain benar; model ini bisa lebih buruk dari tujuh kelas langsung. Hasil tidak dijamin meningkat.
- Pemilihan eksperimen berulang berdasarkan hasil OOF membawa bias riset; target tidak dikejar dengan mengganti label/split atau memilih threshold dari outer-test.
- Skor grid disimpan untuk menelusuri keputusan, auditor mengulang parameter terpilih, bukan keseluruhan48 kombinasi.

## Verifikasi
Kompilasi, sklearn clone dan latihan kecil teknis untuk memeriksa gerbang/classes; audit hash/finite/alignment input aktual. Lima checkpoint,740 original IDs/labels/baseline folds, reproduksi fit/inner/prediksi, hitung ulang Macro-F1 dan hash salinan.

## Implementasi dan verifikasi awal
- Worker dan auditor dibuat/dikompilasi, SCP selesai sebelum launch; source hash lokal/server cocok: worker `c117f65e9460bccc4daeba0de9f3af4ee737e7ef65f57d39cca5a0910f8a3ece`, auditor `da45d08b4f7dd46a9548ab0f53413d6e165b8690adcb7985fa93ca908555d319`.
- Uji teknis memakai fitur asli terverifikasi740x3072 dan70 sampel (10/kelas): sklearn clone lolos, head biner70/domain60 sampel, ambang ekstrem menghasilkan semua NON_METAFORA atau tanpa NON_METAFORA sesuai arah gerbang. Ini bukan pemilihan kualitas.
- Proses full aktif di server`.31`, tmux `tempo-e16`, worker PID3089280, satu CPU. Protocol aktual sesuai grid48/inner3/outer5/hash referensi. Auditor dijalankan otomatis setelah worker exit0; log audit di luar folder hasil agar manifest tidak berubah saat audit mencetak hasil.
- Belum ada OOF lengkap atau skor baru. E12 berjalan, E15 menunggu slot; kandidat terbaik tetap E14 OOF0,5662691391.

## Hasil akhir
- Lima fold selesai dalam110,35/112,85/113,35/113,00/113,69s. Macro-F1 OOF **0,5533678354973841**, belum melampaui E14 atau mencapai0,70.
- Auditor aktual mengulang inner-CV parameter terpilih, mereproduksi740 prediksi dari refit outer-training, memeriksa48 grid/argmax/fold/head-count dan TP/FP/FN/confusion matrix. Ambang terpilih0 pada fold1–4 dan-0,5 fold5, seluruhnya dipilih inner.
- Bukti `docs/server-recovery/2026-10-10/e16_hierarchical/verification.json`, SHA256 `0a4a0e4e4f4c85277383e7ebb670bbd819ca65950de41127f1ee7eeb3ec0bec1`. Sembilan hash salinan cocok; penghitungan stdlib lokal terpisah mengonfirmasi Macro-F1/740 ID unik.
- Worker E16 terminal; E17 mulai setelahnya. E12 masih aktif, dataset/label/produksi tidak berubah, goal keseluruhan tetap aktif.
