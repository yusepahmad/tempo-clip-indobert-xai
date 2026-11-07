# Plan Pengerjaan Revisi II Notebook Joy

**Tanggal:** 2026-11-01
**Status:** in-progress

## Tujuan
Menuntaskan 19 revisi baru R18–R36 dan sembilan butir Agustus R2/R4/R6/R8/R9/R12/R13/R16/R17 melalui audit bukti, koreksi evaluasi, eksperimen terkontrol yang diperlukan, evaluasi XAI, serta delivery yang dapat direproduksi. Model utama tetap keluarga CLIP–IndoBERT dengan shared MTL layer, tiga head dan Joint Loss; Qwen3-VL QLoRA berperan sebagai pembanding.

Plan ini disusun berdasarkan PDF `revision/Daftar-Revisi-II-Pemeriksaan-Notebook-Joy.pdf` dan pemeriksaan awal source lokal. Pelaksanaan diotorisasi pengguna pada 1 November 2026: kerjakan seluruh revisi dan siapkan delivery untuk diteruskan ke Joy. Jadwal di bawah adalah milestone sumber; pekerjaan lokal yang sudah dapat dijalankan dilaksanakan sekarang tanpa menunggu tanggal milestone.

## Ruang Lingkup

### Perubahan pada task penyusunan plan ini
- File plan ini.
- `CHANGELOG.md`: pencatatan penambahan plan setelah file selesai dibuat.

### File/modul yang direncanakan pada pelaksanaan
- `docs/revisi-ii/`: pelacakan 28 butir, keputusan model/metrik, provenance, anotasi, hasil audit, tanggapan kepada pembimbing dan bukti pengujian. Direktori ini belum dibuat pada task penyusunan plan.
- `DEMO_XAI_745_FULL/01_notebook/revisi_ii/`: skrip evaluasi, kontrak prediksi, pengujian dan worker eksperimen baru berversi. Hindari menimpa worker historis berhash.
- `DEMO_XAI_745_FULL/04_hasil_eksperimen/revisi_ii/`: tabel turunan, prediksi baru, CI, analisis kesalahan, konfigurasi, log dan manifest.
- `DEMO_XAI_745_FULL/01_notebook/next_research_20261017/kaggle_micro_e14/results.py`: diaudit sebagai sumber pelaporan lama; evaluator baru ditempatkan di jalur revisi. Bila kompatibilitas membutuhkan perubahan file ini, buat subplan spesifik dan jaga hasil/kontrak hash historis.
- `DEMO_XAI_745_FULL/02_web_demo/`: audit `xai_core.py`, `mtl_engine.py`, `explanation_evidence.py`, `app.py`, dan `index.html`; perubahan hanya yang diperlukan untuk kesesuaian identitas model/metode dan hasil yang benar-benar diuji.
- `DEMO_XAI_745_FULL/06_models/`: manifest/model baru hanya jika refit dan promosi runtime memang diperlukan setelah model utama ditetapkan. Model CV bukan otomatis model deployment.
- Tiga notebook revisi `01_baseline.ipynb`, `02_experiments.ipynb`, `03_final_comparison.ipynb` dalam folder kerja baru; sumber awal ditetapkan pada tahap A. Salinan di delivery lama tidak diedit.
- `docs/CANONICAL_SOURCE.md`, `docs/DELIVERY_MAIN_MODEL.md`, `docs/WORKSPACE_INDEX.md` dan dokumentasi aktif terkait diselaraskan setelah keputusan final, sambil mempertahankan konteks tanggal historis.
- `delivery/revisi_ii_<tanggal-build>/`: arsip revisi baru beserta bukti reproduksi dan checksum; direktori final mengikuti tanggal build nyata.
- `docs/plans/` dan `CHANGELOG.md`: subplan per paket kerja dan catatan perubahan aktual.

### Yang eksplisit tidak disentuh
- PDF sumber, ZIP/snapshot historis, output/prediksi/source eksperimen terkunci, serta checkpoint lama.
- Label gold, ID dan fold canonical tidak diubah diam-diam. Perubahan codebook/dataset harus berupa versi baru dengan alasan, pemetaan, dan hasil sensitivitas terpisah.
- Tidak menghapus cache, environment, gambar, atau job; tidak mengirim pesan ke pembimbing/penilai atau mengunggah/publikasi paket pada task perencanaan ini.
- Tidak menjadikan seluruh 28 nomor sebagai 28 eksperimen atau mengulang training tanpa pemeriksaan bukti.

