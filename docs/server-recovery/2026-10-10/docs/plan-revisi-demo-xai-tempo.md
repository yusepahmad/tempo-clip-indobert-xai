# Plan Revisi Demo XAI — Dekoding Metafora Sampul Majalah Tempo

> **Dokumen riwayat per 5 Oktober 2026** (rencana kerja dan checklist pada tanggal itu; isi lama tidak diubah). Status terbaru: [STATUS_REVISI_20261006.md](STATUS_REVISI_20261006.md) (6 Oktober 2026). Koreksi status bertanggal 6 Okt ada di bawah checklist bagian 12 dan di bagian "Pembaruan 6 Oktober 2026" di akhir dokumen.

Tanggal penyusunan: 5 Oktober 2026  
Status: implementasi teknis tersedia; penerimaan penelitian sebagian terbuka. Status terbaru (diperbarui 6 Okt): [STATUS_REVISI_20261006.md](STATUS_REVISI_20261006.md); ringkasan delivery: [DELIVERY_WEEK_3.md](DELIVERY_WEEK_3.md)  
Lingkup: UI/UX, OCR, Explainable AI (XAI), dan eksperimen Multi-Task Learning (MTL).

## 1. Tujuan dan dasar rencana

Membuat demo lebih mudah dipahami, memperbaiki teks yang masuk ke model, dan menghasilkan penjelasan prediksi yang relevan serta dapat ditelusuri sumbernya.

Rencana ini memperjelas rangkuman VN pada percakapan sebelumnya dan menggunakan enam gambar terlampir sebagai konteks tambahan. Dokumen ini bukan transkrip baru atau kutipan verbatim dari audio. Detail implementasi, ukuran dataset, target metrik, dan estimasi waktu di bawah adalah **usulan kerja**, bukan persyaratan yang sudah disepakati dari VN.

**Hasil yang dituju:** pengguna memahami tiga task, dapat memeriksa headline, memperoleh prediksi dan penjelasan yang konsisten, serta mengetahui kapan hasil perlu diperiksa ulang.

Urutan prioritas:

1. **P0 — UI/UX:** jelaskan tujuan, task, dan kelas; perbaiki konsistensi task yang dipilih.
2. **P1 — OCR:** pisahkan ekstraksi teks dari pemilihan headline dan pertahankan koreksi manual.
3. **P2 — XAI:** susun penjelasan berdasarkan bukti yang tersedia, dengan beberapa struktur narasi.
4. **P3 — MTL:** evaluasi dan eksperimen setelah input serta alur demo stabil.

## 2. Masalah yang perlu diselesaikan

| Area | Temuan dari rangkuman/gambar | Dampak | Perubahan yang direncanakan |
|---|---|---|---|
| UI/UX | Tujuan analisis dan definisi task/kelas perlu diperjelas | Pengguna sulit memahami arti hasil | Tambahkan pengantar, penjelasan task, dan katalog kelas |
| Terminologi | Gambar memberi catatan “cari istilah lain” di dekat nama task | Nama task mungkin belum cukup jelas | Gunakan label ramah pengguna dengan istilah penelitian tetap tersedia |
| OCR | Pada contoh sampul cukai, kolom headline berisi `TEMPO5`; judul sebenarnya ada di teks pendukung | Model dapat menerima headline yang salah | Pisahkan deteksi teks, pemilihan headline, dan pemeriksaan pengguna |
| Confidence | UI menampilkan keyakinan OCR 90% pada contoh headline yang salah | Angka tinggi dapat memberi kesan headline sudah benar | Jelaskan arti skor dan evaluasi pemilihan headline secara terpisah |
| Konsistensi hasil | Pada satu screenshot, pilihan task, tag XAI, dan headline hasil tampak berbeda | Pengguna dapat membaca penjelasan untuk konteks yang keliru | Audit sinkronisasi input, task pilihan, dan hasil; penyebab belum dipastikan |
| XAI | Dua contoh kesimpulan memiliki struktur sangat mirip | Penjelasan terasa berulang dan kurang menonjolkan bukti spesifik | Buat strategi narasi sesuai kondisi bukti |
| Sumber penjelasan | Demo sudah memiliki penanda MODEL, ANOTATOR, CODEBOOK, dan GABUNGAN | Penanda ini perlu tetap terjaga saat narasi diubah | Pertahankan asal setiap klaim dan bedakan anotasi dari atribusi model |
| MTL | Kualitas model masih menjadi bagian eksperimen | Perbaikan tampilan belum tentu memperbaiki prediksi | Evaluasi model secara terpisah dengan data uji yang sesuai |

