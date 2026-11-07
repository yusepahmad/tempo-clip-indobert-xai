# Konteks dipulihkan dari server

Diambil 10 Oktober 2026 dari `yusep@10.12.1.31:/home/yusep/workspace/learn/DEMO_XAI_745_FULL`.
524 berkas catatan, skrip dan bukti hasil disalin; seluruh SHA256 sesuai `RECOVERY_SHA256.json`. Source aplikasi lokal tidak ditimpa. Kredensial, environment, cache dan bobot tidak diambil. ZIP delivery tetap di server. Angka berikut berasal dari bukti historis, bukan pengujian ulang hari ini.

## Status demo terakhir — 6 Oktober
- R5 selesai: peta utama gabungan tiga task, peta task pilihan terpisah.
- Narasi ringkasan/penjelasan, OCR urutan layout, unggah ulang, pembatalan analisis, validasi input dan perbaikan frontend/backend sudah diterapkan.
- Paket `learn/dist/TEMPO_XAI_DELIVERY_WEEK3_20261006.zip` tersedia di server (sekitar 109 MB).
- Instalasi bersih Linux: 70 test Python, 13 frontend, 4 JS, smoke Chromium desktop/mobile 94/94 lulus.
- Baseline tetap dipakai: Macro-F1 Task1/2/3 = 0,438 / 0,320 / 0,276. Fine-tuning Kaggle = 0,5139 / 0,2461 / 0,3699; Task2 turun, checkpoint belum diintegrasikan.
- OCR judul versi terakhir 47/60 dan 41/60; kedua set ikut dipakai memperbaiki kode sehingga optimistis. Foto dosen 2/3 tepat. Target usulan 80% belum tercapai. R4 atribusi GULA-GULA tetap bergantung input dan belum sepenuhnya tertutup.
- Terbuka: Windows bersih, Firefox/Safari, uji manusia, OCR, E01/E02, integrasi checkpoint, autentikasi.

Sumber utama: [status revisi](docs/STATUS_REVISI_20261006.md), [changelog server](CHANGELOG.md), [handoff](docs/HANDOFF_SERVER.md).

## Pekerjaan paling akhir — E01, 8 Oktober
- Tujuan: meningkatkan Task2 melalui deskripsi literal ilustrasi dari Qwen3-VL-8B-Instruct di Kaggle, lalu evaluasi OOF dengan split baseline.
- Kode `01_notebook/e01_vlm.py`, `e01_evaluasi.py` dan `kaggle_e01/` sudah disiapkan.
- Uji alur memakai deskripsi anotator: Task2 TF-IDF 0,531; fusi 0,501; baseline LR 0,321. Ini bukan hasil VLM. Deskripsi NON_METAFORA kosong 83/83, sehingga rujukan anotator bias; rerata F1 enam kelas metafora sekitar 0,46.
- Smoke v1 hang >2 jam tanpa log; penyebab belum diketahui. API masih RUNNING pada 8 Okt 18:20 dan kuota hampir habis.
- v2 sudah memiliki watchdog 40 menit smoke/600 menit full, log tahap, larangan offload CPU/disk, timeout pip. Uji watchdog lulus. v2 belum di-push menurut catatan terakhir.
- Kuota API saat itu 6 jam/periode; refresh tercatat 10 Okt 00:00 dengan zona tidak dinyatakan. Status/kuota saat ini BELUM diperiksa. Batas full 600 menit melebihi kuota 6 jam dan perlu disesuaikan setelah smoke.
- Langkah berikut: cek status sesi/kuota read-only, jalankan smoke v2 bila sesuai otorisasi, laporkan kualitas/durasi, baru putuskan full.

Sumber: [plan E01 dan keputusan user](docs/plans/2026-10-08-e01-vlm-dua-tahap-kaggle.md), `04_hasil_eksperimen/e01_vlm/`.

## Batas keputusan sebelumnya
- Resource eksperimen hanya di dalam `learn`; jangan menyentuh service VLM/LLM server lain atau cache di luar learn.
- Bobot VLM diunduh di kernel Kaggle, bukan server ini.
- Full E01 memerlukan persetujuan user setelah hasil smoke dilaporkan.
- Jangan mengganti baseline atau label dataset tanpa bukti evaluasi.

## Kondisi yang diamati hari ini
SSH berhasil. Tidak ada sesi tmux `tempo-ui` atau `tempo-unduh` dalam daftar saat diperiksa; HTTP tidak diuji sehingga status aplikasi belum dipastikan. Tidak ada training atau push Kaggle yang dijalankan.