## Langkah

### A. Audit bukti dan siapkan pelacakan — target 1–2 November
1. Buat tracker 28 baris, satu per nomor revisi. Kolom: ID, permintaan, tahap, dependensi, pemilik, tenggat asli, target kerja, status, lokasi bukti, hasil verifikasi dan kekurangan.
2. Status mengikuti dokumen: Belum/Berjalan/Selesai/Dibantah. Bukti yang ditemukan tidak otomatis berarti Selesai; Dibantah memerlukan penjelasan teknis dan bukti untuk dibahas, bukan penutupan sepihak.
3. Identifikasi versi notebook yang dikirim tanggal 20/27 Oktober serta arsip yang benar-benar diterima dosen. Catat bila bukti pengiriman tidak tersedia; jangan mengasumsikan ZIP lokal lengkap sudah diterima.
4. Inventaris source/result/OOF/checkpoint/split/protokol/hash untuk 36 baris kandidat di lampiran. Lacak alias seperti M00/E42: pertahankan tabel 36 baris untuk menanggapi PDF, tetapi bedakan jumlah nama dari jumlah konfigurasi/prediksi unik.
5. Audit generator `deskripsi.jsonl`/`zeroshot.jsonl`, prompt lengkap, model/revisi, input proses, waktu, hash dan 20 contoh dengan seed yang dicatat. Bedakan fitur yang mendeskripsikan konsep target dari bukti akses label gold; kesimpulan kebocoran harus berdasarkan alur data.
6. Temukan korpus awal dan anotasi mentah kedua anotator. Rekonstruksi jumlah 1.040→740 per alasan/ID bila memungkinkan; tandai angka yang belum terbukti, tanpa membuat riwayat atau kappa buatan.
7. Mulai kebutuhan manusia sejak awal: siapkan paket anotasi ganda dan calon penilai XAI, tanpa menghubungi siapa pun secara otomatis. Bila anotasi lengkap tidak tersedia, siapkan sampel acak minimal 150 sampul dengan codebook dan seed sebelum anotasi.

Keluaran: `revision_tracker`, `artifact_inventory`, `candidate_mapping`, `feature_provenance`, `corpus_history`, daftar bukti yang belum ditemukan, dan rancangan paket anotasi. Format awal Markdown/JSON/CSV sesuai kebutuhan; bila menghasilkan workbook, gunakan skill spreadsheet pada saat pelaksanaan.

### B. Hitung ulang metrik dan diagnosis — target sampai 3 November
1. Normalisasi pembacaan prediksi tanpa mengubah berkas asli. Kontrak minimum: experiment_id, sample_id, fold, truth/prediction per task, sumber dan SHA-256. Periksa keunikan ID, jumlah OOF, label, fold dan cakupan kelas tetap.
2. Hitung Macro-F1, macro-precision, macro-recall, akurasi dan Cohen kappa setiap task. Micro-F1 historis boleh dipertahankan sebagai alias yang dijelaskan identik dengan akurasi untuk tugas single-label ini.
3. Buat dua tabel: reproduksi peringkat minimum micro/macro dalam PDF untuk audit, dan keputusan model berdasarkan metrik per task serta rerata Macro-F1 berbobot sama yang dinyatakan eksplisit. Minimum tetap diagnostik dan bukan satu-satunya kriteria.
4. Audit ulang korelasi/pergeseran peringkat, ties, alias dan kesimpulan E11/E12. Laporkan bila angka berbeda dari PDF beserta sumbernya; jangan mengubah angka untuk mencocokkan PDF.
5. Untuk model utama sementara dan E11, hasilkan confusion matrix Task 3, distribusi gold/prediksi, recall per kelas dan entropi. Bangun majority baseline dari label training masing-masing fold; baseline berbasis mayoritas seluruh korpus hanya sebagai referensi historis yang diberi konteks.
6. Audit class weighting yang sebenarnya dipakai. Bandingkan weighted/unweighted hanya bila kontrak yang membedakannya sudah jelas; jangan mengasumsikan model lama belum memakai bobot.

Keluaran: tabel kandidat/metrik/peringkat, rekonstruksi klaim pemeriksa, confusion matrix angka+gambar, distribusi/entropi dan memo diagnosis. Bagian R20 yang membutuhkan training dilanjutkan di tahap D, tidak diklaim selesai hanya dari diagnosis.

