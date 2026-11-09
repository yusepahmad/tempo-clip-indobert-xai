# Audit masa berlaku akses Kaggle

**Tanggal:** 2026-10-11
**Status:** done

## Tujuan
Memperbaiki penjaga akses yang menganggap respons auth dengan expiry sama sebagai perpanjangan, tanpa mengulang request model.

## Ruang Lingkup
- `DEMO_XAI_745_FULL/01_notebook/e18_hosted/refresh_access.py`, proses penjaga akses, plan/changelog.
- Bila guard benar-benar menghentikan worker: bukti cache parsial dan arsip state/log pemantau, perolehan akses resmi baru dan kelanjutan worker/source yang sama hanya untuk ID belum diminta; pemasangan ulang pemantau berdasarkan PID/starttime baru.
- Worker1176994, watcher audit, parser, dataset dan hasil tetap. Tidak mencetak key atau memakai provider berbayar lain.

## Langkah
1. Catat bukti endpoint auth resmi mengembalikan expiry sama; SDK request kosong dan hanya method create_default_model_proxy_token tersedia.
2. Hentikan hanya penjaga akses lama; pastikan terminal/lock bebas. Perbaiki penghitung agar hanya expiry yang bertambah dihitung sebagai perpanjangan, respons sama diberi jeda300detik dan percobaan dibatasi12.
3. Jika akses mendekati240detik tanpa perpanjangan, penjaga berhenti untuk audit root. Worker tetap memakai guard180detik sebelum request; jangan otomatisrestart/ulang request.
4. Kompilasi/sourcehash lokal-server dan pemeriksaan kondisi expiry, kemudian jalankan penjaga baru untuk PID/starttime worker asli.
5. Recovery hanya setelah worker terminal terbukti dan traceback menyatakan guard Token expiring sebelum marker request baru: seluruh file records wajib contiguous0..N-1 dan statuscomplete; cocokkan source/config/ID/prompt/image/usage/quota/hash tanpa skor kualitas parsial. Bila ada marker tidak lengkap atau sebab terminal lain, jangan resume otomatis; audit penyebab dahulu.
6. Tunggu token resmi dengan expiry baru yang cukup untuk sisa job; pertahankan file600/atomic, tanpa mencetak key. Pastikan run.lock dan semua watcher/dispatcher lama terminal/lock bebas. Arsipkan state/log lama beserta manifest ke recovery, jangan menimpa bukti terminal.
7. Jalankan source run.py yang sama dengan config/cache sama setelah audit lolos; kode akan melewati seluruh respons complete dan hanya memanggil ID berikutnya. Pasang strictwatch, finalwatch dan dispatcher E20 ulang menggunakan PID/starttime baru setelah state lama diarsipkan; sumber/parser/evaluator tidak berubah. Catat semua identitas baru dan batas audit. Ini kelanjutan ID baru, tidak retry ID sebelumnya.

## Risiko & Asumsi
- Belum diketahui kapan backend menerbitkan token dengan expiry baru. Tidak menjamin job selesai sebelum guard.
- Token API adalah data rahasia; log hanya expiry/status/angka, file tetap mode600 dan atomic.
- Perubahan hanya penjaga akses; hash worker/auditor tetap agar evaluasi dapat diteruskan jika akses valid.

## Verifikasi
Same-expiry tidak dihitung renew dan tidak menimpa file; expiry bertambah diterima, expiry mundur ditolak. PID worker asli tetap aktif, tidak ada request model dari penjaga. Catat hasil runtime tanpa mengklaim perpanjangan yang belum terbukti.

## Bukti implementasi
- SDK request ApiCreateDefaultModelProxyTokenRequest kosong; client hanya menyediakan create_default_model_proxy_token. Tiga respons legacy tetap expiry2026-10-11T01:32:30.573000Z, jadi log lama access_refreshed tidak membuktikan perpanjangan.
- Penjaga lama1290147 terminal dan lock bebas terverifikasi; worker1176994/starttime205000293 tetap hidup. Tidak mengubah worker/watcher audit.
- Source SHA256914838196be2b3cac891851ef5e35308f85f922fa209ab17e4c06933ec15dfbd lokal/server cocok, compile lolos; kondisi same/new/backward expiry diuji. File secret tetap600.
- Penjaga baru2050071 aktif pada tmux tempo-e18-access-fixed, log terpisah e18_access_fixed.log. Runtime mencatat access_not_extended attempt1 dengan expiry lama; belum ada bukti perpanjangan. E18 terakhir527/740 cost1.991566USD.
- Jika backend tidak memperpanjang sampai guard, wajib audit terminal/cache sebelum kelanjutan; tidak otomatisrestart inferensi atau mengulang respons.
- Pemantauan berikutnya:634/740 cost2.385949USD, attempt4 masih expiry sama; worker dan penjaga aktif. Prosedur recovery disiapkan, belum dilakukan karena worker belum terminal.

## Recovery guard selesai
- Worker1176994 terminal dengan traceback persis Token expiring; refresh after audit pada guard sebelum request.688 respons contiguous0..687 complete, tidak ada marker688; seluruh rekonstruksi prompt/image/transmittedPNG/permutation, response/code/usage/quota dan cumulative2.5726695USD lolos dari prefix verifier pinned. Tidak menghitung kualitas parsial. Audit SHA213cb56a646903aebfb30c07244d126e31ee7fc7d5a50ac2c76c2ddec5b18213.
- Semua lima proses lama terminal dan lock bebas, state/log diarsipkan `e18_guard_recovery/pre_resume/` beserta manifest. Salinan lokal recovery guard_recovery diperiksa: hash audit dan9 file arsip cocok; bukti root_copy_verification.json.688 respons sendiri diaudit di server, belum disalin seluruhnya ke lokal.
- Setelah expiry lama lewat, endpoint resmi memberi expiry baru2026-10-11T03:33:18.102000Z, diterima hanya setelah expiry meningkat dan TTL>3600s, atomic600. Tidak mencetak key atau mengganti provider/metode pembayaran.
- Worker baru2352897/starttime205698269 memakai source/config/cache sama; log689 dan690 membuktikan kelanjutan ID baru dan audit kuota lolos. Seluruh source pin watcher/dispatcher lama cocok sebelum rearm.
- Strictwatch2358172/starttime205701289, finalwatch2360326/starttime205702498, E20dispatcher2361801 dan penjagaakses2362139 aktif. Log baru terpisah, state lama tetap tersimpan. E18 belum740 dan belum ada skor kualitas baru; pekerjaan target berlanjut di plan E18/E20.