**Catatan:** screenshot menunjukkan gejala, belum membuktikan penyebab bug. Contohnya, perbedaan headline dapat berasal dari hasil lama, perubahan input, atau state aplikasi. Task investigasi perlu memastikan penyebab sebelum menentukan perbaikan.

## 3. Perjelas tiga task dan kelasnya

Nama berikut terlihat pada gambar. Label alternatif adalah usulan UI dan perlu diselaraskan dengan codebook penelitian.

| Task | Nama pada gambar | Usulan label UI | Pertanyaan yang dijawab |
|---|---|---|---|
| Task 1 | Isu Utama | Topik Utama Sampul | Isu atau topik apa yang dibahas sampul? |
| Task 2 | Domain Sumber Metafora | Ranah Metafora | Ranah konsep apa yang digunakan sebagai perumpamaan? |
| Task 3 | Tipe Entitas Sasaran | Jenis Pihak yang Disorot | Jenis pihak atau entitas apa yang menjadi sasaran pembahasan? |

Label UI tidak mengubah makna label dataset. Simpan ID task dan label kelas asli sebagai acuan internal.

### Informasi wajib untuk setiap task

- Nama, definisi singkat, dan tujuan analisis.
- Daftar kelas sesuai codebook, bukan kelas A/B/C yang dibuat sementara.
- Penjelasan hubungan kelas dengan task: mengapa kelas tersebut menjadi salah satu kategori jawaban.
- Contoh berlabel yang sudah diperiksa dan batasan penggunaan hasil.

### Informasi wajib untuk setiap kelas

| Field | Isi yang disiapkan |
|---|---|
| Nama kelas | Label resmi dari codebook |
| Definisi | Arti kelas dalam 1–2 kalimat |
| Kriteria masuk | Ciri yang membuat contoh termasuk kelas ini |
| Batas pembeda | Perbedaan dengan kelas terdekat atau kondisi yang tidak termasuk |
| Contoh | Sampul berlabel beserta alasan singkat |
| Sumber | Rujukan bagian codebook/anotasi yang dipakai |

Contoh label yang terlihat pada gambar adalah **Permainan & Kontes** dan **Konsumsi & Transaksi** untuk domain sumber metafora. Definisi lengkap harus diambil dari codebook proyek; jangan menyimpulkannya hanya dari nama kelas.

## 4. Struktur UI yang diusulkan

### A. Pengantar

Tampilkan tujuan aplikasi, penjelasan tiga task, dan ringkasan status prototipe. Letakkan detail arsitektur serta metrik pada bagian “Tentang model”, agar pengantar tetap mudah dipahami.

Contoh copy untuk ditinjau:

> Demo ini membantu menelaah topik, ranah metafora, dan jenis pihak yang disorot pada sampul majalah Tempo. Hasil mencakup prediksi model dan bukti yang tersedia untuk membantu pemeriksaan. Periksa teks hasil pembacaan otomatis sebelum memulai analisis.

### B. Input dan pemeriksaan teks

1. Pengguna memilih gambar dari dataset atau mengunggah gambar sendiri.
2. UI menampilkan preview gambar, headline terpilih, dan teks pendukung secara terpisah.
3. Pengguna dapat mengoreksi teks atau memilih kandidat headline lain.
4. Pengguna memilih task yang akan dijelaskan oleh XAI.
5. Analisis menggunakan teks final yang sudah terlihat pada form.

### C. Hasil

Urutan tampilan:

1. Ringkasan input yang dipakai: gambar, headline final, task XAI, dan asal input.
2. Prediksi tiga task: nama task, kelas, dan skor model.
3. Ringkasan penjelasan untuk task XAI yang dipilih.
4. Bukti teks dan bukti visual yang tersedia.
5. Definisi kelas melalui panel detail atau tombol informasi.
6. Perbandingan dengan label/anotasi hanya untuk sampel yang memang memilikinya.

Setiap hasil terikat pada satu analisis. Perubahan gambar, headline, atau task harus membatalkan hasil lama atau memberi penanda jelas bahwa analisis perlu dijalankan ulang.

## 5. Backlog implementasi

PIC belum ditentukan. Pembagian peran di bawah dapat dikerjakan satu orang atau dibagi ke tim.

