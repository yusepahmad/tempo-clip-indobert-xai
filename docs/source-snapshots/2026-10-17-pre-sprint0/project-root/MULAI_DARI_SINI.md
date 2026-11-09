# Mulai dari sini

**Demo XAI — Dekoding Metafora Sampul Majalah Tempo**
Paket delivery Minggu 2 · 28 September 2026

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

---

## Kalau kamu ingin memahami apa ini

Baca berurutan:

| Urutan | Berkas | Isi |
|---|---|---|
| 1 | **`docs/DELIVERY_WEEK_1.md`** | **Mulai dari sini.** Penjelasan lengkap: apa sistem ini, cara kerjanya, dan apa yang dikerjakan Minggu 1 |
| 2 | **`docs/DELIVERY_WEEK_2.md`** | Minggu 2: LIME untuk atribusi kata, dan paragraf kesimpulan berbahasa awam |
| 3 | `00_BACA_DULU.md` | Gambaran isi paket |
| 4 | `01_TUTORIAL.md` | Panduan langkah demi langkah |
| 5 | `02_BATASAN_TEKNIS.md` | Batasan yang harus diketahui sebelum menyimpulkan apa pun dari hasilnya |

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
- **Model lebih bertumpu pada logo daripada ilustrasi.** Dari 25 sampul yang
  diperiksa, 22 di antaranya area paling berpengaruh justru kepala sampul.
  Ini temuan yang dilaporkan apa adanya, bukan cacat yang disembunyikan —
  justru inilah gunanya XAI.
- **Pembacaan teks otomatis tidak sempurna.** Periksa dan perbaiki kolom teks
  sebelum menganalisis.
- **Analisis butuh waktu.** Sekitar 20–60 detik per sampul, karena model
  dilatih ulang dan atribusi LIME membangkitkan ratusan varian judul.

---

## Isi paket

```
MULAI_DARI_SINI.md          berkas ini
setup_windows.bat           setup otomatis Windows (sekali jalan)
jalankan_windows.bat        menjalankan aplikasi di Windows
jalankan_linux.sh           menjalankan aplikasi di Linux/macOS
requirements.txt            daftar pustaka

00_BACA_DULU.md             gambaran paket
01_TUTORIAL.md              panduan langkah demi langkah
02_BATASAN_TEKNIS.md        batasan teknis
CHANGELOG.md                catatan seluruh perubahan

docs/                       laporan, rencana, dan dasar keputusan
  DELIVERY_WEEK_1.md          laporan Minggu 1 (baca ini dulu)
  DELIVERY_WEEK_2.md          laporan Minggu 2
  2026-09-22-keputusan-ocr.md dasar pemilihan OCR
  plans/                      rencana tiga minggu

01_notebook/                script eksperimen + notebook asli
02_web_demo/                aplikasi web
03_data/                    dataset 740 sampul + cache fitur
04_hasil_eksperimen/        metrik dan hasil analisis
05_gambar/                  740 gambar sampul
```

**Catatan:** folder `venv` tidak disertakan (1,9 GB). Ia dibuat di komputermu
sendiri oleh `setup_windows.bat`.

---

## Bila ada masalah

| Gejala | Solusi |
|---|---|
| `py bukan perintah yang dikenali` | Pasang ulang Python 3.10, centang `py launcher` |
| `Python 3.10/3.11 tidak ditemukan` | Cek versi: `python --version`. Harus 3.10 atau 3.11 |
| Galat *"long path"* saat memasang | Pindahkan folder ke path pendek, misal `C:\demo_xai` |
| Pemasangan sangat lambat | Antivirus memindai paket besar. Normal, tunggu |
| Port sudah dipakai | Tutup jendela server yang lama |
| Analisis 10–40 detik | Wajar — model dilatih ulang tiap analisis mode dataset |

Daftar lengkap ada di `docs/DELIVERY_WEEK_1.md` bagian 2.