### C. Tetapkan model utama dan tutup fondasi P1 — target sampai 9 November
1. Saring kandidat yang benar-benar memenuhi CLIP + IndoBERT + shared layer + tiga head + Joint Loss. Catat backbone/varian, dimensi/fitur, status frozen/fine-tuned, optimizer/loss/weighting, input dan augmentasi aktual dari source.
2. Berdasarkan hasil tahap B, bekukan satu identitas model utama beserta alasan, resep dan protokol. Nyatakan seleksi post-hoc pada korpus berulang dan bedakan dari model web yang sedang aktif. Tidak otomatis menganggap E42 layak hanya karena peringkatnya tinggi.
3. Catat keputusan metrik: Macro-F1 utama; akurasi/kappa/precision/recall pendamping; gate absolut 0,70 dihapus dari keputusan revisi. Target proposal historis dan ketidaktercapaiannya tetap diungkapkan; arsip lama tidak ditulis ulang.
4. Susun kontrak 2×2: arsitektur CLIP–IndoBERT/Qwen × input dasar/kaya. Daftar field input harus eksplisit dan sama dalam perbandingan terkait. Tambahkan kontrol Qwen zero-shot dengan input identik untuk memisahkan efek fine-tuning.
5. Siapkan subplan eksperimen wajib P1 (R20/R21) setelah model/metrik/provenance dibekukan: weighted/unweighted, Qwen input dasar, CLIP input kaya, zero-shot 740 ID. Jangan menyebut zero-shot sebagai hasil training CV; evaluasinya menggunakan ID evaluasi yang sama.
6. Jalankan eksperimen P1 yang diperlukan setelah fondasi lolos, simpan seluruh OOF/audit. Bila waktu GPU tidak mencukupi, catat bagian P1 yang masih terbuka dan reforecast tanggal; jangan menandai R21 lengkap dari desain tabel saja.
7. Hitung kappa antaranotator dari label independen sebelum adjudikasi, per task dan ID yang sama. Kalau perlu anotasi baru, minimal 150 sampul, dengan proses independen dan adjudikasi terdokumentasi. Tabel model-versus-manusia memakai cakupan sampel yang dijelaskan; tidak menyebut agreement manusia sebagai batas atas matematis model.

Gerbang G1, 9 November: identitas dan metrik beku, ranking/provenance terverifikasi, riwayat korpus terdokumentasi, anotasi ganda minimal berjalan. Tracker tetap membedakan syarat gerbang PDF dari penyelesaian penuh R20/R21/R23; pekerjaan yang belum selesai tetap terbuka.

### D. Lengkapi statistik dan ablasi terkontrol — target 10–16 November
1. Hitung CI Wilson 95% untuk akurasi dan CI bootstrap Macro-F1 minimal 2.000 resampling dengan seed tersimpan. Untuk selisih Macro-F1 gunakan resampling berpasangan pada ID yang sama. Catat bahwa CI OOF adalah ketidakpastian atas prediksi tersimpan, bukan seluruh variasi seleksi/training.
2. McNemar memakai pasangan benar/salah per ID untuk perbedaan akurasi; jangan menjadikannya uji langsung perbedaan Macro-F1. Simpan b/c, metode, pasangan dan p; tetapkan keluarga perbandingan/koreksi multipel sebelum membaca hasil baru. Tidak signifikan tidak otomatis membuktikan kesetaraan.
3. Buka E48/E49/J01 beserta metrik per kelas. E48 yang diperiksa awal memakai LinearSVC dengan pencarian fitur/normalisasi/C, sehingga bukan otomatis ablasi neural single-task murni dari model MTL utama.
4. Bila parity tidak terpenuhi, buat tiga model single-task dengan backbone, fitur, split, seed, augmentasi, anggaran tuning dan training yang setara; perubahan yang disengaja hanya mekanisme berbagi tugas. Simpan konfigurasi dan alasan setiap perbedaan yang tidak dapat dihindari.
5. Lengkapi majority/image-only/text-only/text-only judul+supporting dan multimodal acuan. Gunakan checkpoint/OOF yang valid bila ada; bila tidak, training ulang terbatas pada konfigurasi yang hilang, tanpa mengarang prediksi historis.
6. Buktikan Joint Loss aktual: bobot tetap/class weights versus learned uncertainty, log parameter bila ada; naskah/sitasi mengikuti implementasi, bukan mengubah implementasi hanya agar sesuai klaim lama.
7. Tutup R20 weighted/unweighted dan R21 input parity bila belum selesai. Semua pembobotan/sampling/seleksi hanya di training/inner fold; outer-test tidak dipakai untuk memilih epoch atau parameter.
8. Nyatakan jumlah konfigurasi unik dan bias seleksi. Tidak menyebut fold yang pernah dilihat sebagai holdout baru. Validasi eksternal kecil adalah opsi tambahan jika data/hak akses/anotasi tersedia, bukan syarat tersembunyi seluruh plan.

