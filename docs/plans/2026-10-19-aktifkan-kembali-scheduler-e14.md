# Aktifkan Kembali Scheduler E14

**Tanggal:** 2026-10-19
**Status:** done

## Tujuan
Melanjutkan antrean evaluasi E14 yang sudah diizinkan pengguna: mengambil
hasil fold selesai, mengirim fold 5 ketika slot tersedia, lalu menunggu dan
memverifikasi sisa fold tanpa menduplikasi job.

## Ruang Lingkup
- Jalankan kembali scheduler yang ada pada
  `DEMO_XAI_745_FULL/01_notebook/next_research_20261017/kaggle_micro_e14/schedule.py`.
- Ledger/lock/log runtime dan hasil fold pada
  `DEMO_XAI_745_FULL/04_hasil_eksperimen/next_research_20261017/06_micro_f1/MICRO_E14_joint_qlora_oof/`.
- Job fold 5 version pertama di Kaggle melalui scheduler; pengumpulan hasil
  fold 4 dan fold berikutnya, agregasi/verifikasi otomatis saat semua selesai.
- Plan E14 utama, plan ini dan `CHANGELOG.md` setelah restart terverifikasi.
- Tidak mengubah kode/protokol training, konfigurasi fold, data, model aplikasi,
  job yang sudah terkirim maupun ZIP delivery.

## Langkah
1. Pastikan tidak ada scheduler aktif dan identitas build/protokol masih cocok.
2. Cek remote handle yang ada serta daftar kernel akun; pastikan fold 5 belum
   ada sebelum membiarkan scheduler mengirimnya dari state PENDING.
3. Jalankan satu scheduler persisten memakai ledger dan lock yang sama, log
   ke folder hasil, maksimum dua job aktif/antre seperti protokol awal.
4. Tunggu satu siklus untuk memverifikasi hasil fold 4 dan pengiriman fold 5;
   bila API gagal, pertahankan handle dan hindari retry push yang ambigu.
5. Konfirmasi PID, lock, ledger terbaru dan status Kaggle; catat hasil aktual.

## Risiko & Asumsi
- Saat cek terakhir fold 1–2 VERIFIED, fold 3 QUEUED, fold 4 COMPLETE di Kaggle,
  fold 5 PENDING lokal. Status diperiksa ulang sebelum restart.
- systemd user manager tidak dapat diakses pada environment ini; gunakan sesi
  proses persisten yang disediakan terminal. Ini tidak menjamin bertahan saat
  laptop/environment dimatikan; laptop/koneksi tetap diperlukan.
- Gangguan API/DNS dan antrean Kaggle tidak berarti training gagal. Tidak
  mengirim ulang fold yang sudah punya version/handle.
- Restart scheduler selesai bukan berarti lima fold atau target 0,70 selesai.

## Verifikasi
`assert_build()` harus lulus; ledger/protokol sama, satu proses scheduler
memegang lock, PID hidup setelah siklus pertama, fold 4 lolos verifier dan
fold 5 mempunyai version/handle terkonfirmasi bila push berhasil. Status live
Kaggle dan ledger harus konsisten. Hasil akhir hanya diklaim setelah 5 fold
terverifikasi dan tepat 740 OOF tersedia.

## Hasil Aktual
- Scheduler diaktifkan kembali pukul 19.41 WIB melalui sesi proses persisten,
  PID 20462. Ledger lama dipakai; exclusive lock terkonfirmasi dipegang proses.
- Hash worker, protokol dan seluruh launcher sesuai build manifest terkunci.
  Lima tes CPU protokol juga lulus. Kode training/scheduler tidak diubah.
- Fold 4 selesai diambil dan diverifikasi pada pukul 19.42 WIB: 148 outer-test,
  Micro-F1 Task 1/2/3 `0.709459 / 0.554054 / 0.709459`. Sumber, protokol,
  label, probabilitas, split dan pemilihan epoch/refit lolos verifier.
- Fold 5 berhasil dikirim sebagai version 1 pada 19.42 WIB; cek langsung
  Kaggle mengonfirmasi RUNNING. Fold 1–4 tidak dikirim ulang; seluruh handle
  tetap version 1. Fold 3 masih memakai job yang sama dalam antrean.
- Log persisten berada di `MICRO_E14_joint_qlora_oof/scheduler.log`.
- Restart selesai; evaluasi utama masih in-progress. Belum ada klaim hasil
  final 740 OOF atau target 0,70. Laptop/environment dan koneksi perlu tetap
  aktif untuk polling, pengambilan hasil dan agregasi otomatis.
- Dicatat pada `CHANGELOG.md`, `[Unreleased] / Added`.