| ID | Prioritas | Task | Peran | Dependensi | Kriteria selesai |
|---|---|---|---|---|---|
| T01 | P0 | Susun definisi tiga task dan katalog kelas | Peneliti/produk | Codebook | Semua kelas punya definisi, pembeda, dan contoh terverifikasi |
| T02 | P0 | Revisi pengantar dan navigasi definisi | UI/UX | T01 | Tujuan dan arti task dapat ditemukan sebelum analisis |
| T03 | P0 | Audit sinkronisasi input, task, dan hasil | Aplikasi | Alur saat ini | Hasil selalu merujuk input/task yang benar; hasil lama tidak membingungkan |
| T04 | P1 | Buat dataset evaluasi OCR | Data/ML | Sampul contoh | Ground truth headline dan teks tersedia dengan aturan penilaian tetap |
| T05 | P1 | Ukur baseline dan sumber kegagalan OCR | ML | T04 | Kesalahan baca teks dibedakan dari kesalahan memilih headline |
| T06 | P1 | Bandingkan konfigurasi/kandidat OCR | ML | T05 | Kandidat diuji pada set yang sama; kualitas dan latensi dicatat |
| T07 | P1 | Integrasikan pemilihan headline dan koreksi | Aplikasi/ML | T06 | Headline, logo, teks pendukung, dan edit pengguna terpisah dengan jelas |
| T08 | P2 | Tetapkan struktur bukti dan asal klaim XAI | ML/aplikasi | T01, T03 | Setiap klaim punya sumber; anotasi tidak disebut atribusi model |
| T09 | P2 | Implementasikan lima strategi narasi | Aplikasi | T07, T08 | Narasi mengikuti bukti dan kondisi input, bukan variasi kata acak |
| T10 | P2 | Uji alur penuh dan konsistensi explanation | QA/peneliti | T02, T03, T07, T09 | Kasus regresi lulus dan klaim tanpa bukti dihapus |
| T11 | P3 | Evaluasi baseline MTL dan eksperimen terbatas | ML | Pipeline stabil, split data | Metrik data uji per task dan per kelas tersedia |
| T12 | P3 | Dokumentasikan hasil dan siapkan demo | Seluruh peran | T10, T11 | Ada hasil evaluasi, batasan, perubahan, dan skenario demo |

T12 dapat menghasilkan catatan demo awal setelah T10. Hasil eksperimen MTL ditambahkan saat T11 selesai, sehingga demo tidak harus menunggu tuning model.

## 6. Rincian OCR: baca teks, lalu pilih headline

### 6.1 Dataset evaluasi

Usulan awal: **30–50 sampul**, mencakup contoh dari lampiran dan variasi berikut:

- Headline bersih, pendek, dan panjang.
- Logo penerbit lebih besar daripada headline.
- Headline beberapa baris dan beberapa judul sekunder.
- Kontras rendah, resolusi rendah, dan teks kecil.
- Gambar dengan anotasi serta tanpa anotasi, jika memang tersedia.

Untuk gambar tanpa headline yang dapat dibaca, gunakan status khusus “tidak terbaca/tidak tersedia”; jangan memaksakan ground truth teks.

Ground truth minimal: ID sampel, headline utama, teks pendukung yang relevan, wilayah teks bila tersedia, kategori kesulitan, dan catatan pemeriksa.

### 6.2 Baseline dan diagnosis

Nilai dua tahap secara terpisah:

1. **Ekstraksi teks:** apakah kata-kata pada gambar berhasil dibaca?
2. **Pemilihan headline:** apakah teks yang dipilih merupakan judul utama?

Pada contoh `CUKAI ABAL-ABAL ROKOK ILEGAL`, teks utama muncul di kolom pendukung tetapi headline terpilih adalah `TEMPO5`. Kasus ini harus menjadi regresi wajib: peningkatan OCR saja belum membuktikan pemilihan headline sudah benar.

### 6.3 Perubahan pipeline yang diusulkan

1. Ambil teks per wilayah beserta koordinat dan skor bila tersedia.
2. Bedakan kandidat headline, logo/masthead, judul sekunder, dan metadata penerbit.
3. Pilih headline dengan mempertimbangkan tata letak, gabungan beberapa baris, dan aturan logo penerbit.
4. Jika kandidat ambigu, tampilkan pilihan atau minta koreksi pengguna.
5. Simpan hasil OCR mentah, headline otomatis, serta headline final secara terpisah.
6. Model dan XAI menggunakan headline final yang sama.

