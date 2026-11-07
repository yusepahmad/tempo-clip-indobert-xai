# Plan Week 3 dan Revisi Demo XAI Tempo

**Tanggal:** 2026-10-05
**Status:** done

> Ditutup sebagai plan induk historis pada 17 Oktober 2026. Implementasi
> aplikasi dan batch telah memiliki subplan serta bukti; acceptance yang masih
> terbuka dipindahkan ke `docs/SPRINT_ROADMAP.md` agar status implementasi tidak
> tercampur dengan target OCR, validasi pengguna, dan target model.

## Progres implementasi 2026-10-05
User telah menginstruksikan pengerjaan. T02/T03/T07–T09, batch/ekspor dan regresi aplikasi diterapkan melalui [subplan implementasi](2026-10-05-implementasi-week3.md). Hasil nyata dan matriks bagian yang masih terbuka ada di [Delivery Week 3](../DELIVERY_WEEK_3.md). T01/T04–T06/T10–T12 belum seluruhnya memenuhi penerimaan: codebook/gambar asli, anotasi evaluasi, skala/Windows dan hasil training/integrasi masih diperlukan. Paket review baseline disiapkan terpisah dari delivery penelitian final.

## Tujuan
Menyelesaikan Week 3 (batch, ekspor, pengujian, delivery) sekaligus revisi pada `docs/plan-revisi-demo-xai-tempo.md`: informasi task/kelas, konsistensi input-hasil, headline OCR, dan narasi berbasis bukti. Menyiapkan evaluasi hasil fine-tuning Kaggle tanpa menghambat perbaikan demo atau mengklaim model telah meningkat.

Plan ini dibuat setelah membaca kode saat ini; belum menyatakan implementasi revisi selesai. Permintaan terbaru user memperluas backlog Week 3. Batas lama “tidak ada training ulang” telah berubah melalui instruksi eksplisit full fine-tuning pada sesi ini; crop logo, perubahan label dataset, backbone baru, dan LLM tetap tidak termasuk.

## Ruang Lingkup
### Perubahan pada task penyusunan plan ini
- File ini dan entry root `CHANGELOG.md` saja.
- Dokumen revisi asal dipertahankan sebagai referensi; kode aplikasi tidak diubah sekarang.

### File/modul yang direncanakan pada implementasi berikutnya
Seluruh path relatif root project, kecuali disebut lain:
- `DEMO_XAI_745_FULL/02_web_demo/app.py`, `index.html`, `xai_core.py`, `ocr_headline.py`, `label_display.py`.
- Calon modul baru pada `02_web_demo/`: `class_catalog.py`, `analysis_service.py`, `explanation_evidence.py`, `batch_jobs.py` (nama final dapat disesuaikan ketika implementasi).
- Script evaluasi/regresi baru di `DEMO_XAI_745_FULL/01_notebook/`; fixture dan hasil baru terpisah di `04_hasil_eksperimen/revisi_week3/`.
- Dokumentasi delivery: `00_BACA_DULU.md`, `01_TUTORIAL.md`, `02_BATASAN_TEKNIS.md`, `TEKS_DELIVERY.md`, `docs/DELIVERY_WEEK_3.md`, matriks revisi→bukti, changelog root dan changelog paket bila paket delivery diperbarui.
- Adapter inferensi encoder fine-tuned hanya setelah hasil/checkpoint valid; perubahan loader, preprocessing, atribusi dan deployment ditetapkan dalam subplan integrasi.

### Tidak disentuh
Dataset mentah `03_data/`, gambar `05_gambar/`, ID task/kelas asli, baseline hasil lama, arsitektur tiga head paralel, runner/job training yang sedang berjalan. Tidak mengambil gambar baru dari internet atau mengarang anotasi/codebook. Tidak menggabungkan angka eksperimen baru ke banner sebelum evaluasi dan sumbernya jelas.

