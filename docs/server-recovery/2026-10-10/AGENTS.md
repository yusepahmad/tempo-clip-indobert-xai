# Project Rules

Aturan wajib untuk semua pekerjaan di project ini. Berlaku untuk setiap task, sekecil apa pun.

## 1. Plan dulu, sebelum eksekusi

Sebelum melakukan perubahan apa pun (kode, konfigurasi, dokumen, struktur file), buat plan terlebih dahulu.

- Plan harus dibuat **sebelum** tool call yang mengubah apa pun.
- Plan berisi: tujuan, file yang tersentuh, langkah-langkah, risiko/asumsi.
- Untuk task trivial sekalipun, tetap tulis plan (boleh ringkas).

## 2. Simpan setiap plan ke `docs/`

Setiap plan disimpan sebagai file markdown di `docs/plans/`.

- Nama file: `docs/plans/YYYY-MM-DD-<slug-singkat>.md`
- Template:

```markdown
# <Judul Plan>

**Tanggal:** YYYY-MM-DD
**Status:** draft | approved | in-progress | done

## Tujuan
<apa yang ingin dicapai dan kenapa>

## Ruang Lingkup
- File/modul yang tersentuh
- Yang eksplisit TIDAK disentuh

## Langkah
1. ...
2. ...

## Risiko & Asumsi
- ...

## Verifikasi
<cara membuktikan hasilnya benar>
```

- Kalau plan berubah di tengah jalan, update file plan-nya — jangan diam-diam menyimpang.

## 3. Catat setiap perubahan ke changelog

Setiap perubahan yang benar-benar diterapkan dicatat di `CHANGELOG.md` di root project.

- Format: [Keep a Changelog](https://keepachangelog.com/) + kategori `Added` / `Changed` / `Fixed` / `Removed`.
- Perubahan baru masuk ke section `## [Unreleased]` di paling atas.
- Setiap entry: apa yang berubah, file terkait, dan link ke plan-nya.
- Contoh entry:

```markdown
### Added
- Modul preprocessing citra di `src/preprocess.py` (plan: `docs/plans/2026-09-22-preprocessing.md`)
```

- Changelog ditulis **setelah** perubahan selesai diterapkan, bukan diprediksi di depan.

## Urutan kerja standar

1. Tulis plan → simpan ke `docs/plans/`
2. Konfirmasi ke user bila ada keputusan yang ambigu
3. Kerjakan sesuai plan
4. Catat hasilnya ke `CHANGELOG.md`
5. Laporkan ke user: apa yang berubah, plan mana, entry changelog mana
