# Metode evaluasi dan statistik

Metrik utama Macro-F1 dengan codebook label tetap (zero_division=0), disajikan per task. Rerata tiga Macro-F1 berbobot sama hanya ringkasan; minimum diagnostik. Akurasi, macro-precision/recall, Cohen kappa dan metrik per kelas disertakan. Micro-F1 single-label identik dengan akurasi dan tidak dipakai untuk memberi kesan metrik berbeda.

CI akurasi: Wilson 95%. CI Macro-F1: percentile bootstrap 2000 replikasi atas pasangan gold/prediksi, seed20261101+indeks task. Selisih macro memakai bootstrap berpasangan atas triple gold/before/after. Implementasi multinomial histogram joint ekuivalen terhadap resampling IID pengamatan, dengan kelas yang tidak muncul di replikasi tetap berada pada denominator macro.

McNemar exact dua sisi menguji selisih benar/salah, yaitu akurasi, bukan Macro-F1. Holm diterapkan ke seluruh pasangan-task yang dicantumkan dalam satu keluarga. Pasangan di keluarga baru ditetapkan dalam source evaluator sebelum tabel baru dihasilkan. CI bootstrap selisih bersifat pointwise eksploratif; jangan menganggapnya sudah terkoreksi family-wise. Tidak signifikan bukan bukti kesetaraan, dan besar selisih tidak boleh diberi p hanya dari jumlah sampel benar yang tidak berpasangan.

Seluruh inference bersyarat pada prediksi OOF tersimpan: overlap data training lintasfold, adaptive selection pada korpus sama, annotator uncertainty dan variability seed baru belum seluruhnya tercakup. Tidak ada holdout baru yang diklaim dari fold yang pernah dipakai seleksi. Kriteria keberhasilan adalah perbandingan yang terukur terhadap majority/unimodal/single-task, bukan angka0,70 tunggal. Target proposal historis tetap disebut sebagai target lama yang belum tercapai, bukan dihapus dari sejarah.

Sumber metode: [SciPy binomtest](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.binomtest.html), [SciPy paired bootstrap](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.bootstrap.html), [Dietterich1998](https://doi.org/10.1162/089976698300017197).
