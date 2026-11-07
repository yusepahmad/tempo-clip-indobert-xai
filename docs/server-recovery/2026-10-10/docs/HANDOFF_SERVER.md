# Handoff lanjutan di server

Tanggal: 2026-10-06 (handoff pagi; status dimutakhirkan 6 Oktober malam). Arsip `TEMPO_SERVER_HANDOFF_20261006.zip` adalah paket pekerjaan untuk dilanjutkan, **bukan delivery client**. Paket delivery client terbaru adalah `TEMPO_XAI_DELIVERY_WEEK3_20261006.zip` ([plan paket](plans/2026-10-06-paket-delivery-final.md)).

> **Status per 6 Oktober malam.** Bagian "Status server", "Status dan keputusan" dan "Pekerjaan berikutnya" sudah dimutakhirkan. Bagian "Transfer dan setup Linux" dan "Menjalankan tanpa bergantung pada SSH aktif" adalah instruksi handoff pagi (riwayat): server review kini dibuka langsung di `0.0.0.0:7861`, bukan lewat tunnel.

## Mulai membaca

1. `docs/STATUS_REVISI_20261006.md`: verdict dan matriks R1–R5/T01–T12 terbaru (6 Okt malam). `docs/AUDIT_DELIVERY_WEEK3_20261006.md` adalah audit pagi yang disimpan sebagai riwayat.
2. `docs/plan-revisi-demo-xai-tempo.md`: acuan revisi; target metrik di sana merupakan usulan.
3. `docs/DELIVERY_WEEK_3.md` dan `docs/HASIL_FULL_TRAINING_KAGGLE.md`: bukti teknis/model.
4. `AGENTS.md`: wajib plan sebelum perubahan, simpan di docs/plans dan catat hasil di CHANGELOG.

Semua path berikut relatif folder `DEMO_XAI_745_FULL` setelah ekstraksi.

## Status server 6 Okt 2026

