# Audit Bug Kode (Frontend, Backend, Modul OCR/Narasi)

**Tanggal:** 2026-10-06
**Status:** done (2026-10-06; autentikasi menunggu keputusan user)

## Tujuan
Atas permintaan user ("tolong audit dan cek bug bug nya … audit lagi code nya"), tiga audit read-only dijalankan paralel (frontend `index.html`; backend `app.py`/`batch_jobs.py`; modul `ocr_headline.py`/`explanation_evidence.py`/`label_display.py`). Setiap temuan diverifikasi agen utama sebelum diperbaiki; perbaikan dicatat di sini dan di CHANGELOG.

## Temuan modul (diverifikasi) dan perbaikan
| # | Tingkat | Temuan | Perbaikan |
|---|---|---|---|
| M1 | Tinggi | Penjelasan task memuat catatan anotator task lain (task1 menyebut sumber kiasan & entitas) — klaim lintas task | Saring catatan per task: task2 → sumber_metafora, pemetaan_makna; task3 → entitas; task1 → tidak ada; bukti `annotation` diberi `task_id` |
| M2 | Tinggi | Filter rubrik fuzzy (hari ini) membuang "SERANGAN", "INVESTASI" → judul terpotong ("JEBAKAN INVESTASI BODONG" → "BODONG") | Selisih panjang ≤1 dan jarak edit ≤2 hanya untuk rubrik ≥11 huruf, ≤1 untuk yang lebih pendek |
| M3 | Sedang | `_ABAIKAN` membuang "EDISI KHUSUS … MOHAMMAD HOESNI THAMRIN" utuh dan rentang tahun "1903-1962" | "EDISI" dibuang hanya bila sisanya tanggal/angka; rentang angka dibuang hanya bila diikuti nama bulan |
| M4 | Sedang | Jalur cadangan "tidak ada kandidat" mengembalikan blok mentah (logo, footer) ke teks pendukung tanpa filter/batas | Pakai filter teks baku, urutan baca, batas 500, kunci respons sama |
| M5 | Rendah–sedang | Peta datar (semua nol) tetap diklaim "paling berpengaruh di bagian atas" | Zona tidak disebut bila rentang peta ≈ 0 |
| M6 | Rendah | Crash pada blok tanpa `yakin`/`yakin=None`/`teks=None`/`tinggi_gambar=None` | Normalisasi di awal `pilih_headline` |
| M7 | Rendah | Pemotongan 500 karakter di tengah kata | Potong di batas kata |
| M8 | Rendah | Tanda baca ganda ".;" "?;" antar kelompok; "31 OKTOBER -6" | "; " tidak ditambahkan bila kelompok berakhir .?!: ; sambung tanpa spasi hanya bila tanda hubung menempel pada huruf |
| M10 | Rendah | Kata kembar "‘JANJI’ dan ‘JANJI’", kutip ganda "‘'Suap'’", "multiple_or_other" kehilangan makna "lainnya", ringkasan "sejalan untuk ketiga aspek" walau label tak lengkap | Dedup + buang kutip di `_kata`; frasa "beberapa pihak atau pihak lain"; perbandingan anotator hanya atas label yang ada |
| M9 | Rendah | Filter wilayah atas (`_LOGO_ATAS`, `_mirip_tempo`) dapat membuang kata pendek di 28% teratas | Tidak diubah (trade-off terdokumentasi, belum ada kasus nyata) |

### Hasil perbaikan modul (diverifikasi)
- M1–M8 dan M10 diterapkan di `ocr_headline.py` dan `explanation_evidence.py`; tambahan: kata ulang terpenggal "GAYA -" + "GAYAAN" disambung rapat.
- Test lama `test_five_strategies_and_task_binding` diubah satu kasus: catatan `entitas` (milik Task 3) diganti `sumber_metafora` (milik Task 2) — test lama mengunci perilaku lintas task yang salah; maksud test (strategi berbasis catatan anotator) tetap.
- Test baru: `test_narasi_ringkasan.py` (+4, total 10), `test_ocr_urutan.py` (+3, total 16); semua lulus.
- Cache audit OCR 250 sampul vs versi sebelum audit kode: judul tepat tidak turun di set mana pun (validasi2 40→41); recall kata pendukung naik (uji 0,807→0,822; validasi2 0,768→0,804; dev 0,868→0,875); presisi naik/tetap kecuali dev 0,787→0,784; skor urutan turun ≤0,009 di dev/uji karena teks sah yang kini dipertahankan ikut dinilai.

