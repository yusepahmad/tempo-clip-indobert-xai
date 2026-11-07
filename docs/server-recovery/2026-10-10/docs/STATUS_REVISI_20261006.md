# Status revisi client per 6 Oktober 2026 (malam)

**Tanggal:** 2026-10-06 (malam), server `10.12.1.31`  
**Verdict:** **paket delivery revisi Week 3 dengan model baseline** — `TEMPO_XAI_DELIVERY_WEEK3_20261006.zip`, berisi `DELIVERY_MANIFEST.json` (SHA256 tiap berkas) dan `requirements-lock-linux.txt`. Paket diuji dari instalasi bersih di Linux, lihat [docs/plans/2026-10-06-paket-delivery-final.md](plans/2026-10-06-paket-delivery-final.md). Ini **bukan** pernyataan bahwa semua sasaran sudah tercapai. Yang masih terbuka: instalasi bersih di Windows, browser selain Chromium, uji pengguna manusia, sasaran OCR 80%, eksperimen E01/E02, integrasi checkpoint Kaggle, dan autentikasi server (menunggu keputusan user). Lihat bagian "Masih terbuka".

Dokumen ini memperbarui matriks di [AUDIT_DELIVERY_WEEK3_20261006.md](AUDIT_DELIVERY_WEEK3_20261006.md) (audit 6 Okt pagi). Audit lama tidak diubah dan tetap menjadi riwayat. Rangkaian pekerjaan ada di [plan lanjutan server](plans/2026-10-06-lanjutan-week3-server.md), langkah 1–5.

## Ringkasan konteks

- Dataset final berisi 740 sampul dengan tiga task: isu (10 kelas), domain sumber metafora (7) dan tipe entitas (8). Ke-25 kelas memakai [codebook operasional](CODEBOOK_OPERASIONAL.md) yang dibuat atas instruksi user. Ini bukan codebook resmi, dan tidak perlu menunggu codebook resmi.
- Model demo adalah **baseline** CLIP ViT-B/32 + IndoBERT beku + head MTL. Macro-F1 5-fold: Task1 0,438, Task2 0,320 (0,3197), Task3 0,276. Full fine-tuning Kaggle sudah COMPLETE (0,5139 / 0,2461 / 0,3699). Karena Task 2 turun, baseline tetap dipakai, dan checkpoint Kaggle belum diunduh atau diintegrasikan.
- Lingkungan bukti 6 Okt: Python 3.10.12, torch 2.14.1+cpu, CPU saja. Versi pustaka lebih baru daripada di mesin asal, jadi angka tidak dijamin identik bit-per-bit (`server_baseline_20261006.json`). `requirements-lock-linux.txt` mencatat versi pustaka yang terbukti lulus semua test di server. `requirements.txt` hanya memuat batas bawah.

Semua path bukti di bawah relatif terhadap `04_hasil_eksperimen/revisi_week3/`, kecuali yang diawali `docs/` atau `01_notebook/`.

## Perubahan sejak sinkronisasi sore 6 Okt

