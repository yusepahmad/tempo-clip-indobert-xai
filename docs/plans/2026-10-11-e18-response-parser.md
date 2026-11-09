# E18 parsing jawaban eksplisit tanpa target

**Tanggal:** 2026-10-11
**Status:** done

## Tujuan
Membedakan kegagalan format satu karakter dari jawaban kategori eksplisit di respons hosted. Menilai parser yang dibekukan sebelum membaca label kualitas, mempertahankan evaluasi strict E18.

## Ruang Lingkup
- `DEMO_XAI_745_FULL/01_notebook/e18_hosted/parse.py` dan `evaluate_parsed.py`, output baru `04_hasil_eksperimen/e18_hosted/parsed/`, recovery dan changelog.
- Worker/prompt/model/request E18 dan auditor strict tidak diubah; label/data asli tetap. Tidak ada request API tambahan.

## Langkah
1. Bekukan aturan label-blind: kode tunggal (opsional markdown/tanda titik), baris akhir dengan awalan persis `Jawab satu kode A sampai G:` diikuti kode tunggal (opsional markdown/titik), atau kode diikuti nama kelas yang cocok dengan codebook. Selain itu INVALID. Jangan ekstrak kode dari alasan bebas.
2. Uji ambiguity/rejection tanpa target, kompilasi dan hash salinan server. Format dari tiga respons INVALID awal hanya dipakai untuk perbaikan parsing; label target/skor belum dibaca.
3. Evaluasi turunan hanya setelah audit strict740 verified, hash seluruh740 cache masih cocok. Parse ulang semua respons, catat aturan perID/strict-versus-parsed, simpan output terpisah. Tidak memilih parser setelah membaca skor.
4. Hitung tujuh kelas secara manual termasuk INVALID sebagai salah, cocokkan sklearn, ID/fold dan laporkan skor strict serta parsed secara terpisah. Simpan hash parser dan evidence.

## Risiko & Asumsi
- Parser bukan peningkatan model; perubahan skor harus dinyatakan sebagai efek parsing.
- Kata kategori/kode dalam alasan dapat menjadi contoh, sehingga hanya format final eksplisit yang diterima. Label yang ambigu atau tak dikenal tetap salah.

## Verifikasi
Uji penerimaan kode/markdown/awalan final dan penolakan beberapa kode, pertanyaan, label mismatch serta alasan tanpa final. Gate incomplete740 wajib menolak. Keluaran strict tidak diubah,740hash evidence sama, manualF1 dan sklearn cocok.

## Koordinasi audit setelah worker terminal
Tambahkan `watch.py` di folder E18 untuk memantau PID/starttime worker1176994 secara read-only setiap45detik. Setelah proses asli terminal dan progress predictions_complete_pending_audit740, jalankan auditor strict lalu parsed sekali. Fcntl/state/hash source mencegah duplikasi; error/hasil parsial berhenti tanpa request/training ulang. Root tetap harus memeriksa bukti, salinan hash dan F1 sebelum klaim.

## Hasil persiapan
12 kasus parser tanpa target lolos; kompilasi lolos. Parser SHA256 `b09c360de8d768ad428bccbb7be55615f7bce38e21fe2bcd4a31a45da7bfc9a2`, evaluator parsed `aa995b726f529feaec35dc847f02670e87362fd7920d611636cebabd75f1acdc`. Evaluasi kualitas menunggu strict740 verified.

Watcher terpasang dengan worker1176994/starttime205000293, tmux `tempo-e18-audit`, phase watching. Hash watcher `7ef3a6cd2020e866e8703948cb12db3206f76f6a056062db2492fd5a579a6c2a`; sumber parser/evaluator cocok server. Gate parsed menolak keluaran tanpa verification strict dan tidak membuat output parsed. Belum ada hasil kualitas parser.
