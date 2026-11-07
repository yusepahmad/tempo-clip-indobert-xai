# Sinkronisasi Notebook Demo ke Dataset 740 Sampul

**Tanggal:** 2026-09-29
**Status:** done

## Tujuan

Client melaporkan bahwa notebook `DEMO_XAI_745_FULL/01_notebook/DEMO_XAI_TEMPO.ipynb`
error saat dijalankan (`KeyError: 'status_validasi'`) dan bahwa "keterangan"
di dalamnya tidak sinkron. Investigasi menunjukkan penyebab akarnya:
notebook ini masih ditulis untuk dataset pilot 189 sampul (`DATASET_189_TASK2_DOMAIN.csv`,
kolom `status_validasi`), padahal proyek sudah pindah ke dataset final
740 sampul (`DATASET_740_TASK2_DOMAIN.csv`, 15 kolom, **tanpa** kolom
`status_validasi`) — ini terlihat dari `docs/plans/2026-09-28-week2-lime-dan-kesimpulan.md`
yang menegaskan "Dataset tetap 740 baris, 15 kolom" sebagai keputusan final,
dan dari folder hasil eksperimen `04_hasil_eksperimen/*_740.json` yang sudah ada.

Jadi notebook `01_notebook` adalah sisa versi lama yang belum di-update
mengikuti pipeline `02_web_demo` yang sudah dipakai. Tujuannya adalah
menyinkronkan notebook ini: path data, jumlah sampul, dan seluruh narasi
markdown/angka yang menyebut "189" → memakai data dan angka 740 yang benar,
serta memperbaiki error `status_validasi`.

## Ruang Lingkup

**Disentuh:**
- `DEMO_XAI_745_FULL/01_notebook/DEMO_XAI_TEMPO.ipynb`
  - Cell 5 (kode): path `DATA_CSV`/`FITUR_NPZ` → arahkan ke berkas `_740`
  - Cell 7 (kode): ganti `df["status_validasi"].value_counts()` dengan
    ringkasan yang memakai kolom yang benar-benar ada (mis. `eligibility`,
    atau dihapus bila tidak relevan lagi)
  - Semua sel markdown yang menyebut "189 sampul" / "target 745" diperbarui
    ke "740 sampul" (Cell 0, 6, 9, 11, 15, 42)
  - String print di sel kode yang menyebut "189" (Cell 14, 28, 39, 41)
  - Tabel PERINGATAN PENTING (Cell 0) dan Bagian 15 (Cell 42): angka
    Macro-F1, hasil leave-one-out, dan status data diperbarui memakai hasil
    nyata yang sudah ada di `04_hasil_eksperimen/hasil_mtl_740_task2domain.json`,
    `analisis_recall_per_kelas_740.csv`, `hasil_uji_satu_gambar_740.json`,
    dan `analisis_zona_740.json` — bukan angka karangan baru
- `CHANGELOG.md`

**Tidak disentuh:**
- `03_data/*.csv`, `05_gambar/` — data tidak diubah, hanya path rujukan
- `02_web_demo/` — sudah sinkron dengan 740, tidak perlu diubah
- Arsitektur model (`KepalaMTL`), metode Grad-CAM/atribusi kata — tidak diubah
- Tidak menjalankan ulang training penuh dari nol di notebook (butuh unduh
  CLIP+IndoBERT ~1.5GB dan waktu lama); angka baru diambil dari hasil
  eksperimen 740 yang sudah tersimpan di `04_hasil_eksperimen/`

## Langkah

1. Ganti `DATA_CSV`/`FITUR_NPZ` di Cell 5 ke `DATASET_740_TASK2_DOMAIN.csv`
   dan `fitur_clip_indobert_740.npz`
2. Perbaiki Cell 7: hapus/ganti baris `status_validasi` dengan info yang
   valid dari kolom yang ada (misalnya ringkasan `eligibility`)
3. Update seluruh teks markdown "189" → "740" secara konsisten. Dataset 740
   sampul diperlakukan sebagai **dataset final** (dikonfirmasi user) — hapus
   framing "dari target 745" dan proyeksi terkait, ganti dengan pernyataan
   bahwa 740 adalah jumlah data final penelitian
4. Update angka di tabel PERINGATAN PENTING (Cell 0) dan Bagian 15 (Cell 42)
   memakai angka nyata dari `04_hasil_eksperimen/`:
   - Macro-F1 Task 2 domain: 0,320 (fusion MTL, dari `hasil_mtl_740_task2domain.json`)
   - Leave-one-out: 7 dari 21 prediksi benar (7 sampul × 3 task, dari `hasil_uji_satu_gambar_740.json`)
   - Zona dominan: 22 dari 25 sampul masih di zona kepala (dari `analisis_zona_740.json`)
5. Cek ulang seluruh notebook untuk referensi kolom yang tidak ada di CSV 740
   (`sample_id`, `headline_verified`, dll — sudah divalidasi cocok)
6. Update `CHANGELOG.md` dengan entry perubahan ini

## Risiko & Asumsi

- **Keputusan dikonfirmasi user (29 Sep):** dataset 740 sampul adalah dataset
  **final** penelitian, bukan lagi progres menuju 745. Seluruh narasi "dari
  target 745" di notebook dihapus/diganti.
- **Risiko:** notebook tidak dijalankan ulang end-to-end (train dari nol)
  karena requirement compute besar; angka yang dipakai bersumber dari hasil
  eksperimen tersimpan, bukan dari eksekusi langsung sel-sel notebook ini.
  Perlu disebutkan ke client bahwa notebook idealnya dijalankan sekali oleh
  mereka untuk memverifikasi ulang secara langsung.
- **Risiko kecil:** folder induk bernama `DEMO_XAI_745_FULL` tapi data di
  dalamnya 740 — nama folder tidak diubah karena di luar scope (menyentuh
  banyak referensi path lain).

## Verifikasi

1. Notebook dapat dijalankan dari awal tanpa `KeyError` pada Cell 7
2. `df.shape[0]` menunjukkan 740, bukan 189
3. Tidak ada lagi teks "189 sampul" tersisa di seluruh notebook (grep bersih)
4. Angka di PERINGATAN PENTING dan Bagian 15 konsisten dengan file JSON/CSV
   di `04_hasil_eksperimen/`
