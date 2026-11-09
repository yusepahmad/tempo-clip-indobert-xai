# Handoff lanjutan di server

Tanggal: 2026-10-06. Arsip `TEMPO_SERVER_HANDOFF_20261006.zip` adalah paket pekerjaan untuk dilanjutkan, **bukan delivery final client**.

## Mulai membaca

1. `docs/AUDIT_DELIVERY_WEEK3_20261006.md`: verdict dan matriks R1–R5/T01–T12.
2. `docs/plan-revisi-demo-xai-tempo.md`: acuan revisi; target metrik di sana merupakan usulan.
3. `docs/DELIVERY_WEEK_3.md` dan `docs/HASIL_FULL_TRAINING_KAGGLE.md`: bukti teknis/model.
4. `AGENTS.md`: wajib plan sebelum perubahan, simpan di docs/plans dan catat hasil di CHANGELOG.

Semua path berikut relatif folder `DEMO_XAI_745_FULL` setelah ekstraksi.

## Status dan keputusan yang harus dipertahankan

- Source UI terbaru berada di `02_web_demo/index.html`: panduan tiga langkah, preview nyata, tab hasil, loading OCR/analisis, textarea pendukung 5 baris dan scroll vertikal.
- Bug textarea self-closing **sudah diperbaiki**. Jangan serialisasi textarea menjadi `<textarea .../>`. Verifikasi struktur dengan HTML5, bukan hanya parser toleran.
- Source/backend baseline berfungsi; audit 740/740 berhasil, ekspor/aset/pemulihan lulus. Uji Windows lama adalah backend/folder terisolasi, bukan browser UI terakhir atau clean-install paket.
- Codebook resmi tidak tersedia. User meminta codebook operasional 25 kelas dibuat; jangan kembali meminta sumber resmi yang tidak ada.
- Tabel ground truth disiapkan dan tiga tinjauan sub-agent sudah dilakukan atas permintaan user; ini bukan uji manusia. Usulan transkripsi tidak mengubah dataset.
- Full Kaggle COMPLETE dan audit OOF lulus. Macro-F1 Task1/2/3 = 0,5139 / 0,2461 / 0,3699. Baseline demo tetap dipakai karena Task2 baseline 0,3197 lebih baik. Checkpoint Kaggle belum diunduh/diintegrasikan; laporan fine-tuning bukan perilaku demo.
- OCR produksi 19/30 tepat pada set diagnosis, gambar dosen 2/3. Sasaran usulan 80% belum tercapai; koreksi manual tetap diperlukan. Beamsearch/kandidat selector tidak diterapkan hanya untuk menaikkan angka.
- Foto asli GULA-GULA: LIME Task2 dengan judul manual dan supporting kosong menghasilkan DEMO positif; ini bukan validasi kelas prediksi. Artefak ada di `04_hasil_eksperimen/revisi_week3/audit_gula_original_lime.json`.

## Pekerjaan berikutnya, urut prioritas

1. **R5:** client meminta satu peta utama gabungan semua task. UI satuan sekarang memakai `d.heatmap_url` task pilihan; backend menyediakan `heatmap_padu_url`. Tampilkan ringkasan gabungan dengan label yang jelas, lalu pertahankan bukti task pilihan di bagian teknis. Jangan menghubungkan peta gabungan dengan klaim atribusi satu task secara keliru.
2. Uji visual browser desktop/mobile: pilih dataset, unggah gambar/OCR, edit teks panjang, loading/sukses/gagal, ganti task/gambar ketika request aktif, tab/keyboard dan batch/review/ekspor. Jangan mengklaim screenshot/usability bila hanya memakai VM/parser/HTTP.
3. Sinkronkan tutorial, batasan, teks delivery dan laporan status dengan UI/model terbaru.
4. Bangun paket final terpisah setelah penutupan; cek source, ZIP dan launcher dari setup bersih Windows/Linux.
5. Pisahkan acceptance demo dari sasaran riset OCR/ground truth/E01/E02. Jangan menyebut semua revisi 100% selesai sebelum bukti mendukung.

## Transfer dan setup Linux

Alamat/OS server belum diberikan; instruksi ini mengasumsikan Linux dan Python 3.10/3.11. Ganti `USER@SERVER` dengan tujuanmu.

Di komputer asal:

```bash
scp TEMPO_SERVER_HANDOFF_20261006.zip USER@SERVER:~/
```

Di server (unzip, Python 3.10/3.11 dan tmux harus tersedia):

