# Mulai dari sini

**Demo XAI — Dekoding Metafora Sampul Majalah Tempo**
Status 6 Oktober 2026 · paket delivery revisi Week 3 (model baseline).
Diuji dari instalasi bersih di Linux, lihat
`docs/plans/2026-10-06-paket-delivery-final.md`. Sebagian hal masih terbuka
(antara lain instalasi bersih Windows, uji pengguna manusia, sasaran OCR 80%).
Status lengkap ada di `docs/STATUS_REVISI_20261006.md`.

---

## Kalau kamu cuma ingin menjalankannya

### Windows

1. Pasang **Python 3.10** dari
   <https://www.python.org/downloads/release/python-31011/>

   Saat memasang, **centang dua kotak ini**:
   - `Add Python to PATH`
   - `py launcher`

   > Python 3.12 ke atas **tidak bisa** — PyTorch belum mendukungnya.

2. Klik dua kali **`setup_windows.bat`** — cukup sekali, perlu 10–30 menit.

3. Klik dua kali **`jalankan_windows.bat`**

4. Tunggu sampai muncul `Running on http://127.0.0.1:7860`,
   lalu buka alamat itu di peramban.

> Saat **pertama kali dijalankan**, aplikasi mengunduh model CLIP, IndoBERT,
> dan EasyOCR (±1,5 GB). Hanya sekali. Jangan tutup jendelanya.

Mematikan: tekan `Ctrl+C` di jendela hitam.

### Linux / macOS

```bash
python3.10 -m venv venv
venv/bin/pip install --upgrade pip
venv/bin/pip install --extra-index-url https://download.pytorch.org/whl/cpu torch torchvision
venv/bin/pip install -r requirements.txt
./jalankan_linux.sh
```

`requirements.txt` hanya memuat batas bawah versi. Untuk memasang versi persis
yang terbukti lulus semua test di server Linux (Python 3.10, CPU), ganti dua
baris pemasangan di atas dengan:

```bash
venv/bin/pip install --index-url https://download.pytorch.org/whl/cpu torch==2.14.1+cpu torchvision==0.29.1+cpu
venv/bin/pip install -r requirements-lock-linux.txt
```

> Instalasi bersih di Windows dari paket ini belum diuji.

---

## Kalau kamu ingin memahami apa ini

Baca berurutan:

| Urutan | Berkas | Isi |
|---|---|---|
| 1 | **`docs/STATUS_REVISI_20261006.md`** | **Mulai dari sini.** Status terbaru revisi R1–R5 dan T01–T12, perubahan terakhir 6 Oktober, serta hal yang masih terbuka |
| 2 | `00_BACA_DULU.md` | Gambaran isi paket |
| 3 | `01_TUTORIAL.md` | Cara menjalankan dan memakai aplikasi (tampilan terbaru) |
| 4 | `02_BATASAN_TEKNIS.md` | Batasan yang harus diketahui sebelum menyimpulkan apa pun dari hasilnya |
| 5 | `docs/DELIVERY_WEEK_3.md` | Laporan Week 3: UI, input, XAI, batch, diagnosis OCR, beserta buktinya |
| 6 | `docs/DELIVERY_WEEK_1.md` | Riwayat Minggu 1: apa sistem ini dan cara kerjanya |
| 7 | `docs/DELIVERY_WEEK_2.md` | Riwayat Minggu 2: LIME untuk atribusi kata dan paragraf kesimpulan berbahasa awam |

---

## Apa yang dilakukan sistem ini, singkatnya

Diberi sebuah sampul Majalah Tempo, sistem memprediksi tiga hal — lalu
**menjelaskan dasar keputusannya**.

| Task | Pertanyaan |
|---|---|
| 1 | Isu apa yang dibahas? |
| 2 | Kiasan dari ranah apa yang dipakai? |
| 3 | Siapa yang dikritik? |

Bagian penjelasannya (**XAI**) itulah inti penelitian: sistem menunjukkan
area gambar mana dan kata mana yang memengaruhi keputusannya, sehingga bisa
diperiksa apakah ia benar karena alasan yang benar.

### Yang perlu diketahui sejak awal

- **Model masih sering meleset.** Macro-F1 Task 2 = 0,320, artinya sekitar
  2 dari 3 tebakan domain kiasan salah. Ini alat bantu analisis, bukan alat putus.
- **Demo memakai model baseline.** Percobaan *fine-tuning* penuh menaikkan
  Task 1 dan Task 3, tetapi **menurunkan Task 2** (0,2461 dibanding baseline
  0,320). Karena itu baseline tetap dipakai; hasil *fine-tuning* belum
  dipasang ke aplikasi.
- **Model lebih bertumpu pada logo daripada ilustrasi.** Dari 25 sampul yang
  diperiksa, 22 di antaranya area paling berpengaruh justru kepala sampul.
  Ini temuan yang dilaporkan apa adanya, bukan cacat yang disembunyikan —
  justru inilah gunanya XAI.
