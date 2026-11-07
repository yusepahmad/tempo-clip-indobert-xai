# Pemantau dan penjadwal lima fold E12

**Tanggal:** 2026-10-10
**Status:** in-progress

Pembaruan2026-10-11: fold1/2 selesai dan diunduh, fold3/4 aktif. Monitor sekarang mendukung `--hold-new-submissions` dan berjalan dengan hold=true agar E15 mendapat kesempatan slot sebelum fold5; koordinasi, audit parsial dan kewajiban membuka hold dicatat di [plan slot E15](2026-10-11-e15-slot-dispatch.md). Training Kaggle aktif tidak dihentikan.

## Tujuan
Melanjutkan lima fold QLoRA secara otomatis selama training beberapa jam, dengan pemeriksaan slot, kuota, protokol dan pengaman pengiriman ganda. Target tetap OOF740 Macro-F1 minimal0,70, tanpa perubahan dataset/label.

## Ruang Lingkup
- `DEMO_XAI_745_FULL/01_notebook/monitor_e12.py`, state/log/output `04_hasil_eksperimen/e12_monitor/`, launcher E12 hanya dibaca, hasil fold hanya JSON/JSONL/CSV/log diunduh; plan/changelog dan salinan learn.
- Adopsi job aktif fold1v2 dan fold2v1; hanya penjadwalan fold3–5 yang belum dikirim, maksimal dua job aktif. Tidak membatalkan/restart job, tidak mengubah worker/protokol, tidak menyentuh layanan produksi.

## Langkah
1. Lock fcntl satu instance, state JSON atomik dan log. Verifikasi hash worker serta source launcher flag/fold/timeout27600s sebelum push.
2. Poll status menggunakan CLI dengan batas observasi; transient error hanya retry job yang sama. COMPLETE diunduh artefaknya tanpa bobot. ERROR/cancellation status menghentikan penjadwalan untuk audit root, bukan otomatis restart.
3. Maksimal dua status RUNNING/QUEUED. Snapshot kuota memakai `.total_seconds()`. Admission konservatif: available sesudah reservasi dikurangi8jam per job aktif harus cukup8jam untuk job baru. Jika belum cukup, tunggu dan periksa ulang.
4. State `submitting` disimpan sebelum push; jika hasil push tidak pasti, tahan penjadwalan untuk audit root. Tidak mengulang push yang mungkin telah diterima. Simpan log push dan source yang dikirim; tandai submitted hanya setelah CLI sukses.
5. Sesudah kelima COMPLETE dan output diunduh, jalankan aggregator ketat sekali menggunakan venv CPU. Jangan klaim skor sebelum audit root atas hasil740 dan hash salinan.

## Risiko & Asumsi
- API kuota/reservasi dapat berubah; perhitungan konservatif dapat menunda penjadwalan. Kuota tidak cukup bukan alasan memotong data/epoch.
- Pengiriman gagal/tidak pasti perlu audit manual agar tidak ada job duplikat. Root tidak mengirim fold3–5 manual selama watcher hidup.
- Pemantau memakai CLI3.12 untuk Kaggle dan venv3.10 untuk aggregator, hanya bobot Kaggle.

## Verifikasi
Kompilasi; mode check hanya membaca dua status aktif dan quota, memvalidasi semua launcher. Lock/state/handle proses watcher diperiksa setelah start; selanjutnya rekonsiliasi log/status Kaggle dan output. Aggregator wajib semua740 sebelum skor diterima.

## Implementasi dan verifikasi awal
- `monitor_e12.py` dibuat dan dikompilasi. Mode `--check` memverifikasi lima launcher/worker, status fold1/2 RUNNING serta kuota total108000s, used18115,67939s, reserved42751,438804s, available47132,881806s. Reservasi aktif diperlakukan konservatif, bukan diabaikan.
- Pemantau aktif di server`.31`, tmux `tempo-e12-monitor`, PID2465585. Lock satu instance terbukti tidak dapat diperoleh proses pemeriksa; state watching mencatat kedua status RUNNING, fold3–5 pending.
- Root tidak melakukan push fold3–5 manual selama watcher hidup. Pemantau tidak mengubah model/label atau worker, tidak mengulang job gagal, dan belum mengirim fold baru karena dua slot aktif.
- Verifikasi penjadwalan/download/aggregator dengan hasil nyata menunggu transisi job. Plan tetap in-progress sampai bukti tersebut tersedia.
