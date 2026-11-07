# UI terpandu dengan kontras dan hierarki jelas

**Tanggal:** 2026-10-06
**Status:** done

## Tujuan
Menanggapi layout kosong, bacaan kecil/nyaru dan urutan penggunaan yang kurang jelas. Buat gambar terpilih serta langkah tindakan menjadi isi utama sebelum hasil tersedia.

## Ruang Lingkup
`02_web_demo/index.html`, `01_notebook/test_workspace_ui.js` (sinkronisasi preview), bukti UI, plan/changelog root dan paket. Backend/model/data/ZIP tidak diubah.

## Langkah
1. Ganti empty state dekoratif dengan preview sampul nyata dan panduan tiga langkah.
2. Nomori kelompok input, sederhanakan istilah dan perjelas aksi utama.
3. Tingkatkan ukuran/kontras teks serta warna semantik tab/panel; pertahankan workspace desktop dan tab hasil.
4. Uji kontrol/ID, pergantian mode-preview, navigasi/loading/respons lama, sintaks dan HTTP; catat batas visual browser.

## Risiko & Asumsi
Konten panjang tetap perlu overflow panel. Warna disertai label teks, bukan satu-satunya pembeda. Browser visual mungkin tidak tersedia; tidak mengklaim uji pengguna baru.

## Verifikasi
Kontrol lama lengkap/unik, state/mode dan navigasi konsisten, kontras warna utama terukur, respons HTTP sesuai source, regresi JS lulus.

## Hasil
Panduan tiga langkah dan preview sampul nyata menggantikan ilustrasi/area kosong. Label form disederhanakan, teks diperbesar dan warna/header/tab/panel lebih kontras; warna disertai nama/keterangan. Uji preview dataset/unggahan kosong/unggahan baru/kembali dataset, tab/keyboard/loading/respons lama, sintaks, 65 ID unik dan HTTP lulus. Enam pasangan warna teks utama memiliki rasio 6,97–14,14. Browser CUA kosong sehingga review visual dan uji pengguna belum dilakukan. Backend dan ZIP lama tidak berubah.
