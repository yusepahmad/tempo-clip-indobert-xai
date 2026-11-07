# E01 — VLM dua tahap untuk Task 2 (persiapan Kaggle)

**Tanggal:** 2026-10-08
**Status:** approved 2026-10-08, dengan syarat di bawah. Langkah 1–2 dikerjakan; langkah 3 (smoke Kaggle) menunggu koneksi Kaggle dari user.

### Keputusan user (8 Okt)
- **Hanya resource di dalam `learn`.** VLM/LLM berbentuk API atau service lain di server tidak boleh disentuh. Tidak ada unduhan atau cache di luar `learn`.
- **Model tahap 1:** Qwen3-VL-8B-Instruct, bobot terbuka yang diunduh **di dalam kernel Kaggle**, bukan service Qwen mana pun di server. Bisa diganti bila user mau.
- **Uji tahap 1:** opsi (ii), langsung smoke Kaggle 12 sampel. Uji lokal (i) dibatalkan karena perlu mengunduh bobot dari luar `learn`.
- **Push ke Kaggle:** Claude menyebutkan kebutuhan koneksi, user yang menyiapkan. Full run tetap menunggu persetujuan user setelah smoke dilaporkan.
- **Push dari server ini (opsi 1, 8 Okt).**
  - Python 3.10 di server hanya bisa memasang Kaggle CLI 1.7.4.5, yang tidak punya `--accelerator`. Karena itu dipasang Python 3.12.15 portabel lewat `uv` plus Kaggle CLI 2.2.4, semuanya di `learn/.kaggle/` (`python/`, `uv-cache/`, `cli/`; `venv/` berisi CLI 1.7.4.5 dan `uv`).
  - Token `learn/.kaggle/kaggle.json` ditaruh user, lalu di-`chmod 600`. Ini di luar `DEMO_XAI_745_FULL/` agar tidak ikut ZIP delivery.
  - Perintah dipanggil dengan `KAGGLE_CONFIG_DIR=/home/yusep/workspace/learn/.kaggle`. Tidak ada yang tertulis di `~/.kaggle` atau `~/.config/kaggle`.
- **Internet kernel:** aktif (`enable_internet: true`). Unduhan bobot dan pip terjadi di Kaggle, bukan di mesin ini.

## Tujuan
Menaikkan Macro-F1 Task 2 (domain sumber metafora). Sekarang angkanya 0,320 pada baseline dan 0,246 pada fine-tuning Kaggle. Target user 0,7 kemungkinan di atas plafon data. Lihat "Dasar" di bawah.

### Dasar
- Model sekarang bertumpu pada kepala sampul (logo dan judul kecil) di 22 dari 25 sampul, bukan pada ilustrasinya (`analisis_zona_740.json`).
- Cek cepat 8 Okt memakai TF-IDF + regresi logistik, 5-fold, split stratifikasi Task 2 (bukan split baseline):

  | Input | Macro-F1 Task 2 |
  |---|---:|
  | Judul + teks pendukung | 0,221 |
  | Deskripsi visual anotator (`task2_source_description`) | 0,538 |
  | Deskripsi visual + catatan mapping anotator | 0,596 |
  | Deskripsi visual + judul + teks pendukung | 0,399 |

- Kesimpulan sementara: deskripsi literal ilustrasi adalah sinyal paling kuat untuk Task 2, dan judul justru mengencerkannya. E01 menguji apakah deskripsi buatan VLM bisa mendekati deskripsi anotator. Angka 0,54–0,60 adalah plafon kasar dengan classifier sederhana, bukan janji hasil.
- **Koreksi 8 Okt (langkah 2):** angka rujukan anotator **terlalu tinggi**. `task2_source_description` kosong pada 83/83 sampel NON_METAFORA dan terisi pada semua kelas lain, sehingga NON_METAFORA dikenali sempurna hanya dari kosongnya deskripsi (recall 1,0). Tanpa kelas itu, rata-rata F1 enam kelas metafora dengan deskripsi anotator ≈ 0,46. Deskripsi VLM selalu berisi, jadi kemudahan ini tidak tersedia. Rujukan realistis untuk E01 adalah sekitar 0,46 pada enam kelas metafora, bukan 0,54–0,60.

