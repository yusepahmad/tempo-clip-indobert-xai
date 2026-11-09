# Status revisi teknis — 8 November 2026

> **Addendum 10 November 2026:** R21 literal telah selesai. R22, R23/R6, dan R31 juga ditutup secara konservatif setelah hasil manusia divalidasi; gold/model/snapshot R4 tidak diubah. Daftar terbuka hanya R8, R32, dan R34/R9. Lihat `docs/revisi-ii/STATUS_SISA_TEKNIS_20261110.md` dan `docs/revisi-ii/KEPUTUSAN_PENUTUPAN_R22_R23_R6_R31_20261110.md`. Bagian lain dipertahankan sebagai riwayat snapshot 8 November.

Snapshot analisis publik R4 tetap 19/28 butir selesai teknis. Integrasi web rich256 terbaru merupakan pekerjaan lanjutan yang diuji terpisah; tidak mengubah pilihan model penelitian E42 atau metrik utama Macro-F1. Tidak ada hasil/rating/riwayat manusia buatan.

## Teknis tersedia

- Paket R4: tiga notebook dengan output penuh, 234 baris metrik dari 78 sumber, hash/protokol/split serta instrumen anonim. 26 tes evaluator/collector/agreement/source lulus.
- Backend web rich256: lima checkpoint asli, replay740, encoder pinned, upload ensemble dan XAI aktual; lihat WEB_RICH256.md dan qa/WEB_TAIL_SERVING_VERIFICATION.json.
- R21 supporting-basic sudah lengkap 740 prediksi. Arm tersebut tetap dibedakan dari citra+judul literal. Source worker/manager/collector literal tersedia dan melindungi submission dari duplikasi.
- R22: bundle input tanpa label, generator/prompt/hash, probe prospective dan 20 contoh pemeriksaan tersedia; tidak membuktikan isolasi proses atau timestamp historis.
- R32: analisis Linux/server dan hasil ekstraksi arsip lulus. Launcher Colab publik menyediakan unduhan arsip/checksum otomatis; laporan Colab baru boleh dianggap bukti setelah benar-benar dijalankan pada runtime Colab.

## Tersisa

| Butir | Bukti/tindakan tersisa | Ketergantungan |
|---|---|---|
| R32 | Run all pada runtime Colab asli dan simpan laporan/screenshot | Runtime Colab melalui akun pengguna |
| R34/R9 | Minimal lima penilai independen XAI dan agreement | Manusia |
| R8 | Dokumen Agustus asli untuk memeriksa tuntutan lengkap | Pemilik dokumen/pembimbing |

Job literal yang tercatat: `research-account/tempo-revisi-ii-qwen-headline-full`, versi 2. Status submitted/RUNNING pada catatan lama bukan pengamatan live terbaru. Workspace aktif belum memiliki autentikasi Kaggle; hasil literal tidak diisi dari smoke atau arm supporting dan job tidak disubmit ulang.

## Melanjutkan R21 setelah autentikasi tersedia

Jalankan dari environment yang sudah memiliki Kaggle CLI dan dependensi analisis, pada source canonical yang memiliki ledger/protokol. Jangan memasukkan token ke Git atau notebook.

```bash
cd DEMO_XAI_745_FULL/01_notebook/revisi_ii
python manage_qwen_headline.py status full
# Jalankan hanya bila status COMPLETE; collector memvalidasi hasil sebelum publikasi.
python manage_qwen_headline.py collect full
```

Jika status ERROR, periksa log privat dan simpan kegagalan sebelum memperbaiki worker atau meluncurkan versi baru. Jika RUNNING, biarkan job yang sama berjalan. Setelah collector verified, bangun delivery R5 baru dengan `build_technical_delivery.py` dari paket R4 canonical; jangan mengubah snapshot R4 atau formulir manusia. Paket publik harus disanitasi ulang dan diverifikasi sebelum dipush.

## Publikasi source dan artefak

Source web dipush pada commit `0e67b75`; Release `v2026.11.08-web-rich256` memuat ZIP model 711.926.368 byte dan checksum yang cocok digest GitHub. Repository teramati private; unduhan anonim memberi404 untuk Release baru maupun R4 lama. Task ini tidak mengubah visibilitas. Gunakan akses GitHub berizin; launcher Colab menyediakan fallback unggah ZIP tanpa token.
