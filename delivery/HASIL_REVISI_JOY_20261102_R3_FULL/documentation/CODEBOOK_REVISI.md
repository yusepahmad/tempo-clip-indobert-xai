# Codebook operasional dan adjudikasi

Label canonical tetap. Tidak ada relabeling otomatis berdasarkan kesalahan model. Definisi tiga task dan daftar label bersumber dari source/protokol yang disertakan. Task 1: isu utama paling dominan; Task 2: domain sumber pemetaan metaforis, berbeda dari isu sasaran; Task 3: tipe entitas yang menjadi fokus kritik, bukan setiap objek yang tampak.

Kelas penampung harus dipakai dengan alasan tertulis. `other_issue`: isu dapat diidentifikasi tetapi berada di luar sembilan kategori utama. `LAINNYA`: ada pemetaan metaforis yang dapat dijelaskan, tetapi sumber tidak termasuk lima domain positif; jangan dipakai hanya karena penilai ragu. `NON_METAFORA`: tidak ditemukan pemetaan sumber–sasaran yang dapat dipertanggungjawabkan; berbeda dari metafora yang sumbernya di luar taxonomy. `multiple_or_other`: catat terpisah alasan “beberapa sasaran dominan” atau “tipe tidak tercakup”, bukan menyatukan semua ketidakpastian.

Prosedur: dua anotator menilai independen, menyimpan label/tingkat keyakinan/alasan; kappa dihitung sebelum diskusi; adjudikator menulis keputusan dan alasan di file baru. Sampel sengketa tidak dihapus hanya untuk menaikkan metrik. Pemecahan kelas memerlukan dataset/codebook versi baru dan tabel pemetaan; hasil lama tetap dipertahankan.

Audit 60 contoh disiapkan untuk memastikan apakah ada subgroup koheren. Belum ada keputusan manusia yang dapat dijadikan dasar perubahan gold. Template anotasi150 tidak memuat gold/model prediction. Daftar kategori yang diperbolehkan ada di protocol.json.

Definisi seluruh label sesuai taxonomy yang dipakai, tanpa perubahan gold:

### task1_issue

| label | definition |
| --- | --- |
| corruption_and_bribery | korupsi, suap, gratifikasi, atau penyalahgunaan dana dan jabatan |
| economy_business_and_state_enterprise | ekonomi, bisnis, keuangan, perusahaan, BUMN, pajak, atau perdagangan |
| election_and_political_competition | pemilu, pilkada, kampanye, koalisi, kandidat, atau kompetisi politik |
| environment_and_natural_resources | lingkungan, energi, tambang, hutan, lahan, air, atau sumber daya alam |
| human_rights_and_social_conflict | hak asasi, diskriminasi, kekerasan sosial, buruh, agama, atau konflik masyarakat |
| law_and_justice | hukum, pengadilan, polisi, kejaksaan, penyidikan, atau keadilan |
| other_issue | isu utama di luar sembilan kategori lain |
| power_and_governance | kekuasaan, pemerintahan, kabinet, birokrasi, kebijakan, atau kepemimpinan |
| public_policy_health_and_disaster | kesehatan, pendidikan, layanan publik, bencana, pandemi, atau kebijakan sosial |
| security_defense_and_terrorism | militer, pertahanan, keamanan nasional, intelijen, terorisme, atau perang |

### task2_domain_sumber

| label | definition |
| --- | --- |
| BENCANA_JERAT | ancaman, bencana, perangkap, jerat, tekanan, atau keadaan terjepit sebagai kiasan |
| HEWAN_TUBUH | hewan, anatomi, penyakit, deformasi, atau perilaku biologis sebagai kiasan |
| KONSUMSI_TRANSAKSI | makanan, jamuan, selera, jual-beli, uang, atau pertukaran nilai sebagai kiasan |
| LAINNYA | metafora dengan domain sumber selain lima domain metaforis yang disebut |
| MESIN_INFRASTRUKTUR | mesin, alat, kendaraan, bangunan, wadah, atau mekanisme buatan sebagai kiasan |
| NON_METAFORA | adegan literal tanpa pemetaan metaforis |
| PERMAINAN_KONTES | permainan, pertandingan, kompetisi, pertunjukan, atau seni sebagai kiasan |

### task3_primary_entity_type

