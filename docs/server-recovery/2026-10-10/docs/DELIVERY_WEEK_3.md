# Delivery Week 3 — revisi demo XAI

Dimutakhirkan: 2026-10-06 (malam); laporan awal 2026-10-05. Status: **paket delivery revisi Week 3** dengan model **baseline** (`TEMPO_XAI_DELIVERY_WEEK3_20261006.zip`, berisi `DELIVERY_MANIFEST.json` dan `requirements-lock-linux.txt`). Paket diuji dari instalasi bersih di Linux, lihat [docs/plans/2026-10-06-paket-delivery-final.md](plans/2026-10-06-paket-delivery-final.md). Masih terbuka: instalasi bersih Windows, browser selain Chromium, uji pengguna manusia, sasaran OCR 80%, E01/E02, integrasi checkpoint Kaggle, dan autentikasi server (keputusan user).
Plan: [implementasi](plans/2026-10-05-implementasi-week3.md), [backlog lengkap](plans/2026-10-05-week3-dan-revisi-demo-xai.md) dan [lanjutan di server](plans/2026-10-06-lanjutan-week3-server.md).
Matriks status R1–R5/T01–T12 terbaru: [STATUS_REVISI_20261006.md](STATUS_REVISI_20261006.md).

## Pembaruan 6 Oktober 2026 (malam)

Perubahan sesudah sinkronisasi dokumen sore 6 Oktober. Path bukti relatif terhadap `04_hasil_eksperimen/revisi_week3/`, kecuali yang diawali `01_notebook/`, `02_web_demo/` atau `docs/`.

