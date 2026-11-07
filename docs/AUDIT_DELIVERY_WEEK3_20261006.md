# Audit kesiapan delivery dan revisi client

**Tanggal:** 2026-10-06  
**Verdict:** siap untuk demo/review baseline dengan batasan; **belum siap disebut delivery final seluruh revisi**.

## Dasar penilaian

Acuan: `plan-revisi-demo-xai-tempo.md`, backlog Week 3, laporan R1–R5 Week 1/2, tiga gambar asli dosen, keputusan user dan source/hasil terbaru. Plan revisi adalah rangkuman/usulan, bukan kontrak atau transkrip VN; sasaran OCR 80% tidak otomatis menjadi syarat client yang sudah disepakati.

Instruksi user tentang codebook operasional dan tinjauan sub-agent berlaku. Tidak ada kebutuhan menunggu codebook resmi yang memang tidak tersedia. Tinjauan agen sudah memenuhi permintaan user tersebut, tetapi bukan bukti pengguna manusia memahami UI.

## Temuan utama

| Prioritas | Temuan | Bukti | Penutupan |
|---|---|---|---|
| P1 | R5 belum sesuai acuan client: peta utama diminta gabungan semua task, UI satuan kini memakai task pilihan | Kutipan R5 di `DELIVERY_WEEK_1.md`; renderer `const utama = d.heatmap_url` di `02_web_demo/index.html` | Tampilkan gabungan sebagai ringkasan semua task, dan pisahkan peta task pilihan sebagai bukti berlabel. Jangan mengaitkan peta gabungan dengan atribusi satu task secara keliru |
| P1 | ZIP delivery tertinggal dari UI terbaru | Integritas ZIP lulus, tetapi `index.html` berbeda dari source; tiga test UI terbaru belum ada di ZIP | Bangun ulang setelah perbaikan/acceptance terakhir, lalu cocokkan source dan integritas |
| P1 | Rendering UI terbaru dan setup paket bersih belum dibuktikan | Uji terbaru HTML5/VM/HTTP; Windows terdahulu memakai vendor serta data/bobot dari instalasi lama | Smoke browser desktop/mobile, kemudian launcher ZIP terbaru pada environment bersih, terutama Windows |
| P2 | Dokumentasi serah terima belum sinkron | Tutorial/TEKS_DELIVERY masih narasi lama; beberapa laporan masih menunggu definisi resmi atau menandai skala/Windows belum diuji | Perbarui panduan tab/loading/multibaris, keputusan codebook, status/model dan teks delivery |
| P2 / sasaran penelitian | Kualitas OCR dan evaluasi teks lengkap masih terbatas | Selector produksi 19/30 (63,3%); gambar dosen 2/3; set diagnosis bukan set independen; keputusan ground truth masih draft | Nyatakan batasan/koreksi manual. Jika target 80% menjadi penerimaan final, perlu evaluasi independen dan peningkatan terukur |

Bug textarea sebelumnya **sudah diperbaiki**, bukan bug aktif yang ditemukan audit ini. Empat test HTML5 lulus, termasuk fixture yang mereproduksi workspace hilang akibat tag self-closing. Ini belum menggantikan review visual layout.

## Matriks R1–R5

| Revisi | Status | Bukti/batas |
|---|---|---|
| R1 — teks otomatis | Diterapkan, kualitas terbatas | OCR/kandidat/edit/loading tersedia; CUKAI benar pada foto asli, WASWAS masih salah huruf |
| R2 — istilah mudah dipahami | Diterapkan | Label ramah pengguna dan katalog tersedia; keterbacaan UI terakhir belum diuji browser/client setelah fix |
| R3 — kesimpulan awam | Diterapkan | Lima strategi berbasis bukti, sumber dan task/class binding diuji; bukan narasi LLM |
| R4 — atribusi kata/LIME | Diterapkan; kasus asli diuji pada konfigurasi tertentu | Foto asli GULA-GULA, judul manual, supporting kosong, Task2 LIME: GULA-GULA −0,01162; DEMO +0,01769; BURUH −0,03821. Semua-negatif tidak muncul pada run ini. Tidak menyatakan kelas prediksi sudah benar |
| R5 — peta gabungan semua task | Belum sesuai tampilan utama satuan sekarang | Backend menghitung gabungan, tetapi UI utama menampilkan peta task pilihan |

