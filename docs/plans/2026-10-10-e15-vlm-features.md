# E15 fitur visual-bahasa Qwen beku

**Tanggal:** 2026-10-10
**Status:** done

## Tujuan
Menguji representasi multimodal langsung dari hidden state Qwen, agar classifier dapat memakai interaksi gambar/teks yang tidak tersedia pada fusi CLIP dan embedding teks terpisah. Target tetap OOF Macro-F1 minimal0,70.

## Ruang Lingkup
- `DEMO_XAI_745_FULL/01_notebook/kaggle_e15/`, kernel private baru, bukti `04_hasil_eksperimen/e15_*`, salinan learn/recovery, plan/changelog.
- Qwen3-VL-8B-Instruct revision E01/E12, float16 beku di dua T4; input/prompt persis E12 (gambar384, deskripsi E01/sumber+alasan/judul/teks dan codebook tetap). Tidak memakai label target/anotasi deskripsi/mapping sebagai input, tidak mengubah data/label/produksi.
- Bobot hanya Kaggle. Persiapan saja selama dua job E12 aktif; **belum push**. Pemantau E12 tidak diubah atau dihentikan pada tahap ini.

## Langkah
1. Ambil hanya DEFINITIONS/build_prompt dari AST worker E12 menjadi helper tanpa impor/training. Audit prompt740 identik dengan input-audit smoke E12 dan tetap sama jika label target diacak.
2. Frozen model backbone menghasilkan last_hidden_state4096. Simpan dua pooling L2: token terakhir, dan mean128 token teks terakhir (abaikan placeholder gambar/video dan padding), tanpa language head/generasi/fit label.
3. Technical smoke12 pertama: finite/norm/dimension dan waktu. Simpan metadata teknis; lanjut740 dalam kernel yang sama hanya jika proyeksi inferensi<=2100s. Batas awalAPI3600s/pip600s/worker3000s, disesuaikan dari smoke bila perlu sebelum retry.
4. Simpan740 embeddings/ID/input hash/gambar/token audit/model revision/source/helper hash dan durasi/memori. Hash/ID/frozen state diverifikasi sebelum nested evaluation.
5. Evaluator CPU/BLAS1 nested inner3seed42/outerbaseline5, StandardScaler di dalam pipeline, grid SVC/LR/LinearSVC identik E13. Lima keluarga: last_token, tail_text_mean, concat keduanya, last_token+BGEcombined, last_token+CLIP. Pemilihan keluarga hanya inner-score. Audit740 OOF/manualF1/hash salinan sebelum klaim.
6. Push hanya setelah pemeriksaan slot/kuota dan koordinasi dengan pemantau E12. Tidak bersaing diam-diam untuk slot; jika perlu jeda penjadwalan, revisi plan eksplisit sebelum aksi tanpa menghentikan training E12 aktif.
7. Siapkan `verify_features.py` terpisah untuk memeriksa hasil lengkap sebelum evaluator: rekonstruksi740 prompt dan hash gambar asli, indeks/ID/token bounds, hash source/revision/input, serta dimensi/finite/L2 kedua pooling. Tidak mengklaim tokenisasi GPU direproduksi di CPU; token hash diperiksa formatnya saja.

## Risiko & Asumsi
- Hidden state model generatif belum tentu embedding yang baik; tidak ada jaminan kenaikan skor. Codebook tetap bukan label target.
- Dispatch duaGPU dan forward backbone langsung perlu technical smoke; masalah kompatibilitas/OOM tidak menjadi alasan membuang sampel atau mengganti label.
- Inferensi dibatasi budget; output parsial tidak menjadi hasil OOF penuh. Uji berulang memiliki bias seleksi riset.

## Verifikasi
Kompilasi, audit AST/prompt aktual740 dan target-label permutation invariance; runtime smoke GPU kemudian. Semua740ID, finite/unit norm4096, input/model/sourcehash; pipeline nested hanya fit train dan routing inner; perhitungan ulang Macro-F1 serta salinan bukti cocok.

## Referensi
- https://huggingface.co/docs/transformers/v5.17.0/en/model_doc/qwen3_vl#transformers.Qwen3VLModel
- Config resmi revision0c351dd01ed87e9c1b53cbc748cba10e6187ff3b: hidden_size4096, image_token_id151655, video_token_id151656.

## Persiapan dan audit prompt
- Worker/prepare/helper/evaluator/launcher private dibuat, seluruh lima berkas Python dikompilasi dan disalin ke learn. Evaluator memeriksa hash worker/helper/NPZ/audit, dimension4096/unitnorm serta signature source/OOF sebelum resume.
- Audit aktual740: hash prompt persis E12 smoke, tidak berubah ketika label target diacak, maksimum2148karakter. AST worker tidak mengakses kolom target/deskripsi/mapping anotator; launcher mengandung worker/helper identik dan metadata private.
- Worker SHA30a2c29b499c75879192c1dcc0b0b47570fb293d3dd12718f449984b06cda4cd, helper SHAa1731aad122005377bfc5d6801cb70f3ab18fb89129d2ba57d2ab50e5e238cbf. Bukti `docs/server-recovery/2026-10-10/e15_preflight/verification.json` dan salinan learn.
- **Belum push dan belum diuji GPU.** E12 fold1/2 masih aktif bersama pemantau; E14 menghitung di CPU. E15 disiapkan untuk slot/kuota berikutnya, tanpa mengubah penjadwalan E12 saat ini.
- Pembaruan2026-10-11: fold1/2 E12 selesai, fold3/4 aktif. Penjadwalan E15 pada slot pertama yang bebas sebelum fold5 dikoordinasikan secara eksplisit melalui [plan slot E15](2026-10-11-e15-slot-dispatch.md); hanya monitor submission ditahan sementara, training aktif tidak dihentikan.
- Auditor fitur `verify_features.py` dibuat dan dikompilasi; SHA256 lokal/server `c6454b9bfb3c0e362f8761ad1dc355b14bf9ff33cc565f4f8a70c97e8eaf65e9` cocok. Rekonstruksi prompt/gambar dan validasi matriks hasil GPU belum dijalankan karena artefak E15 belum tersedia; digest token tidak dianggap bukti reproduksi tokenisasi.