| Pekerjaan | Hasil | Bukti |
|---|---|---|
| Narasi ringkasan dan penjelasan | Narasi tetap disusun dengan templat, tanpa LLM. Tab Prediksi berisi ringkasan awam tiga task (isu, pihak yang disorot, kiasan), tingkat keyakinan, dan perbandingan dengan label anotator untuk mode dataset. Tab Penjelasan berisi task pilihan saja, dalam blok "Mengapa <kelas>?", "Arti kelas ini", "Catatan anotator" (hanya catatan milik task itu) dan "Yang perlu dicek". Isi kedua tab tidak lagi sama | `02_web_demo/explanation_evidence.py`, `01_notebook/test_narasi_ringkasan.py`, `browser_smoke_20261006_narasi.json`; [plan](plans/2026-10-06-narasi-ringkasan-penjelasan.md) |
| Audit OCR urutan kata | Teks pendukung disusun menurut tata letak (baris, lalu kolom/paragraf, dengan deck di bawah judul lebih dulu). Baris lanjutan judul berhuruf hias disambung, dan logo "TEMPO" yang salah baca serta tagline huruf berjarak disaring. Validasi independen 60 sampul: teks pendukung berurutan sempurna 13→35/56, judul tepat 41→43/60. Validasi kedua 60 sampul (per sore): judul tepat 37→39/60 tanpa regresi judul. Keputusan user: batas 6 baris judul dipertahankan, meski CER judul naik pada judul yang sudah salah pilih blok | `docs/AUDIT_OCR_URUTAN_20261006.md`, `ocr_audit_urutan_20261006.json`, `01_notebook/test_ocr_urutan.py`; [plan](plans/2026-10-06-audit-ocr-urutan-kata.md) |
| Sampah teks baku OCR | Blok utuh berikut dibuang: footer "majalah.tempo.co / mingguan" yang salah baca, label rubrik salah baca, harga/ISSN rusak, potongan acak huruf+angka berkeyakinan rendah, dan pecahan logo raksasa. Presisi kata pendukung naik di keempat set audit, tanpa judul tepat yang turun. Bersama perbaikan audit kode, versi aplikasi terakhir: judul tepat 41/60 pada validasi kedua dan 47/60 pada validasi pertama (kedua set kini terkontaminasi) | [plan](plans/2026-10-06-ocr-sampah-teks-baku.md), `docs/AUDIT_OCR_URUTAN_20261006.md` bagian "Angka versi aplikasi terakhir" |
| Unggah gambar | Berkas yang sama bila dipilih lagi kini dibaca ulang dan hasil lamanya dibatalkan. Gambar baru selalu mengganti judul dan teks pendukung, termasuk yang sudah disunting untuk gambar sebelumnya. Ketikan selama OCR gambar yang sama tetap dilindungi. Nama berkas tampil sebagai "Gambar aktif: …" | `browser_smoke_20261006_unggah.json` (93/93), `browser_smoke_20261006_judul.json` (94/94); plan [berkas sama](plans/2026-10-06-fix-unggah-file-sama.md), [judul diganti](plans/2026-10-06-judul-ganti-saat-gambar-baru.md) |
| Audit kode frontend/backend/modul | XSS lewat pesan OCR dan nilai dinamis ditutup. Ada batas sumber daya: judul ≤300 karakter, teks pendukung ≤2000, unggahan analisis/OCR ≤25 MB, gambar dengan sisi >8000 px atau rasio >5:1 ditolak, dan paling banyak 2 job batch aktif/antre. Analisis yang dibatalkan di browser ikut dibatalkan di server (`/api/analisis/batal`; uji nyata 30,2→24,6 detik). Status batch `failed` muncul bila semua item gagal. Pilihan task tersedia di view Batch. Tidak ada path server di respons, NaN dataset tidak lagi tampil "nan", dan CSV aman dari formula. Gambar lebih dari 40 MP juga ditolak, gambar yang lolos diperkecil ke sisi terpanjang 2000 px, dan galat dikembalikan sebagai JSON. Penjelasan task tidak lagi memuat catatan anotator task lain, dan filter rubrik OCR tidak lagi membuang kata judul sah ("INVESTASI", "SERANGAN"). Autentikasi belum ditambahkan (menunggu keputusan user) | `01_notebook/test_audit_backend.py` (33), `01_notebook/test_audit_frontend.py` (13), `browser_smoke_20261006_audit.json`; [plan](plans/2026-10-06-audit-bug-kode.md) |
| Paket delivery | `TEMPO_XAI_DELIVERY_WEEK3_20261006.zip` dengan `DELIVERY_MANIFEST.json` (SHA256 tiap berkas) dan `requirements-lock-linux.txt` (versi pustaka yang terbukti lulus semua test di server; `requirements.txt` hanya batas bawah). Diuji dari instalasi bersih di Linux: 70 test Python, 4 JS, 13 frontend, `verify_r5_http.py`, `verify_week3_http.py` (staging) dan smoke browser 94/94 lulus; Windows belum diuji | `browser_smoke_paket_bersih.json`; [plan paket](plans/2026-10-06-paket-delivery-final.md) |
| Notebook | Teks `01_notebook/DEMO_XAI_TEMPO.ipynb` dimutakhirkan (blok "Pembaruan 6 Oktober" di sel pertama: beda notebook metodologi baseline dengan aplikasi); sel kode dan output tidak berubah | [plan notebook](plans/2026-10-06-notebook-pemutakhiran.md) |

**Bukti akhir:** smoke browser final **94/94** (`browser_smoke_20261006_audit.json`, Chromium headless desktop 1440×900 + mobile 390×844), dan test **70 Python + 13 frontend + 4 JS** lulus (diulang dari instalasi bersih Linux, smoke `browser_smoke_paket_bersih.json` 94/94). Dengan versi aplikasi terakhir, judul OCR tepat 68–78% pada dua set validasi 60 sampul (41/60 dan 47/60; cenderung optimistis karena kedua set ikut dipakai saat perbaikan, angka saat kode dibekukan 63–72%). Sasaran usulan 80% belum tercapai, jadi koreksi manual tetap wajib. Smoke otomatis bukan uji pengguna manusia, dan browser selain Chromium serta Windows belum diuji.