## Temuan frontend & backend dan rencana perbaikan
Laporan auditor (Playwright/test lokal/server) dirangkum; dikerjakan paralel oleh dua sub-agent pada berkas terpisah, ditinjau agen utama (diff terhadap salinan di scratchpad), lalu diuji ulang.

**Backend (`app.py`, `batch_jobs.py`; test baru `01_notebook/test_audit_backend.py`):**
| # | Tingkat | Temuan | Perbaikan |
|---|---|---|---|
| B1 | Tinggi | Form/berkas di-parse di dalam MODEL_LOCK → klien lambat membekukan engine (terbukti 5,1 dtk) | Baca form & berkas sebelum mengunci |
| B2 | Tinggi | PNG kecil berdimensi ekstrem (1×16000) → +3,3 GB RAM | Tolak sisi >8000 px / rasio >5:1, `MAX_IMAGE_PIXELS`, perkecil ke maks 2000 px sebelum disimpan (analisis, OCR, batch) |
| B3 | Tinggi | Tanpa batas kerja: judul tak terbatas (occlusion 0,14 dtk/kata), batch antre tak terbatas, unggah 200 MB | Batas judul 300 & pendukung 2000 karakter, batas ukuran unggah per endpoint, maks job antre/berjalan; **autentikasi/bind tidak diubah — keputusan user** |
| B4 | Sedang | Path absolut bocor (resume/review job tak ada, catatan OCR) | 404 "job tidak ditemukan", catatan OCR disaring, indeks review di luar rentang 404 |
| B5 | Sedang | NaN dataset → "nan" (catatan anotator 83/740; supporting "nan" pada 8 sampel → atribusi pada input berbeda dari prediksi) | Helper teks kosong untuk NaN |
| B6 | Sedang | Proses tidak bisa berhenti saat batch berjalan | Worker batch daemon; status "interrupted" yang sudah ada menangani restart |
| B7 | Sedang | Status item basi setelah resume/review (error/result lama ikut) | Bersihkan saat antre ulang; review hanya untuk item yang perlu ditinjau/unggahan gagal |
| B8 | Sedang | Cache 400 berkas → heatmap hasil yang masih terbuka hilang | Bersihkan per analisis berdasarkan umur/jumlah analisis |
| B9 | Rendah | Formula CSV lolos (\t=, \r, spasi) | Cek setelah lstrip + prefiks tambahan |
| B10 | Rendah | sample_id tak ada diterima; status job selalu complete; status tidak kembali queued saat resume/review | Validasi saat membuat job; status `failed` bila semua gagal; status queued |
| B11 | Rendah | 413/500 berupa HTML | Error handler JSON untuk /api |
| B12 | Rendah | metode_atribusi tak sah diam-diam jadi LIME | 400 |
| B13 | Rendah | Nama berkas OCR berbasis milidetik | uuid |
| B14 | Rendah | Ringkasan batch in-sample "sejalan dengan anotator" tanpa catatan | Catatan in-sample di ringkasan batch |
| B16 | Rendah | `/api/image` di Windows rentan `..\` | Validasi sample_id terhadap dataset |

**Frontend (`index.html`; test baru `01_notebook/test_audit_frontend.py` dengan Playwright + mock):**
| # | Tingkat | Temuan | Perbaikan |
|---|---|---|---|
| F1 | Sedang | XSS: pesan OCR (`catatan` berisi teks OCR) via innerHTML; kata/anotator/verifikasi via innerHTML | `textContent`/escape semua nilai dinamis |
| F3 | Sedang | Render ulang batch membuang ketikan review & menutup details | Pertahankan nilai input/`open`; tombol konfirmasi dikunci saat POST |
| F4 | Sedang | Polling batch berhenti permanen setelah satu error | Jadwal ulang dengan backoff; cek `res.ok` |
| F6 | Rendah | Klik tab mode yang sudah aktif membuang hasil | Abaikan bila mode sama |
| F7 | Rendah | Kandidat OCR usang tertinggal; memilih ulang kandidat sama tak berefek | Kosongkan saat ganti mode; reset pilihan setelah dipakai |
| F8 | Rendah | batchId usang di localStorage → error tiap muat | Hapus saat 404 |
| F9 | Rendah | Dobel klik "Mulai batch" → 2 job; input batch tak dikunci | Kunci tombol/input selama request & job berjalan; kosongkan berkas |
| F10 | Rendah | Mobile: overlay/hasil di luar layar; tab hasil tertutup header | scrollIntoView di mobile; sticky top = tinggi header |
| F11 | Rendah | Task batch diambil dari kontrol tersembunyi | Pilihan task di view Batch; cegah ID duplikat |
| F12 | Rendah | Error non-JSON tampil "Unexpected token '<'" | Helper baca JSON dengan pesan ramah |

**Dikerjakan agen utama setelahnya:** F2/B (analisis yang dibatalkan tetap memakan server → analisis berikutnya dua kali lebih lama): token pembatalan klien→server, server melewati kerja yang sudah dibatalkan.

## Verifikasi
- Test baru untuk tiap perbaikan + seluruh regresi; cache audit OCR (judul tepat tidak boleh turun, presisi/recall pendukung dilaporkan); smoke browser; restart `tempo-ui` (0.0.0.0:7861).

## Hasil frontend, backend dan F2 (2026-10-06)
- Backend B1–B14, B16 diterapkan di `app.py` dan `batch_jobs.py` (sub-agent, ditinjau): masukan divalidasi & dibaca di luar MODEL_LOCK; gambar >8000 px / rasio >5:1 / >40 MP ditolak dan diperkecil ke 2000 px; judul ≤300 & pendukung ≤2000 karakter; unggah analisis/OCR ≤25 MB; maks 2 job batch aktif/antre (429); 404 JSON tanpa path; NaN→""; worker batch daemon; item diantre ulang dibersihkan; cache per analisis (2 jam / 150 analisis); CSV aman; validasi sample_id; status `failed`; error JSON 413/404/500; metode tak sah 400; nama OCR uuid; catatan in-sample di ringkasan batch; `/api/image` hanya sample_id dataset. Variabel `TEMPO_CACHE_DIR`/`TEMPO_JOBS_DIR` agar test tidak menyentuh server hidup.
- Frontend F1, F3, F4, F6–F12 diterapkan di `index.html` (sub-agent, ditinjau): escape semua pesan dinamis, render batch mempertahankan ketikan/`open`, polling dengan backoff, tab mode aktif tidak membuang hasil, kandidat OCR dibersihkan, batchId usang dihapus, tombol/input batch dikunci, gulir otomatis hanya di mobile + sticky tab sesuai tinggi header, pilihan task di view Batch, helper JSON ramah.
- F2 (agen utama): `req_id` per analisis; pembatalan dikirim via `navigator.sendBeacon('/api/analisis/batal')`; server melewati analisis yang dibatalkan saat masih antre dan berhenti di titik periksa sebelum Grad-CAM dan sebelum atribusi kata (409). Uji nyata: hasil kedua 30,2 → 24,6 dtk (sisa = pelatihan ulang leave-one-out yang tidak dapat diputus).
- Test: `test_audit_backend.py` 33 (30 + 3 F2), `test_audit_frontend.py` 13 (11 gagal terhadap HTML lama), seluruh test lama lulus tanpa diubah (selain satu kasus `test_week3_regressions.py` di bagian modul); total Python 70 + frontend 13 + JS 4 lulus. Smoke `browser_smoke_20261006_audit.json` **94/94** (cek status batch kini menerima `failed`; cek pesan gagal tidak peka kapitalisasi).
- Belum: autentikasi/token atau kembali ke bind 127.0.0.1 (keputusan user); migrasi manifest job lama yang masih memuat path; penghapusan otomatis `_jobs`.
