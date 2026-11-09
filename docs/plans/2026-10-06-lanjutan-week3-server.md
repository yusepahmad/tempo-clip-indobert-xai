# Plan Lanjutan Week 3 di Server

**Tanggal:** 2026-10-06
**Status:** done

> Ditutup 17 Oktober 2026 sebagai plan yang telah digantikan delivery Week 3–4
> dan konsolidasi source canonical Sprint 0.

## Tujuan
Menutup kekurangan demo Week 3 dan revisi client berdasarkan audit 2026-10-06, dengan bukti yang dapat diperiksa sebelum delivery final. Plan sudah disiapkan untuk diteruskan; pekerjaan implementasi di bawah belum dijalankan.

## Ruang Lingkup
- Server: `research-user@10.12.1.31`.
- Workspace aktif: `/home/research-user/workspace/learn/DEMO_XAI_745_FULL`.
- UI/backend: `02_web_demo/index.html`, `02_web_demo/app.py` bila kontrak respons perlu diperbaiki.
- Regresi: script relevan di `01_notebook/`, termasuk test UI HTML5/loading/state/workspace dan verifikasi HTTP.
- Dokumentasi: `docs/HANDOFF_SERVER.md`, `docs/DELIVERY_WEEK_3.md`, audit delivery, tutorial dan teks delivery yang tersedia dalam paket.
- Bukti baru: `04_hasil_eksperimen/revisi_week3/`; changelog dan manifest/paket final baru.
- Tidak mengubah dataset, label asli, codebook menjadi klaim resmi, atau mengganti baseline dengan checkpoint Kaggle tanpa evaluasi yang mendukung.
- Tidak melanjutkan training Kaggle atau memindahkan seluruh workspace asal.

## Langkah

### 1. Siapkan environment dan baseline di server
1. Baca `AGENTS.md`, `docs/HANDOFF_SERVER.md`, `docs/AUDIT_DELIVERY_WEEK3_20261006.md`, dan plan ini.
2. Periksa Python 3.10.12 yang tersedia, dependensi venv, Node.js, tmux, akses unduhan model dan kapasitas. Ikuti setup CPU di handoff menggunakan Python 3.10; gunakan path workspace aktual di atas, bukan contoh `~/tempo-server`.
3. Jalankan demo di tmux, bind `127.0.0.1:7861`; akses melalui `ssh -N -L 8850:127.0.0.1:7861 research-user@10.12.1.31`.
4. Jalankan regresi baseline sebelum edit. Catat command, versi, hasil dan batas pemeriksaan. Perbaiki setup bila gagal sebelum mengubah produk.

**Selesai bila:** aplikasi dapat diakses melalui tunnel dan hasil baseline tercatat. Paket tidak membawa venv/cache/checkpoint/job lama; jangan menganggap semuanya sudah tersedia.

### 2. Tutup R5: peta utama gabungan tiga task — P1
1. Telusuri renderer yang memakai `d.heatmap_url` dan kontrak `heatmap_padu_url` dari backend.
2. Tampilkan peta gabungan sebagai ringkasan utama dengan label jelas bahwa peta merangkum tiga task.
3. Pertahankan peta task pilihan sebagai bukti terpisah, dengan task/kelas yang sesuai. Atribusi kata dan narasi task pilihan tidak boleh dinyatakan berasal dari peta gabungan.
4. Beri pesan yang jelas jika peta tidak tersedia; jangan diam-diam menampilkan peta task pilihan dengan label gabungan.
5. Tambahkan regresi bermakna untuk pemilihan URL/label dan pergantian task. Uji dataset serta unggahan.

**Selesai bila:** ringkasan utama benar-benar memakai peta gabungan, bukti task pilihan tetap sesuai, dan regresi serta pemeriksaan HTTP lulus.

### 3. Uji UI terbaru di browser — P1
1. Desktop dan mobile: pastikan form, preview, hasil dan navigasi terbaca; textarea memiliki penutup eksplisit dan panel kanan tampil.
2. Uji dataset → analisis → hasil; unggahan → OCR → koreksi judul/teks pendukung panjang → analisis.
3. Periksa loading terlihat sejak request dimulai, pesan proses jelas, tombol busy sesuai, dan sukses/gagal membersihkan indikator.
4. Ganti gambar/task saat request aktif; respons lama tidak boleh menimpa input/hasil baru.
5. Uji tab/keyboard, scroll vertikal, batch kecil, kegagalan gambar rusak, review dan ekspor CSV/JSON/aset.
6. Uji tiga foto dosen dari `06_gambar_revisi/`; simpan input persis dan konfigurasi metode. Kasus GULA LIME bukan validasi ground truth kelas.
7. Simpan screenshot ukuran viewport dan hasil pemeriksaan. Perbaiki temuan, lalu ulangi hanya pemeriksaan yang terdampak.

**Selesai bila:** tidak ada bug kritis alur/layout/loading, dengan bukti browser. Parser/VM/HTTP tidak dihitung sebagai review visual. Jika browser tidak tersedia, lanjutkan langkah independen dan tandai verifikasi visual masih terbuka.

### 4. Sinkronkan dokumentasi dan status — P2
1. Perbarui tutorial dan teks delivery untuk UI tiga langkah, tab hasil, loading OCR/analisis, teks pendukung multiline dan peta gabungan.
2. Nyatakan demo memakai baseline; Kaggle complete tetapi Task2 Macro-F1 turun sehingga checkpoint belum diintegrasikan.
3. Nyatakan kualitas OCR diagnosis 19/30 dan foto dosen 2/3; koreksi manual tersedia. Sasaran 80% adalah usulan, bukan penerimaan client yang diasumsikan.
4. Hapus kebutuhan menunggu codebook resmi yang tidak ada. Codebook operasional dibuat sesuai instruksi user. Tiga review agen bukan tiga pengguna manusia.
5. Buat matriks R1–R5/T01–T12 terbaru dengan status, bukti, batasan dan pekerjaan terbuka. Audit lama dipertahankan sebagai riwayat; hasil baru diberi tanggal.

