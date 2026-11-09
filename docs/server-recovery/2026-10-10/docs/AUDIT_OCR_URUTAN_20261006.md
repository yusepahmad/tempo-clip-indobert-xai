# Audit OCR: urutan kata judul dan teks pendukung

**Tanggal:** 2026-10-06 (dimutakhirkan 6 Oktober malam: angka versi aplikasi terakhir di bagian "Angka versi aplikasi terakhir") · **Plan:** [2026-10-06-audit-ocr-urutan-kata.md](plans/2026-10-06-audit-ocr-urutan-kata.md)
**Bukti:** `04_hasil_eksperimen/revisi_week3/ocr_audit_urutan_20261006.json` (per sampel, sebelum/sesudah) dan `ocr_audit_blok_20261006.json` (blok EasyOCR mentah). Skrip: `01_notebook/audit_ocr_urutan.py`.

## Ringkasan

Keluhan "salah penataan kata" terbukti, terutama pada **teks pendukung**: blok hanya diurutkan menurut posisi atas, sehingga teaser dua/tiga kolom di kepala sampul saling menyelip. Contoh foto dosen GULA-GULA:

| | Teks pendukung |
|---|---|
| Sampul | kolom kiri "Uji Bukti Mendakwa / Nadiem Makarim H.63", kolom kanan "Lintang Pukang / 3 Juta Rumah H.72" |
| Sebelum | Lintang Pukang Uji Bukti Mendakwa Nadiem Makarim H.63 3 Juta Rumah H.72 P E R L U Presiden Prabowo … |
| Sesudah | Presiden Prabowo menunjuk ketua konfederasi buruh … May Day. H.26; Uji Bukti Mendakwa Nadiem Makarim H.63; Lintang Pukang 3 Juta Rumah H.72 |

Pada **judul**, tidak ditemukan kata yang tertukar; masalahnya judul **terpotong** (baris lanjutan berhuruf hias dibuang karena skor pembacaan rendah) dan **logo "TEMPO" salah baca** (TFMPO, TEMPQ, TEMFO, TEMPC, TRMPO) yang terpilih sebagai judul.

## Metode

- Mesin OCR tidak diganti (EasyOCR produksi). Blok mentah disimpan sekali, lalu selector lama (salinan beku `01_notebook/ocr_selector_baseline_20261006.py`) dan baru dibandingkan pada blok yang sama.
- Kebenaran: `headline_verified` dan `supporting_text_verified` dataset (tidak diubah). Metrik kata dinormalisasi huruf besar; **skor urutan** = LCS urutan kata terhadap jumlah kata yang cocok (1 = urutan sempurna), terpisah dari salah baca.
- Tiga set: **dev** 30 sampul diagnosis lama (untuk merancang), **uji** 100 acak seed 42, **validasi** 60 acak seed 7. Pemeriksaan per sampel pada set uji menemukan pola kesalahan tambahan yang ikut diperbaiki, sehingga set uji **terkontaminasi**; set validasi dibuka hanya setelah kode dibekukan dan menjadi angka utama.

## Hasil

| Set | Metrik | Sebelum | Sesudah |
|---|---|---|---|
| **Validasi (60, independen)** | Teks pendukung urutan sempurna | 13/56 | **35/56** |
| | Skor urutan pendukung (rata-rata) | 0,768 | **0,877** |
| | Judul tepat | 41/60 | **43/60** (5 membaik, 3 memburuk) |
| | Judul salah pilih blok | 12 | **8** |
| | CER judul | 0,178 | **0,146** |
| | Recall kata pendukung | 0,816 | 0,812 |
| Uji (100, terkontaminasi) | Pendukung urutan sempurna | 29/96 | 70/96 |
| | Judul tepat | 68 | 73 (tanpa regresi) |
| Dev (30) | Pendukung urutan sempurna | 7/30 | 19/30 |
| | Judul tepat | 19 | 21 (tanpa regresi) |

Recall kata tidak naik: perbaikan ini menata ulang dan memilih blok, tidak memperbaiki huruf yang salah dibaca EasyOCR.

**Penurunan skor urutan pada sebagian sampel (13 di validasi) seluruhnya disebabkan konvensi**: transkripsi anotator kadang menulis deck lebih dulu, kadang teaser lebih dulu. Selector baru menaruh deck (kalimat di bawah judul) lebih dulu karena paling terkait dengan judul dan teks pendukung dipotong 500 karakter sebelum masuk model. Bila deck dipindah ke belakang, ke-13 sampel itu tidak lagi turun.