Aturan logo harus diuji pada sampul lain; jangan menggunakan aturan “teks terbesar selalu headline”. Daftar model pada screenshot hanya menjadi bahan eksplorasi. Pemilihan kandidat memerlukan pemeriksaan kesesuaian bahasa, lingkungan eksekusi, dan hasil benchmark sebelum diputuskan.

### 6.4 Confidence dan fallback

Jangan memakai satu angka “confidence” untuk tiga hal berbeda:

| Nilai/status | Makna |
|---|---|
| Skor OCR | Skor pembacaan teks yang dilaporkan engine, bila tersedia |
| Status pemilihan headline | Kejelasan kandidat judul menurut aturan/selector yang digunakan |
| Skor klasifikasi | Skor prediksi kelas dari model untuk input tersebut |

Angka OCR 90% tidak membuktikan headline terpilih benar. Ambang seperti 0,80 atau 0,50 pada plan sebelumnya adalah contoh, bukan konfigurasi final. Tentukan ambang melalui evaluasi; jangan menyamakan skor antar-engine tanpa pemeriksaan.

Jika headline tidak andal, arahkan pengguna untuk memeriksa/mengoreksi teks. Mode prediksi tanpa teks hanya boleh tersedia jika jalur tersebut memang didukung dan telah dievaluasi; jangan otomatis menghilangkan input teks pada model multimodal.

## 7. Rincian XAI: variasi struktur dengan bukti yang sama jelasnya

### 7.1 Sumber penjelasan

Pertahankan penanda yang sudah terlihat pada demo:

- **MODEL:** prediksi, skor, dan atribusi yang dihitung untuk analisis saat ini.
- **CODEBOOK:** definisi kelas yang ditulis dan diverifikasi peneliti.
- **ANOTATOR:** catatan manusia yang melekat pada sampel dataset.
- **GABUNGAN:** perbandingan/interpretasi yang menghubungkan sumber-sumber tersebut, dengan rujukan komponennya.

Unggahan baru tidak otomatis memiliki label pembanding atau catatan anotator. Region anotasi manusia juga tidak sama dengan region yang berkontribusi pada keputusan model.

### 7.2 Lima strategi narasi

| Strategi | Kondisi penggunaan | Isi utama | Batasan |
|---|---|---|---|
| Bukti teks | Headline final tersedia dan atribusi kata tersedia | Prediksi task, kata pendukung, kata yang melemahkan | Atribusi harus berasal dari task/kelas yang sedang dijelaskan |
| Bukti visual | Atribusi visual tersedia dan dapat dipetakan ke gambar | Region yang memengaruhi prediksi dan keterbatasannya | Jangan menamai objek jika tidak ada bukti identifikasi objek |
| Perbandingan anotasi | Sampel memiliki label/catatan manusia | Kesamaan atau perbedaan prediksi dengan anotasi | Tandai anotasi sebagai catatan manusia |
| Penjelasan kelas | Definisi codebook tersedia | Arti kelas dan kaitannya dengan bukti yang tersedia | Definisi kelas bukan bukti bahwa prediksi benar |
| Bukti gabungan/terbatas | Ada beberapa bukti atau kondisi input bermasalah | Ringkasan teks-visual, ketidaksesuaian, dan langkah pemeriksaan | Jangan menutup kekurangan bukti dengan narasi yang meyakinkan |

Selector memilih strategi berdasarkan task, asal input, ketersediaan anotasi/atribusi, kualitas headline, dan kondisi prediksi. Pemilihan bukan rotasi acak agar kalimat terlihat berbeda.

### 7.3 Struktur minimal setiap explanation

1. **Hasil:** task apa dan kelas apa yang sedang dijelaskan.
2. **Bukti:** teks/region yang benar-benar tersedia untuk hasil itu.
3. **Makna kelas:** definisi singkat dari codebook, jika relevan.
4. **Keterbatasan:** bukti tidak lengkap, headline ambigu, atau prediksi sulit dibedakan.
5. **Tindak lanjut:** periksa headline, bandingkan label dataset, atau tinjau hasil manual.

Jika heatmap paling kuat berada pada logo atau teks, jelaskan temuan tersebut secara terbatas. Jangan menyimpulkan model memahami ilustrasi hanya karena definisi kelas cocok dengan tema sampul.

Pada screenshot, atribusi teks ditampilkan untuk **Domain Sumber Metafora**. Klaim “kata ini mengarahkan model ke isu utama” perlu memakai atribusi Task 1. Audit ini menjadi bagian T08 dan T10.

