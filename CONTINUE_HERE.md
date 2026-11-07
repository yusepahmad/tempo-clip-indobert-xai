# Lanjutkan pekerjaan di server .31

Workspace: /home/yusep/workspace/tempo-revisi-20261108
Sesi kerja persisten: tmux attach -t tempo-revisi-20261108
Environment analisis: source .venv-analysis/bin/activate

Mulai dengan docs/WORKSPACE_INDEX.md, plan migrasi, CHANGELOG.md dan qa/MIGRATION_VERIFICATION.json. Source canonical: DEMO_XAI_745_FULL/. Paket analisis terbaru: delivery/HASIL_REVISI_JOY_20261108_R4/. Bukti Run all server ada pada paket qa/SERVER_NOTEBOOK_VERIFICATION.json; bukti arsip pada qa/R4_EXTRACTED_VERIFICATION.json yang sudah berstatus verified_extracted_run_all.

R21 supporting 740 telah dikoleksi. Arm literal citra+judul masih job Kaggle privat version 2; jangan push ulang. Source manager/collector dan ledger sudah disalin. Credential Kaggle tidak disalin, driver GPU server tidak tersedia. Analisis CPU siap dan sudah menjalankan tiga notebook. Job Kaggle tidak bergantung laptop tetap online.

Pengguna akan mengerjakan penilaian manusia. Berikan atau terima berkas dari delivery/HASIL_REVISI_JOY_20261108_R4/UNTUK_MANUSIA/. Hasil nyata baru dihitung ketika dikembalikan; jangan isi skor atau riwayat yang hilang dengan AI. R22 masih membutuhkan keputusan provenance historis, R8 dokumen Agustus, R32 bukti Colab asli.

Laptop mengalami Btrfs forced-readonly. Jangan mengubah filesystem laptop atau menghapus file sumber. Scope server adalah migrasi kerja analisis, bukan backup penuh seluruh disk/model/arsip. Salinan server lama tidak ditimpa. Semua perubahan wajib plan docs/plans dan CHANGELOG sesuai AGENTS.md.
