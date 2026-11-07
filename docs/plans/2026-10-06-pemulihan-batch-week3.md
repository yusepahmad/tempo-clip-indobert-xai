# Pemulihan dan penutupan batch Week 3

**Tanggal:** 2026-10-06
**Status:** done

## Tujuan
Memulihkan batch yang terputus setelah 651 sampel berhasil dan menuntaskan audit/paket review.

## Ruang Lingkup
Server lokal, manifest job yang sama, script verifikasi/pengemasan yang sudah disiapkan, docs delivery/plan/changelog. Dataset, label, bobot dan training tidak diubah.

## Langkah
1. Jalankan server terpisah dari terminal dengan log lokal, lalu resume job yang sama.
2. Pastikan 651 hasil berhasil dipertahankan; tunggu 89 sisanya dan audit seluruh 740.
3. Jalankan penutupan dokumentasi dan paket hanya setelah audit lulus.
4. Verifikasi ZIP, status HTTP, regresi serta catat perubahan dan hasil pemulihan.

## Risiko & Asumsi
Batch in-sample bukan evaluasi akurasi. Pemutusan proses dapat terjadi kembali; manifest/aset mempertahankan hasil. Target OCR 80% masih terbuka.

## Verifikasi
740 berhasil/nol gagal, snapshot/aset/ekspor lulus, 651 hasil lama identik, ZIP integritas lulus, dokumen tidak mengklaim penerimaan penelitian penuh.

## Hasil
740/740 berhasil, nol gagal; 651 hash hasil lama tidak berubah. Audit 3.700 aset, 740 URL heatmap, snapshot/task/evidence serta CSV/JSON lulus. HTTP tiga task/input manual dan isolasi error batch lulus; regresi empat test/JavaScript lulus. Paket review diperbarui dan integritas diperiksa.
