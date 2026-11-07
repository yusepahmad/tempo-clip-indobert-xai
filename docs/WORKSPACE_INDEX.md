# Indeks Workspace Server .31

**Diperbarui:** 8 November 2026

Workspace aktif: `yusep@10.12.1.31:/home/yusep/workspace/tempo-revisi-20261108`.
Sesi tmux: `tempo-revisi-20261108`. Environment CPU: `.venv-analysis` (Python 3.10.12, 66 dependensi terkunci). Salinan lama `/home/yusep/workspace/learn/TA-1-sekripsi-tempo-joy-eau-dia-final` dipertahankan.

| Lokasi | Peran |
|---|---|
| DEMO_XAI_745_FULL/ | Source kerja, data/gambar dan hasil/protokol yang dimigrasikan |
| delivery/HASIL_REVISI_JOY_20261108_R4/ | Paket analisis aktif; notebook/HTML dan ZIP instrumen manusia dibuat ulang di server |
| delivery/HASIL_REVISI_JOY_20261108_R4_ANALISIS.zip | Arsip analisis baru; gunakan setelah qa/R4_EXTRACTED_VERIFICATION.json berstatus verified_extracted_run_all |
| delivery/R32_COLAB_20261108/ | Peluncur Colab dan ZIP analisis pasangannya; Colab belum dijalankan |
| delivery/R21_HASIL_FULL_20261107/ | Hasil supporting-basic nyata:5 fold/740 prediksi, 18 baris matrix dan paired tests |
| delivery/HASIL_REVISI_JOY_20261102_R3_FULL/ | Salinan input/analysis/documentation untuk fixture; bukan release R3 lengkap di server baru |
| docs/revisi-ii/ | Provenance, instrumen manusia, sumber audit dan keputusan model |
| qa/MIGRATION_VERIFICATION.json | Hasil 8.060 checksum source/data yang dipilih pada saat transfer; perubahan terencana sesudah transfer dicatat terpisah |
| qa/TESTS_SERVER.log | Hasil tes analisis dan pelindung isian manusia |
| docs/plans/2026-11-08-lanjut-kerja-server31.md | Plan migrasi dan penyesuaian cakupan |

Model utama tetap E42 CLIP–IndoBERT MTL, Macro-F1 metrik utama. Status 19/28 selesai teknis dan 9 terbuka. Supporting-basic R21 tersedia; tuntutan literal citra+judul belum ditutup sampai hasil full diverifikasi. Demo web historis bukan inferensi E42.

Job `yusepmuhamadzazuli/tempo-revisi-ii-qwen-headline-full` version 2 telah submitted dan RUNNING pada snapshot 8 November. Jangan submit ulang. Collector laptop berada pada `/tmp/joy-revisi-20261108`; server tidak menerima credential Kaggle dan belum menjalankan collector privat. Training Kaggle tetap berjalan bila laptop terputus. Koleksi berikutnya perlu akses Kaggle sah dan pemeriksaan ledger/source/protocol/split/hash sebelum publikasi.

GPU server belum tersedia pada driver NVIDIA; analisis CPU telah diuji. Lampiran ZIP model E42 dan blob training/cache besar belum menjadi cakupan migrasi ini. Regenerasi training/XAI memerlukan blob tersebut dan environment ML tersendiri. Semua artefak lama laptop/server tetap ada; tidak ada penghapusan sumber.

Tugas manusia: lihat `delivery/HASIL_REVISI_JOY_20261108_R4/UNTUK_MANUSIA/MULAI_DI_SINI.md`: dua anotator 150 sampul, audit 60, lima penilai × 48 skor, pemeriksaan 20 contoh E01, riwayat korpus/dokumen Agustus, dan Run all Colab. Simpan pengembalian pada folder baru HASIL_ISIAN; jangan menimpa instrumen.

Indeks laptop sebelumnya disimpan di `docs/archives/WORKSPACE_INDEX_LAPTOP_20261101.md` sebagai sejarah.
