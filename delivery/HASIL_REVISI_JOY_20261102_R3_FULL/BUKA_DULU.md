# Versi R3 FULL — hasil audit

Ketiga notebook berisi output tersimpan dan seluruh bukti yang tersedia. Empat confusion matrix Task 3 (baseline, E42, E11, E14), tabel distribusi/entropi/weighting, seluruh gambar XAI, tabel lengkap dan source bukti telah dimasukkan.

- 141 berkas bukti per revisi dan 21 lampiran canonical ditampilkan.
- Seluruh 28 butir memiliki bagian notebook; 19 selesai teknis, 9 masih terbuka.
- Semua tiga notebook lulus Run all lokal; bukti Colab dan penilaian manusia tetap sesuai status.
- 499 file data/prediksi/analisis/model/instrumen/protokol/XAI identik dengan R2.

Mulai dari **MULAI_DI_SINI.html**. Notebook di **notebooks/**, HTML di **notebook_html/**. Rincian pemeriksaan ada di **qa/FULL_NOTEBOOK_VERIFICATION.json** dan cakupan per file di **documentation/NOTEBOOK_FULL_COVERAGE.json**.

---

# Hasil revisi notebook Joy — 2 November 2026

Paket ini mengumpulkan hasil revisi yang tersedia dalam satu folder. Mulai dari **MULAI_DI_SINI.html**; halaman ini dapat dibuka tanpa Python. Untuk melihat revisi R18 yang ditandai, buka **notebook_html/02_experiments.html**, bagian **R18 — Arsitektur Multi-Task Learning CLIP–IndoBERT dengan Joint Loss**.

## Tiga notebook yang diperbaiki
- notebooks/01_baseline.ipynb: data, baseline, metrik, codebook; identitas model R18 ditulis langsung.
- notebooks/02_experiments.ipynb: arsitektur lengkap, rumus Joint Loss, konfigurasi checkpoint per fold, ablasi, input dan XAI.
- notebooks/03_final_comparison.ipynb: keputusan model, statistik, peta 28butir dan tanggapan langsung tiap revisi.

Screenshot delivery 20 Oktober dan halaman sumber R18 ada di dalam notebook sebagai attachment, sehingga tetap terlihat saat notebook dibuka tanpa folder gambar. Salinan file dan hash tersedia di screenshots/. Screenshot lama diberi label historis; hasil revisi dibaca dari tabel baru, bukan disimpulkan dari gambar lama.

## Bukti dan reproduksi
- inputs/ dan analysis/: dataset/fold/prediksi serta metrik yang dihitung ulang.
- tools/ dan source/: evaluator, validator dan source yang dapat ditelusuri.
- qa/: bukti Run all serta replay E42. Colab belum dinyatakan lulus.
- lampiran_model/: ZIP lima checkpoint E42 + cache/citra untuk replay. Seluruh 740 × 3 prediksi telah direplay tanpa perbedaan.
- paket_untuk_manusia/: delapan ZIP terpisah untuk dua anotator, lima penilai XAI dan audit 60 kasus. Jangan membagikan folder analisis atau coordinator_private/ kepada penilai.
- documentation/TINDAK_LANJUT_JOY.md: daftar pekerjaan/bukti yang masih terbuka.

## Batas status delivery
Paket ini hasil revisi teknis yang bisa diperiksa sekarang. Penilaian manusia, data asal 1.040 dan log eksklusi, bukti historis proses E01, wording lengkap revisi Agustus serta QA Colab yang belum terverifikasi tidak dianggap selesai.

Kontrol Qwen zero-shot basic/rich 740 sampel sudah selesai dan diverifikasi. QLoRA basic baru lulus smoke 4 sampel; training lengkap lima fold belum dilakukan, sehingga R21 tetap terbuka. Tidak ada training tersembunyi pada Run all notebook.

Jangan memakai angka/screenshot demo lama sebagai hasil inferensi E42. Model utama E42 dan demo web CLIP-B32 dijelaskan terpisah. Tidak ada perubahan label atau deployment model aktif dalam paket ini.

Dua screenshot aktual perbaikan R18 dan rumus Joint Loss juga tersedia di `screenshots/current_20261102_r18_notebook02.png` dan `screenshots/current_20261102_joint_loss.png`. Keduanya berasal dari tampilan HTML notebook revisi yang sudah dieksekusi secara lokal.

## Pembaruan R1 — klarifikasi R23

Joy sudah menjelaskan bahwa banyak citra sampul berkualitas buruk sehingga tidak dapat dilabeli. Menurut Joy, alasan penyusutan ini pernah disampaikan. Penjelasan sudah dimasukkan ke riwayat korpus, draf naskah, tracker dan notebook. Kappa dua anotator adalah bagian R23 yang terpisah dan masih membutuhkan dua set label independen. Jumlah spesifik mengikuti dokumen revisi/dataset; pesan Joy memakai angka perkiraan.

## R2 — bukti per revisi

Buka `BUKTI_PER_REVISI/INDEX.html` untuk folder R18, R19, dan seterusnya. Setiap folder berisi bukti nyata sesuai permintaan PDF, panduan dan lokasi notebook. 19 folder mengikuti 19 butir selesai teknis; 9 butir terbuka tetap terdaftar dengan alasan dan tidak diberi status selesai.