- **Peta panas utama kini gabungan tiga task.** Di tab Bukti gambar, peta
  utama adalah gabungan ketiga task (sama untuk semua pilihan task). Peta yang
  menjadi dasar penjelasan ada di blok terpisah **"Bukti task pilihan"**.
- **Pembacaan teks otomatis (OCR) terbatas.** Dengan versi aplikasi
  terakhir, judul terbaca tepat 68–78% pada dua set validasi 60 sampul
  (cenderung optimistis; angka saat kode dibekukan 63–72%), dan 2 dari 3 pada
  foto sampul dari dosen. Sasaran usulan 80% belum tercapai. Selalu periksa
  dan koreksi judul sebelum
  menganalisis. Gambar baru, termasuk berkas yang sama bila dipilih lagi,
  selalu dibaca ulang dan mengganti judul/teks sebelumnya.
- **Ringkasan dan penjelasan berbeda tugas.** Tab Prediksi merangkum ketiga
  task dalam bahasa awam. Tab Penjelasan menjelaskan task pilihan saja.
  Keduanya disusun dari bukti dengan templat, bukan LLM.
- **Analisis butuh waktu.** Sekitar 15–20 detik per analisis di CPU server
  uji, karena atribusi kata LIME membangkitkan 120 varian judul. Batch memakai
  occlusion (lebih cepat) secara bawaan.
- **Ada batas masukan.** Judul ≤300 karakter, teks pendukung ≤2000 karakter,
  unggahan ≤25 MB; gambar dengan sisi >8000 px, rasio >5:1 atau lebih dari
  40 MP ditolak. Batch paling banyak 2 job aktif/antre.

---

## Isi paket

```
MULAI_DARI_SINI.md          berkas ini
setup_windows.bat           setup otomatis Windows (sekali jalan)
jalankan_windows.bat        menjalankan aplikasi di Windows
jalankan_linux.sh           menjalankan aplikasi di Linux/macOS
requirements.txt            daftar pustaka aplikasi (batas bawah versi)
requirements-lock-linux.txt versi pustaka persis yang terbukti lulus semua test di server Linux
requirements-verification.txt  pustaka tambahan untuk uji regresi/HTTP
requirements-browser.txt    pustaka tambahan untuk uji browser (tidak dibutuhkan aplikasi)

00_BACA_DULU.md             gambaran paket
01_TUTORIAL.md              panduan langkah demi langkah
02_BATASAN_TEKNIS.md        batasan teknis
CHANGELOG.md                catatan seluruh perubahan
TEKS_DELIVERY.md            draf pesan serah terima
DELIVERY_MANIFEST.json      SHA256 tiap berkas paket (cek integritas)

docs/                       laporan, rencana, dan dasar keputusan
  STATUS_REVISI_20261006.md   status revisi terbaru (baca ini dulu)
  DELIVERY_WEEK_3.md          laporan Week 3
  DELIVERY_WEEK_1.md          laporan Minggu 1 (riwayat)
  DELIVERY_WEEK_2.md          laporan Minggu 2 (riwayat)
  2026-09-22-keputusan-ocr.md dasar pemilihan OCR
  AUDIT_OCR_URUTAN_20261006.md audit OCR urutan kata
  plans/                      rencana dan hasil tiap pekerjaan

01_notebook/                script eksperimen + notebook asli
02_web_demo/                aplikasi web
03_data/                    dataset 740 sampul + cache fitur
04_hasil_eksperimen/        metrik dan hasil analisis
05_gambar/                  740 gambar sampul
06_gambar_revisi/           3 foto sampul dari dosen (uji unggahan)
```

**Catatan:** folder `venv` tidak disertakan (1,9 GB). Ia dibuat di komputermu
sendiri oleh `setup_windows.bat` (Windows) atau perintah Linux di atas.

---

## Bila ada masalah

| Gejala | Solusi |
|---|---|
| `py bukan perintah yang dikenali` | Pasang ulang Python 3.10, centang `py launcher` |
| `Python 3.10/3.11 tidak ditemukan` | Cek versi: `python --version`. Harus 3.10 atau 3.11 |
| Galat *"long path"* saat memasang | Pindahkan folder ke path pendek, misal `C:\demo_xai` |
| Pemasangan sangat lambat | Antivirus memindai paket besar. Normal, tunggu |
| Port sudah dipakai | Tutup jendela server yang lama |
| Analisis terasa lama (±15–20 detik di CPU server uji) | Wajar — atribusi kata LIME membangkitkan 120 varian judul; di komputer lain waktunya bisa berbeda |

Daftar lengkap ada di `docs/DELIVERY_WEEK_1.md` bagian 2.
