# Audit cache akhir E18 otomatis

**Tanggal:** 2026-10-11
**Status:** done

## Tujuan
Menjalankan evaluasi parser v2 dan tujuhkelas dari cache740 setelah watcher strict/v1 selesai, tanpa request model tambahan.

## Ruang Lingkup
- Tambah `DEMO_XAI_745_FULL/01_notebook/e18_hosted/watch_final.py`; state/log/lock terpisah, plan dan changelog.
- Setelah audit final terminal: arsip transfer seluruh cache/hasil E18 di parent output, recovery lokal lengkap dan pemeriksaan hash/decoding/fallback/manualF1 independen. Tidak menyalin direktori kredensial .kaggle.
- Tidak mengubah worker, watcher awal, parser, evaluator, dataset, label, atau protokol. Tidak memulai E19/E20.

## Langkah
1. Bekukan hash evaluator/parser/helper dan watcher awal; tunggu PID/starttime watcher awal terminal.
2. Pastikan worker asli terminal, progress740 dan watcher awal verified; jika tidak, berhenti tanpa retry.
3. Jalankan evaluate_parsed_v2 lalu evaluate_valid satu kali, simpan phase sebelum setiap subprocess. Tolak state/output lama untuk mencegah dispatch ganda.
4. Verifikasi sourcehash/kompilasi/gate incomplete sebelum launch pemantau; hasil tetap menunggu audit salinan root.
5. Setelah final verified, buat arsip cache/hasil tanpa filelock/tmp di luar folder E18, cocokkan hash transfer lalu ekstrak ke recovery lokal. Periksa manifest seluruh740 respons, ID/truth/fold terhadap baseline E14, re-decode dengan parser frozen dan reproduksi mayoritas outer-training serta manual7x7/F1. Diagnostik abstention dipisahkan dari final tujuhkelas; jangan mengklaim inference direproduksi.

## Risiko & Asumsi
- Timeout observasi bukan terminal; gunakan /proc PID/starttime. Exception berhenti tanpa retry.
- Parser dapat menyisakan INVALID; final tujuhkelas memakai fallback training-only yang telah dibekukan, diagnostik abstention tetap terpisah.
- Penahanan proses tercatat hidup. Tidak membaca atau mencetak key, tidak membuat panggilan inference.

## Verifikasi
Kompilasi source; gate pada cache belum lengkap menolak tanpa dispatch; hash lokal/server cocok dan PID pemantau aktif. Audit skor740 sesudah hasil tersedia.

## Hasil implementasi
- `watch_final.py` SHA256 bd0a1aedb40a3b24c1bc4d2768d2a86aac7b5abf8efcf8df85487fb11d571ec9 lokal/server cocok; compile lolos. Gate pada watch_state masihwatching menolak dengan AssertionError sebelum subprocess dan tanpa parsed_v2/valid/finalstate output.
- Pemantau PID1811123 aktif pada tmux tempo-e18-final-audit, statewatching_initial_auditor; mengamati watcher asli1202764/starttime205018702. Sepuluh sourcehash dibekukan. Tidak memulai inference atau E19/E20.
- E18 terakhir367/740 cost1.378141USD. Audit final masih menunggu cache lengkap, bukan klaim skor baru.
- Setelah recovery akses yang diaudit (plan access-expiry-audit), worker2352897 selesai740/740 cumulative2.769054USD; strictwatch2358172 phaseauditing_strict, finalwatch2360326 dan E20dispatcher2361801 menunggu. Belum ada klaim kualitas.
- Audit server strict/v1/v2/final tujuhkelas selesai. Arsip355079byte SHAaec40e587ebb418f6f4aefb6950cacd6129644f1e9e59b4d8f5565f8765080aa disalin/ekstrak dengan pemeriksaan path; tidak mencakup .kaggle. Root memeriksa743 hash manifest strict dan6 final, re-decode740 respons, cocokkan baseline E14 IDs/truth/fold, hitung ulang mayoritas592training per fold dan7x7/F1 manual. Bukti `docs/server-recovery/2026-10-11/e18_hosted/full_cache/root_verification.json`.
- Final tujuhkelas: strict0,25213090184940357 (453rawINVALID), v1=0,3646079161269622 (194), v2=0,37948014866221313 (78). Cost tepat2.7690535USD cocok record/progress/officialquota. Ini protokol zero-shot plus train-majority fallback, bukan murni zero-shot untuk row fallback; abstentiondiagnostic tetap terpisah. Inference hosted tidak diulang; selection bias eksperimen berulang tetap ada.
- E18 tidak mencapai0,70 atau mengungguli E14fixed0,5662691391. E20dispatcher masuktraining, worker CPU2438455 aktif; target thread belum tercapai.
