# Sinkronisasi Dokumentasi dan Dua Catatan Minor (Langkah 4)

**Tanggal:** 2026-10-06
**Status:** done (2026-10-06)

Sub-plan langkah 4 dari [2026-10-06-lanjutan-week3-server.md](2026-10-06-lanjutan-week3-server.md), ditambah dua catatan minor dari [smoke browser](2026-10-06-smoke-browser-ui.md) atas persetujuan user.

## Tujuan
1. Dokumen serah terima menggambarkan aplikasi dan status yang **sekarang**, bukan narasi 189 sampul/Week 1–2, tanpa mengklaim seluruh revisi selesai.
2. Teks petunjuk UI tidak lagi salah di mobile ("sebelah kanan"/"panel kiri").
3. Pesan gagal item batch tidak membocorkan path absolut server.

## Ruang Lingkup
**Kode (dikerjakan agen utama):**
- `02_web_demo/index.html`: lima teks arah layout ("sebelah kanan", "panel kiri") diganti rujukan netral nama panel ("panel Mulai di sini", "panel Sampul pilihan") yang benar di desktop dan mobile. ID/struktur tidak berubah.
- `02_web_demo/batch_jobs.py`: pesan gagal item disusun helper `pesan_gagal()` — `UnidentifiedImageError` → "Gambar tidak terbaca: format berkas tidak dikenali"; error lain tetap `Tipe: pesan` dengan path absolut (POSIX/Windows) diganti nama berkasnya. Traceback lengkap tetap dicetak ke log server. Manifest job lama tidak diubah.
- Regresi baru `01_notebook/test_batch_error_message.py`.

**Dokumen (dikerjakan sub-agent paralel, diperiksa agen utama):**
- Kelompok A: `01_TUTORIAL.md`, `MULAI_DARI_SINI.md`.
- Kelompok B: `00_BACA_DULU.md`, `TEKS_DELIVERY.md`.
- Kelompok C: `02_BATASAN_TEKNIS.md`, `docs/DELIVERY_WEEK_3.md`.
- Kelompok D: baru `docs/STATUS_REVISI_20261006.md` (matriks R1–R5/T01–T12 terbaru) dan `docs/HANDOFF_SERVER.md` (status server + perintah verifikasi terbaru).
- `docs/AUDIT_DELIVERY_WEEK3_20261006.md` **tidak diubah** (riwayat); cukup dirujuk. `docs/plan-revisi-demo-xai-tempo.md`, laporan Week 1/2, codebook, dataset/label/model **tidak disentuh**.

