# Codebook operasional 25 kelas

> **Disusun 5 Oktober 2026; isinya masih dipakai aplikasi per 6 Oktober 2026** (`02_web_demo/codebook_operasional.json`: katalog 25 kelas di tab Panduan dan blok "Arti kelas ini" di tab Penjelasan). Status terbaru: [STATUS_REVISI_20261006.md](STATUS_REVISI_20261006.md) (6 Oktober 2026). Statusnya tetap codebook operasional atas instruksi user, bukan codebook resmi; keselarasan dengan anotasi historis belum dibuktikan.

**Tanggal:** 2026-10-05

Disusun Codex atas instruksi pengguna karena codebook resmi tidak tersedia. Definisi, kriteria, batas kelas, dan alasan contoh merupakan rumusan operasional baru untuk demo. Dokumen ini bukan pedoman asli anotator dan bukan pengesahan akademik. Nama kelas, label contoh, headline, serta catatan sumber/sasaran berasal dari dataset; dataset dan model tidak diubah.

Task 1 menjawab isu yang dibahas; Task 2 menjawab domain sumber metafora; Task 3 menjawab jenis entitas sasaran. Satu sampul mempunyai label berbeda untuk masing-masing pertanyaan. Bukti dari satu task tidak otomatis membenarkan task lainnya.

Aturan umum: gunakan sampul, teks, dan konteks bersama; jangan menetapkan kelas hanya dari satu kata atau skor model. Jika beberapa kategori bersaing, catat alasan pemilihan dan alternatif. Definisi ini tidak dipakai untuk mengklaim bahwa model memahami makna atau bahwa prediksi benar.

## Isu Utama

### Korupsi & Suap (`corruption_and_bribery`)

**Definisi:** Penyalahgunaan kewenangan atau sumber daya untuk keuntungan tidak sah, termasuk suap dan penyelewengan.

**Kriteria:** Pusat persoalan adalah dugaan korupsi, pemberian imbalan, atau penyalahgunaan dana/kewenangan.

**Pembeda:** Bedakan dari law_and_justice jika fokus utama adalah proses peradilan, dan dari ekonomi jika kerugian bisnis tidak menjadi isu korupsi.

**Contoh dataset:** `TMP-DB65F6B7A1E4` — SKANDAL BNI, SIAPA MENIKMATI?

Dataset memberi label corruption_and_bribery pada sampul ini. Headline dan teks pendukung dapat dibaca sebagai konteks isu; tidak tersedia alasan anotasi Task 1 yang terpisah. Kecocokan dengan definisi merupakan usulan operasional, bukan rekonstruksi keputusan anotator.

### Kekuasaan & Tata Kelola (`power_and_governance`)

**Definisi:** Pelaksanaan, pembagian, dan pengawasan kekuasaan serta tata kelola pemerintahan.

**Kriteria:** Fokus pada kabinet, kepemimpinan, jabatan, relasi kekuasaan, atau pengelolaan pemerintahan.

**Pembeda:** Persaingan elektoral masuk election_and_political_competition; korupsi eksplisit dapat menjadi isu utama tersendiri.

**Contoh dataset:** `TMP-78163D7E671E` — OPERA SABUN KOCOK KABINET

Dataset memberi label power_and_governance pada sampul ini. Headline dan teks pendukung dapat dibaca sebagai konteks isu; tidak tersedia alasan anotasi Task 1 yang terpisah. Kecocokan dengan definisi merupakan usulan operasional, bukan rekonstruksi keputusan anotator.

### Pemilu & Persaingan Politik (`election_and_political_competition`)

**Definisi:** Pemilihan pejabat dan persaingan aktor politik untuk memperoleh dukungan atau kekuasaan.

**Kriteria:** Pemilu, pilkada, kandidat, kampanye, koalisi elektoral, atau perebutan suara menjadi pokok sampul.

**Pembeda:** Kebijakan atau tata kelola setelah pemilihan lebih dekat dengan power_and_governance.

**Contoh dataset:** `TMP-26EB95FA7B37` — BOWO, JOKO, HATTA & KALLA