## Rancangan
**Tahap 1 (Kaggle, GPU 2×T4).** VLM membaca 740 sampul dengan dua prompt:
- **A — deskripsi literal** ilustrasi: tokoh, hewan, benda, tindakan, latar. Logo, tanggal, barcode, tulisan, dan penafsiran diabaikan.
- **B — klasifikasi zero-shot** Task 2 dari gambar, judul, dan teks pendukung, memakai definisi/kriteria/pembeda codebook operasional. Contoh dataset di codebook tidak dimasukkan ke prompt agar tidak bocor.

Hasil ditulis per sampel ke JSONL secara bertahap, sehingga job bisa dilanjutkan. `meta.json` mencatat model, revisi, hash prompt, hash CSV, GPU, waktu, dan jumlah keluaran rusak. Job berhenti otomatis bila keluaran rusak massal (gejala overflow fp16).

**Tahap 2 (lokal, CPU, di dalam `learn`).** Evaluasi OOF 5-fold dengan split yang sama dengan `run_evaluation.py`: StratifiedKFold(5, shuffle, seed 42), stratifikasi `task1_issue`, kelas < 5 sampel digabung. Hyperparameter dipilih lewat inner-CV pada fold latih saja.

Varian:
- (a) label zero-shot B langsung;
- (b) TF-IDF deskripsi A + LR;
- (c) fusi deskripsi A + fitur CLIP/IndoBERT baseline + LR.

Rujukan pada split yang sama: deskripsi anotator dan baseline. Task 1 dan 3 ikut dilaporkan.

## Keputusan yang dibutuhkan dari user
1. **Model VLM tahap 1.** Belum diputuskan. Usulan awal Qwen3-VL dipilih Claude tanpa konfirmasi.

   | Opsi | Kelebihan | Kekurangan |
   |---|---|---|
   | Qwen3-VL-8B-Instruct (usulan awal) | Bobot terbuka, revisi bisa dikunci, muat di 2×T4 fp16, kuat untuk deskripsi gambar dan bahasa Indonesia | Keluarga Qwen-VL pernah bermasalah di fp16 |
   | Gemma 3 (4B/12B) | Bobot terbuka, multibahasa bagus | 12B perlu dibagi 2 GPU; perlu menerima lisensi Gemma di HF |
   | InternVL 3 | Kuat di deskripsi visual | Bahasa Indonesia lebih lemah |
   | API (Claude/Gemini/GPT) | Kemungkinan paling akurat; tanpa GPU/Kaggle | Biaya per gambar, sampul dikirim ke pihak ketiga, versi model tidak bisa dikunci; tahap 1 perlu dirombak |

2. **Cara menguji kode tahap 1 sebelum full run.** Kodenya belum pernah terbukti jalan; uji lokal 8 Okt dihentikan.
   - (i) Uji lokal CPU dengan model kecil. Cache model (±4 GB) ditaruh di dalam `learn`, misalnya `learn/.cache_hf/`, dan dihapus setelah uji.
   - (ii) Langsung kernel smoke Kaggle, 12 sampel.
3. **Push ke Kaggle.** Mesin ini belum punya Kaggle CLI dan kredensial. Pilihannya: user push sendiri dari mesinnya, atau CLI dipasang di `venv` proyek dan `kaggle.json` ditaruh di dalam `learn` (perlu izin user).
4. **Internet di kernel Kaggle.** Rancangan memakai `enable_internet: true` untuk mengunduh bobot dari HF dan memasang transformers. Alternatifnya offline: bobot diunggah sebagai dataset/model Kaggle (8B ±17 GB).

## Ruang Lingkup
Semua di dalam `learn/DEMO_XAI_745_FULL/`. Tidak ada baca/tulis/unduh di luar `learn` tanpa izin user.

Berkas yang **sudah terlanjur dibuat 8 Okt** sebelum plan ini disetujui, belum diverifikasi, dan belum dicatat di CHANGELOG:
- `01_notebook/e01_vlm.py`: skrip tahap 1, default Qwen3-VL-8B (revisi `0c351dd0`).
- `01_notebook/e01_evaluasi.py`: skrip tahap 2.
- `01_notebook/kaggle_e01/siapkan_kernel.py`, serta `kaggle_e01/{full,smoke}/` berisi `e01_vlm.py` dan `kernel-metadata.json`. Kernel id `tempo-e01-vlm` dan `tempo-e01-vlm-smoke`, dataset `tempo-benchmark-20261005`.
- `04_hasil_eksperimen/e01_vlm/uji_lokal_cpu/` dan `uji_alur_anotator/`: folder kosong dari uji yang dihentikan.