## Lembar fakta (satu-satunya sumber angka/istilah untuk semua dokumen)
- Dataset 740 sampul (dataset final). Task 1 isu (10 kelas), Task 2 domain sumber metafora (7), Task 3 tipe entitas (8); 25 kelas, codebook operasional dibuat atas instruksi user (bukan codebook resmi; tidak perlu menunggu codebook resmi).
- Model demo = **baseline** CLIP ViT-B/32 + IndoBERT beku + head MTL. Macro-F1 5-fold: Task1 0,438, Task2 0,320 (0,3197), Task3 0,276. Full fine-tuning Kaggle COMPLETE: 0,5139 / 0,2461 / 0,3699; Task 2 turun → **baseline tetap dipakai**, checkpoint belum diunduh/diintegrasikan.
- UI: navigasi **Analisis / Batch / Panduan**. Panel input "Mulai di sini" dengan mode **Dataset / Unggah gambar**; langkah "1. Pilih sampul dari dataset" atau "1. Pilih gambar dari laptop", "2. Periksa judul utama", "Teks pendukung (boleh kosong)" (textarea 5 baris, dapat diperbesar, teks panjang/multibaris didukung), "3. Pilih penjelasan yang ingin dilihat" (Ranah metafora (Task 2) [baku], Topik utama (Task 1), Pihak yang disorot (Task 3)), tombol **Analisis sampul**. Panel "Sampul pilihan" menampilkan preview. Unggahan menjalankan OCR otomatis dengan overlay "Sedang membaca teks gambar" dan daftar "Pilihan judul hasil pembacaan otomatis"; teks yang disunting pengguna tidak ditimpa OCR saat gambar diganti (ada pesan).
- Loading: overlay "Sedang menganalisis sampul", tombol "Menganalisis…"; mengganti input/task saat proses membatalkan hasil lama.
- Hasil lima tab: **Prediksi**, **Bukti gambar**, **Bukti kata**, **Penjelasan**, **Bandingkan label** (navigasi panah/Home/End).
- **R5 (ditutup 6 Okt):** tab Bukti gambar menampilkan **peta gabungan tiga task** sebagai peta utama (rata-rata peta per task yang dinormalisasi; sama untuk semua pilihan task), lalu blok terpisah **"Bukti task pilihan: <task> — kelas <kelas>"** berisi peta task pilihan yang menjadi dasar penjelasan/zona. Peta gabungan bukan dasar atribusi kata/narasi. Peta per task tetap di "Lihat peta panas per task (tampilan teknis)".
- Atribusi kata: LIME baku di analisis satuan (≈15–20 detik per analisis di CPU server), occlusion pilihan cepat di batch. Penjelasan dirangkai dari bukti (bukan LLM), penanda asal MODEL/ANOTATOR/CODEBOOK/GABUNGAN.
- Batch: ID dataset dan/atau gambar unggahan, metode Occlusion/LIME, item unggahan menunggu konfirmasi judul, ekspor CSV/JSON, lanjut/ulang item gagal, tautan "Buka peta gabungan tiga task". Batch dataset = in-sample, bukan metrik akurasi. Skala 740/740 lulus (bukti historis mesin asal).
- OCR: selector produksi 19/30 (63,3%) pada set diagnosis (bukan set independen); foto dosen 2/3 judul tepat (GULA-GULA, CUKAI tepat; WASWAS terbaca `VJASWAS RUPIAH` di server ini, `VJJASWAS` di mesin asal). Sasaran 80% adalah usulan, belum tercapai; koreksi manual tersedia dan wajib diperiksa.
- Foto dosen via browser (Task 2, LIME, judul final): GULA-GULA → Permainan & Kontes; WASWAS (dikoreksi) → Permainan & Kontes; CUKAI → Konsumsi & Transaksi. Kelas unggahan tidak divalidasi. Audit sebelumnya: LIME GULA-GULA dengan supporting kosong memberi DEMO positif — bukan validasi kelas.
- Bukti 6 Okt (server 10.12.1.31, Python 3.10.12, torch 2.14.1+cpu, CPU): baseline `revisi_week3/server_baseline_20261006.json`; R5 `r5_heatmap_verification.json`; smoke browser Chromium headless desktop 1440×900 + mobile 390×844 **80/80** `browser_smoke_20261006.json` + 24 screenshot. Belum: Firefox/Safari, Windows clean install paket terbaru, uji pengguna manusia (tiga tinjauan sub-agent ≠ uji manusia).
- Perintah verifikasi (dari folder paket): `venv/bin/python 01_notebook/test_ui_html5.py`, `test_week3_regressions.py`, `test_week3_training_audit.py`, `test_batch_error_message.py`; `node 01_notebook/test_loading_ui.js`, `test_week3_state.js`, `test_workspace_ui.js`, `test_r5_heatmap.js`; HTTP `verify_r5_http.py` (server hidup); browser `pip install -r requirements-browser.txt` lalu `smoke_browser_week3.py`. `verify_week3_http.py` menulis ke path relatif `DEMO_XAI_745_FULL/04_hasil_eksperimen/revisi_week3` dari folder induk dan **menimpa** bukti historis — jalankan dari folder staging.
- Launcher paket: `jalankan_linux.sh` / `jalankan_windows.bat` → http://127.0.0.1:7860. Server review 6 Okt: tmux `tempo-ui`, 127.0.0.1:7861, tunnel `ssh -N -L 8850:127.0.0.1:7861 research-user@10.12.1.31` → http://127.0.0.1:8850.
- Notebook `DEMO_XAI_TEMPO.ipynb` sudah diarahkan ke dataset 740 sejak 29 Sep (bukan lagi 189).
- Yang masih terbuka: paket ZIP final + setup bersih (langkah 5), Windows/browser lain/pengguna manusia, riset OCR/ground truth (T04–T07), E01/E02 (T11), keputusan integrasi checkpoint.

