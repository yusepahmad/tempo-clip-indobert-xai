# Delivery Windows dan Laporan Hasil Terbaru

**Tanggal:** 2026-10-19
**Status:** done

## Tujuan
Menyediakan ZIP Windows clean revisi terbaru dan laporan Markdown terpisah
berdasarkan hasil eksperimen yang sudah selesai serta snapshot training E14.

## Ruang Lingkup
- Builder baru `delivery/update_20261019/build_latest_windows.py`.
- Paket, laporan, bukti hasil, checksum dan verifikasi pada
  `delivery/update_20261019/clean_windows_latest/`.
- Plan ini dan entry `CHANGELOG.md` setelah pekerjaan selesai.
- Tidak mengubah model aplikasi, data, protokol E14, job Kaggle, scheduler,
  maupun paket delivery lama. Checkpoint besar dan riwayat lama tidak dikemas.

## Langkah
1. Cek hasil lokal, verifikasi metrik dari prediksi, cek status Kaggle dan
   kesehatan scheduler tanpa menghentikan training.
2. Tulis laporan terbaru: E11/E12 740 OOF, E13 inner pilot, OCR, batas capaian,
   model runtime aktif, status E14 bertimestamp dan langkah yang masih tersisa.
3. Buat builder allowlist runtime Windows dengan laporan yang sama di dalam
   ZIP, bukti JSON/CSV ringkas dan snapshot E14; gunakan nama revisi R2.
4. Verifikasi CRC, SHA-256 seluruh konten, provenance data, tidak ada kredensial,
   serta pemeriksaan runtime dari hasil ekstraksi. Windows bersih belum diuji.
5. Catat hasil aktual di changelog dan tandai plan selesai.

## Risiko & Asumsi
- Status E14 berubah setelah paket dibuat; laporan adalah snapshot, bukan hasil
  lima fold final. Saat pemeriksaan awal fold 1–2 RUNNING, fold 3–5 PENDING.
- Hasil pilot 119 validation tidak sebanding langsung dengan 740 OOF.
- Micro-F1 dan Macro-F1 dilaporkan terpisah; tidak mengklaim target tercapai.
- Runtime tetap CLIP–IndoBERT; E13/E14 belum diintegrasikan ke aplikasi.
- Data provenance tidak boleh berubah. Hanya launcher BAT dikonversi CRLF.
- Paket lama dipertahankan; clean berarti seleksi isi ZIP baru.

## Verifikasi
Hitung ulang Micro/Macro-F1 E11/E12/E13 dari CSV prediksi dengan label dataset;
bandingkan hasil JSON. ZIP harus lolos CRC, manifest SHA-256 dan hash data
runtime. Laporan luar/dalam ZIP harus identik; jalankan `check_delivery.py`
dari ekstraksi sementara. Pastikan tidak ada venv, kredensial, checkpoint,
cache, ZIP lama, atau launcher Linux di paket. Catat ukuran dan checksum final.

## Hasil Aktual
- ZIP Windows R2: `delivery/update_20261019/clean_windows_latest/TEMPO_WINDOWS_UPDATE_20261019_R2.zip`.
- Laporan terpisah dan identik di ZIP:
  `delivery/update_20261019/clean_windows_latest/LAPORAN_TERBARU_TEMPO_20261019.md`.
- Snapshot 19 Oktober 2026 pukul 14.16 WIB: fold 1–2 RUNNING dari CLI Kaggle,
  fold 3–5 PENDING lokal; scheduler hidup, belum ada E14 740 OOF.
- E11/E12 (740 ID) dan E13 (119 validation ID) lolos hitung ulang Micro/Macro,
  validasi label/fold/split, hash prediksi dan pemilihan epoch pilot.
- CRC, seluruh hash konten, provenance data, BAT CRLF, scan pola kredensial
  umum dan pemeriksaan runtime hasil ekstraksi lulus. Tidak ada checkpoint,
  cache, venv, ZIP lama maupun launcher Linux dalam paket baru.
- Ukuran 101.151.685 byte (101,15 MB desimal), 786 file.
- SHA-256: `eb1eb43aa23206b971fbff77def3fbc7b4e7c4c2799c3f0d47cd4594c3ac2ad6`.
- `verification.json` dan checksum `.sha256` disediakan di folder delivery.
- Clean install Windows dan uji pengguna tidak dijalankan; model aplikasi,
  sumber hasil, protokol E14, training Kaggle dan paket lama tidak diubah.
- Perubahan dicatat di `CHANGELOG.md`, `[Unreleased] / Added`.
