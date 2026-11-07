# Publikasi Repository GitHub Public

**Tanggal:** 2026-11-08
**Status:** done

## Tujuan
Membuat repository GitHub public baru pada akun yusepahmad untuk source dan hasil penelitian yang berada di server .31, sehingga pekerjaan dapat diakses tanpa menulis ke laptop.

## Ruang Lingkup
- Source workspace /home/yusep/workspace/tempo-revisi-20261108 dibaca; plan ini, CHANGELOG, laporan ekspor publik dan handoff diperbarui setelah hasil aktual.
- Salinan publik terpisah: /home/yusep/workspace/tempo-clip-indobert-xai-public; tidak mengubah paket/server asli. Repository usulan: yusepahmad/tempo-clip-indobert-xai, atau suffix tanggal bila nama sudah digunakan.
- Source, data/prediksi/hasil, dokumen, notebook dan reproduksi R4 yang sudah tersedia di server. Tidak mengklaim seluruh model/cache/arsip laptop tersedia.
- Credential, .env, private keys, kunci kontrol XAI koordinator, registrasi/identitas partisipan dan folder hasil isian manusia tidak dipublikasikan. Environment, cache, file parsial migrasi dan blob model besar tidak masuk Git.
- Paket ZIP publik disanitasi ulang dari R4 dan dipublikasikan sebagai Release; ZIP privat asli tidak diunggah. Tidak memberikan lisensi baru atas bobot/citra pihak ketiga.

## Langkah
1. Periksa identitas GitHub dan izin akun tanpa menampilkan token; inventaris source/ukuran dan instruksi project.
2. Buat salinan publik dengan allowlist berkas kerja dan paket R4. Tambahkan README, .gitignore, provenance, daftar pengecualian serta petunjuk reproduksi. Notebook/web tetap menyebut model aktual; tidak mengklaim web memakai kandidat terbaru.
3. Audit secret dan isi publik menggunakan scanner resmi; periksa kunci privat/identitas yang tersalin melalui snapshot, notebook atau arsip. Tindak lanjuti temuan sebelum upload.
4. Rebuild manifest paket publik dan ZIP, validasi metrik/hash/cakupan serta uji dari ekstraksi. Jalankan tes analisis pada salinan publik. Pertahankan status19/28selesai dan job literal yang masih berjalan.
5. Catat perubahan aktual ke CHANGELOG dan plan, buat commit Git lokal, lalu create repo public baru dan push main setelah berkas konkret lolos audit. Tidak mengubah repo lama atau force-push.
6. Buat GitHub Release berisi ZIP publik/checksum yang sesuai batas ukuran; verifikasi visibilitas public, commit remote, file README dan artefak Release. Laporkan URL dan batas isi.

## Risiko & Asumsi
- Pengguna secara eksplisit meminta repo baru public; tidak perlu konfirmasi publikasi ulang. Token server hanya dipakai melalui helper credential, tidak disalin ke repo/log.
- GitHub menolak file Git>100MiB; artefak besar memakai Release, maksimum2GiBperasset menurut dokumentasi GitHub. Tidak memakai Git LFS/layanan berbayar otomatis.
- Snapshot/data berisi hak pihak ketiga; public tidak berarti pemberian lisensi baru. Registrasi dan kunci buta tetap di server asli.
- Menghapus file dari ekspor mengubah hash paket; manifest publik baru harus sesuai isi aktual. Metrik, label/fold/prediksi penelitian tidak diubah demi ekspor.
- Kegagalan akses GitHub/scan/validasi menghentikan publikasi data, bukan memicu bypass perlindungan push atau unggahan credential.

## Verifikasi
- Identitas akun cocok yusepahmad; repository baru tidak menimpa yang sudah ada.
- Tidak ada credential atau kunci privat penilai dalam tracked files maupun ZIP Release; laporan audit disimpan tanpa nilai secret.
- Semua file Git di bawah100MiB; paket publik memiliki manifest/checksum/CRC valid dan metrik234baris/78sumber sama, serta notebook lulus Run all sesuai cakupan.
- SHA commit lokal=main remote, visibility public, release assets dan checksum terverifikasi.

## Persiapan terverifikasi
- Akun yusepahmad cocok dengan konektor GitHub dan credential helper server. Nama repo tempo-clip-indobert-xai tersedia; tidak ada repo lama yang diubah.
- Salinan public terpisah dibuat. File privat/credential/identitas dan blob besar dikeluarkan; label/fold/prediksi/analisis sama byte demi byte dengan R4.
- Gitleaks v8.30.1 dengan aturan default dan redaksi100% menandai5246generic-api-key. Seluruh temuan ditinjau menurut struktur JSON:5174hash audit token/numeric counts,62manifest SHA,8base-weight SHA,2angka max_abs_valid_token. Tidak ada credential actionable; tidak ada aturan provider atau perlindungan push yang dibypass.
-26tes lulus pada salinan publik; paket Git publik memverifikasi234metrik/78sumber dan cakupan seluruh bukti. Paket Release telah lulus verifikasi terpisah dan diunggah.

## Hasil aktual
- Repository baru public: [yusepahmad/tempo-clip-indobert-xai](https://github.com/yusepahmad/tempo-clip-indobert-xai), branch `main`, snapshot awal `5b3a84bb61936583572f7b8a72b4571fed8efff4`. Tidak ada repo lama yang ditimpa.
- [Release R4](https://github.com/yusepahmad/tempo-clip-indobert-xai/releases/tag/v2026.11.08-r4) memiliki ZIP publik 449.730.156 byte, checksum SHA-256 dan laporan verifikasi. Tag menunjuk snapshot awal; pembaruan catatan publikasi memakai commit main berikutnya.
- SHA-256 ZIP: `a2c9a67f7ee02472f76a0581b364dfc96b6c7bd6584cb71a3cac5a090a8d2035`, sama dengan digest asset GitHub. Ketiga asset berstatus uploaded dan digest/ukuran cocok.
- Ekstraksi ZIP publik lulus Run all tiga notebook, 2.421 hash, 234 metrik dari 78 sumber; 26 tes salinan source publik lulus. Delapan ZIP instrumen manusia dibuat ulang dari formulir kosong yang anonim.
- Akses tanpa autentikasi memverifikasi repo public, README, branch main, metadata Release, serta unduhan berkas checksum. Laporan lengkap tetap di `qa/PUBLIC_ANONYMOUS_VERIFICATION.json` dan `qa/PUBLIC_RELEASE_PUBLISH_STATE.json` pada server.
- Status riset snapshot R4 tetap 19/28 selesai teknis. Bukti manusia, Run all Colab aktual dan eksperimen literal citra+judul belum diklaim selesai. Web tidak dipromosikan ke model baru oleh publikasi ini.
