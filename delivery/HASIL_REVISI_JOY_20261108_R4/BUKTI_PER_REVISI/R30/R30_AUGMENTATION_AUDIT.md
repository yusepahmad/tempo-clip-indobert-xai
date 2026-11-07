# Audit augmentasi

AUG_SELECTED historis dipilih pada inner fold, bukan berdasarkan pemenang outer. Karena itu boleh kalah dari A01 pada outer; menggantinya setelah melihat outer justru memperkenalkan pemilihan pada test. A00/A01/A02/A03 lama dipertahankan.

Source lama memang memakai rotasi±2derajat pada moderate. Revisi baru menghapus rotasi dengan tetap mengonsumsi draw RNG yang sama, sehingga brightness/contrast/JPEG/noise tidak ikut berubah akibat pergeseran RNG. Tidak ada cropgeometris pada transform augmentasi baru. Model/resize-native SigLIP2 tetap dicatat terpisah dari augmentasi.

Kontrol baru menggunakan35 epoch/head192 sama, tepatntrainingdraws/epoch, pilihan50%clean/50%fixedaugmented, samplerjointinverse-sqrt hanya pada training; semua validation/test bersih. Pemilihan pipeline memakai innermean Macro-F1. Protokol baru memperbaiki juga jumlah paparan/update yang sebelumnya bertambah karena clean+aug diduplikasi. Karena lebih dari satu perbaikan protokol, perbandingan legacy versus baru bukan isolasi rotasi tunggal.

Tidak ditemukan back-translation dalam pipeline augmentasi yang benar-benar dijalankan; audit30contoh tidak berlaku pada metode yang tidak digunakan. Jangan membuat 30 terjemahan baru seolah-olah bukti historis.
