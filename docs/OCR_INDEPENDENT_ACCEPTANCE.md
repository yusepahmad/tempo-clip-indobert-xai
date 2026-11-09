# Evaluasi OCR Independen — Sprint 1

**Tanggal:** 17 Oktober 2026  
**Status:** menjadi development evaluation setelah target 80% ditetapkan wajib;
bukan lagi holdout final untuk kandidat hasil tuning berikutnya.

## Desain evaluasi

- Populasi: dataset 740 sampul.
- Eksklusi: seluruh 30 sampel diagnosis/tuning OCR terdahulu.
- Sampel: 60 sampul, enam untuk masing-masing dari 10 kelas Task 1.
- Pemilihan: ranking SHA-256 deterministik menggunakan seed
  `tempo-ocr-independent-v1-2026-10-17` di dalam setiap kelas.
- Manifest dibekukan sebelum OCR dijalankan.
- Hash manifest:
  `c0e438c3fe3dab09ca979c83f495dd3fd553d550d6dd01bc508f0de33899ae6f`.
- Selector produksi tidak diubah selama evaluasi.
- Hash selector:
  `e29a38200b0d9126a3c9c320c5bc27f1e977a335092ecafd72fbdd328e233175`.
- Overlap dengan diagnosis lama: nol.

Manifest dan raw output berada di
`DEMO_XAI_745_FULL/04_hasil_eksperimen/revisi_week3/ocr_independent/`.

## Hasil headline

| Metrik | Hasil |
|---|---:|
| Sampel | 60 |
| Exact match | 43/60 |
| Exact accuracy | **71,67%** |
| Mean character error rate | 0,1635 |
| Median character error rate | 0,0000 |
| Mean token-F1 | 0,8373 |
| Median waktu | 2,12 detik |
| P95 waktu | 7,92 detik |

Jika 80% exact match dijadikan gate wajib, konfigurasi produksi sekarang
**belum lulus**. Dibutuhkan minimal 48/60 benar; hasil saat ini 43/60.

## Hasil teks pendukung

| Metrik | Hasil |
|---|---:|
| Sampel dengan anotasi | 60 |
| Exact match | 5/60 |
| Exact accuracy | 8,33% |
| Mean character error rate | 0,5002 |
| Mean token-F1 | 0,7587 |

Angka supporting text hanya **proxy**. Kolom `supporting_text_verified` adalah
anotasi konten dataset dan belum dibuktikan sebagai transkripsi lengkap semua
teks visual pada sampul. Karena itu angka 8,33% tidak boleh dipakai sebagai
acceptance OCR penuh atau sebagai bukti bahwa 91,67% ekstraksi salah.

## Kasus headline yang membutuhkan review manusia

| Sample ID | Ground truth dataset | Output OCR produksi |
|---|---|---|
| `TMP-0C0E1B72F18D` | Thohir Story | THOHIR |
| `TMP-0F0C6D5016F1` | Sekam Api Reformasi Polri | SEKAM API-REFORMAsIL POLRI |
| `TMP-24E2B1C69076` | Ketika Harus Memilih | NEMILIH |
| `TMP-2A50DAEE5D77` | Amuk dalam Sekam di Tolikara | DI TOLIKARA |
| `TMP-3213E13AD7AF` | PELAT NOMOR KOSONG | PELAT NOMOR |
| `TMP-62AD9ECE5DA7` | Ormas Paramiliter: Politik, Bisnis, Kekerasan | BISNIS ~ KEKERASAN |
| `TMP-760D0F334283` | Bagimu Negeri Menyediakan Api | A NwAR BAGIMUNEGERI MEWEDIAKAMAA |
| `TMP-8831D7051F6E` | Ada Apa dengan Pizza | ADAAAPA DENGANPLZZA diduqa pernah menogunakan bahan |
| `TMP-92C55AD605A4` | Kisruh BRIN | K1S RU H |
| `TMP-A176C2B83D3E` | Dalam Sekam Api Papua | FALAM SEKAMT API PAPUA |
| `TMP-C77D73EB386E` | Invasi ISIS di Marawi | INVAsIIISIS DI MARAWI |
| `TMP-D9F6EBF7B6AB` | LEKRA DAN GEGER 1965 | MULHEERITA |
| `TMP-DD8FC4A25FEB` | Oei Tjoe Tat Penyambung Lidah Bung Karno | Bug |
| `TMP-E85FDA2EB5BA` | Islam Jalan Damai | ISLAM |
| `TMP-EEE734A2EAB9` | Main Perkara Hakim Agung | MAIN PERKARA HAKIM AGUNG 'rearingan ! |
| `TMP-FA7EAD61DB20` | Muslim Konservatif: Saleh atau Salah? | SALEH ATAU SALAH? |
| `TMP-FB4EF95E9C9A` | GO DAI | DAI |

