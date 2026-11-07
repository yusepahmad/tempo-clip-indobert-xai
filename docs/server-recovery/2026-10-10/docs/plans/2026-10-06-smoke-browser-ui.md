# Smoke UI Browser Headless (Langkah 3)

**Tanggal:** 2026-10-06
**Status:** done (2026-10-06; Chromium headless Linux saja)

Sub-plan langkah 3 dari [2026-10-06-lanjutan-week3-server.md](2026-10-06-lanjutan-week3-server.md).

## Tujuan
Membuktikan UI terbaru (termasuk R5) berfungsi dan terbaca di browser sungguhan, desktop dan mobile, dengan screenshot dan checklist yang dapat diperiksa ulang. Temuan bug diperbaiki lalu pemeriksaan terdampak diulang.

## Ruang Lingkup
- Baru: `01_notebook/smoke_browser_week3.py` (Playwright Python, Chromium headless) dan `requirements-browser.txt` (dependensi khusus pemeriksaan browser, terpisah dari aplikasi).
- Bukti: `04_hasil_eksperimen/revisi_week3/browser_smoke_20261006/` (screenshot PNG per viewport/langkah, unduhan ekspor) dan `browser_smoke_20261006.json` (checklist, input persis, konsol/HTTP error, durasi).
- Venv proyek mendapat paket `playwright`; biner browser di cache `~/.cache/ms-playwright` (sudah ada build chromium-1243; diunduh hanya bila versi pustaka meminta build lain).
- `02_web_demo/*` hanya diubah bila ditemukan bug; perubahan itu dicatat sebagai temuan di plan ini sebelum diperbaiki.
- TIDAK: dataset/label/model, backend kecuali bug, docs delivery (langkah 4), uji Windows, uji manusia.

## Langkah
1. Pasang Playwright, pastikan Chromium headless jalan.
2. Tulis skrip smoke ke server `tempo-ui` (`127.0.0.1:7861`), viewport desktop 1440×900 dan mobile 390×844 (touch), konteks browser bersih per viewport:
   1. Halaman awal: tanpa error konsol; panel kanan/workspace tampil (regresi textarea); tidak ada scroll horizontal; nav Analisis/Batch/Panduan.
   2. Dataset → analisis (LIME, baku UI) → overlay loading terlihat sejak request mulai, tombol busy → hasil; lima tab hasil di-screenshot; tab "Bukti gambar": `imgHeat` = peta gabungan, `imgHeatTask` = peta task pilihan, keduanya termuat (naturalWidth>0).
   3. Keyboard: ArrowRight/Left/Home/End pada tab hasil memindah fokus dan panel.
   4. Race: mulai analisis, ganti task saat request aktif → hasil lama tidak tampil, state kembali ready; analisis ulang menampilkan task baru.
   5. Unggah foto dosen → overlay OCR → headline terisi; isi teks pendukung panjang multibaris → textarea memuat utuh dan halaman dapat digulir vertikal; analisis → hasil.
   6. Ganti gambar unggahan saat OCR berjalan → hasil OCR lama tidak menimpa (headline sesuai gambar terakhir).
   7. Kegagalan: `/api/analisis` dipaksa gagal (route abort) → pesan error dan loading dibersihkan.
   8. Tiga foto dosen (`06_gambar_revisi/`), Task 2, metode baku UI: catat headline OCR, headline final yang dipakai, kelas, durasi.
   9. Batch kecil: 1 ID dataset + 1 gambar rusak, metode occlusion → status selesai/gagal tampil, review needs_review bila ada, unduh CSV/JSON berhasil, tautan peta gabungan terbuka (PNG).
   10. Panduan: katalog termuat 10/7/8 kelas.
3. Simpan screenshot dan checklist; perbaiki bug yang ditemukan, ulangi pemeriksaan terdampak.
4. Catat hasil di plan, plan induk, CHANGELOG.

