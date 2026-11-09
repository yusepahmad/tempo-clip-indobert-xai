# Jalankan Demo Lokal untuk Uji Pengguna

**Tanggal:** 2026-10-20
**Status:** done

## Tujuan
Menjalankan aplikasi yang tersedia agar pengguna dapat mencoba UI terbaru.

## Ruang Lingkup
- Proses aplikasi lokal pada `127.0.0.1:7860` melalui launcher Linux yang ada.
- Plan ini dan catatan hasil aktual di `CHANGELOG.md`.
- Tidak mengubah source, dependensi, data, model, training maupun ZIP.

## Langkah
1. Cek proses/port agar tidak menjalankan server duplikat.
2. Jalankan `DEMO_XAI_745_FULL/jalankan_linux.sh` dalam sesi persisten.
3. Periksa HTTP halaman, endpoint model dan data sampel serta source UI sorting.
4. Berikan alamat lokal dan jelaskan identitas model aplikasi yang berjalan.

## Risiko & Asumsi
- Runtime yang tersedia tetap CLIP–IndoBERT; E14 QLoRA hasil penelitian belum
  diintegrasikan sebagai backend aplikasi. Menjalankan aplikasi tidak mengubahnya.
- Environment/laptop harus tetap aktif. Pemeriksaan kesiapan HTTP bukan uji
  penuh inferensi upload/OCR; pemakaian pertama bisa memerlukan unduhan encoder.

## Verifikasi
Launcher melewati `check_delivery.py`, server hidup, HTTP halaman dan endpoint
model/sampel sukses, model aktif sesuai manifest dan UI sorting terbaru termuat.

## Hasil Aktual
- Server aktif pada `http://127.0.0.1:7860`, PID 8877, sesi proses persisten.
- Launcher melewati `check_delivery.py`; startup head MTL selesai normal.
- HTTP halaman, `/api/models` dan `/api/samples` sukses; dataset 740 sampel,
  model `clip-indobert-mtl-v1`, source UI sorting terbaru terkonfirmasi.
- Tidak menjalankan inferensi upload/OCR atau mengubah backend ke E14.
- Dicatat pada `CHANGELOG.md`, `[Unreleased] / Added`.
