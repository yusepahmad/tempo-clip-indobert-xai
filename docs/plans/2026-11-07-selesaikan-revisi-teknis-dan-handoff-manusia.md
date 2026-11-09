# Selesaikan Revisi Teknis dan Handoff Manusia

**Tanggal:** 2026-11-07
**Status:** in-progress

## Tujuan
Menyelesaikan pekerjaan revisi yang dapat dikerjakan otomatis, terutama integrasi hasil QLoRA basic R21, dan menyediakan instruksi konkret untuk pekerjaan manusia yang tersisa.

## Ruang Lingkup
- Source builder/evaluator terkait pada `DEMO_XAI_745_FULL/01_notebook/revisi_ii/` bila diperlukan; hasil koleksi `04_hasil_eksperimen/revisi_ii/qwen_basic_jobs/full/` dan `experiments/RII_QWEN_QLORA_BASIC/`.
- Paket baru `delivery/R21_HASIL_FULL_20261107/` dan `delivery/HASIL_REVISI_JOY_20261108_R4/` beserta ZIP/checksum, bukti QA, notebook, tracker dan panduan manusia.
- `docs/revisi-ii/`, plan ini, `docs/WORKSPACE_INDEX.md` dan root `CHANGELOG.md`.
- Tidak menimpa paket R3/arsip lama, label/split, fitur E01 historis, skor manusia atau model demo. Tidak melakukan panggilan berbayar.
- Tambahan setelah mencocokkan PDF: worker/manager/tes baru `qwen_headline` dan job privat terpisah untuk permintaan literal citra+judul R21. Arm basic lama mengandung supporting text sehingga tidak cukup untuk menutup tuntutan literal. Smoke wajib lulus; full hanya dengan kuota gratis terverifikasi, ledger anti-duplikasi, maksimum9 jam wall/18 jam-GPU. Tidak mengganti hasil lama atau menjanjikan job selesai dalam sesi ini. Collector berbatas waktu disiapkan untuk job yang berjalan.

## Langkah
1. Audit builder, status sembilan butir dan akses runtime Colab yang tersedia.
2. Koleksi keluaran kecil Qwen basic yang sudah COMPLETE, verifikasi protokol/source/data/hash/ID/truth/fold/split/probabilitas/input audit, dan hitung metrik/CI/paired tests R21.
3. Bangun paket R4 yang mengintegrasikan hasil ke analisis, tiga notebook, bukti R21, tracker dan narasi; bedakan selesai teknis dari persetujuan akademik. Jalankan smoke dan, jika lulus/kuota cukup, full citra+judul terpisah. R21 tetap terbuka sampai arm literal tersedia; jangan menganggap supporting text setara judul saja.
4. Kerjakan pemeriksaan provenance E01 yang dapat dibuktikan tanpa merekayasa riwayat. Coba akses Colab; jika akses tidak tersedia, sediakan peluncur dan instruksi konkret tanpa mengklaim Colab lulus.
5. Siapkan satu pintu panduan/paket manusia: dua anotator150 sampul, audit60, lima penilai XAI, riwayat korpus, dokumen Agustus dan bukti/proses konfirmasi E01. Template tetap kosong.
6. Uji evaluator/collector, Run all tiga notebook, cakupan bukti, link/hash dan ekstraksi ZIP baru; perbarui indeks dan changelog setelah hasil aktual tersedia.

## Risiko & Asumsi
- R21 memakai resep epoch inner rich historis dan batas input CLIP berbeda; keterbatasan kesetaraan harus tetap dijelaskan.
- COMPLETE Kaggle bukan otomatis hasil valid; collector harus lulus sebelum publikasi. Bobot checkpoint besar tidak diperlukan untuk analisis ulang prediksi dan tidak diklaim direplay.
- Isolasi/timestamp E01 historis tidak dapat dibuat surut; regenerasi fitur baru tidak membuktikan sejarah dan memerlukan eksperimen lanjutan jika menggantikan fitur penelitian.
- Kebutuhan manusia tidak diganti AI. Penutupan akademik tetap bergantung pada pemeriksaan pembimbing. Dokumen Agustus asli dan data korpus yang hilang hanya dapat diberikan pemiliknya.
- Colab memerlukan akses sesi akun; bila tidak tersedia, laporkan batas akses dan tugas runtime yang spesifik untuk pengguna.

## Verifikasi
- Tepat740 ID unik, lima fold masing-masing148, gold/fold canonical identik, hash source/protocol/prediction/input audit benar dan probabilitas konsisten.
- R21 memiliki18 baris matriks/zero-shot berangka aktual, tiga paired tests/CI dan narasi yang cocok hasil.
- Tiga notebook R4 dieksekusi ulang dengan output tersimpan; paket/link/hash/ZIP diperiksa, versi sebelumnya tidak ditimpa.
- Tracker, README, notebook dan panduan konsisten mengenai jumlah selesai/terbuka; seluruh instrumen manusia kosong.
- Bukti Colab diberi status verified hanya jika runtime Colab nyata menghasilkan laporan.

## Pembaruan 8 November 2026
- Pengguna meminta status delivery dan tugas manusia; pekerjaan teknis tetap dilanjutkan.
- Hasil supporting740 sudah dikoleksi pada7November; smoke citra+judul sekarang COMPLETE dan akan dikoleksi sebelum full.
- Folder delivery baru memakai tanggal8November2026. Collector headline dapat membangun paket lanjutan berversi baru sesudah full benar-benar COMPLETE/verified; tidak menimpa R4. Jika runtime masih berjalan, status dilaporkan berjalan, bukan selesai.