Dataset memberi label election_and_political_competition pada sampul ini. Headline dan teks pendukung dapat dibaca sebagai konteks isu; tidak tersedia alasan anotasi Task 1 yang terpisah. Kecocokan dengan definisi merupakan usulan operasional, bukan rekonstruksi keputusan anotator.

### Ekonomi, Bisnis & BUMN (`economy_business_and_state_enterprise`)

**Definisi:** Aktivitas ekonomi, keuangan, dunia usaha, dan pengelolaan perusahaan termasuk BUMN.

**Kriteria:** Fokus pada pasar, perbankan, industri, perusahaan, investasi, atau dampak ekonomi.

**Pembeda:** Kasus bisnis berlabel korupsi atau peradilan tetap perlu dipilah menurut pusat persoalan, bukan nama perusahaan saja.

**Contoh dataset:** `TMP-FD83C3FCCF0D` — PANSUS CENTURY: SIAPA JADI KORBAN

Dataset memberi label economy_business_and_state_enterprise pada sampul ini. Headline dan teks pendukung dapat dibaca sebagai konteks isu; tidak tersedia alasan anotasi Task 1 yang terpisah. Kecocokan dengan definisi merupakan usulan operasional, bukan rekonstruksi keputusan anotator.

### Kebijakan Publik, Kesehatan & Bencana (`public_policy_health_and_disaster`)

**Definisi:** Kebijakan layanan publik, kesehatan, dan penanganan bencana beserta dampaknya pada masyarakat.

**Kriteria:** Fokus pada pelayanan, regulasi publik, masalah kesehatan, atau respons terhadap bencana.

**Pembeda:** Bencana sebagai metafora masuk Task 2; kategori ini membahas isu aktual, bukan bentuk visual.

**Contoh dataset:** `TMP-015F9748262A` — JARINGAN MAKELAR CANGKOK GINJAL

Dataset memberi label public_policy_health_and_disaster pada sampul ini. Headline dan teks pendukung dapat dibaca sebagai konteks isu; tidak tersedia alasan anotasi Task 1 yang terpisah. Kecocokan dengan definisi merupakan usulan operasional, bukan rekonstruksi keputusan anotator.

### Hukum & Peradilan (`law_and_justice`)

**Definisi:** Penegakan hukum, proses peradilan, putusan, dan pencarian keadilan.

**Kriteria:** Penyelidikan, persidangan, putusan, aturan hukum, atau perlakuan hukum menjadi isu dominan.

**Pembeda:** Korupsi sebagai perbuatan masuk corruption_and_bribery jika proses hukumnya bukan fokus utama.

**Contoh dataset:** `TMP-8D0A20A6A066` — AKBAR TERPOJOK SIAPA SENANG

Dataset memberi label law_and_justice pada sampul ini. Headline dan teks pendukung dapat dibaca sebagai konteks isu; tidak tersedia alasan anotasi Task 1 yang terpisah. Kecocokan dengan definisi merupakan usulan operasional, bukan rekonstruksi keputusan anotator.

### Hak Asasi & Konflik Sosial (`human_rights_and_social_conflict`)

**Definisi:** Hak warga, kebebasan, diskriminasi, dan konflik antarkelompok dalam masyarakat.

**Kriteria:** Fokus pada pelanggaran hak, pembungkaman, kebebasan sipil, kekerasan sosial, atau konflik komunitas.

**Pembeda:** Ancaman pertahanan/terorisme lebih dekat dengan security_defense_and_terrorism jika aspek keamanan menjadi pokok utama.

**Contoh dataset:** `TMP-BB220780A305` — AWAS TEROR DIGITAL

Dataset memberi label human_rights_and_social_conflict pada sampul ini. Headline dan teks pendukung dapat dibaca sebagai konteks isu; tidak tersedia alasan anotasi Task 1 yang terpisah. Kecocokan dengan definisi merupakan usulan operasional, bukan rekonstruksi keputusan anotator.

### Lingkungan & Sumber Daya Alam (`environment_and_natural_resources`)

**Definisi:** Kondisi lingkungan serta pemanfaatan dan penguasaan sumber daya alam.

**Kriteria:** Hutan, lahan, tambang, air, pencemaran, konservasi, atau kerusakan ekologis menjadi pusat isu.