| # | Perubahan | Bukti |
|---|---|---|
| 1 | **Narasi ringkasan dan penjelasan ditulis ulang, tetap tanpa LLM.** Tab Prediksi menampilkan ringkasan awam yang mencakup tiga task (isu, pihak yang disorot, kiasan), tingkat keyakinan, dan perbandingan dengan label anotator (mode dataset). Tab Penjelasan hanya membahas task pilihan, dalam blok "Mengapa <kelas>?", "Arti kelas ini", "Catatan anotator" (hanya catatan milik task itu) dan "Yang perlu dicek". Isi kedua tab tidak lagi sama | `01_notebook/test_narasi_ringkasan.py`, `browser_smoke_20261006_narasi.json`; [plan](plans/2026-10-06-narasi-ringkasan-penjelasan.md) |
| 2 | **Audit OCR.** Teks pendukung kini disusun menurut tata letak: baris, lalu kolom/paragraf, dengan deck di bawah judul lebih dulu. Baris lanjutan judul berhuruf hias disambung, dan logo "TEMPO" yang salah baca serta tagline huruf berjarak disaring. Validasi independen 60 sampul: teks pendukung berurutan sempurna 13→35/56, judul tepat 41→43/60. Validasi kedua 60 sampul (per sore): judul tepat 37→39/60 tanpa regresi judul. Sampah teks baku juga dibuang (footer tempo.co/mingguan yang salah baca, label rubrik salah baca, harga/ISSN rusak, potongan acak huruf+angka), dan filter rubrik tidak lagi membuang kata judul sah. Dengan versi aplikasi terakhir, judul tepat 41/60 (68%) pada validasi kedua dan 47/60 (78%) pada validasi pertama; kedua set sudah ikut dipakai saat perbaikan sehingga angka ini cenderung optimistis (angka saat kode dibekukan: 43/60 dan 38/60, 63–72%). Sasaran usulan 80% belum tercapai, jadi koreksi manual tetap wajib. Keputusan user: batas 6 baris judul dipertahankan | `docs/AUDIT_OCR_URUTAN_20261006.md`, `ocr_audit_urutan_20261006.json`, `01_notebook/test_ocr_urutan.py`; plan [urutan](plans/2026-10-06-audit-ocr-urutan-kata.md), [sampah teks baku](plans/2026-10-06-ocr-sampah-teks-baku.md) |
| 3 | **Unggah gambar.** Memilih berkas yang sama lagi kini memicu pembacaan ulang dan membatalkan hasil lama. Gambar baru selalu mengganti judul dan teks pendukung dengan hasil pembacaan gambar baru, tetapi ketikan selama OCR gambar yang sama tetap dilindungi. Nama berkas tampil sebagai "Gambar aktif: …" | `browser_smoke_20261006_unggah.json`, `browser_smoke_20261006_judul.json`; plan [berkas sama](plans/2026-10-06-fix-unggah-file-sama.md), [judul diganti](plans/2026-10-06-judul-ganti-saat-gambar-baru.md) |
| 4 | **Audit kode frontend/backend/modul dan perbaikannya.** Celah XSS lewat pesan OCR dan nilai dinamis ditutup. Ada batas sumber daya: judul ≤300 karakter, teks pendukung ≤2000, unggahan analisis/OCR ≤25 MB, gambar dengan sisi >8000 px, rasio >5:1 atau lebih dari 40 MP ditolak (gambar yang lolos diperkecil ke sisi terpanjang 2000 px), dan maksimal 2 job batch aktif/antre. Galat dikembalikan sebagai JSON. Analisis yang dibatalkan di browser kini juga dibatalkan di server. Status batch `failed` muncul bila semua item gagal. Pilihan task tersedia di view Batch. Respons tidak lagi memuat path server, nilai kosong (NaN) di dataset tidak lagi tampil sebagai "nan", dan penjelasan task tidak lagi memuat catatan anotator task lain. Rincian lain ada di plan | `01_notebook/test_audit_backend.py` (33), `01_notebook/test_audit_frontend.py` (13), `browser_smoke_20261006_audit.json`; [plan](plans/2026-10-06-audit-bug-kode.md) |

| 5 | **Paket delivery dan uji instalasi bersih Linux.** `TEMPO_XAI_DELIVERY_WEEK3_20261006.zip` dibangun dengan `DELIVERY_MANIFEST.json` dan `requirements-lock-linux.txt`. Dari ZIP yang diekstrak ke folder baru dengan venv baru: 70 test Python, 4 JS, 13 frontend, `verify_r5_http.py`, `verify_week3_http.py` (staging) dan smoke browser 94/94 lulus. Windows belum diuji | `browser_smoke_paket_bersih.json`; [plan paket](plans/2026-10-06-paket-delivery-final.md) |
| 6 | **Notebook.** Teks `01_notebook/DEMO_XAI_TEMPO.ipynb` dimutakhirkan 6 Okt (blok "Pembaruan 6 Oktober" di sel pertama tentang beda notebook dan aplikasi); sel kode dan output tidak berubah | [plan notebook](plans/2026-10-06-notebook-pemutakhiran.md) |

**Bukti akhir:** smoke browser final **94/94** (`browser_smoke_20261006_audit.json`, Chromium headless desktop + mobile; diulang 94/94 dari instalasi bersih, `browser_smoke_paket_bersih.json`), dan test **70 Python + 13 frontend + 4 JS** lulus.

## Matriks R1–R5