Review manusia perlu menetapkan apakah ground truth dataset memang headline
visual yang diharapkan, apakah output kehilangan subjudul, atau OCR salah baca.
Keputusan ini harus dibuat sebelum selector dituning; 60 sampel ini setelah itu
tetap menjadi set evaluasi, bukan set tuning.

## Gate eksternal

| Gate | Status | Kebutuhan |
|---|---|---|
| Keputusan target exact match 80% | Menunggu pengguna/peneliti | Tetapkan sebagai wajib atau target arah |
| Review ground truth 17 kegagalan | Menunggu manusia | Periksa gambar dan isi keputusan tanpa mengubah hasil raw |
| Clean install Windows terbaru | Belum dijalankan | Mesin/VM Windows bersih |
| Uji pengguna manusia | Belum dijalankan | Dosen atau calon pengguna menjalankan skenario yang disiapkan |
| Browser selain Chromium | Belum dijalankan | Firefox/WebKit atau browser target yang disepakati |

## Keputusan pengguna dan konsekuensi evaluasi

Pada 17 Oktober 2026 pengguna menetapkan exact match headline 80% sebagai gate
wajib. Hasil 60 sampel ini sudah terlihat dan kini dipakai untuk diagnosis,
sehingga tidak boleh dipakai kembali sebagai satu-satunya bukti final setelah
tuning. Holdout final baru harus dibekukan sebelum perubahan OCR dan baru
dijalankan setelah kandidat ditetapkan.

## Keputusan teknis sementara

OCR tetap layak sebagai pengisi awal yang wajib dapat dikoreksi pengguna, tetapi
belum layak diklaim memenuhi target 80% exact headline. Tidak ada perubahan
selector yang dilakukan dalam sprint ini agar set independen tidak berubah
menjadi data tuning secara diam-diam.

## Kandidat 2 dan holdout final

Setelah 60 sampel di atas direklasifikasi menjadi development, selector
diperbaiki untuk menggabungkan baris headline kecil yang menempel langsung dan
menjalankan re-OCR crop lokal pada fragmen display besar berkeyakinan rendah.
Kandidat terkunci dengan SHA-256
`94bb5c5ef5fd38ae7480d51f435e6c80264e150f04fdfe8f03327747a21435db`.
Pada development, kandidat mencapai 48/60 (80,0%) dan seluruh 16 regresi unit
OCR lulus.

Holdout final dibekukan sebelum kandidat dijalankan: 80 sampel, delapan per
kelas Task 1, tanpa overlap dengan 90 sampel pengembangan. Hash manifest
`658b230828f0f925963c4dd8064ea2b37df84146e380d97dd6e69f5a62c32258`.
Hasil read-once kandidat terkunci adalah **60/80 (75,0%)**. Dengan syarat
minimal 64/80, gate OCR 80% **belum lulus**. Raw hasil dan 20 kegagalan berada
di `04_hasil_eksperimen/revisi_week3/ocr_final_holdout/results.json`; hasil ini
tidak ditimpa atau dinyatakan lulus secara post-hoc.

## Validasi manusia atas 20 kegagalan

Pengguna memeriksa seluruh 20 kasus: 5 `valid`, 12 `invalid`, dan 3
`ambiguous`. Headline koreksi seluruh kasus konsisten dengan ground truth
dataset setelah normalisasi, sehingga tidak diperlukan perubahan ground truth.

Jika lima hasil non-exact yang dinilai masih valid dihitung sebagai usability,
hasilnya menjadi **65/80 (81,25%)**. Metrik ini dilaporkan terpisah dan tidak
menggantikan exact match: exact match tetap **60/80 (75%)**, sehingga gate
formal OCR exact match 80% masih belum lulus. Tiga kasus ambigu tidak dihitung
sebagai diterima. Bukti beku terdapat di
`DEMO_XAI_745_FULL/04_hasil_eksperimen/revisi_week3/ocr_final_holdout/human_validation.json`.
