# E33 — Hasil optimasi joint CLIP–IndoBERT MTL

12Oktober2026. Satu shared layer dan tiga head joint loss; encoder beku.24konfigurasi ditetapkan sebelum outertest, dipilih lewat2innerfold per5outerfold identik baseline.

| Task | Baseline | E33 nested | Delta |
|---|---:|---:|---:|
| Isuutama |0,4380|0,3951|-0,0430|
| Domainsumbermetafora |0,3197|0,3530|+0,0333|
| Tipeentitas |0,2764|0,3196|+0,0433|

Kontrolbaseline direproduksi identik. Auditor server mengulang selectedinnerfit, selectedouterfit dan baselinefit; prediksi740sampul×3task cocok. Auditor rootstdlib menghitung ulang MacroF1 dan pairedbootstrap2000replicates. Interval eksploratif deltaTask2[0,00587;0,06120] tidak memperhitungkan ketergantungan antar-foldtrain maupun bias banyak eksperimen, sehingga bukan jaminan peningkatan pada sampul baru.

Belum ada promosi delivery: Task1turun dan integrasiXAI kandidat belum diuji. Demo utama tetap baseline. Target0,70 belum tercapai.

Kelas lemah Task2: LAINNYA F1~0,206; KONSUMSI_TRANSAKSI~0,221; BENCANA_JERAT~0,276. Confusionterbesar antara MESIN_INFRASTRUKTUR dan KONSUMSI_TRANSAKSI/BENCANA_JERAT/PERMAINAN_KONTES. Diagnosis ini menunjukkan batas representasi frozen dan ambiguitas kelas yang perlu diperiksa; tidak membuktikan label salah. Label tetap dipertahankan.

Langkahberikutnya E34 membuka2blok terakhir keduaencoder dengan LRkecil dan epochselection hanya innerholdout, termasuk opsi epoch0. Ini menghindari memilih epoch memakai testfold; full-finetuning120epoch sebelumnya menurunkan Task2ke0,2461. GPUhanyaKagglegratis yang diizinkan pengguna, dengan smoke dan budgetguard.

Bukti: [result](server-recovery/2026-10-12/e33_joint_mtl/result.json), [rootaudit](server-recovery/2026-10-12/e33_joint_mtl/root_verification.json), [plan](plans/2026-10-12-e33-joint-mtl-optimization.md). Penanganan konflikgradien merupakan kandidatriset selanjutnya, mengacu [PCGrad](https://arxiv.org/abs/2001.06782); E33belum mengimplementasikanPCGrad.
