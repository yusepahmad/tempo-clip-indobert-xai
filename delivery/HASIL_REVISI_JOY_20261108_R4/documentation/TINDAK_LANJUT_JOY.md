# Tindakan yang masih perlu diselesaikan Joy

| revision_id | title | remaining | owner |
| --- | --- | --- | --- |
| R21 | Kesetaraan masukan dan Qwen zero-shot | Hasil belum lengkap: RII_QWEN_QLORA_HEADLINE_ONLY. Arm basic sebelumnya memuat supporting text sehingga bukan citra+judul literal yang diminta PDF. | Eksperimen GPU/collector |
| R22 | Provenance fitur E01 | Generator/hash/prompt tersedia; tuntutan isolasi proses historis dan timestamp penciptaan asli belum dapat dibuktikan. | Peneliti/pembimbing: terima bukti field-flow atau minta regenerasi fitur versi baru |
| R23 | Agreement manusia dan riwayat korpus | Alasan umum eksklusi sudah diklarifikasi Joy: kualitas citra buruk sehingga tidak dapat dilabeli, dan menurut Joy pernah disampaikan. Yang belum tersedia: dua set anotasi independen untuk kappa; dokumentasi korpus awal/keputusan per ID dan sensitivitas belum dapat direkonstruksi. | Dua anotator; pemilik data untuk dokumentasi rinci bila tersedia |
| R31 | Kelas penampung dan dekomposisi Task 2 | Tabel/codebook/sensitivitas selesai; audit manusia60 sampul dan adjudikasi codebook belum diisi. | Joy/anotator |
| R32 | Reproduksi mandiri dan Colab bersih | Paket dan uji lokal disediakan; bukti Run all Colab bersih belum terverifikasi. | Uji Colab melalui akun pengguna |
| R34 | XAI dan penilai independen | XAI aktual/tes/model replay/rubrik/kontrol tersedia; skor nyata minimal5 penilai independen dan agreement belum tersedia. | Joy/lima penilai independen |
| R6 | Adjudikasi dan eksklusi | Alasan umum eksklusi sudah diklarifikasi Joy: kualitas citra buruk sehingga tidak dapat dilabeli, dan menurut Joy pernah disampaikan. Yang belum tersedia: dua set anotasi independen untuk kappa; dokumentasi korpus awal/keputusan per ID dan sensitivitas belum dapat direkonstruksi. | Dua anotator; pemilik data untuk dokumentasi rinci bila tersedia |
| R8 | Baseline dan ablasi | Ablasi/prediksi tersedia; wording lengkap dokumen Agustus asli belum ditemukan, jadi penutupan R8 lama belum dapat dipastikan. | Joy/pembimbing: dokumenAgustus |
| R9 | Lima penilai independen | XAI aktual/tes/model replay/rubrik/kontrol tersedia; skor nyata minimal5 penilai independen dan agreement belum tersedia. | Joy/lima penilai independen |

Anotasi/penilaian belum dilakukan oleh manusia tidak boleh diganti keluaran AI. Gunakan paket terpisah untuk anotator/penilai; jangan kirim kunci privat koordinator ke penilai. Untuk metadata sumber yang tidak tersedia, konfirmasi ke pemilik data/pembimbing dengan bukti spesifik; jangan mengarang alasan eksklusi.
