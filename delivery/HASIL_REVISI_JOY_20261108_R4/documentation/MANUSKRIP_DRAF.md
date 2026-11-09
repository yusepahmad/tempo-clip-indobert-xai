# Kelayakan MTL CLIP–IndoBERT untuk Dekoding Metafora Sampul Tempo: Evaluasi Macro-F1 dan Batas Penjelasan Model

**Status:** draf materi penelitian untuk diperiksa Joy/pembimbing; belum mengikuti template jurnal tertentu, belum melalui penilaian manusia tambahan, dan belum disubmit. Bagian yang memerlukan bukti manusia dinyatakan terbuka.

## Abstrak
Penelitian ini mengevaluasi arsitektur multi-task learning CLIP–IndoBERT untuk klasifikasi isu, domain sumber metafora, dan tipe entitas sasaran pada740 sampul majalah Tempo. Evaluasi menggunakan lima outer fold dan pemilihan konfigurasi pada inner fold. Audit ulang menggunakan Macro-F1 menunjukkan bahwa peringkat kandidat bergantung kuat pada metrik dan dapat berbeda dari peringkat akurasi. Model E42, yang dipilih post-hoc dari kandidat arsitektur yang memenuhi spesifikasi, menghasilkan Macro-F1 sekitar0,525/0,396/0,403. Angka merupakan seleksi pada korpus yang digunakan berulang dan berpotensi optimistis; belum merupakan validasi eksternal. Ablasi terkontrol dan pengujian XAI memperlihatkan keterbatasan yang tidak dapat diringkas sebagai keberhasilan universal MTL. Nilai kesepakatan anotator dan penilaian XAI independen belum tersedia dan tidak diestimasi sebagai pengganti data manusia.

## Pendahuluan dan kontribusi
Sampul pers menggabungkan ilustrasi dan tulisan untuk menyampaikan kritik dan hubungan metaforis yang tidak selalu dapat dipahami dari satu modalitas saja. Penelitian ini menguji kelayakan arsitektur multimodal dengan representasi visual CLIP dan teks IndoBERT yang dilatih dengan tiga objective. Fokus pertanyaannya adalah kinerja per task, kontribusi pembelajaran bersama dibanding kontrol, dan batas interpretasi penjelasan model.

Kontribusi yang dapat didukung adalah penataan korpus dan evaluasi tiga task, audit empiris perubahan seleksi ketika metrik diganti, serta pemetaan keterbatasan arsitektur/protokol dan penjelasannya. Klaim bahwa korpus merupakan yang pertama di dunia tidak dibuat tanpa kajian pembanding. Qwen3-VL QLoRA digunakan sebagai pembanding berskala lebih besar dengan konteks input yang dijelaskan, bukan sebagai pengganti diam-diam arsitektur utama.

## Data dan anotasi
Dataset canonical berisi740 ID dengan10 kelas isu,7 kelas domain sumber dan8 kelas tipe entitas. Jumlah dan distribusi per kelas dapat direproduksi dari dataset paket. Label merupakan interpretasi anotasi, bukan kebenaran objektif tunggal. Kolom keyakinan anotator bukan ukuran agreement antar dua manusia.

Menurut klarifikasi Joy yang diteruskan pengguna pada 2 November 2026, korpus berkurang karena banyak citra sampul berkualitas buruk sehingga tidak dapat dilabeli; menurut Joy alasan ini telah disampaikan sebelumnya. Dengan demikian alasan umum penyusutan telah dijelaskan. Pesan menyebut sekitar 1.000 ke 700-an; angka spesifik 1.040 berasal dari dokumen revisi/proposal dan 740 ID terverifikasi pada dataset. Riwayat keputusan per ID belum dapat direkonstruksi dari berkas yang tersedia, sehingga distribusi eksklusi dan analisis sensitivitas tetap terbatas. Kualitas citra tidak disamakan dengan sengketa label atau kesulitan interpretasi semantik. Anotasi independen dua penilai masih diperlukan untuk kappa, terpisah dari penjelasan penyusutan. Paket menyediakan subsampel acak150 sampul untuk anotasi ganda serta60 kasus kelas penampung untuk adjudikasi. Sampai diisi manusia, kappa antaranotator tetap Not Evaluated. Lihat CORPUS_HISTORY.md dan R23_KLARIFIKASI_JOY.json.

## Metode model dan evaluasi
E42 menggunakan CLIP ViT-L/14 beku pada view full/crop, IndoBERT dengan sepuluh blok awal beku serta dua blok terakhir trainable, shared layer256 dan tiga head. Joint Loss berupa CE berbobot kelas dari training dan bobot task tetap; learned uncertainty weighting Kendall tidak diimplementasikan. Variasi LR/loss dan epoch dipilih pada inner fold historis. Outerfold ditetapkan menurut stratifikasi Task 1; keseimbangan Task 2/3 perlu dibaca dari distribusi per fold.

