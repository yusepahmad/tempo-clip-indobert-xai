# Aktifkan Web CLIP–IndoBERT Terbaik

**Tanggal:** 2026-11-08
**Status:** in-progress

## Tujuan
Mengaktifkan web pada server .31 menggunakan kandidat CLIP–IndoBERT dengan Micro-F1 terbaik sesuai bukti evaluasi, lalu push source dan dokumentasi ke repository public yang baru. Pengguna telah memilih CLIP–IndoBERT, bukan Qwen.

## Ruang Lingkup
- Source web `DEMO_XAI_745_FULL/02_web_demo/`, kontrak model `06_models/`, source launcher/serving yang diperlukan, dokumentasi deploy, plan, CHANGELOG serta README publik.
- Artefak checkpoint/backbone asli disalin read-only dari laptop atau arsip yang tersedia ke server; tidak dimasukkan ke Git. Tidak mengubah label/fold/prediksi penelitian, delivery R4, status revisi manusia, filesystem laptop atau model Qwen.
- Perubahan disinkronkan secara eksplisit ke `tempo-clip-indobert-xai-public/`, tanpa credential/cache/log/data pribadi.

## Langkah
1. Audit peringkat Micro-F1 kandidat CLIP–IndoBERT, protokol, source training, checkpoint dan kebutuhan encoder. Tentukan kriteria terbaik secara terbuka; tidak mencampur Qwen.
2. Migrasikan artefak yang diperlukan dengan SHA-256, siapkan runtime CPU karena driver GPU server belum tersedia. Pertahankan baseline sebagai opsi eksplisit, tanpa fallback diam-diam.
3. Implementasikan backend inference model terpilih, identitas/status/skor yang akurat, dan XAI melalui checkpoint yang sama. Dataset memakai model outer-fold sesuai ID; upload/teks edit memakai ensemble yang dijelaskan atau refit sah bila tersedia. Jangan menyajikan CSV OOF sebagai inference.
4. Jalankan pemeriksaan checkpoint/probabilitas terhadap prediksi asli dan uji API, unggahan, XAI serta UI; aktivasi persisten di port yang kosong.
5. Perbarui petunjuk akses/reproduksi dan CHANGELOG sesuai hasil aktual, audit diff publik lalu commit/push main. Verifikasi URL web dan SHA remote.

## Risiko & Asumsi
- Permintaan aktifkan dan push adalah otorisasi menjalankan layanan web proyek di server dan push ke repo public. Tidak perlu meminta konfirmasi lagi.
- “Terbaik” perlu merujuk pada cakupan/aturan ranking 740 OOF; pemilihan post-hoc harus disebut, bukan dianggap hasil evaluasi baru.
- Checkpoint/backbone belum ada pada workspace migrasi. Artefak hanya boleh disebut siap sesudah hash/replay valid. CPU tersedia dengan RAM cukup, tetapi inferensi/XAI bisa lebih lambat daripada GPU.
- Jika model terbaik tidak dapat direkonstruksi dari checkpoint sah, laporkan keterbatasan secara eksplisit; jangan mengaku baseline sebagai model terbaru atau membuat checkpoint palsu.

## Verifikasi
- Kontrak model dan API menyebut ID kandidat, backbone, input, protokol serta Micro-F1 yang sama dengan hasil analisis.
- Replay outer-fold menghasilkan label/probabilitas sesuai referensi; jalur unggahan benar-benar menghitung encoder+model.
- XAI memakai model/konteks yang sama; skor dinyatakan belum dikalibrasi.
- API/halaman web bisa diakses di server; proses tetap berjalan setelah SSH selesai.
- Git bersih, credential/artefak runtime tidak masuk commit, SHA main remote cocok.

## Keputusan implementasi setelah audit
- Terpilih `RII_TAIL_RICH256`, peringkat maksimum minimum Micro-F1 tiga task di antara kandidat CLIP–IndoBERT bersama yang dievaluasi pada 740 OOF. Micro-F1 Task 1/2/3: 0,493243/0,524324/0,514865; pemilihan bersifat post-hoc. Macro-F1 tetap dicantumkan; tidak mengklaim unggul atas Qwen atau terbaik pada setiap task.
- Lima checkpoint asli masih tersedia pada output Kaggle; diambil tanpa submission/training baru dan diverifikasi terhadap `checkpoint_sha256` pada hasil eksperimen. Dataset memakai outer-fold, termasuk batch dan teks edit; unggahan baru memakai rerata probabilitas lima fold. Ensemble unggahan tidak memiliki skor OOF tersendiri.
- Input rich mencakup headline, supporting, deskripsi gambar, observasi sumber visual dan alasan visual yang label-blind. Dataset memakai JSONL canonical. Unggahan harus mengisi tiga keterangan visual, tanpa generasi Qwen tambahan. Batch unggahan dibatasi eksplisit ke jalur satu-per-satu karena UI batch lama tidak menampung keterangan per gambar; batch dataset tetap didukung.
- Inference dan XAI melalui checkpoint asli, pinned CLIP-L14 full/crop dan IndoBERT front 10 blok; tidak ada pelatihan ulang head baseline. Runtime terpisah `.venv-web` dengan torch CPU.
