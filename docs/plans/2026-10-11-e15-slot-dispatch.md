# Slot E15 sebelum QLoRA fold5

**Tanggal:** 2026-10-11
**Status:** done

## Tujuan
Memperoleh fitur multimodal E15 dalam job maksimal1jam pada slot pertama yang bebas, tanpa menunggu seluruh QLoRA selesai. Target tetap OOF Macro-F1 minimal0,70; hasil terbaik saat ini E14 keluarga fusi0,5662691391.

## Ruang Lingkup
- `01_notebook/monitor_e12.py`: opsi hold-new-submissions dan restart hanya proses pemantau, bukan job training Kaggle.
- `01_notebook/monitor_e15.py`: dispatcher satu kali, artefak status/log E15, verifier/evaluator E15 yang sudah disiapkan; plan E12monitor/E15, changelog, recovery hasil parsial E12.
- Auditor OOF `01_notebook/kaggle_e15/verify.py`: lima keluarga dan routing nested, reproduksi inner/refit parameter terpilih dan skor manual.
- E12 fold3/4 tetap berjalan, fold1/2 tetap hasil asli; fold5 ditahan sementara. Dataset/label/produksi dan worker/launcher training tidak diubah.

## Langkah
1. Audit dua fold E12 yang selesai dengan pemeriksaan aggregator yang sama, tanpa menulis aggregate parsial atau mengklaim skor740. Salin hanya JSON/JSONL/CSV, bukan bobot adapter.
2. Tambahkan flag hold-new-submissions; validasi state watching tanpa submission sedang berlangsung, hentikan hanya monitorPID2465585, tunggu proses berakhir/lock bebas, restart monitor dengan flag tersebut. Tetap download/audit status fold3/4, jangan push fold5 selama hold.
3. Dispatcher E15 memeriksa lock dan state hold E12, status aktual job3/4, serta kuota SDK.total_seconds. Push E15 private maksimal3600s hanya bila jumlah job aktif kurang2 dan available-minus8jam per job aktif cukup3600s. Persist submitting sebelum push, hasil tak pasti berhenti untuk audit root tanpa retry.
4. Poll E15 aktual; COMPLETE download hanya JSON/JSONL/NPZ, jalankan verify_features dan evaluator CPU satu core. ERROR/cancel berhenti untuk audit root, tidak auto-restart.
5. Setelah E15 terminal diaudit, buka hold dan lanjutkan E12 fold5 sesuai kuota. Hasil OOF E15 harus diverifikasi sebelum klaim. Catat bukti/hash/perubahan aktual ke changelog.
6. Siapkan auditor OOF sebelum hasil tersedia: rekonstruksi classifier dari parameter tercatat dengan whitelist grid (tanpa eval string), ulang inner-CV parameter terpilih/refit outer-training untuk25 model akhir, cocokkan seluruh prediksi dan routing nested. Tidak mengulang pencarian grid penuh, tidak mengubah evaluator/worker yang telah disiapkan.

## Risiko & Asumsi
- Status API bisa terlambat; timeout observasi bukan terminal dan bukan alasan restart. Maksimaldua job aktif tetap dijaga.
- E15 technical smoke bisa gagal; jangan membuang sampel atau memperpanjang batas tanpa audit penyebabnya.
- Pergantian monitor hanya aman pada state watching/submitted/downloaded/pending yang telah diperiksa; keadaan submitting mengharuskan berhenti dan audit root.

## Verifikasi
Kompilasi, hash source/launcher, lock/PID/starttime/state aktual, dua fold E12 lolos split/epoch/probability/manualscore. Dispatcher mengecek status dan kuota sebelum write; semua740 fitur dan OOF E15 diaudit sebelum laporan hasil.

## Pemeriksaan keluarga selesai selama evaluasi berjalan
- Salin hanya empat keluarga yang sudah COMPLETE ke recovery `e15_vlm_features/completed_families`; cocokkan hash salinan, ID/label/fold terhadap baseline E14 dan hitung F1 manual.
- Pemeriksaan ini tidak menggantikan auditor inner/refit/routing akhir. Keluarga kelima dan nested masih menunggu; tidak memulai training atau API baru.
- Pemeriksaan selesai:8 hash salinan cocok server, empat keluarga masing-masing740 ID unik/truth/fold cocok baseline E14 dan prediksi tujuhkelas; F1 manual last_token0,5197824485, tail_text_mean0,4592830809, last_tail0,5021824359, vlm_bge0,5373709776 cocok JSON. Bukti `completed_families/copy_score_verification.json`; belum audit inner/refit/routing.

