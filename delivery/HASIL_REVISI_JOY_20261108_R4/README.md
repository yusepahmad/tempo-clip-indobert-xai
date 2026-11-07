# Public analysis export

Read PUBLIC_EXPORT_SCOPE.md. Coordinator-only files are kept on the original server.

# R4 ANALISIS — server .31

Baca SCOPE_ANALISIS_SERVER.md. Lampiran model opsional belum disalin.

# Revisi II Joy — R4, 8 November 2026

**19/28 selesai teknis; 9 masih terbuka.** R21 basic supporting telah dikoleksi: lima fold, 740 prediksi nyata. Permintaan literal citra+judul ditampilkan terpisah; nilainya tidak diisi dari arm supporting atau smoke. Model utama tetap E42, metrik utama Macro-F1.

- Buka MULAI_DI_SINI.html, notebook_html/ atau notebooks/. Tiga notebook berisi output tersimpan; Run all hanya menghitung analisis prediksi pada CPU, tanpa training/API.
- Tugas manusia dan berkas pengembalian: UNTUK_MANUSIA/MULAI_DI_SINI.md. ZIP individual hanya untuk penerima masing-masing. Jangan membagikan coordinator_private kepada penilai.
- Tabel R21: documentation/R21_HASIL_TERKINI.md, R21_TABEL_2X2.md dan R21_LITERAL_2X2.md. Batas konteks dan resep inner rich tetap diungkapkan.
- Ulang analisis: buat venv Python 3.10 kompatibel, pasang requirements-analysis-lock.txt; jalankan `python tools/evaluate.py --package --workspace . --output analysis`, lalu `python tools/validate_package.py --root .`.
- Colab: gunakan COLAB_RUN_ALL.ipynb dan R32_ANALISIS_PORTABEL.zip yang berpasangan dari folder R32 pendamping. Bukti Colab masih Not Evaluated sampai laporan runtime nyata serta screenshot tersedia. Akses browser Colab tidak tersedia pada sesi ini.
- Source, split, hasil, protokol dan hash disertakan. Menjalankan ulang training/XAI memerlukan bobot/cache dan lingkungan ML tersendiri. Demo web historis CLIP-B32 bukan inferensi E42.
- Seluruh paket R3 dan arsip lama dipertahankan. Tidak ada label, rating manusia, timestamp historis atau keputusan pembimbing yang dibuat agent.
