# Revisi Langsung Tiga Notebook dan Bukti Screenshot

**Tanggal:** 2026-11-02
**Status:** done

## Tujuan
Memasukkan jawaban revisi langsung ke 01_baseline.ipynb, 02_experiments.ipynb dan 03_final_comparison.ipynb, khususnya pernyataan eksplisit arsitektur Multi-Task Learning CLIP–IndoBERT dengan Joint Loss pada R18. Menyertakan screenshot delivery historis dan bukti revisi yang dapat dibaca di notebook tanpa membuka dokumen lain.

## Ruang Lingkup
- Generator notebook, dokumen identitas arsitektur dan builder paket pada `DEMO_XAI_745_FULL/01_notebook/revisi_ii/`.
- Bukti baru `docs/revisi-ii/notebook_evidence/` dan delivery berversi baru `delivery/revisi_ii_20261102/`.
- Plan induk dan `CHANGELOG.md` diperbarui setelah pekerjaan nyata.
- Screenshot lama dibaca/disalin dengan source/hash dan label historis. PDF sumber serta delivery lama tidak ditimpa. Label, fold, model aktif dan checkpoint tidak diubah.

## Langkah
1. Cocokkan bagian R18 yang ditandai pengguna terhadap PDF dan source/checkpoint E42.
2. Tambahkan pernyataan identitas, alur arsitektur, rumus Joint Loss, konfigurasi per fold, pemetaan kandidat dan batas perbedaan dengan demo web.
3. Simpan screenshot delivery lama beserta provenance. Render halaman R18 dari PDF asli sebagai kutipan visual tanpa mengaku sebagai screenshot beranotasi milik pengguna.
4. Tampilkan materi revisi R18 langsung pada ketiga notebook; materi lengkap pada notebook02/03. Tambahkan gambar terlampir di notebook agar tetap terlihat ketika berkas dipindah.
5. Buat indeks R18–R36 dan sembilan butir Agustus ke notebook/heading terkait. Status manusia tetap terbuka. Ambil screenshot tampilan revisi aktual bila browser dapat diakses.
6. Build paket baru, Run all tiga notebook, verifikasi identitas/loss terhadap source/checkpoint, attachment/hash/CRC dan hasil ekstraksi.
7. Catat hasil nyata ke changelog dan laporkan lokasi notebook/paket terbaru.

## Risiko & Asumsi
- Kata Joint Loss berarti jumlah loss tiga task; tidak berarti learned uncertainty weighting. E42 menggunakan class-weighted cross entropy dan bobot task tetap yang dipilih pada inner CV.
- Detail konfigurasi harus diambil per fold; jangan mengklaim satu bobot task untuk semua fold jika checkpoint berbeda.
- Screenshot historis bukan bukti versi terbaru atau kelulusan Colab. Screenshot dekoratif tidak menggantikan source/prediksi/tes.
- Gambar yang dilampirkan pengguna terlihat di percakapan tetapi belum mempunyai path lokal; bukti sumber diambil dari PDF asli dan screenshot final yang tersedia di workspace, tanpa merekonstruksi lingkaran/highlight pengguna.
- Sisa R21/penilaian manusia/provenance/Colab tidak dianggap selesai akibat penambahan screenshot. Scope utama turn ini memperjelas notebook dan bukti visual.

## Verifikasi
- Ketiga notebook memuat identitas model dan jawaban R18 sebagai markdown langsung, bukan hanya referensi dokumen.
- Rumus, konfigurasi dan checkpoint hash cocok dengan source/metadata E42; tiga task/kategori10/7/8 dan shared layer jelas.
- Screenshot historis diberi tanggal/source/hash dan keterangan; attachment valid dan render terbaca.
- Tiga notebook dieksekusi tanpa error. Manifest, ZIP CRC dan validator metrik lulus dari ekstraksi.

## Penyesuaian berdasarkan instruksi pengguna
- Pengguna meminta satu folder hasil revisi yang dapat dikerjakan sekarang dan langsung selesai. Target delivery `delivery/HASIL_REVISI_JOY_20261102/` mencakup tiga notebook, screenshot, sumber/hasil analisis, paket manusia dan lampiran model. Tidak menunda delivery ini demi pelaksanaan penilaian manusia atau training QLoRA lima fold yang belum dilakukan.
- Hasil zero-shot yang job-nya sudah COMPLETE dikoleksi/verifikasi sebelum dimasukkan bila kontraknya lulus; tidak menjalankan eksperimen training baru dalam scope delivery segera ini.

## Hasil aktual
- Folder `delivery/HASIL_REVISI_JOY_20261102/` selesai disusun dengan tiga notebook terisi, HTML, source/data/prediksi, instrumen manusia dan lampiran model.
- R18 ditulis langsung di ketiga notebook; notebook02 memuat rumus, alur2304→256→tigahead dan konfigurasi lima fold. Metadata/hash checkpoint cocok; fold5 memakai1:1:1, fold1–4 memakai1:2:2.
- Enam bukti visual: tiga screenshot20Oktober, render halaman5 PDF, dua screenshot aktual browser lokal R18/JointLoss. Empat gambar sumber/historis menjadi attachment notebook; dua screenshot baru berada pada folder screenshots.
- Zero-shot basic/rich740 dikoleksi/diverifikasi; kelompok canonical hanya dipakai diagnostik dan diberi label no-training. QLoRA basic full tetap belum dilakukan, tidak diisi hasil smoke.
- 19tes lokal lulus. Run all tiga notebook lulus lokal dan pada ekstraksi ZIP di venv terpisah (18,82/18,54/19,66detik, tanpa error). Counter independen memverifikasi231baris metrik/77sumber;1296hash kandidat cocok sebelum/sesudah Runall.
- Tampilan R18, tabel, empat rumus MathJax dan gambar diperiksa di browser lokal; tidak ada overflow horizontal. Uji ini bukan klaim Colab.
- Status global tetap19/28butir selesai teknis dan9terbuka. Plan induk tetap in-progress; yang diselesaikan plan ini adalah integrasi notebook/screenshot dan delivery segera yang diminta pengguna.
