# Implementasi Week3
**Tanggal:** 2026-10-05
**Status:** done
## Tujuan
Implementasikan revisi konsistensi/UI/OCR/XAI dan mode batch pada baseline sambil menunggu hasil Kaggle.
## Ruang Lingkup
app.py, index.html, ocr_headline.py, modul evidence/catalog/batch baru, script regresi/evaluasi OCR, hasil revisi_week3 dan dokumentasi delivery/changelog. Dataset/gambar/baseline/training tidak diubah. Codebook lengkap/gambar dosen menunggu sumber; integrasi fine-tuned menunggu hasil valid.
## Langkah
1. Snapshot input dan task/class evidence; serialisasi engine bersama untuk mencegah race.
2. UI katalog/preview/invalidation; OCR kandidat/logo dan skor terpisah.
3. Selector lima strategi narasi yang membatasi klaim ke bukti.
4. Batch queue single worker, progress/review/error peritem dan export tersimpan, memakai core sama tanpa leave-one-out batch.
5. Regresi synthetic dan HTTP nyata, baseline OCR diagnosis, dokumentasi serta hasil/hambatan.
6. Tambahkan audit hasil fine-tuning (lima fold, hash data, cakupan OOF, metrik per kelas dan confusion matrix); jalankan setelah output lengkap tersedia. Script audit dan delivery masuk ruang lingkup, tanpa mengubah training aktif.
## Risiko & Asumsi
Batch model tetap pada corpus bersifat eksplorasi in-sample; bukan metrik evaluasi. Belum memiliki sumber lengkap25kelas/gambar dosen. API baseline head shared membutuhkan lock. Pengujian740/Windows/integrasi model baru tidak diklaim tanpa bukti.
## Verifikasi
Task/input tidak tertukar, manual teks dipakai, logo TEMPO5 difilter tanpa membuang TEMPE/MOMEN, lima narasi memiliki provenance, batch item gagal tidak menghentikan item lain dan ekspor valid, uji HTTP dengan model nyata.

## Hasil
Implementasi baseline, batch, audit persiapan training dan dokumentasi selesai. Tiga regresi Python, satu audit synthetic, regresi JavaScript dan HTTP tiga task lulus. Diagnosis OCR30:18 tepat; pembanding selector dengan blok sama:19 tepat. Hasil, batasan dan penerimaan eksternal yang belum selesai dicatat di `docs/DELIVERY_WEEK_3.md`; plan induk tetap in-progress. Paket review mengecualikan venv, cache, job privat lokal, bobot training dan credentials.
