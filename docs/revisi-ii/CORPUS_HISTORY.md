# Riwayat korpus dan anotasi

Dataset canonical yang ditemukan: 740 ID unik, SHA-256 `cba20f8250bcb59481ed2d3d7d5d42fb8242c96a7ba2d11a2cd02ad80862961a`. Eligibility: {'eligible_sociopolitical': 740}. Tidak ditemukan korpus awal 1.040 baris atau log 300 keputusan eksklusi per ID. Kolom `annotator_confidence`, deskripsi dan mapping note adalah satu set anotasi yang sudah tergabung; tidak tersedia dua set label independen untuk menghitung kappa manusia. Jangan menganggap ketiadaan data awal membuktikan sampel sengketa dibuang. Alasan umum penyusutan telah diklarifikasi; dokumentasi rinci per ID dan analisis sensitivitas belum dapat direkonstruksi.

Tindakan siap pakai: paket dua anotator untuk 150 sampul acak, serta audit 60 kasus kelas penampung. Kappa tidak dihitung dari prediksi AI sebagai pengganti manusia. Setelah anotasi nyata tersedia, jalankan `human_agreement.py`.

## Klarifikasi dari Joy — diterima 2 November 2026

Menurut keterangan Joy yang diteruskan pengguna, jumlah korpus berkurang karena banyak citra sampul Tempo berkualitas buruk dan tidak dapat dilabeli. Joy menyatakan alasan ini telah disampaikan sebelumnya. Dengan demikian, **alasan umum penyusutan sudah dijelaskan** dan tidak lagi dicatat sebagai alasan yang belum diberikan.

Pesan menggunakan angka sekitar 1.000 dan 700-an. Angka spesifik 1.040 bersumber dari dokumen revisi/proposal; jumlah 740 ID unik dapat diperiksa pada dataset canonical. Pesan ini tidak memberikan tanggal komunikasi sebelumnya, daftar gambar yang dikeluarkan, kriteria teknis terukur, atau keputusan per ID; rincian tersebut tidak direka.

Kualitas citra buruk berbeda dari sengketa label atau ketidakpastian interpretasi semantik. Tidak ada kesimpulan bahwa sampel sengketa sengaja dibuang untuk meningkatkan metrik. Bila dokumentasi seleksi asli masih tersedia, gunakan untuk melengkapi keterlacakan; ketidaktersediaannya tidak meniadakan penjelasan Joy.

Bagian R23 tentang **kesepakatan antaranotator** tetap terpisah. Pada 10 November 2026, dua set label manusia independen untuk 150 sampel telah diterima: kappa Task 1/2/3 sebesar 0,5721/0,9498/0,9430. Disagreement mempertahankan label kanonik sebagai keputusan adjudikasi konservatif. Penjelasan penyusutan tidak menggantikan riwayat eksklusi per-ID; ketidaktersediaan riwayat tersebut dilaporkan sebagai keterbatasan. Catatan sumber: `R23_KLARIFIKASI_JOY.json` dan `delivery/ADDENDUM_HASIL_MANUSIA_20261110/`.
