# Audit hasil full training Kaggle

**Tanggal:** 2026-10-05
**Status:** done

## Tujuan
Verifikasi training selesai, simpan hasil evaluasi dan bandingkan terhadap baseline sebelum integrasi demo.

## Ruang Lingkup
- Output terpisah di `DEMO_XAI_745_FULL/04_hasil_eksperimen/finetuned_kaggle/`, script audit jika diperlukan, laporan hasil, panduan training dan CHANGELOG.
- Dataset, baseline, aplikasi dan job training tidak diubah. Integrasi checkpoint membutuhkan audit arsitektur/loader berikutnya.

## Langkah
1. Periksa status Kaggle; unduh log/metrik/prediksi tanpa checkpoint besar terlebih dahulu.
2. Periksa hash data, mapping kelas, lima fold, epoch akhir, cakupan OOF dan metrik per kelas.
3. Bandingkan metrik baseline dan laporkan batasan protokol.
4. Simpan hasil audit, dokumentasi dan changelog setelah verifikasi.

## Risiko & Asumsi
- COMPLETE pada platform belum membuktikan output evaluasi lengkap.
- Checkpoint besar dapat memerlukan waktu/ruang; unduh hanya setelah inventaris ukuran dan kebutuhan.
- Perbandingan OOF tidak otomatis membuktikan signifikansi atau performa deployment.

## Verifikasi
740 sampel unik dievaluasi tepat satu kali, lima fold selesai120epoch, metrik dihitung ulang dan konsisten, tidak ada output smoke atau ketidaksesuaian hash/kelas.

## Hasil
COMPLETE terverifikasi; metrik/log/prediksi disimpan, audit metrics-only dan protokol lulus. Task1/3 naik tetapi Task2 turun; baseline tetap default. Checkpoint besar belum diunduh/diperiksa karena belum digunakan untuk integrasi. Laporan `docs/HASIL_FULL_TRAINING_KAGGLE.md` menjelaskan angka dan batasannya. Uji audit synthetic tetap lulus setelah opsi metrics-only ditambahkan.
