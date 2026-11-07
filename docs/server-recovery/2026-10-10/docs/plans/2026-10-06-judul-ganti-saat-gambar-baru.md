# Judul Diganti Saat Gambar Baru Diunggah

**Tanggal:** 2026-10-06
**Status:** done (2026-10-06)

## Tujuan
User: "ketika saya edit judul terus saya upload image baru itu si judul gak ganti". Perilaku lama (sejak Week 1) sengaja mempertahankan judul/teks yang disunting saat gambar diganti dan hanya memberi pesan. User menilai ini bug: suntingan itu milik gambar sebelumnya. Keputusan: **gambar baru = teks dibaca ulang dari gambar baru**.

## Ruang Lingkup
- `02_web_demo/index.html` `bacaOtomatis()`: saat berkas dipilih, kolom judul dan teks pendukung selalu dikosongkan lalu diisi hasil OCR gambar baru; `_ocrTerakhir` direset. Pesan status menyebut bahwa suntingan untuk gambar sebelumnya diganti (bila ada).
- Tetap dipertahankan: suntingan yang diketik **selama OCR gambar yang sama berjalan** tidak ditimpa (`textEditRev`).
- `01_notebook/smoke_browser_week3.py`: skenario `scenario_edit_preserved` diganti menjadi "judul suntingan diganti saat gambar baru" + "suntingan selama OCR dipertahankan".
- `01_TUTORIAL.md` B.3, `docs/STATUS_REVISI_20261006.md` T03/T07 diselaraskan.
- TIDAK: mode dataset (judul dataset tetap mengikuti sampul terpilih seperti sekarang), backend.

## Verifikasi
- Test JS lama lulus; Playwright: sunting judul → unggah gambar lain → judul = OCR gambar baru; ketik saat OCR berjalan → tidak ditimpa; smoke lengkap lulus.

## Hasil (2026-10-06)
- `bacaOtomatis()` kini selalu mengosongkan judul/teks pendukung lalu mengisinya dengan hasil OCR gambar baru; pesan menyebut suntingan untuk gambar sebelumnya diganti. Ketikan selama OCR gambar yang sama tetap dilindungi.
- Smoke `browser_smoke_20261006_judul.json` **94/94** (skenario `scenario_edit_preserved` diganti: judul suntingan lama diganti hasil gambar baru; ketikan selama OCR tidak ditimpa). Test JS lama lulus.