Keluaran: tabel metrik+CI, pasangan perbandingan/uji, OOF setiap konfigurasi, tabel ablasi MTL/unimodal, audit loss dan pernyataan bias seleksi.

### E. Audit backbone, augmentasi, label dan reproduksi awal — target 17–23 November
1. Buka M01–M04 per task dan audit kesetaraan eksperimen. Bandingkan backbone hanya dengan menyatakan perubahan lain yang ada. Jalankan ulang hanya bila dibutuhkan untuk klaim terisolasi.
2. Buka A00–A03 dan AUG_SELECTED, parameter transformasi dan pemilihan inner. Pipeline yang dipilih di inner boleh kalah dari satu konfigurasi pada outer; jangan mengganti pemenang berdasarkan outer-test. Jika transformasi melanggar kontrak semiotika, perbaiki dalam eksperimen baru berversi.
3. Audit 30 hasil back-translation bila metode tersebut benar-benar digunakan. Bila tidak digunakan, lampirkan bukti ketidakberlakuannya dan tanggapan untuk pembimbing; jangan membuat contoh seolah hasil pipeline yang pernah dijalankan.
4. Audit 30 LAINNYA + 30 multiple_or_other dengan anotator. Laporkan metrik per kelas, Macro-F1 lengkap dan sensitivitas tanpa kelas penampung dengan definisi perhitungan eksplisit; jangan diam-diam menghapus sampel/kelas.
5. Pecah evaluasi Task 2 menjadi deteksi metafora dan klasifikasi domain pada sampel gold bermetafora; nyatakan aturan prediksi NON_METAFORA. Pemecahan head/label adalah eksperimen opsional versi baru, bukan syarat agar tabel evaluasi dapat dibuat.
6. Buat paket reproduksi versi awal dari sumber kerja baru, berisi notebook, evaluator, dataset/fitur yang boleh didistribusikan, prediksi, split, result, requirements versi persis, README dan manifest.
7. Sediakan mode baca output tersimpan dan mode analisis dari awal. Mode analisis harus Run all tanpa memperbaiki path manual, akses notebook lain, Drive pribadi, atau training tersembunyi. Upload/ekstraksi paket sebagai langkah setup dijelaskan.
8. Uji lingkungan bersih lokal dan Colab baru; simpan log/versi/tangkapan layar. Jika akses Colab belum tersedia, tandai uji Colab Belum/Not Evaluated dan jangan menutup R32.

Gerbang G2, 23 November: statistik dan ablasi yang mendukung klaim tersedia, paket reproduksi diuji. Jika sumber daya tidak cukup, dokumentasikan pengurangan klaim/backbone/augmentasi kepada pembimbing; butir tidak otomatis dianggap selesai.

### F. XAI dan penilaian manusia — persiapan sejak 2 November; selesai paling lambat 7 Desember
1. Audit `xai_core.py`, checkpoint/model yang benar-benar dijelaskan, varian CLIP dan metode atribusi. Jangan menyimpulkan implementasi tidak ada hanya karena tidak muncul di notebook, atau menyebut peta gradien sebagai bukti faithfulness tanpa uji.
2. Verifikasi pilihan metode visual untuk backbone melalui paper/dokumentasi primer sebelum implementasi. Pertahankan atau ganti metode berdasarkan bukti; jangan mengganti backbone/model utama semata-mata untuk memudahkan XAI.
3. Pastikan LIME menjelaskan head/kelas yang sama dengan prediksi model utama, dengan citra tetap dan perturbasi teks yang didokumentasikan. Jika model utama berubah dari runtime aktif, buat uji kesetaraan dan refit deployment terpisah; hasil CV tidak diklaim sebagai hasil inferensi refit.
4. Siapkan rubrik tertulis sebelum skor dinilai: interpretability manusia dan pengujian faithfulness berbasis perilaku model dilaporkan sebagai bukti yang berbeda. Sertakan kontrol peta acak, protokol penilai dan minimal lima penilai independen dari anotasi.
5. Pengguna/peneliti mengatur perekrutan, persetujuan dan penilaian; siapkan paket penilaian teracak, tanpa memperlihatkan identitas kontrol. Simpan skor asli. Tidak menghubungi orang lain atau mengisi skor sebagai agen.
6. Hitung Krippendorff Alpha atau ICC sesuai skala/desain yang dipilih dan diverifikasi sumber primer, selain ringkasan skor. Laporkan hasil aktual termasuk bila kontrol dinilai tinggi.
7. Integrasikan metode, contoh dan evaluasi ke notebook. Jika 7 Desember belum terpenuhi, siapkan opsi amendemen lingkup untuk keputusan bersama pembimbing, tanpa menghapus XAI dari judul secara sepihak.

