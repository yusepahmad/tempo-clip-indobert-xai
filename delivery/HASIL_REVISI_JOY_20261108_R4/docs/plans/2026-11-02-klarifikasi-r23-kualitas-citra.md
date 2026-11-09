# Klarifikasi R23 — Eksklusi karena Kualitas Citra

**Tanggal:** 2026-11-02
**Status:** done

## Tujuan
Memasukkan keterangan Joy yang diteruskan pengguna: penyusutan korpus terjadi karena banyak citra sampul berkualitas buruk dan tidak dapat dilabeli; alasan itu pernah disampaikan. Tidak lagi menyatakan alasan penyusutan belum dijelaskan.

## Ruang Lingkup
- `docs/revisi-ii/CORPUS_HISTORY.md`, catatan klarifikasi, generator audit/report dan tiga notebook delivery revisi R1.
- Delivery lama dan ZIP yang sudah diserahkan dipertahankan; versi baru `delivery/HASIL_REVISI_JOY_20261102_R1/`.
- Tidak mengubah label, prediksi, fold, metrik, checkpoint atau mengisi agreement manusia.

## Langkah
1. Simpan keterangan pengguna dengan atribusi Joy dan tanggal penerimaan, tanpa mengarang tanggal komunikasi terdahulu atau rincian per sampul.
2. Pisahkan alasan umum eksklusi yang sudah diklarifikasi, dokumentasi per ID yang belum tersedia, dan agreement dua anotator yang tetap belum dihitung.
3. Perbarui source/report, tracker R23/R6, draf naskah, notebook dan panduan dalam versi delivery baru.
4. Periksa konsistensi teks dan pastikan seluruh metrik/prediksi sama; catat changelog serta manifest versi baru.

## Risiko & Asumsi
- Pesan menyebut sekitar1.000/700-an. Angka spesifik1.040/740 berasal dari PDF/dataset, bukan rincian baru yang dikonfirmasi pesan ini.
- Tidak menambahkan kriteria seperti resolusi/blur/crop atau keputusan per ID yang tidak diberikan Joy.
- Kualitas citra buruk berbeda dari sengketa label atau ketidakpastian semantik. Tidak menganggap sampel sengketa sengaja dibuang.
- R23 tidak ditutup seluruhnya karena agreement antaranotator masih memerlukan dua set anotasi manusia independen.

## Verifikasi
- Narasi menyebut alasan kualitas citra dengan atribusi yang benar dan mengakui penjelasan sebelumnya menurut Joy.
- Tracker tidak lagi menagih alasan umum sebagai belum diberikan; kebutuhan agreement dan dokumentasi rinci dipisahkan.
- Dataset/prediksi/metrik dan file model identik dengan delivery sebelumnya; notebook tidak mempunyai error output.

## Hasil verifikasi
- Catatan Joy disimpan dengan atribusi; angka perkiraan dibedakan dari jumlah pada dokumen/dataset. R23/R6 mengakui alasan umum sudah dijelaskan.
- Riwayat korpus, draf naskah dan jawaban revisi konsisten; notebook01/03 memuat klarifikasi pada output/teks. Ketiga notebook lulus Run all lokal tanpa perubahan source sel kode.
- Dataset, prediksi, seluruh hasil analisis dan lampiran model identik dengan versi sebelumnya. Tidak ada label atau metrik diubah. Status global tetap19selesai teknis/9terbuka karena agreement dan bukti lainnya belum tersedia.