- Arsip sudah diekstrak di `/home/yusep/workspace/learn/DEMO_XAI_745_FULL` pada server `10.12.1.31`; 979 file cocok dengan manifest handoff.
- Venv Python 3.10.12 dibuat dengan `uv venv venv --python /usr/bin/python3.10 --seed`, karena paket sistem `python3.10-venv` tidak terpasang (tanpa `ensurepip`). Paket dipasang dengan `venv/bin/python -m pip`; torch 2.14.1+cpu.
- CPU saja: driver NVIDIA tidak berfungsi (`nvidia-smi` gagal).
- Server demo berjalan di tmux `tempo-ui`, log `/home/yusep/workspace/learn/tempo-ui-7861.log`. Atas permintaan user, bind kini `0.0.0.0:7861` (http://10.12.1.31:7861 dari jaringan internal) **tanpa autentikasi**; keputusan autentikasi atau kembali ke `127.0.0.1` masih tertunda. Riwayat: awalnya bind `127.0.0.1:7861` dengan tunnel `ssh -N -L 8850:127.0.0.1:7861 yusep@10.12.1.31`.
- Tautan unduh ZIP delivery: server statis **sementara** `python3 -m http.server 8853` di tmux `tempo-unduh`, hanya folder `/home/yusep/workspace/learn/dist/`, tanpa autentikasi. Matikan setelah user selesai mengunduh.
- Langkah 1–5 [plan lanjutan](plans/2026-10-06-lanjutan-week3-server.md) selesai: baseline server, R5, smoke browser Chromium, sinkronisasi dokumentasi, dan paket delivery + uji instalasi bersih Linux (Windows belum). Langkah 6 (audit penutupan) belum ditandai selesai di plan. Bukti: `04_hasil_eksperimen/revisi_week3/server_baseline_20261006.json`, `r5_heatmap_verification.json`, `browser_smoke_20261006_audit.json` (final 94/94), `browser_smoke_paket_bersih.json` (instalasi bersih 94/94).

## Status dan keputusan yang harus dipertahankan

- Source UI terbaru berada di `02_web_demo/index.html`: panduan tiga langkah, preview nyata, tab hasil, loading OCR/analisis, textarea pendukung 5 baris dan scroll vertikal, serta tab Bukti gambar dengan peta gabungan tiga task (R5) dan blok bukti task pilihan. Tambahan 6 Okt malam: ringkasan tiga task di tab Prediksi dan penjelasan task pilihan di tab Penjelasan; gambar baru (atau berkas sama dipilih lagi) selalu dibaca ulang dan mengganti judul/teks pendukung, dengan label "Gambar aktif"; pembatalan analisis dikirim ke server; pilihan task di view Batch; batas masukan (judul ≤300, pendukung ≤2000 karakter, unggahan ≤25 MB, gambar ekstrem ditolak, maks 2 job batch).
- Bug textarea self-closing **sudah diperbaiki**. Jangan serialisasi textarea menjadi `<textarea .../>`. Verifikasi struktur dengan HTML5, bukan hanya parser toleran.
- Source/backend baseline berfungsi; audit 740/740 berhasil, ekspor/aset/pemulihan lulus. Uji Windows lama adalah backend/folder terisolasi, bukan browser UI terakhir atau clean-install paket.
- Codebook resmi tidak tersedia. User meminta codebook operasional 25 kelas dibuat; jangan kembali meminta sumber resmi yang tidak ada.
- Tabel ground truth disiapkan dan tiga tinjauan sub-agent sudah dilakukan atas permintaan user; ini bukan uji manusia. Usulan transkripsi tidak mengubah dataset.
- Full Kaggle COMPLETE dan audit OOF lulus. Macro-F1 Task1/2/3 = 0,5139 / 0,2461 / 0,3699. Baseline demo tetap dipakai karena Task2 baseline 0,3197 lebih baik. Checkpoint Kaggle belum diunduh/diintegrasikan; laporan fine-tuning bukan perilaku demo.
- OCR versi aplikasi terakhir: judul tepat 41/60 (validasi kedua) dan 47/60 (validasi pertama), keduanya set yang sudah terkontaminasi; angka saat kode dibekukan 43/60 dan 38/60 ([audit OCR](AUDIT_OCR_URUTAN_20261006.md)). Riwayat 5 Okt: 19/30 pada set diagnosis. Gambar dosen 2/3. Sasaran usulan 80% belum tercapai; koreksi manual tetap diperlukan. Beamsearch/kandidat selector tidak diterapkan hanya untuk menaikkan angka. Batas 6 baris judul dipertahankan (keputusan user).
- Foto asli GULA-GULA: LIME Task2 dengan judul manual dan supporting kosong menghasilkan DEMO positif; ini bukan validasi kelas prediksi. Artefak ada di `04_hasil_eksperimen/revisi_week3/audit_gula_original_lime.json`. Pada smoke browser 6 Okt (judul OCR yang sama, teks pendukung hasil OCR terisi), ketiga kata GULA-GULA, DEMO dan BURUH bernilai negatif (`browser_smoke_20261006.json`). Hasil atribusi bergantung pada input.

## Pekerjaan berikutnya, urut prioritas

1. ~~**R5:** peta utama gabungan semua task~~ — **selesai 6 Okt.** Peta utama tab Bukti gambar = `heatmap_padu_url` berlabel gabungan tiga task; blok "Bukti task pilihan" memakai `heatmap_url` dengan task dan kelas. Lihat [sub-plan R5](plans/2026-10-06-r5-peta-gabungan-dan-changelog.md).
2. ~~Uji visual browser desktop/mobile~~ — **selesai 6 Okt untuk Chromium headless**: 80/80 cek (diulang 83/83 setelah langkah 4), 24 screenshot desktop 1440×900 dan mobile 390×844. Lihat [sub-plan smoke](plans/2026-10-06-smoke-browser-ui.md). Firefox/Safari, Windows dan pengguna manusia belum diuji.
3. ~~Sinkronkan tutorial, batasan, teks delivery dan laporan status~~ — **disinkronkan 6 Okt**, termasuk teks petunjuk mobile dan pesan gagal batch tanpa path absolut. Lihat [sub-plan sinkronisasi](plans/2026-10-06-sinkronisasi-docs-dan-catatan-minor.md) dan `docs/STATUS_REVISI_20261006.md`.
4. ~~Bangun paket final terpisah; cek source, ZIP dan launcher dari setup bersih~~ — **selesai 6 Okt untuk Linux**: `TEMPO_XAI_DELIVERY_WEEK3_20261006.zip` + `DELIVERY_MANIFEST.json`, instalasi bersih lulus 70 Python + 4 JS + 13 frontend + smoke 94/94. **Windows belum diuji.** Lihat [plan paket](plans/2026-10-06-paket-delivery-final.md).
5. Pisahkan acceptance demo dari sasaran riset OCR/ground truth/E01/E02. Jangan menyebut semua revisi 100% selesai sebelum bukti mendukung.

## Transfer dan setup Linux

*Riwayat handoff pagi* (saat itu alamat/OS server belum diberikan); instruksi ini mengasumsikan Linux dan Python 3.10/3.11. Ganti `USER@SERVER` dengan tujuanmu. Untuk versi pustaka persis yang lulus semua test di server, pakai `requirements-lock-linux.txt` (lihat `MULAI_DARI_SINI.md`).

Di komputer asal:

```bash
scp TEMPO_SERVER_HANDOFF_20261006.zip USER@SERVER:~/
```

Di server (unzip, Python 3.10/3.11 dan tmux harus tersedia):

```bash
mkdir -p ~/tempo-server
unzip ~/TEMPO_SERVER_HANDOFF_20261006.zip -d ~/tempo-server
cd ~/tempo-server/DEMO_XAI_745_FULL
python3.11 -m venv venv
venv/bin/python -m pip install --upgrade pip
venv/bin/python -m pip install --index-url https://download.pytorch.org/whl/cpu torch torchvision
venv/bin/python -m pip install -r requirements.txt
venv/bin/python -m pip install -r requirements-verification.txt
```

Gunakan `python3.10` jika itu versi yang tersedia. Ini setup CPU untuk meneruskan demo; pemakaian GPU server dapat disiapkan terpisah setelah jenis GPU/driver diketahui. Node.js dibutuhkan untuk regresi JavaScript. Encoder CLIP/IndoBERT dan model EasyOCR diunduh pada pemakaian pertama: internet dan ruang disk cukup diperlukan. Jangan memasang `HF_HUB_OFFLINE=1` sebelum cache model tersedia.

## Menjalankan tanpa bergantung pada SSH aktif

```bash
cd ~/tempo-server/DEMO_XAI_745_FULL
tmux new -s tempo-ui
cd 02_web_demo
OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 ../venv/bin/python -u -c "import torch; torch.set_num_threads(4); from app import app; app.run(host='127.0.0.1', port=7861, debug=False)"
```

Detach tmux dengan **Ctrl+B lalu D**. Kembali dengan `tmux attach -t tempo-ui`. Ctrl+C di dalam tmux menghentikan server. Ini server demo untuk review melalui tunnel, bukan konfigurasi hosting publik. (Server review 6 Okt malam dijalankan dengan perintah yang sama tetapi `host='0.0.0.0'` atas permintaan user, tanpa tunnel dan tanpa autentikasi.)

Di komputer asal, buka terminal baru:

```bash
ssh -N -L 8850:127.0.0.1:7861 USER@SERVER
```

Buka **http://127.0.0.1:8850**. Port lokal 8850 dipakai agar tidak berbenturan dengan demo lokal 7861. Jika memakai launcher bawaan, port defaultnya 7860; sesuaikan tunnel dan URL verifikasi. Jangan membuka port Flask langsung ke publik untuk kebutuhan review ini.

## Verifikasi dari root paket

```bash
venv/bin/python 01_notebook/test_ui_html5.py
venv/bin/python 01_notebook/test_week3_regressions.py
venv/bin/python 01_notebook/test_week3_training_audit.py
venv/bin/python 01_notebook/test_batch_error_message.py
venv/bin/python 01_notebook/test_narasi_ringkasan.py
venv/bin/python 01_notebook/test_ocr_urutan.py
(cd 01_notebook && ../venv/bin/python -W ignore -m unittest test_audit_backend)   # memuat model; cache/job ke folder sementara
venv/bin/python 01_notebook/test_audit_frontend.py   # Playwright + mock, perlu server hidup untuk halaman
node 01_notebook/test_loading_ui.js
node 01_notebook/test_week3_state.js
node 01_notebook/test_workspace_ui.js
node 01_notebook/test_r5_heatmap.js
```

Dengan server hidup di port 7861:

```bash
venv/bin/python 01_notebook/verify_r5_http.py
```

Skrip ini menulis `04_hasil_eksperimen/revisi_week3/r5_heatmap_verification.json` (path relatif file skrip). Bukti R5 6 Okt akan tertimpa, jadi salin dulu bila perlu dibandingkan.

Smoke browser (Playwright, Chromium headless). Dependensinya terpisah dari aplikasi:

```bash
venv/bin/python -m pip install -r requirements-browser.txt
venv/bin/python -m playwright install chromium
venv/bin/python 01_notebook/smoke_browser_week3.py
```

Skrip ini menulis `04_hasil_eksperimen/revisi_week3/browser_smoke_<TAG>.json` beserta folder screenshot, dan membuat job batch baru di `_jobs`. `<TAG>` diambil dari `SMOKE_TAG`, defaultnya tanggal hari ini. Pakai `SMOKE_TAG` lain agar bukti `browser_smoke_20261006` tidak tertimpa. Kedua skrip HTTP/browser membaca `TEMPO_DEMO_URL` (default `http://127.0.0.1:7861`).

Script HTTP historis `verify_week3_http.py` menulis ke path relatif `DEMO_XAI_745_FULL/04_hasil_eksperimen/revisi_week3`. Jika dijalankan dari folder induk paket, skrip ini **menimpa bukti historis** `revisi_week3/{task*,batch_export*,http_verification}.json`. Jalankan dari folder staging terpisah, seperti pada baseline 6 Okt, lalu salin hasil yang diperlukan:

```bash
PKG=/home/yusep/workspace/learn/DEMO_XAI_745_FULL   # sesuaikan bila paket diekstrak di tempat lain
STAGE=$(mktemp -d)
mkdir -p "$STAGE/DEMO_XAI_745_FULL/04_hasil_eksperimen"
cd "$STAGE" && TEMPO_DEMO_URL=http://127.0.0.1:7861 "$PKG/venv/bin/python" "$PKG/01_notebook/verify_week3_http.py"
ls "$STAGE/DEMO_XAI_745_FULL/04_hasil_eksperimen/revisi_week3"   # salin yang perlu ke folder bukti bertanggal
```

Jangan menjalankan `verify_scale740.py`/`finalize_week3_delivery.py` begitu saja: keduanya mengacu job lokal lama, port tertentu dan layout repo asal. Bukti skala lama ada dalam paket, tetapi job/aset `_jobs` tidak dipindah. Untuk uji skala baru buat job/launch record baru dan sesuaikan audit secara eksplisit. Jangan menulis metrik akurasi dari batch in-sample.

## Isi dan batas paket

Source terbaru, 740 gambar/data/fitur baseline, docs/plan/aturan, script training/QA dan metrik fine-tuning disertakan. Venv, cache, job/aset lokal, checkpoint besar, arsip bersarang dan credentials tidak disertakan. Tiga foto dosen disalin ke `06_gambar_revisi/` untuk regresi lanjutan; file asli tidak diedit. URL heatmap pada ekspor lama bukan tautan portabel. Dataset/label/image asli harus tetap dipertahankan.

## Prompt untuk Codex di server

Salin setelah membuka folder paket:

> Baca AGENTS.md, docs/HANDOFF_SERVER.md, docs/STATUS_REVISI_20261006.md dan docs/plans/2026-10-06-lanjutan-week3-server.md. Langkah 1–5 sudah selesai: R5, smoke browser Chromium, sinkronisasi dokumentasi, dan paket delivery `TEMPO_XAI_DELIVERY_WEEK3_20261006.zip` yang lulus uji instalasi bersih Linux. Lanjutkan langkah 6 (audit penutupan) dan uji instalasi bersih Windows bila mesin Windows tersedia. Server review berjalan di 0.0.0.0:7861 tanpa autentikasi; keputusan autentikasi menunggu user. Pertahankan dataset/label dan baseline; model Kaggle belum diintegrasikan. Codebook operasional serta evaluasi agen sudah dibuat atas instruksi saya. Buat plan di docs/plans sebelum perubahan dan catat CHANGELOG setelah perubahan. Jangan mengklaim seluruh revisi selesai tanpa bukti. Jika browser/server belum tersedia, jelaskan keterbatasan dan lanjutkan pekerjaan independen.
