# Sanitasi Identitas Project dan Delivery

**Tanggal:** 2026-11-10
**Status:** in-progress

## Tujuan
Menghasilkan branch utama dan paket delivery yang dapat di-clone atau diunduh client tanpa nama pribadi, username akun, alamat home, identitas server, metadata author, atau tautan akun pribadi.

## Ruang Lingkup
- Seluruh file yang dipublikasikan pada repository GitHub dan delivery client.
- Teks, JSON/CSV, notebook, HTML, source, log, metadata Git, tag, dan release yang dapat mengekspos identitas pribadi.
- Riwayat Git akan diganti dengan riwayat bersih agar clone tidak membawa nama author/committer lama.
- Akun GitHub/Kaggle, job, dataset, dan repository eksternal tidak dihapus; referensinya di artefak client disensor atau diganti placeholder netral.
- Workspace internal yang tidak menjadi artefak client tidak dipublikasikan; salinan sumber lokal dipertahankan sampai hasil sanitasi terverifikasi.
- Perbaikan akses client untuk indeks bukti R18–R36 dan keterhubungan backend/model E42 setelah laporan regresi dari client.

## Langkah
1. Inventaris seluruh pola identitas, path personal, metadata author, file biner/arsip, tag, dan release pada repository publikasi.
2. Bangun salinan staging bersih dan terapkan redaksi konsisten dengan placeholder netral.
3. Hapus artefak runtime/log/cache/arsip lama yang tidak diperlukan client atau tidak dapat disanitasi secara aman.
4. Regenerasi checksum/manifest dan verifikasi fungsi utama serta kelengkapan delivery.
5. Jalankan pemindaian nama, username, email, path home, metadata notebook, Git author, dan string pada arsip/biner.
6. Buat riwayat Git baru dengan author netral, ganti branch utama secara terkontrol, lalu audit ulang clone baru.
7. Audit tag/release; hapus atau ganti referensi yang masih mengekspos identitas dari jalur download client.
8. Tambahkan jalur kompatibilitas dari URL paket R3 lama ke indeks bukti R4 dan uji seluruh tautan lokal revisi.
9. Audit aset E42, konfigurasi backend, dan startup web; kaitkan model yang benar atau sediakan kegagalan yang eksplisit bila bobot belum ada.
10. Catat hasil final pada changelog tanpa memasukkan identitas yang disensor.

## Risiko & Asumsi
- Penulisan ulang riwayat Git mengubah semua SHA commit dan memerlukan force-push; clone lama tidak dapat fast-forward.
- URL eksternal pribadi yang disensor tidak lagi dapat dipakai untuk mengunduh artefak privat; paket client harus mandiri atau memakai instruksi placeholder.
- File biner lama yang tidak dapat diverifikasi bebas identitas akan dikeluarkan dari delivery bersih, bukan diedit secara spekulatif.
- Redaksi identitas tidak boleh mengubah data penelitian, metrik, model, label, atau kesimpulan ilmiah.
- E42 hanya boleh dinyatakan aktif bila checkpoint yang sesuai tersedia dan lolos checksum; prediksi tersimpan tidak boleh disamarkan sebagai inferensi model baru.
- Repository tetap berada pada akun pemilik saat ini, sehingga host halaman repository dapat tetap menampilkan pemilik akun; isi clone, commit, dan paket download harus netral.

## Verifikasi
- Pemindaian case-insensitive terhadap seluruh alias identitas menghasilkan nol temuan pada clone bersih.
- Tidak ada path home personal, alamat email pribadi, URL akun pribadi, atau author Git lama.
- Arsip delivery diekstrak dan dipindai; manifest/checksum cocok setelah regenerasi.
- Tes utama dan validator delivery lulus pada staging bersih.
- URL R3 lama membuka indeks revisi yang valid dan backend web melaporkan status E42 secara benar.
- Clone baru dari branch utama hanya berisi riwayat dan author netral.
