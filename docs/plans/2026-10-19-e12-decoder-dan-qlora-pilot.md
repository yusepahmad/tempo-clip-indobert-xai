# Eksekusi Decoder Joint E12 dan Pilot QLoRA

**Tanggal:** 2026-10-19
**Status:** done

## Tujuan
Menguji decoder joint berbiaya CPU rendah terlebih dahulu, lalu pilot joint
QLoRA dengan training partition memadai untuk mengejar Micro-F1 tiap task 0,70.

## Ruang Lingkup
- Script MICRO-E12, hasil/config/prediksi/audit/manifest pada folder eksperimen
  baru; integrasi ranking dan laporan Micro-F1.
- Pilot QLoRA Kaggle terpisah dari smoke E07; seluruh inner-training fold 1,
  validasi epoch di inner-validation, outer-test tidak untuk tuning.
- Changelog dan plan aktif. Dataset, label, fold, runtime aplikasi dan ZIP
  delivery yang sudah dibagikan tidak diubah.

## Langkah
1. E12 membangun ulang stack klasik/Qwen/BGE/caption dari fitur frozen.
2. Dalam setiap inner split, seluruh stack (base cross-fit, base refit, meta
   head) dilatih hanya pada inner-training. Tidak reuse historical OOF.
3. Bandingkan head flat dan hierarkis Task 3; pilih smoothing, kekuatan prior
   joint dan marginal/MAP decoding berdasarkan minimum Micro-F1 inner.
4. Refit pipeline terpilih pada outer-training, evaluasi lima outer folds E42,
   simpan prediksi kontrol tanpa prior dan prediksi decoder.
5. Verifikasi hash, 740 ID unik, fold, metrik dan pemeriksaan isolasi label.
6. Siapkan dan jalankan pilot QLoRA dengan anggaran GPU dibatasi; keputusan
   perluasan lima fold hanya dari hasil inner-validation dibanding kontrol.
   Pilot MICRO-E13 menggunakan seluruh inner-training fold 1 (473 sampel),
   inner-validation 119 sampel, maksimal enam epoch bergantian task. Tidak
   melakukan refit maupun inferensi outer-test pada tahap pilot. Checkpoint
   terbaik, prediksi validation dan status intermediate disimpan tiap epoch.
7. Simpan hasil aktual, perbarui ranking/laporan dan changelog.

## Risiko & Asumsi
- Multiple testing pada 740 sampel tetap menyebabkan bias seleksi tingkat
  penelitian; hasil internal CV bukan validasi independen baru.
- Nested stack E10/E11 memiliki outer-test terpisah, tetapi meta inner CV
  menggunakan fitur cross-fit yang belum dibangun ulang untuk masing-masing
  meta-validation. E12 menggunakan nesting penuh untuk seleksi decoder.
- Prior dapat memperkuat bias kelas mayoritas; strength 0 menjadi kontrol.
- Hyperparameter base/head dibekukan sebelum E12; tidak memilih dari outer-test.
- Smoke E07 48 sampel belum cukup menolak QLoRA secara umum. Keputusan lama
  no-go hanya berlaku untuk mempromosikan konfigurasi smoke tersebut.
- Anggaran pilot maksimum 6 jam GPU; jika throughput tidak memadai, checkpoint
  dan ringkasan intermediate wajib disimpan.

## Verifikasi
- E12: tidak ada irisan train/eval pada tiap level; seluruh model dalam inner
  evaluation hanya menerima target inner-training.
- Verifikasi hasil CSV independen terhadap dataset dan folds; micro=accuracy.
- Prior strength nol identik dengan argmax probabilitas head.
- E07/pilot tidak diperlakukan sebagai bukti 740 OOF atau target tercapai.

## Hasil eksekusi sementara
- MICRO-E12 selesai: Micro-F1 `0,5784/0,5446/0,5108`; kontrol tanpa prior
  `0,5797/0,5500/0,5122`. Tidak dipromosikan; minimum terbaik historis tetap
  E11 `0,5324`.
- Verifikasi E12 lulus: 740 ID unik, label/fold identik sumber, 15 split inner
  disjoint, seleksi konfigurasi sesuai metrik inner, micro=accuracy, hash valid.
- E13 version 1 COMPLETE di
  `yusepmuhamadzazuli/tempo-micro-e13-joint-qlora-inner-pilot`; enam epoch selesai,
  epoch 3 dipilih berdasarkan minimum validation Micro-F1. Durasi 3 jam 41
  menit. Micro-F1 `0,7227/0,5882/0,6807`; minimum naik 9,24 poin dibanding kontrol.
- Prediksi/label/split/pemilihan epoch/hash dan Micro/Macro-F1 E13 cocok dengan
  log dan terverifikasi lokal. Lulus gate praktis pilot; bukan 740 OOF.
- Metrik/prediksi/log sudah diunduh. Transfer checkpoint besar tidak bergerak
  dan dihentikan lokal; checkpoint tetap tersedia pada output Kaggle. Tidak
  ada job training Kaggle yang dihentikan atau dijalankan ulang.
- Kontrol inner E13: Micro-F1 `0,5546/0,4958/0,5546`. Batas praktis lanjut:
  kenaikan minimum >=0,03 tanpa task turun >0,03, atau semua task >=0,70.
  Ini gate alokasi komputasi, bukan bukti statistik generalisasi.
- Evaluasi lima outer fold dengan protokol training yang dikunci merupakan
  pekerjaan berikutnya, belum dilaksanakan oleh plan pilot ini.
