# R32 — paket analisis portabel

Turunan R3 FULL untuk Run all analisis pada CPU. Semua notebook, prediksi, split, evaluator, bukti dan output tetap disertakan. Lampiran checkpoint/cache training, kunci privat koordinator dan ZIP pembagian penilai tidak disertakan karena tidak diperlukan untuk Run all analisis. Ini bukan paket untuk melatih ulang model.

Jalankan `python tools/run_clean_notebooks.py --root . --output /lokasi/hasil-baru`. Folder output harus belum ada. Untuk Colab, buka COLAB_RUN_ALL.ipynb pada paket tindak lanjut dan unggah ZIP analisis saat diminta; tidak memerlukan Drive atau GPU.

Bukti Colab belum ada sampai notebook benar-benar dijalankan pada Colab dan laporan RUNTIME_VERIFICATION.json mencatat colab_verified=true. Ambil screenshot sel ringkasan hasil pada Colab. Kelulusan lokal dicatat terpisah.
