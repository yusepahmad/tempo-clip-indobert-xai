# Penyelarasan delivery dengan tesis CLIP–IndoBERT MTL XAI

**Tanggal:** 2026-10-12
**Status:** done

## Tujuan
Mengembalikan model utama ketiga task ke satu shared-head multi-task CLIP–IndoBERT, dengan XAI model yang sama dan pelaporan skor yang benar.

## Ruang Lingkup
- Paket baru `delivery/week34_clip_indobert_20261012/`, runtime, UI, metadata model, dokumentasi, pengujian dan bundel ZIP.
- Deployment terisolasi server .31, verifikasi port 7863 lalu pergantian layanan utama 7862 setelah lulus.
- Plan sebelumnya dan CHANGELOG root untuk menjelaskan E14 menjadi pembanding.
- Dataset, label, hasil penelitian historis, dan arsip E14 tidak diubah. Tidak menjalankan layanan AI berbayar atau eksperimen GPU baru.

## Langkah
1. Salin sumber delivery yang telah diperbaiki UX-nya tanpa cache/weights dan runtime E14.
2. Aktifkan satu model joint MTL tiga task; tambahkan identitas, protokol dan kontrak XAI yang sesuai.
3. Sesuaikan UI, dokumentasi, launcher dan notebook; pisahkan hasil E14 sebagai pembanding.
4. Jalankan regresi, pengujian arsitektur, inferensi HTTP/upload baru, XAI, UI dan evaluasi fusion lima fold bila sumber tersedia.
5. Deploy layanan utama setelah lulus; bangun dan verifikasi paket baru, catat perubahan dan hasil aktual.

## Risiko & Asumsi
- Baseline menggunakan encoder beku dan melatih shared layer serta tiga head, bukan fine-tuning encoder; harus dinyatakan.
- Macro-F1 historis Task2 0,3197261392590282 tidak boleh diklaim 0,5663 atau 0,70.
- LOO dataset, in-sample batch, dan unggahan baru berbeda dari evaluasi CV historis.
- XAI visual adalah gradient × activation patch CLIP; XAI teks LIME/occlusion bukan bukti kausal kebenaran metafora.

## Verifikasi
Regresi Python/JavaScript, pemeriksaan tiga head dan joint loss, API identitas seluruh task, unggahan baru dan OCR/XAI, browser desktop/mobile, pemeriksaan ZIP/hash dan pemeriksaan layanan port 7862. Simpan bukti baru terpisah dari bukti E14.

## Hasil Aktual
- Paket terisolasi dibuat di `delivery/week34_clip_indobert_20261012/DEMO_XAI_745_FULL`, default joint MTL tiga task, encoder beku; E14/Qwen/SVC tidak menjadi runtime utama.
- Identitas/protokol/XAI seluruh task diperbarui bersama UI, notebook pemeriksaan, launcher, DELIVERY.md dan statusWeek34. Arsip E14 lama hash-nya tidak berubah.
- Fusion5fold direproduksi identik:0,4380318985 /0,3197261393 /0,2763519250; metrik historis tidak ditimpa.
-85tesPython,4skripJavaScript, HTTP3task/edit/upload/occlusion/LIME/batch/review/ekspor/cancel, browserdesktop/mobile5tab dan unggahanfoto dosen+OCR+LIME+heatmap lulus.
- Layanan utama `.31:7862` dialihkan setelah verifikasi7863; identitas dan analisis nyata port7862 lulus. Environment Python bersih yang sudah tersedia digunakan kembali; tidak mengklaim instalasi bersih baru.
- ZIP baru sudah dibangun dan lulus CRC/hash/exclusion/secret scan; final bundel mencakup catatan ini. Batasan: target0,70/Windows/uji manusia belum terpenuhi.
- Bukti terpisah `07_delivery_evidence/`; rujukan utama `docs/DELIVERY_MAIN_MODEL.md`.
