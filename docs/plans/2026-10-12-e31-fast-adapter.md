# E31 diagnosis kesalahan dan adapter ringan pada fitur beku

**Tanggal:** 2026-10-12
**Status:** done

## Tujuan
Menguji satu perubahan keluarga model dengan biaya rendah menuju target Task2 Macro-F1 0,70. Baseline terbaik E14 0,5662691391334344. Diagnosis merupakan eksplorasi, bukan bukti generalisasi.

## Ruang Lingkup
- Tambah `DEMO_XAI_745_FULL/01_notebook/e31_adapter{,_checks,_verify,_root_verify}.py` dan script diagnosis bila diperlukan.
- Bukti baru di `docs/server-recovery/2026-10-12/e31_adapter/`, output server `04_hasil_eksperimen/e31_adapter/` dan preparation terpisah.
- Plan ini, CHANGELOG.md dan salinan server project.
- Tidak mengubah dataset/label asli, baseline/hasil lama, sumber fitur E14/E22, aplikasi demo, model encoder, prompt atau credentials. Tanpa request AI/GPU/download/dependency tambahan.

## Langkah
1. Audit error OOF E14 per kelas/pasangan; pilih deterministik sampai42 kasus (maks6 perkelas) untuk diagnosis. Simpan konteks input asli dan prediksi, tanpa menyimpulkan penyebab visual sebelum melihat gambar.
2. Bekukan kandidat: pipeline per-block training-only StandardScaler/L2/PCA64 dari helper E29 immutable; classifier residual bottleneck32 + linear7, CPU float32, seed42, fullbatch AdamW lr0,01 selama200epoch. Normalisasi input classifier dipelajari training-only. Alpha0 merupakan kontrol linear; alpha0,2 adapter. Grid16 = mode semantic/caption_fusion x alpha0/0,2 x weightdecay0,01/0,1 x classweightNone/balanced. Ini adapter multimodal terinspirasi CLIP-Adapter, bukan implementasi paper persis.
3. Uji deterministic refit/weights/finiteprob, heldout isolation, kontrol alpha0, serial-parallel2kandidat, gate prior/source/input dan actual592/148 smoke tanpa skor outer. Ukur durasi untuk estimasi260fit, hentikan full jika estimasi konservatif melebihi2jam.
4. Setelah root memverifikasi preparation/source/input: launch sekali nestedinner3/outer5 split baseline42 di server .31, grid selection firstargmax inner saja. Log/progress/PID/starttime tercatat; tidak restart status tidak pasti.
5. Auditor server mereproduksi selectedinner/refit/modelstate/normalizer/PCA/prediksi; salin fulloutput dan audit root stdlib atas8hash/current source/grid16/original740fold/manual7classF1 sebelum menyebut hasil final.
6. Catat hasil nyata dan limit; hanya promote bila meningkatkan hasil terverifikasi. Jangan menjalankan grid tambahan dalam plan ini. Perubahan input visual merupakan kandidat terpisah setelah diagnosis, bukan otomatis.

## Risiko & Asumsi
- 740 sampul kecil; adapter bisa overfit. Kontrol linear/regularisasi dan nestedCV membantu tetapi tidak menjamin0,70.
- PCA64 bisa membuang informasi; satu setting tetap untuk membatasi waktu. Tidak diam-diam menambah pilihan setelah melihat outer score.
- Diagnosis seluruh OOF dan repeated experiment selection menimbulkan bias eksplorasi; tidak ada externalholdout. Label tidak dikoreksi sepihak.
- Fitur beku E14/E22 yang sudah diaudit digunakan ulang; auditor root tidak mengulang encoder atau fullgrid. ExactCPU reproducibility diwajibkan pada environment server saat ini.
- Diagnosis awal hanya pola kuantitatif dan konteks teks; jika visual belum diperiksa, tulis belum diperiksa.

## Verifikasi
Sourcehash root/server dan prior/cache pins cocok; synthetic dan actualsmoke lulus; runtimegate260fit*1,5 <=2jam; semua740ID/truth/fold identik E14, training-only transform dan innerselection, rawselectedfits reproduced, manualMacroF1 dan manifest root cocok. Changelog ditulis sesudah perubahan nyata.

## Hasil aktual
- Diagnosis E14:303/740 salah,42kasus dipilih deterministik6perkelas; 7contactsheet originalimageSHA checked dan ditinjau. Output `diagnosis.json`, `diagnostic_cases.json`, `visual_diagnosis.json`, `visual_sheets/`. Dugaan konflik objek literal/topik/relasi, bukan sertifikasi label salah. Render pertama gagal karena pathCSV images/ bukan lokasi berkas; diperbaiki ke05_gambar/basename lalu semua42hash cocok, tidak mengubah dataset.
- Source frozen worker de56f05b26be0de4b75ac3ea8161eb8874f4da7f562f03eb17ad6d068b4d63da, verifier45dac9e0c388b695ce2c8552ab7e523a0936cc0ed65175299677abfc0f036399, checks e7faa79ff083f321c1f380387562498581fbde87084f4fc8b49eda4c8678104f. Rootauditor cabb3801457988c2eacf94805b0b50d0f4faf0154eed9934d1cf13b4d7537f7d (pathpreparation disesuaikan sebelumfullaudit). Root/server cocok.
- Preparation seluruh deterministic/heldout/classweights/control/serial-joblib4/missingprior tests lolos; actual592fit0,7662851107s, konservatif260fit*1,5=4,98menit. PreparationSHA012c3d20ee87e0857e422e7b6fd7d5af14e3830305dbdce9b87c2705b84cd68b, unchangedE29features/source/priorE30/grid16 diperiksaroot.
- Launch sekali tmuxtempo-e31-adapter setelah gate, auditorchained; saat observasi workerfull sudah selesai5fold, auditorPID3160446/starttime216111620 stateR/exactcmdline. PID workerfull tidak sempat diambil, tidak diasumsikan. Runtimefold13,58/8,72/8,30/8,76/9,03detik. Audit semua selectedinner/refit/PCA/normalizer/adapter/classweight/state/probability/predictions exact.
- SerververificationSHAbfca993047894981b7cb5ea8292325a0dd3e1c7bb9d06a69f158c222dd6a670a. Fullcopyroot dan independent8hash/grid16/original740baselinefold/manualF1 lolos, bukti `root_oof_verification.json`. FinalMacro-F1 **0,4748302904710198**, di bawahbestE14 **0,5662691391334344**; target0,70belum. Tidakpromote dan tidak menambahgrid.
- Statusdone hanya scopeE31. Tidak ada API/GPU/download tambahan. Limit repeatedselection/noexternalholdout dan upstreamsampledencoder tetap.
