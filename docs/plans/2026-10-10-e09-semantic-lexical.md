# E09 fusi fitur semantik dan leksikal

**Tanggal:** 2026-10-10
**Status:** done

## Tujuan
Menguji informasi kata/karakter bersama representasi E5 deskripsi+sumber/alasan yang mencapai OOF0,5423, untuk mendekati target Task2 Macro-F1 minimal0,70.

## Ruang Lingkup
- `DEMO_XAI_745_FULL/01_notebook/e09_semantic_lexical.py`, salinan learn, output `04_hasil_eksperimen/e09_semantic_lexical/`, plan/changelog dan bukti hasil.
- Embedding E06 beku, teks E01 serta judul/teks asli. Tanpa deskripsi/mapping anotator dan tanpa modifikasi dataset/label/model produksi.
- CPU satu worker/BLAS1 di learn; tidak memakai GPU atau mengganggu kernel E07/E08.

## Langkah
1. Validasi hash NPZ/CSV/E01 dan740 ID embedding; split baseline integer Task1 seed42.
2. Di dalam Pipeline, fit StandardScaler embedding semantik dan TF-IDF word/char+TruncatedSVD128 hanya pada inner-training; normalisasi perblok.
3. Inner3fold memilih bobot leksikal0/0,5/2/8, SVC RBF C1/10/100, gamma scale/1, dan classweight none/balanced. Nol adalah kontrol semantik dalam protokol yang sama; tidak memilih bobot memakai outer-test.
4. Jalankan5 outerfold, satu proses terkunci, cache preprocessing/checkpoint per-fold dengan hash protokol. Simpan740 OOF, per-fold/per-kelas/confusion matrix.
5. Hitung ulang skor, validasi ID/label/fold dan catat hasil aktual.

## Risiko & Asumsi
- SVD dapat membuang kata langka dan fusi belum tentu memperbaiki E06.
- Setiap preprocessing yang mempelajari data harus berada di GridSearchCV Pipeline; embedding pretrained tetap beku dan bebas label.
- Banyak eksperimen pada OOF yang sama tetap memiliki bias seleksi riset; hasil tidak otomatis menjadi bukti generalisasi independen.

## Verifikasi
Assert hash/ID/shape/finite; preprocessing hanya fit indeks training yang diterima pipeline; skor final dari740 target unik, fold sama baseline. Kompilasi, verifikasi PID/log, lalu hitung ulang Macro-F1 dan cocokkan JSON/CSV.

## Penerapan awal
- Skrip dikompilasi lokal/server dan aktif dalam tmux `tempo-e09` di server`.31`, PID1493765. Validasi data/embedding/E01 lolos dan protocol.json tertulis; belum ada skor OOF lengkap.
- Semua bobot teks termasuk kontrol0 dipilih hanya lewat inner-CV. E08 satu core tetap aktif, sehingga total eksperimen CPU ini dibatasi dua worker tunggal; E07 full tetap RUNNING.

## Penyelesaian dan audit
- Proses mencapai COMPLETE dengan skor laporan0,5265301784. Salin JSON/CSV/log (tanpa cache) ke `docs/server-recovery/2026-10-10/e09_semantic_lexical/`; audit manual740 OOF/hash/ID/label/fold dan simpan verification.json sebelum menetapkan hasil final.
- Audit selesai: Macro-F1 manual0,5265301784475923 cocok laporan dalam toleransi1e-12;740 ID unik/label/fold cocok dataset/E04, checkpoint setiap fold cocok prediksi, hash source sesuai protocol, sembilan berkas salinan cocok SHA256 server. Bukti `verification.json`.
- Bobot leksikal inner terpilih2/8/0,5/0,5/2 per fold. Hasil belum mengalahkan E06 0,5423; model produksi tetap. E07/E08 dan full E10 berikutnya menjadi pekerjaan lanjutan.
