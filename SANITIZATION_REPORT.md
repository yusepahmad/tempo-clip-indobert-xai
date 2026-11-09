# Laporan Sanitasi Identitas

**Tanggal:** 10 November 2026  
**Cakupan:** branch utama dan seluruh file yang diterima melalui clone/download repository.

## Yang dibersihkan

- Nama dan alias pribadi.
- Username GitHub dan Kaggle pribadi.
- Alamat home/workspace yang mengandung username asli.
- URL akun, repository, dataset, dan job yang mengandung username asli.
- Metadata notebook, source, JSON, HTML, CSV, log, serta dokumentasi yang memuat identitas tersebut.
- Author dan committer pada riwayat Git yang didistribusikan.

## Kebijakan penggantian

Referensi yang masih diperlukan untuk memahami provenance diganti dengan placeholder netral seperti `research-account`, `project-owner`, dan `research-user`. Placeholder bukan akun aktif dan tidak mengubah angka penelitian.

## Batas

Sanitasi berlaku pada isi clone/download. Halaman hosting tetap berada di bawah akun pemilik repository sampai repository dipindahkan ke organisasi atau akun client. Akun dan job eksternal tidak dihapus oleh proses ini.

## Pemeriksaan

- Pemindaian case-insensitive pada seluruh file, termasuk mode biner, harus menghasilkan nol kemunculan alias yang disensor.
- Riwayat Git harus terdiri dari commit bersih dengan author netral.
- Manifest paket utama dibangun ulang setelah redaksi.
- Parser JSON, notebook, source Python, dan validator paket dijalankan pada staging bersih.
