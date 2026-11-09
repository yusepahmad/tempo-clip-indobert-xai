# Verifikasi gambar asli dosen

**Tanggal:** 2026-10-05
**Status:** done
## Tujuan
Periksa tiga file WhatsApp yang ditunjuk user sebagai gambar dosen, uji OCR nyata dan perbarui tabel/bukti revisi.
## Ruang Lingkup
Script/output uji terpisah di hasil revisi_week3, tabel pemeriksaan, laporan gambar, delivery dan CHANGELOG. Gambar asli/dataset/model tidak diubah.
## Langkah
1. Baca gambar dan transkripsikan headline yang terlihat sebagai acuan pemeriksaan agen.
2. Jalankan OCR aktual, simpan blok/kandidat/skor/latensi dan exact headline setelah normalisasi.
3. Cocokkan gambar dengan korpus tanpa menyamakan judul yang cocok dengan file identik.
4. Catat hasil, kasus gagal dan keterbatasan; perbarui status sumber gambar.
## Risiko & Asumsi
Transkripsi agen bukan validasi dosen; judul diperiksa visual, supporting tidak otomatis dianggap verified. Tidak mengarang label kelas untuk unggahan.
## Verifikasi
Tiga output nyata tersimpan, acuan dan prediksi terpisah, hash/dimensi tercatat; status gambar asli tersedia menggantikan klaim belum ada.

## Hasil
GULA-GULA dan CUKAI headline tepat; WASWAS terbaca VJJASWAS dan membutuhkan koreksi. Output raw/manifest tersimpan, tabel dan laporan diperbarui. Ketiga file tidak cocok hash dataset; unggahan tidak diberi label otomatis. Tidak mengklaim evaluasi klasifikasi/XAI atau supporting lengkap selesai.
