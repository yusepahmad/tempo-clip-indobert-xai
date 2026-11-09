# Instalasi Kaggle CLI

**Tanggal:** 2026-10-05
**Status:** done

## Tujuan
Memasang CLI resmi Kaggle di laptop Linux untuk pengelolaan notebook dan training background.

## Ruang Lingkup
- Environment tool user melalui uv dan executable `~/.local/bin/kaggle`.
- Plan ini dan CHANGELOG.md root.
- Tidak mengubah environment model/training, mengunggah dataset, menjalankan job Kaggle, atau menyimpan token akun.

## Langkah
1. Periksa tool yang tersedia dan panduan resmi Kaggle CLI.
2. Install paket kaggle menggunakan uv tool install dalam environment terisolasi.
3. Verifikasi versi, help, dan subcommand kernels.
4. Catat hasil instalasi dan langkah autentikasi berikutnya di plan/changelog.

## Risiko & Asumsi
- Instalasi membutuhkan jaringan; kompatibilitas Python akan dicek saat install.
- Autentikasi Kaggle terpisah; tidak meminta token rahasia di chat.
- Scope instalasi laptop Linux tempat project dan VS Code digunakan.

## Verifikasi
`kaggle --version`, `kaggle --help`, dan `kaggle kernels --help` berhasil; executable tersedia di PATH.

## Hasil
- Paket kaggle 2.2.4 terpasang via uv tool install, memakai environment Python 3.13 terisolasi. Executable `/home/research-user/.local/bin/kaggle`.
- Versi, help utama, kernels help dan auth help berhasil. Pemanggilan pertama help paralel memicu race pada pembuatan config oleh CLI; pengulangan berurutan berhasil tanpa perubahan kode.
- Autentikasi akun belum dilakukan; berikutnya user menjalankan `kaggle auth login` dari terminal lokal. Tidak ada token ditampilkan atau upload/job dijalankan.
