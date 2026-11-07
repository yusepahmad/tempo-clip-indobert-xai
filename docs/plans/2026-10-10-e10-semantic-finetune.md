# E10 fine-tuning encoder semantik dua masukan

**Tanggal:** 2026-10-10
**Status:** done

## Tujuan
Menguji encoder E5 yang dilatih supervised untuk Task2, setelah fitur E5 beku E06 mencapai0,5423. Target tetap Macro-F1 OOF minimal0,70.

## Ruang Lingkup
- `DEMO_XAI_745_FULL/01_notebook/kaggle_e10/`, salinan learn, kernel private baru, bukti `04_hasil_eksperimen/e10_*`, plan/changelog.
- Reporter kuota `01_notebook/kaggle_quota_seconds.py`, snapshot kuota sebelum full dan koreksi asumsi durasi pada plan E05/E07/E10.
- Model intfloat/multilingual-e5-base revision E06; dua masukan deskripsi dan sumber+alasan dari E01. Dataset/label asli, tanpa anotasi deskripsi/mapping sebagai fitur.
- Bobot hanya di Kaggle. Tidak mengubah produksi atau menghentikan E07/E08/E09 aktif.

## Langkah
1. Buat encoder bersama untuk dua masukan prefix query, masked mean pooling, concatenation, LayerNorm/dropout/head7kelas. Semua parameter encoder dilatih.
2. AMP float16, gradient checkpointing, batch8, panjang384; weighted CE memakai hitungan kelas dari training yang sedang dipakai, encoder LR2e-5 dan head LR2e-4.
3. Split baseline5fold. Pilih epoch dari inner20% stratified Task2, max12/patience3; inisialisasi ulang lalu refit seluruh outer-training selama epoch pilihan. Outer-test hanya dinilai sekali.
4. Smoke32training/16validation/16test, max2epoch; cek finite loss/grad, bobot encoder+head berubah, checkpoint reload cocok dan ukur waktu/memori. Smoke bukan metrik kualitas.
5. Full hanya sesudah smoke lulus dan estimasi/batas waktunya sesuai snapshot kuota; simpan740 OOF, probabilities, fold/history/config/hash. Tidak mengubah hyperparameter memakai outer-test.

## Risiko & Asumsi
- Fine-tuning dapat overfit; validasi inner dan reinitialization mencegah pemilihan epoch memakai test.
- Full encoder XLM-R base memakai memori besar; smoke menentukan kelayakan. Bila OOM, revisi plan sebelum mengubah konfigurasi.
- Pemuatan/download model harus di Kaggle dan internet aktif; tidak mengunduh bobot di server.
- E07 full memakai kuota yang sudah direservasi; push hanya setelah pemeriksaan kuota ulang. Tidak ada jaminan0,70.

## Verifikasi
Kompilasi, validasi hash CSV/E01/revision, assertion train/validation/test disjoint, finite outputs dan bobot benar berubah. Full740 ID unik/splitbaseline/label cocok, skor ulang dari CSV. Bukti teknis/memori/waktu dan batas evaluasi dicatat.

## Referensi
- https://huggingface.co/intfloat/multilingual-e5-base
- https://huggingface.co/docs/transformers/v5.17.0/en/main_classes/model

## Persiapan dan keputusan smoke
- Worker/launcher smoke/full selesai dibuat dan dikompilasi. Audit lima inner split disjoint; subset smoke32/16 mencakup semua7kelas. Checkpoint config memakai versi torch string agar compatible dengan weights_only reload.
- API terbaru timeUsed11892,8s, reserved0s, allowed21600s; E07 full RUNNING. Bahkan dengan asumsi konservatif E07 memakai seluruh batas7200s, smoke1800s masih di bawah sisa snapshot. Lanjut smoke private, full tetap menunggu hasil/waktu/kuota ulang.
- Smoke subprocess1200s dan pip600s, batas API1800s. Menggunakan warmup10% lalu LR tetap dan mencatat indeks seluruh split untuk audit.
- Push smoke v1 berhasil. Kaggle membuat slug dari title `tempo-e10-semantic-finetune-smoke`; metadata diperbaiki mengikuti slug aktual tanpa repush/restart. Full memakai slug selaras `tempo-e10-semantic-finetune-full`.

