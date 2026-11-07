# Paket Final Notebook Colab, Benchmark dan Web Terbaru

**Tanggal:** 2026-10-20
**Status:** done

## Tujuan
Membuat satu ZIP final untuk presentasi dan audit eksperimen: notebook Colab
dengan output angka/grafik tersimpan, benchmark aktual, dokumentasi perubahan
19 Oktober 2026, seluruh source/notebook/hasil eksperimen lokal dan web terbaru.

## Ruang Lingkup
- Builder/validator dan materi baru pada `delivery/experiment_final_20261020/`.
- Tiga notebook presentasi baru, CSV benchmark, grafik PNG/SVG, dokumentasi,
  manifest dan satu ZIP dengan top folder `experiment_final/`.
- Salinan source/data/hasil historis project dengan path relatif dipertahankan;
  seluruh notebook `.ipynb` asli disalin byte-identik, tidak ditimpa.
- Web terbaru CLIP–IndoBERT dan launcher Windows/Linux tetap disertakan.
- Plan ini, ringkasan dokumentasi dan entry changelog setelah implementasi.
- Tidak mengubah model aplikasi, dataset/label, job Kaggle, protokol training,
  hasil sumber maupun paket delivery lama. Tidak menjalankan training ulang.

## Langkah
1. Audit inventaris notebook/source/hasil, schema prediksi dan log. Bandingkan
   snapshot delivery 17/19 Oktober untuk before/after bila tersedia; tandai
   perubahan yang hanya didukung plan/log, bukan diff notebook yang terverifikasi.
2. Kumpulkan benchmark long-format dari JSON/CSV/log aktual dengan provenance.
   Hitung ulang accuracy, macro precision/recall/F1 dari prediksi yang tersedia;
   pisahkan 740 OOF, 119 pilot, 24 smoke, historical dan belum dievaluasi.
3. Buat perbandingan E11/E12/E14 OOF dan kontrol/E13 pada validation yang sama,
   delta poin persentase dan persen relatif; runtime hanya dari field/log yang
   jelas. CPU/RAM/GPU utilisation yang tidak direkam diberi Not Evaluated.
4. Buat tiga notebook presentasi sesuai delapan bagian yang diminta, dengan
   kode implementasi/reproduksi dan output tersimpan melalui eksekusi lokal
   CPU-only. Training GPU opsional dinonaktifkan secara default; reproduksi
   analisis/plot bisa dijalankan ulang di Colab setelah ekstraksi ZIP.
5. Susun dokumentasi perubahan 19 Oktober, panduan presentasi, indeks seluruh
   eksperimen, environment/dependency dan batas reproduksi. Hasil E14 yang
   selesai 20 Oktober dibedakan dari pilot/perubahan 19 Oktober.
6. Kemas source, notebook asli, hasil/fitur/checkpoint lokal yang relevan,
   data/gambar dan web dalam struktur rapi. Eksklusi hanya venv, cache runtime,
   kredensial, output web sementara dan arsip delivery duplikat; semua eksklusi
   dicatat. Checkpoint remote yang tidak tersedia tidak dianggap ada lokal.
7. Jalankan nbformat/nbclient, validasi sel output dan gambar embedded, render
   HTML notebook untuk inspeksi browser serta cek metrik/hash/CRC/isi ZIP.
   Cek web dari ekstraksi tanpa mengubah server yang sedang dipakai pengguna.
   Timestamp arsip historis sebelum 1980 dinormalisasi hanya pada metadata
   ZIP; byte file tidak diubah. Jika kompresi terhenti, verifikasi seluruh
   entry parsial terhadap manifest sebelum melanjutkan tanpa duplikasi entry.
8. Catat ukuran/checksum, hasil QA dan keterbatasan di plan/changelog; berikan
   satu ZIP final dan urutan notebook yang dibuka.

## Risiko & Asumsi
- Workspace tidak memiliki Git history. Before/after source hanya diklaim
  literal jika ada snapshot yang benar-benar cocok; sisanya perbandingan
  metode/artefak dengan tingkat bukti dinyatakan, bukan riwayat edit rekaan.
- Screenshot E13 berasal dari pilot 119 validation, bukan 740 OOF final.
  Tidak boleh dibandingkan sebagai eksperimen kontrol yang setara dengan E14.
- Semua hasil historis disimpan terpisah; tidak memilih epoch berbeda per task.
- Tidak semua eksperimen memiliki prediksi/log resource lengkap. Nilai absen
  bukan nol; gunakan Not Evaluated dan jelaskan alasan.
- Tiga notebook baru diverifikasi lokal dengan format Jupyter/Colab-compatible;
  membuka/menjalankan pada akun Colab langsung belum tentu dapat diuji di sini.
- File hasil/fitur besar dapat membuat ZIP >1 GB; transparansi dan kelengkapan
  didahulukan. Model publik/cache bisa perlu diunduh saat reproduksi training.
