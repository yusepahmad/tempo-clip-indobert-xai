# Ambil dan Verifikasi Final E14 Lima Fold

**Tanggal:** 2026-10-19
**Status:** done

## Tujuan
Mengambil hasil fold 3 dan 5 yang sudah COMPLETE di Kaggle, memverifikasi
kelima fold, lalu menghitung hasil final internal 740 OOF tanpa mencampur skor
pilot atau mengubah prosedur training.

## Ruang Lingkup
- Collector/verifier yang sudah ada di
  `DEMO_XAI_745_FULL/01_notebook/next_research_20261017/kaggle_micro_e14/`.
- Artefak fold 3/5, verifikasi ulang fold 1/2/4, agregat E14, ledger/log dan
  manifest pada `04_hasil_eksperimen/next_research_20261017/06_micro_f1/`.
- Rekap/ranking dan manifest siklus melalui `finalize_micro_f1.py`.
- Ringkasan final Markdown di `docs/`, plan E14 utama, plan ini dan changelog.
- Tidak mengubah data/label, worker/protokol/launcher training, model aplikasi,
  job Kaggle atau ZIP delivery. Tidak mengunduh checkpoint adapter besar.

## Langkah
1. Cek ledger, lock, hash build dan pastikan semua fold sudah punya handle
   version 1; tidak ada fold PENDING atau SUBMITTING yang bisa memicu push.
2. Jalankan satu siklus scheduler `--once` menggunakan ledger lama. Siklus
   mengambil hasil fold 3 dan 5, memverifikasi tiap fold, menggabungkan 740 OOF,
   memperbarui ledger complete dan menjalankan rekap ketika semua verified.
3. Verifikasi independen: hash dataset/protokol/source/prediksi, 740 ID unik,
   label dataset, fold yang benar, split disjoint, probabilitas/argmax, epoch
   terpilih dan refit; hitung ulang Micro-F1 serta Macro-F1.
4. Bandingkan hasil final dengan E11 (740 OOF), pisahkan dari E13 (119 inner
   validation), laporkan gate masing-masing metrik tanpa mengklaim keberhasilan
   sebelum hasil tersedia.
5. Simpan ringkasan final, perbarui plan/changelog dan periksa semua manifest
   hasil setelah pembaruan. Tidak menjalankan training baru.

## Risiko & Asumsi
- API/unduhan Kaggle bisa timeout. Jangan push ulang job yang sudah COMPLETE;
  bila perlu ulang hanya pengambilan/verifikasi artefak yang sama.
- Label/source/protokol yang tidak cocok harus menghentikan agregasi.
- Ini CV internal pada korpus yang berulang dipakai dan desain informed by
  pilot, bukan test eksternal baru; target Micro dan Macro tetap berbeda.
- Adapter hanya dicatat hash remote; tidak mengklaim checkpoint lokal sudah
  diuji karena tugas ini hanya mengumpulkan bukti evaluasi.

## Verifikasi
Kelima fold masing-masing 148 outer-test verified dan exactly 740 ID unik pada
agregat; hasil hitung ulang cocok JSON, hash manifest lulus, ledger complete,
tidak ada pengiriman kernel baru. Lima tes protokol CPU dijalankan ulang.
Target 0,70 dievaluasi per task untuk Micro-F1 dan Macro-F1 secara terpisah.

## Hasil Aktual
- Pengambilan dimulai 19 Oktober; selesai 20 Oktober 2026 pukul 00.00 WIB.
- Fold 3 dan 5 COMPLETE berhasil diambil, kelima fold diverifikasi ulang;
  ledger menjadi complete, seluruh handle tetap version 1. Tidak ada job baru.
- Tepat 740 ID unik / 5 × 148 test, label/fold/split/pemilihan epoch/refit dan
  probabilitas/argmax lulus; 740 gambar lokal cocok hash dataset dan audit input
  2.220 pasangan per fold identik antarfold.
- Hasil final Micro-F1 `0.7202702703 / 0.5662162162 / 0.6675675676`.
- Macro-F1 `0.6733214997 / 0.5102816960 / 0.5954802972`.
- Hitung ulang independen cocok JSON, 33 entry manifest E14/per-fold dan
  159 entry manifest siklus lulus; lima tes CPU protokol lulus.
- E14 terbaik pada ranking siklus MICRO menurut minimum Micro-F1, tetapi
  target ketiga task ≥0,70 belum tercapai. Hanya Task 1 lulus Micro-F1;
  seluruh Macro-F1 masih di bawah 0,70.
- Ringkasan: `docs/HASIL_FINAL_MICRO_E14_2026-10-20.md`.
- SHA-256 prediksi: `65590694cb53049daf266e491a447be49ebeba42a9d707147bfad80e50746167`.
- Changelog `[Unreleased] / Added` diperbarui. Model aplikasi/protokol/data,
  checkpoint remote dan ZIP delivery tidak diubah.