## Pembaruan 6 Oktober 2026 (server, siang–sore)

Pekerjaan langkah 1–4 [plan lanjutan](plans/2026-10-06-lanjutan-week3-server.md) di server review `10.12.1.31`. Bagian-bagian setelah pembaruan ini (Perubahan aplikasi sampai Bukti tambahan penutupan teknis) adalah catatan 5–6 Oktober dari mesin asal dan dipertahankan sebagai riwayat bukti; blok perintah verifikasi dan status delivery sudah dimutakhirkan. [Audit 6 Oktober pagi](AUDIT_DELIVERY_WEEK3_20261006.md) tidak diubah.

Path bukti relatif terhadap `04_hasil_eksperimen/revisi_week3/`, kecuali yang diawali `01_notebook/`, `02_web_demo/` atau `docs/`.

| Pekerjaan | Hasil | Bukti |
|---|---|---|
| Setup server dan baseline | Python 3.10.12 (venv), torch 2.14.1+cpu, transformers 5.18.0, CPU saja. Sebelum perubahan: 3 regresi Python dan 3 regresi JS lulus; HTTP model nyata tiga task, judul manual dan batch (satu berhasil, satu gagal) lulus; OCR foto dosen 2/3 tepat. Demo berjalan di tmux `tempo-ui`, `127.0.0.1:7861` | `server_baseline_20261006.json`; output HTTP dan `pip_freeze.txt` di `server_baseline_20261006/` |
| R5 ditutup | Tab Bukti gambar menampilkan **peta gabungan tiga task** sebagai peta utama (rata-rata peta per task yang dinormalisasi; sama untuk semua pilihan task), lalu blok **"Bukti task pilihan: <task> — kelas <kelas>"** berisi peta task pilihan yang menjadi dasar penjelasan/zona. Peta gabungan bukan dasar atribusi kata/narasi. Bila peta gabungan tidak ada, UI menulis "tidak tersedia", tidak menampilkan peta task berlabel gabungan. Peta per task tetap di "Lihat peta panas per task (tampilan teknis)"; tautan batch menjadi "Buka peta gabungan tiga task" | `01_notebook/test_r5_heatmap.js` (gagal pada UI lama, lulus pada UI baru); `r5_heatmap_verification.json` (sampel dataset tiga task: hash peta gabungan identik, peta task pilihan berbeda per task; unggahan foto GULA-GULA); [sub-plan R5](plans/2026-10-06-r5-peta-gabungan-dan-changelog.md) |
| Smoke browser | **80/80** cek lulus, Chromium headless (Playwright), desktop 1440×900 dan mobile 390×844, 24 screenshot. Mencakup halaman awal, dataset → analisis LIME dengan loading, lima tab hasil, R5, keyboard tab, race ganti task/ganti gambar, kegagalan jaringan, unggah + OCR + teks pendukung panjang multibaris, tiga foto dosen, batch kecil dengan ekspor CSV/JSON, katalog 25 kelas | `browser_smoke_20261006.json`, `browser_smoke_20261006/`; [sub-plan smoke](plans/2026-10-06-smoke-browser-ui.md) |
| Perbaikan tata letak | Blok "Bukti task pilihan" menyisakan kolom kanan kosong di desktop; keterangan dipindah ke samping peta (mobile tetap bertumpuk) | `02_web_demo/index.html`; screenshot `desktop_03_dataset_visual.png`, `mobile_03_dataset_visual.png` |
| Dua catatan minor smoke diperbaiki | (1) Teks petunjuk arah layout ("sebelah kanan", "panel kiri") diganti rujukan netral nama panel ("panel Mulai di sini", "panel Sampul pilihan") yang benar di desktop dan mobile. (2) Pesan gagal item batch tidak lagi memuat path absolut server: gambar tak terbaca → "Gambar tidak terbaca: format berkas tidak dikenali"; error lain memakai nama berkas saja. Traceback lengkap tetap di log server | `02_web_demo/index.html`, `02_web_demo/batch_jobs.py`, regresi `01_notebook/test_batch_error_message.py`; [sub-plan sinkronisasi](plans/2026-10-06-sinkronisasi-docs-dan-catatan-minor.md) |
| Changelog disatukan | Isi `../TRANSFER_CHANGELOG.md` digabung ke `CHANGELOG.md` proyek sehingga paket memuat satu riwayat | `CHANGELOG.md` |