- Web terbaru tetap CLIP–IndoBERT, tidak diam-diam diganti E14 QLoRA. Colab
  untuk analisis/notebook; web dijalankan lokal, tanpa tunnel publik otomatis.

## Verifikasi
Semua notebook baru nbformat valid dan dieksekusi dengan nbclient tanpa error;
setiap bagian memiliki Objective/Methodology/Changes/Implementation/Benchmark
Results/Visualization/Analysis/Conclusion. Output tabel/grafik tersimpan dan
dapat dirender tanpa training ulang. Benchmark di-cross-check sumber dan SHA;
740 OOF serta pilot kontrol memakai ID/split tepat. Grafik ditinjau visual.
ZIP lulus CRC, manifest SHA-256, identitas notebook asli dan HTML web terbaru,
provenance data, scan kredensial umum, pemeriksaan runtime dari ekstraksi.
Jangan mengklaim clean Windows atau eksekusi Colab GPU jika tidak dilakukan.

## Hasil Aktual
- Paket: `delivery/experiment_final_20261020/TEMPO_EXPERIMENT_FINAL_20261020.zip`,
  satu root `experiment_final/`, 6.547 file, sekitar 3,13 GB terkompresi
  (3,44 GB sebelum kompresi). SHA final dicatat pada `.zip.sha256` dan
  `PACKAGING_VERIFICATION.json` di folder delivery; tidak ditanam ke file yang
  akan mengubah hash ZIP itu sendiri.
- Tiga notebook baru `01_baseline`, `02_experiments`, `03_final_comparison`
  berhasil dieksekusi dengan nbclient lokal, nbformat valid, tanpa error pada
  eksekusi final. Masing-masing memiliki delapan bagian yang diminta, tabel
  HTML tersimpan dan PNG embedded (2/5/4 output gambar). Tidak ada training baru.
- Sembilan CSV: 159 baris benchmark (150 dihitung ulang dari prediksi dan
  9 tercatat dalam JSON historis), 85 perbandingan termasuk minimum task,
  1.249 per-class, 53 catatan waktu/resource, enam step benchmark historis,
  tiga set OCR, 63 inventaris JSON hasil, 417 inventaris perubahan source dan
  11 inventaris notebook/snapshot. Jumlah baris lintas CSV tidak dijumlahkan
  menjadi jumlah percobaan independen.
- Tujuh grafik unik PNG/SVG ditinjau visual. Tiga HTML notebook lulus Chromium
  offline dengan 2/5/4 gambar termuat dan tabel numerik terlihat. Tabel pilot
  juga direkalkulasi/render memakai artifact-tool: MIN, delta pp dan persen
  relatif cocok, tanpa formula error.
- Sebelas salinan notebook aktif/pemulihan/snapshot diarsipkan byte-identik.
  Snapshot baseline 17→19 berubah pada sel Markdown 0,27,42, tanpa perubahan
  sel kode. Alasan perubahan dokumen historis tidak dipastikan; bukan optimasi
  yang diklaim menaikkan metrik. Source/hasil E12/E13/E14 dan batas tanggal
  training/pengambilan hasil 19→20 Oktober dijelaskan terpisah.
- Seluruh source/data/gambar/hasil lokal serta snapshot dokumen pemulihan
  dipertahankan, termasuk fitur penelitian dan checkpoint yang memang ada.
  Kredensial, venv/interpreter cache dan state web sementara dikecualikan dengan
  daftar alasan. Enam input fitur E12 tersedia dan cocok SHA-256.
- Web terbaru disertakan, beserta wrapper SETUP_WINDOWS/RUN_WEB_WINDOWS CRLF.
  Enam regresi Node, dua Chromium sorting desktop/mobile, dan lima tes CPU E14
  dari source salinan paket lulus. Model web tetap CLIP–IndoBERT.
- ZIP lulus CRC, semua hash konten, identitas source/notebook, serta runtime
  `check_delivery.py` dari ekstraksi. Metadata timestamp historis 1970 yang
  tidak didukung ZIP dinormalisasi ke 1980 hanya dalam metadata; byte sumber
  tetap sama. Entry parsial diverifikasi sebelum resume, tidak ada duplikasi.
- Materi menyatakan target Micro/Macro tiga task belum tercapai. Resource
  absen ditandai Not Evaluated, tidak diganti estimasi/angka nol. Durasi worker
  E14 tidak disebut sebagai wall-clock atau billing GPU.
- Belum diuji pada akun Colab langsung, training GPU Colab, clean Windows,
  acceptance OCR baru atau pengguna manusia. Batas ini tertulis di README,
  notebook, reproduksi dan laporan verifikasi. Source/model asli tidak diedit.
- Changelog dicatat pada `CHANGELOG.md`, `[Unreleased] / Added`.