Gerbang G3, 7 Desember: XAI model utama tervalidasi, rubrik/kontrol/skor lima penilai dan agreement tersedia, atau keputusan amendemen resmi dicatat.

### G. Naskah, tanggapan revisi dan delivery akhir — target 8–24 Desember
1. Tulis hasil sesuai model utama final dan bukti aktual, termasuk hasil negatif/trade-off. Jangan mengunci kesimpulan baseline lama atau menyebut Qwen sebagai batas atas yang setara bila input/protokol belum setara.
2. Nyatakan kontribusi, bias seleksi, korpus satu penerbit, interpretasi label, sejarah penyusutan, resolusi gambar, urutan opsi, stratifikasi dan reuse pilot sesuai hasil audit. Pernyataan yang dibantah dilengkapi alasan/sumber.
3. Lengkapi sitasi dari sumber primer dengan DOI/tahun/halaman terverifikasi; sertakan etika, potensi penyalahgunaan dan batas distribusi data/model sesuai keputusan pemilik data.
4. Sinkronkan tiga notebook, tabel, grafik, model manifest/runtime dan README; angka tampil dibulatkan sewajarnya tetapi nilai mentah presisi penuh tetap disimpan untuk verifikasi.
5. Buat tanggapan 28 baris kepada pembimbing: permintaan, tindakan, temuan/bantahan, file/sel bukti, tes dan status. Nomor lama merujuk bukti baru yang sama agar tidak dihitung sebagai pekerjaan berulang.
6. Bangun delivery final berversi baru; verifikasi CRC, checksum arsip, manifest seluruh file dan Run all dari ekstraksi. Catat platform yang benar-benar diuji dan yang belum.
7. Siapkan paket untuk diperiksa pengguna. Pengiriman kepada pembimbing, unggah publik, submit jurnal dan perubahan lingkup resmi dilakukan hanya jika diminta secara eksplisit.

## Pemetaan Seluruh 28 Butir

