# Pemeriksaan Delivery Terakhir

**Tanggal:** 2026-11-01
**Status:** done

## Tujuan
Mengidentifikasi delivery lokal terakhir, memeriksa integritas dan isi paket, serta merangkum status dan batasan yang didukung bukti.

## Ruang Lingkup
- Pemeriksaan read-only terhadap `delivery/`, dokumentasi hasil, panduan, dan bukti verifikasi terkait.
- Perubahan hanya pada file plan ini dan `CHANGELOG.md` untuk mencatat pemeriksaan yang selesai.
- Source aplikasi, model, dataset, artefak delivery, serta layanan eksternal tidak diubah.

## Langkah
1. Identifikasi paket terbaru berdasarkan tanggal release, inventaris lokal, dan changelog.
2. Baca panduan serta bukti verifikasi paket dan bandingkan dengan status eksperimen terbaru.
3. Verifikasi ulang checksum SHA-256 dan CRC tiga ZIP pembanding (Colab PREPARATION, eksperimen final, Windows R3), hash konten bila ada manifest, serta kelengkapan komponen utama tanpa ekstraksi.
4. Catat hasil pemeriksaan pada plan dan changelog, lalu laporkan paket yang tepat dan batasannya.

## Risiko & Asumsi
- Delivery terakhir diartikan sebagai paket yang tersedia lokal; bukti pengiriman atau penerimaan klien belum tersedia.
- Timestamp filesystem dan indeks lama bukan bukti tunggal urutan release.
- Pemeriksaan integritas tidak membuktikan runtime Windows atau Colab berhasil; bukti historis dipisahkan dari verifikasi ulang saat ini.
- Root workspace tidak memiliki metadata Git yang dapat dibaca.

## Verifikasi
- Checksum ZIP cocok dengan file `.sha256`; seluruh entry lolos CRC.
- Inventaris ZIP sesuai bukti packaging dan memuat panduan, notebook, data/model, serta web yang dijanjikan.
- Status model dan batasan ditelusuri ke panduan serta laporan hasil, tanpa menyatakan pengujian runtime baru.

## Hasil Pemeriksaan — 1 November 2026

| Paket lokal | Ukuran byte | File ZIP | Hash konten yang diperiksa | Hasil |
| --- | ---: | ---: | ---: | --- |
| `delivery/colab_micro_e14_20261020/build_01/TEMPO_MICRO_E14_COLAB_PREPARATION_20261020.zip` | 97.715.920 | 765 | 764 | SHA-256 arsip, CRC dan manifest lulus |
| `delivery/experiment_final_20261020/TEMPO_EXPERIMENT_FINAL_20261020.zip` | 3.131.185.835 | 6.547 | 6.546 | SHA-256 arsip, CRC dan manifest lulus |
| `delivery/update_20261019/clean_windows_r3/TEMPO_WINDOWS_UPDATE_20261019_R3.zip` | 101.521.865 | 798 | 797 | SHA-256 arsip, CRC dan manifest lulus |

Setiap manifest tidak mencantumkan hash dirinya sendiri; seluruh file lainnya tercakup. Tidak ditemukan path absolut/traversal, nama entry duplikat, atau file manifest yang hilang. Verifikasi dilakukan tanpa ekstraksi, perubahan ZIP, atau menjalankan ulang aplikasi.

### Identitas delivery dan temuan

1. Artefak paling baru yang ditemukan adalah Colab PREPARATION, dibuat 20 Oktober 2026 pukul 02.18 WIB menurut `PACKAGE_STATE.json`. `checkpoint_verified=false`, stage `preparation_only_checkpoint_pending`, dan tidak ada `adapter_model.safetensors` dalam ZIP. Paket belum siap untuk inferensi E14. Status GPU Colab tetap Not Evaluated.
2. Paket final eksperimen tanggal 20 Oktober memuat ketiga notebook presentasi, wrapper setup/jalankan Windows, source web dan manifest lengkap. README menyatakan runtime CLIP–IndoBERT; hasil E14 adalah hasil riset, belum model aktif web. Bukti packaging historis menyatakan runtime hasil ekstraksi pernah lolos, tetapi pemeriksaan ini tidak mengulang runtime.
3. Tidak ditemukan entry `ci_d01` di paket final. Hasil eksperimen duplikasi training 2× yang dicatat belakangan di `docs/EKSPERIMEN_CLIP_INDOBERT_DUPLIKASI_2X_2026-10-20.md` belum masuk snapshot ZIP ini dan tidak dipromosikan ke web.
4. Windows R3 tanggal 19 Oktober adalah paket Windows khusus terakhir yang ditemukan. Laporan di luar/dalam ZIP identik, tetapi memuat snapshot E14 dua fold terverifikasi, sebelum hasil final 740 OOF. Ia bukan ringkasan penelitian terbaru.
5. Hasil final MICRO-E14 740 OOF yang tercantum di paket final dan dokumentasi adalah Micro-F1 Task 1/2/3 `0,720270 / 0,566216 / 0,667568` dan Macro-F1 `0,673321 / 0,510282 / 0,595480`. Target 0,70 seluruh task belum tercapai.
6. Folder model lokal `DEMO_XAI_745_FULL/06_models/micro-e14-qlora-v1/` hanya memuat kontrak, konteks visual dan manifest aset saat pemeriksaan. Ledger refit terakhir masih observasi historis RUNNING pada 20 Oktober pukul 02.20 WIB; status Kaggle live tidak diperiksa dan tidak diasumsikan masih RUNNING sekarang.
7. Clean Windows, inferensi GPU Colab, dan penerimaan pengguna tidak diuji dalam pemeriksaan ini. Tidak ada bukti pengiriman/penerimaan klien yang diperiksa; kesimpulan hanya mencakup artefak lokal.

### Checksum arsip terverifikasi

- Final eksperimen: `7c7b74c986855022dc33faf8d0324ca9eb99324b5276199f8ded1c6867740692`.
- Colab PREPARATION: `d639215d7b605d483e6e6e331d6c55c9bf886709990bf9da4b6c2c5cd6c134b2`.
- Windows R3: `bdea8443ae2674bb4623dca02ab902be927684033ea1433a07188c7160a37762`.
