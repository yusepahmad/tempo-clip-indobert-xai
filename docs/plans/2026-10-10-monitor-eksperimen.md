# Pemantau eksperimen Kaggle

**Tanggal:** 2026-10-10
**Status:** done

## Tujuan
Mengambil output terminal E05/E06 dan menjalankan evaluasi E06 otomatis tanpa job duplikat selama goal berjalan.

## Ruang Lingkup
- `DEMO_XAI_745_FULL/01_notebook/monitor_task2.py`, salinan learn, `04_hasil_eksperimen/task2_monitor/`, output E05/E06 dan plan/changelog.
- Pemantau tidak menghentikan/restart kernel aktif dan tidak mengubah dataset/label atau model produksi.

## Langkah
1. Poll status CLI tiap60 detik dengan timeout dan tulis observasi aktual.
2. Download output E05/E06 hanya saat terminal; simpan log/JSON/CSV/NPZ, hindari checkpoint besar.
3. E06 hanya dievaluasi jika embeddings/meta valid; satu evaluator dengan lock eksklusif dan child process yang di-wait.
4. Setelah keduanya terminal dan evaluasi selesai, hentikan pemantau; inspeksi bukti untuk menentukan E07 berikutnya.

## Risiko & Asumsi
- API dapat sementara gagal; error observasi tidak berarti kernel terminal dan tidak menjadi alasan restart.
- Proses evaluasi CPU dapat lama; tetap gunakan2 job/BLAS1 sesuai evaluator.
- Pemantau bukan bukti keberhasilan model; metrics diperiksa terpisah sebelum klaim target.

## Verifikasi
Lock fcntl mencegah dua pemantau; terminal hanya berasal API; child evaluator dicek exit code; file status/history memiliki hasil aktual. PID/tmux diverifikasi hidup setelah launch.

## Hasil penerapan
- Kompilasi lokal/server lulus. Pemantau aktif di server `.31`, tmux `tempo-task2-monitor`, PID `1106327`.
- Observasi pertama 2026-10-10 09:02:46 UTC: E05/E06 RUNNING; evaluator belum dimulai. Bukti server `04_hasil_eksperimen/task2_monitor/status.json` dan `history.jsonl`.
- Plan tetap in-progress sampai output dan evaluasi selesai.
- E05/E06 COMPLETE, download berhasil. Evaluasi E06 selesai exit0; status final09:32:54 UTC dan log `finished_existing_runs`. Pemantau menyelesaikan tugas tanpa restart kernel atau evaluator duplikat.