## Implementasi dan bukti aktual
- Dua fold E12 selesai dan lolos pemeriksaan aggregator per fold tanpa concatenation/aggregate parsial: fold1 epoch3/F1=0,5265211669819665, fold2 epoch2/F1=0,5533934467820908,148 sampel masing-masing. Bukti `docs/server-recovery/2026-10-11/e12_qlora/partial_audit/verification.json`;10 hash salinan cocok, stdlib lokal mengonfirmasi ID/fold/label/confusion matrix/F1. Bobot adapter tidak disalin.
- Flag hold-new-submissions dibuat dan dikompilasi. Monitor lama2465585 dihentikan setelah state watching/fold5pending/no-submitting diperiksa; terminal dan lock bebas dikonfirmasi sebelum restart. Monitor baru PID1706216, tmux `tempo-e12-monitor-hold`, state hold=true; job Kaggle tidak dihentikan.
- Dispatcher E15 dibuat/dikompilasi; preflight launcher embedded source/timeouts/private/hash, monitor hold live+locked, status aktual3/4 RUNNING dan kuota SDK lolos. Snapshot used58993,42s/reserved34275,69s/available14730,89s (sesudah reservasi, bukan jaminan kuota saat push).
- Dispatcher aktif PID1723727, tmux `tempo-e15-monitor`, state pending dengan dua job E12 RUNNING. Belum push E15 dan belum ada hasil GPU baru; menunggu slot serta admission kuota konservatif. Fold5 tetap pending.
- Setelah E15 terminal, root harus audit lalu membuka hold dan melanjutkan fold5; evaluator/OOF E15 masih pekerjaan tersisa. Goal belum tercapai, kandidat terbaik tetap E14 OOF0,5663.
- Auditor OOF E15 `kaggle_e15/verify.py` dibuat/dikompilasi; SHA256 lokal/server `a3f8da3b3f20a381be49c4e049014478eca479cada4285fc0e5520445530841d` cocok. Parser whitelist/clone diuji terhadap25 parameter model E13 nyata (grid identik), dua constructor alternatif dan penolakan classifier asing. Belum menjalankan audit hasil E15 karena fitur/OOF belum tersedia.
- Pemeriksaan ulang API mengonfirmasi E12 fold3/4 masih RUNNING; snapshot kuota used73385,99s/reserved27079,41s/available7534,60s (2,093jam sesudah reservasi). Pemantau E12/E15 masih hidup dan E15 pending; snapshot bukan keputusan admission masa depan atau skor baru.

## E15 selesai dan evaluasi dimulai
- API aktual mengonfirmasi E12 fold3/4 COMPLETE dan hasil diunduh pemantau. Metrik yang belum diaudit root penuh: fold3 epoch6/F1=0,5665131261, fold4 epoch5/F1=0,5449290553. Ini hasil per fold, bukan OOF740; audit semua fold tetap wajib sebelum klaim agregat.
- Dispatcher mengirim E15 setelah keduanya selesai, kernel COMPLETE. Semua740 fitur4096 dimensi dari kedua pooling lolos audit feature/provenance, inferensi723,89s. Bukti disalin ke `docs/server-recovery/2026-10-11/e15_vlm_features/`; bobot model tetap di Kaggle.
- Evaluator E15 CPU/BLAS1 aktif di tmux `tempo-e15-eval`, PID586083, dilanjutkan auditor otomatis setelah exit0. Log evaluasi/audit disimpan di luar folder hasil. Belum ada skor OOF E15.
- Monitor hold1706216 dihentikan setelah E15 terminal+audit fitur dan seluruh fold1–4 downloaded dikonfirmasi; terminal/lock bebas diperiksa sebelum monitor baru590278 berjalan tanpa hold. Fold5 pending karena kuota24171,92s (~6,714jam) kurang batas28800s. Tidak memperpendek training atau mengganti protokol untuk memaksakan launch.

## Evaluator lengkap, audit akhir berjalan
- Evaluator586083 terminal; log COMPLETE vlm_visual0,5154439289 dan nested_selected.json mencatat0,5295626661. Ini metrik sementara sebelum audit akhir, tidak mencapai0,70.
- Auditor otomatis PID1713653 terkonfirmasi R+; log berhasil mereproduksi12/25 selected inner/refit (last_token5, tail_text_mean5, last_tail2). Belum ada verification.json final yang diklaim; tidak restart evaluator/auditor.

## Audit final selesai
- PID1713653 terminal dan verification.json statusverified: seluruh25 selected inner/refit cocok, semua fitur/sourcehash,740 ID/truth/fold dan nested routing serta confusion/F1 manual lolos. Tidak mengulang grid penuh.
- Recovery `docs/server-recovery/2026-10-11/e15_vlm_features/oof/` berisi12 hasil+server verification+root_verification.json. Semua12 hash hasil cocok manifest, hash auditor cocok source lokal, stdlib lokal mengonfirmasi enam OOF740, F1 manual dan routing. SHA serververification bdf0282a1ec5e63093d7e606ab417ab4fbf7d5d13f53d28d6604f3cca5ac2f34.
- Final nested0,5295626660525913; keluarga last_token0,519782448524796, tail_text_mean0,45928308089795494, last_tail0,5021824359153343, vlm_bge0,5373709775977532, vlm_visual0,5154439288673007. E15 tidak mengungguli E14fixed0,5662691391; target0,70 belum tercapai. Monitor E12 tetap menangani fold5 sesuai plan E12; penyelesaian E15 tidak berarti OOF QLoRA lengkap.
