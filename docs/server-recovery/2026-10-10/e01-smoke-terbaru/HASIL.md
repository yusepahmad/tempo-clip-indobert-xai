# Hasil smoke E01 diperiksa 10 Oktober 2026

Sumber: https://www.kaggle.com/code/yusepmuhamadzazuli/tempo-e01-vlm-smoke/log dan output API Kaggle. Status COMPLETE.

- Qwen3-VL-8B-Instruct, revision 0c351dd01ed87e9c1b53cbc748cba10e6187ff3b, fp16, 2×Tesla T4.
- 12/12 deskripsi dan 12/12 prediksi zero-shot; ID unik dan set ID kedua output cocok.
- 0 keluaran ditandai rusak, 0 label kosong, 0 JSON tidak valid. Metadata selesai=true.
- Muat model 124,5 detik; inferensi rata-rata 9,36 detik/sampel. Log mencapai hasil akhir sekitar detik 289 dan konversi notebook sekitar detik 298.
- Proyeksi inferensi 740 sampel: 1,92 jam, belum termasuk seluruh overhead dan variasi panjang keluaran. Bukan durasi full yang sudah diukur.

## Penilaian
Smoke berhasil secara teknis. Belum membuktikan peningkatan Macro-F1 Task2; perlu full output lalu evaluasi OOF sesuai plan.
Deskripsi dapat dibaca, tetapi sampel TMP-EC1AFE264B60 memasukkan tulisan NARKOBA/KAMPUNG/CERITA DARI meski prompt A meminta mengabaikan teks. Zero-shot TMP-BB454CBBB59B memakai kata judul "selera" sebagai sumber. Kepatuhan deskripsi literal dan ketergantungan pada judul perlu dilaporkan. Ketepatan objek belum diverifikasi terhadap gambar asli.

Output tidak memuat tahap.log atau field watchdog baru; jangan menganggap run ini pasti memakai kode v2 tanpa metadata versi kernel. Status v1 macet dari catatan 8 Oktober kini sudah tidak mewakili hasil terbaru.

Full run belum dijalankan. Sesuai keputusan user dalam plan E01 8 Oktober, full menunggu persetujuan setelah smoke dilaporkan. Kuota saat ini belum diperiksa; batas full 600 menit perlu ditinjau terhadap kuota historis 6 jam.
