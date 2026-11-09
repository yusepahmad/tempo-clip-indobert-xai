# Versi R3 FULL — hasil audit

Ketiga notebook berisi output tersimpan dan seluruh bukti yang tersedia. Empat confusion matrix Task 3 (baseline, E42, E11, E14), tabel distribusi/entropi/weighting, seluruh gambar XAI, tabel lengkap dan source bukti telah dimasukkan.

- 141 berkas bukti per revisi dan 21 lampiran canonical ditampilkan.
- Seluruh 28 butir memiliki bagian notebook; 19 selesai teknis, 9 masih terbuka.
- Semua tiga notebook lulus Run all lokal; bukti Colab dan penilaian manusia tetap sesuai status.
- 499 file data/prediksi/analisis/model/instrumen/protokol/XAI identik dengan R2.

Mulai dari **MULAI_DI_SINI.html**. Notebook di **notebooks/**, HTML di **notebook_html/**. Rincian pemeriksaan ada di **qa/FULL_NOTEBOOK_VERIFICATION.json** dan cakupan per file di **documentation/NOTEBOOK_FULL_COVERAGE.json**.

---

# Revisi II Notebook Joy — paket penelitian

Status saat build: **19 dari 28butir selesai secara teknis; 9 masih terbuka**. Paket siap untuk diperiksa Joy dan berisi bukti yang tersedia, bukan klaim seluruh revisi telah ditutup. Lihat `documentation/TINDAK_LANJUT_JOY.md` sebelum meneruskan sebagai hasil final.

## Mulai membaca
1. Buka `MULAI_DI_SINI.html` untuk ringkasan, lalu `notebook_html/03_final_comparison.html` atau notebook di `notebooks/`.
2. Ketiga notebook memiliki output tersimpan setelah pengujian lokal. Membaca hasil tidak memerlukan GPU, model dasar, atau library Python.
3. Model utama penelitian adalah E42. Demo web historis pada source memakai CLIP-B32 dan tidak boleh dilabeli sebagai inferensi E42. Tidak ada klaim web Qwen menjadi model utama.

## Menjalankan ulang analisis
Ekstrak ZIP utuh sehingga folder `joy_revisi_ii/` tersedia. Gunakan Python 3.10 atau versi yang kompatibel dengan requirements terkunci, lalu:

```sh
python -m venv .venv
# Linux/macOS: source .venv/bin/activate
# Windows: .venv\Scripts\activate
python -m pip install -r requirements-analysis-lock.txt
python tools/evaluate.py --package --workspace . --output analysis
python tools/validate_package.py --root .
```

Untuk Colab: unggah/ekstrak paket analisis ke `/content/joy_revisi_ii`, pasang requirements bila diperlukan, lalu buka salah satu notebook. Notebook mendeteksi folder paket tanpa path komputer pengembang. Run all menghitung ulang metrik/CI dari prediksi, tidak menjalankan training atau meminta credential. Bukti Colab hanya dianggap ada jika `qa/COLAB_VERIFICATION.json` berstatus verified.

## Isi dan batas reproduksi
- `inputs/`: dataset canonical, fold, seluruh prediksi ternormalisasi dan sumber/hash asli.
- `analysis/`: metrik per task/per kelas, CI, paired tests, peringkat, diagnosis dan grafik.
- `tools/`: evaluator, validator, source build, tes dan worker revisi.
- `source/`: source historis dan konfigurasi/audit kecil untuk keterlacakan.
- `experiment_protocols/`: source/protocol/job state dari eksperimen nyata. Status yang masih running bukan hasil final.
- `xai_e42/`: delapan contoh E42 outerfold, replay parity, rollout, LIME dan deletion.
- `documentation/`: tanggapan 28butir, draf naskah, provenance, codebook dan tindak lanjut.
- `human_inputs/`: template kosong 150sampul anotasi, 60 kasus adjudikasi dan penilaian XAI. Kosong berarti belum dilakukan.
- `coordinator_private/`: kunci kontrol untuk koordinator; jangan bagikan kepada penilai.

Paket analisis dapat dihitung ulang tanpa bobot encoder. Menjalankan ulang training/XAI memerlukan fitur/checkpoint/libraries ML yang dicantumkan di protokol dan lampiran model bila disediakan; pretrained weights publik harus diunduh dari pin resminya. Source Kaggle historis memakai path `/kaggle/input` dan bukan bagian Run all analisis CPU ini. Akses dataset/kernel privat bukan otomatis diberikan kepada penerima ZIP.

## Yang belum boleh diklaim
Anotasi ganda, riwayat 1040→740 dan lima penilai XAI belum ditemukan. Skor manusia tidak diisi AI. Sel input-parity yang belum memiliki 740 prediksi tetap Not Evaluated. Validasi eksternal, clean Windows dan Colab yang belum dijalankan tidak dianggap lulus hanya karena pengujian Linux lokal berhasil.

Ini penyerahan privat penelitian. Hak cipta citra/bobot mengikuti pemilik/penyedia; paket bukan lisensi distribusi publik.