Model utama dipilih setelah kandidat dievaluasi pada korpus yang sama, berdasarkan rerata Macro-F1 per task dengan bobot sama di antara kandidat yang memenuhi arsitektur proposal. Ini seleksi post-hoc, bukan keputusan yang telah dipreregistrasikan sebelum melihat seluruh hasil. Alias dan salinan prediksi didokumentasikan, dan kandidat yang memakai SigLIP2/DINOv2/stacking tidak diberi identitas arsitektur CLIP–IndoBERT utama.

Metrik utama adalah Macro-F1; precision/recall macro, akurasi, kappa model dan metrik per kelas melengkapi laporan. Wilson 95%dipakai untuk akurasi, bootstrap 2000 replikasi untuk macro dan selisih macro berpasangan. Exact McNemar/Holm menguji selisih akurasi, bukan macro. CI bersyarat pada prediksi OOF dan tidak menghilangkan bias seleksi atau ketergantungan training lintasfold. Kriteria keberhasilan berupa perbandingan terukur dengan kontrol, bukan ambang0,70 universal.

## Hasil utama
| task | macro_f1 | macro_ci_low | macro_ci_high | accuracy | kappa |
| --- | --- | --- | --- | --- | --- |
| task1_issue | 0.5255 | 0.4810 | 0.5647 | 0.5541 | 0.4853 |
| task2_domain_sumber | 0.3956 | 0.3606 | 0.4295 | 0.4351 | 0.3154 |
| task3_primary_entity_type | 0.4034 | 0.3555 | 0.4469 | 0.5189 | 0.3537 |

Hasil menunjukkan kemampuan yang terbatas dan tidak merata antar task. Domain sumber tetap lebih sulit daripada isu utama. Tidak ada alasan mengganti Macro-F1 dengan akurasi ketika keduanya memberi gambaran berbeda. Kegagalan baseline web historis terhadap majority pada akurasi Task 3 dilaporkan sebagai temuan baseline itu; kesimpulan tersebut tidak otomatis berlaku pada E42 yang dipilih kemudian.

## Ablasi dan pembanding
| experiment | task | macro_f1 | accuracy | kappa |
| --- | --- | --- | --- | --- |
| RII_TAIL_IMAGE_ONLY | task1_issue | 0.3518 | 0.3649 | 0.2747 |
| RII_TAIL_IMAGE_ONLY | task2_domain_sumber | 0.4318 | 0.4527 | 0.3457 |
| RII_TAIL_IMAGE_ONLY | task3_primary_entity_type | 0.3214 | 0.4365 | 0.2726 |
| RII_TAIL_MTL_UNWEIGHTED | task1_issue | 0.4685 | 0.5405 | 0.4619 |
| RII_TAIL_MTL_UNWEIGHTED | task2_domain_sumber | 0.4110 | 0.4581 | 0.3322 |
| RII_TAIL_MTL_UNWEIGHTED | task3_primary_entity_type | 0.3607 | 0.5446 | 0.3574 |
| RII_TAIL_MTL_WEIGHTED | task1_issue | 0.5073 | 0.5297 | 0.4603 |
| RII_TAIL_MTL_WEIGHTED | task2_domain_sumber | 0.4104 | 0.4365 | 0.3209 |
| RII_TAIL_MTL_WEIGHTED | task3_primary_entity_type | 0.3661 | 0.4986 | 0.3367 |
| RII_TAIL_SINGLE_TASK | task1_issue | 0.4973 | 0.5405 | 0.4668 |
| RII_TAIL_SINGLE_TASK | task2_domain_sumber | 0.4084 | 0.4378 | 0.3210 |
| RII_TAIL_SINGLE_TASK | task3_primary_entity_type | 0.3719 | 0.5216 | 0.3517 |
| RII_TAIL_TEXT_SUPPORTING | task1_issue | 0.4886 | 0.5054 | 0.4379 |
| RII_TAIL_TEXT_SUPPORTING | task2_domain_sumber | 0.2799 | 0.2838 | 0.1692 |
| RII_TAIL_TEXT_SUPPORTING | task3_primary_entity_type | 0.3468 | 0.3905 | 0.2622 |

Resep controlledtail baru memakai backbone/representasi yang sama, fixedLR dan seleksi epoch inner menurut mean Macro, tetapi bukan reproduksi grid6 konfigurasi E42 historis. MTL dan single-task harus dibandingkan per task dan CI; tidak dibuat klaim semua task selalu memperoleh manfaat. E48 lama memakai SVM dan bukan ablation neural murni. Prediksi baseline/unimodal yang dahulu hilang direkonstruksi dan kecocokan baseline740dibuktikan.

