# Audit Leakage dan Train–Serve Parity

## Hasil

- Dataset: **740 ID unik**, seluruhnya memiliki gambar dan hash gambar cocok: **False**.
- Exact duplicate berdasarkan SHA-256: **0 grup**.
- Grup duplikat deklaratif beranggota >1: **0**; lintas fold: **0**.
- Kandidat near-duplicate dHash (jarak ≤2): **0**; lintas fold: **0**.
- Fold E42 mencakup setiap sample tepat sekali dan berisi fold 1–5.

Kandidat dHash bukan bukti duplikat; hasilnya disimpan di `near_duplicate_candidates.csv` untuk inspeksi manusia. Tidak ada exact duplicate yang dapat menyebabkan kebocoran lintas fold.

## Train–serve parity

Training E41/E42 memakai `headline_verified [SEP] supporting_text_verified`. Mode dataset pada aplikasi memakai kolom yang sama secara default, tetapi pengguna dapat mengeditnya. Mode upload memakai headline hasil OCR atau koreksi pengguna dan supporting text yang dimasukkan pengguna. Jadi preprocessing antarmuka kompatibel secara bentuk, tetapi distribusi teks upload **tidak identik** dengan teks verified saat training. Ini adalah gap deployment, bukan bukti label leakage.

## Batas klaim

OOF 5-fold pada corpus yang sama adalah evaluasi internal. Pemilihan berulang E33–E49 pada corpus ini menciptakan selection bias; hasil tidak boleh disebut validasi eksternal independen.