**Pembeda:** Konteks lingkungan saja tidak cukup bila pokok sampul adalah korupsi atau konflik hukum.

**Contoh dataset:** `TMP-4650B47F4E32` — PENGGEDE DI HULU CISADANE

Dataset memberi label environment_and_natural_resources pada sampul ini. Headline dan teks pendukung dapat dibaca sebagai konteks isu; tidak tersedia alasan anotasi Task 1 yang terpisah. Kecocokan dengan definisi merupakan usulan operasional, bukan rekonstruksi keputusan anotator.

### Keamanan, Pertahanan & Terorisme (`security_defense_and_terrorism`)

**Definisi:** Keamanan, pertahanan negara, militer, dan ancaman terorisme.

**Kriteria:** Fokus pada operasi keamanan, pertahanan, angkatan bersenjata, atau terorisme.

**Pembeda:** Kebebasan sipil dan konflik komunitas lebih dekat dengan human_rights_and_social_conflict jika itulah pusat pembahasan.

**Contoh dataset:** `TMP-E2A77C58A55A` — SOEDIRMAN: SEORANG PANGLIMA, SEORANG MARTIR

Dataset memberi label security_defense_and_terrorism pada sampul ini. Headline dan teks pendukung dapat dibaca sebagai konteks isu; tidak tersedia alasan anotasi Task 1 yang terpisah. Kecocokan dengan definisi merupakan usulan operasional, bukan rekonstruksi keputusan anotator.

### Isu Lainnya (`other_issue`)

**Definisi:** Isu utama yang belum tercakup oleh sembilan kategori isu lainnya.

**Kriteria:** Gunakan setelah memeriksa seluruh kategori isu, misalnya profil sejarah atau edisi khusus yang tidak cocok.

**Pembeda:** Kategori residual ini bukan pengganti keputusan ketika informasi belum cukup; catat ketidakpastian secara terpisah.

**Contoh dataset:** `TMP-ED5D7EE892F5` — MUHAMMAD YAMIN 1903-1962

Dataset memberi label other_issue pada sampul ini. Headline dan teks pendukung dapat dibaca sebagai konteks isu; tidak tersedia alasan anotasi Task 1 yang terpisah. Kecocokan dengan definisi merupakan usulan operasional, bukan rekonstruksi keputusan anotator.

## Domain Sumber Metafora

### Mesin & Infrastruktur (`MESIN_INFRASTRUKTUR`)

**Definisi:** Domain sumber berupa mesin, alat kerja, kendaraan, bangunan, infrastruktur, atau mekanisme buatan.

**Kriteria:** Ada pemetaan dari fungsi, kerusakan, pengendalian, atau kerja alat/struktur ke isu sasaran.

**Pembeda:** Alat yang tampil literal tidak otomatis metafora; alat transaksi/permainan dipilah menurut mekanisme pemetaan dominan.

**Contoh dataset:** `TMP-EC1AFE264B60` — CERITA DARI KAMPUNG NARKOBA

Catatan anotator menyebut sumber: Karet penghapus (setip) menghapus kata NARKOBA pada permukaan sampul. Pemetaan yang dicatat: Penghapusan kata memetakan upaya pengaburan, penutupan, atau penghilangan jejak peredaran narkoba dan keterlibatan oknum aparat. Hubungan ini diusulkan sebagai contoh kriteria kelas; belum diperiksa ulang pada gambar.

### Permainan & Kontes (`PERMAINAN_KONTES`)

**Definisi:** Domain sumber berupa permainan, pertandingan, kompetisi, atau panggung pertunjukan sebagai arena berstrategi.

**Kriteria:** Pemetaan memakai menang-kalah, aturan main, pemain, peran, panggung, atau pengaturan pertunjukan.

**Pembeda:** Persaingan politik literal adalah isu Task 1; Task 2 memerlukan sumber metaforis. Cakupan pertunjukan mengikuti contoh anotasi opera sabun.

**Contoh dataset:** `TMP-78163D7E671E` — OPERA SABUN KOCOK KABINET