## Dasar dan Temuan Audit Awal
| Bukti | Implikasi rencana |
| --- | --- |
| Laporan Week 2 dan timeline sebelumnya sudah menutup R1–R5 secara fungsional, tetapi kasus gambar dosen tertentu belum tersedia | Kerjakan revisi sebagai penyempurnaan dan regresi baru; jangan menghapus riwayat/klaim keterbatasan |
| `ocr_headline.py` memakai EasyOCR id/en CPU; blok menyimpan posisi/tinggi/skor, selector heuristik sudah ada | Ukur engine dan selector secara terpisah; tidak langsung mengganti engine |
| Pola logo belum secara jelas menampung `TEMPO5` | Jadikan fixture wajib dan ukur sebelum memperluas aturan; hindari membuang headline sah seperti TEMPE/MOMEN |
| `index.html` memiliki nomor urut request OCR `_ocrKe` dan perlindungan edit manual | Pertahankan mekanisme yang sudah ada; audit request analisis serta invalidasi hasil secara terpisah |
| Mode dataset di `app.py` mengambil headline/fitur verified dan melatih head leave-one-out; unggahan memakai teks form dan training head seluruh korpus | Edit teks dataset membutuhkan ekstraksi fitur ulang; tidak cukup mengganti teks yang ditampilkan. Protokol dataset/batch/unggahan harus eksplisit |
| `app.py` menghitung atribusi pada task pilihan, tetapi `susun_kesimpulan()` tidak menerima ID task dan mengaitkan kata ke isu Task 1 | Prioritas tinggi: kontrak task/kelas pada bukti dan klaim harus diperbaiki sebelum variasi narasi |
| Definisi domain ada di `xai_core.py`, label ramah pengguna ada di `label_display.py`; codebook resmi lengkap belum ditemukan pada pencarian awal | Inventarisasi sumber resmi; jangan menganggap semua definisi 25 kelas telah diverifikasi |
| Fine-tuning Kaggle merupakan eksperimen terpisah, sementara demo saat ini memakai fitur encoder baseline dan head yang dilatih runtime | Checkpoint fine-tuned tidak dapat dipasang sebagai head saja; perlu adapter encoder, preprocessing, serta XAI yang sesuai |

## Langkah dan Backlog Terpadu
Urutan kerja implementasi: tulis subplan → kerjakan → verifikasi → catat changelog. Perubahan scope memperbarui subplan. PIC pelaksana teknis: Codex bersama user; verifikasi definisi/contoh resmi: user/peneliti.

### W3-01 — Bekukan acuan dan kontrak analisis (P0; T01/T03/T08)
1. Inventarisasi 10 kelas Task 1, 7 kelas Task 2, 8 kelas Task 3 dari dataset/model/codebook; catat sumber definisi dan contoh yang benar-benar tersedia.
2. Reproduksi task/headline yang tidak sinkron serta kasus logo. Pisahkan fakta hasil reproduksi dari dugaan screenshot.
3. Tetapkan kontrak analysis_id dan snapshot input: sample/upload ID, fingerprint gambar, headline final, supporting final, task XAI, kelas target, metode atribusi aktual, asal input, model/protokol.
4. Bukti atribusi membawa task_id/class_id; klaim kata tidak boleh berpindah task. Heatmap gabungan tiga task diberi identitas berbeda dari heatmap task pilihan.
5. Bedakan prediksi, label pembanding, dan catatan manusia. Unggahan tidak mendapat anotasi/label corpus otomatis.
**Selesai bila:** reproduksi dan kontrak terdokumentasi; setiap hasil/atribusi/narasi merujuk snapshot yang sama. Langkah ini tidak menunggu hasil training.

### W3-02 — UI, katalog kelas, dan state hasil (P0; T01–T03)
- Pengantar menjelaskan tujuan tiga task, batas prototipe, dan pemeriksaan teks sebelum analisis.
- Gunakan label ramah pengguna yang sudah ada sebagai default; alternatif nama baru dari revisi ditinjau dengan sumber penelitian sebelum mengganti istilah.
- Katalog setiap kelas: label resmi, definisi, kriteria, pembeda, contoh berlabel, sumber. Isi yang belum memiliki sumber ditandai belum diverifikasi, bukan dibuat seolah resmi.
- Preview input, headline/supporting final dan pilihan task terlihat sebelum analisis; hasil menampilkan snapshot yang digunakan.
- Perubahan gambar/teks/task/mode menginvalidasi hasil dan request lama. Request ID/abort handling mencegah balasan analisis/OCR lama menimpa form/hasil terbaru.
- Koreksi manual dipertahankan; untuk mode dataset yang diedit, fitur teks harus dihitung ulang tanpa mencampur fitur verified lama. Mode/protokol ditampilkan.
**Selesai bila:** pergantian input saat request berjalan tidak mencampur hasil; ketiga task dan kelas tersedia dari sumber yang diverifikasi. Review 2–3 pengguna dapat dijadwalkan setelah UI stabil, bukan diklaim otomatis.