Setelah plan disetujui, berkas-berkas ini disesuaikan dengan keputusan di atas, atau dihapus bila user mau mulai bersih.

TIDAK disentuh: aplikasi `02_web_demo/`, dataset, model baseline, paket delivery, dan kernel Kaggle lama.

## Langkah (setelah disetujui)
1. Sesuaikan `e01_vlm.py` dengan model pilihan (keputusan 1) dan mode internet (keputusan 4). Jalankan `siapkan_kernel.py`. Pastikan salinan `full/` dan `smoke/` hanya berbeda pada `LIMIT`, dan `py_compile` lulus.
2. Uji alur tahap 2: `e01_evaluasi.py --pakai-deskripsi-anotator`. Ini hanya CPU dan tanpa unduhan. Harapannya Macro-F1 Task 2 varian deskripsi anotator di kisaran 0,5–0,6 dengan split baseline.
3. Uji tahap 1 sesuai keputusan 2:
   - (i) lokal: 4 sampel, batch 2, lalu jalankan ulang untuk membuktikan resume (0 sampel diproses ulang);
   - (ii) smoke Kaggle 12 sampel.

   Periksa isi deskripsi, label valid, keluaran rusak, dan estimasi jam untuk 740 sampel.
4. Laporkan hasil uji dan estimasi waktu/kuota ke user. **Full run hanya setelah user setuju.**
5. Push full (cara sesuai keputusan 3), unduh output ke `04_hasil_eksperimen/e01_vlm/kaggle_full/`, lalu jalankan `e01_evaluasi.py`.
6. Catat ke `CHANGELOG.md`, tulis hasil ke dokumen hasil E01, lalu laporkan.

Tindak lanjut terpisah, di luar plan ini:
- E01b: crop kepala sampul untuk fitur CLIP (CPU lokal);
- uji kesepakatan anotator kedua (plafon manusia);
- E02: perbaikan resep fine-tuning (head Task 2 terpisah/bobot loss, LR encoder kecil atau LoRA, early stopping dengan inner validation).

## Hasil langkah 1–2 (8 Okt)
- **Langkah 1:** `siapkan_kernel.py` membangun `full/` (LIMIT=0) dan `smoke/` (LIMIT=12). Diff hanya pada baris LIMIT. `py_compile` lulus. Fungsi bantu `parse_b` (JSON valid, fallback kode, tidak valid), `rusak`, dan `cari_data` diperiksa manual dan lulus. Model belum pernah dimuat; itu menunggu smoke Kaggle.
- **Langkah 2:** `e01_evaluasi.py --pakai-deskripsi-anotator` lulus dengan split baseline. Bukti ada di `04_hasil_eksperimen/e01_vlm/uji_alur_anotator/`. Macro-F1:

  | Task | TF-IDF deskripsi anotator | Fusi deskripsi + CLIP/IndoBERT | CLIP/IndoBERT + LR |
  |---|---:|---:|---:|
  | Task 1 | 0,285 | 0,495 | 0,424 |
  | Task 2 | 0,531 (lihat koreksi NON_METAFORA) | 0,501 | 0,321 |
  | Task 3 | 0,291 | 0,361 | 0,321 |

  CLIP/IndoBERT + LR mereproduksi baseline MTL Task 2 (0,321 vs 0,320), jadi split dan alurnya konsisten. Run ini memakai ±25 core karena thread BLAS per job. Skrip sudah dikunci ke 1 thread BLAS per job (total 8) untuk run berikutnya.