Catatan anotator menyebut sumber: Opera sabun dan panggung pertunjukan. Pemetaan yang dicatat: Perombakan kabinet digambarkan sebagai drama politik yang diatur oleh pemimpin.. Hubungan ini diusulkan sebagai contoh kriteria kelas; belum diperiksa ulang pada gambar.

### Bencana & Jerat (`BENCANA_JERAT`)

**Definisi:** Domain sumber berupa bencana, ancaman, jerat, perangkap, atau keadaan fisik terjepit.

**Kriteria:** Pemetaan memakai bahaya, kehancuran, terperangkap, atau tekanan ruang sebagai sumber makna.

**Pembeda:** Bencana aktual tanpa pemetaan dapat NON_METAFORA; bagian tubuh dalam jerat dipilah menurut mekanisme dominan.

**Contoh dataset:** `TMP-8D0A20A6A066` — AKBAR TERPOJOK SIAPA SENANG

Catatan anotator menyebut sumber: Sudut ruang dan posisi fisik terjepit. Pemetaan yang dicatat: Posisi di sudut menggambarkan tekanan politik dan hukum yang menyudutkan Akbar.. Hubungan ini diusulkan sebagai contoh kriteria kelas; belum diperiksa ulang pada gambar.

### Hewan & Tubuh (`HEWAN_TUBUH`)

**Definisi:** Domain sumber berupa hewan, bagian tubuh, atau bentuk dan perilaku biologis.

**Kriteria:** Sifat hewan, anatomi, deformasi, atau perilaku tubuh dipetakan ke tokoh atau persoalan.

**Pembeda:** Potret manusia atau hewan literal tidak cukup; unsur konsumsi dapat tumpang tindih dan perlu dicatat.

**Contoh dataset:** `TMP-DB65F6B7A1E4` — SKANDAL BNI, SIAPA MENIKMATI?

Catatan anotator menyebut sumber: Tikus yang berpesta dan mengais makanan atau dokumen. Pemetaan yang dicatat: Pihak yang menikmati korupsi digambarkan sebagai tikus yang berpesta dari skandal BNI.. Hubungan ini diusulkan sebagai contoh kriteria kelas; belum diperiksa ulang pada gambar.

### Konsumsi & Transaksi (`KONSUMSI_TRANSAKSI`)

**Definisi:** Domain sumber berupa makanan, jamuan, selera, jual-beli, pembayaran, atau pertukaran keuntungan.

**Kriteria:** Ada pemetaan dari makan, memilih hidangan, berbagi jatah, atau pertukaran nilai ke persoalan sasaran.

**Pembeda:** Makanan atau uang literal tidak otomatis metafora; jika hewan merupakan sumber utama, pertimbangkan HEWAN_TUBUH.

**Contoh dataset:** `TMP-BB454CBBB59B` — KAPOLRI SELERA CIKEAS

Catatan anotator menyebut sumber: Pilihan menu makanan atau hidangan selera restoran pribadi. Pemetaan yang dicatat: Selera kuliner pribadi memetakan penunjukan pejabat tinggi penegak hukum berdasarkan kenyamanan dan loyalitas politik penguasa. Hubungan ini diusulkan sebagai contoh kriteria kelas; belum diperiksa ulang pada gambar.

### Tanpa Metafora (`NON_METAFORA`)

**Definisi:** Sampul tanpa pemetaan metaforis visual-verbal yang teridentifikasi pada anotasi.

**Kriteria:** Elemen dipahami secara literal dan tidak ditemukan hubungan sumber-sasaran metaforis yang cukup.

**Pembeda:** Ketidakpastian pembaca bukan bukti tanpa metafora; kasus ambigu perlu dicatat dan ditinjau.

**Contoh dataset:** `TMP-4650B47F4E32` — PENGGEDE DI HULU CISADANE

Label dataset adalah NON_METAFORA dan catatan sumber serta pemetaan kosong. Ini contoh label yang tersedia, bukan bukti mandiri bahwa semua elemen sampul literal.

### Lainnya (`LAINNYA`)

**Definisi:** Domain sumber metafora yang tidak tercakup oleh lima domain positif lainnya.

**Kriteria:** Metafora teridentifikasi tetapi mekanisme sumbernya tidak cocok dengan kategori domain yang tersedia.