### W3-03 — Evaluasi dan perbaikan headline OCR (P1; T04–T07)
1. Pakai ulang benchmark OCR yang tersedia sebagai baseline historis. Buat set diagnosis baru 30–50 sampul dengan manifest ID, kategori kesulitan, ground truth headline/supporting, sumber dan status verifikasi.
2. Pisahkan subset pengembangan aturan dan subset pemeriksaan yang tidak dipakai tuning; catat jumlah per kategori. Verified headline dataset tidak selalu mencakup seluruh teks gambar, sehingga evaluasi ekstraksi membutuhkan anotasi teks yang diperiksa.
3. Simpan blok OCR mentah dan koordinat, kandidat headline, alasan selector, headline otomatis/final serta edit pengguna.
4. Ukur exact match headline setelah normalisasi yang disepakati, CER/WER bila ground truth lengkap, jumlah logo salah pilih, kegagalan per kategori, median/p95 latensi.
5. Perbaiki logo bercampur nomor (`TEMPO5`), gabungan beberapa baris, dan kandidat ambigu. Pertahankan pilihan kandidat serta koreksi manual; jangan menganggap teks terbesar selalu judul.
6. Bandingkan konfigurasi EasyOCR/selector terlebih dahulu; engine alternatif hanya jika baseline membuktikan masalah pembacaan yang tidak terselesaikan. Engine/ambang final mengikuti hasil uji, bukan screenshot.
7. Pisahkan skor pembacaan OCR, status seleksi headline dan skor klasifikasi. Jangan menampilkan rata-rata OCR sebagai peluang headline benar.
**Selesai bila:** regresi logo/multibaris/manual edit lulus; tabel sebelum/sesudah pada set yang sama tersedia. Target ≥80% dari revisi adalah sasaran usulan, bukan janji hasil. Bila gambar cukai asli tidak tersedia, fixture blok sintetis hanya menguji selector dan tidak diklaim uji end-to-end sampul asli.

### W3-04 — Narasi XAI dengan sumber bukti (P2; T08–T10)
- Strukturkan bukti MODEL/CODEBOOK/ANOTATOR/GABUNGAN dan asal tiap klaim, mencakup task, kelas, input dan model yang dijelaskan.
- Audit klaim pada template lama, termasuk pernyataan maksud/kritik umum yang tidak mempunyai rujukan, dan atribusi Task 2 yang disebut mendukung Task 1.
- Selector deterministik untuk lima strategi: bukti teks, visual, perbandingan anotasi, definisi kelas, gabungan/terbatas. Strategi boleh memakai beberapa bukti; tidak mengacak sinonim demi variasi.
- Semua strategi memuat hasil, bukti tersedia, makna kelas bila ada, keterbatasan dan tindak lanjut. Region heatmap tidak otomatis diberi nama objek; zona logo bukan bukti memahami ilustrasi.
- Jangan memakai threshold baru sebagai probabilitas terkalibrasi; aturan keraguan/ambigu dicatat beserta dasar evaluasinya.
**Selesai bila:** pada seluruh kasus regresi tidak ada klaim lintas task, anotasi palsu atau fakta tanpa sumber; variasi narasi mengikuti kondisi bukti.

