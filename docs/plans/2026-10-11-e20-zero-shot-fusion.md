# E20 fusi fitur frozen dan kategori zero-shot hosted

**Tanggal:** 2026-10-11
**Status:** done

## Tujuan
Menguji apakah prediksi zero-shot E18 menambah informasi pada fitur E5/BGE/CLIP untuk Task2 menuju Macro-F1 minimal0,70. Persiapan tidak memakai kuota AI/GPU dan menunggu E18 lengkap sebelum training.

## Ruang Lingkup
- `DEMO_XAI_745_FULL/01_notebook/e20_zero_shot_fusion.py` dan auditor, output `04_hasil_eksperimen/e20_zero_shot_fusion/`, recovery, plan/changelog.
- Dispatcher `01_notebook/watch_e20.py`, state/log/lock terpisah dalam `04_hasil_eksperimen/e20_dispatch/` untuk menunggu pemantau audit akhir E18 terminal dan verified.
- Tidak menggunakan prediksi E14/E19 atau model yang belajar label heldout sebagai fitur. E18 zero-shot tanpa contoh/traininglabel, parser frozen sebelum label kualitas, dapat menjadi fitur input-only. Label/data/worker aktif tetap.

## Langkah
1. Gate E18 strict740 verified dan parsed740 verified; cocokkan cached response/input/source/hash serta originalID/fold. Ambil kategori parsed sebagai one-hot8 (7kelas+INVALID), tanpa target truth dalam konstruksi fitur.
2. Gabungkan E5description/source_reason1536 + BGEcombined1024 + CLIPimg512 + one-hot8. Hash frozen sources sama eksperimen sebelumnya. One-hot invariant terhadap targetlabel permutation.
3. Pipeline: fit StandardScaler hanya inner/outertraining perblok numerik, L2 perblok, weights BGE1/CLIP1, E5[0,5;2], VLM[0;0,5;1;2;4]. One-hot tetap unit tanpa scaler. SVCrbf C[1;10;100], gamma[scale;0,1;1], classweightNone/balanced.180grid/fold; weight0 memberi kontrol tanpa VLM.
4. Inner3 Task2 stratseed42 memilih grid; outer5 Task1 baseline seed42 (592/148) mengevaluasi740. Tidak ada routing dari skor outertest atau tuning threshold setelah melihat label heldout. Satu CPU dan checkpoint immutable source/input protocol.
5. Auditor rerun inner3 terpilih/refit5/prediksi740, periksa gridscore/argmax/reports/manualF1 dan originals. Jangan klaim seluruh grid direproduksi; catat batas audit dan selection bias repeated experiments.
6. Kompilasi/hash dan uji transformer clone/train-scaler/invariance pada data sintetis. Full menunggu E18 terminal/audit dan CPU E15 selesai; belum dijalankan dalam persiapan ini. Catat perubahan aktual.
7. Dispatcher membekukan sourcehash E20/parser/helper, menunggu PID/starttime finalwatch E18 terminal, memeriksa audit E15 dan cache final E18 lengkap. Jika salah satu hasil valid E18 mencapai0,70, lewati training untuk audit root; selain itu jalankan E20 dan auditor sekali. State/output lama atau exception memerlukan audit root tanpa retry. Tidak ada request model, tidak menjalankan E19.

## Risiko & Asumsi
- Kategori VLM bisa salah; weight0 adalah kontrol yang dipilih inner tanpa melihat outertest.
- Kualitas hosted/evaluasi berulang tidak menjamin generalisasi; repeated selection bias tetap dilaporkan.
- Label E19 few-shot cross-fold tidak sah sebagai fitur frozen global, sehingga tidak dipakai. Tidak mengubah label target untuk mengejar skor.

## Verifikasi
Sumber pinned,740IDs/alignment/fold, unit one-hot tiaprow dibangun hanya dari respons, scalerfittrain-only,180grid/inner3/outer5, checkpoint source/invariant. Setelah full: refit/inneraudit, OOF740/manualF1/hashcopy. Target belum terbukti sebelum bukti lengkap.

