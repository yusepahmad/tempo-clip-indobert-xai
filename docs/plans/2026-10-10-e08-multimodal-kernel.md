# E08 fusi multimodal dengan kernel nonlinear

**Tanggal:** 2026-10-10
**Status:** done

## Tujuan
Menguji informasi visual CLIP dan teks IndoBERT bersama teks VLM E01 melalui SVM nonlinear, sambil E05/E06 masih berjalan. Target tetap Macro-F1 Task2 minimal0,70; hasil E08 belum diketahui.

## Ruang Lingkup
- Skrip baru `DEMO_XAI_745_FULL/01_notebook/e08_multimodal.py`, salinan learn, output `04_hasil_eksperimen/e08_multimodal/`, plan dan changelog.
- Fitur beku dan deskripsi/prediksi E01 yang sudah tersedia; label Task2 hanya untuk supervised training/evaluasi.
- Tidak mengubah CSV, label, model produksi, kernel Kaggle aktif atau layanan di luar learn.

## Langkah
1. Validasi hash data/fitur dan kesesuaian ID E01; gunakan split baseline Task1 integer seed42.
2. Normalisasi L2 setiap modalitas per sampel; TF-IDF word/char fit hanya training melalui Pipeline.
3. Tiga keluarga: CLIP+IndoBERT, CLIP+teks VLM/asli, seluruh modalitas. Inner3fold memilih SVC C/gamma/class weight dan bobot teks. Keluarga final dipilih dari skor inner setiap outer fold.
4. Jalankan satu proses terkunci, satu job/BLAS1 dalam tmux; simpan OOF740, parameter, per-kelas, confusion matrix, hash/config.
5. Hitung ulang skor langsung dari OOF, bandingkan E04 tanpa memilih keluarga memakai skor outer-test; catat hasil aktual.

## Risiko & Asumsi
- SVM sparse nonlinear dapat lambat; cache preprocessing dibatasi ke folder eksperimen, satu job untuk membatasi CPU saat evaluator E06 berjalan.
- Normalisasi per sampel tidak mempelajari statistik populasi; TF-IDF tetap harus fit ulang di setiap inner fold.
- Gabungan fitur tidak menjamin perbaikan. Banyak eksperimen tetap memiliki bias seleksi riset; target tidak dinyatakan tercapai tanpa bukti OOF lengkap dan batas evaluasi.

## Verifikasi
Assert hash/ID/shape/finite, seluruh740 target tepat satu fold dan train/test disjoint. Simpan pilihan inner terpisah dari skor outer. Kompilasi lalu jalankan langsung; verifikasi PID hidup, keluaran740 unik dan skor ulang independen.

## Hasil penerapan awal
- Skrip dikompilasi dan diluncurkan di server `.31`, tmux `tempo-e08`, PID1206852; proses hidup dan protocol.json berhasil ditulis setelah validasi hash/ID/finite.
- Fitur CLIP740x512 dan IndoBERT740x768; satu job, BLAS1, hash skrip tersimpan dalam protocol. Resume menolak checkpoint dengan hash data/skrip atau versi sklearn berbeda.
- Belum ada skor OOF lengkap; plan tetap in-progress sampai evaluasi selesai.

## Hasil sementara terverifikasi
- Keluarga `visual_bert` selesai: Macro-F1 OOF0,35148611232002386. Perhitungan ulang dari CSV cocok dengan JSON; 740ID unik, label cocok CSV asli, split baseline cocok dan setiap fold148 sampel.
- Dua keluarga dengan teks VLM masih berjalan; skor gabungan/final E08 belum tersedia. PID1206852 diverifikasi masih aktif memakai sekitar satu core CPU.

## Penyelesaian dan audit
- Proses mencapai COMPLETE NESTED, laporan0,4805749075. Seluruh keluarga selesai; lanjut salin JSON/CSV/log tanpa cache ke `docs/server-recovery/2026-10-10/e08_multimodal/`, audit740 OOF/selection/checkpoint/hash dan simpan verification.json sebelum menetapkan hasil.
- Audit manual selesai: nested0,4805749074542595; keluarga tetap visual_bert0,3514861123, visual_text0,4734423652, visual_bert_text0,4900665564. Seluruh740 ID/label/fold dan15 checkpoint cocok, pemenang keluarga benar menurut skor inner setiap fold, sourcehash dan25 salinan SHA256 cocok. Bukti verification.json.
- Belum melampaui E06/E11; model produksi tidak berubah. E07/E10 dan E12 QLoRA menjadi pekerjaan berikutnya.