Hasil foto dosen di smoke browser (Task 2, LIME, judul final): GULA-GULA → Permainan & Kontes; WASWAS (OCR `VJASWAS RUPIAH`, dikoreksi) → Permainan & Kontes; CUKAI → Konsumsi & Transaksi. Kelas unggahan tidak divalidasi. Audit pagi `audit_gula_original_lime.json` (GULA-GULA, judul manual, teks pendukung kosong) memberi DEMO positif; pada smoke, dengan teks pendukung terisi hasil OCR, ketiga kata judul GULA-GULA bernilai negatif. Atribusi bergantung pada input, dan keduanya bukan validasi kelas.

Batas bukti 6 Oktober: smoke adalah Chromium headless otomatis — bukan Firefox/Safari, bukan Windows, dan bukan uji pengguna manusia. Run 80/80 diambil sebelum dua perbaikan minor di atas; setelah perbaikan smoke diulang lengkap (`SMOKE_TAG=20261006_langkah4`) dan lulus 83/83, termasuk cek teks petunjuk tanpa arah kiri/kanan dan pesan gagal batch tanpa path server (`browser_smoke_20261006_langkah4.json`). Skala 740/740 tidak diulang di server (bukti historis mesin asal). Versi pustaka server lebih baru dari mesin asal (`requirements.txt` hanya batas bawah), sehingga angka tidak dijamin identik bit-per-bit. Akses tunnel dari komputer user belum diverifikasi dari sisi user.