**Pembeda:** Bedakan dari NON_METAFORA: LAINNYA tetap memiliki pemetaan metaforis; hindari sebagai tempat semua kasus ambigu.

**Contoh dataset:** `TMP-FD83C3FCCF0D` — PANSUS CENTURY: SIAPA JADI KORBAN

Catatan anotator menyebut sumber: Korban persembahan dan pengadilan simbolis. Pemetaan yang dicatat: Penyelidikan politik digambarkan sebagai proses mencari korban atau kambing hitam.. Hubungan ini diusulkan sebagai contoh kriteria kelas; belum diperiksa ulang pada gambar.

## Sasaran Kritik

### Perorangan (`individual`)

**Definisi:** Satu orang yang menjadi entitas sasaran utama.

**Kriteria:** Anotasi sasaran mengutamakan seorang tokoh tertentu.

**Pembeda:** Tokoh yang mewakili lembaga tidak otomatis individual; ikuti sasaran yang dimaksud, bukan hanya wajah pada sampul.

**Contoh dataset:** `TMP-8D0A20A6A066` — AKBAR TERPOJOK SIAPA SENANG

Anotasi sasaran menyebut “Akbar Tanjung” dan label dataset individual. Alasan usulan: jenis sasaran tersebut dibaca mengikuti kriteria di atas. Pengelompokan tetap mengikuti label dataset, bukan kesimpulan dari headline saja.

### Pemerintah (`government`)

**Definisi:** Pemerintah eksekutif, kabinet, kementerian, atau administrasi pemerintahan sebagai sasaran.

**Kriteria:** Sasaran utama berupa lembaga/proses eksekutif atau kelompok pejabat dalam kapasitas pemerintahan.

**Pembeda:** Pisahkan dari seorang tokoh pribadi, legislatif, dan aparat hukum menurut fungsi sasaran.

**Contoh dataset:** `TMP-78163D7E671E` — OPERA SABUN KOCOK KABINET

Anotasi sasaran menyebut “Kabinet Indonesia Bersatu dan Presiden Susilo Bambang Yudhoyono” dan label dataset government. Alasan usulan: jenis sasaran tersebut dibaca mengikuti kriteria di atas. Pengelompokan tetap mengikuti label dataset, bukan kesimpulan dari headline saja.

### Beberapa Pihak / Lainnya (`multiple_or_other`)

**Definisi:** Beberapa sasaran lintas tipe atau sasaran yang tidak cocok dengan tujuh tipe lainnya.

**Kriteria:** Anotasi menyebut campuran entitas tanpa satu tipe dominan, atau entitas di luar kategori tersedia.

**Pembeda:** Banyak orang dalam satu lembaga tidak selalu kategori ini; tentukan apakah lembaga itu merupakan sasaran tunggal.

**Contoh dataset:** `TMP-DB65F6B7A1E4` — SKANDAL BNI, SIAPA MENIKMATI?

Anotasi sasaran menyebut “Bank Negara Indonesia dan pelaku skandal BNI” dan label dataset multiple_or_other. Alasan usulan: jenis sasaran tersebut dibaca mengikuti kriteria di atas. Pengelompokan tetap mengikuti label dataset, bukan kesimpulan dari headline saja.

### Masyarakat Sipil & Media (`civil_society_or_media`)

**Definisi:** Organisasi masyarakat sipil, komunitas, kelompok warga, atau media sebagai sasaran.

**Kriteria:** Sasaran utama adalah organisasi sosial, kelompok masyarakat, organisasi nonpemerintah, atau lembaga media.

**Pembeda:** Perusahaan komersial masuk business bila kapasitas usaha dominan; orang tertentu dapat individual.

**Contoh dataset:** `TMP-1A5862984B3D` — KANTONG BOCOR DANA UMAT

Anotasi sasaran menyebut “Aksi Cepat Tanggap (ACT)” dan label dataset civil_society_or_media. Alasan usulan: jenis sasaran tersebut dibaca mengikuti kriteria di atas. Pengelompokan tetap mengikuti label dataset, bukan kesimpulan dari headline saja.

