# Changelog

Semua perubahan penting pada project ini dicatat di file ini.
Format mengikuti [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

### Fixed
- Smoke Kaggle E01 v1 hang lebih dari 2 jam tanpa log. `01_notebook/e01_vlm.py` kini memakai:
  - tenggat internal `BATAS_MENIT` (smoke 40, full 600) dengan watchdog yang menutup run secara rapi;
  - `tahap.log` ber-timestamp (pip, unduh bobot, muat model, tiap batch);
  - larangan offload ke CPU/disk;
  - timeout pip 15 menit.

  `kaggle_e01/siapkan_kernel.py` mengatur `BATAS_MENIT` per kernel (plan: [docs/plans/2026-10-08-e01-vlm-dua-tahap-kaggle.md](docs/plans/2026-10-08-e01-vlm-dua-tahap-kaggle.md)).

### Added
- Persiapan eksperimen E01 (VLM dua tahap untuk Task 2), belum dijalankan di Kaggle:
  - `01_notebook/e01_vlm.py`: tahap 1, deskripsi literal dan zero-shot Task 2 oleh Qwen3-VL-8B, dengan resume dan berhenti otomatis bila keluaran rusak.
  - `01_notebook/e01_evaluasi.py`: tahap 2, OOF 5-fold dengan split baseline, inner-CV, cek hash CSV, maksimal 8 core.
  - `01_notebook/kaggle_e01/` (`siapkan_kernel.py`, kernel `full/` dan `smoke/`).
  - Bukti uji alur `04_hasil_eksperimen/e01_vlm/uji_alur_anotator/`.

  Kaggle CLI 2.2.4 dengan Python 3.12 portabel dipasang di `learn/.kaggle/`, di luar folder paket, sehingga push bisa langsung dari server.

  Temuan: deskripsi anotator kosong untuk semua NON_METAFORA, sehingga rujukan "plafon" Task 2 terlalu tinggi; realistis ≈0,46 pada enam kelas metafora (plan: [docs/plans/2026-10-08-e01-vlm-dua-tahap-kaggle.md](docs/plans/2026-10-08-e01-vlm-dua-tahap-kaggle.md)).

## [Delivery Week 3] - 2026-10-06
Paket `TEMPO_XAI_DELIVERY_WEEK3_20261006.zip` (model baseline). Changelog ini tidak pernah dipotong per rilis sebelumnya, sehingga bagian ini memuat seluruh riwayat sejak 22 September; paket Week 1 (22 Sep) dan Week 2 (28–29 Sep) tercatat pada entri masing-masing di bawah.

### Changed
- Pemeriksaan akhir pemutakhiran 6 Oktober: dokumen hidup diselaraskan dengan perilaku aplikasi (angka OCR versi aplikasi terakhir, perilaku unggah, batas masukan, status paket/Windows/autentikasi), dokumen riwayat diberi catatan riwayat dan koreksi status bertanggal, teks Panduan/metode di `index.html` serta docstring/komentar kode dan launcher dimutakhirkan tanpa mengubah perilaku (plan: [docs/plans/2026-10-06-cek-akhir-pemutakhiran.md](docs/plans/2026-10-06-cek-akhir-pemutakhiran.md)).

### Fixed
- `01_notebook/verify_gambar_dosen.py` dan `compare_decoder_week3.py` membaca foto dosen dari `06_gambar_revisi/` (sebelumnya folder induk sehingga gagal dijalankan dari paket); `verify_gambar_dosen.py` menerima folder keluaran agar bukti 5 Okt tidak tertimpa. Bukti `ocr_audit_urutan_20261006.json` dihitung ulang dengan selector terakhir (plan: [docs/plans/2026-10-06-cek-akhir-pemutakhiran.md](docs/plans/2026-10-06-cek-akhir-pemutakhiran.md)).

### Changed
- `01_notebook/DEMO_XAI_TEMPO.ipynb` (hanya sel markdown): tanggal pemutakhiran 6 Oktober 2026, blok "Pembaruan 6 Oktober" yang menjelaskan beda notebook metodologi baseline dengan aplikasi (LIME baku, peta gabungan R5, ringkasan/penjelasan, OCR, fine-tuning Kaggle tidak dipakai), "173 catatan" → "657"; sel kode/output tidak berubah. Rujukan di `00_BACA_DULU.md` dan `01_TUTORIAL.md` diselaraskan; ZIP delivery dibangun ulang (plan: [docs/plans/2026-10-06-notebook-pemutakhiran.md](docs/plans/2026-10-06-notebook-pemutakhiran.md)).

### Added
- Paket delivery `TEMPO_XAI_DELIVERY_WEEK3_20261006.zip` dibangun oleh `01_notebook/bangun_paket_delivery.py` dengan `DELIVERY_MANIFEST.json` (SHA256 tiap berkas), `requirements-lock-linux.txt`, dan izin eksekusi `jalankan_linux.sh`; dokumen delivery disinkronkan. Uji instalasi bersih Linux dari ZIP: seluruh test (70 Python, 4 JS, 13 frontend), verifikasi HTTP dan smoke browser 94/94 lulus (`browser_smoke_paket_bersih.json`); Windows belum diuji (plan: [docs/plans/2026-10-06-paket-delivery-final.md](docs/plans/2026-10-06-paket-delivery-final.md)).

### Fixed
- Audit kode — backend `02_web_demo/app.py`, `batch_jobs.py`: unggahan tidak lagi dibaca saat engine terkunci; gambar berdimensi ekstrem ditolak/diperkecil; batas panjang judul/pendukung, ukuran unggah dan antrean batch; tidak ada path server di respons; NaN dataset tidak lagi menjadi "nan"; proses dapat berhenti saat batch berjalan; status item batch tidak basi; cache per analisis; CSV aman dari formula; validasi sample_id dan status `failed`; error JSON untuk 413/404/500; metode atribusi tak sah ditolak; nama berkas OCR unik; catatan in-sample di ringkasan batch; `/api/image` dibatasi ke dataset (plan: [docs/plans/2026-10-06-audit-bug-kode.md](docs/plans/2026-10-06-audit-bug-kode.md)).
- Audit kode — frontend `02_web_demo/index.html`: XSS lewat pesan OCR/nilai dinamis ditutup; daftar batch mempertahankan ketikan review dan panel terbuka; polling batch pulih setelah error; tab mode aktif tidak membuang hasil; kandidat OCR usang dibersihkan; batchId usang dihapus; tombol/input batch dikunci saat berjalan; gulir otomatis dan tab lengket yang benar di mobile; pilihan task di view Batch; pesan ramah untuk respons non-JSON (plan: [docs/plans/2026-10-06-audit-bug-kode.md](docs/plans/2026-10-06-audit-bug-kode.md)).
- Pembatalan analisis (F2): analisis yang dibatalkan di browser kini juga dibatalkan di server (`/api/analisis/batal`, `req_id`), sehingga analisis baru tidak menunggu analisis lama selesai (uji nyata 30,2→24,6 dtk) (plan: [docs/plans/2026-10-06-audit-bug-kode.md](docs/plans/2026-10-06-audit-bug-kode.md)).

### Added
- `01_notebook/test_audit_backend.py` (33 test), `01_notebook/test_audit_frontend.py` (13 test Playwright dengan mock); smoke `browser_smoke_20261006_audit.json` 94/94 (plan: [docs/plans/2026-10-06-audit-bug-kode.md](docs/plans/2026-10-06-audit-bug-kode.md)).

### Fixed
- Audit kode — modul narasi `02_web_demo/explanation_evidence.py`: penjelasan task kini hanya memuat catatan anotator milik task itu (Task 1 tidak lagi menyebut sumber kiasan/entitas; bukti ANOTATOR diberi `task_id`); peta datar tidak lagi diklaim punya zona dominan; kata atribusi kembar dan kutip ganda dirapikan; "beberapa pihak atau pihak lain"; ringkasan tidak menulis "ketiga aspek" bila label anotator tak lengkap; akronim di awal definisi tetap kapital. Test lama `test_week3_regressions.py` diubah satu kasus (catatan `entitas` milik Task 3 diganti `sumber_metafora` milik Task 2) karena mengunci perilaku lintas task yang salah (plan: [docs/plans/2026-10-06-audit-bug-kode.md](docs/plans/2026-10-06-audit-bug-kode.md)).
- Audit kode — `02_web_demo/ocr_headline.py`: filter rubrik tidak lagi membuang "SERANGAN"/"INVESTASI" (judul "JEBAKAN INVESTASI BODONG" utuh); "EDISI KHUSUS … THAMRIN" dan rentang tahun "1903-1962" tidak lagi dibuang; jalur tanpa kandidat judul memakai filter teks baku dan urutan baca; masukan blok tidak lengkap tidak crash; potong 500 karakter di batas kata; tanpa ".;" ganda antar kelompok; tanda hubung tanggal berspasi, kata ulang terpenggal ("GAYA -" + "GAYAAN") disambung. Cache 250 sampul: judul tepat tidak turun (validasi2 40→41), recall pendukung naik (uji 0,807→0,822; validasi2 0,768→0,804). Test baru di `test_narasi_ringkasan.py` dan `test_ocr_urutan.py` (plan: [docs/plans/2026-10-06-audit-bug-kode.md](docs/plans/2026-10-06-audit-bug-kode.md)).

### Fixed
- OCR `02_web_demo/ocr_headline.py`: sampah teks baku sampul tidak lagi masuk teks pendukung/judul — footer "majalah.tempo.co / mingguan" salah baca (MAJALAHTEMPOCO, TEMPOCO/MINGGUAN, TEMPOCOIMINGGUAN), label rubrik salah baca (INVES AGASI), harga/ISSN rusak, potongan acak huruf+angka, pecahan logo raksasa. Presisi kata pendukung naik di keempat set audit tanpa judul tepat yang turun; regresi di `01_notebook/test_ocr_urutan.py` (plan: [docs/plans/2026-10-06-ocr-sampah-teks-baku.md](docs/plans/2026-10-06-ocr-sampah-teks-baku.md)).

### Changed
- `02_web_demo/index.html`: memilih gambar unggahan baru kini selalu mengganti judul dan teks pendukung dengan hasil pembacaan gambar baru, termasuk yang sudah disunting untuk gambar sebelumnya (dilaporkan user sebagai bug); ketikan selama OCR gambar yang sama tetap dilindungi. Skenario smoke diperbarui, `browser_smoke_20261006_judul.json` 94/94; `01_TUTORIAL.md` B.3 diselaraskan (plan: [docs/plans/2026-10-06-judul-ganti-saat-gambar-baru.md](docs/plans/2026-10-06-judul-ganti-saat-gambar-baru.md)).

### Fixed
- `02_web_demo/index.html`: memilih gambar unggahan yang sama lagi kini memicu OCR ulang dan membatalkan hasil lama — sebelumnya browser tidak mengirim `change` sehingga gambar/hasil tidak berganti. Berkas aktif disimpan terpisah dan input dikosongkan setelah dibaca; nama berkas aktif ditampilkan ("Gambar aktif: …"). Skenario ditambahkan ke `01_notebook/smoke_browser_week3.py`; smoke `browser_smoke_20261006_unggah.json` 93/93 (plan: [docs/plans/2026-10-06-fix-unggah-file-sama.md](docs/plans/2026-10-06-fix-unggah-file-sama.md)).

### Fixed
- OCR judul `02_web_demo/ocr_headline.py` (lanjutan audit): kicker kecil berkeyakinan rendah tidak lagi tersambung (blok < 0,30 harus ≥ 0,85× tinggi judul), baris di tengah judul berleading rapat ikut tersambung, kata sebaris harus bersebelahan (baris bertumpuk berkotak tinggi tidak tertukar), batas baris judul 4→6. Validasi kedua 60 sampul: judul tepat 37→39/60 tanpa regresi judul; trade-off CER judul naik pada judul yang sudah salah pilih blok (deck terserap). Penurunan ambang ukuran ke 0,55 dicoba dan dibatalkan karena regresi (plan: [docs/plans/2026-10-06-audit-ocr-urutan-kata.md](docs/plans/2026-10-06-audit-ocr-urutan-kata.md)).

### Added
- Set validasi kedua di `01_notebook/audit_ocr_urutan.py` (`ocr_validasi2`), salinan beku `01_notebook/ocr_selector_audit1_20261006.py`, 4 test baru di `test_ocr_urutan.py`, smoke `browser_smoke_20261006_ocr2.json` (83/83); laporan audit, STATUS R1 dan BATASAN OCR diperbarui (plan: [docs/plans/2026-10-06-audit-ocr-urutan-kata.md](docs/plans/2026-10-06-audit-ocr-urutan-kata.md)).

### Fixed
- OCR `02_web_demo/ocr_headline.py`: teks pendukung disusun menurut tata letak (baris → kolom/paragraf → deck di bawah judul lebih dulu, lalu atas→bawah dan kiri→kanan) sehingga teaser antarkolom tidak lagi saling menyelip; baris lanjutan judul berhuruf hias yang berkeyakinan rendah disambung berantai dan disebut di catatan; logo "TEMPO" salah baca dan tagline huruf berjarak tidak lagi menjadi judul/pendukung. Validasi independen 60 sampul: urutan pendukung sempurna 13→35/56, judul tepat 41→43/60 (3 regresi tercatat di laporan) (plan: [docs/plans/2026-10-06-audit-ocr-urutan-kata.md](docs/plans/2026-10-06-audit-ocr-urutan-kata.md)).

### Added
- Audit OCR `docs/AUDIT_OCR_URUTAN_20261006.md`, skrip `01_notebook/audit_ocr_urutan.py`, salinan selector beku `01_notebook/ocr_selector_baseline_20261006.py`, regresi `01_notebook/test_ocr_urutan.py`, bukti `ocr_audit_urutan_20261006.json`/`ocr_audit_blok_20261006.json` dan smoke `browser_smoke_20261006_ocr.json` (83/83). STATUS R1/T05 dan BATASAN OCR diperbarui (plan: [docs/plans/2026-10-06-audit-ocr-urutan-kata.md](docs/plans/2026-10-06-audit-ocr-urutan-kata.md)).

### Changed
- Narasi ringkasan dan penjelasan ditulis ulang agar tidak kaku, tetap tanpa LLM: `02_web_demo/explanation_evidence.py` mendapat `ringkas()` (ringkasan awam isu/pihak/kiasan + keyakinan + perbandingan anotator) dan `explain()` kini menghasilkan blok "Mengapa <kelas>?" / "Arti kelas ini" / "Catatan anotator" serta satu daftar "Yang perlu dicek" alih-alih peringatan di tiap kalimat; tab Prediksi dan tab Penjelasan tidak lagi menampilkan paragraf yang sama. `app.py` (`ringkasan`, label anotator ke `explain`) dan `index.html` (render kartu ringkasan, blok penjelasan, ringkasan batch) diperbarui; dokumen BATASAN bagian 5, tutorial dan status R3 diselaraskan (plan: [docs/plans/2026-10-06-narasi-ringkasan-penjelasan.md](docs/plans/2026-10-06-narasi-ringkasan-penjelasan.md)).

### Added
- `01_notebook/test_narasi_ringkasan.py` dan smoke browser `browser_smoke_20261006_narasi.json` (83/83) (plan: [docs/plans/2026-10-06-narasi-ringkasan-penjelasan.md](docs/plans/2026-10-06-narasi-ringkasan-penjelasan.md)).

### Fixed
- `02_web_demo/index.html`: lima petunjuk berarah layout ("sebelah kanan", "panel kiri") diganti nama panel ("panel Mulai di sini", "panel Sampul pilihan") agar benar di desktop dan mobile (plan: [docs/plans/2026-10-06-sinkronisasi-docs-dan-catatan-minor.md](docs/plans/2026-10-06-sinkronisasi-docs-dan-catatan-minor.md)).
- `02_web_demo/batch_jobs.py`: pesan gagal item batch disusun `pesan_gagal()` — gambar rusak menjadi "Gambar tidak terbaca: format berkas tidak dikenali" dan path absolut server diganti nama berkas di manifest/CSV/JSON/UI; traceback lengkap tetap ke log server. Manifest job lama tidak diubah. Komentar usang di `02_web_demo/app.py` tentang peta narasi diselaraskan dengan kode (tanpa perubahan perilaku) (plan: [docs/plans/2026-10-06-sinkronisasi-docs-dan-catatan-minor.md](docs/plans/2026-10-06-sinkronisasi-docs-dan-catatan-minor.md)).

### Added
- `01_notebook/test_batch_error_message.py` (gagal terhadap kode lama) dan dua cek baru di `smoke_browser_week3.py`; smoke ulang `browser_smoke_20261006_langkah4.json` 83/83 lulus (plan: [docs/plans/2026-10-06-sinkronisasi-docs-dan-catatan-minor.md](docs/plans/2026-10-06-sinkronisasi-docs-dan-catatan-minor.md)).
- `docs/STATUS_REVISI_20261006.md`: matriks R1–R5/T01–T12 terbaru dengan bukti, batasan, penutupan temuan audit pagi, daftar terbuka dan jalur riset terpisah; audit pagi dipertahankan sebagai riwayat (plan: [docs/plans/2026-10-06-sinkronisasi-docs-dan-catatan-minor.md](docs/plans/2026-10-06-sinkronisasi-docs-dan-catatan-minor.md)).

### Changed
- Dokumen disinkronkan dengan aplikasi dan status 6 Oktober: `01_TUTORIAL.md` (bagian baru "Memakai aplikasi", notebook 740), `MULAI_DARI_SINI.md`, `00_BACA_DULU.md`, `TEKS_DELIVERY.md`, `02_BATASAN_TEKNIS.md` (peta gabungan R5, LIME 120 varian, fine-tuning, OCR, batch in-sample, versi pustaka), `docs/DELIVERY_WEEK_3.md`, `docs/HANDOFF_SERVER.md` (status server, perintah verifikasi, staging `verify_week3_http.py`). Termasuk temuan R4: dengan teks pendukung hasil OCR, ketiga kata GULA-GULA bernilai negatif (dinyatakan terbuka di UI); tidak diklaim seluruh revisi selesai (plan: [docs/plans/2026-10-06-sinkronisasi-docs-dan-catatan-minor.md](docs/plans/2026-10-06-sinkronisasi-docs-dan-catatan-minor.md)).

### Added
- Smoke UI browser headless `01_notebook/smoke_browser_week3.py` (Playwright/Chromium, desktop 1440×900 dan mobile 390×844) dan `requirements-browser.txt`: alur dataset/unggah/OCR/teks panjang, loading, lima tab, keyboard, race task/OCR, kegagalan jaringan/server, R5, tiga foto dosen, batch/ekspor dan katalog. Run final 80/80 lulus; screenshot dan checklist di `04_hasil_eksperimen/revisi_week3/browser_smoke_20261006/` dan `browser_smoke_20261006.json`. Bukan Firefox/Safari/Windows atau uji pengguna manusia (plan: [docs/plans/2026-10-06-smoke-browser-ui.md](docs/plans/2026-10-06-smoke-browser-ui.md)).

### Fixed
- `02_web_demo/index.html`: keterangan blok "Bukti task pilihan" dipindah ke kolom kanan di samping peta sehingga desktop tidak menyisakan kolom kosong; mobile tetap bertumpuk (plan: [docs/plans/2026-10-06-smoke-browser-ui.md](docs/plans/2026-10-06-smoke-browser-ui.md)).

### Fixed
- R5 peta gabungan: tab "Bukti gambar" di `02_web_demo/index.html` kini menampilkan `heatmap_padu_url` sebagai peta utama berlabel gabungan tiga task, dan peta task pilihan (`heatmap_url`) sebagai blok terpisah "Bukti task pilihan" dengan nama task dan kelas yang dijelaskan. Tanpa fallback: bila peta gabungan tidak ada, ditampilkan pesan, bukan peta task berlabel gabungan. Label tautan review batch dan petunjuk verifikasi visual diselaraskan. Backend, narasi dan atribusi kata tidak diubah (plan: [docs/plans/2026-10-06-r5-peta-gabungan-dan-changelog.md](docs/plans/2026-10-06-r5-peta-gabungan-dan-changelog.md)).

### Added
- `01_notebook/test_r5_heatmap.js` (regresi pemilihan peta/label, pergantian task, tanpa fallback; gagal terhadap UI lama) dan `01_notebook/verify_r5_http.py` (HTTP model nyata dataset tiga task + unggahan foto dosen, hash PNG). Bukti `04_hasil_eksperimen/revisi_week3/r5_heatmap_verification.json`: peta gabungan identik antar-task, peta task pilihan cocok dengan peta per task. Review visual browser belum dilakukan (plan: [docs/plans/2026-10-06-r5-peta-gabungan-dan-changelog.md](docs/plans/2026-10-06-r5-peta-gabungan-dan-changelog.md)).

### Added
- Environment dan baseline server `10.12.1.31`: venv Python 3.10.12 (via `uv`, karena `python3.10-venv` sistem tidak ada) dengan torch 2.14.1+cpu dan dependensi `requirements.txt`/`requirements-verification.txt`; enam regresi Python/JS lulus; demo berjalan di tmux `tempo-ui` pada `127.0.0.1:7861`; HTTP model nyata tiga task/input manual/batch dan OCR tiga foto dosen (2/3 tepat) lulus. Bukti `04_hasil_eksperimen/revisi_week3/server_baseline_20261006.json` dan folder `server_baseline_20261006/`; bukti historis tidak ditimpa dan 979 file manifest tetap cocok. Tunnel dari sisi user dan review visual browser belum diverifikasi (plan: [docs/plans/2026-10-06-lanjutan-week3-server.md](docs/plans/2026-10-06-lanjutan-week3-server.md)).

### Changed
- `CHANGELOG.md` disatukan dengan `../TRANSFER_CHANGELOG.md` (riwayat lengkap dari mesin asal, termasuk entri transfer dan plan lanjutan); dua entri ringkas yang hanya ada di changelog proyek dibuang karena versi rincinya sudah tercakup. Sebagian entri lama memakai path relatif folder induk (`DEMO_XAI_745_FULL/...`) (plan: [docs/plans/2026-10-06-r5-peta-gabungan-dan-changelog.md](docs/plans/2026-10-06-r5-peta-gabungan-dan-changelog.md)).

### Added
- Plan lanjutan Week 3 di server: setup/baseline, penutupan R5, smoke browser, sinkronisasi docs, paket/setup bersih dan audit akhir; jalur riset OCR/E01/E02 dipisahkan dengan kriteria selesai dan bukti yang diperlukan (plan: [docs/plans/2026-10-06-lanjutan-week3-server.md](docs/plans/2026-10-06-lanjutan-week3-server.md)).

### Added
- Paket Week 3 ditransfer dan diekstrak ke `research-user@10.12.1.31:/home/research-user/workspace/learn/DEMO_XAI_745_FULL`; checksum arsip dan 979 hash file manifest cocok. Bukti `WEEK3_TRANSFER_VERIFICATION.json` tersimpan di server; venv/cache/job/checkpoint tidak disalin, aplikasi belum dijalankan (plan: [docs/plans/2026-10-06-transfer-week3-server.md](docs/plans/2026-10-06-transfer-week3-server.md)).

### Added
- Handoff server `TEMPO_SERVER_HANDOFF_20261006.zip`, `docs/HANDOFF_SERVER.md`, `requirements-verification.txt`, manifest per-file dan tiga salinan foto dosen di `06_gambar_revisi/`. Memuat source UI terbaru/data/bukti/metrik dan prompt lanjutan, panduan setup/tmux/SSH tunnel; tanpa venv/cache/job/checkpoint besar/credentials/ZIP bersarang. Integritas/kecocokan source diperiksa; bukan final client atau deploy server (plan: [docs/plans/2026-10-06-handoff-server.md](docs/plans/2026-10-06-handoff-server.md)).

### Added
- Audit kesiapan delivery terhadap R1–R5/T01–T12 di `docs/AUDIT_DELIVERY_WEEK3_20261006.md`: verdict review baseline, belum final; heatmap utama R5 tidak sesuai acuan gabungan, ZIP/UI tertinggal, smoke browser/setup bersih belum terverifikasi, docs/sasaran OCR terbuka. Regresi/HTTP lulus; foto asli GULA LIME memperlihatkan DEMO positif pada konfigurasi judul manual/supporting kosong, tanpa klaim kelas benar. Bukti `revisi_week3/delivery_readiness_audit.json` dan `audit_gula_original_lime.json` (plan: [docs/plans/2026-10-06-audit-delivery-client.md](docs/plans/2026-10-06-audit-delivery-client.md)).

### Fixed
- Dua tag textarea self-closing di `02_web_demo/index.html` diganti penutup eksplisit; memperbaiki panel kanan hilang dan kontrol Batch bercampur dengan input setelah konversi teks pendukung. HTML5 struktur/HTTP dan regresi JS lulus (plan: [docs/plans/2026-10-06-fix-textarea-html.md](docs/plans/2026-10-06-fix-textarea-html.md)).

### Added
- `01_notebook/test_ui_html5.py` empat regresi parser HTML5 dan `revisi_week3/html5_fix_verification.json`, termasuk fixture yang mereproduksi textarea menelan workspace. html5lib 1.1 dipasang pada venv untuk verifikasi (plan: [docs/plans/2026-10-06-fix-textarea-html.md](docs/plans/2026-10-06-fix-textarea-html.md)).

### Changed
- `02_web_demo/index.html`: teks pendukung dataset/unggahan memakai textarea 5 baris yang dapat diperbesar; scroll halaman ke bawah diizinkan sesuai koreksi user agar teks panjang tidak dipadatkan. Tab hasil dan loading tetap tersedia; regresi/ID/HTTP/sintaks lulus (plan: [docs/plans/2026-10-06-teks-pendukung-multibaris.md](docs/plans/2026-10-06-teks-pendukung-multibaris.md)).

### Added
- Loading OCR/analisis pada `02_web_demo/index.html`: overlay spinner dengan pesan proses, indikator OCR inline, tombol busy dan aria-busy/live status. Analisis menunggu pembacaan gambar selesai; selesai/gagal/pergantian input membersihkan loading tanpa respons usang menimpa gambar baru. Tidak memakai persentase palsu (plan: [docs/plans/2026-10-06-loading-upload-analisis.md](docs/plans/2026-10-06-loading-upload-analisis.md)).
- `01_notebook/test_loading_ui.js` dan `revisi_week3/loading_ui_verification.json`: lifecycle OCR/analisis, respons usang dan kegagalan lulus bersama regresi navigasi/state/preview. Visual browser belum tersedia (plan: [docs/plans/2026-10-06-loading-upload-analisis.md](docs/plans/2026-10-06-loading-upload-analisis.md)).

### Changed
- `02_web_demo/index.html`: panduan tiga langkah dan preview sampul nyata menggantikan empty state dekoratif; judul/input dibuat lebih langsung, teks diperbesar, header/warna/panel dibuat lebih kontras, tab hasil diberi nama tindakan dan warna semantik. Workspace desktop tetap memakai tab, tanpa menambah halaman panjang (plan: [docs/plans/2026-10-06-ui-guidee-kontras.md](docs/plans/2026-10-06-ui-guidee-kontras.md)).

### Added
- Regresi sinkronisasi preview aktif di `01_notebook/test_workspace_ui.js` dan bukti `revisi_week3/guided_ui_verification.json`: mode dataset/unggahan kosong/baru/kembali dataset, navigasi/state/sintaks/ID/HTTP lulus; enam pasangan kontras utama 6,97–14,14. Review visual browser belum tersedia (plan: [docs/plans/2026-10-06-ui-guidee-kontras.md](docs/plans/2026-10-06-ui-guidee-kontras.md)).

### Changed
- `02_web_demo/index.html`: workspace desktop mengikuti tinggi layar; Analisis/Batch/Panduan menjadi view bergantian, hasil dibagi lima tab dengan navigasi keyboard. Form/preview dipadatkan, ringkasan prediksi tiga kolom dan anotator di tab Verifikasi; scroll otomatis ke hasil dihapus. Detail panjang tetap dapat digulir di panel dan mobile tetap adaptif (plan: [docs/plans/2026-10-06-ui-workspace-tanpa-scroll-panjang.md](docs/plans/2026-10-06-ui-workspace-tanpa-scroll-panjang.md)).

### Added
- `01_notebook/test_workspace_ui.js` dan `revisi_week3/workspace_ui_verification.json`: uji view/hash/active state/tab/keyboard/fokus, regresi state lama/sintaks/HTTP/ID lulus. Verifikasi visual browser belum tersedia (plan: [docs/plans/2026-10-06-ui-workspace-tanpa-scroll-panjang.md](docs/plans/2026-10-06-ui-workspace-tanpa-scroll-panjang.md)).

### Changed
- Redesign `DEMO_XAI_745_FULL/02_web_demo/index.html` menjadi dashboard modern terang sesuai pilihan user: panel input/preview kiri, hasil kanan dengan empty/loading state, ringkasan interpretasi sebelum bukti detail, header navigasi dan batch kolaps. Layout responsif, label form/fokus keyboard dan reduced-motion tersedia. Backend/model/OCR tidak diubah; ZIP review sebelumnya belum memuat redesign (plan: [docs/plans/2026-10-06-redesign-dashboard-ui.md](docs/plans/2026-10-06-redesign-dashboard-ui.md)).

### Added
- Regresi state dashboard di `01_notebook/test_week3_state.js` dan bukti `revisi_week3/dashboard_ui_verification.json`: ID lama utuh/unik, label valid, HTTP/sintaks/loading/invalidation/respons terlambat lulus. Review visual browser belum tersedia pada sesi ini (plan: [docs/plans/2026-10-06-redesign-dashboard-ui.md](docs/plans/2026-10-06-redesign-dashboard-ui.md)).

### Fixed
- Batch Week3 dipulihkan setelah server terputus pada 651 hasil: semua hash hasil lama tetap, 89 sisanya selesai, audit 740/740 lulus. Server pemeriksaan dijalankan terpisah dari terminal; HTTP tiga task/input manual dan error batch diulang serta lulus. Bukti `revisi_week3/scale740_resume_verification.json`; docs dan paket review diperbarui (plan: [docs/plans/2026-10-06-pemulihan-batch-week3.md](docs/plans/2026-10-06-pemulihan-batch-week3.md)).

### Added
- Audit HTTP seluruh 740 sampel lulus, 3.700 aset/740 URL heatmap/snapshot diperiksa, CSV/JSON lengkap; bukti `revisi_week3/scale740_verification.json`. Paket review dibangun ulang dengan docs/status terbaru, tanpa cache/job/environment lokal (plan: [docs/plans/2026-10-05-penutupan-teknis-week3.md](docs/plans/2026-10-05-penutupan-teknis-week3.md)).

### Fixed
- Encoding UTF-8 eksplisit pada `02_web_demo/class_catalog.py`, `app.py` dan `batch_jobs.py` memperbaiki pembacaan katalog/manifest di Windows. Regresi empat test lulus pada Linux/Windows (plan: [docs/plans/2026-10-05-penutupan-teknis-week3.md](docs/plans/2026-10-05-penutupan-teknis-week3.md)).

### Added
- Script `01_notebook/verify_week3_windows.py`, `verify_scale740.py`, `finalize_week3_delivery.py`, `experiment_selector_week3.py` dan `compare_decoder_week3.py`: verifikasi Windows terisolasi untuk halaman/katalog/tiga task/heatmap, audit skala, pengemasan setelah audit lulus, eksperimen selector dan beamsearch OCR, serta usulan transkripsi visual 11 kasus di `docs/PEMERIKSAAN_VISUAL_OCR.md`. Bukti di `04_hasil_eksperimen/revisi_week3/`; kandidat OCR tidak diterapkan karena belum cukup baik, beamsearch mengalami overflow (plan: [docs/plans/2026-10-05-penutupan-teknis-week3.md](docs/plans/2026-10-05-penutupan-teknis-week3.md)).

### Changed
- Checklist `docs/plan-revisi-demo-xai-tempo.md` diperbarui sesuai bukti dan `docs/DELIVERY_WEEK_3.md` diselaraskan dengan codebook operasional, gambar asli dosen, audit training dan verifikasi Windows; membedakan evaluasi agen dari pengguna manusia (plan: [docs/plans/2026-10-05-penutupan-teknis-week3.md](docs/plans/2026-10-05-penutupan-teknis-week3.md)).

### Added
- Uji OCR tiga gambar WhatsApp asli yang dikonfirmasi user sebagai gambar dosen: GULA-GULA/CUKAI headline tepat, WASWAS terbaca VJJASWAS. Script `01_notebook/verify_gambar_dosen.py`, output `revisi_week3/gambar_dosen/`, laporan `docs/VERIFIKASI_GAMBAR_DOSEN.md` dan tabel/delivery diperbarui; file asli/dataset tetap. Hash unggahan berbeda dari korpus; tidak mengarang label kelas (plan: [docs/plans/2026-10-05-gambar-asli-dosen.md](docs/plans/2026-10-05-gambar-asli-dosen.md)).

### Added
- Codebook operasional25kelas atas instruksi user (JSON `02_web_demo/codebook_operasional.json`, `docs/CODEBOOK_OPERASIONAL.md`), tabel13kasus `docs/TABEL_PEMERIKSAAN_REVISI.md` dan tiga tinjauan sub-agent `docs/EVALUASI_AGEN_WEEK3.md`. Katalog/narasi memakai definisi baru dengan provenance draft, bukan codebook asli; evaluasi agen bukan uji manusia (plan: [docs/plans/2026-10-05-codebook-dan-evaluasi-agen.md](docs/plans/2026-10-05-codebook-dan-evaluasi-agen.md)).

### Fixed
- Peta utama mengikuti taskpilihan, narasi zona tidak menyimpulkan objek, skor diberi disclaimerkalibrasi; reviewbatch mendapat preview/label/kandidat, input dilindungi saatpolling, counterkandidatOCR dan pesanerrorresume diperbaiki. Regresi Python/JS serta HTTPmodelnyata/katalog25kelas/previewupload lulus; docsdelivery dan paketreview diperbarui (plan: [docs/plans/2026-10-05-codebook-dan-evaluasi-agen.md](docs/plans/2026-10-05-codebook-dan-evaluasi-agen.md)).

### Added
- Hasil full training Kaggle COMPLETE disimpan di `DEMO_XAI_745_FULL/04_hasil_eksperimen/finetuned_kaggle/`: log600epoch/lima fold, prediksi740OOF dan audit metrik/split/hash. Macro-F1 Task1/2/3=0,5139/0,2461/0,3699; Task2 turun dari baseline0,3197 sehingga baseline demo tetap dipertahankan. Laporan `docs/HASIL_FULL_TRAINING_KAGGLE.md`; script audit mendapat opsi `--metrics-only`, uji synthetic lulus. Checkpoint belum diunduh/diintegrasikan (plan: [docs/plans/2026-10-05-audit-hasil-full-training.md](docs/plans/2026-10-05-audit-hasil-full-training.md)).

### Added
- Paket review `DEMO_XAI_745_WEEK3_REVIEW.zip` dengan dokumentasi/bukti Week3; integritas ZIP lulus, tanpa venv/cache/job/bobot training. Screenshot hasil baseline tersimpan di `revisi_week3/demo_week3.png`; bukan delivery penelitian final (plan: [docs/plans/2026-10-05-implementasi-week3.md](docs/plans/2026-10-05-implementasi-week3.md)).
- Week3 baseline: katalog25kelas `class_catalog.py`, bukti/selector lima narasi `explanation_evidence.py`, batch persisten/review/retry/CSV/JSON `batch_jobs.py`; script regresi HTTP/JS/Python, diagnosis OCR30, pembanding selector dan audit hasil full training. Bukti di `DEMO_XAI_745_FULL/04_hasil_eksperimen/revisi_week3/`; hasil dan batasan di `docs/DELIVERY_WEEK_3.md` (plan: [docs/plans/2026-10-05-implementasi-week3.md](docs/plans/2026-10-05-implementasi-week3.md)).

### Fixed
- `02_web_demo/app.py` dan `index.html`: input manual dataset/unggahan benar-benar dipakai, snapshot task/input dan respons terlambat dilindungi, engine bersama diserialisasi; narasi memakai atribusi task pilihan dan menyatakan keterbatasan. `ocr_headline.py` menyimpan blok/koordinat JSON-safe, kandidat dan skor terpisah, menyaring TEMPO5/TEMPO 5; selector replay19/30 tepat, target80% belum tercapai. Codebook resmi/integrasi fine-tuned/penerimaan penuh tetap terbuka (plan: [docs/plans/2026-10-05-implementasi-week3.md](docs/plans/2026-10-05-implementasi-week3.md)).

### Added
- Plan Week3 dan revisi UI/OCR/XAI/MTL di `docs/plans/2026-10-05-week3-dan-revisi-demo-xai.md`: menggabungkan T01–T12 dengan batch/ekspor/delivery, audit awal kode, prioritas konsistensi task-input-bukti, gerbang evaluasi/integrasi fine-tuned, estimasi dan kriteria penerimaan. Belum mengubah aplikasi (plan: [docs/plans/2026-10-05-week3-dan-revisi-demo-xai.md](docs/plans/2026-10-05-week3-dan-revisi-demo-xai.md)).

### Added
- Full training Kaggle private `research-account/tempo-full-training` versi1 diluncurkan atas instruksi user: dua T4,5fold×120epoch,batch16,timeout6jam; status RUNNING dan quota sebelum submit29,82jam. Bukti `DEMO_XAI_745_FULL/04_hasil_eksperimen/finetuned_kaggle/launch_status.json`, panduan diperbarui; hasil final belum tersedia (plan: [docs/plans/2026-10-05-mulai-full-training-kaggle.md](docs/plans/2026-10-05-mulai-full-training-kaggle.md)).

### Added
- Runner full training dua T4 (5-fold/120epoch, global batch16) di `DEMO_XAI_745_FULL/01_notebook/kaggle_benchmark/full_training/`: checkpoint atomic tiap5epoch, resume model/optimizer/scaler/RNG kedua rank, model/metrik/prediksi per fold dan OOF final. Panduan `docs/TRAINING_KAGGLE.md`; smoke Kaggle versi2 berhasil restart epoch1→epoch2 dan evaluasi148sampul, bukti di `DEMO_XAI_745_FULL/04_hasil_eksperimen/kaggle_full_smoke/`. Bobot class-weight dipastikan float32 setelah versi1 gagal dtype; full training belum dimulai (plan: [docs/plans/2026-10-05-full-training-kaggle.md](docs/plans/2026-10-05-full-training-kaggle.md)).

### Added
- Uji optimasi dua T4 terverifikasi di `DEMO_XAI_745_FULL/01_notebook/kaggle_benchmark/optimized/`: fused AdamW, static graph, transfer pinned/nonblocking, pemeriksaan finite gabungan setiap langkah. Paired epoch baseline 20,46 detik vs kandidat 15,60 detik; empat rank sukses dan loss global berbeda <0,001. Output/log/perbandingan di direktori hasil `kaggle_benchmark/optimized/`, panduan diperbarui (plan: [docs/plans/2026-10-05-verifikasi-optimasi-kaggle.md](docs/plans/2026-10-05-verifikasi-optimasi-kaggle.md)).

### Added
- Benchmark DDP dua T4 di `DEMO_XAI_745_FULL/01_notebook/kaggle_benchmark/dual_gpu/`, batch global 16 dengan weighted CE global; kedua rank/encoder terverifikasi. Output/log/perbandingan di `DEMO_XAI_745_FULL/04_hasil_eksperimen/kaggle_benchmark/dual_gpu/`: epoch 24,13 detik vs 30,98 detik satu GPU, pengurangan waktu 22,13%; panduan diperbarui (plan: [docs/plans/2026-10-05-benchmark-kaggle-dual-gpu.md](docs/plans/2026-10-05-benchmark-kaggle-dual-gpu.md)).

### Added
- Hasil benchmark Kaggle versi 3 sukses setelah verifikasi nomor HP: satu T4, 592 sampul/epoch dalam 30,98 detik, kedua encoder diperbarui, peak allocated 3,89 GiB. Output/log disimpan di `DEMO_XAI_745_FULL/04_hasil_eksperimen/kaggle_benchmark/`; panduan memuat estimasi 600 epoch 5,16 jam dan batasannya (plan: [docs/plans/2026-10-05-benchmark-kaggle.md](docs/plans/2026-10-05-benchmark-kaggle.md)).

### Changed
- Benchmark Kaggle versi 2 terbukti gagal sebelum training karena runtime CPU; ditambahkan kernel diagnostik private dan hasil `DEMO_XAI_745_FULL/04_hasil_eksperimen/kaggle_benchmark/gpu_diagnostic.json`. Editor Kaggle meminta verifikasi nomor HP untuk akses GPU/internet; panduan diperbarui, waktu epoch belum tersedia (plan: [docs/plans/2026-10-05-benchmark-kaggle.md](docs/plans/2026-10-05-benchmark-kaggle.md)).

### Added
- Script dan metadata benchmark satu epoch di `DEMO_XAI_745_FULL/01_notebook/kaggle_benchmark/`, panduan `docs/BENCHMARK_KAGGLE.md`, dataset private `research-account/tempo-benchmark-20261005`, serta job private `research-account/tempo-one-epoch-benchmark` versi 1 dikirim lalu gagal DNS saat setup; paket private versi 2 berisi wheels/bobot offline (778 file terverifikasi) dan job versi 2 berhasil dikirim, dengan permintaan GPU T4/batas satu jam (plan: [docs/plans/2026-10-05-benchmark-kaggle.md](docs/plans/2026-10-05-benchmark-kaggle.md)).

### Added
- Kaggle CLI 2.2.4 dipasang di environment tool user terisolasi via uv; executable `/home/research-user/.local/bin/kaggle`, verifikasi versi dan subcommand kernels/auth berhasil. Autentikasi akun belum dilakukan (plan: [docs/plans/2026-10-05-install-kaggle-cli.md](docs/plans/2026-10-05-install-kaggle-cli.md)).

### Added
- Runner `DEMO_XAI_745_FULL/01_notebook/train_finetune_windows.py` untuk full fine-tuning 5-fold/120 epoch di Windows, microbatch 1/effective batch 16, AMP dan checkpointing, normalisasi weighted CE per batch efektif; uji satu optimizer step pada 16 sampul berhasil, hasil terpisah di `DEMO_XAI_745_FULL/04_hasil_eksperimen/smoke_training_windows.json` (plan: [docs/plans/2026-10-05-training-gtx1650-windows.md](docs/plans/2026-10-05-training-gtx1650-windows.md)).
- Lingkungan training Windows terisolasi di `C:\Users\User\tempo-training-20261005` (Python 3.11.9, PyTorch 2.7.0 CUDA 11.8), salinan data/bobot, script `DEMO_XAI_745_FULL/01_notebook/benchmark_finetune_gpu.py`, snapshot `DEMO_XAI_745_FULL/requirements-training-windows.lock.txt`, hasil `DEMO_XAI_745_FULL/04_hasil_eksperimen/benchmark_finetune_gpu.json`, dan panduan `docs/PERSIAPAN_TRAINING_GPU_WINDOWS.md`. Tiga langkah full encoder training berhasil pada GTX 1650 4 GiB dengan AMP dan checkpointing; gradien dan pembaruan bobot kedua encoder terverifikasi, peak allocated 3,47 GiB (plan: [docs/plans/2026-10-05-training-gtx1650-windows.md](docs/plans/2026-10-05-training-gtx1650-windows.md)).

### Added
- Persiapan koneksi SSH Windows `192.168.0.26`: fingerprint ED25519 dicocokkan dengan hasil PowerShell user dan disimpan di `~/.ssh/known_hosts`; autentikasi key berhasil sebagai `msi\user` dan pemeriksaan remote `nvidia-smi` mendeteksi GTX 1650 dengan VRAM 4 GiB (plan: [docs/plans/2026-10-05-koneksi-ssh-windows.md](docs/plans/2026-10-05-koneksi-ssh-windows.md)).

### Added
- Benchmark CPU terbatas pada data nyata di `DEMO_XAI_745_FULL/01_notebook/benchmark_finetune_cpu.py`, hasil `DEMO_XAI_745_FULL/04_hasil_eksperimen/benchmark_finetune_cpu.json`, dan panduan `docs/PERSIAPAN_TRAINING_CPU.md`: audit hardware, 740 gambar, gradien kedua encoder, serta estimasi waktu training (plan: [docs/plans/2026-10-05-persiapan-training-cpu.md](docs/plans/2026-10-05-persiapan-training-cpu.md)).

### Fixed
- `DEMO_XAI_745_FULL/01_notebook/finetune_encoder_colab.ipynb`: model preprocessing dilepas setelah transform diambil dan model tiap fold dilepas setelah bobot disimpan, mencegah model fold menumpuk di GPU (plan: [docs/plans/2026-10-05-persiapan-training-cpu.md](docs/plans/2026-10-05-persiapan-training-cpu.md)).

### Added
- `01_notebook/finetune_encoder_colab.ipynb` — notebook baru untuk fine-tuning penuh CLIP+IndoBERT (~276 juta parameter, disetujui dosen), didesain untuk dijalankan di Google Colab (GPU T4) karena mesin lokal hanya CPU. Skema 5-fold CV, 120 epoch/fold, identik dengan evaluasi model beku untuk perbandingan apel-ke-apel. Diverifikasi lewat dry-run di CPU lokal dengan 4 sampul nyata: shape cocok (1280 dim gabungan), gradien terbukti mengalir ke kedua encoder, tidak ada syntax error (plan: `docs/plans/2026-09-29-fine-tuning-encoder-colab.md`)
- `DEMO_XAI_TEMPO_W2_2026-09-29.zip` (97 MB) — paket delivery Minggu 2 diperbarui, mencakup perbaikan notebook demo, klarifikasi `02_BATASAN_TEKNIS.md`, dan verifikasi setup Windows dari environment bersih; diverifikasi dengan mengecek isi zip (tanpa `venv`/`__pycache__`/`_cache`, file kunci lengkap)
- Proposal Minggu 3 (menunggu ACC dosen, belum dikerjakan): crop area logo lalu evaluasi ulang (risiko rendah) dan fine-tuning sebagian encoder (risiko tinggi, scoping waktu terpisah) — dua-duanya di luar ruang lingkup yang dikunci 22 September (plan: `docs/plans/2026-09-22-timeline-3-minggu.md`)

### Changed
- `02_BATASAN_TEKNIS.md`: ditambahkan ringkasan eksekutif di awal dokumen yang menyorot dua batasan paling penting (performa model Macro-F1 0,320, dan Grad-CAM/LIME sebagai adaptasi bukan implementasi baku), menegaskan keduanya di luar ruang lingkup perbaikan (keputusan 22 Sep: arsitektur & dataset tidak diubah). Bagian 7 dan 8 diperbarui: "740 dari 745" diluruskan jadi "740 sampul, dataset final", dan catatan notebook `DEMO_XAI_TEMPO.ipynb` yang menyebut "belum dijalankan ulang untuk 740 sampul" diperbarui mengikuti perbaikan 29 Sep

### Verified
- Uji end-to-end lewat HTTP `/api/analisis` untuk tiga mode (dataset leave-one-out, unggahan, dan sampul NON_METAFORA) — semua HTTP 200, tanpa regresi pada label tampil (R2), paragraf kesimpulan + badge GABUNGAN (R3), dan heatmap terpadu (R5) (plan: `docs/plans/2026-09-28-week2-lime-dan-kesimpulan.md`)
- Item "Konteks Key word" (revisi 15 Sep hal. 5) dikonfirmasi sudah terimplementasi (`xai_core.py:899-920`) dan berfungsi lewat HTTP — checkbox di timeline sempat tertinggal tak tercentang meski kodenya sudah ada sejak 28 Sep (plan: `docs/plans/2026-09-22-timeline-3-minggu.md`)

### Fixed
- `01_notebook/run_xai_analysis.py` docstring/komentar menyebut "5 sampul contoh" padahal kode memakai 7 (satu per domain unik) — diselaraskan
- `01_notebook/DEMO_XAI_TEMPO.ipynb` error `KeyError: 'status_validasi'` dan seluruh keterangan tertinggal dari dataset pilot 189 sampul: notebook masih merujuk `DATASET_189_TASK2_DOMAIN.csv`/`fitur_clip_indobert_189.npz` (berkas sudah tidak ada) dan kolom `status_validasi` yang tidak pernah ada di dataset final. Diarahkan ke `DATASET_740_TASK2_DOMAIN.csv`/`fitur_clip_indobert_740.npz`, ringkasan validasi kini memakai kolom `eligibility` yang benar-benar ada, dan seluruh narasi "189 sampul"/"target 745" diganti "740 sampul" (dataset final). Tabel peringatan dan ringkasan batasan diperbarui memakai angka nyata dari `04_hasil_eksperimen/hasil_mtl_740_task2domain.json`, `analisis_recall_per_kelas_740.csv`, `hasil_uji_satu_gambar_740.json`, dan `analisis_zona_740.json` (plan: `docs/plans/2026-09-29-sinkronisasi-notebook-demo-740.md`)

### Added
- `DEMO_XAI_TEMPO_W2_2026-09-28.zip` (96,3 MB) — paket delivery Minggu 2; diverifikasi dengan diekstrak ke folder bersih lalu dijalankan
- `docs/DELIVERY_WEEK_2.md` — laporan Minggu 2
- Kaitan judul dengan konteks (permintaan "Konteks Key word", revisi hal. 5): kata kunci kini disandingkan langsung dengan isu yang diprediksi, dan kata yang menarik ke arah berbeda ikut disebut bila pengaruhnya berarti
- Paragraf kesimpulan berbahasa awam di atas penjelasan teknis (revisi R3): `susun_kesimpulan()` di `02_web_demo/xai_core.py`, kartu tersendiri di antarmuka dengan penanda "dasar pembacaan konsisten" / "perlu diperiksa ulang". Dirangkai dari hasil model, definisi codebook, dan catatan anotator — bukan model bahasa (plan: `docs/plans/2026-09-28-week2-lime-dan-kesimpulan.md`)
- Atribusi kata dengan LIME (revisi R4): `atribusi_kata_lime()` di `xai_core.py`, memakai model surrogate dan sampling berbobot jarak sehingga pengaruh antar-kata ikut terhitung. Dipakai sebagai metode baku; occlusion tetap tersedia lewat parameter `metode_atribusi`
- `01_notebook/uji_banding_atribusi.py` + `04_hasil_eksperimen/uji_banding_atribusi.json` — uji banding LIME vs occlusion pada 25 sampul: gejala "seluruh kata negatif" 1/25 (LIME) vs 2/25 (occlusion), sepakat kata teratas 22/25, korelasi urutan 0,851, stabilitas LIME 1,0, waktu 17,68 s vs 0,83 s per sampul
- Metode atribusi yang dipakai kini ditampilkan ke pembaca, tidak lagi perlu ditebak
- `lime>=0.2` di `requirements.txt`

### Changed
- Jumlah varian LIME diturunkan dari 200 ke 120 setelah diuji: 80 varian memberi korelasi 0,960 terhadap 200 dengan kata teratas sama pada 4/5 sampul, sementara waktu turun dari 15,9 ke 6,1 detik. Analisis dataset kini ~12-23 detik, sebelumnya ~60 detik
- `MULAI_DARI_SINI.md` menunjuk laporan Minggu 2 dan menyebut perkiraan waktu analisis
- `02_BATASAN_TEKNIS.md` bagian 2 ditulis ulang: dari "occlusion, bukan LIME" menjadi perbandingan dua metode beserta angkanya, termasuk catatan bahwa kasus spesifik dosen ("GULA-GULA DEMO BURUH") belum dapat diuji ulang karena berkasnya tidak ada di korpus
- `02_BATASAN_TEKNIS.md` bagian 5 menyebut paragraf kesimpulan baru dan batasnya untuk sampul di luar dataset

### Fixed
- `str.lower()` pada nama kelas merusak akronim ("Ekonomi, Bisnis & BUMN" menjadi "bumn"); ditangani `_huruf_kecil_aman()`

### Fixed
- Folder cache tidak pernah dibersihkan: tiap analisis menyimpan sampai 4 berkas PNG sehingga memproses banyak sampul menumpuk ratusan MB. Kini hanya 400 berkas terbaru yang disimpan (`bersihkan_cache()` di `app.py`)
- Dokumen merujuk path venv yang tidak ada (`../../demo_xai/venv/bin/python`) di `00_BACA_DULU.md` dan docstring `app.py`; pembaca baru akan gagal di langkah pertama
- Mengganti gambar tidak memperbarui teks: kolom headline/pendukung tetap berisi hasil OCR gambar sebelumnya karena hanya diisi bila kosong (`if (!hl.value)`). Kini isi yang berasal dari OCR ditimpa saat gambar berganti, sementara teks yang disunting pengguna tetap dipertahankan dan diberi tahu lewat pesan status
- Teks lama tertinggal ketika pembacaan gambar baru gagal: kolom kini dikosongkan lebih dulu sebelum OCR dijalankan
- Jawaban OCR yang datang terlambat dapat menimpa hasil gambar yang lebih baru bila pengguna berganti gambar dengan cepat; ditangani dengan penomoran permintaan
- Berpindah ke tab "Pilih dari dataset" meninggalkan berkas dan teks unggahan sebelumnya; kini dibersihkan
- OCR memilih sisa logo TEMPO sebagai headline ketika logo tertutup objek foto ("TEN" pada sampul "ANCANG-ANCANG JOKOWI"): penyaringan logo dibuat dua lapis, dan pemilihan headline kini memakai skor gabungan tinggi × posisi × keyakinan × penalti panjang, bukan tinggi blok semata
- Satu baris paragraf deskripsi dapat mengalahkan headline karena panjang teks tidak diperhitungkan (sampul "NAF HODA BARU KADIN")
- Baris headline berpenggal tanda hubung tersambung dengan spasi ("ANCANG- ANCANG"); kini "ANCANG-ANCANG"
- Prediksi tetap ditampilkan tanpa isyarat apa pun ketika judul masukan rusak; kini muncul blok peringatan bila judul kurang dari dua kata atau di bawah 8 karakter
- Tanda kontribusi kata tercetak `+-0.023` pada nilai negatif; sekarang diformat lewat helper `_tanda()` (`02_web_demo/xai_core.py`)
- Kata berkontribusi negatif tidak lagi disebut "paling menopang keputusan"; bila seluruh kata negatif, dinyatakan terus terang bahwa tidak ada kata yang menopang
- Blok berlabel `GABUNGAN` tidak pernah muncul: kini tetap tampil selama ada peta panas, dengan isi menyesuaikan ada-tidaknya catatan anotator (`xai_core.py`)
- Nilai NaN yang terbaca sebagai string `"nan"` pada 83 sampul NON_METAFORA lolos sebagai catatan anotator; disaring lewat helper `_bersih()`
- Celah path traversal pada `/api/heatmap/<token>` dan `/api/unggahan/<token>`: token kini dibatasi huruf, angka, dan garis bawah
- Teks usang dari versi 189 sampul di antarmuka: "Macro-F1 0,174" → 0,320, "189 tersedia" → 740, "173 catatan" → 657, "12 sampul" → 63, "16 dari 189" → 83 dari 740

### Added
- `DEMO_XAI_TEMPO_W1_2026-09-22.zip` (96,3 MB) — paket delivery Minggu 1, tanpa `venv`/cache/pycache; diverifikasi dengan diekstrak ke folder bersih lalu dijalankan
- `MULAI_DARI_SINI.md` — halaman pertama paket: cara menjalankan di Windows/Linux, urutan membaca dokumen, dan tiga batasan yang harus diketahui sejak awal
- `setup_windows.bat` dan `jalankan_windows.bat` — setup dan menjalankan aplikasi di Windows dengan dua kali klik, termasuk deteksi versi Python dan pesan galat yang menjelaskan solusinya
- `jalankan_linux.sh` — padanan untuk Linux/macOS
- `docs/DELIVERY_WEEK_1.md` — laporan lengkap Minggu 1: pengantar untuk pembaca baru, cara menjalankan di Windows & Linux, status 5 revisi, rincian yang dikerjakan, 9 bug yang diperbaiki, bukti dan angka, rancangan Minggu 2-3, batasan, dan keputusan ruang lingkup
- Pembacaan teks sampul otomatis (OCR) untuk mengisi kolom headline saat unggah (revisi R1): modul `02_web_demo/ocr_headline.py`, endpoint `POST /api/ocr`, dan pengisian otomatis di antarmuka. Kolom tetap dapat disunting; kegagalan OCR tidak menggagalkan unggah
- `01_notebook/uji_banding_ocr.py` + `04_hasil_eksperimen/uji_banding_ocr.json` — uji banding OCR pada 20 sampul asli. Setelah audit: F1 0,895, presisi 0,960, 14/20 sempurna dan 0 gagal total, dibanding OCR mentah F1 0,204
- Penyaringan logo "TEMPO" yang terbaca rusak agar tidak terpilih sebagai headline — F1 0,684 → 0,804, lalu 0,895 setelah audit lanjutan
- Peta panas terpadu ketiga task (`gradcam_terpadu()` di `xai_core.py`): peta per task dirata-ratakan setelah masing-masing dinormalisasi, lalu dinormalisasi ulang. Ditampilkan sebagai peta utama; peta per task tetap tersedia di panel "tampilan teknis" (revisi R5)
- `02_web_demo/label_display.py` — pemetaan 25 nama kelas teknis ke istilah awam untuk tampilan saja; dataset tidak diubah (revisi R2)
- `docs/2026-09-22-keputusan-ocr.md` — dasar pemilihan EasyOCR dibanding TrOCR, beserta batasannya
- `easyocr` dan `sentencepiece` di `requirements.txt`
- `02_BATASAN_TEKNIS.md` — dokumen batasan yang sebelumnya dirujuk dua kali di `01_TUTORIAL.md` tetapi tidak ada
- Timeline 3 minggu (22 Sep – 12 Okt 2026) di `docs/plans/2026-09-22-timeline-3-minggu.md`: rencana penutupan revisi R1–R5 + mode batch, beserta 4 keputusan ruang lingkup (arsitektur tidak diubah, LIME sungguhan, temuan fokus-logo dilaporkan jujur, output batch + satuan)
- Dokumen pemahaman sistem + inventaris revisi pembimbing di `docs/2026-09-22-pemahaman-demo-dan-revisi.md` (arsitektur DEMO_XAI_745_FULL, 5 butir revisi dari `revision.pdf`, 5 temuan verifikasi kode)
- Aturan kerja project di `.claude/CLAUDE.md`: setiap task wajib punya plan, plan disimpan ke `docs/plans/`, setiap perubahan dicatat ke changelog (plan: `docs/plans/2026-09-22-setup-workflow-rules.md`)
- Direktori `docs/plans/` sebagai tempat penyimpanan plan
- `CHANGELOG.md` sebagai catatan perubahan project
