#!/usr/bin/env python3
"""Pemetaan nama kelas teknis ke istilah yang mudah dipahami pembaca.

Revisi 15 Sep (R2): "semua nama kelas jangan kaku jadi bisa di ganti atau
rename (bukan di dataset) saat di tampilkan dengan istilah lebih mudah di
pahami".

PENTING — pemetaan ini hanya untuk TAMPILAN.
Dataset (`03_data/DATASET_740_TASK2_DOMAIN.csv`) tidak diubah sama sekali,
begitu juga label yang dipakai saat pelatihan dan evaluasi. Semua metrik di
`04_hasil_eksperimen/` tetap memakai nama kelas teknis, sehingga hasil
eksperimen tetap dapat direproduksi dan dibandingkan dengan laporan.

Cara pakai:
    from label_display import tampil, tampil_lengkap

    tampil("KONSUMSI_TRANSAKSI")        -> "Konsumsi & Transaksi"
    tampil("corruption_and_bribery")    -> "Korupsi & Suap"

Bila sebuah kelas belum terdaftar di sini, fungsi `tampil` tidak akan gagal:
ia mengembalikan versi rapi dari nama teknisnya (garis bawah jadi spasi,
huruf awal kapital). Jadi menambah kelas baru di dataset tidak merusak
antarmuka.
"""

from __future__ import annotations

# --------------------------------------------------------------------------
# Task 1 — Isu utama (10 kelas)
# --------------------------------------------------------------------------
LABEL_TASK1 = {
    "corruption_and_bribery": "Korupsi & Suap",
    "power_and_governance": "Kekuasaan & Tata Kelola",
    "election_and_political_competition": "Pemilu & Persaingan Politik",
    "economy_business_and_state_enterprise": "Ekonomi, Bisnis & BUMN",
    "public_policy_health_and_disaster": "Kebijakan Publik, Kesehatan & Bencana",
    "law_and_justice": "Hukum & Peradilan",
    "human_rights_and_social_conflict": "Hak Asasi & Konflik Sosial",
    "environment_and_natural_resources": "Lingkungan & Sumber Daya Alam",
    "security_defense_and_terrorism": "Keamanan, Pertahanan & Terorisme",
    "other_issue": "Isu Lainnya",
}

# --------------------------------------------------------------------------
# Task 2 — Domain sumber metafora (7 kelas)
#
# Istilah dipilih agar terbaca sebagai frasa biasa, bukan kode.
# Contoh yang disorot dosen: KONSUMSI_TRANSAKSI -> "Konsumsi & Transaksi",
# PERMAINAN_KONTES -> "Permainan & Kontes".
# --------------------------------------------------------------------------
LABEL_TASK2 = {
    "MESIN_INFRASTRUKTUR": "Mesin & Infrastruktur",
    "PERMAINAN_KONTES": "Permainan & Kontes",
    "BENCANA_JERAT": "Bencana & Jerat",
    "HEWAN_TUBUH": "Hewan & Tubuh",
    "KONSUMSI_TRANSAKSI": "Konsumsi & Transaksi",
    "NON_METAFORA": "Tanpa Metafora",
    "LAINNYA": "Lainnya",
}

# --------------------------------------------------------------------------
# Task 3 — Tipe entitas sasaran (8 kelas)
# --------------------------------------------------------------------------
LABEL_TASK3 = {
    "individual": "Perorangan",
    "government": "Pemerintah",
    "multiple_or_other": "Beberapa Pihak / Lainnya",
    "civil_society_or_media": "Masyarakat Sipil & Media",
    "business": "Pelaku Usaha",
    "judiciary_or_law_enforcement": "Peradilan & Penegak Hukum",
    "political_party": "Partai Politik",
    "legislature": "Lembaga Legislatif",
}

# Semua pemetaan digabung. Nama kelas antar-task tidak ada yang bertabrakan,
# sehingga satu kamus datar sudah cukup dan pemanggilnya tidak perlu tahu
# kelas ini milik task yang mana.
SEMUA_LABEL = {**LABEL_TASK1, **LABEL_TASK2, **LABEL_TASK3}

# Nama task itu sendiri, untuk judul di antarmuka.
LABEL_TASK = {
    "task1_issue": "Isu Utama",
    "task2_domain_sumber": "Domain Sumber Metafora",
    "task3_primary_entity_type": "Sasaran Kritik",
}


def tampil(kelas: str) -> str:
    """Nama kelas untuk ditampilkan ke pembaca.

    Bila kelas belum terdaftar, dirapikan seadanya alih-alih menampilkan
    nama teknis mentah — dan tidak pernah melempar error.
    """
    if kelas is None:
        return ""
    kelas = str(kelas)
    if kelas in SEMUA_LABEL:
        return SEMUA_LABEL[kelas]
    return kelas.replace("_", " ").strip().title()


def tampil_lengkap(kelas: str) -> str:
    """Istilah awam diikuti nama teknisnya dalam kurung.

    Dipakai pada tampilan teknis, supaya pembaca yang menelusuri metodologi
    tetap bisa mencocokkan dengan dataset dan tabel hasil eksperimen.
    """
    if kelas is None:
        return ""
    kelas = str(kelas)
    mudah = tampil(kelas)
    return mudah if mudah == kelas else f"{mudah} ({kelas})"


def nama_task(task: str) -> str:
    """Nama task untuk ditampilkan ke pembaca."""
    return LABEL_TASK.get(task, task)
