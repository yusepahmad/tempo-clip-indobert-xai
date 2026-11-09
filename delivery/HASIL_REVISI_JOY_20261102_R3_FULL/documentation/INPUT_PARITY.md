# Arsitektur dan kekayaan masukan

Basic yang benar untuk model utama adalah citra + headline_verified + supporting_text_verified. Rich menambah description1000char, sumber_visual250char dan alasan500char dari E01. Label gold dan domain prediksi tidak dialirkan menjadi field fitur.

| Arsitektur | Basic | Rich |
|---|---|---|
| CLIP–IndoBERT tail controlled | RII_TAIL_MTL_WEIGHTED (128 token) | RII_TAIL_RICH256 (256 token) |
| Qwen3-VL QLoRA | RII_QWEN_QLORA_BASIC | MICRO_E14_joint_qlora_oof historis |

Zero-shot Qwen basic/rich adalah kontrol tambahan tanpa training, bukan OOF model terlatih. RII_FROZEN_MTL_RICH adalah kontrol CLS128 terpisah:736/740teks terpotong. Cache rich256 meliputi seluruh input pada data ini, tetapi tokenisasi/input efektif tetap berbeda antarmodel. Pada tail, nilai max-length ikut berubah agar rich tidak terpotong; perbandingan ini menilai konfigurasi input praktis, bukan isolasi panjang token.

Basic QLoRA memakai epoch per fold yang sama dengan pilihan inner rich historis[3,1,3,2,3], seed/refit/protokol sama; fold1 mengembalikan adapter awal pilot yang sama. Ini kontras input bersyarat pada resep rich, bukan tuningbasic independen berbasisMacro. Hanya tabel hasil yang benar-benar tersedia boleh dipakai; sel kosong tetap Not Evaluated dan R21terbuka sampai740 prediksi diverifikasi.
