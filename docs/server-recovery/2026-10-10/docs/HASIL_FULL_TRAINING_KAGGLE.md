# Hasil full training Kaggle

> **Dokumen riwayat per 5 Oktober 2026** (audit hasil training). Status terbaru: [STATUS_REVISI_20261006.md](STATUS_REVISI_20261006.md) (6 Oktober 2026). Per 6 Okt keputusannya tidak berubah: fine-tuning Kaggle tidak dipakai karena Task 2 turun, paket delivery memakai baseline, dan checkpoint Kaggle belum diunduh atau diintegrasikan.

Tanggal audit: 2026-10-05. Kernel `yusepmuhamadzazuli/tempo-full-training`: **COMPLETE**.
Plan: [audit hasil training](plans/2026-10-05-audit-hasil-full-training.md).

## Hasil yang terverifikasi

Lima fold selesai masing-masing120epoch (600 record unik), loss finite. Hash dataset dan notebook cocok dengan sumber lokal. Prediksi740sampul unik mencakup setiap sampul tepat sekali dan indeks test cocok dengan StratifiedKFold5, seed42, stratifikasi isu dengan kelas langka digabung. Metrik dihitung ulang dari prediksi per fold dan cocok dengan OOF/metrik final.

Waktu yang dijumlahkan dari record epoch: **2,95jam**. Ini waktu compute epoch, bukan total waktu job termasuk setup/evaluasi. Tidak ada smoke output yang dipakai.

| Task | Macro-F1 baseline | Macro-F1 fine-tuned | Selisih | Accuracy fine-tuned |
|---|---:|---:|---:|---:|
| Isu utama | 0,4380 | 0,5139 | +0,0759 | 57,16% |
| Domain sumber metafora | 0,3197 | 0,2461 | −0,0736 | 34,32% |
| Jenis entitas sasaran | 0,2764 | 0,3699 | +0,0936 | 54,05% |

Baseline berasal dari `hasil_mtl_740_task2domain.json`, menggunakan encoder beku dan head fusion. Script baseline menggunakan konstruksi split5fold/seed42/stratifikasi yang sama; fine-tuning memperbarui kedua encoder. Ini perbandingan eksperimen OOF, bukan bukti signifikansi statistik atau performa pada korpus eksternal.

## Keputusan untuk demo

**Pertahankan baseline sebagai default.** Fine-tuning tidak meningkatkan semua task: domain metafora yang menjadi fokus demo justru menurun. Accuracy domain sedikit lebih tinggi daripada baseline32,03%, tetapi Macro-F1 lebih rendah, sehingga accuracy saja memberi gambaran yang tidak lengkap.

Recall Task2 per kelas: Bencana/Jerat12,0%; Hewan/Tubuh13,3%; Konsumsi/Transaksi7,1%; Lainnya4,8%; Mesin/Infrastruktur78,5%; Non Metafora49,4%; Permainan/Kontes11,3%. Hasil menunjukkan performa antar kelas tidak seimbang. Macro-F1 per fold Task2 sekitar0,213–0,253; penurunan bukan hanya satu fold.

Penyebab belum dibuktikan. Epoch panjang, konfigurasi learning rate, pembobotan loss dan optimasi bersama perlu diuji terkontrol jika eksperimen lanjutan dilakukan. Jangan menyebut overfitting sebagai diagnosis pasti tanpa validasi sepanjang training. Pemilihan epoch/hyperparameter berikutnya membutuhkan inner validation; jangan menyesuaikan model langsung pada outer test lalu melaporkan test yang sama sebagai evaluasi independen.

## Artefak lokal dan batas audit

Direktori `DEMO_XAI_745_FULL/04_hasil_eksperimen/finetuned_kaggle/` berisi log Kaggle; subdirektori `tempo_full/` berisi metrik/prediksi lima fold, OOF, history600epoch, progress akhir, metrik per kelas dan:

- `week3_audit.json`: metrik tiga task, confusion matrix, precision/recall/F1 per kelas dan contoh salah.
- `training_protocol_audit.json`: cakupan epoch, split, loss dan hash notebook.

Audit dijalankan dengan `--metrics-only`: **checkpoint besar belum diunduh/diperiksa**, dan aplikasi belum memakai model fine-tuned. File bobot tetap tersedia pada output Kaggle. Pemeriksaan isi checkpoint, adapter arsitektur, tokenizer/preprocessing dan atribusi diperlukan jika model ini akan menjadi opsi pembanding di demo. Paket review Week3 sebelumnya masih memuat baseline, bukan hasil training baru.

```bash
DEMO_XAI_745_FULL/venv/bin/python DEMO_XAI_745_FULL/01_notebook/audit_finetuned_week3.py DEMO_XAI_745_FULL/04_hasil_eksperimen/finetuned_kaggle/tempo_full --metrics-only
```