| ID | Tahap utama | Bukti penutupan |
| --- | --- | --- |
| R18 | A–C | Pemetaan kandidat + identitas/model/protokol beku + pengungkapan seleksi. |
| R19 | B | Metrik dari prediksi, dua tabel peringkat, korelasi dan analisis perubahan kesimpulan. |
| R20 | B–D | Confusion matrix/distribusi/entropi dan hasil weighted/unweighted yang setara. |
| R21 | C–D | Tabel input/arsitektur 2×2 + kontrol zero-shot + OOF/CI/kappa. |
| R22 | A–C | Generator/prompt/model/input/hash/20 contoh dan keputusan provenance berbukti. |
| R23 | A/C | Anotasi independen/kappa, riwayat korpus dan sensitivitas bila sumber tersedia. |
| R24 | B–D | Evaluator dan tabel baru Macro-F1 utama; metrik per kelas dan akurasi/kappa. |
| R25 | D | CI/bootstrap/uji berpasangan dan klaim selisih yang sesuai ukuran ketidakpastian. |
| R26 | A/D/G | Jumlah konfigurasi unik + pengungkapan bias, validasi eksternal bila dilakukan. |
| R27 | D | Parity single-task/MTL, metrik/CI/prediksi dan Joint Loss aktual. |
| R28 | D | Prediksi seluruh konfigurasi baseline/unimodal dan perbandingan berpasangan. |
| R29 | E | M01–M04 per task + audit parity + identitas backbone. |
| R30 | E | Parameter augmentasi, alasan inner selection dan audit contoh/metode yang berlaku. |
| R31 | E | Audit 60 sampul, sensitivitas kelas penampung dan evaluasi Task 2 terpisah. |
| R32 | E/G | Paket lengkap, environment terkunci dan bukti Run all bersih termasuk Colab. |
| R33 | G | Narasi hasil/kontribusi/temuan negatif konsisten model terpilih dan statistik. |
| R34 | F | Metode XAI, faithfulness/rubrik/kontrol/lima penilai/agreement atau amendemen resmi. |
| R35 | C/G | Gate 0,70 tidak dipakai dalam keputusan baru; kriteria komparatif dan target historis jelas. |
| R36 | G | Keterbatasan/etika/batas distribusi/sitasi primer terverifikasi. |
| R2 | A/E | Codebook operasional, kelas penampung dan contoh keputusan/adjudikasi. |
| R4 | F | Audit kelayakan metode visual pada varian CLIP utama dengan sumber primer dan uji. |
| R6 | A/C | Jejak penyusutan/adjudikasi, alasan per ID dan sensitivitas yang dapat dibuktikan. |
| R8 | D/E | Matriks baseline/ablasi sesuai dokumen Agustus + prediksi dan statistik; cek rincian PDF Agustus sebelum menutup. |
| R9 | A/F | Rubrik/protokol dan skor asli minimal lima penilai independen beserta agreement. |
| R12 | B/C/D | Macro-F1 utama dalam seleksi dan pelaporan baru. |
| R13 | C/G | Justifikasi kriteria komparatif, pelepasan gate absolut dan pelaporan target proposal. |
| R16 | G | Referensi relevan dengan implementasi dan metadata terverifikasi. |
| R17 | G | Bagian etika dan penyalahgunaan dengan batas pemakaian/distribusi yang disepakati. |

Sembilan butir Agustus di atas bersumber dari tabel Revisi II. Sebelum menutupnya, baca wording dokumen Agustus asli agar rincian yang tidak dikutip di Revisi II tidak terlewat.

## Risiko & Asumsi

- Tenggat R18/R22 tanggal 31 Oktober sudah lewat pada tanggal plan. Target pemulihan audit awal 1–2 November dicatat terpisah; jangan mengganti tenggat asli atau mengklaim pekerjaan terlambat tanpa memeriksa bukti yang ada.
- Jadwal adalah target bergantung pada jumlah rerun yang benar-benar diperlukan, GPU/kuota, ketersediaan checkpoint dan proses manusia. Tidak menjanjikan durasi training sebelum smoke/estimasi sumber daya nyata.
- Jika provenance belum dapat dibuktikan, tandai bukti tidak cukup dan pisahkan klaim yang bergantung padanya. Jika akses gold benar-benar terbukti, karantina hasil terkait, buat subplan remediasi dan laporkan dampaknya; jangan membatalkan seluruh Task 2 atau mengubah lingkup penelitian tanpa menilai sumber kontaminasi dan keputusan pembimbing.
- Klaim/statistik dalam PDF merupakan hipotesis audit sampai dihitung ulang. P-value/CI/peringkat dan usulan metode tidak disalin sebagai hasil terverifikasi.
- Model/fitur/split yang tidak sama tidak diberi label ablasi murni; hasil selection-inner yang lebih rendah di outer tidak diperbaiki dengan memilih ulang pada outer.
- Root workspace tidak memiliki metadata Git yang dapat dibaca pada pemeriksaan sebelumnya. Gunakan inventaris SHA-256/snapshot terpilih sebelum edit; jangan menjalankan inisialisasi repository atau menyalin seluruh workspace tanpa kebutuhan.
- Data anotasi ganda, korpus yang dikeluarkan, versi notebook 27 Oktober dan bukti kirim mungkin belum ditemukan. Catat kebutuhan spesifik setelah pencarian, lanjutkan pekerjaan independen, dan jangan membuat bukti pengganti.
- Perubahan identitas model utama tidak otomatis mengubah runtime web. Promosi membutuhkan checkpoint/refit, manifest, parity inference dan XAI yang teruji, serta keputusan yang terdokumentasi.
- Pengguna/peneliti menyediakan anotator dan minimal lima penilai independen, menjalankan interaksi akun bila akses otomatis tidak tersedia, dan menyepakati keputusan lingkup/distribusi dengan pembimbing.
- Kebutuhan hak cipta/data ditangani dalam isi paket dan README yang relevan; tanpa asumsi bahwa arsip boleh dipublikasikan.

## Verifikasi

