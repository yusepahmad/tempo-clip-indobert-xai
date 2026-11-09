# Changelog

Semua perubahan penting pada project ini dicatat di file ini.
Format mengikuti [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

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
- Codebook operasional25kelas, tabel13kasus dan tiga evaluasi agen; katalog/narasi terintegrasi, buginput/batch/peta/skor diperbaiki. Lihat docs/EVALUASI_AGEN_WEEK3.md; bukan uji manusia (plan root: docs/plans/2026-10-05-codebook-dan-evaluasi-agen.md).

### Added
- Week3 baseline: katalog25kelas, snapshot input/task, OCR kandidat/logo, lima strategi evidence, batch persisten dengan review/retry dan ekspor CSV/JSON, hasil regresi/diagnosis serta audit training. Lihat `docs/DELIVERY_WEEK_3.md`; penerimaan penelitian dan integrasi fine-tuned belum lengkap (plan root: `docs/plans/2026-10-05-implementasi-week3.md`).


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
