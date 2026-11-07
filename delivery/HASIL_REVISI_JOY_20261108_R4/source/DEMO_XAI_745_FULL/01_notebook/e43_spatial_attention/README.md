# E43 shared regional attention CLIP–IndoBERT

Pipeline: `extract.py` → `verify_features.py` → `prepare.py`. `finalize_features.py` menunggu sesi ekstraksi spesifik terminal, lalu menjalankan dua tahap terakhir dengan check=True; tidak me-restart proses atau meluncurkan GPU.

Setelah paket lengkap disalin lokal: `python build_launchers.py PACKAGE_DIR`. Upload dataset default private saja. Smoke terlebih dahulu, kemudian full hanya bila smoke lulus, kuota gratis≥2jam, pay-to-scale nonaktif dan tidak ada job lain aktif. Source dan hash paket dikunci pada launcher.

Training:9config,120epochs, shared text-conditioned32regionattention, sharedMLP3heads, positivejointloss. Pemilihan maxminimummeaninnerF1 tiga task memakai nested5×2; outertest tidak memilih config. Kontrol tanpaattention tetap dievaluasi. Source `model.py` dan protokol plan adalah definisi arsitektur/fit.

Hasil GPU bersifat provisional. `python verify_result.py PACKAGE_DIR GPU_OUTPUT_DIR` merekonstruksi740OOF CPUFP32 sekaligus memeriksa split, independent selection, checkpoint/source/input hashes. `python root_verify.py GPU_OUTPUT_DIR` menghitung Macro-F1 dengan stdlib. `checks.py` dan `check_root_audit.py` bukan skor kualitas model.

Regionalfeatures berasal dari full dan crop E36: patchtokens16×16 → average4×4cells → CLIPprojection768 → L2norm; urutanfull16/crop16 row-major. Fullglobalfeatures dibandingkan dengan E36 seluruh740; auditor regional memakai pooling implementasi terpisah untuk6sample dan memeriksa seluruhimageSHA.

Attentionweights tidak otomatis menjadi faithfulXAI. Delivery memerlukan full encodergraph, overlay alignment full/crop, token/pixelgradients, perturbation/sanity, newuploadE2E dan cleaninstall. Tidak mengganti aplikasi atau mengklaim semua task0,70 sebelum gate tersebut terbukti. Batas tetap740labelsasli dan kuotaKagglegratis. Repeatedexperimentselection dicatat sebagai keterbatasan.