## Temuan selama pelaksanaan
1. **Teks pendukung multibaris dikirim dengan CRLF** — Chromium menormalisasi `\n` → `\r\n` pada multipart/form-data (standar HTML; dibuktikan dengan `new Response(FormData)`). Isi teks utuh; bukan bug aplikasi. Cek skrip dinormalisasi, observasi dicatat di JSON. Backend tidak diubah.
2. **`net::ERR_FAILED` di konsol** berasal dari uji kegagalan jaringan yang disengaja; event selama skenario kegagalan ditandai `expected`.
3. **Skenario foto dosen mewarisi judul suntingan** — perilaku yang dirancang (suntingan pengguna tidak ditimpa OCR, dengan pesan). Skrip kini memulai tiap foto dari kolom bersih dan menambah cek eksplisit perilaku tersebut.
4. **Kontras tab hasil tampak rendah di screenshot** — artefak transisi `background .15s`; warna akhir benar (`#98570b`/putih). Skrip menunggu 400 ms sebelum screenshot tab. Bukan bug.
5. **Blok "Bukti task pilihan" (perubahan R5) menyisakan kolom kanan kosong di desktop** — diperbaiki di `02_web_demo/index.html`: keterangan dipindah ke kolom kanan di samping peta (mobile tetap bertumpuk). ID tidak berubah.

Catatan minor, tidak diperbaiki di langkah ini (dicatat untuk langkah 4/keputusan user): teks "Gambar yang dipilih tampil di sebelah kanan" kurang tepat di mobile (gambar tampil di bawah); pesan gagal item batch memuat path absolut server (`UnidentifiedImageError: ... /_jobs/...`).

## Risiko & Asumsi
- Headless Chromium bukan pengguna manusia dan bukan Firefox/Safari/Windows; screenshot adalah bukti render, bukan penilaian usability.
- Analisis LIME di CPU ~10–25 detik; skrip memakai timeout longgar.
- Batch membuat job lokal baru di `_jobs` (bukan bagian paket).
- Server tunggal yang sama dipakai; race test bergantung pada analisis cukup lama untuk diinterupsi.

## Verifikasi
- `venv/bin/python 01_notebook/smoke_browser_week3.py` keluar 0 dan menulis `browser_smoke_20261006.json` dengan semua cek `true`.
- Screenshot diperiksa secara visual (dibuka dan dilihat), terutama tab Bukti gambar dan tampilan mobile.
- Regresi JS/Python lama + R5 tetap lulus bila ada perbaikan.

## Hasil (2026-10-06)
- Run final setelah semua perbaikan: **80/80 cek lulus**, 239 detik, 24 screenshot (desktop 1440×900, mobile 390×844) di `04_hasil_eksperimen/revisi_week3/browser_smoke_20261006/`, checklist `browser_smoke_20261006.json`. Tanpa error konsol/halaman/HTTP tak terduga (3 event dari uji kegagalan disengaja ditandai `expected`).
- Tercakup: halaman awal/regresi textarea, tanpa scroll horizontal, dataset → analisis LIME dengan loading/tombol busy, lima tab hasil, R5 (peta gabungan + bukti task pilihan) di dataset/unggahan/foto dosen, keyboard tab, race ganti task, kegagalan jaringan/server, unggah + OCR + teks pendukung panjang (1.150 karakter, textarea resize vertikal, halaman dapat digulir), race OCR ganti gambar, suntingan pengguna dipertahankan saat ganti gambar, batch 1 sukses + 1 gambar rusak gagal dengan ekspor CSV/JSON dan tautan peta gabungan PNG, katalog 25 kelas.
- Foto dosen (Task 2, LIME): GULA-GULA (OCR tepat) → Permainan & Kontes; WASWAS (OCR `VJASWAS RUPIAH`, dikoreksi ke acuan visual agen) → Permainan & Kontes; CUKAI (OCR tepat) → Konsumsi & Transaksi. Kelas tidak divalidasi.
- Screenshot diperiksa visual: tab Bukti gambar desktop/mobile, tab Bukti kata, unggah teks panjang mobile, batch. Perbaikan tata letak blok task pilihan terverifikasi (keterangan di kolom kanan desktop, bertumpuk di mobile).
- Regresi lama + R5 tetap lulus setelah perbaikan.
- Belum: Firefox/Safari, Windows/browser user, uji pengguna manusia.
