# Notebook Full dan Audit Kelengkapan Bukti

**Tanggal:** 2026-11-02
**Status:** done

## Tujuan
Melengkapi penyajian tiga notebook agar seluruh bukti revisi yang sudah tersedia dapat dibaca dan ditemukan dari notebook, termasuk confusion matrix baseline yang terlewat di notebook 02.

## Ruang Lingkup
- Generator notebook dan pemeriksaan kelengkapan pada `DEMO_XAI_745_FULL/01_notebook/revisi_ii/`.
- Delivery baru `delivery/HASIL_REVISI_JOY_20261102_R3_FULL/`, tiga notebook beserta HTML, indeks bukti, laporan QA, ZIP lengkap dan ZIP bukti.
- Plan ini dan `CHANGELOG.md`; paket lama dipertahankan.
- Tidak mengubah dataset, label, prediksi, skor, checkpoint, atau mengadakan training/penilaian manusia baru.

## Langkah
1. Audit seluruh manifest bukti revisi, indeks status, generator, dan keluaran tiga notebook terhadap paket R2.
2. Tambahkan semua bukti yang sudah tersedia ke bagian notebook terkait, dengan judul dan sumber yang jelas. Sediakan indeks cakupan seluruh butir termasuk yang masih terbuka.
3. Bangun R3_FULL dari paket R2, perbarui generator/sumber terkait, jalankan tiga notebook dan ekspor HTML; bangun ulang navigasi bukti.
4. Verifikasi setiap berkas manifest dapat ditemukan dari notebook, seluruh gambar/tabel tersedia, tautan lokal valid, dan data/model/analisis tetap identik dengan R2.
5. Periksa tampilan HTML bila browser tersedia; susun laporan kelengkapan, changelog, manifest hash, ZIP dan checksum. Uji ZIP setelah ekstraksi.

## Risiko & Asumsi
- “Full” berarti seluruh bukti yang sudah tersedia ditampilkan/ditautkan secara lengkap, bukan mengklaim sembilan butir terbuka sudah selesai.
- Tabel besar dan source disajikan dengan navigasi dan lampiran agar notebook tetap terbaca; gambar diagnosis R20 ditampilkan ketiganya secara langsung.
- Reproduksi lokal diverifikasi; keberhasilan Colab tidak diklaim tanpa dijalankan di Colab.
- Audit menemukan confusion matrix E14 tambahan di analisis canonical. R20 kini menyertakan empat model (baseline, E11, E42, E14); bukti per revisi bertambah dari 139 menjadi 141 berkas tanpa membuat prediksi baru.
- Browser tidak tersedia pada sesi ini (inventaris kosong dan pembukaan IAB gagal). QA tampilan dibatasi pada pemeriksaan HTML, anchor, gambar terlampir dan kelengkapan tabel; tidak mengklaim screenshot browser baru.

## Verifikasi
- Run all ketiga notebook tanpa error; baseline, E11, E42 dan E14 tampil sebagai output gambar notebook 02.
- Audit otomatis semua manifest bukti dan indeks revisi terhadap notebook/HTML; tidak ada berkas/tautan yang hilang.
- Validator paket, hash input/prediksi/analisis/model, CRC ZIP dan checksum lulus, termasuk paket ekstraksi.

## Hasil aktual
- Generator notebook menampilkan empat confusion matrix Task 3 langsung pada notebook 02: baseline, E42, E11 dan E14.
- Seluruh 141 berkas bukti pada 19 butir selesai teknis dan 21 lampiran canonical ditampilkan dalam tiga notebook. Seluruh 46 tabel CSV ditampilkan tanpa pemotongan baris; semua gambar XAI tersedia. Seluruh 28 butir memiliki bagian termasuk sembilan yang tetap terbuka.
- Audit output/HTML lulus: 162 berkas, 48 hash gambar unik, 1.008 tautan lokal; tidak ada berkas manifest, bagian revisi atau analisis/dokumen canonical yang terlewat.
- Ketiga notebook lulus Run all lokal dan Run all ulang dari ekstraksi ZIP. Kandidat arsip lengkap lulus 1.808 hash dan 231 baris metrik yang dihitung independen; 499 file input/analisis/model/instrumen/protokol/XAI tetap identik R2.
- Sepuluh tes evaluator lulus. Tiga simulasi kelalaian ditolak pemeriksa: output baseline dihapus, penanda bukti dihapus, dan baris CSV dipotong. Simulasi hanya di memori dan tidak mengubah artefak asli.
- ZIP bukti mandiri lulus CRC/SHA256, 474 hash dan 733 tautan lokal setelah ekstraksi terpisah. Tautan HTML notebook tetap berada dalam arsip bukti.
- Source, laporan QA, plan dan changelog disertakan pada paket R3_FULL. Pemeriksaan browser visual/Colab tidak dijalankan karena browser tidak tersedia; tidak dibuat screenshot browser baru atau skor manusia buatan.