Server review: tmux `tempo-ui`. Atas permintaan user, server kemudian dijalankan dengan bind `0.0.0.0:7861` (http://10.12.1.31:7861 dari jaringan internal, tanpa autentikasi) menggantikan tunnel `ssh -N -L 8850:127.0.0.1:7861 research-user@10.12.1.31`. Launcher paket tetap `127.0.0.1:7860`. Untuk mengunduh ZIP delivery, server statis **sementara** dijalankan di port 8853 (tmux `tempo-unduh`, hanya folder `dist/`, tanpa autentikasi); server ini akan dimatikan setelah user selesai mengunduh.

## Perubahan aplikasi (catatan 5 Oktober, riwayat)

- Pengantar tujuan, panel tiga task dan katalog 25 kelas (10 isu, 7 domain, 8 jenis entitas). Contoh diambil dari label dataset. Definisi, kriteria, pembeda dan contoh tersedia melalui codebook operasional yang disusun sesuai instruksi user, dengan provenance rumusan baru.
- Preview gambar dan headline/teks pendukung final untuk dataset maupun unggahan. Edit pengguna menjadi input model. Hasil lama dibatalkan saat input/task berubah; respons terlambat tidak menimpa analisis berikutnya.
- OCR mengembalikan blok mentah, koordinat, kandidat judul dan skor engine. Logo `TEMPO5` disaring; headline beberapa baris digabung. Skor pembacaan tidak disebut peluang headline benar. Hasil OCR tetap perlu diperiksa.
- Explanation terikat pada task/kelas saat ini. Lima strategi dipilih berdasarkan bukti; kontribusi negatif, zona logo/teks dan skor rendah dijelaskan sebagai keterbatasan. Definisi dan catatan anotator tidak disebut alasan model.
- Batch dataset/unggahan: antrean serial, progres, koreksi OCR, kegagalan per item, lanjut/retry, ekspor CSV/JSON dan aset heatmap tersimpan. Manifest bertahan setelah restart server; pengguna menekan lanjut untuk job terputus.

## Cara mencoba

Jalankan launcher paket seperti biasa (`jalankan_linux.sh` atau `jalankan_windows.bat`), lalu buka http://127.0.0.1:7860. Server review 6 Oktober: lihat akhir bagian Pembaruan 6 Oktober di atas. Langkah di bawah ditulis 5 Oktober; nama elemen UI terbaru (panel "Mulai di sini", tab hasil, peta gabungan) ada di [tutorial](../01_TUTORIAL.md) dan bagian pembaruan di atas.

1. Buka panel arti task; periksa definisi dan status sumbernya.
2. Pilih dataset, periksa preview, ubah headline bila perlu, pilih task dan klik Analisis. Ringkasan hasil harus menampilkan teks final dan task yang sama.
3. Unggah gambar. Periksa kandidat OCR, koreksi headline/teks pendukung, lalu analisis. Unggahan tidak memiliki label/anotasi pembanding.
4. Untuk batch, masukkan ID dataset dipisahkan koma atau pilih beberapa gambar. Pilih metode atribusi (dan, sejak 6 Oktober, task di view Batch) lalu mulai. Unggahan menunggu konfirmasi teks sebelum analisis.
5. Unduh CSV untuk ringkasan; JSON menyimpan hasil dan bukti lengkap. Setelah restart server, gunakan Lanjutkan job terakhir. Item berhasil dipertahankan; item gagal dapat dicoba ulang.

Batch dataset memakai head yang dilatih seluruh korpus, sehingga hasilnya eksplorasi **in-sample**. Analisis dataset tunggal memakai leave-one-out. Kedua mode tidak boleh dibandingkan sebagai benchmark akurasi yang sama. LIME lebih lambat; metode aktual dicatat jika fallback occlusion digunakan.

## Bukti verifikasi (tabel: catatan 5 Oktober; perintah verifikasi: 6 Oktober)

Lokasi hasil: `DEMO_XAI_745_FULL/04_hasil_eksperimen/revisi_week3/`.

| Pemeriksaan | Hasil |
|---|---|
| Regresi selector OCR, lima strategi/task binding, batch/restart | 4 unit test lulus |
| Respons analisis lama vs analisis baru | Uji JavaScript lulus |
| Audit training dengan fixture lengkap, fold duplikat dan hash salah | Uji lulus; fixture bukan hasil training |
| HTTP model nyata untuk tiga task dan headline manual | Lulus, `http_verification.json` dan tiga JSON task |
| Batch dataset + gambar rusak, CSV/JSON dan URL heatmap | Lulus, satu berhasil/satu gagal; error terisolasi |
| Unggahan nyata: OCR → review → teks manual → analisis | Lulus, `batch_upload_review.json`; tanpa anotasi palsu |
| GULA-GULA DEMO BURUH, atribusi LIME nyata | `gula_gula_candidate.json`; ketiga kata berkontribusi negatif pada kelas Task 2 yang diprediksi, tidak dipakai sebagai dukungan positif |
| Diagnosis OCR 30 gambar | 18/30 tepat (60%); headline CER rata-rata 0,2270; median 4,43 detik, p95 12,99 detik |
| Pembanding selector pada 30 blok OCR yang sama | 18/30 → 19/30 tepat (63,3%), `selector_comparison.json`; logo `TEMPO 5` ikut difilter |

Tiga gambar asli dosen sudah diuji: GULA-GULA dan CUKAI tepat, WASWAS salah terbaca. Hash file berbeda dari korpus; label korpus tidak dipindahkan otomatis ke unggahan.

Evaluasi OCR terdiri dari 20 contoh diagnosis historis ditambah 10 contoh menurut variasi panjang judul. Ini belum set independen atau representatif secara layout. Pembanding memakai blok OCR tersimpan dan hanya mengukur pemilihan headline; latensi OCR di atas berasal dari pengukuran sebelum perubahan terakhir selector. Sasaran 80% belum tercapai. Kasus gagal mencakup judul tidak lengkap, huruf salah terbaca dan teks asing yang ikut masuk. Ground truth beberapa baris, terutama judul yang bercampur ringkasan artikel, perlu ditinjau peneliti. Model/XAI selalu memakai teks final pengguna.

Perintah verifikasi (dimutakhirkan 2026-10-06). Jalankan dari **folder paket** `DEMO_XAI_745_FULL/` dengan Python venv paket:

```bash
# regresi tanpa server
venv/bin/python 01_notebook/test_ui_html5.py
venv/bin/python 01_notebook/test_week3_regressions.py
venv/bin/python 01_notebook/test_week3_training_audit.py
venv/bin/python 01_notebook/test_batch_error_message.py
venv/bin/python 01_notebook/test_narasi_ringkasan.py
venv/bin/python 01_notebook/test_ocr_urutan.py
(cd 01_notebook && ../venv/bin/python -m unittest test_audit_backend -v)   # memuat model, analisis nyata di CPU
node 01_notebook/test_loading_ui.js
node 01_notebook/test_week3_state.js
node 01_notebook/test_workspace_ui.js
node 01_notebook/test_r5_heatmap.js

# HTTP R5, saat server demo hidup (menulis ulang r5_heatmap_verification.json)
TEMPO_DEMO_URL=http://127.0.0.1:7861 venv/bin/python 01_notebook/verify_r5_http.py

# smoke browser Chromium headless, saat server demo hidup
venv/bin/python -m pip install -r requirements-browser.txt
venv/bin/python -m playwright install chromium
TEMPO_DEMO_URL=http://127.0.0.1:7861 venv/bin/python 01_notebook/smoke_browser_week3.py

# regresi frontend (Playwright, endpoint berat di-mock), saat server demo hidup
TEMPO_DEMO_URL=http://127.0.0.1:7861 venv/bin/python 01_notebook/test_audit_frontend.py
```

Port `7861` adalah server review. Untuk launcher paket, ganti dengan `7860`.

Smoke browser menulis `browser_smoke_<YYYYMMDD>/` dan `.json`; menjalankannya pada tanggal yang sama menimpa bukti hari itu (nama dapat diganti dengan `SMOKE_TAG`).

**Peringatan `verify_week3_http.py`:** script ini menulis ke path relatif `DEMO_XAI_745_FULL/04_hasil_eksperimen/revisi_week3` dari folder kerja saat dijalankan. Bila dijalankan dari folder induk paket, ia **menimpa** bukti historis `revisi_week3/{task*,batch_export*,http_verification}.json`. Jalankan dari folder staging, misalnya:

```bash
mkdir -p /tmp/staging/DEMO_XAI_745_FULL/04_hasil_eksperimen/revisi_week3
cd /tmp/staging
TEMPO_DEMO_URL=http://127.0.0.1:7861 /path/ke/DEMO_XAI_745_FULL/venv/bin/python /path/ke/DEMO_XAI_745_FULL/01_notebook/verify_week3_http.py
```

`01_notebook/evaluate_ocr_week3.py` (diagnosis OCR) juga menulis ulang `revisi_week3/ocr_diagnosis.json` dan `ocr_manifest.json`; jalankan hanya bila memang ingin memperbarui bukti itu.

## Evaluasi model dan gerbang integrasi

Baseline tersimpan di `04_hasil_eksperimen/hasil_mtl_740_task2domain.json`: fusion Macro-F1 Task 1 **0,4380**, Task 2 **0,3197**, Task 3 **0,2764**. Angka tersebut merupakan eksperimen baseline sebelumnya, bukan hasil perbaikan OCR/UI atau fine-tuning baru.

Pembaruan 2026-10-05: full training Kaggle COMPLETE dan audit metrik/protokol lulus. Task1/3 meningkat, Task2 menurun; hasil tetap terpisah dari demo. Lihat [laporan training](HASIL_FULL_TRAINING_KAGGLE.md). Checkpoint belum diunduh/diintegrasikan. Untuk audit setelah checkpoint tersedia, jalankan:

```bash
# dari folder paket DEMO_XAI_745_FULL/
venv/bin/python 01_notebook/audit_finetuned_week3.py /path/to/tempo_full
```

Audit menolak output smoke, hash data berbeda, fold/kelas tidak lengkap, cakupan OOF duplikat serta metrik tidak konsisten. Output `week3_audit.json` berisi metrik tiga task, per kelas, confusion matrix dan contoh salah. Keberadaan checkpoint diperiksa, tetapi isi bobot dan provenance split harus diperiksa lagi sebelum adapter model diintegrasikan. Jangan menyatakan peningkatan hanya berdasarkan contoh prediksi demo atau hasil in-sample.

## Status delivery saat ini

Dimutakhirkan 2026-10-06 (malam). Matriks lengkap R1–R5/T01–T12 beserta bukti dan batasan: [STATUS_REVISI_20261006.md](STATUS_REVISI_20261006.md). Ringkasan di bawah adalah status paket delivery revisi Week 3 (baseline). Ringkasan ini tidak menyatakan bahwa semua sasaran tercapai.

- R5: **ditutup 6 Oktober** — peta utama di tab Bukti gambar adalah peta gabungan tiga task; peta task pilihan tampil terpisah sebagai dasar penjelasan/zona. Bukti `test_r5_heatmap.js`, `r5_heatmap_verification.json` dan smoke browser. Diuji di Chromium saja.
- T01: codebook operasional 25 kelas sudah dibuat sesuai instruksi user dan dipakai aplikasi. Rumusan ini bukan pedoman anotator lama; keselarasan label tetap perlu keputusan peneliti.
- T02, T03, T07–T09: implementasi input final, katalog, narasi berbasis bukti (ringkasan tiga task + penjelasan task pilihan, tanpa LLM) dan batch/ekspor selesai. Pada 6 Oktober malam: unggah ulang berkas sama, penggantian judul saat gambar baru, pembatalan analisis ke server, dan perbaikan audit kode.
- T04–T06: diagnosis OCR, dua eksperimen pembanding, dan audit urutan kata (6 Oktober) selesai. Judul tepat 68–78% pada dua set validasi untuk versi aplikasi terakhir (cenderung optimistis; 63–72% saat kode dibekukan), jadi target headline 80% belum tercapai. Tersedia [usulan pemeriksaan visual 11 kasus](PEMERIKSAAN_VISUAL_OCR.md); tidak mengganti ground truth.
- T10 (sebagian): tiga gambar asli dosen diuji (OCR 2/3 judul tepat), tiga tinjauan agen selesai, uji Windows lama lulus (backend di folder terisolasi, bukan UI browser terbaru atau instalasi bersih paket terbaru). Batch penuh 740 lulus di mesin asal: 740 berhasil, nol gagal, 740 pemeriksaan HTTP heatmap, 3.700 aset dan CSV 741 baris termasuk header (`scale740_verification.json`); in-sample, bukan metrik akurasi. Pembaruan 6 Oktober: smoke Chromium headless desktop/mobile **80/80** (`browser_smoke_20261006.json`, 24 screenshot), lalu run final **94/94** (`browser_smoke_20261006_audit.json`); test 70 Python + 13 frontend + 4 JS lulus. Belum: Firefox/Safari, Windows dengan paket terbaru, uji pengguna manusia — evaluasi agen dan smoke otomatis tidak diklaim sebagai uji manusia.
- T11: full training Kaggle COMPLETE, audit metrik/protokol lulus. Task1/3 meningkat, Task2 menurun; baseline tetap menjadi model demo. Checkpoint baru belum diintegrasikan, sehingga hasil fine-tuning tidak diklaim sebagai perilaku demo. E01/E02 belum dilaporkan.
- Keamanan server: launcher paket hanya mendengarkan `127.0.0.1:7860`. Server review `tempo-ui` dibuka di `0.0.0.0:7861` atas permintaan user dan tautan unduh sementara di port 8853; keduanya tanpa autentikasi. Autentikasi belum ada dan menunggu keputusan user.
- T12: paket delivery `TEMPO_XAI_DELIVERY_WEEK3_20261006.zip` dibangun dari source terbaru dengan `DELIVERY_MANIFEST.json` (SHA256 tiap berkas) dan `requirements-lock-linux.txt`. Paket diuji dari instalasi bersih di Linux (seluruh test dan smoke 94/94 lulus), lihat docs/plans/2026-10-06-paket-delivery-final.md. Instalasi bersih Windows belum diuji. ZIP review lama (`DEMO_XAI_745_WEEK3_REVIEW.zip`) adalah riwayat dan sudah digantikan. Penerimaan penelitian masih memerlukan keputusan semantik/ground truth dan target evaluasi OCR (sasaran 80% adalah usulan, belum tercapai).

## Bukti tambahan penutupan teknis (5–6 Oktober, riwayat)

Lokasi output tetap `04_hasil_eksperimen/revisi_week3/`.

| Pemeriksaan | Hasil |
|---|---|
| Windows: halaman, 740 sampel, katalog 25 kelas, tiga task model nyata dan heatmap | Lulus; `windows_verification.json`. Dijalankan melalui SSH pada folder terisolasi dengan data/bobot lama read-only; bukan uji interaksi browser manusia |
| Regresi Python Linux dan Windows | Empat test lulus, termasuk manifest Unicode di luar cp1252; `windows_regression_verification.json` |
| Selector alternatif pada blok OCR sama | Kandidat 20/30 (66,7%) vs produksi 19/30; tambahan 10 contoh bukan set independen. Tidak diterapkan karena bukti perbaikan terbatas |
| EasyOCR beamsearch, 30 korpus + 3 gambar dosen | 16/30 vs greedy 19/30; gambar dosen tetap 2/3. Ada peringatan overflow numerik; kandidat ditolak. `decoder_comparison.json`, `decoder_numerical_warning.json` |

Bug decoding default Windows diperbaiki dengan encoding UTF-8 eksplisit pada katalog, definisi dan manifest batch. Environment training Windows tidak diubah; Flask hanya dipasang ke direktori vendor verifikasi.

Lihat [codebook](CODEBOOK_OPERASIONAL.md), [tabel pemeriksaan](TABEL_PEMERIKSAAN_REVISI.md), [evaluasi agen](EVALUASI_AGEN_WEEK3.md), [gambar dosen](VERIFIKASI_GAMBAR_DOSEN.md), dan [plan penutupan](plans/2026-10-05-penutupan-teknis-week3.md). Paket review lama `DEMO_XAI_745_WEEK3_REVIEW.zip` (riwayat 5 Okt, sudah digantikan paket delivery 6 Okt) mengecualikan environment, cache/job lokal dan checkpoint training.

Verifikasi skala: seluruh snapshot/input/task/kelas/evidence dan probabilitas valid; ekspor JSON berisi 740 item. Ini uji alur in-sample, bukan evaluasi akurasi. Job asli dan aset berada di `_jobs/` lokal dan dikecualikan dari ZIP; URL ekspor bukan aset portabel paket.

Penutupan teknis 2026-10-06: batch dipulihkan setelah proses terputus pada 651 hasil. Hash seluruh hasil lama identik; 89 sisanya selesai. Verifikasi HTTP tiga task/input manual, batch error terisolasi dan ekspor diulang setelah restart dan lulus. Bukti: `scale740_resume_verification.json` dan `http_verification.json`.