### W3-05 — Core bersama dan mode batch (wajib Week 3)
- Ekstrak core analisis bersama untuk satuan/batch; konfigurasi model/protokol berada pada konteks yang eksplisit.
- Buat job batch asynchronous dengan queue satu worker awal, manifest input/hasil per item, progres queued/running/success/failed dan pemulihan item yang belum selesai. Model global tidak boleh dilatih/diubah bersamaan oleh request dataset lain; gunakan konteks terisolasi atau serialisasi akses.
- Batch default memakai occlusion (metode aktual dicatat), sementara satuan mempertahankan LIME/fallback. Bila LIME dipilih batch, UI memberi estimasi berdasarkan benchmark dan progres.
- Batch unggahan mengikuti headline selector/koreksi: item ambigu masuk status perlu pemeriksaan, bukan diberi headline buatan. Item gambar rusak/OCR gagal tidak menggagalkan semua item.
- Tentukan dua protokol: batch eksplorasi memakai model tetap; evaluasi dataset memakai prediksi out-of-fold yang sesuai fold. Prediksi in-sample bukan metrik evaluasi dan bukan leave-one-out.
- Ekspor CSV ringkas + JSON bukti/model/metode/protokol + indeks gambar/heatmap. Simpan output sebelum cache sementara dibersihkan; hasil yang masih aktif tidak dihapus oleh batas cache lama.
**Selesai bila:** batch kecil campuran item valid/rusak selesai dengan status per item, ekspor dapat dibaca, progress akurat, dan hasil satuan/batch konsisten bila konfigurasi/protokolnya sama. Uji skala 740 dilakukan sesudah pilot dengan estimasi storage/latensi, bukan menjalankan 740 pelatihan leave-one-out.

### W3-06 — Evaluasi fine-tuning dan gerbang integrasi (P3; T11)
- Setelah Kaggle COMPLETE, unduh hasil/model; cek 5 fold, masing-masing120epoch, 740 OOF unik, mapping kelas, split, konfigurasi, checkpoint dan log. Job RUNNING atau smoke bukan hasil eksperimen penuh.
- Hitung Macro-F1/accuracy per task, precision/recall/F1/support per kelas, confusion matrix, metrik fold dan contoh salah klasifikasi; bandingkan baseline hanya setelah protokol/split dipastikan setara.
- Pisahkan E00 baseline, eksperimen fine-tuning yang sudah berjalan, dan E01 OCR/input. Training saat ini memakai verified text; perbaikan OCR demo tidak boleh disebut penyebab peningkatan dari fine-tuning.
- Tuning baru E02/early stopping memerlukan validation yang terpisah; jangan memilih epoch/checkpoint terbaik dengan label test fold. Hasil job saat ini120epoch fixed dicatat apa adanya.
- Integrasi membutuhkan encoder visual CLIP/IndoBERT beserta head dari checkpoint yang sama dan preprocessing identik; LIME/visual attribution harus memanggil model yang sama dengan prediksi. Jangan memakai encoder lama untuk XAI hasil encoder baru.
- Dataset demo evaluatif memakai model held-out fold untuk sampel tersebut. Unggahan baru memerlukan kebijakan model deployment yang dinyatakan; ensemble fold bukan OOF valid untuk sampel corpus yang pernah dilihat sebagian fold.
- Baseline tetap tersedia. Aktifkan model baru hanya setelah pemeriksaan output/logits, task mapping dan XAI lulus; tidak menjanjikan F1 naik atau fokus logo hilang.
**Selesai bila:** hasil evaluasi tersimpan terpisah dan sumber metrik UI jelas. Integrasi dapat menyusul jika checkpoint/XAI belum kompatibel; demo revisi tetap bisa ditinjau dengan baseline.

### W3-07 — Regresi, dokumentasi dan delivery (T10/T12)
- Jalankan satuan dataset/unggahan serta batch: headline diedit, pergantian gambar/task, balasan request terbalik, OCR ambigu/kosong, gambar rusak, NON_METAFORA, atribusi semua-negatif, heatmap None/logo, prediksi-anotasi berbeda dan cache cleanup.
- Gambar cukai/GULA-GULA DEMO BURUH asli dicatat tersedia atau belum tersedia. Fixture sintetis tidak menggantikan bukti gambar dosen.
- Review dua mode pada Linux dan smoke Windows bila lingkungan tersedia; rekam keterbatasan yang belum diuji.
- Perbarui tutorial, batasan dan matriks ID T01–T12 + revisi lama R1–R5 → lokasi implementasi → bukti uji → status.
- Paket delivery hanya menyertakan artefak yang diperlukan, tanpa venv/kredensial/cache. Salinan docs dalam paket disinkronkan saat delivery, satu sumber utama plan tetap root docs.
**Selesai bila:** hasil uji dan kasus gagal tercatat, paket bisa dijalankan dari lingkungan bersih, status setiap revisi jujur dan bukti bisa ditelusuri.

