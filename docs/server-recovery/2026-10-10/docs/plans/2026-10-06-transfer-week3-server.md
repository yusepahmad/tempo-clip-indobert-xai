# Transfer Week 3 ke Server

**Tanggal:** 2026-10-06
**Status:** done

## Tujuan
Memindahkan paket kerja Week 3 agar dapat dilanjutkan di server research-user@10.12.1.31.

## Ruang Lingkup
- Paket TEMPO_SERVER_HANDOFF_20261006.zip yang sudah diverifikasi, beserta checksum.
- Tujuan /home/research-user/workspace/learn/DEMO_XAI_745_FULL.
- Plan ini dan CHANGELOG.md; salinan catatan transfer ke server.
- Tidak menyalin seluruh workspace, venv, cache model, job batch, atau checkpoint besar. Tidak menghapus sumber lokal, tidak menjalankan aplikasi atau training.

## Langkah
1. Pastikan akses SSH, kapasitas, dan folder tujuan kosong.
2. Kirim arsip Week 3 dan checksum, verifikasi SHA256 sebelum ekstraksi.
3. Ekstrak dan verifikasi seluruh file berdasarkan manifest paket.
4. Catat hasil transfer dan lokasi lanjutan di changelog, sinkronkan catatan ke server.

## Risiko & Asumsi
- Paket handoff memuat demo baseline terbaru dan bukti audit; belum final seluruh revisi client.
- Environment server perlu dibuat ulang mengikuti docs/HANDOFF_SERVER.md.
- Folder tujuan kosong telah diperiksa; sumber lokal dipertahankan.

## Verifikasi
Checksum arsip harus cocok, seluruh hash file manifest harus cocok, dan entrypoint app/panduan audit harus tersedia pada server.

## Hasil
- Arsip 103.296.265 byte terkirim dan SHA256 cocok.
- 979 file sesuai manifest, tanpa kesalahan.
- Bukti server: /home/research-user/workspace/learn/WEEK3_TRANSFER_VERIFICATION.json.
- Environment belum dibuat dan aplikasi belum dijalankan; sumber lokal tetap tersedia.
