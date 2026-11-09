# Urutkan Skor Prediksi dan Delivery Windows R3

**Tanggal:** 2026-10-19
**Status:** done

## Tujuan
Mengurutkan baris tabel Prediksi tiga task dari persentase model tertinggi
ke terendah sesuai tangkapan layar pengguna, lalu mengirim ZIP Windows terbaru.

## Ruang Lingkup
- `DEMO_XAI_745_FULL/02_web_demo/index.html`: urutan tampilan tabel prediksi.
- Tes regresi di `DEMO_XAI_745_FULL/01_notebook/` untuk sorting dan render tabel.
- `delivery/update_20261019/build_latest_windows.py`: release R3, laporan dan
  verifikasi paket; output baru `clean_windows_r3/` agar R2 tetap tersedia.
- Plan ini dan `CHANGELOG.md` setelah perubahan selesai.
- Tidak mengubah skor, model, pemetaan task/kelas, data, training Kaggle,
  urutan panel XAI lainnya maupun paket lama.

## Langkah
1. Periksa renderer dan pola tes frontend yang tersedia.
2. Urutkan salinan entry prediksi berdasarkan skor numerik menurun; bila sama
   pertahankan urutan asal, skor tidak valid ditaruh terakhir. Tampilkan
   penjelasan singkat bahwa tabel sudah terurut dan skor belum dikalibrasi.
3. Uji contoh 30,4% > 27,0% > 17,7%, angka string, nilai sama/tidak valid,
   label tetap berpasangan dan input prediksi tidak berubah; jalankan regresi UI.
4. Buat ZIP Windows R3 dengan source UI baru, laporan terbaru dan bukti hasil;
   cek CRC, hash, konten UI dalam ZIP dan runtime hasil ekstraksi.
5. Catat hasil aktual, checksum dan tes pada plan/changelog, lalu berikan ZIP.

## Risiko & Asumsi
- Permintaan diartikan mengurutkan tiga baris task pada tabel yang dilingkari,
  bukan mengubah prediksi atau memilih model dengan skor lebih tinggi.
- Pengurutan hanya presentasi; persentase antartask bukan peluang benar yang
  sudah terkalibrasi dan tidak mengubah task yang dipilih untuk penjelasan XAI.
- Status training dalam laporan adalah snapshot, bukan hasil final E14.
- Instalasi Windows bersih tetap memerlukan pengujian pengguna.

## Verifikasi
Tes Node untuk helper/renderer sorting dan regresi frontend yang relevan;
bila browser tersedia, cek render tabel pada browser dengan respons fixture
tanpa menjalankan inferensi berat. Verifikasi manifest SHA-256, CRC, source UI
terbaru dalam ZIP, laporan luar/dalam identik dan `check_delivery.py` dari
ekstraksi. Paket R2 serta protokol/job training tidak disentuh.

## Hasil Aktual
- Sorting pada tabel yang dilingkari sudah numerik menurun; fixture pengguna
  tampil `30.4% → 27.0% → 17.7%`. Task, kelas, runner-up dan bar tidak tertukar.
- Enam skrip regresi Node termasuk `test_prediction_sort.js` lulus; empat tes
  HTML5 dan dua tes Chromium sorting desktop/mobile/escaping lulus. Fixture
  browser sempat timeout karena menunggu lebih dari satu opsi meski mock hanya
  satu sampel; kondisi tunggu diperbaiki, kedua tes lalu lulus pada rerun.
- ZIP Windows R3: `delivery/update_20261019/clean_windows_r3/TEMPO_WINDOWS_UPDATE_20261019_R3.zip`.
- Ukuran 101.521.865 byte (101,52 MB desimal), 798 file.
- SHA-256: `bdea8443ae2674bb4623dca02ab902be927684033ea1433a07188c7160a37762`.
- CRC, semua hash konten, source HTML terbaru, provenance data, kesamaan
  laporan luar/dalam ZIP dan runtime `check_delivery.py` hasil ekstraksi lulus.
- Laporan/bukti diperbarui karena E14 berubah sejak R2: pada snapshot 18.45 WIB,
  fold 1–2 COMPLETE dan artefak diverifikasi ulang, fold 3 QUEUED, fold 4
  RUNNING, fold 5 PENDING. Belum ada 740 OOF final. Scheduler lokal tidak
  terdeteksi aktif; keadaan ini dicatat tanpa restart atau perubahan job.
- Builder sekarang mengemas status dinamis; bila cek live gagal, timestamp
  observasi ledger dan sumber fallback dibedakan secara eksplisit.
- Paket R2, sumber data/model dan protokol/job training tidak diubah. Uji
  clean Windows tetap belum dilakukan. Perubahan dicatat pada
  `CHANGELOG.md`, `[Unreleased] / Added` dan `/ Changed`.