Kontrol backbone baru mempertahankan dimensi visual768, teks768, head/loss/split yang sama. Hasil SigLIP2/DINOv2 diposisikan sebagai pembanding backbone pada keluarga frozen yang dinyatakan; tidak disamakan dengan varian E42 yang menyesuaikan tail. Augmentasi moderate historis mengandung rotasi. Rerun baru menghapus rotasi dan menyeimbangkan paparan training, dengan pemilihan pipeline hanya pada inner fold. Pipeline tidak dipilih ulang berdasarkan skor outer.

Konteks input Qwen lebih kaya pada eksperimen historis. Tabel arsitektur×masukan, zero-shot tanpa training, dan refitbasic dengan epoch yang diwarisi dari pilihan inner rich digunakan untuk memeriksa kontribusi input. Sel yang belum memiliki740 prediksi valid tetap terbuka. Perbedaan ukuran model/pretraining/token budget dan sejarah pemilihan epoch membatasi atribusi selisih hanya kepada arsitektur.

## Analisis kelas penampung dan penjelasan
Macro lengkap mempertahankan seluruh kelas dan sampel. Sensitivitas tanpa label penampung serta subset gold non-penampung disajikan dengan definisi yang berbeda dan eksplisit. Task 2dipisahkan menjadi deteksi metafora dan klasifikasi domain pada sampel gold bermetafora; prediksi NON_METAFORA tetap dihitung sebagai kesalahan domain. Kelas tidak dihapus untuk menaikkan angka utama.

XAI E42 direplay pada delapan sampel outer test. Attention rollout menunjukkan aliran perhatian visual yang class-agnostic dan tidak disebut Grad-CAM. LIME menjelaskan head kelas dengan citra ditahan tetap dan menyertakan kecocokan surrogate. Deletion top20% versus kontrol acak memberikan hasil campuran; peta menarik secara visual tidak otomatis faithful. Rubrik/kontrol dan paket lima penilai sudah disiapkan, tetapi skor serta agreement manusia belum tersedia. Karena itu belum ada klaim acceptance manusia atas kualitas penjelasan.

## Keterbatasan
Korpus dipakai berulang untuk pemilihan banyak konfigurasi; kandidat terpilih dapat optimistis. Data berasal dari satu penerbit sehingga kerangka editorialnya tidak mewakili seluruh pers Indonesia. Label adalah interpretasi manusia; agreement belum terukur. Riwayat penyusutan belum lengkap. Crop/resize pada encoder dapat membuang teks/komposisi, dan pembanding Qwen dibatasi citra384 piksel. Opsi jawaban Qwen tetap dalam urutan yang sama sehingga bias posisi belum dikontrol. Fold 1 rich E14 memakai reuseinnerpilot dan batas3 epoch ditentukan setelah riwayat6 epoch; outer test tidak dipakai, tetapi keputusan pilot tetap menjadi keterbatasan desain. Semua temuan adalah internal repeated-corpus evaluation, bukan independent acceptance.

## Etika dan pembatasan penggunaan
Sistem ditujukan untuk analisis deskriptif hubungan visual-verbal dan sasaran kritik dalam korpus penelitian. Prediksinya bukan penetapan kebenaran, kewajaran, atau kelayakan kritik pers dan tidak boleh dipakai untuk menilai seseorang secara otomatis.

Kemampuan mengelompokkan sasaran kritik dapat disalahgunakan untuk memantau, membungkam, atau menekan kritik pers. Penggunaan di luar riset memerlukan penilaian dampak dan pemeriksaan manusia; laporan perlu mengungkap kesalahan, ketimpangan kelas, dan keterbatasan penerbit/korpus secara terbuka.

Paket ini disiapkan untuk penyerahan privat kepada peneliti/pemilik proyek. Paket tidak memberikan lisensi publik atas citra sampul, dataset, atau bobot pihak ketiga. Kebijakan akses riset melalui permintaan tertulis merupakan usulan yang perlu disahkan pemilik data/pembimbing sebelum distribusi lebih lanjut. Model publik dasar tetap mengikuti lisensi penyedianya; tidak ada klaim kepemilikan atas karya sampul.

## Kesimpulan
Evaluasi ulang mendukung pelaporan Macro-F1 per task, pemisahan arsitektur utama dan pembanding, serta pengungkapan seleksi post-hoc. Penelitian menghasilkan bukti kemampuan sekaligus batas MTL CLIP–IndoBERT, dengan hasil negatif/trade-off yang dipertahankan. Validasi eksternal, agreement manusia, adjudikasi codebook dan evaluasi XAI independen merupakan pekerjaan yang masih perlu dituntaskan sebelum mengklaim generalisasi dan acceptance penuh. Target proposal historis yang belum terpenuhi dilaporkan tanpa mengubah hasil atau menetapkan ambang pengganti setelah melihat skor.

## Referensi
Lihat REFERENCES.md. Sitasi model/metode harus mengikuti implementasi aktual, bukan menjadikan related work sebagai klaim modul yang telah digunakan.