## Jadwal dan Prioritas
Deadline historis12Oktober2026 perlu diperlakukan sebagai target review yang masih perlu dikonfirmasi jika berubah. Revisi baru memperluas scope; estimasi7–10hari kerja dari dokumen sumber tidak otomatis muat dalam satu minggu.

| Urutan | Alokasi awal | Output |
| --- | --- | --- |
| 1 | 0,5–1hari | W3-01 audit, kontrak input/task/bukti, fixture |
| 2 | 1–1,5hari | W3-02 UI/state dan katalog sumber yang tersedia |
| 3 | 1,5–2hari | W3-03 OCR baseline/selector/koreksi |
| 4 | 1–1,5hari | W3-04 narasi berbasis bukti |
| 5 | 1,5–2hari | W3-05 batch/progres/ekspor |
| 6 | 1–1,5hari | W3-07 regresi dan delivery |
| Terpisah | 0,5–1hari evaluasi; integrasi perlu scoping | W3-06 hasil Kaggle dan kompatibilitas model |

Target review6–12Oktober: konsistensi hasil dan atribusi, OCR selector/koreksi, batch pilot/ekspor, bukti regresi serta batasan. Katalog25kelas yang belum tersumber, benchmark OCR diperluas, integrasi fine-tuned dan uji740 penuh tidak dinyatakan selesai bila belum lolos gerbang. Bila kapasitas/deadline tidak cukup, catat item tersisa dan alasan; jangan memotong validasi atau menaikkan klaim.

## Risiko & Asumsi
- Codebook resmi dan gambar revisi dosen mungkin belum ada: pekerjaan state/core/batch dapat lanjut; definisi/ground truth spesifik menunggu sumber yang benar.
- Kode singleton ENG melatih model per request: refactor concurrency diperlukan sebelum batch dan satuan berjalan bersamaan.
- Koreksi dataset tanpa recompute fitur akan memberi penjelasan salah konteks; explicit feature recomputation wajib.
- Jumlah cache dan latensi CPU untuk OCR/XAI bisa membatasi batch; ukur pilot sebelum skala740.
- Model fine-tuned tidak otomatis kompatibel dengan demo baseline; evaluasi dan adapter terpisah wajib.
- Tidak ada target kenaikan Macro-F1 yang dijanjikan; OCR≥80% dan review2–3pengguna merupakan usulan ukuran penerimaan.

## Verifikasi
1. Plan mencakup T01–T12 serta batch/progres/ekspor/delivery dari Week3 lama.
2. Implementasi berikutnya punya subplan, hasil uji sebelum/sesudah dan changelog.
3. Invariant utama: gambar, teks final, task, kelas, model dan atribusi berasal dari analisis yang sama.
4. Ground truth/codebook yang belum diverifikasi ditandai; klaim sumber dan protokol evaluasi dipisahkan.
5. Hasil training baru digunakan setelah kelengkapan OOF/checkpoint diperiksa; banner tidak diganti dari perkiraan.

## Keputusan/Informasi yang Perlu Dilanjutkan
- Lokasi codebook resmi lengkap dan gambar dosen; bila belum ada, minta saat pekerjaan bagian itu dimulai.
- Nama task alternatif merupakan usulan: default mempertahankan ID/label penelitian dan display mapping yang tersedia.
- Kebijakan headline kosong: koreksi diperlukan sesuai jalur multimodal sekarang; tidak otomatis menambah mode tanpa teks.
- Deadline review dan kapasitas annotation/review manusia perlu dipastikan; tidak menghambat audit dan perbaikan konsistensi awal.

## Pekerjaan Pertama Setelah Plan
W3-01: buat kontrak analysis snapshot + bukti task/kelas, reproduksi race hasil dan klaim lintas task, lalu subplan W3-02. Tidak perlu menunggu training selesai.