### 7.4 Contoh narasi terbatas

Contoh struktur, bukan hasil model yang baru dihitung:

> Model memprediksi [kelas] untuk [task]. Pada analisis ini, [kata/region] memberikan kontribusi terhadap prediksi tersebut. Menurut codebook, kelas ini merujuk pada [definisi]. Karena [keterbatasan yang terdeteksi], hasil perlu diperiksa bersama headline final dan bukti yang ditampilkan.

Tidak perlu menambahkan model bahasa untuk menyelesaikan revisi ini. Template berbasis bukti tetap dapat dipakai. Jika model bahasa kelak dipertimbangkan, itu menjadi eksperimen terpisah dengan pemeriksaan asal klaim.

## 8. Evaluasi MTL

### Lingkup awal

- Pertahankan konfigurasi CLIP–IndoBERT saat ini sebagai baseline.
- Bekukan versi preprocessing/OCR untuk perbandingan yang adil.
- Pastikan pembagian train, validation, dan test terdokumentasi serta tidak memiliki sampel yang sama.
- Jika data terlalu kecil untuk split tunggal yang layak, tentukan protokol validasi bersama peneliti sebelum melaporkan performa.
- Catat Macro-F1 per task, hasil per kelas, confusion matrix, dan contoh salah klasifikasi.

Angka performa pada banner screenshot adalah informasi UI yang belum diverifikasi di dokumen ini. Sebelum dipakai untuk menyatakan peningkatan, pastikan angka berasal dari evaluasi pada data yang tidak dipakai melatih model.

| Eksperimen | Yang diubah | Yang dipertahankan | Pertanyaan evaluasi |
|---|---|---|---|
| E00 — baseline | Tidak ada | Konfigurasi saat ini | Bagaimana performa awal pada protokol evaluasi yang ditetapkan? |
| E01 — perbaikan input | Headline/preprocessing OCR | Checkpoint dan split yang sama | Apakah headline yang lebih tepat memperbaiki hasil? |
| E02 — tuning terbatas | Satu variabel training yang dipilih | Data dan pipeline input final | Apakah perubahan memberi manfaat konsisten per task? |

Jangan sekaligus mengganti OCR, backbone, split, dan template penjelasan. Eksperimen harus memungkinkan penyebab perubahan hasil dinilai.

## 9. Kriteria penerimaan dan kasus uji

### Target usulan

| Area | Ukuran | Target awal/usulan |
|---|---|---|
| UI/UX | Pengguna dapat menemukan arti task/kelas | Seluruh task dan kelas memiliki informasi lengkap; tinjau dengan 2–3 pengguna |
| OCR | Headline utama benar setelah normalisasi spasi/kapitalisasi | Sasaran awal ≥80% pada set evaluasi; laporkan jumlah benar/total dan kegagalan per kategori |
| OCR | Kesalahan pemilihan logo sebagai headline | Seluruh contoh regresi yang dikenal diperbaiki; pantau pada set evaluasi |
| XAI | Klaim bisa ditelusuri ke sumber | Seluruh klaim pada kasus uji memiliki sumber yang sesuai |
| XAI | Task/kelas/input konsisten | Tidak ada ketidaksesuaian pada kasus regresi |
| MTL | Evaluasi baseline lengkap | Metrik per task/kelas dengan protokol data yang jelas; target peningkatan ditetapkan setelah baseline |
| Performa | Waktu OCR dan analisis | Catat latensi median dan p95; tentukan batas setelah baseline tersedia |

Ukuran dataset awal digunakan untuk diagnosis dan penerimaan demo. Jangan menganggap hasil 30–50 sampul mewakili seluruh variasi sampul.

### Kasus regresi wajib

1. **Sampul cukai:** `TEMPO5` tidak terpilih sebagai headline utama; judul beberapa baris disatukan dengan benar.
2. **Logo lebih besar:** selector tetap membedakan logo penerbit dari headline.
3. **Koreksi manual:** teks yang diedit pengguna menjadi input model dan ditampilkan identik pada hasil.
4. **Pergantian gambar/task:** hasil sebelumnya dibatalkan atau ditandai usang; atribusi mengikuti task baru.
5. **Unggahan tanpa anotasi:** tidak muncul klaim berbasis anotator atau label pembanding yang tidak tersedia.
6. **Sampel dataset:** prediksi dan anotasi dipisahkan secara jelas, termasuk saat berbeda.
7. **Bukti visual pada logo:** narasi tidak mengklaim ilustrasi menjadi alasan utama.
8. **OCR ambigu/tidak terbaca:** pengguna mendapat langkah pemeriksaan; tidak ada headline yang dikarang.
9. **Prediksi sulit dibedakan:** narasi menyebut keterbatasan berdasarkan aturan yang telah ditentukan.
10. **Beberapa contoh sampul:** narasi berbeda sesuai bukti, tanpa menambahkan fakta atau maksud pembuat sampul yang tidak tersedia.

