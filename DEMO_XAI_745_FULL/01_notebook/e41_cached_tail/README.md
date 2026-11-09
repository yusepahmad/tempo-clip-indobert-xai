# E41: cached frozen front, trainable IndoBERT tail

Eksperimen joint MTL tiga task pada 740 sampul asli. CLIP-L14 tetap beku;
dua blok terakhir IndoBERT dan shared head dilatih bersama. Pemilihan epoch
maksimalkan minimum mean Macro-F1 tiga task pada dua inner folds. Outer test
tidak dipakai memilih epoch. Ambang keberhasilan semua task adalah 0,70.

## Evaluasi

1. `verify_cache.py` memeriksa cache sebelum latihan.
2. Smoke GPU memeriksa pembaruan tail, shared layer dan semua head.
3. Full kernel menghasilkan lima checkpoint dan OOF GPU AMP provisional.
4. Di server, jalankan `python verify_result.py CACHE_DIR GPU_OUTPUT_DIR`.
   Evaluator memeriksa source/cache/checkpoint SHA, split dan pemilihan epoch,
   kemudian melakukan forward CPU FP32 untuk seluruh 740 outer-test samples.
5. `python root_verify.py GPU_OUTPUT_DIR` menghitung ulang Macro-F1 dengan
   stdlib dan memeriksa hash artefak serta input. `check_root_audit.py` menguji
   penerimaan fixture sintetis dan penolakan metrik/target/hash yang salah.

Skor canonical memakai CPU FP32, ditetapkan sebelum hasil GPU tersedia.
Perbedaan prediksi GPU AMP dicatat tanpa memilih presisi yang memberi skor lebih
tinggi. Audit pemilihan epoch memakai trace tersimpan; seluruh latihan GPU tidak
direproduksi. Bootstrap bersifat eksploratif karena eksperimen berulang pada data
yang sama dan training folds saling beririsan.

## Kontrak rekonstruksi delivery (belum terintegrasi)

- Input teks: `headline_verified [SEP] supporting_text_verified`, tokenizer
  IndoBERT asli dengan panjang maksimum 128. Ikuti snapshot/model SHA pada
  manifest cache. Unggahan baru memerlukan teks hasil OCR yang dapat diedit.
- Jalankan embedding dan sepuluh blok pertama IndoBERT asli, lalu dua blok
  terlatih dari checkpoint E41. Masked mean mengecualikan padding dan special
  tokens; normalisasi L2 mengikuti `tail_model.py`.
- CLIP-L14 menggunakan bobot/preprocess pinned E36: full image dan crop
  `(0, int(.20*h), w, int(.94*h))`. Normalisasi masing-masing fitur, gabungkan
  full/crop, kalikan bobot visual 2, lalu gabungkan representasi teks.
- Gunakan shared head serta ketiga head dari checkpoint yang sama. Lima
  checkpoint CV hanya untuk evaluasi OOF; model produksi memerlukan refit
  seluruh data dengan prosedur pemilihan epoch yang ditetapkan dan dicatat.
- XAI harus menghubungkan graph gambar dan teks ke frozen encoder serta tail
  terlatih. Gradien terhadap cache fitur saja belum membuktikan XAI terhadap
  piksel/token. Prediksi, penjelasan dan ekspor harus merujuk model SHA sama.

Integrasi unggahan baru, XAI tiga task, refit produksi, clean install, dan QA
delivery belum lulus hanya karena smoke atau audit OOF lulus. Aplikasi baseline
tetap aktif sampai kandidat siap dan seluruh gate delivery terbukti.
