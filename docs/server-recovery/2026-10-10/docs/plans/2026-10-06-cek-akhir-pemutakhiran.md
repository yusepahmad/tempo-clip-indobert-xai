# Cek Akhir Pemutakhiran 6 Oktober

**Tanggal:** 2026-10-06
**Status:** done (2026-10-06)

## Tujuan
User: "tolong cek lagi semua apakah ada yang belum di ubah dan di update karena kan ini update tanggal 6". Pastikan setiap berkas di paket delivery konsisten dengan kondisi 6 Oktober: tidak ada klaim "kondisi sekarang" yang usang, tanggal kepala dokumen jelas (dokumen hidup = 6 Okt; dokumen riwayat ditandai sebagai riwayat), teks aplikasi dan komentar kode sesuai perilaku.

## Temuan awal (agen utama)
- `02_BATASAN_TEKNIS.md:427` masih menulis teks suntingan tidak ditimpa OCR saat gambar diganti (perilaku sudah diubah 6 Okt).
- `docs/DELIVERY_WEEK_3.md` berkepala "Tanggal: 2026-10-05".
- `CHANGELOG.md` belum punya bagian rilis delivery (semua masih `[Unreleased]`).
- Sebelas laporan bertanggal 5 Okt dan dokumen 22 Sep belum diperiksa terhadap status 6 Okt; teks statis aplikasi, komentar kode dan launcher belum diperiksa.

## Ruang Lingkup & pembagian (sub-agent paralel, berkas tidak tumpang tindih; ditinjau agen utama)
- **A — dokumen hidup:** `00_BACA_DULU.md`, `MULAI_DARI_SINI.md`, `01_TUTORIAL.md`, `02_BATASAN_TEKNIS.md`, `TEKS_DELIVERY.md`, `docs/STATUS_REVISI_20261006.md`, `docs/DELIVERY_WEEK_3.md`, `docs/HANDOFF_SERVER.md`, `docs/AUDIT_OCR_URUTAN_20261006.md`.
- **B — dokumen riwayat/laporan:** `docs/plan-revisi-demo-xai-tempo.md`, `docs/TABEL_PEMERIKSAAN_REVISI.md`, `docs/VERIFIKASI_GAMBAR_DOSEN.md`, `docs/PEMERIKSAAN_VISUAL_OCR.md`, `docs/CODEBOOK_OPERASIONAL.md`, `docs/EVALUASI_AGEN_WEEK3.md`, `docs/HASIL_FULL_TRAINING_KAGGLE.md`, `docs/TRAINING_KAGGLE.md`, `docs/BENCHMARK_KAGGLE.md`, `docs/PERSIAPAN_TRAINING_CPU.md`, `docs/PERSIAPAN_TRAINING_GPU_WINDOWS.md`, `docs/2026-09-22-*.md`, `docs/DELIVERY_WEEK_1.md`, `docs/DELIVERY_WEEK_2.md`, `docs/AUDIT_DELIVERY_WEEK3_20261006.md` — isi riwayat tidak ditulis ulang; catatan riwayat + rujukan status terbaru; klaim status yang kini salah diberi koreksi bertanggal.
- **C — aplikasi & kode:** teks statis `02_web_demo/index.html` (Panduan, keterangan model, pengantar), docstring/komentar `02_web_demo/*.py`, docstring skrip `01_notebook/*.py`, `jalankan_linux.sh`, `jalankan_windows.bat`, `setup_windows.bat`, komentar `requirements*.txt` — tanpa mengubah perilaku, ID elemen, atau string yang diuji test.
- **Agen utama:** `CHANGELOG.md` (bagian rilis delivery), `AGENTS.md` (tidak diubah kecuali usang), plan; setelahnya grep pola usang, seluruh test + smoke, ZIP dibangun ulang dan dibandingkan.

## Verifikasi
- Grep pola usang di seluruh paket (di luar plan/CHANGELOG/riwayat bertanda) kosong.
- Seluruh test Python/JS/frontend + smoke browser lulus setelah perubahan C.
- ZIP baru: CRC/manifest lulus; daftar berkas yang berubah dilaporkan.

## Hasil (2026-10-06)
- **A (9 dokumen hidup):** angka OCR "65–72%" (angka saat kode dibekukan) diganti rumusan versi aplikasi terakhir "68–78% pada dua set validasi (cenderung optimistis; 63–72% saat kode dibekukan)"; perilaku unggah (`02_BATASAN_TEKNIS.md` ±427), batas masukan lengkap (40 MP, perkecil 2000 px, galat JSON), status paket/instalasi bersih/Windows, server 0.0.0.0:7861 tanpa autentikasi + unduh 8853, kepala `DELIVERY_WEEK_3.md` 6 Okt, langkah batch dengan pilihan task, `requirements-lock-linux.txt`, notebook; penyebut "15→32/57" yang salah dihapus. 67 tautan relatif dicek, tidak ada yang rusak.
- **B (16 dokumen riwayat):** catatan riwayat + rujukan STATUS di bawah judul; koreksi status bertanggal 6 Okt di checklist `plan-revisi-demo-xai-tempo.md`, `TABEL_PEMERIKSAAN_REVISI.md`, `EVALUASI_AGEN_WEEK3.md`, `AUDIT_DELIVERY_WEEK3_20261006.md`, `DELIVERY_WEEK_1/2.md`, dokumen training (Kaggle COMPLETE, tidak dipakai), `VERIFIKASI_GAMBAR_DOSEN.md`; isi riwayat tidak ditulis ulang.
- **C (teks aplikasi & kode):** teks Panduan/model/OCR/metode di `index.html` (ID dan string yang diuji tetap), docstring/komentar `02_web_demo/*.py` dan `01_notebook/*.py` (perbandingan AST: hanya docstring/komentar), launcher/setup, komentar requirements. 70 Python + 4 JS + 13 frontend lulus.
- **Agen utama:** `ocr_audit_urutan_20261006.json` dihitung ulang dengan selector terakhir (kolom `produksi` sebelumnya basi); `01_notebook/verify_gambar_dosen.py` dan `compare_decoder_week3.py` kini membaca `06_gambar_revisi/` (sebelumnya folder induk — perintah uji ulang gagal dari paket) dan `verify_gambar_dosen.py` menerima folder keluaran (diuji: GULA-GULA/CUKAI tepat, WASWAS `VJJASWAS`); catatan usang soal JSON basi dibetulkan; angka OCR di dokumen riwayat diseragamkan; tabel LIME "ratusan varian" → 120/200; `CHANGELOG.md` diberi bagian rilis delivery.
- Sapuan pola usang akhir: sisa hanya di bagian berlabel riwayat (mis. tabel uji banding Week 2 di dokumen riwayat).