## Hasil persiapan
- Worker SHA256 `f5c48d57cc375e200fa61d0c634b0812c2dc8de93069b704f239abfd5863d270`; auditor `dd2384f34df51339645e5e0889210562bfa1bc141c6f3133dea7b97ec28f1866`. Kompilasi/source hash server cocok.
- Uji sintetis70 sampel (56train/14test) membuktikan clone/predict14, scaler mean hanya training dan tidak berubah saat transformtest, one-hot berbobot tepat, kontrolvlm_weight0 nol,180grid. Gate full menolak E18 tanpa verification sebelum membuat output/training.
- Full E20 belum berjalan dan tidak ada skor. Menunggu E18 audit lengkap dan CPU E15 selesai. Artefak hasil/audit tidak diklaim dari uji sintetis.

## Pembekuan decodingv2 sebelum training/inference
Sebelum E19/E20 dijalankan, gunakan parser `e18_hosted/parse_v2.py` yang telah lolos22kasus format tanpa targetlabels. E18 strict/v1 tetap dipertahankan. E19 harus menunggu hasil strict/v1/v2 lengkap terverifikasi dan semuanya di bawah0,70 sebelum inference; source/parser/evaluator/OoFhash dipin. E20 memakai kategori zero-shot parsed_v2 saja; tidak memilih parser dari skor heldout. Source E19/E20 diganti sebelum menghasilkan runconfig/checkpoint, lalu gate/kompilasi/hash diverifikasi lagi. Proses E18/watch tetap.

## Verifikasi source setelah decodingv2
- `e20_zero_shot_fusion.py` SHA256 `a4a5c1499155a2e65c01ea2b660656033a257af0a38002a1728b71444dc63dc9`.
- `e20_zero_shot_fusion_verify.py` SHA256 `3d2d904c03e5872e6c71d475cceb0cc16705deea761be855d270d50a87ed95b4`.
Kompilasi/hash server cocok; gate E19/E20 tetap menolak E18 belumverified tanpa inference/training/output. Belum ada runconfig/checkpoint/skor baru.

## Pemisahan fitur label-blind dan fallback terlatih
E20 tetap membangun one-hot8 dari respons mentah yang di-decode parsed_v2 (termasuk INVALID), tidak dari `valid/*/oof.csv`. Fallback mayoritas belajar label outer-training dan tidak boleh dipakai sebagai fitur frozen global antarfold. SVC E20 sendiri selalu menghasilkan tujuh kelas valid. Evaluasi final E18/E19 memakai kontrak tujuhkelas sesuai plan `2026-10-11-valid-seven-class-decoding.md`; skor abstention bukan bukti target.

## Dispatcher setelah E15 verified
- E15 telah lolos audit25model/OOF740; tidak ada evaluator CPU E15 yang perlu ditunggu lagi.
- `watch_e20.py` SHA2565f9533c7da0e3176cc514e9d89031c06a4570e29f323038bfb2874a09772c5f1 lokal/server cocok dan compile lolos. Gate cache E18 belumlengkap menolak sebelum training/dispatchoutput; direktori hasil E20 belum dibuat.
- PID1838656 aktif pada tmux tempo-e20-dispatch, phasewaiting_final_e18_audit, memantau finalwatch1811123/starttime205383362 dengan sourcehash dibekukan. State/lock/log terpisah, tidak memulai E19/API dan tidak otomatisretry. Training belum dimulai, belum ada skor E20.
- Sesudah recovery E18 dan semua audit finalverified, dispatcher baru2361801 phase training; CPUworker2438455 aktif. E18finalsemuaroute<0,70. Fitur rawv2 tetap input-only, source/grid tidak berubah. Belum ada skor E20; auditor akan dijalankan setelah worker exit0.

## Hasil final terverifikasi
- Worker/auditor/dispatcher terminal; serveraudit selectedinner3/refit5 dan740prediksi lolos, finalMacroF1=0,5617121910174215.
- Root memeriksa8 hash hasil+source pins, original740 ID/truth/fold/tujuhkelas, semua5train/test/prediksi,180gridorder/argmax dan choseninner vs serveraudit, provenance rawparsed_v2 (bukan fallback terlatih) dan manual7x7/F1=0,5617121910174216. Bukti `docs/server-recovery/2026-10-11/e20_zero_shot_fusion/root_verification.json`.
- Empat fold memilih VLMweight0, fold5 memilih0,5. Tidak mengungguli E14fixed0,5662691391 atau target0,70. Batas: seluruhgrid/inference tidak diulang dan selectionbias eksperimen berulang tetap ada. E21 menjadi kelanjutan CPU.