## Langkah
1. Perbaiki dua catatan minor + regresi; jalankan semua regresi.
2. Jalankan sub-agent A–D paralel dengan lembar fakta; larangan: mengubah file di luar kelompoknya, mengarang angka, menyebut "100% selesai".
3. Periksa diff tiap dokumen terhadap lembar fakta; grep sisa narasi usang ("189 sampul" sebagai status kini, "740 dari 745", "belum dijalankan ulang", "Peta utama memakai task pilihan", "batch belum tersedia").
4. Ulangi smoke browser bagian terdampak (teks petunjuk) + regresi.
5. Catat hasil di plan, plan induk, CHANGELOG.

## Risiko & Asumsi
- Riwayat (laporan Week 1/2, audit 6 Okt, changelog lama) dipertahankan sebagai riwayat; hanya dokumen "pintu masuk" dan status yang diperbarui.
- Sub-agent bisa salah tafsir; semua hasil diperiksa agen utama sebelum dicatat.

## Verifikasi
- Regresi Python/JS + test baru lulus; smoke browser terdampak lulus.
- Grep narasi usang kosong di dokumen pintu masuk; angka di dokumen cocok lembar fakta.
- Manifest handoff: hanya file yang direncanakan berubah.

## Hasil (2026-10-06)
- **Kode:** lima teks arah layout di `index.html` diganti nama panel; `batch_jobs.py` memakai `pesan_gagal()` (gambar rusak → "Gambar tidak terbaca: format berkas tidak dikenali", path absolut → nama berkas, traceback ke log server). Tambahan di luar daftar awal: komentar usang di `app.py` ("peta yang dinarasikan adalah peta terpadu") dibetulkan — kode memang memakai peta task pilihan; perilaku tidak berubah. Server `tempo-ui` direstart agar modul batch baru termuat.
- **Regresi:** `test_batch_error_message.py` lulus dan gagal terhadap `batch_jobs.py` handoff (pesan lama); 4 test Python + 4 test JS lulus.
- **Smoke ulang:** `SMOKE_TAG=20261006_langkah4`, **83/83** lulus termasuk cek baru "tanpa arah kiri/kanan" (desktop+mobile) dan "pesan gagal batch tanpa path server". Bukti `browser_smoke_20261006_langkah4.json` + folder screenshot; run 80/80 langkah 3 dipertahankan.
- **Dokumen:** sub-agent A–D memperbarui `01_TUTORIAL.md` (bagian baru B "Memakai aplikasi"; huruf bagian lama bergeser B→C … E→F, tidak ada rujukan eksternal ke huruf lama), `MULAI_DARI_SINI.md`, `00_BACA_DULU.md`, `TEKS_DELIVERY.md`, `02_BATASAN_TEKNIS.md`, `docs/DELIVERY_WEEK_3.md`, `docs/HANDOFF_SERVER.md`, dan baru `docs/STATUS_REVISI_20261006.md`. Agen utama memeriksa: grep narasi usang bersih, angka konsisten dengan lembar fakta, bagian inti tutorial dibaca. Koreksi agen utama: rujukan smoke diperbarui ke run 83/83, kalimat R4 di `TEKS_DELIVERY.md`, placeholder `/PATH/KE/` di HANDOFF diganti perintah staging nyata (dijalankan persis dan lulus).
- **Koreksi faktual dari sub-agent yang diverifikasi:** LIME aplikasi memakai 120 varian (`n_sampel=120` di `xai_core.py`); 200 hanya pada uji banding. Bagian 5 BATASAN kini menjelaskan penjelasan berbasis bukti terikat task (`explanation_evidence.py`).
- **Temuan R4 (perlu keputusan user):** foto GULA-GULA, Task 2, LIME, judul "GULA-GULA DEMO BURUH" + teks pendukung hasil OCR (berisi judul artikel lain di sampul) → ketiga kata negatif (−0,003/−0,011/−0,015), deterministik di dua run dan direproduksi via HTTP. Dengan teks pendukung kosong (audit pagi) DEMO positif. Tab Penjelasan menyatakan "Tidak ada kata dengan kontribusi positif untuk kelas yang dijelaskan". Didokumentasikan apa adanya di STATUS/BATASAN/DELIVERY/TEKS_DELIVERY/HANDOFF; tidak diubah karena ini perilaku model/atribusi, bukan bug UI.
