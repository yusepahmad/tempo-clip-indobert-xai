# Penahanan akses hosted untuk klarifikasi tagihan

**Tanggal:** 2026-10-11
**Status:** done

## Tujuan
Mencegah request hosted tambahan setelah pengguna melaporkan tagihan, dan mencatat batas bukti biaya yang tersedia.

## Ruang Lingkup
- Proses E18 PID1176994 dan pembaruan akses PID1290147 pada server .31; plan ini dan CHANGELOG.md.
- Tidak mengubah dataset, label, protokol evaluasi, kredensial, atau metode pembayaran. Tidak memulai inference baru.

## Langkah
1. Verifikasi status proses E18 yang sudah ditahan sebagai mitigasi langsung.
2. Tahan proses pembaruan token tanpa menghapus akses/cache.
3. Catat bukti status dan pemakaian kuota; tunggu informasi layanan, nominal, dan tanggal tagihan dari pengguna sebelum melanjutkan hosted.
4. Revisi setelah pengguna mengonfirmasi Kaggle gratis dan meminta verifikasi ulang: bila sumber resmi menyatakan akses gratis dalam kuota dan endpoint aktual cocok Kaggle, buka penahanan proses asli berdasarkan otorisasi eksperimen sebelumnya. Tetap budget6USD, saldo minimum, cache/no-retry dan audit kuota; tidak membeli kredit atau menambah metode pembayaran. Invoice lain tetap belum teridentifikasi.

## Risiko & Asumsi
- Nilai pemakaian kuota bukan bukti penagihan kartu. Metode pembayaran dan invoice belum diketahui.
- Satu request yang telah dikirim sebelum penahanan dapat selesai di backend; tidak boleh diulang otomatis.
- Token dapat kedaluwarsa saat ditahan. Kelanjutan memerlukan pemeriksaan akses dan cache terlebih dahulu.
- Evaluator CPU E15 yang telah berjalan tidak memanggil API model dan dapat terus berjalan.

## Verifikasi
- ps memastikan kedua PID berstatus T; tidak melakukan SIGCONT atau request model.
- Pembacaan kuota sebelumnya menunjukkan used USD1.1275505, daily remaining8.8724495 dan monthly remaining98.8724495. Angka ini bukan konfirmasi invoice.
- E15 PID586083 terkonfirmasi R+; hasil final belum tersedia saat pemeriksaan.

## Hasil verifikasi ulang
- Pengguna meminta verifikasi ulang setelah menemukan bahwa Kaggle gratis. Pengumuman resmi Kaggle Staff menyatakan akses model gratis dalam batas kuota: https://www.kaggle.com/discussions/product-announcements/667898 . Dokumentasi resmi CLI menjelaskan angka USD sebagai inference spend Model Proxy: https://github.com/Kaggle/kaggle-cli/blob/main/docs/benchmarks.md .
- Pembacaan API terbaru: used USD1.1230505, daily remaining8.8769495/total10 dan monthly remaining98.8769495/total100. Nilai backend berubah dari pembacaan sebelumnya; sebab koreksi tidak diketahui, tidak menganggapnya invoice atau refund.
- Host konfigurasi diperiksa tanpa mencetak key: mp-staging.kaggle.net. Worker memakai MODEL_PROXY_API_KEY untuk /openapi/chat/completions, model google/gemini-3-flash-preview. Tidak memakai endpoint Gemini langsung pada worker ini.
- Kesimpulan: jalur eksperimen yang diperiksa menggunakan kuota gratis Kaggle dan masih dalam batas kuota. Sumber tagihan yang sempat dilaporkan tidak dapat ditentukan dari bukti ini.
- Kedua PID masih berstatus T. Tidak ada request inference baru atau pembukaan penahanan pada verifikasi ini.

## Kelanjutan setelah verifikasi gratis
- Preflight proses asli masih T, E18 progress298/740 cost1.1206325; endpoint dan batas kuota sudah terverifikasi. Resume hanya PID yang sama, pembaruan akses dahulu, lalu worker; tidak restart request yang tak pasti. Bila audit kuota gagal, biarkan worker berhenti dan periksa cache sebelum tindakan lanjut.
- SIGCONT kedua PID asli selesai; ps menunjukkan worker Sl+ dan akses S+. Log299/740 cost1.1230505 membuktikan respons tertunda tersimpan dan audit kuota lolos tanpa retry. Watcher1202764 tetap S+. Penahanan sementara ditutup setelah sumber gratis diverifikasi; kelanjutan eksperimen mengikuti plan E18. Sumber invoice lain tetap tidak diketahui, tidak ada klaim audit rekening pengguna.