1. Tracker memuat tepat 28 ID unik: R18–R36 dan R2/R4/R6/R8/R9/R12/R13/R16/R17; setiap status Selesai memiliki bukti file/sel dan pemeriksaan yang bisa diulang.
2. Evaluator diuji dengan fixture ketimpangan kelas, kelas tidak diprediksi, pasangan ID teracak, duplikasi/hilang ID, alias kandidat, serta split/truth mismatch. Perhitungan inti dibandingkan ke implementasi/library independen dengan toleransi tercatat.
3. Setiap eksperimen baru menyimpan OOF, konfigurasi, seed, epoch/seleksi inner, input/source/data hash dan log; gold dan outer-test tidak ikut pemilihan model atau pembobotan training.
4. Statistik memakai pasangan/cakupan sampel yang benar dan tidak menyamakan uji akurasi dengan uji Macro-F1 atau tidak-signifikan dengan bukti setara.
5. Tidak ada angka Not Evaluated yang diisi estimasi; missing evidence, deadline bergeser dan bantahan tetap terlihat.
6. Notebook hasil revisi memakai sumber tabel yang sama, tidak memuat error tersimpan, dan lulus Run all setelah setup di lingkungan bersih. Bukti Colab/Windows hanya diklaim jika benar-benar dijalankan.
7. Identitas model utama, hasil CV, model deployment dan metode XAI dapat ditelusuri; peta/atribusi berasal dari model/head/input yang dijelaskan.
8. Delivery baru lulus SHA-256/CRC/manifest dan verifikasi dari ekstraksi; ZIP historis tidak diubah. Changelog hanya mencatat perubahan yang sudah diterapkan.

## Prioritas Saat Pelaksanaan Dimulai
1. Buat tracker dan inventaris kandidat/OOF serta provenance.
2. Hitung ulang Macro-F1/peringkat dan diagnosis Task 3 tanpa training.
3. Tetapkan model/protokol dan kebutuhan eksperimen sesungguhnya; mulai proses anotasi/penilai sejak awal.
4. Lanjutkan gerbang G1→G2→G3, lalu naskah dan delivery.

## Log Pelaksanaan

- 1 November 2026: mulai audit source/OOF/provenance dan siapkan evaluator serta delivery baru. Data manusia yang belum tersedia diminta lokasi filenya; pekerjaan independen terus berjalan. Paket tidak akan diberi klaim semua revisi selesai jika bukti anotator/penilai/runtime masih belum ada.
- Audit awal selesai: tidak ditemukan dua anotator/1.040record/lima penilai pada507headerCSV dan18ZIP. Generator E01/hash/prompt ditemukan; tes AST740baris hanya membaca headline/supporting, tetapi proses historis tetap memuat CSV berlabel. E42 dipilih post-hoc berdasarkan meanMacro-F1 kandidat proposal. Baseline direplay identik740×3; controlled rerun frozen/backbone, lima arm tail GPU dan augmentasi tanpa rotasi selesai. XAI delapan outer-test sampel lulus parity dengan hasil deletion campuran. KandidatB01 memuat73sumber/219baris metrik; tiga notebook dan validatorCounter lulus di environment terpisah dari ekstraksi. R21input/Qwen dan izin QAColab masih berjalan. Instrumen manusia siap, tanpa skor buatan. Detail lanjutan: subplan `2026-11-01-revisi-ii-evaluasi-delivery.md`.

- 2 November 2026: atas instruksi pengguna, hasil yang dapat diselesaikan sekarang dihimpun pada `delivery/HASIL_REVISI_JOY_20261102/`. Identitas/JointLoss R18 ditulis langsung pada tiga notebook, screenshot historis dan aktual disertakan. Zero-shot Qwen740 basic/rich sudah terverifikasi.19tes dan Runall tiga notebook dari ZIP pada venv terpisah lulus. Status tetap19selesai teknis/9terbuka; QLoRA basic full, manusia, sumber historis dan Colab belum diklaim selesai. Lihat plan `2026-11-02-revisi-langsung-notebook-dan-screenshot.md`.

- 2 November 2026: bukti disusun per19butir selesai dalam folder R18/R19/dst pada delivery R2 dan ZIP bukti ringan.139berkas,15subset CSV dan226tautan diperiksa; core186file sama dengan R1. Status global tetap19/28selesai teknis,9terbuka. Plan pengemasan: `2026-11-02-folder-bukti-per-revisi.md`.
