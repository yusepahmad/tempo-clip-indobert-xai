# R5 Peta Gabungan dan Penyatuan Changelog

**Tanggal:** 2026-10-06
**Status:** done (2026-10-06; review visual browser tetap terbuka di langkah 3 plan induk)

Sub-plan langkah 2 dari [2026-10-06-lanjutan-week3-server.md](2026-10-06-lanjutan-week3-server.md), ditambah penyatuan changelog atas persetujuan user.

## Tujuan
1. Menyatukan `../TRANSFER_CHANGELOG.md` ke `CHANGELOG.md` proyek agar paket final memuat satu riwayat lengkap.
2. Menutup R5: peta utama di UI analisis satuan adalah peta gabungan tiga task (permintaan client: "hanya satu dan sama dan itu harus mencakup semua"), sementara peta task pilihan tetap tersedia sebagai bukti terpisah yang berlabel jelas.

## Ruang Lingkup
- `CHANGELOG.md`: diganti isi `../TRANSFER_CHANGELOG.md` + entri langkah 1 server. Dua entri ringkas yang hanya ada di proyek (codebook/evaluasi agen dan Week3 baseline) dibuang karena versi rincinya sudah ada di changelog transfer. `../TRANSFER_CHANGELOG.md` sendiri tidak diubah (berada di luar paket, tetap sebagai jejak transfer).
- `02_web_demo/index.html`:
  - fungsi murni `pilihPetaPanas(d)` + `renderPetaPanas(d)` sebelum `function tampil(d, modeData)`;
  - tab "Bukti gambar": peta utama = `heatmap_padu_url` berlabel gabungan tiga task; blok baru "Bukti task pilihan" (`imgHeatTask`, `capHeatTask`, `judulHeatTask`) memakai `heatmap_url` dengan nama task dan kelas yang dijelaskan;
  - keterangan panel per task diselaraskan;
  - tautan review batch "Buka heatmap" → "Buka peta gabungan tiga task".
  - petunjuk verifikasi visual (`verifVisual`) menyebut kedua peta, bukan "peta panas ini" yang ambigu.
- Regresi baru `01_notebook/test_r5_heatmap.js` (VM, pola sama dengan test JS lain).
- Verifikasi HTTP baru `01_notebook/verify_r5_http.py` → `04_hasil_eksperimen/revisi_week3/r5_heatmap_verification.json` (path absolut relatif file script, tidak menimpa bukti lain).
- TIDAK disentuh: `app.py`/`xai_core.py` (kontrak backend sudah benar), cara hitung peta gabungan, narasi/kesimpulan (tetap terikat task pilihan), dataset/label, docs delivery (langkah 4).

## Langkah
1. Satukan changelog, verifikasi baris unik proyek hanya entri ringkas yang sudah tercakup.
2. Implementasi UI:
   - Peta utama: bila `heatmap_padu_url` ada → tampilkan, caption: peta gabungan Isu/Kiasan/Sasaran (rata-rata peta per task yang dinormalisasi), merangkum area yang memengaruhi ketiga prediksi; bukan dasar atribusi kata/narasi task pilihan; bukan deteksi objek.
   - Bila tidak ada → sembunyikan gambar dan tulis "Peta gabungan tidak tersedia"; **tidak** jatuh kembali ke peta task pilihan berlabel gabungan.
   - Bukti task pilihan: judul memuat `task_xai` dan `kelas_untuk_atribusi_tampil`; caption menyatakan peta ini dasar narasi/zona untuk task tersebut. Bila tidak ada → pesan tidak tersedia.
   - Atribusi src di-reset agar gambar analisis sebelumnya tidak tertinggal.
3. Regresi JS: dataset (keduanya ada), padu hilang (tanpa fallback), task hilang, pergantian task (task_xai/kelas berganti → label ikut berganti, URL utama tetap padu), tidak ada `const utama = d.heatmap_url`, `tampil` memanggil `renderPetaPanas`.
4. Jalankan seluruh regresi lama + baru.
5. HTTP model nyata ke server `tempo-ui`: halaman memuat ID baru; `/api/analisis` dataset (task1/task2) dan unggahan (foto dosen) → `heatmap_padu_url` dan `heatmap_url` berbeda, keduanya PNG valid, peta per task ada 3.
6. Catat CHANGELOG, update plan induk.

## Risiko & Asumsi
- Flask melayani `index.html` dari disk per permintaan; bila di-cache, server tmux perlu dimuat ulang.
- Test JS lama memotong script dari `let analysisSeq=` sampai `function tampil(d, modeData)`; fungsi baru di rentang itu harus aman didefinisikan tanpa DOM.
- Peta gabungan untuk satu sampul sama di semua task (tidak bergantung pilihan task) — memang tujuan R5; diuji di HTTP.
- Ini bukan review visual browser (langkah 3 plan induk).

## Verifikasi
- `node 01_notebook/test_r5_heatmap.js` + tiga test JS lama; tiga test Python lama.
- `venv/bin/python 01_notebook/verify_r5_http.py` (server 7861) → `r5_heatmap_verification.json`.
- Manifest handoff: hanya file yang direncanakan berubah.

## Hasil (2026-10-06)
- Changelog disatukan: semua baris `../TRANSFER_CHANGELOG.md` ada di `CHANGELOG.md`; hanya dua entri ringkas proyek yang dibuang. Salinan sebelum penggabungan disimpan di scratchpad sesi, bukan di paket.
- `index.html`: peta utama = `heatmap_padu_url` berlabel gabungan; blok "Bukti task pilihan" memakai `heatmap_url` dengan task + kelas; tanpa fallback berlabel salah; label batch dan petunjuk verifikasi diselaraskan. Flask melayani file dari disk, server `tempo-ui` tidak perlu dimuat ulang.
- `test_r5_heatmap.js` lulus dan **gagal** terhadap `index.html` handoff asli (bukti test bermakna); 3 test JS + 3 test Python lama tetap lulus.
- `verify_r5_http.py` lulus: sampel dataset tiga task → peta gabungan identik (sha `6b2e9015…`), peta task pilihan berbeda per task dan sama dengan peta per task yang diminta; unggahan foto dosen GULA-GULA (judul manual, Task 2 occlusion) → kelas Permainan & Kontes, kedua peta PNG valid dan berbeda. Bukti `04_hasil_eksperimen/revisi_week3/r5_heatmap_verification.json`.
- Belum: review visual desktop/mobile (langkah 3 plan induk).
