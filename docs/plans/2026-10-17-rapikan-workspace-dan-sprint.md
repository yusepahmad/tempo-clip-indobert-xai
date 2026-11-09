# Rapikan Workspace dan Susun Sprint Prioritas

**Tanggal:** 2026-10-17
**Status:** done

## Tujuan
Merapikan orientasi workspace tanpa menghapus artefak, menetapkan lokasi acuan
untuk source dan delivery, serta menyusun sprint prioritas berdasarkan audit
pekerjaan Week 1–4 dan goal penelitian yang masih terbuka.

## Ruang Lingkup
- Menambah indeks workspace dan dokumen sprint aktif di `docs/`.
- Memperbarui status dokumen timeline/plan Week 3 yang sudah tidak mencerminkan
  implementasi aktual.
- Mencatat hasil perapian di `CHANGELOG.md`.
- Tidak menghapus atau memindahkan ZIP, cache, environment, dataset, checkpoint,
  hasil eksperimen, maupun folder delivery.
- Tidak mengubah source aplikasi atau memilih checkpoint/model baru.

## Langkah
1. Tetapkan peta direktori dan sumber acuan berdasarkan bukti terbaru.
2. Susun backlog menjadi sprint berurutan dengan prioritas, dependency,
   deliverable, dan acceptance criteria.
3. Tandai timeline lama sebagai arsip perencanaan dan selaraskan status plan
   Week 3 dengan hasil implementasi yang sudah tersedia.
4. Periksa keberadaan seluruh path yang dirujuk dan konsistensi status.
5. Catat perubahan aktual pada `CHANGELOG.md` dan tutup plan.

## Risiko & Asumsi
- `DEMO_XAI_745_FULL/` dan paket `delivery/week34_clip_indobert_20261012/`
  memiliki perbedaan; dokumen hanya menjelaskan perbedaan, bukan melakukan
  sinkronisasi source.
- Sprint mengutamakan konsolidasi dan reproducibility sebelum eksperimen model
  tambahan.
- Target Macro-F1 ketiga task minimal 0,70 tetap dianggap goal aktif sampai
  pengguna memutuskan sebaliknya.

## Verifikasi
- Semua path yang dirujuk dokumen tersedia.
- Sprint membedakan pekerjaan selesai, acceptance tertunda, dan eksperimen.
- Tidak ada file atau direktori lama yang dihapus/dipindahkan.
- `CHANGELOG.md` memuat entry dengan tautan ke plan ini.
