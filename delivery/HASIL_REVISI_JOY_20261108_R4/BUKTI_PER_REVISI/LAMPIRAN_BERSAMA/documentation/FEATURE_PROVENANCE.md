# Provenance fitur E01

Generator lengkap, prompt, model/revisi, metadata dan hash kedua keluaran ditemukan dan cocok dengan worker E14. Gold task tidak diinterpolasi ke prompt; kolom `domain` pada zeroshot adalah keluaran klasifikasi model, bukan gold. Namun generator membaca CSV berlabel secara penuh ke proses. Karena itu tuntutan literal “CSV berlabel tidak pernah masuk proses” tidak terpenuhi. Bukti yang tersedia mendukung pemisahan field prompt, bukan isolasi proses formal. Tanggal salinan recovery bukan waktu penciptaan asli.

Lihat `FEATURE_PROVENANCE.json` dan 20 contoh dengan seed tetap. Jika diperlukan pembuktian isolasi proses yang lebih kuat, gunakan input allowlist berkas baru tanpa label dan jalankan pembangkitan ulang terpisah; hasilnya menjadi fitur versi baru. Keberadaan nama domain pada keluaran prediksi saja tidak membuktikan kebocoran gold.


## Pembaruan 8 November 2026

Audit input allowlist tanpa gold dijalankan ulang: 740 ID dan 742 hash lulus; guard Python menolak pembacaan CSV gold asli. Ini bukti prospektif, bukan isolasi OS atau bukti proses historis. Regenerasi fitur tidak dijalankan: tanpa keputusan metodologis, mengganti fitur akan mengubah eksperimen dan tidak memulihkan timestamp lama. Pemeriksaan 20 contoh oleh manusia disediakan pada UNTUK_MANUSIA/R22_REVIEW_MANUSIA_20.csv.
