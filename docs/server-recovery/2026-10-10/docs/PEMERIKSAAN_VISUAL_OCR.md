# Pemeriksaan visual kasus OCR

> **Dokumen riwayat per 5 Oktober 2026.** Status terbaru: [STATUS_REVISI_20261006.md](STATUS_REVISI_20261006.md) (6 Oktober 2026). Usulan transkripsi di bawah tetap usulan agen, bukan ground truth tervalidasi (T04 masih sebagian). Evaluasi OCR terbaru (urutan baca berbasis tata letak, filter sampah teks baku, angka validasi) ada di [AUDIT_OCR_URUTAN_20261006.md](AUDIT_OCR_URUTAN_20261006.md).

Tanggal: 2026-10-05. Sebelas gambar korpus diperiksa langsung oleh agen. Ini usulan transkripsi untuk review, bukan validasi manusia atau perubahan anotasi. Dataset dan angka evaluasi lama tetap. Kolom kosong berarti tidak ada teks pendukung utama yang diusulkan; judul artikel sekunder dikecualikan.

| ID | Usulan headline | Usulan teks pendukung | Catatan |
|---|---|---|---|
| TMP-C0470EF4F455 | BANDAR ANGGARAN | Belasan anggotanya terindikasi melakukan transaksi keuangan mencurigakan. | Banggar merupakan tulisan ilustrasi; referensi dataset memasukkannya. |
| TMP-1EF49983B649 | PERANG BUBAT DI TANAH JAWA |  | OCR melewatkan baris DI TANAH JAWA. |
| TMP-77A5A0AE79DA | BUNG TOMO | Soerabaja di Tahun 45 | Referensi dataset menggabungkan judul dan subjudul. |
| TMP-67D344FE05F8 | KIPI SATU HOAKS SERIBU | Pemerintah gamang menangani kejadian ikutan pasca-imunisasi. Perlu aturan jelas dan penanganan transparan untuk mencegah kampanye anti-vaksin Covid-19. | Huruf bagan pemeriksaan mata ikut dipilih OCR. |
| TMP-C6F070C953D9 | JUNGKIR BALIK ‘RAJA JAWA’ |  | Judul RAJA JAWA terlewat; duplikat terbalik tidak perlu digabung. |
| TMP-167D0CCDCB75 | MAKAR | POLISI MEMATAHKAN RENCANA SEGELINTIR ORANG MENUNGGANGI AKSI 212. KUDETA SERIUS ATAU ASAL-ASALAN? | Artefak logo STEMPO ikut dipilih. |
| TMP-0875C1C0AF91 | ATAS NAMA BANGSA AMERIKA | Selain membayar tarif tambahan, Indonesia wajib mencabut hambatan dagang bagi produk Amerika Serikat. Benarkah Prabowo mengabaikan rekomendasi tim perunding saat bernegosiasi dengan Trump? | NAMA dibaca NANA. |
| TMP-92F172188EAB | KISRUH IMPOR BERAS | KEPUTUSAN PEMERINTAH MEMBUKA KERAN IMPOR BERAS JADI PRO-KONTRA. TERSEBAB DATA YANG SIMPANG-SIUR. | IMPOR sebagian tertutup ilustrasi. |
| TMP-D60E7B54C360 | TERORIS DI PELUPUK MATA | PENUSUKAN WIRANTO DISIAPKAN SEHARI SEBELUM KEJADIAN. MENGGUNAKAN METODE INGHIMASI—SERANGAN MENDADAK, CEPAT, DAN MEMATIKAN DENGAN MEMAKAI SENJATA RINGAN. | Kesalahan huruf dan spasi DI PELUPUK. |
| TMP-758796F60BC6 | TIM MAWAR DAN RUSUH SARINAH | Polisi menengarai keterlibatan penculik aktivis 1998 dalam huru-hara 22 Mei lalu. Kesaksian pelaku lapangan. | Teks pendukung dibedakan dari headline. |
| TMP-579182AE35FE | AMBYAR… | JENDERAL POLISI AKTIF MULAI BERTUGAS SEBAGAI KETUA KOMISI PEMBERANTASAN KORUPSI. INILAH AKHIR KISAH CICAK VERSUS BUAYA. | Ringkasan bertingkat dalam ilustrasi berbeda dari headline. |
