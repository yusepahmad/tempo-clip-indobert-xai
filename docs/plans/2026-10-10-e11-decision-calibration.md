# E11 kalibrasi probabilitas dan keputusan Macro-F1

**Tanggal:** 2026-10-10
**Status:** done

## Tujuan
Menguji penyesuaian keputusan perkelas pada representasi E06 untuk memperbaiki Macro-F1, terutama kelas minoritas, tanpa mengubah label atau memakai outer-test untuk tuning.

## Ruang Lingkup
- `DEMO_XAI_745_FULL/01_notebook/e11_decision_calibration.py`, salinan learn, `04_hasil_eksperimen/e11_decision_calibration/`, plan/changelog/bukti.
- Reuse fitur beku dan pilihan keluarga/parameter E06 berdasarkan skor inner setiap outerfold. Tidak memakai skor outer E06 untuk seleksi.
- Satu workerCPU/BLAS1; tidak memakai GPU, mengubah produksi/data, atau mengganggu E07/E08.

## Langkah
1. Validasi hash/ID dan split baseline. Untuk setiap outerfold, pilih keluarga E06 dari skor inner lalu baca parameter modelnya; scaler tetap di Pipeline.
2. Gunakan CalibratedClassifierCV sigmoid, cv3, ensemble=False. Cross-fit calibrator pada outer-training lewat tiga fold lagi sehingga probabilitas tuning tidak dihasilkan model yang fit pada sampel targetnya.
3. Mulai bias log-probabilitas nol; coordinate search tiapkelas di[-1,1] langkah0,125, maksimal5putaran, hanya meningkatkan Macro-F1 training cross-fit. Semua aturan ditetapkan sebelum melihat hasil outer.
4. Fit calibrator seluruh outer-training, bekukan bias, evaluasi outer-test sekali. Simpan kontrol argmax probabilitas dan keputusan adjusted,740 OOF, probabilitas, indeks/crossfitfold/parameter/bias/perkelas.
5. Hitung ulang skor dan cocokkan ID/fold/hashes. Hasil utama memakai prosedur adjusted yang sudah ditentukan, tidak memilih kontrol dari skor outer.

## Risiko & Asumsi
- Bias dapat overfit training cross-fit atau kalibrasi mengubah ranking yang sudah baik; tidak menjamin peningkatan0,5423/target0,70.
- Parameter/family E06 telah dipilih memakai outer-training yang sama. Cross-fitting untuk bias bersyarat pada pilihan itu, sehingga skor training bukan estimasi independen seluruh seleksi; outer-test tetap tidak terlibat dalam pembelajaran apa pun.
- Seluruh scaler berada dalam estimator yang dikalibrasi, termasuk fold kalibrasi. Sigmoid dipilih tetap; isotonic tidak diuji pada data kecil.

## Verifikasi
Finite probabilitas, jumlah perbaris1, urutan kelas cocok; setiap training crossfit ID bukan outer-test;740 target unik/splitbaseline. Resume hanya jika protokol/hash sama. Kompilasi dan PID/log, lalu audit OOF/manualscore dan provenance bias.

## Referensi
https://scikit-learn.org/1.7/modules/generated/sklearn.calibration.CalibratedClassifierCV.html

## Penerapan dan audit hasil
- Kompilasi lokal/server lulus; proses tmux `tempo-e11` mencapai COMPLETE. Laporan adjusted OOF0,5436173125, kontrol raw0,5218560098.
- Salin JSON/CSV/log tanpa lock ke `docs/server-recovery/2026-10-10/e11_decision_calibration/`; audit740 OOF, probabilitas/bias, training crossfit IDs/folds/diagnostik dan hash salinan. Simpan verification.json setelah lolos, sebelum menetapkan hasil terverifikasi.
- Audit selesai: manual adjusted Macro-F1 **0,5436173125461431**, raw0,521856009819245;740 ID/label/fold cocok dataset/E04. Bias terbatas sesuai grid, keputusan outer dapat direkonstruksi dari probabilitas+bias, diagnostik training cocok, seluruh592 training ID per fold bebas outer-test, crossfitfold tepat seed1042, family/parameter sesuai inner E06. Empatbelas berkas salinan cocok SHA256; bukti verification.json.
- Naik tipis0,00129 dari E06, belum target0,70 dan belum bukti kenaikan generalisasi yang meyakinkan. Model produksi tidak berubah; E07/E08 dan full E10 berikutnya tetap diperlukan.
