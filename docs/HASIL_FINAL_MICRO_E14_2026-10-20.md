# Hasil Final MICRO-E14 — Joint QLoRA Lima Fold

**Tanggal penyelesaian:** 20 Oktober 2026, pukul 00.00 WIB.  
**Status evaluasi:** COMPLETE; lima fold VERIFIED; tepat 740 prediksi OOF.  
**Status target tiga task ≥0,70:** belum tercapai, baik Micro-F1 maupun Macro-F1.

## Ringkasan

Hasil fold 3 dan 5 telah diambil dari Kaggle. Semua fold diverifikasi ulang
dan digabungkan sesuai urutan dataset tetap, tanpa duplikasi ID. MICRO-E14
menjadi kandidat terbaik pada siklus MICRO menurut minimum Micro-F1 ketiga
task, tetapi itu tidak berarti semua target sudah lulus.

| Task | Micro-F1 | Macro-F1 | Prediksi benar | Micro ≥0,70 | Macro ≥0,70 |
| --- | ---: | ---: | ---: | --- | --- |
| Task 1 — Isu utama | 0,720270 | 0,673321 | 533/740 | Lulus | Belum |
| Task 2 — Domain sumber metafora | 0,566216 | 0,510282 | 419/740 | Belum | Belum |
| Task 3 — Tipe entitas utama | 0,667568 | 0,595480 | 494/740 | Belum | Belum |

Micro-F1 identik dengan accuracy untuk klasifikasi multiclass single-label
ini. Macro-F1 adalah rata-rata F1 antarkelas, bukan nama lain untuk Micro-F1.
Target awal Macro-F1 tidak dianggap terpenuhi hanya karena Task 1 lulus Micro.

## Perbandingan dengan E11 pada 740 OOF

| Model / Micro-F1 | Task 1 | Task 2 | Task 3 | Minimum |
| --- | ---: | ---: | ---: | ---: |
| MICRO-E11 | 0,581081 | 0,559459 | 0,532432 | 0,532432 |
| MICRO-E14 | 0,720270 | 0,566216 | 0,667568 | 0,566216 |
| Selisih, poin persentase | +13,92 | +0,68 | +13,51 | +3,38 |

Perbaikan besar terjadi pada Task 1 dan Task 3. Kenaikan Task 2 hanya sekitar
0,68 poin persentase terhadap E11, sehingga menjadi pembatas skor minimum.
Ranking ini berdasarkan hasil CV internal yang berulang dipakai; selisih
angka tidak otomatis membuktikan signifikansi atau generalisasi eksternal.

Hasil pilot E13 `0,7227 / 0,5882 / 0,6807` berasal dari 119 inner-validation
yang dipakai memilih epoch. Angka tersebut tidak digabung dengan E14 dan tidak
dianggap hasil 740 OOF. Pembanding E12 structured decoder juga tidak mengganti
hasil E14. Rekap 11 eksperimen selesai tersedia pada `micro_f1_comparison.csv`.

## Hasil per fold

Semua job Kaggle tetap version 1; tidak ada push ulang atau training baru
selama pengambilan dan verifikasi ini.

| Fold | Epoch terpilih | Outer-test | Micro-F1 Task 1 | Task 2 | Task 3 | Status |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | 3 | 148 | 0,695946 | 0,608108 | 0,648649 | VERIFIED |
| 2 | 1 | 148 | 0,743243 | 0,520270 | 0,668919 | VERIFIED |
| 3 | 3 | 148 | 0,729730 | 0,554054 | 0,628378 | VERIFIED |
| 4 | 2 | 148 | 0,709459 | 0,554054 | 0,709459 | VERIFIED |
| 5 | 3 | 148 | 0,722973 | 0,594595 | 0,682432 | VERIFIED |

Setiap outer fold memakai satu adapter joint untuk ketiga task. Epoch dipilih
hanya dari inner-validation sesuai protokol, kemudian adapter di-reset dan
di-refit pada seluruh 592 outer-training. Tidak memilih epoch berbeda untuk
masing-masing task berdasarkan skor outer-test.

## Pemeriksaan yang lulus

1. Hash dataset aktual cocok dengan frozen protocol; hash source worker dan
   kelima launcher tetap cocok dengan build manifest. Fold sumber E42 tidak
   berubah. Data/label tidak diedit untuk menaikkan hasil.
2. Masing-masing fold berisi tepat 148 ID outer-test unik dan sesuai mapping;
   gabungan tepat 740 ID unik, masing-masing muncul satu kali, urutan kembali
   mengikuti dataset. Kelima test fold saling disjoint.
