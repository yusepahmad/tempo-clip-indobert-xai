# E33 — Optimasi joint CLIP–IndoBERT MTL menuju Macro-F1 Task2 0,70

**Tanggal:** 2026-10-12
**Status:** done

## Tujuan
Menguji peningkatan dari baseline Task2 0,3197261393 dengan mempertahankan dua encoder CLIP–IndoBERT, shared representation, tiga head dan joint loss. Target0,70 adalah sasaran, bukan hasil yang dijamin.

## Ruang Lingkup
- Kode `DEMO_XAI_745_FULL/01_notebook/e33_joint_mtl/` untuk model, nested evaluator, checks dan auditor.
- Hasil baru `04_hasil_eksperimen/e33_joint_mtl/`, salinan bukti `docs/server-recovery/2026-10-12/e33_joint_mtl/`, plan/changelog dan rencana fase selanjutnya.
- Tidak mengubah dataset/label, arsip E14, aplikasi utama7862 atau checkpoint delivery sebelum kandidat diverifikasi.
- Tahap pertama CPU server .31, tanpa hostedAI/API atau GPU berbayar. Pengguna mengizinkan GPU Kaggle hanya dalam kuota gratis. E33 tetap CPU; kuota aktual diperiksa, fase GPU memiliki plan terpisah sebelum eksekusi.

## Langkah
1. Audit fitur/label dan pola kesalahan baseline; bekukan grid dan split sebelum melihat hasil outer.
2. Implementasikan kandidat joint MTL: bobot loss Task2, regularisasi, kapasitas shared layer, bobot fitur visual, serta residual linear per task (tetap ada shared representation). Semua task memiliki bobot loss positif.
3. Gunakan 5outerfold identik baseline (Task1 strata, rare<5 pooled,seed42). Pemilihan24kandidat melalui2innerfold Task2,seed123, hanya pada outertraining. Lapor metrik ketiga task dan kontrol baseline yang dilatih pada outertraining yang sama.
4. Uji determinisme, pemisahan heldout, training-only classweights, gradient ketiga task ke shared layer, hash input dan baselineparity. Jalankan evaluasi dan audit OOF740.
5. Bandingkan dengan baseline menggunakan selisih dan pairedbootstrap eksploratif; simpan confusion/perclass/error audit. Kandidat belum dipromosikan otomatis; bila lebih baik, siapkan evaluasi multi-seed dan integrasi XAI tersendiri.
6. Berdasarkan hasil, tentukan fase fine-tuning terbatas/penanganan konflik gradien yang tetap sesuai judul, tanpa menjanjikan0,70.

## Risiko & Asumsi
- Fitur encoder beku dapat membatasi performa; mengganti head saja mungkin tidak cukup.
- Penggunaan korpus yang sama untuk banyak eksperimen berisiko selectionbias meski nested; belum ada holdout baru independen.
- Residual per task bukan pengganti shared MTL; ablasinya harus jelas.
- Bootstrap pada OOF bersifat eksploratif, bukan bukti signifikansi definitif karena foldtrain saling tumpang tindih.
- Pemeriksaan error menggunakan label hanya sesudah seluruh prediksi outer dikunci; tidak merevisi label untuk mengejar skor.

## Verifikasi
Inputhash sesuai release,740OOFmasing-masingsekali, semua split terpisah, innerindices subset outertrain, baselineparity semua task, repeatedfitfixture deterministik, perubahan labelheldout tidak memengaruhi fit, jointgradient dan perclassweightedloss. Auditor menghitung ulang metrik dan bootstrap stdlib/root independen. Sumber teori pembobotan/konflik MTL: https://arxiv.org/abs/1711.02257 dan https://arxiv.org/abs/2001.06782 (bukan klaim implementasi PCGrad pada E33).

## Progres
- Checks determinisme, perubahan fitur/label heldout, training-only weights dan gradient ketiga task ke shared representation lulus di server. Grid24dibekukan sebelum outerprediksi. Worker tmux`tempo-e33-mtl` berjalan CPU1thread; tidak mengubah demo utama.

## Hasil Aktual
-24konfigurasi,5outer×2inner selesai424,95detik CPU1thread. Task2MacroF1 **0,35301788013102264** vs0,3197261392590282 (delta+0,033291740872); Task1 **0,3950516289858456** turun dari0,4380; Task3 **0,3196467284962802** naik dari0,2764.
- Kontrolbaseline identik seluruh metrik historis. Auditor mereproduksi semua selectedinnerscores, selectedheadrefit5fold, baseline5fold dan740prediksi ketiga task; fullgrid tidak diulang auditor.
- Tidak ditemukan hashgambar/duplicategroup lintasfold yang sama. Root menghitung metrik manual stdlib dan pairedbootstrap2000replicates eksploratif; bukti terpisah`docs/server-recovery/2026-10-12/e33_joint_mtl/`.
- Target0,70 belum tercapai; kandidat belum mengganti delivery karena trade-offTask1 dan belum integrasiXAI. FaseE34 fine-tuning2blokterakhir dengan epochselectioninner-only telah disiapkan dan smoke dimulai memakai Kagglegratis yang diizinkan pengguna.
