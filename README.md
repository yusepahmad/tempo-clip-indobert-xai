# Tempo — CLIP–IndoBERT MTL dan XAI

Source dan hasil analisis penelitian dekoding metafora sampul majalah Tempo pada 740 sampel, tiga task, dan lima fold. Model utama penelitian: **E42 CLIP-L14–IndoBERT joint MTL**. Metrik utama **Macro-F1**; Micro-F1/akurasi dan kappa dilaporkan sebagai pendamping.

**Snapshot 8 November 2026: 19 dari 28 butir revisi selesai teknis; 9 masih terbuka.** Ini paket untuk pemeriksaan/reproduksi, bukan klaim seluruh revisi, penilaian manusia atau target 0,70 sudah selesai.

## Hasil utama

| Model | Macro-F1 Task 1 | Task2 | Task3 | Peran |
|---|---:|---:|---:|---|
| E42 CLIP–IndoBERT | 0.525483 | 0.395560 | 0.403398 | Model utama penelitian; seleksi post-hoc diungkapkan |
| MICRO-E14 Qwen3-VL QLoRA | 0.673321 | 0.510282 | 0.595480 | Pembanding; bukan IndoBERT |
| QLoRA basic dengan supporting text | 0.684652 | 0.492739 | 0.590929 | Kontrol R21 terverifikasi 740 prediksi |

MICRO-E14 mempunyai Micro-F1 **0.720270 / 0.566216 / 0.667568**. Basic supporting dan arm literal citra+judul adalah eksperimen berbeda; nilai arm literal yang belum dikoleksi tetap Not Evaluated. Epoch QLoRA diwarisi dari pilihan inner rich historis; batas konteks CLIP dan Qwen berbeda. CI/perbandingan bersifat kondisional terhadap prediksi tersimpan dan tidak menghapus bias seleksi pada korpus berulang.

![Ringkasan hasil](delivery/HASIL_REVISI_JOY_20261108_R4/analysis/primary_results.png)

## Unduh hasil lengkap

Buka [Release R4 publik](https://github.com/yusepahmad/tempo-clip-indobert-xai/releases/tag/v2026.11.08-r4) untuk ZIP analisis dengan output notebook/HTML, tabel, source dan instrumen anonim, beserta checksum. Paket publik mengeluarkan kunci kontrol privat koordinator, registrasi/identitas partisipan, formulir pengembalian pribadi dan credential. ZIP privat asli tidak diunggah. Model/cache training besar tidak termasuk.

## Menjalankan ulang analisis dari clone

Gunakan Python 3.10:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r DEMO_XAI_745_FULL/01_notebook/revisi_ii/requirements-analysis-lock.txt
python delivery/HASIL_REVISI_JOY_20261108_R4/tools/evaluate.py --package --workspace delivery/HASIL_REVISI_JOY_20261108_R4 --output delivery/HASIL_REVISI_JOY_20261108_R4/analysis
python delivery/HASIL_REVISI_JOY_20261108_R4/tools/validate_package.py --root delivery/HASIL_REVISI_JOY_20261108_R4
```

Buka notebook di `delivery/HASIL_REVISI_JOY_20261108_R4/notebooks/` atau HTML pada `notebook_html/`. Run all analisis memakai CPU, tanpa training, API atau credential. Training/XAI ulang memerlukan model/cache dan environment ML tersendiri yang dirujuk protokol.

Untuk tes analisis:

```bash
cd DEMO_XAI_745_FULL/01_notebook/revisi_ii
python -m unittest -v test_evaluate test_human_agreement test_open_followup test_qwen_headline test_technical_delivery
```

## Isi dan status

- `DEMO_XAI_745_FULL/`: source notebook/eksperimen/web, data dan hasil/protokol yang tersedia.
- `delivery/HASIL_REVISI_JOY_20261108_R4/`: paket analisis publik; 234 baris metrik/78 sumber, tiga notebook dan bukti per revisi.
- `delivery/HASIL_REVISI_JOY_20261102_R3_FULL/`: fixture input/analisis/dokumentasi historis untuk tes; bukan arsip R3 lengkap.
- `docs/revisi-ii/`: provenance, keputusan model, definisi task dan instrumen kosong.
- `docs/plans/` dan `CHANGELOG.md`: rencana dan riwayat perubahan. Catatan server/laptop historis tidak menyatakan deployment publik aktif.

Source web terbaru memakai **RII_TAIL_RICH256 CLIP-L14–IndoBERT** dengan lima checkpoint asli. Micro-F1 OOF Task 1/2/3: **0.493243 / 0.524324 / 0.514865**. Kandidat web dipilih post-hoc berdasarkan maksimum minimum Micro-F1; E42 tetap model utama penelitian R4 berdasarkan Macro-F1. Dataset memakai checkpoint held-out; upload memakai ensemble lima fold yang belum dievaluasi terpisah. Lihat [panduan web, input rich, pemasangan model dan pengujian](docs/WEB_RICH256.md). Bobot didistribusikan sebagai [asset Release web rich256](https://github.com/yusepahmad/tempo-clip-indobert-xai/releases/tag/v2026.11.08-web-rich256), terpisah dari Git.

[Status revisi dan ketergantungan yang tersisa](docs/STATUS_REVISI_TERKINI.md) menjelaskan pekerjaan Kaggle/penilaian manusia/provenance yang belum dapat ditutup. [Buka launcher R32 di Colab](https://colab.research.google.com/github/yusepahmad/tempo-clip-indobert-xai/blob/main/docs/COLAB_PUBLIC_R4.ipynb) untuk mengunduh Release R4 otomatis dan menjalankan tiga notebook; launcher tersedia belum berarti Colab sudah lulus.

Penilaian manusia belum tersedia: anotasi independen 150 sampul oleh dua anotator, audit 60 sampul, lima penilai XAI, pemeriksaan 20 contoh E01 serta riwayat korpus masih diperlukan. Bukti Run all Colab belum ada; pengujian Linux/server tidak disebut kelulusan Colab.

## Hak materi pihak ketiga

Publikasi repository tidak memberikan lisensi baru atas citra majalah, teks atau bobot model pihak ketiga. Atribusi dan batas materi mengikuti sumber/pemiliknya. Tidak ada lisensi menyeluruh baru yang ditambahkan pada ekspor ini.
