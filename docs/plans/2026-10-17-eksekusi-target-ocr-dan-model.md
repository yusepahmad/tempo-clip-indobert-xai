# Eksekusi Target OCR dan Model

**Tanggal:** 2026-10-17
**Status:** in-progress

## Tujuan
Mengerjakan seluruh pekerjaan teknis yang tidak memerlukan data tambahan,
Windows bersih, atau partisipan manusia untuk mengejar OCR exact match ≥80%
dan Macro-F1 ≥0,70 pada masing-masing dari tiga task.

## Ruang Lingkup
- Audit 20 kegagalan OCR holdout pertama dan siapkan lembar validasi ambigu.
- Kembangkan kandidat OCR berikutnya memakai data yang sudah terbuka sebagai
  development, lengkap dengan regression test dan evaluasi baru yang sah.
- Audit dataset, label, split, duplikasi, imbalance, confusion, dan indikasi
  negative transfer model.
- Menjalankan eksperimen lokal yang layak sesuai resource dan bukti audit.
- Memperbarui dokumentasi, roadmap, dan changelog berdasarkan hasil aktual.
- Tidak menambah data baru, mengubah label tanpa keputusan pengguna, atau
  mengklaim uji Windows/manusia yang belum dilakukan.

## Langkah
1. Kategorikan 20 kegagalan OCR dan buat tabel keputusan label untuk pengguna.
2. Uji preprocessing/crop/multi-pass secara terkontrol pada seluruh data OCR
   yang sudah terbuka; tambahkan regression fixture untuk perbaikan yang sah.
3. Bekukan evaluation set OCR baru dari data yang belum pernah dibuka sebelum
   menjalankan kandidat berikutnya; gunakan desain yang masih mungkin dengan
   sisa distribusi kelas dan jelaskan keterbatasannya.
4. Audit statistik dataset, duplikasi, label, split, confusion matrix, dan
   baseline per task dari artefak yang tersedia.
5. Tentukan eksperimen model berikutnya dari audit, jalankan preflight dan
   training/evaluasi yang dapat diselesaikan pada resource tersedia.
6. Promosikan OCR/model hanya bila seluruh gate wajib benar-benar lulus.
7. Catat hasil, risiko tersisa, dan handoff Windows/uji pengguna.

## Risiko & Asumsi
- Data tetap 740 sampel; peningkatan model harus berasal dari kualitas label,
  formulasi, representasi, regularisasi, atau protokol—bukan penambahan data.
- Holdout OCR 80 sampel yang sudah dibuka menjadi data diagnosis setelah audit;
  bukti final berikutnya harus memakai sampel yang sebelumnya belum dibuka.
- Kelas OCR `other_issue` telah habis untuk holdout seimbang baru; evaluasi baru
  mungkin perlu sampling acak terstratifikasi tidak seimbang dan pelaporan per
  kelas.
- Target Macro-F1 0,70 mungkin tidak tercapai dengan informasi/data saat ini;
  kegagalan akan dilaporkan apa adanya beserta bukti dan opsi yang tersisa.
- Validasi label ambigu dilakukan pengguna; eksperimen tidak mengubah label
  tersebut sampai keputusan diterima.

## Verifikasi
- Setiap evaluasi menyimpan manifest, hash input/source, raw prediction, dan
  denominator.
- OCR dinyatakan lulus hanya jika evaluation set baru mencapai ≥80%.
- Model dinyatakan lulus hanya jika satu model/protokol mencapai Macro-F1
  ≥0,70 pada ketiga task.
- Unit/regression test relevan lulus dan tidak ada hasil lama yang ditimpa.

## Eksperimen Terpilih

Audit awal menetapkan E48 sebagai diagnosis negative transfer: tiga classifier
single-task dilatih pada cache frozen `visual`, `base_mean`, atau gabungannya,
menggunakan outer fold E42 yang sama. Feature family, normalisasi, dan C dipilih
hanya dari inner fold masing-masing task. E48 tidak memenuhi kontrak final
joint-model dan tidak boleh dipromosikan; hasilnya menentukan apakah eksperimen
berikutnya perlu task-specific tower/gating atau tetap memperdalam shared model.
