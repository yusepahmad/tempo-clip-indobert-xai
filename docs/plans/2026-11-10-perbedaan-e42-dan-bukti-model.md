# Perbedaan Eksperimen terhadap E42 dan Bukti Model

**Tanggal:** 2026-11-10
**Status:** done

## Tujuan
Menjawab permintaan klien dengan menjelaskan perubahan arsitektur, input, loss, learning rate, epoch, dan prosedur seleksi pada setiap eksperimen E36–E49 dibandingkan E42, serta menyediakan bukti visual aktual yang menunjukkan komponen CLIP, IndoBERT, dan XAI pada E42.

## Ruang Lingkup
- Menambah dokumen kanonik perbandingan E36–E49 terhadap E42 di `docs/revisi-ii/`.
- Menambahkan addendum daftar R kanonik di `docs/revisi-ii/`, khususnya R18, R27, R29, R30, dan R34, tanpa memodifikasi paket R4 yang memiliki manifest integritas.
- Membuat halaman bukti dan screenshot untuk CLIP, IndoBERT, serta XAI dari source/protokol/artefak aktual.
- Memakai bukti yang sudah tersedia; tidak melatih ulang model, mengubah checkpoint, metrik, prediksi, atau status penyelesaian revisi.

## Langkah
1. Audit source, protocol, README, hasil E36–E49, dan konfigurasi fold E42.
2. Susun tabel per eksperimen: komponen yang diubah, epoch/LR/loss, serta perbedaan langsung terhadap E42.
3. Buat indeks bukti E42 yang memetakan CLIP, IndoBERT, fusion/head, dan XAI ke source serta hash/protokolnya.
4. Buat tiga halaman bukti visual dan render screenshot PNG: CLIP, IndoBERT, dan XAI aktual.
5. Buat addendum `TANGGAPAN_28_REVISI` dan tambahkan ringkasan/tautan pada bukti R18/R27/R29/R30/R34 yang relevan; paket R4 asli tetap immutable.
6. Verifikasi isi, tautan lokal, dimensi screenshot, dan konsistensi klaim terhadap source/protokol.
7. Catat perubahan aktual pada `CHANGELOG.md` dan tutup plan.

## Risiko & Asumsi
- Istilah “tiap E” ditafsirkan sebagai rangkaian eksperimen E36–E49 yang langsung membentuk atau membandingkan keluarga E42.
- E48 memiliki source lengkap berupa diagnostik single-task `LinearSVC`; dokumen harus menegaskan bahwa E48 bukan ablation neural atau model joint seperti E42.
- Paket R4 tidak diubah agar hash pada manifest tetap valid; permintaan penambahan daftar R diwujudkan sebagai addendum kanonik terpisah.
- Screenshot arsitektur merupakan render bukti source/protokol, bukan foto UI training; screenshot XAI memakai artefak E42 aktual yang sudah terverifikasi.
- Perubahan hanya pada dokumentasi/bukti; status 19/28 dan hasil numerik tidak diubah.

## Verifikasi
- Setiap baris E36–E49 memiliki rujukan source/protocol atau catatan keterbatasan.
- Konfigurasi E42 cocok dengan `R18_ARCHITECTURE_AUDIT.json` dan `e42_tail_grid/tail_model.py`.
- Tiga screenshot dapat dibuka, berlabel jelas, dan XAI menampilkan artefak actual held-out E42.
- Tautan dari daftar R menuju dokumen dan screenshot tidak rusak.

## Hasil
- Dokumen perbandingan E36–E49, addendum R18/R27/R29/R30/R34, dan tautan dari dokumen R18 telah dibuat.
- Tiga screenshot 1600×1000 telah dirender dan diperiksa visual; screenshot XAI memuat rollout held-out E42 aktual.
- Seluruh file wajib dan target tautan lokal tersedia; paket R4 asli tidak dimodifikasi.