| label | definition |
| --- | --- |
| business | perusahaan swasta, pengusaha, atau organisasi bisnis |
| civil_society_or_media | warga, aktivis, organisasi sipil, media, jurnalis, atau kelompok masyarakat |
| government | pemerintah, presiden sebagai institusi eksekutif, menteri, kabinet, birokrasi, atau lembaga negara umum |
| individual | satu orang tertentu sebagai sasaran utama |
| judiciary_or_law_enforcement | polisi, jaksa, hakim, pengadilan, KPK, atau lembaga penegak hukum |
| legislature | DPR, parlemen, legislator, atau lembaga legislatif |
| multiple_or_other | beberapa tipe sasaran sekaligus atau sasaran yang tidak termasuk kategori lain |
| political_party | partai politik atau organisasi politik partisan |

Jika beberapa isu/sasaran sama dominannya, anotator menuliskan pilihan dan alasan untuk adjudikasi; jangan menyamakan ketidakpastian dengan NON_METAFORA atau membuang kasus sengketa. Bedakan kritik orang tertentu (`individual`) dari institusi eksekutif (`government`) berdasarkan fokus kritik, bukan semata-mata ada gambar manusia.

Definisi sumber Task 2 yang digunakan pada generator historis (sebagai bukti prompt, bukan hasil adjudikasi baru):

```text
Ini sampul Majalah Tempo.
Judul utama: {judul}
Teks pendukung: {pendukung}

Tentukan domain sumber metafora visual-verbal sampul ini, yaitu dari ranah apa kiasan gambarnya diambil (bukan isu yang dibahas). Pilih tepat satu kode:
MESIN_INFRASTRUKTUR: Domain sumber berupa mesin, alat kerja, kendaraan, bangunan, infrastruktur, atau mekanisme buatan. Kriteria: ada pemetaan dari fungsi, kerusakan, pengendalian, atau kerja alat/struktur ke isu sasaran. Pembeda: alat yang tampil literal tidak otomatis metafora; alat transaksi/permainan dipilah menurut mekanisme pemetaan dominan.
PERMAINAN_KONTES: Domain sumber berupa permainan, pertandingan, kompetisi, atau panggung pertunjukan sebagai arena berstrategi. Kriteria: pemetaan memakai menang-kalah, aturan main, pemain, peran, panggung, atau pengaturan pertunjukan. Pembeda: persaingan politik literal bukan metafora; perlu sumber metaforis.
BENCANA_JERAT: Domain sumber berupa bencana, ancaman, jerat, perangkap, atau keadaan fisik terjepit. Kriteria: pemetaan memakai bahaya, kehancuran, terperangkap, atau tekanan ruang sebagai sumber makna. Pembeda: bencana aktual tanpa pemetaan dapat NON_METAFORA; bagian tubuh dalam jerat dipilah menurut mekanisme dominan.
HEWAN_TUBUH: Domain sumber berupa hewan, bagian tubuh, atau bentuk dan perilaku biologis. Kriteria: sifat hewan, anatomi, deformasi, atau perilaku tubuh dipetakan ke tokoh atau persoalan. Pembeda: potret manusia atau hewan literal tidak cukup; jika konsumsi tumpang tindih, pilih mekanisme dominan.
KONSUMSI_TRANSAKSI: Domain sumber berupa makanan, jamuan, selera, jual-beli, pembayaran, atau pertukaran keuntungan. Kriteria: ada pemetaan dari makan, memilih hidangan, berbagi jatah, atau pertukaran nilai ke persoalan sasaran. Pembeda: makanan atau uang literal tidak otomatis metafora; jika hewan merupakan sumber utama, pertimbangkan HEWAN_TUBUH.
NON_METAFORA: Sampul tanpa pemetaan metaforis visual-verbal. Kriteria: elemen dipahami secara literal dan tidak ada hubungan sumber-sasaran metaforis yang cukup. Pembeda: ketidakpastian pembaca bukan bukti tanpa metafora.
LAINNYA: Domain sumber metafora yang tidak tercakup lima domain positif lainnya. Kriteria: metafora teridentifikasi tetapi mekanisme sumbernya tidak cocok dengan kategori yang tersedia. Pembeda: berbeda dari NON_METAFORA karena tetap ada pemetaan metaforis; jangan dipakai sebagai tempat semua kasus ambigu.

Jawab hanya dengan JSON satu baris: {"sumber_visual": "<benda/adegan yang menjadi sumber kiasan>", "domain": "<KODE>", "alasan": "<satu kalimat>"}
```
