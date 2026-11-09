# Sprint 0 — Konsolidasi Workspace

**Tanggal:** 2026-10-17
**Status:** done

## Tujuan
Menjadikan `DEMO_XAI_745_FULL/` sebagai source kerja canonical yang konsisten
dengan perbaikan terverifikasi pada snapshot delivery Week 3–4, sekaligus
menyelaraskan identitas model, dokumentasi awal, status plan, dan bukti regresi.

## Ruang Lingkup
- Audit perbedaan source utama terhadap
  `delivery/week34_clip_indobert_20261012/DEMO_XAI_745_FULL/`.
- Sinkronisasi selektif perbaikan aplikasi/release yang memiliki bukti dan test,
  terutama R5 heatmap gabungan.
- Penetapan manifest source canonical dan model aktif.
- Penyelarasan dokumen awal serta status plan aktif yang dapat diputuskan dari
  bukti lokal.
- Regresi Python, JavaScript, dan pemeriksaan HTTP yang dapat dijalankan pada
  environment lokal.
- Tidak mengubah dataset, label, hasil eksperimen, checkpoint, atau snapshot
  delivery historis.
- Tidak mempromosikan model eksperimen baru.

## Langkah
1. Buat inventaris diff terfilter dan klasifikasikan perubahan source,
   dokumentasi, test, evidence, data, serta artefak runtime.
2. Identifikasi perubahan release yang aman dan relevan untuk source canonical.
3. Port perubahan terpilih beserta test pendukung ke source utama.
4. Buat manifest canonical yang mencatat model, metrik, source, dan pengecualian.
5. Selaraskan dokumen onboarding dengan status terbaru.
6. Audit status plan terbuka dan perbarui hanya yang memiliki bukti cukup.
7. Jalankan regresi yang relevan, simpan ringkasan hasil, dan perbarui roadmap.
8. Catat perubahan aktual di `CHANGELOG.md` dan tutup plan bila seluruh
   acceptance Sprint 0 terpenuhi.

## Risiko & Asumsi
- Snapshot delivery dapat mengandung file generated/evidence yang tidak patut
  disalin ke source utama.
- Source utama mungkin memiliki eksperimen lebih baru; sinkronisasi tidak boleh
  mengganti file tersebut secara membabi buta.
- Test penuh yang membutuhkan layanan/model eksternal dapat mahal atau tidak
  tersedia; keterbatasan harus dicatat dan tidak dianggap lulus.
- Model aktif tetap `clip-indobert-mtl-v1` sampai ada keputusan promosi baru.

## Verifikasi
- Manifest diff menunjukkan file yang dipindahkan, dipertahankan, dan diabaikan.
- R1–R5 pada source utama konsisten dengan release terbaru.
- Dokumen awal menyebut model aktif dan metrik yang sama.
- Regresi yang tersedia lulus dan hasilnya tersimpan.
- Tidak ada perubahan pada snapshot di `delivery/`.
