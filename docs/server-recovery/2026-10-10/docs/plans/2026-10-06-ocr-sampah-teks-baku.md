# OCR: Buang Sampah Teks Baku Sampul dari Teks Pendukung

**Tanggal:** 2026-10-06
**Status:** done (2026-10-06)

## Tujuan
User menemukan teks kotor di teks pendukung OCR ("INVES AGASI", "TEMPOCO/MINGGUAN", "TEMPOCOIMINGGUAN") pada foto GULA-GULA dan CUKAI. Penelusuran 250 sampul audit (cache `ocr_audit_blok_20261006.json`) menemukan empat kelompok sampah teks baku yang lolos karena `_ABAIKAN` hanya mencocokkan bentuk persis:
1. footer "majalah.tempo.co / mingguan" salah baca (MAJALAHTEMPOCO ×17, TEMPOCO/MINGGUAN, TEMPOCOIMINGGUAN, TENPOCO/MINGGUAN, MAJALAHTEMFOCO, MAJALAHTEMPO,CO, gabungan tanggal + footer);
2. label rubrik salah baca sebagai blok tersendiri (INVES AGASI);
3. harga/ISSN rusak (RP'5OESOOBER, RP?50.OOGMBER, RP 45 Doo, ISSM 012);
4. potongan acak huruf+angka satu kata berkeyakinan rendah (7uizo, Juui6, Coo3, Doo10, 77u1zb, XI7Va).

## Ruang Lingkup
- `02_web_demo/ocr_headline.py` `_bukan_teks_sampul()`: aturan pencocokan toleran untuk keempat kelompok; hanya berlaku pada **seluruh blok** (bukan potongan kalimat), sehingga teaser seperti "Investigasi: …", "Rp 36 miliar" di tengah kalimat, "DPR", "KPK", "OBAT" tetap.
- Regresi di `01_notebook/test_ocr_urutan.py` (contoh sampah dibuang, contoh sah dipertahankan).
- Ukur di cache audit (semua set): recall kata pendukung tidak boleh turun; jumlah segmen sampah dan presisi kata dilaporkan; judul tepat tidak boleh turun.
- TIDAK: mesin OCR, urutan baca, dataset.

## Risiko & Asumsi
- Kata sah yang kebetulan mirip teks baku bisa terbuang; dibatasi dengan syarat blok utuh, panjang pendek, dan (untuk potongan acak) keyakinan rendah.

## Verifikasi
- Test baru + seluruh regresi; metrik cache sebelum/sesudah; foto dosen GULA-GULA/CUKAI tanpa sampah; smoke browser.

## Hasil (2026-10-06)
- `_sampah_baku()` di `ocr_headline.py`: footer tempo.co/mingguan (pola + selisih ≤1 untuk MINGGUAN), label rubrik selisih ≤2, harga/ISSN rusak (keyakinan <0,75, bukan nominal MILIAR/TRILIUN/JUTA/RIBU), potongan huruf+angka satu kata (≤8 karakter, keyakinan <0,75), pecahan logo raksasa di 15% teratas (≤4 huruf).
- Percobaan pertama terlalu luas (membuang "DAI"/"WANI" judul yang letaknya tinggi, teaser "RP 179,56 MILIAR", "MINGGU INI"); dipersempit sebelum dicatat.
- Cache audit 250 sampul: presisi kata pendukung naik di semua set (dev 0,778→0,787; uji 0,804→0,816; validasi 0,800→0,810; validasi2 0,783→0,793); judul tepat tidak turun di set mana pun (validasi2 39→40: logo "APO" tidak lagi terpilih). Recall pendukung tetap, kecuali validasi 0,811→0,799 karena satu sampul (TMP-F8F480) yang judulnya sudah salah sebelumnya: setelah footer sampah dibuang, deck terpilih sebagai judul.
- Foto dosen GULA-GULA, WASWAS, CUKAI: tidak ada lagi "INVES AGASI", "TEMPOCO…", "SN: Olze".
- Regresi `test_ocr_urutan.py` + daftar sampah/teks sah; seluruh test lulus; server direstart.
