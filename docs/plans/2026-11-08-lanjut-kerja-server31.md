# Lanjutkan Pekerjaan pada Server .31

**Tanggal:** 2026-11-08
**Status:** done

## Tujuan
Memindahkan workspace aktif dari laptop yang filesystem-nya read-only ke server research-user@10.12.1.31 agar revisi dan finalisasi delivery dapat dilanjutkan.

## Ruang Lingkup
- Workspace baru: /home/research-user/workspace/tempo-revisi-20261108.
- Source canonical DEMO_XAI_745_FULL, data740/gambar, hasil eksperimen/checkpoint, docs/revision/scripts dan delivery R3 FULL/tindak lanjut/R21 serta R4 terverifikasi dari /tmp laptop.
- Source yang diperbaiki di /tmp mengungguli draf project untuk builder, collector dan instruksi terbaru. Salinan laptop/R4 draf gagal tidak dijadikan delivery final.
- Environment Python baru .venv-analysis, QA transfer/hash/Run all, catatan handoff, plan dan CHANGELOG.
- Tidak menghapus sumber laptop, menimpa workspace lama learn, mengubah layanan/port lama, menyalin rahasia/autentikasi atau melatih model baru pada server. Venv lama, __pycache__, cache/jobs web dan arsip ZIP historis besar tidak disalin. Benchmark historis kecil yang diperlukan evaluator tetap disertakan.

## Langkah
1. Uji SSH dan baca instruksi server; inventaris kapasitas, source/env/GPU dan target baru.
2. Salin source/data/docs/delivery aktif menggunakan rsync resumable; gunakan copy-dest salinan lama bila cocok agar transfer efisien tanpa hardlink yang bisa mengubah salinan lama.
3. Dahulukan hasil/source sementara dari /tmp, pisahkan draf delivery lokal yang belum valid. Verifikasi checksum transfer dan manifest paket aktual.
4. Buat environment analisis Python3.10 terisolasi dengan versi terkunci. Jalankan validator dan tes yang relevan di server; finalisasi ZIP R4/Colab, uji ekstraksi dan Run all.
5. Rekam lokasi kerja baru dan task manusia. Job headline tetap di Kaggle; collector laptop yang sudah berjalan tidak dipindah/diulang tanpa verifikasi akses dan ledger. Tidak menyalin credential Kaggle otomatis.
6. Catat perubahan aktual, batas GPU/akses dan hasil verifikasi ke CHANGELOG dan plan di server; berikan perintah SSH/cd untuk melanjutkan.

## Risiko & Asumsi
- SSH research-user@10.12.1.31 sudah berhasil; workspace lama ada di /home/research-user/workspace/learn/TA-1-sekripsi-tempo-joy-eau-dia-final.
- Ruang server tersedia sekitar148GB; ukuran transfer dibatasi pada workspace aktif. Semua transfer ke direktori baru tanpa --delete.
- GPU driver nvidia-smi tidak berfungsi; pekerjaan analisis memakai CPU. Tidak memperbaiki driver server bersama otomatis.
- Hasil /tmp laptop akan hilang saat reboot, maka dipindah lebih dahulu. Laptop hanya dibaca.
- Credential tidak termasuk transfer; Kaggle privat memerlukan login server bila kelak collector dipindahkan. Job Kaggle tidak tergantung laptop tetap menyala.

## Verifikasi
- Rsync sukses dan pemeriksaan checksum dry-run tidak menemukan perbedaan pada file yang dimigrasikan; file yang sengaja dikecualikan dicatat.
- R4 memiliki740prediksi tambahan,78sumber/234metrik,3notebook terisi, seluruh hash/cakupan/link cocok; tidak mengklaim arm headline penuh selesai sebelum hasil nyata.
- Environment server dapat mengimpor dependensi terkunci dan menjalankan validator/tes/Run all ekstraksi ZIP.
- Workspace lama tidak ditimpa dan tidak ada source lokal dihapus.

## Penyesuaian transfer untuk workspace analisis
Koneksi laptop memakai hotspot/VPN dan berkas besar memperlambat kesiapan kerja. Prioritas dipersempit menjadi source, data/gambar, seluruh prediksi/result/protocol, notebook, dokumentasi dan instrumen manusia yang diperlukan untuk revisi/Run all CPU. Lampiran ZIP model E42 (488MB), ZIP historis/Colab lama dan blob training/cache .pt/.pth/.npy/.npz/.safetensors/.bin/.onnx ditunda, tidak dihapus. Manifest pemeriksaan transfer menyebut daftar yang ditunda; tidak ada klaim seluruh arsip/model sudah bermigrasi. Paket baru di server diberi scope analisis; manifest/hash dibuat ulang sesuai isi nyata. Paket lama server dan semua file laptop tetap utuh. Transfer resumable dipersempit tanpa --delete. Model/XAI yang telah tersimpan tetap bisa diperiksa; regenerasi training/XAI membutuhkan blob opsional tersebut.

## Regenerasi output pada server
Notebook output/HTML dan delapan ZIP manusia dapat dibuat ulang dari source, prediksi dan gambar yang sama di server. Berkas hasil render yang berulang dan ZIP manusia R4 tidak perlu ditransfer: notebook dieksekusi ulang, HTML diregenerasi dan ZIP instrumen dibangun dari template kosong canonical. Snapshot R3 digunakan hanya sebagai fixture input/analysis/documentation; bukan release lengkap untuk diserahkan. Paket R4 server menjadi paket analisis baru dengan QA dan manifest server sendiri. Cache _jobs/_cache pada snapshot recovery juga dikecualikan. Semua pengecualian bersifat salinan, sumber tidak dihapus.

## Finalisasi server
Builder lanjutan disesuaikan agar dapat memakai paket R4 analisis sebagai sumber tanpa mengganti isian pengguna pada paket lama. Peluncur Colab memakai requirements-analysis-lock.txt lengkap. Paket dan snapshot source diperbarui sebelum sealing/QA ekstraksi.

## Hasil aktual
- SSH .31 berhasil; workspace baru dan tmux siap, tanpa menimpa salinan learn.
- SHA256 8.060 file terpilih cocok; 531.306.812 byte baseline transfer diverifikasi.
- Python 3.10.12 dengan 66 dependensi terkunci siap; 26 tes lulus, termasuk perlindungan pengembalian manusia.
- Tiga notebook R4 lulus Run all server dan ekstraksi ZIP ulang. 234 metrik, 78 sumber, 141 bukti revisi + 29 lampiran, 49 CSV penuh dan 1.054 tautan HTML diperiksa. Instrumen manusia tetap kosong; delapan ZIP dibuat ulang dari input canonical di server.
- ZIP analisis 449.938.890 byte dan checksum tersedia; paket Colab 449.939.083 byte dan launcher disiapkan, Colab belum dijalankan.
- Lampiran model/cache training besar ditunda. Source asli/laptop/learn tidak dihapus. Credential tidak dipindah; Kaggle headline version 2 tetap RUNNING pada snapshot terakhir, collector laptop belum dipindahkan.
- qa/MIGRATION_SOURCE_MANIFEST.json adalah baseline penerimaan; perubahan source helper, test baru, WORKSPACE_INDEX, CONTINUE_HERE dan CHANGELOG setelahnya merupakan perubahan terencana yang dicatat.
