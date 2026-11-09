# Setup Workflow Rules (plan, docs, changelog)

**Tanggal:** 2026-09-22
**Status:** done

## Tujuan
Menetapkan aturan kerja permanen untuk project ini: setiap pekerjaan diawali plan, plan disimpan ke `docs/`, dan setiap perubahan dicatat ke changelog.

## Ruang Lingkup
- `.claude/CLAUDE.md` — file aturan project (dibaca otomatis tiap sesi)
- `docs/plans/` — direktori penyimpanan plan
- `CHANGELOG.md` — changelog root

Tidak menyentuh: `DEMO_XAI_745_FULL/`, `revision.pdf`.

## Langkah
1. Buat `.claude/CLAUDE.md` berisi tiga aturan + template plan + urutan kerja standar
2. Buat direktori `docs/plans/`
3. Buat plan ini sebagai contoh penerapan pertama
4. Inisialisasi `CHANGELOG.md` dengan section `[Unreleased]`

## Risiko & Asumsi
- Asumsi: project belum berisi `CLAUDE.md` atau `CHANGELOG.md` lain — terverifikasi, keduanya belum ada.
- Asumsi: `docs/` memang diperuntukkan untuk dokumentasi kerja, bukan output skripsi. Kalau ternyata `docs/` akan dipakai untuk naskah TA, plan bisa dipindah ke `docs/plans/` terpisah tanpa konflik karena sudah bersarang.

## Verifikasi
`.claude/CLAUDE.md`, `docs/plans/2026-09-22-setup-workflow-rules.md`, dan `CHANGELOG.md` ada dan terbaca.
