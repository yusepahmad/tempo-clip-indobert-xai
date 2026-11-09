# Penutupan teknis Week 3
**Tanggal:** 2026-10-05
**Status:** done
## Tujuan
Kerjakan verifikasi skala740, akses/uji Windows, evaluasi kandidat OCR dan sinkronisasi status delivery.
## Ruang Lingkup
Script/output verifikasi terpisah, kandidat OCR jika terbukti, docsdelivery/changelog/paket review. Akses Windows memakai host/key yang sebelumnya diotorisasi; tidak mengubah dataset, label atau training. Kode uji disalin ke direktori `week3-verification` terisolasi dan Flask dipasang dengan pip --target vendor; environment training lama tidak dimutasi. Data/bobot Windows yang sudah ada dipakai read-only melalui konstanta runtime, bukan perubahan source training.
## Langkah
1. Verifikasi dataset740 dan jalur batch nyata, snapshot/evidence serta ekspor/progres.
2. Cek SSH Windows, cocokkan fingerprint sebelum akses; jalankan pemeriksaan kompatibilitas apabila terjangkau.
3. Ukur kandidat OCR pada blok sama serta pembanding decoding EasyOCR beamsearch pada30contoh dan3gambar dosen; simpan kasus gagal. Jangan memaksa koreksi ejaan untuk mencapai target. Produksi tidak diganti hanya berdasarkan diagnosis yang telah dilihat.
4. Periksa visual 11 kasus OCR gagal dan siapkan usulan headline/teks pendukung bertanda tinjauan agen; jangan mengganti ground truth dataset.
5. Sinkronkan checklist pada plan revisi utama dengan bukti implementasi dan catat gerbang penelitian terbuka.
6. Perbarui docs agar statuslama tidak bertentangan dengan codebook/gambar/training terbaru, rebuildpaketreview. Sinkronisasi dan pengemasan otomatis hanya setelah audit 740 lulus.
## Risiko & Asumsi
BatchCPU memerlukan waktu dan aset; in-sample bukan evaluasi akurasi. Windows dapat tidakterjangkau/autentikasi belum tersedia. TargetOCR80% tidak dijamin; pemeriksaan agen tidak menjadi validasi manusia. Integrationmodelbaru tetap gerbangterpisah karena Task2menurun.
## Verifikasi
Jumlah740 unik, peritemtask/input/expor/aset konsisten; buktiWindows jelas pass/block besertaalasan; angkaOCR tidak dikarang; docsdanpaket sesuai hasil.

## Hasil
Uji skala 740, Windows dan regresi lulus. UTF-8 diperbaiki. Kandidat OCR dievaluasi dan ditolak untuk produksi; 11 usulan visual dibuat. Dokumentasi dan paket review disinkronkan. Sasaran OCR 80% serta penerimaan semantik manusia tetap terbuka sebagai batas penelitian, tidak diklaim selesai.