**Selesai bila:** tutorial sesuai perilaku aplikasi dan laporan tidak menyebut semua revisi selesai tanpa bukti.

### 5. Bangun dan uji paket delivery terbaru — P1
1. Bangun arsip baru dari source setelah R5/UI/docs ditutup. Jangan menimpa arsip handoff atau menyajikan ZIP review lama sebagai versi terbaru.
2. Sertakan dependensi verifikasi dan test UI terbaru; manifest SHA256, changelog, panduan setup serta bukti penerimaan.
3. Verifikasi CRC ZIP, hash seluruh file, kesamaan source dan kelengkapan data/aset yang disertakan. Jangan sertakan venv/cache/credentials/job lokal sebagai dependensi tersembunyi.
4. Ekstrak ke folder bersih dan buat environment baru. Jalankan launcher Linux serta smoke model/HTTP/ekspor. Uji setup/launcher Windows pada Windows bila tersedia; pemeriksaan Linux tidak menggantikannya.
5. Periksa eksport lama yang berisi URL lokal: bedakan bukti historis dari aset portabel. Buat job kecil baru untuk verifikasi; jangan menjalankan audit skala lama dengan hardcoded job/path tanpa penyesuaian.

**Selesai bila:** ZIP cocok source terbaru, setup bersih terbukti pada platform yang diklaim, dan paket tidak membutuhkan instalasi lokal lama.

### 6. Audit penutupan dan serah terima
1. Jalankan pemeriksaan akhir yang relevan setelah perubahan terakhir; catat bukti tanpa mengulang training atau batch 740 jika tidak diperlukan.
2. Tulis verdict terbaru: siap review atau siap final untuk scope yang benar-benar terpenuhi. Cantumkan Windows/browser/riset yang belum terverifikasi jika masih terbuka.
3. Catat perubahan di `CHANGELOG.md`, update status plan/hasil dan berikan lokasi arsip, checksum, cara menjalankan, serta daftar pekerjaan tersisa.

### 7. Jalur riset yang tetap terbuka, setelah penutupan demo
- T04/T05: lengkapi transkripsi headline/supporting/layout dan evaluasi ekstraksi pada set independen; pisahkan anotasi usulan dari ground truth tervalidasi.
- T06/T07: ukur kandidat selector/decoder pada data serta kondisi latensi yang sebanding sebelum mengganti produksi.
- T11 E01/E02: eksperimen perbaikan input dan tuning terkontrol dengan split/checkpoint/konfigurasi yang konsisten, lalu laporkan OOF/per-task dan biaya waktunya.
- Jangan mengubah label asli atau memilih model hanya berdasarkan kenaikan satu task. Integrasi model Kaggle perlu keputusan berbasis evaluasi, bukan karena training sudah selesai.

## Risiko & Asumsi
- Status awal masih siap review baseline, belum final seluruh revisi client.
- Server sudah menerima arsip dan 979 file lolos manifest; environment dan aplikasi belum disiapkan saat plan dibuat.
- Job/aset batch lama dan bobot model tidak dipindah; bukti historis tersedia, tetapi URL heatmap lama tidak portabel.
- Browser dan mesin Windows mungkin tidak tersedia di server. Ini batas bukti yang wajib dilaporkan, bukan alasan menghentikan pekerjaan independen.
- Set diagnosis OCR tidak independen; peningkatan pada set itu saja tidak membuktikan generalisasi.
- User telah mengizinkan codebook operasional dan review sub-agent; tidak perlu meminta sumber resmi yang memang tidak ada.

## Verifikasi
- Python: `venv/bin/python 01_notebook/test_ui_html5.py`, `test_week3_regressions.py`, `test_week3_training_audit.py` menggunakan prefix venv yang sama.
- JavaScript: `node 01_notebook/test_loading_ui.js`, `test_week3_state.js`, `test_workspace_ui.js` menggunakan prefix node yang sama, serta regresi R5 baru.
- HTTP dari `/home/research-user/workspace/learn`: `TEMPO_DEMO_URL=http://127.0.0.1:7861 DEMO_XAI_745_FULL/venv/bin/python DEMO_XAI_745_FULL/01_notebook/verify_week3_http.py`.
- Browser: screenshot dan checklist desktop/mobile, termasuk proses OCR/analisis, error, race, teks panjang, peta gabungan dan task pilihan.
- Paket: SHA256/manifest, ekstraksi bersih, launcher dan smoke per platform yang diklaim.
- Catat hasil nyata dan path artefak; jangan mengubah status menjadi done sebelum langkah scope penerimaan yang diperlukan selesai.

## Prompt untuk melanjutkan di server
> Baca AGENTS.md dan docs/plans/2026-10-06-lanjutan-week3-server.md. Kerjakan penutupan demo Week 3 berurutan: setup/baseline, R5 peta gabungan, smoke UI browser, dokumentasi, paket terbaru dan audit akhir. Pertahankan baseline/dataset/label. Update plan sebelum perubahan scope dan catat changelog setelah perubahan. Jalur riset yang belum selesai dilaporkan terpisah. Jangan klaim visual/Windows/seluruh revisi selesai tanpa bukti.