3. Truth pada CSV prediksi sama dengan label dataset untuk ketiga task.
   Inner-training/validation/test disjoint; seleksi epoch dan jumlah epoch
   refit cocok dengan aturan maksimum (minimum Micro-F1, mean), tie paling awal.
4. Seluruh probabilitas finite dan nonnegatif, jumlah tiap baris ≈1; argmax
   cocok dengan prediksi kelas. Micro-F1 dihitung ulang dan sama dengan accuracy.
5. Micro-F1 dan Macro-F1 agregat dihitung ulang secara independen dari CSV dan
   cocok dengan `result.json` serta `metrics.json`.
6. Hash 740 gambar lokal cocok dengan dataset dan input audit remote. Tiap
   fold memiliki 2.220 pasangan unik `(sample_id, task)`; audit input termasuk
   hash prompt/gambar serta jumlah token identik di kelima fold.
7. Hash prediksi/split/input-audit cocok dengan hasil remote. Semua 33 entry
   pada manifest agregat/per-fold E14 dan 159 entry manifest siklus MICRO lulus
   pemeriksaan setelah rekap. File ledger/log yang mutable tidak dimasukkan
   sebagai bukti hash konten statis.
8. Lima tes CPU protokol lulus, termasuk pemeriksaan split, payload, reset
   adapter/refit dan penolakan label prediksi yang dimanipulasi.

Ledger sekarang `status: complete` dengan kelima fold `VERIFIED`. Scheduler
one-shot sudah selesai normal; tidak perlu memantau antrean E14 lagi.

## Jarak terhadap target

Untuk Micro-F1 ≥0,70 pada 740 sampel diperlukan minimal 518 prediksi benar
per task. Task 1 sudah melampaui ambang. Task 2 masih kurang 99 prediksi benar
neto (13,38 poin persentase); Task 3 kurang 24 (3,24 poin persentase).
Ini perhitungan jarak skor, bukan estimasi peluang keberhasilan eksperimen baru.

Untuk Macro-F1, ketiga task masih di bawah 0,70. Hasil ini menyelesaikan
evaluasi E14, bukan menyelesaikan seluruh target penelitian. Belum dilakukan
eksperimen lanjutan atau perubahan model aplikasi pada pekerjaan ini.

## Artefak dan hash

Folder hasil:
`DEMO_XAI_745_FULL/04_hasil_eksperimen/next_research_20261017/06_micro_f1/MICRO_E14_joint_qlora_oof/`

- `result.json`: metrik lengkap dan detail kelima fold.
- `predictions.csv`: 740 prediksi OOF final.
- `metrics.json`, `verification.json`, `decision.md`, `manifest_sha256.json`.
- `fold1/` sampai `fold5/`: hasil, prediksi, split, audit dan verifikasi per fold.
- `scheduler_state.json`: ledger complete, semua handle version 1.
- Rekap siklus satu folder di atas: `micro_f1_report.md`,
  `micro_f1_comparison.csv`, `manifest_sha256_all.json`.

SHA-256 protokol:
`7b1eb1fdaf8547e842df793726e106b1d29b222b16ef3d9b672388d9d46ec65e`.

SHA-256 worker:
`cb09acda21117f0acba38233fca382ec9916b08c5c73f297fa0f70c9469003ed`.

SHA-256 CSV 740 OOF:
`65590694cb53049daf266e491a447be49ebeba42a9d707147bfad80e50746167`.

## Batas interpretasi dan perubahan

Ini evaluasi internal pada korpus tetap yang sudah berulang dipakai untuk
eksplorasi; pilot ikut memengaruhi desain protokol. Tidak ada test eksternal
baru. Seluruh verifikasi artefak lulus, tetapi itu bukan bukti target tercapai
atau validasi independen terhadap generalisasi.

Checkpoint adapter besar tidak diunduh atau diuji ulang lokal; hash adapter
dicatat dari output remote. Model aplikasi tetap `clip-indobert-mtl-v1`;
integrasi QLoRA, clean Windows, uji pengguna, dan pengujian OCR baru tidak
dilakukan di sini. ZIP R3 yang sudah dibagikan tetap snapshot sebelumnya,
bukan paket baru berisi hasil E14 final ini.

Plan pekerjaan dimulai 19 Oktober dan selesai setelah pergantian hari:
[verifikasi final E14](plans/2026-10-19-verifikasi-final-e14-oof.md).
Perubahan dicatat pada `CHANGELOG.md`, `[Unreleased] / Added`.
