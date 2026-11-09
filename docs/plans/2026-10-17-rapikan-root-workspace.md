# Rapikan Root Workspace

**Tanggal:** 2026-10-17
**Status:** done

## Tujuan
Merapikan tampilan root workspace dengan mengelompokkan paket delivery lama,
berkas verifikasi, checksum, PDF revisi, screenshot, dan gambar referensi tanpa
menghapus data atau merusak referensi internal.

## Ruang Lingkup
- Mempertahankan di root: `.claude/`, `DEMO_XAI_745_FULL/`, `delivery/`,
  `docs/`, `scripts/`, `AGENTS.md`, dan `CHANGELOG.md`.
- Memindahkan ZIP historis beserta verification/checksum ke subfolder arsip di
  `delivery/archive/`.
- Memindahkan `revision.pdf` serta gambar lepas ke `docs/references/` dengan
  nama yang tetap dapat ditelusuri.
- Memperbarui seluruh referensi path yang terdampak.
- Tidak menghapus, menimpa, mengekstrak ulang, atau mengubah isi file biner.

## Langkah
1. Inventaris file lepas dan cari seluruh referensi path di source/dokumentasi.
2. Buat struktur tujuan berdasarkan jenis dan periode artefak.
3. Pindahkan file menggunakan path eksplisit, tanpa glob destruktif.
4. Perbarui referensi path yang terdampak dan indeks workspace.
5. Verifikasi jumlah, ukuran, checksum yang tersedia, dan tidak adanya file
   lepas yang seharusnya terarsip.
6. Catat perubahan pada `CHANGELOG.md` dan tutup plan.

## Risiko & Asumsi
- Path absolut atau path root lama mungkin dipakai oleh dokumen/script; semua
  referensi yang dapat ditemukan akan diperbarui.
- ZIP diperlakukan sebagai artefak historis immutable.
- Gambar WhatsApp dan `revision.pdf` diperlakukan sebagai bahan referensi,
  bukan input runtime aplikasi.

## Verifikasi
- Root hanya berisi direktori utama serta `AGENTS.md` dan `CHANGELOG.md`.
- Semua file yang dipindahkan masih ada dengan ukuran yang sama.
- Checksum yang sudah tersedia tetap cocok.
- Pencarian path lama tidak menemukan referensi aktif yang belum diperbarui.
