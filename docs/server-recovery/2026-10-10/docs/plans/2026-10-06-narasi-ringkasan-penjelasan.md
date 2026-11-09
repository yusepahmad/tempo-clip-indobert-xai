# Narasi Ringkasan dan Penjelasan yang Lebih Luwes

**Tanggal:** 2026-10-06
**Status:** done (2026-10-06)

## Tujuan
User menilai "Ringkasan interpretasi" (tab Prediksi) dan tab Penjelasan terlalu kaku. Temuan:
1. Kedua tab menampilkan paragraf yang **identik** (`penjelasan = [kesimpulan.paragraf]`).
2. Paragraf berupa rantai ±8 kalimat templat dengan peringatan berulang ("zona ini tidak mengidentifikasi objek", "pada metode atribusi yang dipakai", penutup baku) dan istilah teknis (task, zona dominan, atribusi).
3. Catatan anotator (mis. "Posisi di sudut menggambarkan tekanan politik…") dan perbedaan label anotator tidak dipakai di narasi.
4. Ringkasan hanya membahas satu task, padahal R3 meminta kesimpulan awam (isu, siapa yang disorot, cara menyampaikan).

Keputusan user (2026-10-06): **tetap template berbasis bukti, bukan LLM**; **ringkasan membahas tiga task sekaligus**, tab Penjelasan khusus alasan task pilihan.

## Ruang Lingkup
- `02_web_demo/explanation_evidence.py`:
  - Fungsi baru `ringkas(pred, headline, label=None, catatan=None)` → `{paragraf, bagian:[{asal, teks}], keyakinan, tanda}`. Kalimat awam tiga task: isu (label tampil, huruf kecil aman, "&" → "dan"), pihak (frasa awam per kelas Task 3), kiasan (frasa + maksud umum dari `_FRASA_DOMAIN`/`_MAKSUD_DOMAIN` di `xai_core.py`, dinyatakan sebagai makna umum jenis kiasan, bukan makna sampul ini). Tingkat keyakinan dari skor tiga task (tanpa menyebut persen di ringkasan). Mode dataset: perbandingan dengan label anotator dan kutipan `pemetaan_makna` (asal ANOTATOR).
  - `explain(...)` tetap terikat task/kelas pilihan; kunci lama (`paragraf, strategi, bukti, alasan_ragu, dapat_dipercaya, task_id, class_id, asal`) dan logika strategi tidak berubah. Tambah `blok:[{label, asal, teks}]` (Mengapa <kelas>? [MODEL], Arti kelas ini [CODEBOOK], Catatan anotator [ANOTATOR, bila ada]) dan `cek:[...]` ("Yang perlu dicek", peringatan dikumpulkan). Parameter opsional baru `label=None` untuk membandingkan label anotator task itu. `paragraf` = gabungan blok + cek (kompatibel batch/ekspor).
  - Zona disebut sebagai posisi ("bagian atas sampul (area logo dan judul kecil)", "bagian tengah, tempat ilustrasi biasanya berada", "bagian bawah (area judul besar dan barcode)"); tidak menamai objek.
- `02_web_demo/app.py`: panggil `ringkas()`; `penjelasan` dari `kesimpulan["blok"]`; respons tambah `ringkasan`.
- `02_web_demo/index.html`: kartu "Ringkasan interpretasi" merender `ringkasan.bagian` (dengan penanda asal) dan tanda keyakinan; tab Penjelasan merender blok + daftar "Yang perlu dicek"; ringkasan batch memakai `ringkasan.paragraf` bila ada. Render via `textContent` (aman).
- Regresi baru `01_notebook/test_narasi_ringkasan.py`.
- Dokumen terdampak: `02_BATASAN_TEKNIS.md` bagian 5, `01_TUTORIAL.md` B.5/E, `docs/STATUS_REVISI_20261006.md` R3.
- TIDAK: model, atribusi, dataset/label, codebook, LLM, peta panas.

## Langkah
1. Implementasi `ringkas()` + perluasan `explain()`; app.py; index.html.
2. Test baru + regresi lama (termasuk `test_five_strategies_and_task_binding` tanpa diubah).
3. Restart `tempo-ui` (bind 0.0.0.0 sesuai keputusan user), periksa contoh nyata: sampul dataset AKBAR (label berbeda), satu sampul dataset yang cocok, foto dosen GULA (tanpa kata positif), satu NON_METAFORA.
4. Smoke browser ulang (tag baru) + screenshot tab Prediksi/Penjelasan diperiksa visual.
5. Update dokumen terdampak, CHANGELOG, plan.

## Risiko & Asumsi
- Frasa awam Task 3 dan penggabungan isu ditulis baru (bukan dari dataset); hanya parafrasa nama kelas, tidak menambah klaim.
- `_MAKSUD_DOMAIN` adalah makna umum jenis kiasan; harus selalu dibingkai "kiasan semacam ini biasanya…", bukan klaim tentang sampul.
- Perbandingan anotator hanya untuk mode dataset (leave-one-out); unggahan tidak punya label.
- Tetap tidak membuktikan prediksi benar; tanda keyakinan memakai skor belum terkalibrasi, sehingga disebut "dugaan" bila rendah.

## Verifikasi
- `test_narasi_ringkasan.py`: ringkasan menyebut tiga aspek; ringkasan ≠ penjelasan; penjelasan tidak menyebut task lain; tanpa kata positif dinyatakan; zona tidak menamai objek; BUMN tetap kapital; NON_METAFORA; label anotator berbeda disebut; unggahan tanpa blok anotator.
- Regresi lama Python/JS lulus; HTTP contoh nyata dibaca; smoke browser lulus; screenshot diperiksa.

## Hasil (2026-10-06)
- `explanation_evidence.py`: `ringkas()` baru (tiga task, keyakinan, perbandingan anotator) dan `explain()` dengan `blok`/`cek`; kunci dan logika strategi lama tetap (`test_five_strategies_and_task_binding` lulus tanpa diubah). Frasa domain disalin dari `xai_core.py` agar modul tidak memuat torch.
- `app.py`: `ringkasan` di respons, `penjelasan` dari blok, label anotator diteruskan. `index.html`: kartu ringkasan berpenanda asal + tanda keyakinan; tab Penjelasan berupa blok + "Yang perlu dicek"; ringkasan batch memakai `ringkasan.paragraf`; render via DOM/`textContent`.
- Setelah membaca contoh nyata (AKBAR label berbeda, NON_METAFORA, JATUH BANGUN AHOK cocok 3/3, GULA unggahan) dirapikan: kutipan anotator tanpa titik ganda, entitas anotator dikutip, peringatan zona tidak mengulang kalimat.
- Test: `test_narasi_ringkasan.py` 6 lulus; 5 Python + 4 JS lama lulus. Smoke browser `browser_smoke_20261006_narasi.json` **83/83**; screenshot tab Prediksi dan Penjelasan diperiksa visual.
- Dokumen: `02_BATASAN_TEKNIS.md` bagian 5, `01_TUTORIAL.md` B.5/E, `docs/STATUS_REVISI_20261006.md` R3.
- Server `tempo-ui` direstart tetap bind 0.0.0.0:7861.