## Hasil smoke dan batas full
- Smoke v1 COMPLETE. Audit finite loss/grad, encoder/head berubah pada inner dan refit, checkpoint reload probabilitas/prediksi cocok;32/16/16 indeks disjoint dan sesuai outerfoldbaseline,16 ID/label/probabilitas valid, hash worker cocok.
- Peak GPU5,2183GiB; warm epoch32sampel0,9551s. Proyeksi training maksimum5fold*(474+592)*12 sekitar1909s, belum termasuk setup/validasi/teks lebih panjang.
- Bukti JSON/CSV/history/log tanpa bobot disalin ke `docs/server-recovery/2026-10-10/e10_smoke/`.
- Enam berkas bukti salinan lokal/server cocok SHA256. Smoke hanya bukti teknis; skor16 target tidak menjadi klaim kualitas atau dasar tuning.
- Full disiapkan batas subprocess4800s dan API5400s (90menit), memberi ruang lebih dari proyeksi kasar. Snapshot API timeUsed12186,9s/21600, reserved0; E07 masih RUNNING dan pelaporan reservasi tidak mencerminkan job aktif. Full ditahan sampai E07 selesai atau tersedia bukti anggaran gabungan cukup. Tidak memotong protokol epoch hanya demi memaksakan kuota.

## Koreksi kuota dan keputusan full
- Inspeksi objek API asli membuktikan `total_time_allowed` adalah `datetime.timedelta(days=1, seconds=21600)`: **108000s/30jam**, bukan21600s/6jam. Serialisasi SDK `.to_dict()` menghilangkan komponen hari; `.total_seconds()` adalah pembacaan yang benar.
- Snapshot objek asli timeUsed13154,470536s, reserved0s, allowed108000s, sisa94845,529464s (26jam20menit). Anggaran jauh cukup untuk sisa batas E07 dan full E10 bersamaan; alasan penundaan sebelumnya berasal dari pembacaan SDK yang salah.
- Buat reporter numerik memakai `.total_seconds()`, simpan snapshot `04_hasil_eksperimen/e10_full/quota_before_push.json` dan salinan bukti lokal `docs/server-recovery/2026-10-10/e10_full/`, koreksi catatan lama, lalu push full E10 v1 batas5400s. E07 tetap aktif dan tidak direstart.
- Reporter dikompilasi dan snapshot10:12:40 UTC mencatat allowed30jam, used13238,781017s, available94761,218983s/26,32256jam. Launcher private/flagfull/hash worker sesuai smoke tervalidasi. Full `tempo-e10-semantic-finetune-full` v1 berhasil dipush dan API RUNNING; E07 juga masih RUNNING.

## Hasil full dan audit
- Full v1 COMPLETE, OOF Macro-F1 **0,49091247767012647**, di bawah terbaik E11 0,5436173125. Epoch pilihan inner per fold5/4/4/5/6; hasil ini tidak menggantikan model terbaik.
- `01_notebook/kaggle_e10/verify.py` memeriksa740 ID/label/probabilitas, argmax, split outer baseline dan inner seed persis, pemilihan epoch/early stopping dari history, perubahan encoder/head serta hash data/source. Skor TP/FP/FN manual cocok persis.
- Sembilan berkas JSON/JSONL/CSV disalin tanpa bobot ke `docs/server-recovery/2026-10-10/e10_full/e10_full/`; seluruh SHA256 cocok server. Bukti audit `verification.json`, log kernel juga disimpan.
- Snapshot10:35:24 UTC: allowed108000s, used15771,078003s, reserved0, available92228,921997s/25,6191jam. Reservasi berubah antar snapshot dan tidak dipakai untuk menyimpulkan job berhenti; status job diperiksa langsung. Target0,70 belum tercapai, lanjut smoke E12 sesuai plan terpisah.
