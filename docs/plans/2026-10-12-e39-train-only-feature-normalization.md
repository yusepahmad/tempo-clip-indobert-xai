# E39 — Normalisasi fitur training-only untuk CLIP-L14–IndoBERT MTL

**Tanggal:** 2026-10-12
**Status:** done

## Tujuan
Menguji apakah centering/standardisasi permodalitas membantu head MTL memanfaatkan variasi antar sampul. E36 terbaik Task2 0,4315215326, namun Task1 turun. Target tetap0,70, tanpa menambah740sampul.

## Ruang Lingkup
- `DEMO_XAI_745_FULL/01_notebook/e39_feature_norm/`, output/recoveryE39, status/changelog.
- Reuse fiturE36full/crop dan IndoBERTCLS asli; hanya CPU .31. Tidak ada GPU/download/API baru.
- Tidak mengubah dataset/label/fold, hasil E36/E38 atau aplikasi delivery.

## Langkah
1. Tetapkan10konfigurasi sebelumouter: baselineB32CLS; L14bothCLS tanpa centering(drop0,2;visual2;Task2weight2); center+unitnorm atau zscore+unitnorm ×visualweight[1,2]×Task2weight[1,2]. Shared256/drop0,2/120epoch, joint3head; baseline memakai parameterasli.
2. Mean/std masing-masing L14full/crop/IndoBERTCLS dihitung hanya dari subset fit setiap inner dan outer, disimpan sebagai buffer checkpoint. Stdclamp1e-4; L2normalize tiapmodalitas sesudahtransform. Tidak menggunakan statistik outertest/innervalid.
3. Uji statistiktraining-only/heldoutinvariance, determinisme, finitezero-variance, jointgradients. Gate featureauditE36.
4. Nested5outerbaseline×2innerTask2seed123, pilihkonfigurasi melaluiinner saja; simpan740OOF3task, checkpoint/split/trace.
5. Audit selectedinner/outerrefit, baselineparity, bufferstats, rootmanualF1; laporkan ketigatask dan tradeoff, tanpa promosi otomatis.

## Risiko & Asumsi
Normalisasi bisa membesarkan noise, belum tentu menaikkan skor. Repeatedselectionkorpus sama membatasi klaim; target0,70 hanya berdasarkan hasil sah. Semua fitur label/rationale eksternal tetap dikecualikan.

## Verifikasi
Model/source/datahash, disjointnested, foldbaselineexact, buffer mean/std hanya train, selectedrefit/740OOFparity, manualMacroF1. Dataset740 asli dan kuotagratis tetap.

## Progres
- Checks10configs/baselineparity/train-onlybuffers/heldoutinvariance/determinisme/zero-variance/jointgradients lulus. PipelineCPU tmux `tempo-e39-nested` mulai: fit lalu selectedrefitaudit hanya jika fit sukses.

## Hasil akhir
- Fit nested10config selesai dan audit server/root lulus (verification.json & root_verification.json `passed`, 740OOF 3task, baseline parity, selected refit parity).
- **Task2 `0,4347570621`** (best baru, naik dari E36 0,4315215326; baseline 0,3197261393), **Task1 `0,4303600018`** (baseline 0,4380318985), **Task3 `0,3366194258`** (baseline 0,2763519250).
- Paired bootstrap (2000 replikasi, seed42) delta Task2 vs baseline 95% CI `[0,07664; 0,15239]` (eksploratif; overlap fold & repeated selection tidak diperhitungkan).
- `selected_configs = [1,1,1,5,1]`; `target_reached: false` (0,70). Tidak dipromosikan ke aplikasi delivery; hasil/checkpoint terpisah di `04_hasil_eksperimen/e39_feature_norm/`.

## Hasil akhir
- Task1MacroF1 0,4303600018; Task2 **0,4347570621**; Task3 0,3366194258.285,63detikCPU. Selectedconfigs1/1/1/5/1: kontroltanpacentering menang4/5fold, centering1fold. Tidak menunjukkan manfaat normalisasi yang konsisten.
- Baselineparityexact; auditserverselectedinner/refit/buffertrainstats/740OOF lulus, rootmanualF1/hashlulus. DeltaTask2vsbaseline+0,1150309228; intervalbootstrapeksploratif[0,07664;0,15239]. DeltaE36hanya+0,0032355295, belum bukti keuntunganpraktis. Task1turun0,0076719dari baseline, Task3naik. Target0,70belum; tidakdipromosikan.