## 10. Urutan kerja dan estimasi

Estimasi awal **7–10 hari kerja efektif** untuk satu pelaksana yang sudah memahami aplikasi, dengan codebook dan akses kode tersedia. Ini estimasi, bukan tenggat. Eksperimen training yang memerlukan komputasi lama dapat dilanjutkan setelah demo awal siap.

| Tahap | Estimasi | Pekerjaan | Output yang ditinjau |
|---|---|---|---|
| A — konteks dan UI | 1–2 hari | T01–T03 | Definisi, alur UI, serta hasil yang sinkron |
| B — OCR | 2–3 hari | T04–T07 | Baseline, hasil perbandingan, dan headline selector |
| C — XAI | 2 hari | T08–T09 | Bukti terstruktur dan lima strategi narasi |
| D — validasi demo | 1 hari | T10, dokumentasi awal T12 | Kasus regresi dan demo yang siap ditinjau |
| E — MTL | 1–2 hari untuk evaluasi/penyiapan awal | T11, finalisasi T12 | Baseline evaluasi dan catatan eksperimen |

### Pekerjaan pertama

- Inventarisasi codebook, label tiga task, pipeline OCR, dan metode atribusi yang sedang dipakai.
- Reproduksi kasus `TEMPO5` serta ketidaksesuaian task/headline pada screenshot.
- Susun definisi task/kelas dan rancangan pengantar.
- Tandai contoh regresi sebelum mengubah pipeline.

### Gerbang sebelum melanjutkan

- **Sebelum XAI final:** definisi kelas tersedia, input/task sinkron, dan kontrak headline final jelas.
- **Sebelum demo ditinjau:** kasus regresi lulus, asal klaim terlihat, dan input unggahan tidak diberi anotasi palsu.
- **Sebelum menyatakan model meningkat:** protokol evaluasi valid dan perubahan input/model terdokumentasi.

## 11. Keputusan yang perlu ditetapkan saat implementasi

Hal berikut tidak menghalangi penyusunan plan, tetapi perlu diselesaikan sebelum bagian terkait dibangun:

1. Daftar kelas dan definisi resmi dari codebook.
2. Persetujuan label UI alternatif untuk tiga task.
3. Engine OCR yang sedang digunakan dan bentuk outputnya.
4. Metode atribusi visual serta task yang dijelaskan oleh masing-masing hasil atribusi.
5. Kebijakan saat headline tidak tersedia: koreksi wajib atau mode alternatif yang sudah dievaluasi.
6. Protokol split/evaluasi MTL dan sumber angka pada banner.
7. PIC, kapasitas harian, dan tanggal demo yang sebenarnya.

## 12. Checklist selesai

- [x] Tujuan demo dijelaskan di awal.
- [ ] Tiga task dan seluruh kelas memiliki definisi yang terverifikasi.
- [ ] Label UI selaras dengan codebook dan label dataset.
- [x] Gambar, headline final, pilihan task, dan hasil analisis konsisten.
- [ ] Ekstraksi teks dan pemilihan headline dievaluasi terpisah.
- [x] Kasus `TEMPO5` menjadi regresi yang lulus.
- [x] Koreksi manual tersimpan dan dipakai oleh model/XAI.
- [x] Skor OCR, status headline, dan skor klasifikasi dibedakan.
- [x] Strategi narasi mengikuti bukti yang tersedia.
- [x] Klaim MODEL, CODEBOOK, ANOTATOR, dan GABUNGAN dapat ditelusuri.
- [x] Unggahan baru tidak diperlakukan sebagai sampel beranotasi.
- [x] Keterbatasan atribusi dan prediksi ditampilkan secara spesifik.
- [x] Evaluasi baseline MTL menggunakan protokol data yang terdokumentasi.
- [x] Hasil benchmark, kasus gagal, dan catatan demo tersedia.

### Koreksi status checklist — 6 Oktober 2026

