# Koneksi SSH Laptop Training Windows

**Tanggal:** 2026-10-05
**Status:** done

## Tujuan
Menghubungkan laptop Linux ke laptop Windows GTX 1650 untuk pemeriksaan dan persiapan training.

## Ruang Lingkup
- `~/.ssh/known_hosts`: tambah host Windows setelah fingerprint diverifikasi.
- Public key lokal yang sudah ada dipasang oleh user ke `C:\ProgramData\ssh\administrators_authorized_keys` dengan ACL terbatas.
- Plan ini dan `CHANGELOG.md` root.
- Tidak mengubah dataset/model atau menjalankan training penuh.

## Langkah
1. Verifikasi port 22 dan fingerprint ED25519 dengan hasil PowerShell user.
2. Tambahkan host terverifikasi ke known_hosts tanpa menimpa entri lain.
3. Berikan perintah pemasangan public key untuk akun Administrator Windows.
4. Tes login BatchMode, whoami, dan nvidia-smi setelah pemasangan selesai.
5. Catat perubahan yang diterapkan dan hasil koneksi.

## Risiko & Asumsi
- IP DHCP bisa berubah; firewall Windows saat ini membatasi akses dari 192.168.0.36.
- Akun user anggota Administrators; lokasi authorized_keys mengikuti konfigurasi default OpenSSH Windows.
- Private key tidak ditransfer. Public key memakai key lokal yang sudah ada.

## Verifikasi
Fingerprint harus cocok dengan SHA256:qbYejFzE/xmkFrsV63OqV6Vp4chYWczGlKHniiJcoYM; login tanpa password berhasil; GPU teridentifikasi lewat nvidia-smi.

## Hasil Verifikasi
- Login SSH BatchMode dengan key lokal berhasil sebagai `msi\user`.
- Fingerprint server cocok; `nvidia-smi` berhasil melalui SSH.
- GTX 1650 terdeteksi dengan VRAM 4096 MiB, terpakai 467 MiB saat pemeriksaan; driver 610.47.
- `where python` hanya menemukan alias WindowsApps dan `where py` tidak menemukan launcher; kesiapan Python/CUDA perlu diperiksa terpisah.
- Folder `C:\Users\User\AppData\Local\Programs\Python\Python311` ada, tetapi pemanggilan `python.exe` di lokasi itu gagal; interpreter Python aktif belum terverifikasi.
