# E46 regularisasi label smoothing dan weight decay CPU

**Tanggal:** 2026-10-13
**Status:** done

## Tujuan
Menguji regularisasi tambahan untuk overfitting yang terukur, memajukan target semua tiga Macro-F1 >=0,70 tanpa biaya GPU.

## Ruang Lingkup
- Source `DEMO_XAI_745_FULL/01_notebook/e46_label_smoothing/`, output E46, recovery, status dan CHANGELOG.
- Tidak mengubah740sampul/label, cache, E44 yang masih aktif, E45, atau delivery.

## Langkah
1. Reuse frozen pinned CLIP-L14 full/crop dan IndoBERT mean; satu shared MLP256/ReLU/drop0,4 dan3head. Kontrol baseline CLIPB32/IndoBERTCLS identik.
2. Grid tujuh config: baseline asli; CLIPL14both/mean visualweight2, lossweights1:2:2, label_smoothing[0;0,1;0,2] x weight_decay[0,0001;0,01],120epoch/lr0,001/seed42.
3. Weighted CrossEntropyLoss label_smoothing resmi torch, classweights training-only; label tersimpan tidak berubah. Lima outerfold baseline identik,2innerfold Task2seed123; pilih max minimum across-task meaninnerF1, ties pertama.
4. Preflight smoothing0 parity baseline, heldout label invariance, deterministic fit/joint gradients. CPU training1threadserver, audit selectedinner+outerrefit/all740/rootmanualF1/hash.
5. Dokumentasikan seluruh hasil; tidak promosi otomatis.

## Risiko & Asumsi
Label smoothing dengan classweights memberi massa target yang dibaurkan dan belum tentu cocok untuk kelas langka. RepeatedCV bukan externalholdout. Tidak menjamin target0,70. E44 dilaporkan user log masih bertambah; tidak disentuh.

## Verifikasi
Baseline exact parity, valid splits/training-only, configselectiontrace, selectedfit/checkpoints reproducible, manualMacroF1 ketigatask untuk740OOF. Semua3>=0,70 dan delivery/XAI gates tetap kriteria tujuan.

## Progres aktual
Source/model/run/serververifier/rootverifier/preflight tersedia dan syntax lulus. Serverpreflight lulus baseline smoothing0exact, heldoutlabelinvariance, determinism dan shared/3headgradient. NestedCPU dijalankan session61108; belum hasil final. E44 tetap dipantau session18517; user mengonfirmasi log training bertambah.

## Hasil final teraudit
Training178,57198detikCPU. Auditserverselectedinner/outerrefit/baseline/all740OOF serta rootstdlib/hash lulus. MacroF1 Task1=0,4574594089576398; Task2=0,41784551726374614; Task3=0,35335800489881736. Selectedconfig[3,3,3,3,1]: smoothing0,1/wd0,0001 empatfold dan smoothing0/wd0,0001 satufold. Minimumtask lebih rendah dariE41/E42; tidakpromosi. Semua0,70 belumtercapai.