```bash
mkdir -p ~/tempo-server
unzip ~/TEMPO_SERVER_HANDOFF_20261006.zip -d ~/tempo-server
cd ~/tempo-server/DEMO_XAI_745_FULL
python3.11 -m venv venv
venv/bin/python -m pip install --upgrade pip
venv/bin/python -m pip install --index-url https://download.pytorch.org/whl/cpu torch torchvision
venv/bin/python -m pip install -r requirements.txt
venv/bin/python -m pip install -r requirements-verification.txt
```

Gunakan `python3.10` jika itu versi yang tersedia. Ini setup CPU untuk meneruskan demo; pemakaian GPU server dapat disiapkan terpisah setelah jenis GPU/driver diketahui. Node.js dibutuhkan untuk regresi JavaScript. Encoder CLIP/IndoBERT dan model EasyOCR diunduh pada pemakaian pertama: internet dan ruang disk cukup diperlukan. Jangan memasang `HF_HUB_OFFLINE=1` sebelum cache model tersedia.

## Menjalankan tanpa bergantung pada SSH aktif

```bash
cd ~/tempo-server/DEMO_XAI_745_FULL
tmux new -s tempo-ui
cd 02_web_demo
OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 ../venv/bin/python -u -c "import torch; torch.set_num_threads(4); from app import app; app.run(host='127.0.0.1', port=7861, debug=False)"
```

Detach tmux dengan **Ctrl+B lalu D**. Kembali dengan `tmux attach -t tempo-ui`. Ctrl+C di dalam tmux menghentikan server. Ini server demo untuk review melalui tunnel, bukan konfigurasi hosting publik.

Di komputer asal, buka terminal baru:

```bash
ssh -N -L 8850:127.0.0.1:7861 USER@SERVER
```

Buka **http://127.0.0.1:8850**. Port lokal 8850 dipakai agar tidak berbenturan dengan demo lokal 7861. Jika memakai launcher bawaan, port defaultnya 7860; sesuaikan tunnel dan URL verifikasi. Jangan membuka port Flask langsung ke publik untuk kebutuhan review ini.

## Verifikasi dari root paket

```bash
venv/bin/python 01_notebook/test_ui_html5.py
venv/bin/python 01_notebook/test_week3_regressions.py
venv/bin/python 01_notebook/test_week3_training_audit.py
node 01_notebook/test_loading_ui.js
node 01_notebook/test_week3_state.js
node 01_notebook/test_workspace_ui.js
```

Script HTTP historis menulis path berawalan `DEMO_XAI_745_FULL`, sehingga jalankan dari folder induk:

```bash
cd ~/tempo-server
TEMPO_DEMO_URL=http://127.0.0.1:7861 DEMO_XAI_745_FULL/venv/bin/python DEMO_XAI_745_FULL/01_notebook/verify_week3_http.py
```

Jangan menjalankan `verify_scale740.py`/`finalize_week3_delivery.py` begitu saja: keduanya mengacu job lokal lama, port tertentu dan layout repo asal. Bukti skala lama ada dalam paket, tetapi job/aset `_jobs` tidak dipindah. Untuk uji skala baru buat job/launch record baru dan sesuaikan audit secara eksplisit. Jangan menulis metrik akurasi dari batch in-sample.

## Isi dan batas paket

Source terbaru, 740 gambar/data/fitur baseline, docs/plan/aturan, script training/QA dan metrik fine-tuning disertakan. Venv, cache, job/aset lokal, checkpoint besar, arsip bersarang dan credentials tidak disertakan. Tiga foto dosen disalin ke `06_gambar_revisi/` untuk regresi lanjutan; file asli tidak diedit. URL heatmap pada ekspor lama bukan tautan portabel. Dataset/label/image asli harus tetap dipertahankan.

## Prompt untuk Codex di server

Salin setelah membuka folder paket:

> Baca AGENTS.md, docs/HANDOFF_SERVER.md dan docs/AUDIT_DELIVERY_WEEK3_20261006.md. Lanjutkan penutupan revisi client dari source ini. Prioritas pertama selaraskan R5 heatmap gabungan dengan bukti task pilihan tanpa klaim lintas task, kemudian smoke UI browser, sinkronisasi dokumentasi dan paket final/setup bersih. Pertahankan dataset/label dan baseline; model Kaggle belum diintegrasikan. Codebook operasional serta evaluasi agen sudah dibuat atas instruksi saya. Buat plan di docs/plans sebelum perubahan dan catat CHANGELOG setelah perubahan. Jangan mengklaim seluruh revisi selesai tanpa bukti. Jika browser/server belum tersedia, jelaskan keterbatasan dan lanjutkan pekerjaan independen.
