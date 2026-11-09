# Verifikasi Optimasi Kaggle
**Tanggal:** 2026-10-05
**Status:** done
## Tujuan
Pastikan optimasi dua T4 mempercepat epoch tanpa mengganti batch 16/LR/arsitektur dan dengan pemeriksaan finite gradien tetap setiap langkah.
## Ruang Lingkup
- kaggle_benchmark/optimized, output optimized, panduan dan changelog.
- Tidak menyentuh runner Windows atau menjalankan training penuh.
## Langkah
1. Jalankan baseline dan kandidat masing-masing satu epoch pada runtime yang sama, init dan sampler seed sama.
2. Kandidat: DDP static_graph untuk graf parameter terpakai/tidak terpakai yang tetap, fused AdamW, pin_memory dan transfer nonblocking; satukan pemeriksaan finite gradien agar satu sinkronisasi per langkah.
3. Verifikasi kedua encoder berubah, kedua rank sukses, finite setiap langkah, parameter unused dicatat, loss baseline/kandidat dibandingkan.
4. Unduh hasil; laporkan percepatan aktual atau regresi.
## Risiko & Asumsi
- Static graph gagal bila penggunaan parameter berubah; benchmark tidak membuktikan semua training jangka panjang.
- Fused optimizer dapat memiliki perbedaan numerik kecil; hasil satu epoch bukan jaminan metrik akhir.
- Tidak memakai cache preprocessing/worker multiprocessing sebelum dibuktikan aman.
## Verifikasi
Syntax; runtime dua T4; 37 langkah masing-masing konfigurasi; loss global dekat; pembaruan kedua encoder dan timing GPU disinkronkan.

## Hasil
Paired runtime COMPLETE; semua empat rank report sukses. Baseline 20,46 detik, kandidat 15,60 detik. Parameter unused adalah bert.pooler.dense.weight/bias, tetap pada kedua mode; static graph berhasil. Seluruh gradien dicek setiap langkah; kedua encoder berubah. Loss global berbeda kurang dari 0,001. Baseline checks pada uji ini menghitung tensor finite sebelum sinkronisasi per tensor, berbeda dari baseline awal 24,13 detik, sehingga perbandingan utama memakai paired runtime. Hasil diunduh; training penuh belum dijalankan.