| Revisi | Status 6 Okt | Bukti | Batasan |
|---|---|---|---|
| R1 — teks otomatis (OCR) | Diterapkan, kualitas terbatas | OCR berjalan otomatis saat unggah, ada daftar "Pilihan judul hasil pembacaan otomatis" dan koreksi manual. Urutan baca berbasis tata letak dan filter sampah teks baku ditambahkan 6 Okt. Bukti: `docs/AUDIT_OCR_URUTAN_20261006.md`, `ocr_audit_urutan_20261006.json`, `ocr_diagnosis.json`, `server_baseline_20261006.json` (OCR foto dosen) | Dengan versi aplikasi terakhir, judul tepat 41/60 (68%) pada validasi kedua dan 47/60 (78%) pada validasi pertama; kedua set sudah ikut dipakai saat perbaikan sehingga angka ini cenderung optimistis (angka saat kode dibekukan: 43/60 dan 38/60, 63–72%). Sasaran usulan 80% belum tercapai, jadi koreksi manual tetap wajib. Salah baca huruf berasal dari EasyOCR dan tidak berubah (WASWAS terbaca `VJASWAS` di server ini, `VJJASWAS` di mesin asal). Foto dosen: 2/3 judul tepat. Batas 6 baris judul (keputusan user) membuat CER judul naik pada judul yang memang sudah salah pilih blok. Angka lama 19/30 (63,3%) berasal dari set diagnosis yang tidak independen |
| R2 — istilah mudah dipahami | Diterapkan | Label ramah pengguna, panduan tiga langkah, tab Panduan dengan katalog 25 kelas; screenshot browser desktop 1440×900 dan mobile 390×844 (`browser_smoke_20261006_audit/`) | Screenshot membuktikan teks terender, bukan bahwa pengguna memahaminya. Tiga tinjauan sub-agent bukan uji manusia |
| R3 — kesimpulan awam | Diterapkan; narasi ditulis ulang 6 Okt | Tab Prediksi berisi ringkasan awam tiga task beserta perbandingan anotator. Tab Penjelasan berisi penjelasan task pilihan (Mengapa / Arti kelas / Catatan anotator milik task itu / Yang perlu dicek). Tetap tanpa LLM. Bukti: `test_narasi_ringkasan.py`, `browser_smoke_20261006_narasi.json`, `browser_smoke_20261006_audit.json` | Bukan narasi LLM. Keterbacaan belum diuji pada pengguna manusia. Makna kiasan disebut sebagai makna umum jenis kiasan, bukan tafsir sampul tertentu |
| R4 — atribusi kata (LIME) | Diterapkan; diuji pada foto dosen lewat browser | LIME menjadi metode baku analisis satuan (≈15–20 detik di CPU server). Smoke browser Task 2, LIME, judul final: GULA-GULA → Permainan & Kontes; WASWAS (dikoreksi) → Permainan & Kontes; CUKAI → Konsumsi & Transaksi (`browser_smoke_20261006.json`). Audit pagi: `audit_gula_original_lime.json` | Kelas unggahan tidak divalidasi. Audit pagi (GULA-GULA, teks pendukung kosong) memberi DEMO positif. Di smoke browser, teks pendukung terisi hasil OCR dan ketiga kata GULA-GULA bernilai negatif. Pola yang dikeluhkan di R4 masih bisa muncul tergantung input. Tab Penjelasan menyatakannya terbuka. Ini perilaku LIME pada input itu, bukan validasi kelas |
| R5 — peta gabungan semua task | Diterapkan 6 Okt | Peta utama tab Bukti gambar adalah peta gabungan tiga task (sama untuk semua pilihan task), diikuti blok "Bukti task pilihan: <task> — kelas <kelas>". Bukti: `01_notebook/test_r5_heatmap.js`, `r5_heatmap_verification.json`, smoke browser desktop/mobile | Peta gabungan adalah rata-rata peta per task yang dinormalisasi. Peta ini bukan dasar atribusi kata atau narasi, dan bukan deteksi objek. Bila sebuah peta datar, narasi tidak lagi menyebut zona dominan. Diuji di Chromium saja |

## Matriks T01–T12, batch dan ekspor