Tanda centang di atas adalah status 5 Okt dan tidak diubah. Kolom berikut mencatat keadaan per 6 Okt (malam). Path bukti tanpa awalan folder relatif terhadap `04_hasil_eksperimen/revisi_week3/`. Matriks lengkap: [STATUS_REVISI_20261006.md](STATUS_REVISI_20261006.md).

| Butir checklist (status 5 Okt) | 6 Okt | Bukti |
|---|---|---|
| Tujuan demo dijelaskan di awal (x) | Tetap. Panduan tiga langkah dan tab Panduan (katalog 25 kelas) terender di Chromium desktop/mobile; keterbacaan belum diuji pada pengguna manusia | `guided_ui_verification.json`, `browser_smoke_20261006_audit.json` |
| Definisi tiga task/kelas terverifikasi ( ) | Tetap terbuka dalam arti verifikasi peneliti. Codebook operasional 25 kelas selesai sesuai instruksi user (T01) dan dipakai katalog/narasi, tetapi bukan codebook resmi dan keselarasannya dengan anotasi historis belum dibuktikan | [CODEBOOK_OPERASIONAL.md](CODEBOOK_OPERASIONAL.md) |
| Label UI selaras dengan codebook/dataset ( ) | Label ramah pengguna dan katalog memakai codebook operasional (R2 diterapkan). Persetujuan peneliti atas label UI tidak tercatat di dokumen status | [STATUS_REVISI_20261006.md](STATUS_REVISI_20261006.md) (R2, T01) |
| Gambar, headline final, task dan hasil konsisten (x) | Tetap lulus (T03) dan diperluas: memilih berkas yang sama memicu OCR ulang; gambar baru selalu mengganti judul/teks pendukung; analisis yang dibatalkan di browser ikut dibatalkan di server | `browser_smoke_20261006_unggah.json`, `browser_smoke_20261006_judul.json`, `01_notebook/test_audit_backend.py` |
| Ekstraksi teks dan pemilihan headline dievaluasi terpisah ( ) | Sebagian (T05, jalur riset). Audit 6 Okt menilai judul dan teks pendukung (recall, presisi, urutan kata) pada set dev/uji/validasi/validasi kedua; kebenaran teks pendukung adalah transkripsi anotator berkonvensi campuran; salah baca huruf EasyOCR belum ditangani | [AUDIT_OCR_URUTAN_20261006.md](AUDIT_OCR_URUTAN_20261006.md), `ocr_audit_urutan_20261006.json` |
| Kasus `TEMPO5` lulus (x) | Tetap: foto dosen CUKAI terbaca `CUKAI ABAL-ABAL ROKOK ILEGAL` di server 6 Okt | `server_baseline_20261006.json`, `browser_smoke_20261006_audit.json` |
| Koreksi manual tersimpan dan dipakai (x) | Tetap, dengan perubahan perilaku 6 Okt: suntingan untuk gambar sebelumnya diganti hasil OCR saat gambar baru dipilih; ketikan selama OCR gambar yang sama tetap dilindungi | `browser_smoke_20261006_judul.json`; [plan](plans/2026-10-06-judul-ganti-saat-gambar-baru.md) |
| Strategi narasi mengikuti bukti (x) | Narasi ditulis ulang 6 Okt, tetap tanpa LLM: tab Prediksi berisi ringkasan awam tiga task dan perbandingan anotator; tab Penjelasan hanya membahas task pilihan (Mengapa / Arti kelas / Catatan anotator / Yang perlu dicek) | `01_notebook/test_narasi_ringkasan.py`, `browser_smoke_20261006_narasi.json`; [plan](plans/2026-10-06-narasi-ringkasan-penjelasan.md) |
| Klaim MODEL/CODEBOOK/ANOTATOR/GABUNGAN dapat ditelusuri (x) | Diperketat 6 Okt: catatan anotator hanya dipakai untuk task pemiliknya | `01_notebook/test_week3_regressions.py`, `01_notebook/test_narasi_ringkasan.py`; [plan](plans/2026-10-06-audit-bug-kode.md) |
| Keterbatasan atribusi dan prediksi spesifik (x) | Tetap; peta datar tidak lagi diklaim punya zona dominan. R4: dengan teks pendukung hasil OCR, ketiga kata GULA-GULA bernilai negatif pada smoke browser, dan tab Penjelasan menyatakannya terbuka | [STATUS_REVISI_20261006.md](STATUS_REVISI_20261006.md) (R4), `browser_smoke_20261006_audit.json` |
| Evaluasi baseline MTL terdokumentasi (x) | Tetap. Full fine-tuning Kaggle selesai, tetapi Task 2 turun 0,3197 → 0,2461 sehingga demo tetap baseline; checkpoint belum diintegrasikan; E01/E02 belum dilaporkan | [HASIL_FULL_TRAINING_KAGGLE.md](HASIL_FULL_TRAINING_KAGGLE.md) |
| Hasil benchmark, kasus gagal, catatan demo (x) | Paket `TEMPO_XAI_DELIVERY_WEEK3_20261006.zip` dibangun dan diuji dari instalasi bersih di Linux; instalasi bersih Windows belum diuji | `browser_smoke_paket_bersih.json`; [plan](plans/2026-10-06-paket-delivery-final.md) |

