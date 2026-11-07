# Plan Dokumen Batasan Masalah dan Perbaikan

**Tanggal:** 2026-10-17
**Status:** done

## Tujuan
Menyusun dokumen Markdown yang menjelaskan batasan masalah proyek, kondisi
aktual terhadap target wajib, dan pekerjaan perbaikan yang diprioritaskan.

## Ruang Lingkup
- Menambahkan dokumen `docs/BATASAN_MASALAH_DAN_PERBAIKAN.md`.
- Menggunakan bukti OCR holdout final dan ranking model joint terbaru.
- Memperbarui `CHANGELOG.md` setelah dokumen selesai.
- Tidak mengubah kode, model, dataset, ground truth, atau hasil eksperimen.

## Langkah
1. Rumuskan batasan objek, data, task, OCR, model, evaluasi, XAI, dan deployment.
2. Catat baseline dan gap target berdasarkan hasil teraudit.
3. Susun perbaikan menurut prioritas dan acceptance criteria yang terukur.
4. Periksa konsistensi angka dan tautan artefak.
5. Catat dokumen baru ke changelog.

## Risiko & Asumsi
- Dokumen membedakan target wajib dari hasil yang sudah tercapai.
- Estimasi solusi tidak boleh dinyatakan sebagai hasil eksperimen.
- Perubahan ruang lingkup penelitian perlu persetujuan peneliti/dosen.

## Verifikasi
Angka OCR dan Macro-F1 cocok dengan artefak hasil, seluruh target memiliki
definisi lulus yang eksplisit, dan dokumen dapat dibaca sebagai backlog kerja.
