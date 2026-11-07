# Tindak lanjut revisi — 2 November 2026

**Belum semua dapat ditutup hari ini.** Ada sembilan nomor terbuka, setara tujuh kelompok pekerjaan karena R23/R6 dan R34/R9 saling terkait. Pengguna mengonfirmasi belum memiliki dokumen Agustus, dua hasil anotator, atau lima hasil penilai. Status utama tetap 19/28 selesai teknis; bahan tambahan ini tidak mengubahnya secara otomatis.

| Butir | Yang sudah saya kerjakan sekarang | Yang masih diperlukan | Estimasi dari kondisi sekarang |
|---|---|---|---|
| R21 | Smoke lulus; full lima fold privat sudah dikirim dan RUNNING; tabel 2×2 + zero-shot dan CI kappa tersedia; collector otomatis aktif | Job selesai, verifikasi 740 prediksi dan tinjauan batas kesetaraan input | 5–9 jam sejak mulai, tanpa jaminan; collector/tabel beberapa menit setelah COMPLETE |
| R22 | 740 input tanpa kolom label, 742 file berhash, generator asli lengkap dan wrapper pembatas baca; uji menolak CSV berlabel | Bukti isolasi/timestamp runtime historis yang memang tidak direkam tidak dapat dibuat sekarang | Materi teknis tambahan selesai; regenerasi baru diperkirakan 2,5–4 jam dari log lama, lalu rerun model yang memakai fitur baru terpisah. Tidak dijalankan otomatis karena tidak akan membuktikan runtime lama |
| R23 + R6 | Paket A/B masing-masing 150 sampul, codebook, kalkulator kappa teruji, tabel pembanding kappa dan klarifikasi riwayat korpus | Dua anotator independen; catatan korpus awal/300 eksklusi per ID bila ada | Perkiraan 5–10 jam per anotator (dapat paralel), lalu 30–60 menit perhitungan/laporan setelah file lengkap; dokumentasi korpus bergantung pemilik data |
| R31 | Tabel sensitivitas/dekomposisi sudah ada; paket audit 30 LAINNYA + 30 multiple_or_other siap | Pemeriksaan dan alasan/adjudikasi manusia | Perkiraan 3–6 jam manusia, lalu 30–60 menit rekap; perubahan kelas dapat menuntut eksperimen lanjutan |
| R32 | ZIP analisis portabel; peluncur Colab; Run all dari ekstraksi pada venv baru lulus tiga notebook | Jalankan COLAB_RUN_ALL.ipynb pada Colab asli dan ambil screenshot sel ringkasan. Browser tidak terhubung pada sesi ini | Sekitar 20–40 menit setelah ada akses, termasuk upload/pip; bergantung koneksi/runtime |
| R34 + R9 | XAI aktual, kontrol buta, rubrik dan lima ZIP penilai siap; kalkulator ICC teruji | Lima penilai independen yang tidak ikut anotasi; skor dan dokumentasi partisipasi nyata | Perkiraan 1–2 jam per penilai, dapat paralel setelah orang tersedia; 30–60 menit rekap. Waktu rekrutmen belum diketahui |
| R8 | Bukti baseline/ablasi sudah tersedia di R3 FULL | Dokumen revisi Agustus asli untuk mencocokkan setiap tuntutan | Sekitar 15–30 menit pencocokan setelah dokumen diterima; waktu mendapat dokumen belum diketahui |

## Yang dapat kamu pakai sekarang

1. **R21/R21_TABEL_2X2.md** dan CSV: angka aktual; tiga sel QLoRA basic per task masih kosong sampai hasil full lulus. Basic saat ini citra + headline + supporting; CLIP rich 256 vs basic 128 token tidak disebut efek fitur murni.
2. **COLAB_RUN_ALL.ipynb** dan **R32_ANALISIS_PORTABEL.zip**: buka launcher pada Colab CPU baru, Run all, unggah ZIP saat diminta, simpan ZIP bukti runtime dan screenshot hasil. Tanpa Drive/GPU. Uji Linux baru ada pada R32_CLEAN_ENV_VERIFICATION.json dan tidak diberi label Colab.
3. **PAKET_MANUSIA/**: bagikan hanya ANOTATOR_A/B masing-masing ke dua orang berbeda; PENILAI_XAI_R1–R5 masing-masing ke lima orang di luar tim anotasi; ADJUDIKASI_60 ke pemeriksa kelas. Jangan memberi penilai paket analisis/kunci kontrol. Koordinator mencatat persetujuan dan independensi secara privat.
4. **R22_INPUT_TANPA_LABEL/** dan **tools/label_blind_bundle.py**: bahan input untuk pembangkitan versi baru. Generator lama disalin utuh; timestamp manifest adalah waktu ekspor baru, bukan timestamp E01 asli. Guard Python bukan sandbox OS. Tidak ada fitur/model lama diganti.

## Pengolahan setelah hasil manusia masuk

Letakkan jawaban asli dalam folder terpisah. Dari folder paket tambahan ini, gunakan:

```sh
python tools/human_agreement.py annotation --a /path/annotator_A.csv --b /path/annotator_B.csv --protocol /path/protocol.json --output /path/agreement.json
python tools/human_agreement.py xai --ratings /path/lima_penilai_digabung.csv --expected-template PAKET_MANUSIA/ratings_template.csv --output /path/xai_agreement.json
```

Gunakan protocol.json dari paket anotator. Gabungkan lima ratings.csv dengan rater_id tetap. Semua item/dimensi harus terisi untuk seluruh penilai. Identitas manusia/independensi tidak dapat dibuktikan hanya dari nilai CSV; koordinator harus mendokumentasikannya. File kosong ditolak dan tidak diganti nol. Template kappa manusia tidak berisi angka buatan.

## Job yang sedang berjalan

Kernel: https://www.kaggle.com/code/yusepmuhamadzazuli/tempo-revisi-ii-qwen-basic-full

Pemantau berjalan pada workspace asli, mengecek berkala dan tidak melakukan submission ulang. Jika selesai dan terverifikasi, hasil serta tabel dibuat di `delivery/R21_HASIL_FULL_20261102/`. Jika ERROR atau validasi gagal, hasil tidak dipromosikan. Snapshot job dalam paket ini tidak berubah otomatis; status live ada di workspace `DEMO_XAI_745_FULL/04_hasil_eksperimen/revisi_ii/qwen_basic_jobs/full/`.

## Batas pekerjaan

Saya dapat menjalankan eksperimen, memeriksa file, menghitung statistik, membuat tabel/naskah dan memvalidasi paket. Anotasi/penilaian manusia harus dikerjakan manusia; dokumen asli dan timestamp historis yang tidak tersedia tidak dapat saya ciptakan. Menutup seluruh sembilan butir hari ini belum realistis dari kondisi bukti saat ini.

Snapshot status: **RUNNING**, diamati 2026-11-02T07:18:47.822477+00:00. Awal preflight 13.58 WIB; rentang perkiraan selesai 18.58–22.58 WIB pada 2 November bila berjalan normal, ditambah antrean/overhead yang belum tercakup. Ini estimasi, bukan janji.
