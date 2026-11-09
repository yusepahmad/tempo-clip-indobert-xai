# Handoff lanjutan ke server

**Tanggal:** 2026-10-06
**Status:** done

## Tujuan
Menyediakan source terbaru, konteks audit, panduan setup/verifikasi dan prompt lanjutan untuk melanjutkan pekerjaan pada server.

## Ruang Lingkup
`docs/HANDOFF_SERVER.md`, salinan docs/AGENTS dalam paket, salinan tiga foto dosen di `06_gambar_revisi/`, requirements verifikasi, arsip handoff/manifest, plan/changelog. Tidak deploy/upload ke server, mengubah model/dataset atau menyatakan semua revisi selesai.

## Langkah
1. Dokumentasikan status, keputusan user, temuan R5/OCR/UI/paket, tugas berikutnya dan batas bukti.
2. Siapkan setup Python, dependensi test, perintah menjalankan via tmux serta akses SSH tunnel localhost.
3. Sinkronkan docs/aturan proyek dan buat arsip source/data/gambar/hasil audit yang relevan tanpa venv/cache/job/credential/checkpoint besar.
4. Verifikasi integritas ZIP, kesamaan source, daftar pengecualian dan checksum.

## Risiko & Asumsi
Alamat/OS server belum disebut: panduan mengasumsikan Linux Python 3.10/3.11; tidak melakukan koneksi. Setup pertama butuh unduhan encoder. Job lokal/heatmap dalam cache tidak dipindah; ekspor URL lama bukan tautan portabel. ZIP adalah handoff pekerjaan, bukan final client.

## Verifikasi
HTML terbaru identik dalam ZIP, docs/audit/aturan tersedia, tes dependensi tercatat, ZIP CRC/checksum valid.

## Hasil
Panduan setup/tmux/tunnel/test dan prompt Codex siap. Source/data/740 gambar/3 foto revisi/hasil audit/metrik training/aturan disertakan; cache/job/venv/checkpoint besar/arsip bersarang tidak disertakan. Arsip CRC serta kecocokan source/panduan/audit lulus, manifest per-file dan SHA256 disediakan. Tidak ada koneksi/deploy ke server; environment bersih belum diuji.