**Regresi judul yang tersisa (validasi, belum diperbaiki agar validasi tetap independen):**
- `TMP-0F6191AD00E9` "BERTARUH PADA VAKSIN" → "5uth! BERTARUH PADA VAKSIN" dan `TMP-EF68E29B88C5` "INTRIK IVERMECTIN" → "Sutl: INTRIK IVERMECTIN": noise sebaris di kiri judul ikut tersambung.
- `TMP-E885379FE6E3` "KORUPSI BANsOS KUBU BANTENG" → "KORUPSI BANsOS BANTENG": satu kata hilang.

## Perubahan di `02_web_demo/ocr_headline.py`

1. **Urutan baca berbasis tata letak** untuk teks pendukung: blok → baris (sejajar vertikal, celah ≤ 0,6× tinggi huruf agar kolom tidak tergabung) → kelompok kolom/paragraf (bertumpuk, ukuran huruf mirip, tumpang horizontal) → deck di bawah judul lebih dulu, lalu pita atas→bawah dan kiri→kanan; kelompok dipisah "; ". Tinggi baris memakai blok tertinggi; potongan paragraf rata kiri-kanan dikembalikan ke barisnya.
2. **Judul disambung berantai**: baris seukuran yang menempel dan sekolom dengan judul ikut digabung, termasuk baris berhuruf hias berkeyakinan rendah (≥ 0,15, ≥ 4 karakter, mayoritas huruf); blok seperti itu disebut di catatan OCR agar diperiksa. Kata sebaris diurutkan kiri→kanan.
3. **Filter teks baku sampul**: logo besar di bagian atas yang memuat atau mirip "TEMPO" (selisih ≤ 2 huruf) dan tagline huruf berjarak ("E N A K", "P E R L U").

Regresi `01_notebook/test_ocr_urutan.py` (12 test setelah lanjutan; versi awal 8 test gagal semua terhadap selector lama) dan `test_week3_regressions.py` lulus. Smoke browser `browser_smoke_20261006_ocr.json` 83/83.

## Lanjutan: tiga regresi judul (6 Oktober, sore)

Perbaikan setelah validasi pertama, lalu diuji pada **validasi kedua** (60 sampul acak seed 11, di luar dev/uji/validasi; salinan beku versi audit pertama `01_notebook/ocr_selector_audit1_20261006.py`):

1. Blok berkeyakinan < 0,30 hanya tersambung ke judul bila tingginya ≥ 0,85× judul — kicker kecil "5uth!", "Sutl:" tidak lagi masuk.
2. Baris di tengah rentang grup judul berleading rapat ikut tersambung ("KORUPSI BANsOS **KUBU** BANTENG").
3. Setelah validasi kedua dibuka (label: terkontaminasi): kata sebaris harus bersebelahan, bukan saling menimpa horizontal ("NYAWA PENCABUT" → "PENCABUT NYAWA"); batas baris judul 4 → 6 (judul 5 baris tidak lagi terpotong). Penurunan ambang ukuran 0,62→0,55 dicoba lalu **dibatalkan** karena memicu 3 regresi di set lain.

| Validasi kedua (60) | Sebelum audit | Audit pertama | Lanjutan (beku, angka utama) | Versi aplikasi (setelah poin 3) |
|---|---|---|---|---|
| Judul tepat | 37 | 38 | 38 | **39** |
| Judul salah pilih blok | 14 | 13 | 13 | 13 |
| CER judul | 0,268 | 0,260 | 0,260 | 0,290 |
| Pendukung urutan sempurna | 15 | 33 | 33 | 32 |
| Skor urutan pendukung | 0,800 | 0,877 | 0,877 | 0,872 |

- Dibanding sebelum audit: **0 judul memburuk** pada validasi kedua; 17 penurunan skor urutan pendukung seluruhnya karena konvensi deck.
- Poin 1–2 memperbaiki ketiga regresi validasi pertama (judul tepat validasi pertama 43→46/60) tanpa mengubah keluaran di validasi kedua.
- **Trade-off poin 3:** dua judul panjang kini utuh ("…SAMPAI JAUH", "…SANG PEMBELA REPUBLIK"), tanpa regresi judul di keempat set; tetapi pada judul yang memang sudah salah pilih blok, lebih banyak kalimat deck terserap ke judul sehingga CER judul validasi kedua naik 0,260→0,290 dan satu teks pendukung kehilangan urutan sempurna. Judul seperti itu tetap harus dikoreksi manual. **Keputusan user: batas 6 baris dipertahankan.**
- Masih tersisa: "OBAT" pada "OBAT PENCABUT NYAWA" tidak tersambung (kotak "PENCABUT" membengkak sehingga "OBAT" 0,60× di bawah ambang 0,62×).

