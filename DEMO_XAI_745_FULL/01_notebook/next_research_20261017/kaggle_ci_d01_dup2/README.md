# CI-D01: exact train-only duplication2×

Dokumentasi: `docs/EKSPERIMEN_CLIP_INDOBERT_DUPLIKASI_2X_2026-10-20.md` dari root workspace.

- Bukan Qwen: frozen CLIP-L14 + frozen-front/trainable-tail IndoBERT, tiga task bersama.
- Bandingkan 1× versus2× paparan, dengan warm-head/initial state sama.
- Split ID dahulu; hanya training digandakan. Dataset tetap740 ID unik.
- Dua innerfold memilih epoch; lima outerfold untuk masing-masing arm.
- CPU FP32 saved-checkpoint reload canonical; GPU AMP diagnosis.
- `build.py` membekukan source/protokol dan menghasilkan dua launcher.
- `test_protocol.py` menguji kebocoran/multiplicity/payload/gradien lokal.
- `manage.py submit smoke`, `status smoke`, `collect smoke`; lalu `submit full`, `status full`, `collect full`.
- Semua push sekali dan tercatat ledger. Jangan hapus ledger untuk melakukan retry; selesaikan status ambigu terlebih dahulu.
- Tidak ada watcher otomatis. `collect full` memverifikasi dan menghasilkan laporan aktual; sebelum selesai, skor baru Not Evaluated.
- Hasil pada `04_hasil_eksperimen/next_research_20261017/08_ci_d01_duplicate2x/`.
- Worker/model/protokol historis, dataset, label, web dan ZIP lama tidak ditimpa.