Butir lain (skor dibedakan, unggahan tidak diperlakukan sebagai sampel beranotasi) tidak berubah statusnya.

**Deliverable implementasi:** revisi UI, katalog kelas, dataset evaluasi OCR, tabel benchmark, perbaikan headline selector, strategi XAI berbasis bukti, laporan kasus regresi, dan catatan evaluasi MTL. Plan ini menjadi acuan pengerjaan; tidak menyatakan bahwa perubahan aplikasi tersebut sudah dilakukan.


## Pembaruan pelaksanaan 2026-10-05

User menetapkan codebook resmi tidak tersedia dan meminta definisi disusun: codebook operasional 25 kelas sudah terintegrasi, tetapi keselarasan dengan anotasi lama belum diverifikasi peneliti. User meminta tinjauan sub-agent: tiga evaluasi agen selesai dan dilaporkan sebagai simulasi, bukan pengguna manusia. Gambar asli dosen tersedia; dua dari tiga headline OCR tepat.

Windows dan tiga task model nyata lulus, regresi Python/JavaScript lulus. Pemilihan headline dan pembanding decoding sudah diuji; ekstraksi teks lengkap belum memiliki ground truth mandiri yang disahkan. Target OCR 80% belum tercapai, usulan visual tersedia untuk 11 kasus gagal. Full training Kaggle serta audit selesai; demo mempertahankan baseline karena Task 2 fine-tuning menurun. Batch 740 lulus untuk penutupan skala, bukan benchmark akurasi. Detail/bukti/status akhirnya ada di [delivery](DELIVERY_WEEK_3.md).

## Pembaruan 6 Oktober 2026

Paragraf 5 Okt di atas tidak diubah. Koreksi dan tambahan per 6 Okt (malam), dengan bukti di [STATUS_REVISI_20261006.md](STATUS_REVISI_20261006.md):

- **Status keseluruhan:** paket delivery revisi Week 3 dengan model baseline (`TEMPO_XAI_DELIVERY_WEEK3_20261006.zip`), diuji dari instalasi bersih di Linux. Ini bukan pernyataan bahwa semua sasaran tercapai.
- **"Windows ... lulus" pada paragraf 5 Okt** merujuk uji backend di folder Windows terisolasi (`windows_verification.json`), bukan UI terbaru atau instalasi bersih paket delivery. Instalasi bersih Windows belum diuji.
- **R5 ditutup 6 Okt:** peta utama tab Bukti gambar adalah peta gabungan tiga task, diikuti blok "Bukti task pilihan" (`01_notebook/test_r5_heatmap.js`, `r5_heatmap_verification.json`; [plan](plans/2026-10-06-r5-peta-gabungan-dan-changelog.md)).
- **OCR (bagian 6 dan 9):** teks pendukung disusun menurut tata letak dan sampah teks baku dibuang ([AUDIT_OCR_URUTAN_20261006.md](AUDIT_OCR_URUTAN_20261006.md)). Judul tepat 68–78% pada dua set validasi audit OCR 6 Okt untuk versi aplikasi terakhir (cenderung optimistis; 63–72% saat kode dibekukan); sasaran usulan ≥80% belum tercapai, jadi koreksi manual tetap wajib.
- **Audit kode frontend/backend:** celah XSS ditutup, batas masukan ditambahkan, analisis yang dibatalkan ikut dibatalkan di server, dan status batch `failed` muncul bila semua item gagal ([plan](plans/2026-10-06-audit-bug-kode.md)).
- **Masih terbuka:** instalasi bersih Windows, browser selain Chromium, uji pengguna manusia, sasaran OCR 80%, E01/E02, integrasi checkpoint Kaggle, dan autentikasi server (lihat "Masih terbuka" di dokumen status).