| ID | Status 6 Okt | Bukti | Catatan / batasan |
|---|---|---|---|
| T01 | Selesai sesuai instruksi user | `docs/CODEBOOK_OPERASIONAL.md` | Codebook operasional 25 kelas; keselarasannya dengan anotasi historis belum dibuktikan |
| T02 | Diterapkan; render browser terbukti | `guided_ui_verification.json`, `workspace_ui_verification.json`, screenshot smoke desktop/mobile | Belum diuji apakah pengguna manusia bisa membacanya dengan mudah |
| T03 | Lulus | `01_notebook/test_week3_state.js`, `server_baseline_20261006.json`, smoke browser (race ganti task; berkas sama dipilih ulang; gambar baru mengganti judul, ketikan selama OCR dilindungi), `test_audit_backend.py` (pembatalan analisis ke server) | Edit teks dataset menghitung ulang fitur. Respons usang tidak menimpa hasil baru. Analisis yang dibatalkan dilewati atau dihentikan server di titik periksa (uji nyata 30,2→24,6 detik; sisanya adalah pelatihan ulang leave-one-out yang tidak bisa diputus) |
| T04 | Sebagian (riset) | `ocr_diagnosis.json`, `ocr_manifest.json`, `visual_ocr_proposals.json`, `docs/PEMERIKSAAN_VISUAL_OCR.md` | Diagnosis 30 headline dan usulan transkripsi sudah ada. Transkripsi layout lengkap yang tervalidasi belum ada |
| T05 | Sebagian (riset) | `ocr_audit_urutan_20261006.json`, `docs/AUDIT_OCR_URUTAN_20261006.md` | Judul + teks pendukung (recall, presisi, urutan kata) dievaluasi pada set dev/uji/validasi/validasi kedua. Kebenaran teks pendukung adalah transkripsi anotator yang konvensinya campuran. Salah baca huruf EasyOCR belum ditangani |
| T06 | Dibandingkan, tidak diterapkan | `selector_comparison.json`, `selector_experiment.json`, `decoder_comparison.json`, `beamsearch/` | Kandidat tidak diterapkan karena buktinya belum cukup |
| T07 | Diterapkan, kualitas otomatis terbatas | Kandidat judul, koreksi manual, pemisahan input final, label "Gambar aktif", filter sampah teks baku, smoke browser | Kualitas OCR mengikuti batasan R1 |
| T08 | Diterapkan | `docs/DELIVERY_WEEK_3.md`, `01_notebook/test_week3_regressions.py`, `test_narasi_ringkasan.py` | Sumber klaim dan pengikatan ke task/kelas tersedia. Catatan anotator hanya dipakai untuk task pemiliknya. Posisi peta panas tidak dipakai untuk menamai objek |
| T09 | Diterapkan dan diuji | `01_notebook/test_week3_regressions.py`, `test_narasi_ringkasan.py` | Lima strategi narasi dirangkai dari bukti (bukan LLM). Ringkasan tiga task terpisah dari penjelasan task pilihan |
| T10 | Sebagian | Regresi otomatis 70 Python + 13 frontend + 4 JS; smoke Chromium headless final **94/94** (`browser_smoke_20261006_audit.json`); riwayat 80/80 dan 83/83; tiga tinjauan sub-agent (`docs/EVALUASI_AGEN_WEEK3.md`); foto dosen; skala 740 (`scale740_verification.json`); Windows lama (`windows_verification.json`) | Smoke browser bukan uji pengguna manusia. Firefox/Safari belum diuji. Uji Windows lama hanya mencakup backend di folder terisolasi, bukan UI terbaru atau instalasi bersih paket ini |
| T11 | Training dan audit selesai; integrasi belum | `docs/HASIL_FULL_TRAINING_KAGGLE.md` | Task2 0,3197 → 0,2461, sehingga demo tetap memakai baseline. Checkpoint belum diintegrasikan. E01 dan E02 belum dilaporkan |
| T12 | Paket delivery dibangun | `TEMPO_XAI_DELIVERY_WEEK3_20261006.zip`, `DELIVERY_MANIFEST.json`, `requirements-lock-linux.txt`; [plan paket](plans/2026-10-06-paket-delivery-final.md) | Diuji dari instalasi bersih di Linux, lihat docs/plans/2026-10-06-paket-delivery-final.md. Instalasi bersih di Windows belum diuji |
| Batch / ekspor / restart | Lulus | `scale740_verification.json`, `scale740_resume_verification.json` (bukti historis mesin asal); `server_baseline_20261006.json`; smoke browser (batch dataset + gambar rusak, ekspor CSV/JSON); `test_audit_backend.py` | Skala 740/740 lulus di mesin asal dan tidak diulang di server. Batch dataset bersifat in-sample, jadi bukan metrik akurasi, dan ringkasan batch kini mencantumkan catatan in-sample. Paling banyak 2 job aktif/antre. Status `failed` muncul bila semua item gagal. CSV aman dari formula. Pesan gagal tidak memuat path server. Manifest job lama tidak dimigrasi |

## Temuan audit 6 Okt pagi dan penutupannya