Kelas hasil GULA-GULA adalah PERMAINAN_KONTES, dengan skor sekitar 0,4808. Tidak ada ground truth kelas unggahan yang divalidasi, sehingga ini regresi perilaku atribusi, bukan bukti ketepatan klasifikasi. Hasil satu run LIME tidak menjadi jaminan untuk setiap konfigurasi teks/gambar.

## Matriks T01–T12 dan Week 3

| ID | Status audit |
|---|---|
| T01 | Codebook operasional 25 kelas selesai sesuai instruksi user; keselarasan dengan anotasi historis belum dibuktikan |
| T02 | Pengantar/panduan tiga langkah/katalog tersedia; penerimaan keterbacaan UI terakhir belum terverifikasi |
| T03 | Input final/task/snapshot dan respons usang lulus; edit teks dataset menghitung ulang fitur |
| T04 | Diagnosis 30 headline dan usulan transkripsi tersedia; supporting/layout lengkap serta set independen belum lengkap |
| T05 | Baseline/diagnosis headline ada; belum evaluasi seluruh ekstraksi teks |
| T06 | Selector/beamsearch dibandingkan; kandidat tidak diterapkan tanpa bukti cukup. Latensi decoder memakai kondisi thread/init berbeda |
| T07 | Logo/kandidat/koreksi dan pemisahan input final diterapkan; kualitas otomatis masih terbatas |
| T08 | Sumber klaim dan task/class binding tersedia; posisi heatmap tidak dipakai menamai objek |
| T09 | Lima strategi narasi diterapkan dan diuji |
| T10 | Regresi otomatis, tiga tinjauan agen sesuai permintaan, gambar dosen, backend Windows dan skala 740 tersedia; UI browser/clean package terbaru belum diuji |
| T11 | Full fine-tuning/audit metrik OOF selesai. Task2 turun 0,3197 → 0,2461 sehingga demo mempertahankan baseline. Checkpoint belum diintegrasikan; E01 perbaikan input dengan split/checkpoint sama dan E02 tuning terkontrol belum dilaporkan selesai |
| T12 | Paket review tersedia, tetapi belum memuat source UI terbaru dan dokumentasi belum sinkron; belum final |
| Batch/ekspor/restart | Audit 740 berhasil/nol gagal, 3.700 aset/740 URL/snapshot dan CSV 741 baris lulus. Pemulihan mempertahankan 651 hash hasil lama. Ini eksplorasi in-sample, bukan angka akurasi |

Integrasi fine-tuned bukan syarat otomatis untuk demo baseline: keputusan mempertahankan baseline didukung metrik. Jika client mengharapkan aplikasi memakai checkpoint Kaggle, expectation itu belum terpenuhi dan perlu disebutkan.

## Verifikasi audit ini

- Python: 4 test HTML5, 4 regresi Week3, 1 audit training fixture lulus. Fixture bukan training nyata.
- JavaScript: suite loading/OCR/race, state analisis, tab/keyboard/preview lulus.
- HTTP model nyata tiga task, headline/supporting manual, batch satu berhasil/satu gambar rusak, CSV/JSON/aset lulus ulang.
- Foto asli GULA-GULA LIME selesai 21,3 detik, pada input yang disebut di atas; `audit_gula_original_lime.json`.
- ZIP integritas lulus, **kesetaraan dengan source gagal**. `test_ui_html5.py`, `test_loading_ui.js`, `test_workspace_ui.js` belum di ZIP.
- HTTP halaman cocok source, 740 sampel dan katalog 10/7/8 tersedia. Server lokal dipulihkan setelah proses sesi audit sempat berhenti; ini tidak diklaim sebagai bug browser.

Bukti ringkas: `DEMO_XAI_745_FULL/04_hasil_eksperimen/revisi_week3/delivery_readiness_audit.json`.

## Sebelum delivery final

1. Tutup ketidaksesuaian R5 tanpa mengaburkan bukti task pilihan.
2. Smoke UI terakhir di browser: upload/OCR, edit teks panjang, loading/error, analisis, tab, pergantian mode dan batch.
3. Sinkronkan tutorial, batasan dan teks serah terima; jelaskan baseline dan kualitas OCR.
4. Bangun ulang ZIP, cocokkan source/bukti dan jalankan dari setup bersih.
5. Pisahkan fitur selesai dari sasaran OCR/evaluasi/semantik yang masih terbuka. Jangan menulis “100% semua revisi selesai”.

**Rekomendasi:** serahkan sebagai versi demo untuk review revisi, bukan hasil final seluruh revisi client. Audit ini tidak mengubah produk atau membangun ulang ZIP.
