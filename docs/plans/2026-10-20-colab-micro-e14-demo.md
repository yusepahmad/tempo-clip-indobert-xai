# Demo sementara MICRO-E14 pada Google Colab GPU

**Tanggal:** 2026-10-20
**Status:** in-progress

## Tujuan
Menindaklanjuti pilihan pengguna: memakai Colab GPU untuk demo web E14 sementara, training tetap pada Kaggle. Menyediakan notebook launcher dan paket runtime kecil dengan status/validasi transparan.

## Ruang Lingkup
- Notebook Colab baru, helper verifikasi/start/stop runtime, pengujian dan dokumentasi.
- Paket Colab terpisah pada `delivery/colab_micro_e14_20261020/`, berisi web terbaru, dataset/gambar, kontrak dan checkpoint jika sudah terverifikasi.
- Plan deployment E14 dan changelog diperbarui.
- Tidak mengubah protokol/training CV, tidak menimpa ZIP lama, tidak memakai kredensial pribadi di paket.
- Tidak membuka tunnel publik; demo lewat proxy port Colab atau akses sesi Colab pengguna.

## Langkah
1. Periksa status Kaggle dan API Colab resmi; audit kebutuhan dependensi/file runtime.
2. Buat notebook dengan pemeriksaan GPU, upload/pilih ZIP, ekstraksi aman+hash, lingkungan Python terpisah, verifikasi checkpoint, start web dan health check.
3. Sajikan web lewat proxy port Colab setelah `ready=true`; sertakan langkah stop, troubleshooting dan batasan.
4. Siapkan paket yang bisa diperbarui setelah checkpoint selesai. Jika belum selesai, notebook harus berhenti dengan alasan jelas, bukan memakai baseline.
5. Uji struktur notebook, ekstraksi/hash, startup/health dengan fixture dan regresi yang relevan. Eksekusi GPU Colab hanya bila sesi tersedia; hasil tidak direkayasa.
6. Catat perubahan aktual di changelog dan bedakan artefak siap dari demo GPU yang benar-benar berjalan.

## Risiko & Asumsi
- Job refit Kaggle masih RUNNING; paket yang belum punya checkpoint tidak boleh disebut model E14 siap inference.
- GPU/kuota Colab dan akses sesi akun belum pasti. Tidak meminta/membundel token Kaggle/Hugging Face.
- Instalasi dependency harus terpisah dari kernel Colab agar tidak mengganti Torch yang sedang diimpor.
- Unggahan baru/XAI E14 belum tersedia; dataset demo adalah in-sample refit740 dan skor belum terkalibrasi.
- Proxy Colab bersifat sementara dan sesi perlu tetap hidup; tidak diperlakukan sebagai hosting produksi.

## Verifikasi
- Notebook nbformat valid, kode compile, penanda output aktual vs belum dieksekusi.
- ZIP tanpa credential/venv/cache job, CRC dan seluruh SHA; ekstraksi menolak traversal/symlink/overwrite.
- Readiness hanya setelah GPU smoke/model check, tidak ada fallback baseline.
- Dokumentasikan secara eksplisit apakah Colab GPU benar-benar diuji atau belum.
