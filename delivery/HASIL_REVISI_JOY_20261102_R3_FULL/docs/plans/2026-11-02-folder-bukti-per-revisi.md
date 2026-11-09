# Folder Bukti untuk Setiap Revisi yang Selesai

**Tanggal:** 2026-11-02
**Status:** done

## Tujuan
Memudahkan klien/pembimbing mencocokkan bagian “Bukti yang diserahkan” di PDF dengan berkas nyata. Sediakan folder bernama R18, R19, dan seterusnya untuk19butir yang berstatus selesai teknis, lengkap dengan bukti dan panduan baca.

## Ruang Lingkup
- Script builder/verifier baru di `DEMO_XAI_745_FULL/01_notebook/revisi_ii/`.
- Delivery baru `delivery/HASIL_REVISI_JOY_20261102_R2/BUKTI_PER_REVISI/`, ZIP lengkap R2 dan ZIP bukti ringan terpisah.
- `CHANGELOG.md`, plan ini, dan panduan delivery diperbarui.
- Versi R0/R1/ZIP lama tidak ditimpa. Dataset, label, fold, prediksi, metrik, source sel kode notebook, checkpoint dan status19selesai/9terbuka tidak diubah.

## Langkah
1. Ekstrak requirement “Bukti yang diserahkan” per R18–R36 dari PDF asli dengan batas heading yang benar; butir Agustus dirujukkan ke bagian Revisi II terkait tanpa mengaku dokumen asli ditemukan.
2. Petakan19butir selesai ke berkas nyata: CSV, penetapan model, perbandingan terfilter, source/JointLoss, grafik, provenance, penjelasan augmentasi, draf naskah/referensi/etika.
3. Buat folder langsung `BUKTI_PER_REVISI/R18`, `R19`, dst; nama berkas bermakna, README dan HTML berisi permintaan, checklist, source/hash dan lokasi notebook. Buat indeks seluruh28butir dan daftar9yang belum ditutup.
4. Sertakan file bukti utama secara fisik, bukan sekadar menunjuk folder lain. HTML notebook dan PDF sumber menjadi referensi bersama dalam ZIP bukti agar tetap dapat dibaca terpisah dari paket lengkap.
5. Verifikasi36baris R18/R19, empat prediksi740baris pada R28, pasangan uji/ID/task per tabel, kesamaan nilai CSV terfilter dengan canonical, keberadaan/hash seluruh bukti serta link lokal HTML. Tidak membuat skor manusia atau hasil back-translation yang tidak pernah dilakukan.
6. Buat delivery R2 dan ZIP bukti saja; verifikasi manifest/SHA256/CRC serta kesamaan input/analisis/notebook/model dengan R1. Catat perubahan aktual ke changelog.

## Risiko & Asumsi
- Status Selesai berarti materi teknis tersedia sesuai tracker, bukan persetujuan dosen. Butir terbuka tidak diberi folder seolah semua buktinya lengkap.
- Audit30back-translation pada R30 diberi keterangan tidak berlaku karena metode tersebut tidak digunakan, dengan source/protokol sebagai bukti, bukan30contoh buatan.
- Empat prediksi yang diminta R28 ditata sebagai majority, image-only, text-only supporting, multimodal pada keluarga baseline yang sama; kontrol E42-family disertakan terpisah dengan protokol yang jelas.
- Bootstrap/McNemar dipertahankan sesuai implementasi: McNemar menguji akurasi, bukan Macro-F1. Tidak menjalankan training atau menghitung ulang hasil hanya untuk mengubah format bukti.
- ZIP bukti ditujukan untuk pembacaan/audit; reproduksi Run all memakai paket lengkap karena input/runtime bersama tetap berada di sana.

## Verifikasi
- Tepat19folder R yang semuanya sesuai status Selesai, tepat28baris indeks dan9butir terbuka.
- Setiap requirement/checklist menautkan file yang benar-benar ada dan berhash; setiap subset CSV benar-benar berasal dari canonical.
- Notebook dan source analisis/data/model identik dengan R1. Validator paket canonical tetap lulus.
- ZIP lengkap dan ZIP bukti memiliki CRC dan checksum sah; link HTML internal menuju berkas yang ada setelah ekstraksi.

## Hasil aktual
- Selesai19folder R untuk19butir selesai teknis,139berkas bukti nyata, indeks28butir dan daftar9terbuka. Setiap folder memiliki README, BUKA_BUKTI.html, manifest asal/hash dan tautan menuju section notebook.
- R18/R19 masing-masing36baris kandidat; R28 memuat empat predictions.csv utama masing-masing740ID, ditambah kontrol tail yang dipisahkan. Semua ID/truth/fold cocok canonical.
- Lima belas tabel subset cocok dengan CSV canonical;226tautan lokal ke file/anchor terverifikasi. ZIP bukti lulus CRC/checksum dan diperiksa kembali setelah ekstraksi terpisah tanpa paket lengkap.
- Notebook, dataset/prediksi, analisis dan lampiran model tetap identik dengan R1 (186file inti diperiksa); tidak ada training, relabeling atau perubahan skor/status.
- Browser untuk QA visual tidak tersedia pada sesi ini. Verifikasi tampilan dilakukan terbatas pada struktur HTML dan pemeriksaan navigasi/file setelah ekstraksi; tidak diklaim ada screenshot browser baru atau kelulusan Colab.
- Catatan back-translation R30 menjelaskan metode tidak digunakan; tidak dibuat30contoh buatan. Status19selesai teknis/9terbuka tetap mengikuti tracker R1.
