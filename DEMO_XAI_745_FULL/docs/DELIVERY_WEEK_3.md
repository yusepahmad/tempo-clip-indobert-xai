# Delivery Week 3 — revisi demo XAI

Tanggal: 2026-10-05. Status: implementasi baseline siap ditinjau; penerimaan penelitian belum lengkap.
Plan: [implementasi](plans/2026-10-05-implementasi-week3.md) dan [backlog lengkap](plans/2026-10-05-week3-dan-revisi-demo-xai.md).

## Perubahan aplikasi

- Pengantar tujuan, panel tiga task dan katalog 25 kelas (10 isu, 7 domain, 8 jenis entitas). Contoh diambil dari label dataset. Definisi, kriteria, pembeda dan contoh tersedia melalui codebook operasional yang disusun sesuai instruksi user, dengan provenance rumusan baru.
- Preview gambar dan headline/teks pendukung final untuk dataset maupun unggahan. Edit pengguna menjadi input model. Hasil lama dibatalkan saat input/task berubah; respons terlambat tidak menimpa analisis berikutnya.
- OCR mengembalikan blok mentah, koordinat, kandidat judul dan skor engine. Logo `TEMPO5` disaring; headline beberapa baris digabung. Skor pembacaan tidak disebut peluang headline benar. Hasil OCR tetap perlu diperiksa.
- Explanation terikat pada task/kelas saat ini. Lima strategi dipilih berdasarkan bukti; kontribusi negatif, zona logo/teks dan skor rendah dijelaskan sebagai keterbatasan. Definisi dan catatan anotator tidak disebut alasan model.
- Batch dataset/unggahan: antrean serial, progres, koreksi OCR, kegagalan per item, lanjut/retry, ekspor CSV/JSON dan aset heatmap tersimpan. Manifest bertahan setelah restart server; pengguna menekan lanjut untuk job terputus.

## Cara mencoba

Jalankan launcher paket seperti biasa (`DEMO_XAI_745_FULL/jalankan_linux.sh` atau `jalankan_windows.bat`). Server pemeriksaan selama implementasi tersedia di `http://127.0.0.1:7861`.

1. Buka panel arti task; periksa definisi dan status sumbernya.
2. Pilih dataset, periksa preview, ubah headline bila perlu, pilih task dan klik Analisis. Ringkasan hasil harus menampilkan teks final dan task yang sama.
3. Unggah gambar. Periksa kandidat OCR, koreksi headline/teks pendukung, lalu analisis. Unggahan tidak memiliki label/anotasi pembanding.
4. Untuk batch, masukkan ID dataset dipisahkan koma atau pilih beberapa gambar. Pilih metode atribusi dan mulai. Unggahan menunggu konfirmasi teks sebelum analisis.
5. Unduh CSV untuk ringkasan; JSON menyimpan hasil dan bukti lengkap. Setelah restart server, gunakan Lanjutkan job terakhir. Item berhasil dipertahankan; item gagal dapat dicoba ulang.

Batch dataset memakai head yang dilatih seluruh korpus, sehingga hasilnya eksplorasi **in-sample**. Analisis dataset tunggal memakai leave-one-out. Kedua mode tidak boleh dibandingkan sebagai benchmark akurasi yang sama. LIME lebih lambat; metode aktual dicatat jika fallback occlusion digunakan.

## Bukti verifikasi

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

Perintah verifikasi dari root project (gunakan Python venv paket):

```bash
DEMO_XAI_745_FULL/venv/bin/python DEMO_XAI_745_FULL/01_notebook/test_week3_regressions.py
node DEMO_XAI_745_FULL/01_notebook/test_week3_state.js
DEMO_XAI_745_FULL/venv/bin/python DEMO_XAI_745_FULL/01_notebook/test_week3_training_audit.py
TEMPO_DEMO_URL=http://127.0.0.1:7861 DEMO_XAI_745_FULL/venv/bin/python DEMO_XAI_745_FULL/01_notebook/verify_week3_http.py
DEMO_XAI_745_FULL/venv/bin/python DEMO_XAI_745_FULL/01_notebook/evaluate_ocr_week3.py
```

## Evaluasi model dan gerbang integrasi

Baseline tersimpan di `04_hasil_eksperimen/hasil_mtl_740_task2domain.json`: fusion Macro-F1 Task 1 **0,4380**, Task 2 **0,3197**, Task 3 **0,2764**. Angka tersebut merupakan eksperimen baseline sebelumnya, bukan hasil perbaikan OCR/UI atau fine-tuning baru.

Pembaruan 2026-10-05: full training Kaggle COMPLETE dan audit metrik/protokol lulus. Task1/3 meningkat, Task2 menurun; hasil tetap terpisah dari demo. Lihat [laporan training](HASIL_FULL_TRAINING_KAGGLE.md). Checkpoint belum diunduh/diintegrasikan. Untuk audit setelah checkpoint tersedia, jalankan:

```bash
DEMO_XAI_745_FULL/venv/bin/python DEMO_XAI_745_FULL/01_notebook/audit_finetuned_week3.py /path/to/tempo_full
```

Audit menolak output smoke, hash data berbeda, fold/kelas tidak lengkap, cakupan OOF duplikat serta metrik tidak konsisten. Output `week3_audit.json` berisi metrik tiga task, per kelas, confusion matrix dan contoh salah. Keberadaan checkpoint diperiksa, tetapi isi bobot dan provenance split harus diperiksa lagi sebelum adapter model diintegrasikan. Jangan menyatakan peningkatan hanya berdasarkan contoh prediksi demo atau hasil in-sample.

## Status delivery saat ini

- T01: codebook operasional 25 kelas sudah dibuat sesuai instruksi user dan dipakai aplikasi. Rumusan ini bukan pedoman anotator lama; keselarasan label tetap perlu keputusan peneliti.
- T02, T03, T07–T09: implementasi input final, katalog, narasi berbasis bukti dan batch/ekspor selesai.
- T04–T06: diagnosis OCR dan dua eksperimen pembanding selesai, tetapi target headline 80% belum tercapai. Tersedia [usulan pemeriksaan visual 11 kasus](PEMERIKSAAN_VISUAL_OCR.md); tidak mengganti ground truth.
- T10: tiga gambar asli dosen diuji (2/3 headline tepat), tiga tinjauan sub-agent selesai dan uji Windows nyata lulus. Evaluasi agen tidak diklaim sebagai uji pengguna manusia. Batch penuh 740 lulus: 740 berhasil, nol gagal, 740 pemeriksaan HTTP heatmap, 3.700 aset dan CSV 741 baris termasuk header. Bukti: `scale740_verification.json`.
- T11: full training Kaggle COMPLETE, audit metrik/protokol lulus. Task1/3 meningkat, Task2 menurun; baseline tetap menjadi model demo. Checkpoint baru belum diintegrasikan, sehingga hasil fine-tuning tidak diklaim sebagai perilaku demo.
- T12: paket untuk review teknis tersedia; penerimaan penelitian masih memerlukan keputusan semantik/ground truth dan target evaluasi OCR.

## Bukti tambahan penutupan teknis

Lokasi output tetap `04_hasil_eksperimen/revisi_week3/`.

| Pemeriksaan | Hasil |
|---|---|
| Windows: halaman, 740 sampel, katalog 25 kelas, tiga task model nyata dan heatmap | Lulus; `windows_verification.json`. Dijalankan melalui SSH pada folder terisolasi dengan data/bobot lama read-only; bukan uji interaksi browser manusia |
| Regresi Python Linux dan Windows | Empat test lulus, termasuk manifest Unicode di luar cp1252; `windows_regression_verification.json` |
| Selector alternatif pada blok OCR sama | Kandidat 20/30 (66,7%) vs produksi 19/30; tambahan 10 contoh bukan set independen. Tidak diterapkan karena bukti perbaikan terbatas |
| EasyOCR beamsearch, 30 korpus + 3 gambar dosen | 16/30 vs greedy 19/30; gambar dosen tetap 2/3. Ada peringatan overflow numerik; kandidat ditolak. `decoder_comparison.json`, `decoder_numerical_warning.json` |

Bug decoding default Windows diperbaiki dengan encoding UTF-8 eksplisit pada katalog, definisi dan manifest batch. Environment training Windows tidak diubah; Flask hanya dipasang ke direktori vendor verifikasi.

Lihat [codebook](CODEBOOK_OPERASIONAL.md), [tabel pemeriksaan](TABEL_PEMERIKSAAN_REVISI.md), [evaluasi agen](EVALUASI_AGEN_WEEK3.md), [gambar dosen](VERIFIKASI_GAMBAR_DOSEN.md), dan [plan penutupan](plans/2026-10-05-penutupan-teknis-week3.md). Paket `DEMO_XAI_745_WEEK3_REVIEW.zip` mengecualikan environment, cache/job lokal dan checkpoint training.

Verifikasi skala: seluruh snapshot/input/task/kelas/evidence dan probabilitas valid; ekspor JSON berisi 740 item. Ini uji alur in-sample, bukan evaluasi akurasi. Job asli dan aset berada di `_jobs/` lokal dan dikecualikan dari ZIP; URL ekspor bukan aset portabel paket.

Penutupan teknis 2026-10-06: batch dipulihkan setelah proses terputus pada 651 hasil. Hash seluruh hasil lama identik; 89 sisanya selesai. Verifikasi HTTP tiga task/input manual, batch error terisolasi dan ekspor diulang setelah restart dan lulus. Bukti: `scale740_resume_verification.json` dan `http_verification.json`.
