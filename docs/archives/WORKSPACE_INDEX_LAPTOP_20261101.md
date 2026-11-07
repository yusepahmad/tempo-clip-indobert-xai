# Indeks Workspace

**Diperbarui:** 1 November 2026

## Project

**Eksperimen Multi-Task Learning CLIP–IndoBERT Berbasis XAI untuk Dekoding
Metafora Sampul Majalah Tempo**

## Status singkat

- Fitur aplikasi Week 1–3 sudah tersedia: OCR dan koreksi teks, prediksi tiga
  task, XAI visual dan teks, kesimpulan awam, batch, resume, serta ekspor.
- Delivery riset lengkap historis: `delivery/experiment_final_20261020/`;
  Windows khusus terakhir: R3 tanggal 19 Oktober. Colab E14 tanggal 20 Oktober
  adalah paket persiapan, bukan inferensi yang telah diverifikasi.
- Revisi II sedang dikerjakan pada source/hasil `revisi_ii/`; model utama
  penelitian ditetapkan E42 dengan pengungkapan seleksi post-hoc. Macro-F1
  menjadi metrik utama dan target proposal lama dilaporkan sebagai historis.
- Kandidat paket revisi/QA berada di `delivery/revisi_ii_20261101/`. Status28
  butir dan kebutuhan manusia yang masih terbuka tercantum dalam tracker;
  kandidat QA tidak boleh dianggap seluruh revisi selesai.

## Peta direktori

| Lokasi | Peran | Perlakuan |
|---|---|---|
| `DEMO_XAI_745_FULL/` | Source kerja utama, data, eksperimen, dan web demo | Acuan pengembangan setelah sinkronisasi Sprint 0 |
| `delivery/week34_clip_indobert_20261012/DEMO_XAI_745_FULL/` | Snapshot basis sinkronisasi historis 17 Oktober | Arsip perilaku release; jangan diedit sebagai source kerja |
| `delivery/experiment_final_20261020/` | Delivery riset/presentasi historis lengkap | Arsip immutable |
| `delivery/revisi_ii_20261101/` | Kandidat baru, QA dan delivery Revisi II | Baca status paket dan tracker; release baru memakai build berversi |
| `docs/revisi-ii/` | Bukti audit, keputusan model dan instrumen manusia | Acuan revisi bersama source dan hasil nyata |
| `delivery/week34_20261012/` | Delivery pembanding E14 | Arsip pembanding, bukan model utama |
| `docs/` | Dokumentasi lintas source, laporan, goal, dan plan | Acuan manajemen proyek |
| `docs/plans/` | Riwayat rencana perubahan | Jangan dipakai sebagai status tunggal tanpa laporan hasil |
| `docs/server-recovery/` | Snapshot pemulihan server | Arsip pemulihan, bukan source canonical |
| `delivery/archive/` | Paket delivery/review historis yang sebelumnya berada di root | Arsip immutable; indeks dan SHA-256 tersedia di `delivery/archive/README.md` |
| `docs/references/` | PDF revisi, screenshot, dan gambar asli dosen | Bahan sumber; indeks dan SHA-256 tersedia di `docs/references/README.md` |

## Sumber kebenaran per topik

| Topik | Dokumen acuan |
|---|---|
| Revisi aktif dan urutan kerja | `docs/plans/2026-11-01-pengerjaan-revisi-ii-notebook.md` |
| Implementasi dan QA Revisi II | `docs/plans/2026-11-01-revisi-ii-evaluasi-delivery.md` |
| Source canonical dan model aktif | `docs/CANONICAL_SOURCE.md` |
| Audit status plan terbuka | `docs/PLAN_STATUS_AUDIT.md` |
| Model delivery utama | `docs/DELIVERY_MAIN_MODEL.md` |
| Goal dan gate penelitian | `docs/GOAL_DELIVERY_GATES.md` |
| Status Week 3–4 terbaru | `delivery/week34_clip_indobert_20261012/DEMO_XAI_745_FULL/docs/DELIVERY_WEEK34_STATUS.md` |
| Bukti release terbaru | `delivery/week34_clip_indobert_20261012/DEMO_XAI_745_FULL/07_delivery_evidence/` |
| Status perubahan | `CHANGELOG.md` |

## Aturan source canonical

1. Perubahan baru dikerjakan pada `DEMO_XAI_745_FULL/` setelah perbedaan
   terhadap snapshot delivery diaudit.
2. Folder `delivery/` diperlakukan sebagai artefak release immutable; release
   baru dibuat pada folder berversi baru.
3. Perbaikan yang hanya ada di delivery harus dipindahkan secara terpilih dan
   diuji, bukan menyalin seluruh folder secara buta.
4. Setiap perubahan mengikuti plan di `docs/plans/` dan dicatat pada root
   `CHANGELOG.md`.
5. Hasil eksperimen tidak otomatis menjadi model delivery. Promosi membutuhkan
   gate metrik, hash, checkpoint, XAI, dan pengujian E2E.

## Catatan historis perbedaan source

- Perbedaan heatmap source/snapshot yang dicatat sebelum Sprint 0 telah
  ditangani pada sinkronisasi 17 Oktober; lihat `CANONICAL_SOURCE.md`.
- Sejumlah dokumen awal masih memuat baseline dan status lama.
- Beberapa plan eksperimen tetap berstatus `in-progress` walaupun eksperimen
  berikutnya telah berjalan; status tersebut perlu diaudit satu per satu.

## Larangan perapian otomatis

Jangan menghapus `venv`, `_cache`, `_jobs`, checkpoint, hasil eksperimen, ZIP,
atau snapshot server hanya karena ukurannya besar. Pembersihan fisik harus
memiliki inventaris ukuran, bukti bahwa artefak sudah tersalin, dan persetujuan
pengguna atas target yang tepat.
