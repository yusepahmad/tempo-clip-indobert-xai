# Web CLIP–IndoBERT rich256

Backend default source web terbaru adalah `clip-indobert-tail-rich256-v1`, kandidat `RII_TAIL_RICH256`. Ini berbeda dari E42 yang tetap menjadi model utama penelitian R4 berdasarkan Macro-F1. Baseline historis tersedia hanya dengan pilihan eksplisit `TEMPO_BACKEND=clip-indobert-mtl`.

| Metrik OOF 740 sampel | Task 1 | Task 2 | Task 3 |
|---|---:|---:|---:|
| Micro-F1 | 0.493243 | 0.524324 | 0.514865 |
| Macro-F1 | 0.461915 | 0.496684 | 0.400093 |

Pemilihan web dilakukan post-hoc dengan memaksimalkan minimum Micro-F1 tiga task di antara kandidat joint CLIP–IndoBERT yang memiliki 740 prediksi OOF lengkap. Ini bukan klaim terbaik pada setiap task atau unggul atas Qwen. CI penelitian tetap kondisional pada prediksi/korpus dan tidak menghapus bias seleksi.

## Model dan input

CLIP-L14 full/crop + IndoBERT front 10 blok beku / tail 2 blok terlatih + shared 256 + tiga head joint. Lima checkpoint asli Kaggle diverifikasi SHA-256, tanpa training ulang saat startup.

- Dataset: checkpoint outer-fold yang tidak melatih ID tersebut, termasuk batch dataset dan teks yang diedit. Nilai benchmark berlaku untuk input canonical; teks edit bukan benchmark baru.
- Upload baru: rerata probabilitas kelima model. Kualitas ensemble upload belum dievaluasi terpisah. Skor softmax belum dikalibrasi.
- Selain headline/supporting, model rich membutuhkan deskripsi gambar, observasi sumber visual dan alasan visual. Upload wajib mengisi ketiganya; dataset memakai JSONL canonical yang hash-nya diverifikasi. Tidak ada generasi Qwen tambahan pada web.
- XAI memakai model/konteks yang sama dengan prediksi. Atribusi teks mengubah headline dengan supporting/deskripsi visual tetap. Batch unggahan belum didukung karena membutuhkan keterangan per gambar; batch dataset didukung.

## Akses repository dan Release

Repository teramati **private** pada 8 November 2026; task ini tidak mengubah visibilitas. Link source/Release memerlukan akun GitHub yang memiliki akses. Unduhan anonim `--download` memerlukan repository public. Untuk kondisi private, unduh asset ZIP lewat browser yang sudah login atau GitHub CLI:

```bash
gh release download v2026.11.08-web-rich256 --repo project-owner/tempo-clip-indobert-xai --pattern 'TEMPO_WEB_RICH256_MODEL_20261108.zip' --dir /tmp/tempo-model
```

Lalu ganti langkah `--download` di bawah dengan `--archive /tmp/tempo-model/TEMPO_WEB_RICH256_MODEL_20261108.zip`. Kedua jalur memeriksa delapan hash file sebelum instalasi. Jangan memasukkan credential ke source/notebook.

## Reproduksi dari clone

Gunakan Python 3.10 dan ruang disk untuk checkpoint/cache/backbone. Bobot tidak disimpan dalam Git. Model ZIP pada Release web berisi delapan artefak yang hash-nya tercatat pada `06_models/clip-indobert-tail-rich256-v1/manifest.json`; backbone diambil dari revisi Hugging Face yang dipin.

```bash
python3 -m venv .venv-web
.venv-web/bin/python -m pip install -r DEMO_XAI_745_FULL/02_web_demo/requirements-web-lock.txt
.venv-web/bin/python DEMO_XAI_745_FULL/02_web_demo/prepare_tail_assets.py --download
.venv-web/bin/python DEMO_XAI_745_FULL/02_web_demo/prepare_tail_assets.py --check-only
.venv-web/bin/python DEMO_XAI_745_FULL/02_web_demo/test_tail_serving.py
.venv-web/bin/python DEMO_XAI_745_FULL/02_web_demo/serve_tail.py
```

`prepare_tail_assets.py --archive /path/model.zip` memasang arsip lokal sebagai alternatif unduhan Release. Hash seluruh arsip diverifikasi pada jalur download; seluruh delapan file selalu diverifikasi sebelum instalasi. `TEMPO_TAIL_ASSET_DIR` dapat mengalihkan direktori artefak besar. Cache Hugging Face dapat dialihkan memakai `HF_HOME` sebelum persiapan dan serving.

Launcher memakai CPU, satu worker/empat thread, mode offline dan port default 7860. Akses `http://127.0.0.1:7860`; `TEMPO_BIND=127.0.0.1:7860` membatasi listen ke localhost. Gunakan process manager lingkungan deployment untuk layanan persisten. Source ini tidak menyatakan layanan pada server tertentu sudah aktif.

## Verifikasi

Tes serving memeriksa checksum checkpoint, replay label dan Micro-F1 seluruh 740 sampel, kesesuaian encoder live dengan cache, API dataset/unggahan, model XAI yang sama, LIME/occlusion dan penolakan input rich yang tidak lengkap. Bukti aktual tersedia pada `qa/WEB_TAIL_SERVING_VERIFICATION.json` di root repository. Jalur inferensi benar-benar menghitung model; CSV OOF hanya digunakan sebagai referensi pengujian.

Model ZIP tidak menyertakan credential, identitas penilai atau seluruh cache training. Atribusi/lisensi backbone tetap mengikuti repositori pihak ketiga. Paket R4 dan hasil penelitian historis dipertahankan sebagai snapshot terpisah.