| Prioritas | Temuan (audit pagi) | Status 6 Okt malam | Bukti / sisa |
|---|---|---|---|
| P1 | R5 belum sesuai: peta utama memakai task pilihan | **Ditutup** | `test_r5_heatmap.js`, `r5_heatmap_verification.json`, smoke browser; [sub-plan R5](plans/2026-10-06-r5-peta-gabungan-dan-changelog.md) |
| P1 | ZIP delivery tertinggal dari UI terbaru | **Ditutup** | Paket dibangun dari source terbaru dengan `DELIVERY_MANIFEST.json`; [plan paket](plans/2026-10-06-paket-delivery-final.md) |
| P1 | Rendering UI terbaru dan setup paket bersih belum dibuktikan | **Chromium dan Linux ditutup; Windows terbuka** | Smoke final 94/94 desktop + mobile. Diuji dari instalasi bersih di Linux, lihat docs/plans/2026-10-06-paket-delivery-final.md. Windows belum diuji |
| P2 | Dokumentasi serah terima belum sinkron | **Disinkronkan 6 Okt malam** | Dokumen riwayat (laporan Week 1/2, audit pagi) tidak diubah |
| P2 / riset | Kualitas OCR dan evaluasi teks lengkap terbatas | **Membaik, tetap terbuka (riset)** | Judul tepat 68–78% pada dua set validasi untuk versi aplikasi terakhir (cenderung optimistis; 63–72% saat kode dibekukan), sasaran usulan 80% belum tercapai; koreksi manual tersedia dan wajib |

## Masih terbuka

1. Instalasi bersih di Windows (`setup_windows.bat` + `jalankan_windows.bat`) dari paket ini. Hasil Linux tidak menggantikan Windows.
2. Browser selain Chromium (Firefox/Safari) dan browser di mesin user/client.
3. Uji pengguna manusia untuk keterbacaan UI, ringkasan dan penjelasan (R2/R3/T02). Tiga tinjauan sub-agent bukan pengganti.
4. Sasaran OCR 80% (usulan) belum tercapai: judul tepat 68–78% pada dua set validasi untuk versi aplikasi terakhir (cenderung optimistis; 63–72% saat kode dibekukan).
5. Eksperimen E01 (perbaikan input) dan E02 (tuning terkontrol).
6. Keputusan integrasi checkpoint Kaggle. Jika client mengharapkan aplikasi memakai checkpoint itu, ekspektasi tersebut belum terpenuhi.
7. Autentikasi server (menunggu keputusan user). Launcher paket hanya mendengarkan `127.0.0.1:7860`. Server review `tempo-ui` dijalankan dengan bind `0.0.0.0:7861` (http://10.12.1.31:7861) atas permintaan user, tanpa autentikasi. Tautan unduh ZIP memakai server statis **sementara** di port 8853 (tmux `tempo-unduh`, hanya folder `dist/`, tanpa autentikasi) dan akan dimatikan setelah user selesai mengunduh.
8. Hal minor: manifest job batch lama yang masih memuat path belum dimigrasi, dan `_jobs` belum dihapus otomatis.

## Bukan target demo (jalur riset)

- T04/T05: transkripsi headline/supporting/layout dan evaluasi ekstraksi pada set independen. Usulan transkripsi perlu dipisahkan dari ground truth tervalidasi.
- T06/T07: kandidat selector/decoder harus diukur pada data dan kondisi latensi yang sebanding sebelum produksi diganti.
- Sasaran OCR 80%: masih usulan, belum menjadi syarat penerimaan yang disepakati. Jika menjadi syarat, perlu evaluasi independen.
- T11 E01/E02: eksperimen dengan split/checkpoint yang konsisten.
- Validasi kelas prediksi pada gambar unggahan (termasuk foto dosen) memerlukan ground truth.

## Perintah verifikasi

Dari folder paket:

- Tanpa server: `venv/bin/python 01_notebook/test_ui_html5.py`, `test_week3_regressions.py`, `test_week3_training_audit.py`, `test_batch_error_message.py`, `test_narasi_ringkasan.py`, `test_ocr_urutan.py`; `cd 01_notebook && ../venv/bin/python -m unittest test_audit_backend -v` (memuat model dan menjalankan analisis nyata di CPU); `node 01_notebook/test_loading_ui.js`, `test_week3_state.js`, `test_workspace_ui.js`, `test_r5_heatmap.js`.
- Dengan server hidup: `verify_r5_http.py`. Skrip HTTP/browser membaca `TEMPO_DEMO_URL` (bawaan `http://127.0.0.1:7861`, server review); untuk launcher paket pakai `TEMPO_DEMO_URL=http://127.0.0.1:7860`.
- Browser (`pip install -r requirements-browser.txt`): `TEMPO_DEMO_URL=… venv/bin/python 01_notebook/test_audit_frontend.py` dan `smoke_browser_week3.py`.

Rincian dan peringatan `verify_week3_http.py` ada di [HANDOFF_SERVER.md](HANDOFF_SERVER.md).