## Lanjutan: sampah teks baku (6 Oktober, malam)

Atas laporan user ("INVES AGASI", "TEMPOCO/MINGGUAN", "TEMPOCOIMINGGUAN"), blok utuh berikut kini dibuang: footer tempo.co/mingguan salah baca, label rubrik salah baca, harga/ISSN rusak, potongan acak huruf+angka berkeyakinan rendah, dan pecahan logo raksasa di 15% teratas. Kata pendek sah ("DPR", "KPK", "BPJs", "OBAT") dan teaser bernominal ("Rp 179,56 miliar") tetap. Presisi kata pendukung naik di keempat set tanpa judul tepat yang turun; rincian di [plan](plans/2026-10-06-ocr-sampah-teks-baku.md).

## Lanjutan: audit kode modul OCR (6 Oktober, malam)

Audit kode ([plan](plans/2026-10-06-audit-bug-kode.md)) memperbaiki filter rubrik yang membuang kata judul sah ("SERANGAN", "INVESTASI"; judul "JEBAKAN INVESTASI BODONG" kini utuh), "EDISI KHUSUS … THAMRIN" dan rentang tahun "1903-1962" yang ikut terbuang, jalur tanpa kandidat judul, potongan 500 karakter di batas kata, serta kata ulang terpenggal ("GAYA -" + "GAYAAN"). Regresi `test_ocr_urutan.py` kini 16 test.

## Angka versi aplikasi terakhir (6 Oktober, malam)

Dihitung ulang dengan `01_notebook/audit_ocr_urutan.py evaluasi` pada cache blok yang sama (`ocr_audit_blok_20261006.json`) setelah perbaikan sampah teks baku dan audit kode. Kolom "Sebelum audit" = selector awal.

| Set | Metrik | Sebelum audit | Versi aplikasi terakhir |
|---|---|---|---|
| Validasi kedua (60) | Judul tepat | 37/60 | **41/60 (68%)** |
| | Judul salah pilih blok | 14 | 12 |
| | CER judul | 0,268 | 0,273 |
| | Recall kata pendukung | 0,772 | 0,803 |
| | Pendukung urutan sempurna | 15/53 | 33/55 |
| Validasi pertama (60) | Judul tepat | 41/60 | **47/60 (78%)** |
| | CER judul | 0,178 | 0,245 |
| | Recall kata pendukung | 0,816 | 0,799 |
| Uji (100) | Judul tepat | 68 | 73 |
| Dev (30) | Judul tepat | 19 | 21 |

- Tidak ada judul yang tepat sebelum audit lalu menjadi salah, di keempat set.
- **Kedua set validasi sudah terkontaminasi**: keduanya ikut ditelusuri saat memperbaiki (validasi pertama untuk lanjutan, validasi kedua untuk poin 3, sampah teks baku dan audit kode). Karena itu 68–78% cenderung optimistis. Angka independen saat kode dibekukan adalah 43/60 (72%, validasi pertama, audit pertama) dan 38/60 (63%, validasi kedua, lanjutan beku).
- CER judul validasi pertama naik karena pada judul yang sudah salah pilih blok lebih banyak kalimat deck terserap (lihat trade-off poin 3 dan sampul `TMP-F8F480…` di plan sampah teks baku).
- Berkas bukti `ocr_audit_urutan_20261006.json` dihitung ulang 6 Okt malam setelah perbaikan sampah teks baku dan audit kode: kolom `produksi` = versi aplikasi terakhir (validasi 47/60, validasi kedua 41/60); kolom `baseline` dan `audit1` tetap salinan beku sebagai pembanding.

## Yang tetap terbatas

- Salah baca huruf (WASWAS → `VJASWAS`/`VJJASWAS`, berbeda menurut jumlah thread CPU) dan judul yang tidak terdeteksi sama sekali (mis. "BANGGAR") berada di EasyOCR; tidak berubah.
- Versi aplikasi terakhir: judul tepat 41/60 (68%) di validasi kedua, dan 12/60 masih mengambil blok yang salah (per sore: 39/60 dan 13/60). Sasaran usulan 80% belum tercapai. Koreksi manual tetap wajib.
- Kebenaran teks pendukung adalah transkripsi anotator yang konvensinya campuran; skor urutan sebagian mencerminkan konvensi.
