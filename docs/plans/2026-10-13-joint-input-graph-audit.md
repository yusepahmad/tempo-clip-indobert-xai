# Audit gabungan input gambar dan teks

**Tanggal:** 2026-10-13
**Status:** done

## Tujuan
Membuktikan rekonstruksi graph penuh CLIP–IndoBERT joint MTL untuk mendukung integrasi XAI delivery tanpa menunggu GPU E44.

## Ruang Lingkup
- Utility baru `DEMO_XAI_745_FULL/01_notebook/tail_graph_audit/joint_audit.py`, laporan E41, recovery dan CHANGELOG.
- Tidak mengubah checkpoint, dataset, label, source eksperimen atau aplikasi delivery.

## Langkah
1. Gabungkan forward CLIP gambar full/crop dan IndoBERT teks asli, mengganti dua blok terakhir sesuai checkpoint masing-masing fold.
2. Periksa lima sampel heldout (satu per fold), hash input/weights/checkpoint dan parity logit dengan jalur cache canonical.
3. Untuk kelas prediksi yang sama, periksa gradien ketiga task ke kedua view gambar dan embedding teks; randomisasi classifier Task1 harus mengubah kedua gradien.
4. Jalankan CPU server, sinkronkan laporan dan catat hasil aktual.

## Risiko & Asumsi
Lima sampel bukan sertifikasi seluruh dataset. Gradien pada view praproses dan embedding belum membuktikan overlay koordinat asli, fidelity perturbasi atau E2E unggahan baru. E41 hanya kandidat teraudit, bukan model delivery baru.

## Verifikasi
Hash, disjoint heldout/train, finite nonzero gradients, logit per-modalitas maxabs <2e-5, gabungan <4e-5 dan argmax sama, randomization sensitivity untuk kelas yang sama. Hasil tidak menggantikan target semua Macro-F1 >=0,70.

## Penyesuaian numerik
Run awal gagal batas gabungan2e-5 (Task2 2,0325e-5). Untuk dua rekonstruksi sekaligus, audit kini memeriksa masing-masing kontribusi visual/text <2e-5, gabungan <4e-5, serta argmax identik semua task. Batas tidak digunakan untuk memilih skor atau checkpoint.

Run kedua menunjukkan sumber selisih terutama jalur visual (maks2,0385e-5), teks <7,2e-7. Kriteria parity FP32 kini scale-aware torch.allclose rtol1e-5/atol2e-5 per-modalitas dan gabungan, tetap mencatat maxabs dan wajib argmax sama. Tidak mengklaim bitwise parity.

## Hasil aktual
Lima fold heldout lulus joint fullgraph parity scale-aware; semua argmax identik cache. Maks selisih logit gabungan2,0325184e-5 (fold4 Task2). Semua3task memiliki gradien finite nonzero ke dua view pixel dan embedding; randomisasi classifier Task1 pada kelas yang sama mengubah kedua gradien. Hash laporan/source lokal cocok server. Bukan sertifikasi fidelity/overlay/upload; skor tidak berubah.

## Sinkronisasi catatan
Plan ini dan plan E44/E45/recovery serta CHANGELOG disalin ke docs/root package eksperimen server .31 agar catatan sumber sesuai workspace. Tidak mengubah runtime delivery.
