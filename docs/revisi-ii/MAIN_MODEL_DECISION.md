# Penetapan model utama

Identitas model penelitian: **E42 (`e42_tail_grid`)**, alias M00. Macro-F1 Task1/2/3: 0.525483/0.395560/0.403398; rerata 0.441480. Kandidat ini memenuhi cabang CLIP–IndoBERT, satu shared layer dan tiga head. IndoBERT dua blok terakhir fine-tuned, sehingga istilah seluruh encoder beku tidak tepat. Loss merupakan jumlah CE berbobot tetap dengan class weights training-only, bukan learned uncertainty Kendall.

Pemilihan ini dilakukan setelah kandidat dievaluasi pada korpus yang sama. Angka merupakan hasil seleksi post-hoc pada repeated-corpus internal CV dan berpotensi optimistis. Rerata Macro-F1 berbobot sama antar task dipakai untuk keputusan ini; per-task menjadi laporan utama dan minimum hanya diagnostik. Alias/duplikasi prediksi tidak dihitung sebagai bukti eksperimen independen.

Web historis CLIP-B32 tetap demo historis terpisah; bukan inferensi model E42. Penjelasan E42 harus memakai checkpoint outer fold yang sesuai atau refit deployment baru yang diverifikasi. Qwen E14 adalah pembanding dengan input lebih kaya, bukan model utama atau bukti ablasi arsitektur yang terisolasi.
