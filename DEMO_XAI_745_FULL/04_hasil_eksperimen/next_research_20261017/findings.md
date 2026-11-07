# Temuan Final Sprint 0–4

1. Audit dataset/split/provenance lulus; 740 gambar cocok hash dan tidak ada exact duplicate.
2. Model comparison M00–M04 selesai. E42 tetap terbaik dengan Macro-F1 0.5255/0.3956/0.4034.
3. Augmentation A00–A03 selesai; pipeline pilihan inner-fold minimum 0.3564 dan tidak mengalahkan E42.
4. E49 MMoE dan J01 hierarchical auxiliary tidak mengatasi negative transfer.
5. OCR exact match terbaik pada holdout kedua adalah 76,67% (69/90); gate 80% gagal.
6. Target ketiga task ≥0,70 gagal dan tidak diturunkan. Evaluasi tetap disebut internal OOF, bukan external validation.
7. Runtime delivery tidak diganti karena tidak ada kandidat yang lolos gate.
8. Pengujian clean Windows dan pengguna manusia tetap menunggu pelaksanaan pengguna.
