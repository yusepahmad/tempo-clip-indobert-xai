# Protokol Terkunci dan Evaluasi Lima Fold Joint QLoRA

**Tanggal:** 2026-10-19
**Status:** done

## Tujuan
Mengukur Micro-F1 ketiga task dari satu prosedur joint QLoRA melalui 740
prediksi outer OOF, setelah pilot E13 menunjukkan kenaikan pada inner validation.

## Ruang Lingkup
- Eksperimen MICRO-E14 baru: frozen protocol, worker, generator launcher Kaggle
  per fold, scheduler maksimum dua sesi, collector/verifier OOF dan hasil.
- Dataset tetap 740, label dan outer folds E42 tidak berubah.
- Satu adapter bersama untuk tiga objective, sama dengan E13; input sah untuk
  inferensi, revision/model/dependency/transform/hyperparameter dibekukan.
- Runtime aplikasi dan arsip delivery yang sudah dibagikan tidak diubah.

## Langkah
1. Kunci protokol dan hash sebelum job E14 dikirim; simpan mapping 740 ID/fold.
2. Maksimum tiga joint epoch untuk seleksi pada inner split 80/20 masing-masing
   outer-training. Pilih maksimum minimum Micro-F1; mean sebagai tie-breaker;
   jika persis sama pilih epoch lebih awal. Tidak memilih dari outer-test.
3. Fold 1 memakai ulang history E13 epoch 1–3 dan initial adapter E13 hanya jika
   seluruh split, input audit, parameter dan sumber pilot cocok. Fold 2–5
   melakukan inner training baru; tidak memakai skor/label E13 untuk seleksi.
4. Reset adapter persis ke initial state, reset optimizer/scaler/RNG, refit pada
   seluruh 592 outer-training untuk jumlah epoch terpilih, lalu prediksi 148
   outer-test satu kali dengan satu adapter dan ketiga objective.
5. Simpan checkpoint tiap epoch agar kegagalan runtime tidak menghapus kemajuan.
   Dua slot batch maksimum; kelima fold dikirim berurutan saat slot tersedia.
6. Ambil artefak metrik/prediksi lebih dahulu. Gabungkan hanya setelah semua
   5 fold selesai; cek 740 ID unik, label, fold, source/protocol/data/feature
   hashes, dan micro=accuracy. Laporkan Macro-F1 juga.
7. Perbarui laporan/changelog berdasarkan hasil aktual; target tercapai hanya
   jika setiap task masing-masing Micro-F1 >=0,70 pada evaluasi lengkap.

## Risiko & Asumsi
- Kuota awal 21,86 jam GPU; estimasi 18–21 jam GPU dari throughput E13,
  bukan jaminan durasi. Antrean tidak memiliki ETA. Jika komputasi kurang,
  simpan hasil/checkpoint dan laporkan; jangan ubah protokol per fold.
- Batas tiga epoch dipilih dari pilot sebelum E14; tidak menggabungkan skor
  maksimum task dari epoch berbeda. Setiap fold memilih epoch training-only.
- Korpus sudah berulang kali dipakai riset dan pilot memengaruhi desain.
  Hasilnya internal CV dengan research-level selection bias, bukan pengujian
  independen baru. Termasuk pembatasan interpretasi atas reuse fold 1.
- Lima fold bukan jaminan peningkatan ke 0,70; Task 2 tetap bottleneck.
- Training hanya di Kaggle; laptop menjalankan validasi ringan/orchestration.
- Job aktif tidak diganti hanya karena polling timeout atau log belum tersedia.

## Verifikasi
- Decoder/reset adapter diuji lokal memakai tensor kecil dan model ber-buffer.
- Launcher memuat worker/protocol yang hash-nya sama dengan sumber terkunci.
- Split ID training/validation/test disjoint dan sama dengan protokol E42.
- Semua fold memakai protocol/source/hash yang sama dan satu adapter per fold.
- Verifier independen menghitung metrik dari CSV, memeriksa probabilitas,
  pemilihan epoch/refit/split dan hash; hasil parsial tidak menjadi klaim 740 OOF.

## Pelaksanaan
- Protokol terkunci SHA-256:
  `7b1eb1fdaf8547e842df793726e106b1d29b222b16ef3d9b672388d9d46ec65e`.
- Worker bersama SHA-256:
  `cb09acda21117f0acba38233fca382ec9916b08c5c73f297fa0f70c9469003ed`.
- Docker Kaggle dipin ke image E13; dependensi training dipin pada launcher.
- Lima tes CPU lulus: identitas payload, split/reuse, reset tensor trainable,
  urutan reset/refit/test, dan penolakan label CSV yang dimanipulasi.
- Fold 1–2 version 1 terkonfirmasi RUNNING. Fold 3–5 berada di antrean lokal.
  Scheduler aktif melalui sesi proses persisten dan memakai ledger/lock untuk
  mencegah job duplikat; status live perlu dibaca dari Kaggle dan proses lokal.
- Laptop harus tetap menyala untuk pengiriman fold lanjutan dan pengambilan
  hasil. Training Kaggle yang sudah terkirim tetap berjalan bila laptop offline.
- Proses penilaian lima fold masih berjalan; hasil akhir belum tersedia.

## Pembaruan 19 Oktober 2026 pukul 19.42 WIB
- Atas permintaan pengguna, scheduler yang tidak aktif dihidupkan kembali
  memakai ledger/lock yang sama, tanpa mengubah protokol atau mem-push ulang
  job lama (plan restart:
  [aktifkan scheduler](2026-10-19-aktifkan-kembali-scheduler-e14.md)).
- Fold 1, 2 dan 4 sudah VERIFIED lokal (masing-masing 148 outer-test).
  Fold 4 Micro-F1 `0.709459 / 0.554054 / 0.709459`.
- Fold 3 masih antre; fold 5 version 1 baru dikirim dan terkonfirmasi RUNNING
  langsung dari Kaggle. Scheduler PID 20462 aktif dan memegang exclusive lock.
- Hasil parsial tidak digabung menjadi klaim final; penilaian 740 OOF tetap
  menunggu kelima fold. Source/worker/launcher/protocol hash tetap terkunci.

## Penyelesaian 20 Oktober 2026 pukul 00.00 WIB
- Seluruh job COMPLETE di Kaggle; fold 3/5 sudah diambil dan kelima fold
  VERIFIED. Ledger complete; tepat 740 ID OOF unik tanpa duplikasi.
- Micro-F1 final `0.720270 / 0.566216 / 0.667568`; Macro-F1
  `0.673321 / 0.510282 / 0.595480`. Protokol/evaluasi selesai, target tiga task
  ≥0,70 belum tercapai. Task 2 tetap pembatas.
- Hitung ulang independen serta verifikasi hash/gambar/label/fold/input audit
  lulus. Tidak ada perubahan protokol/training atau pengiriman job baru.
- Ringkasan final:
  [hasil final E14](../HASIL_FINAL_MICRO_E14_2026-10-20.md).
- Plan pengambilan/verifikasi:
  [verifikasi final](2026-10-19-verifikasi-final-e14-oof.md).