### Pelaku Usaha (`business`)

**Definisi:** Perusahaan, koperasi, atau pelaku usaha dalam kapasitas bisnis sebagai sasaran.

**Kriteria:** Sasaran berpusat pada badan usaha atau aktivitas usaha.

**Pembeda:** BUMN dapat business jika disorot sebagai badan usaha; pemerintah sebagai pembuat kebijakan tetap government.

**Contoh dataset:** `TMP-A0B2109BF3D7` — BOLONG-BOLONG INDOSURYA

Anotasi sasaran menyebut “Koperasi Simpan Pinjam Indosurya dan Henry Surya” dan label dataset business. Alasan usulan: jenis sasaran tersebut dibaca mengikuti kriteria di atas. Pengelompokan tetap mengikuti label dataset, bukan kesimpulan dari headline saja.

### Peradilan & Penegak Hukum (`judiciary_or_law_enforcement`)

**Definisi:** Lembaga peradilan dan penegakan hukum sebagai sasaran.

**Kriteria:** Pengadilan, hakim dalam fungsi lembaga, kepolisian, kejaksaan, atau aparat hukum menjadi sasaran utama.

**Pembeda:** Tokoh aparat sebagai pribadi dapat individual; lembaga eksekutif lain masuk government.

**Contoh dataset:** `TMP-EC1AFE264B60` — CERITA DARI KAMPUNG NARKOBA

Anotasi sasaran menyebut “Aparat penegak hukum dan jaringan narkotika Kampung Ambon” dan label dataset judiciary_or_law_enforcement. Alasan usulan: jenis sasaran tersebut dibaca mengikuti kriteria di atas. Pengelompokan tetap mengikuti label dataset, bukan kesimpulan dari headline saja.

### Partai Politik (`political_party`)

**Definisi:** Partai atau organisasi dan aktor yang disorot dalam kapasitas kepartaian.

**Kriteria:** Sasaran utama adalah partai, koalisi, atau persaingan aktor yang diposisikan sebagai kekuatan politik.

**Pembeda:** Kandidat bernama tidak otomatis partai; contoh dataset mengandung perluasan aktor elektoral sehingga batas ini perlu diterapkan hati-hati.

**Contoh dataset:** `TMP-9145AA2669BC` — PILKADA SERASA PILPRES

Anotasi sasaran menyebut “Kandidat pilkada dan kandidat pemilihan presiden” dan label dataset political_party. Alasan usulan: jenis sasaran tersebut dibaca mengikuti kriteria di atas. Pengelompokan tetap mengikuti label dataset, bukan kesimpulan dari headline saja.

### Lembaga Legislatif (`legislature`)

**Definisi:** Lembaga legislatif, parlemen, atau alat kelengkapannya sebagai sasaran.

**Kriteria:** DPR, komisi, pansus, atau fungsi legislasi/pengawasan parlemen menjadi sasaran utama.

**Pembeda:** Seorang legislator sebagai pribadi dapat individual; partainya sebagai organisasi dapat political_party.

**Contoh dataset:** `TMP-FD83C3FCCF0D` — PANSUS CENTURY: SIAPA JADI KORBAN

Anotasi sasaran menyebut “Panitia Khusus Hak Angket Bank Century DPR RI” dan label dataset legislature. Alasan usulan: jenis sasaran tersebut dibaca mengikuti kriteria di atas. Pengelompokan tetap mengikuti label dataset, bukan kesimpulan dari headline saja.

## Verifikasi dan batas penggunaan

25 label sudah dicocokkan dengan daftar tampilan dan masing-masing contoh telah ditemukan dengan label yang sama di CSV. Contoh bukan hasil evaluasi prediksi. Perbedaan antara rumusan baru dan anotasi lama perlu dicatat sebagai temuan, bukan diatasi dengan mengubah label secara diam-diam.

Sumber data: `DEMO_XAI_745_FULL/03_data/DATASET_740_TASK2_DOMAIN.csv`. Pemetaan tampilan: `DEMO_XAI_745_FULL/02_web_demo/label_display.py`. Versi mesin: `DEMO_XAI_745_FULL/02_web_demo/codebook_operasional.json`.