## Smoke v1 gagal, perbaikan untuk v2 (8 Okt, disetujui user)
- **v1:** push 15:51, masih RUNNING pada 18:05. `--timeout 3600` tidak dipatuhi. Log dan output kosong lewat CLI, dan CLI tidak punya perintah stop. User menghentikan sesi lewat web. Penyebab hang tidak diketahui.
- **Perbaikan di `e01_vlm.py`:**
  1. Batas waktu internal (`BATAS_MENIT`: smoke 40, full 600). Thread watchdog menulis `tahap.log` dan `meta.json` lalu keluar normal saat tenggat, termasuk bila hang terjadi di pip, unduhan, atau generate. Dengan begitu run selalu selesai dan output tersimpan.
  2. `tahap.log` ber-timestamp di folder output: pip, unduhan bobot (`snapshot_download` terpisah), muat model, peta device dan memori GPU, serta tiap batch.
  3. Offload ke CPU/disk dilarang: `max_memory` hanya untuk GPU, dan run gagal dengan pesan jelas bila ada lapisan di CPU/disk. Ini dugaan penyebab lambat yang belum terbukti.
  4. `pip install` diberi timeout 15 menit.
- **Langkah:**
  1. Edit skrip dan `siapkan_kernel.py` (BATAS_MENIT per kernel).
  2. Jalankan `py_compile`, diff salinan, dan uji watchdog secara lokal tanpa model.
  3. Pastikan v1 tidak RUNNING lagi.
  4. Push smoke v2.
- **Hasil:**
  - Langkah 1–2 selesai. Salinan kernel hanya berbeda pada LIMIT/BATAS_MENIT, dan `py_compile` lulus.
  - Uji lokal tanpa model (`04_hasil_eksperimen/e01_vlm/uji_watchdog/`): watchdog berhenti di tenggat dengan status `waktu_habis`, error ditangkap dengan status `gagal` beserta traceback di `tahap.log`, dan keduanya exit 0.
  - **Langkah 3 tertahan:** user melaporkan sesi sudah di-stop, tetapi API masih menunjukkan v1 RUNNING sampai 18:13. v2 tidak di-push agar tidak ada dua sesi GPU.
- **Temuan 18:20 (read-only):**
  - Sesi v1 tidak bisa di-stop user dari web. `kernels logs --follow` ditolak server (HTTP 500).
  - Statistik kuota akun lewat `learn/.kaggle/kuota.py` (SDK `GetAcceleratorQuotaStatistics`): `totalTimeAllowed` 21.600 dtk (**6 jam per periode**, bukan 30 jam seperti 5 Okt), `timeUsed` 20.758 → 20.773 dtk dalam 15 detik. Artinya v1 masih memakan kuota, dan sisa ±14 menit akan habis sekitar 18:35. Refresh kuota: 2026-10-10 00:00 (zona waktu tidak dinyatakan API, kemungkinan UTC = 07:00 WIB).
  - SDK punya `CancelKernelSession`, tetapi butuh `kernel_session_id` yang tidak dikembalikan oleh status atau metadata. Pembatalan tidak dicoba.
- **Akibatnya:**
  - Smoke v2 baru bisa di-push setelah kuota refresh.
  - Full 740 sampel harus muat dalam 6 jam per periode. `BATAS_MENIT` full perlu diturunkan dari 600, atau full dibagi beberapa periode lewat `RESUME_SOURCE`, atau dipertimbangkan model 4B. Keputusannya diambil setelah smoke v2 memberi angka detik per sampel.

## Risiko & Asumsi
- fp16 di T4 bisa menghasilkan NaN atau teks rusak. Mitigasinya: smoke dulu dan berhenti otomatis.
- Versi transformers di Kaggle tidak pasti. Launcher memasang `transformers==5.17.0`, sama dengan kernel lama.
- Durasi full belum diukur. Estimasi diambil dari smoke.
- Deskripsi VLM bisa jauh lebih buruk daripada deskripsi anotator. Bila begitu, E01 tetap menjadi bukti negatif yang dilaporkan apa adanya.
- Codebook di prompt B adalah codebook operasional 5 Okt, bukan codebook resmi.
- Hasilnya evaluasi OOF pada 740 sampel yang sama, bukan bukti untuk korpus eksternal.

## Verifikasi
- Uji tahap 1 (lokal atau smoke): jumlah baris JSONL sama dengan jumlah sampel uji. Setiap sampel punya deskripsi dan label zero-shot valid. Resume tidak memproses ulang sampel. `meta.json` lengkap.
- Uji alur tahap 2 mereproduksi kisaran cek cepat dengan split baseline.
- Full: 740/740 sampel, split dan hash CSV cocok, dan metrik tahap 2 bisa dihitung ulang dari JSONL.
