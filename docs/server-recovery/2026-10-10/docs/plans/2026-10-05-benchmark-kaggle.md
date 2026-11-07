# Benchmark Satu Epoch Kaggle

**Tanggal:** 2026-10-05
**Status:** done

## Tujuan
Mengukur durasi satu epoch CLIP+IndoBERT di GPU Kaggle untuk memperkirakan kebutuhan 5-fold/120 epoch terhadap kuota GPU 30 jam.

## Ruang Lingkup
- Tambah `DEMO_XAI_745_FULL/01_notebook/kaggle_benchmark/benchmark.py` dan `kernel-metadata.json`.
- Tambahkan wheels Python 3.13 Linux dan bobot pretrained CLIP/IndoBERT ke paket private agar benchmark bisa berjalan offline; salin bobot cache tanpa perubahan.
- Paket upload sementara `/tmp/tempo-kaggle-benchmark-upload`: CSV final, 740 gambar, notebook definisi model; tanpa credential, venv atau hasil training Windows.
- Dataset dan kernel PRIVATE pada akun Kaggle yang sudah login; batas job 3600 detik, satu epoch fold pertama (592 sampul), effective batch 16 dengan AMP.
- Plan ini, panduan hasil `docs/BENCHMARK_KAGGLE.md`, artefak hasil benchmark lokal jika job selesai, CHANGELOG.md.
- Tidak menghentikan training Windows, menjalankan eksperimen penuh, atau mengubah dataset/baseline.

## Langkah
1. Periksa akun dan opsi metadata/accelerator CLI.
2. Buat script benchmark Kaggle, upload paket input sebagai private dataset.
3. Jalankan kernel private GPU T4 dengan limit satu jam; ukur training dan evaluasi fold pertama. Versi 1 gagal DNS saat pip install meskipun metadata internet true; versi berikut memakai wheels dan pretrained weights lokal yang diunggah sebagai dataset private.
4. Versi 2 gagal karena torch bawaan CPU. Jalankan kernel diagnostik private terpisah `tempo-gpu-diagnostic` (maksimum 180 detik), mencatat nvidia-smi, device NVIDIA dan versi torch; tidak melakukan training. Simpan script/metadata di subfolder `diagnostic/`.
5. Pantau status/log, unduh output dan bandingkan estimasi terhadap kuota.
6. Dokumentasikan hasil nyata atau hambatan autentikasi/akses yang ditemukan.

## Risiko & Asumsi
- GPU bergantung kuota/verifikasi akun dan ketersediaan; hanya satu GPU digunakan oleh kode meskipun runtime T4 memiliki dua kartu.
- Encoder pretrained dan dependensi disediakan offline; setup dipisahkan dari waktu epoch.
- Benchmark hanya satu epoch, bukan metrik hasil 120 epoch. Estimasi tidak menjamin kecepatan berkelanjutan.
- Dataset dan kode tetap private; metadata lisensi other dengan deskripsi original authors retain copyright, tanpa memberi lisensi baru atas sampul Tempo. Pilihan copyright-authors dari dokumentasi ditolak API.
- Paket dependensi memakai torch bawaan Kaggle, open_clip_torch dan transformers kompatibel; error harus diperbaiki sebelum pengukuran dianggap valid.

## Verifikasi
Syntax script, metadata private, 740 path gambar, split 592/148, optimizer dan gradien encoder valid, durasi epoch dan GPU tercatat, output Kaggle terunduh bila berhasil.

## Progres
Versi 2 setup offline berhasil tetapi GPU tidak tersedia. Diagnostik terpisah selesai pada CPU tanpa perangkat NVIDIA. UI Kaggle menonaktifkan GPU/internet dan meminta verifikasi nomor HP. Menunggu user menyelesaikan verifikasi; benchmark satu epoch belum berjalan.

Setelah user menyelesaikan verifikasi, diagnostik versi 2 mendeteksi dua T4/CUDA. Benchmark versi 3 sukses: 30,98 detik/epoch, evaluasi 5,25 detik, peak allocated 3,89 GiB, kedua encoder diperbarui. Hasil dan log diunduh; estimasi 600 epoch 5,16 jam. Eksperimen penuh belum dijalankan.
