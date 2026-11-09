# MICRO-E12

Gate 0,70: belum lulus.

Micro-F1: {'task1_issue': 0.5783783783783784, 'task2_domain_sumber': 0.5445945945945946, 'task3_primary_entity_type': 0.5108108108108108}.

Kontrol tanpa prior: {'task1_issue': 0.5797297297297297, 'task2_domain_sumber': 0.55, 'task3_primary_entity_type': 0.5121621621621621}.

## Keputusan

Tidak dipromosikan. Minimum decoder `0,5108` sedikit di bawah kontrol tanpa
prior `0,5122` (-0,14 poin persentase), dan di bawah minimum E11 `0,5324`.
Prior tidak menghasilkan perbaikan konsisten pada konfigurasi yang diuji.
Pencarian konfigurasi prior tambahan dihentikan untuk menjaga waktu eksperimen.

Lima outer fold dan 15 audit inner split lulus verifikasi. Seluruh stack dibuat
ulang di inner-training sebelum memilih decoder. Perbandingan dengan kontrol
tanpa prior merupakan ablation paling langsung; E10/E11 memakai prosedur
seleksi meta yang berbeda dan dilaporkan terpisah.

Evaluasi internal; tidak menjadi validasi independen akibat penggunaan korpus berulang.
