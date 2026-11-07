#!/usr/bin/env python3
"""Inti demo XAI: prediksi 3 task + Grad-CAM visual + atribusi kata.

Dipakai oleh app.py (web) dan bisa dipanggil langsung dari CLI.

Catatan penting soal Grad-CAM pada CLIP ViT:
Grad-CAM klasik dirancang untuk CNN. Pada Vision Transformer, aktivasi dan
gradien diambil dari token patch pada blok transformer KEDUA DARI BELAKANG
(pada blok terakhir gradien token patch bernilai nol karena hanya token CLS
yang dipakai embedding), besarannya |aktivasi x gradien| per patch, lalu
di-reshape kembali menjadi grid 7x7 (untuk ViT-B/32 pada input 224px). Ini
pendekatan yang lazim dipakai, tetapi bukan Grad-CAM CNN yang identik —
perbedaan ini harus disebut di laporan.

Peta gabungan tiga task (`gradcam_terpadu`) adalah peta utama di antarmuka;
peta task pilihan menjadi dasar narasi/zona. Atribusi kata: LIME (baku 120
varian) untuk analisis satu sampul, occlusion untuk batch. Narasi ringkasan
dan penjelasan yang tampil di aplikasi disusun `explanation_evidence.py`.

Karena encoder CLIP dibekukan dan yang dilatih hanya head MTL, gradien dialirkan
dari skor kelas prediksi ke aktivasi patch CLIP melalui head. Jadi peta panas
menunjukkan patch mana yang paling memengaruhi keputusan head, bukan sekadar
apa yang "menarik" bagi CLIP.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from PIL import Image

# Pemetaan nama kelas teknis -> istilah awam, untuk tampilan saja.
# Dataset dan label pelatihan tidak tersentuh (revisi 15 Sep, R2).
from label_display import nama_task, tampil

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
# Path relatif terhadap paket ini (bukan workspace asal).
DATA_CSV = ROOT / "03_data" / "DATASET_740_TASK2_DOMAIN.csv"
FEATURES = ROOT / "03_data" / "fitur_clip_indobert_740.npz"
DIR_GAMBAR = ROOT / "05_gambar"

CLIP_MODEL = "ViT-B-32"
CLIP_PRETRAINED = "laion2b_s34b_b79k"
INDOBERT = "indobenchmark/indobert-base-p1"

TASKS = {
    "task1_issue": "Task 1 — Isu Utama",
    "task2_domain_sumber": "Task 2 — Domain Sumber Metafora",
    "task3_primary_entity_type": "Task 3 — Tipe Entitas Sasaran",
}
SEED = 42


class MTLHead(nn.Module):
    def __init__(self, in_dim, n_classes, hidden=256, p_drop=0.4):
        super().__init__()
        self.shared = nn.Sequential(nn.Linear(in_dim, hidden), nn.ReLU(), nn.Dropout(p_drop))
        self.heads = nn.ModuleDict({t: nn.Linear(hidden, n) for t, n in n_classes.items()})

    def forward(self, x):
        h = self.shared(x)
        return {t: head(h) for t, head in self.heads.items()}


class XAIEngine:
    """Memuat data, melatih head MTL sekali, lalu melayani prediksi + XAI."""

    def __init__(self) -> None:
        import pandas as pd
        self.df = pd.read_csv(DATA_CSV, encoding="utf-8-sig")
        z = np.load(FEATURES)
        self.X = np.hstack([z["img"], z["txt"]]).astype(np.float32)
        self.dim_img = z["img"].shape[1]

        self.tasks = list(TASKS)
        self.maps, self.y, self.ncls = {}, {}, {}
        for t in self.tasks:
            cats = sorted(self.df[t].astype(str).unique())
            self.maps[t] = cats
            self.y[t] = self.df[t].astype(str).map({c: i for i, c in enumerate(cats)}).to_numpy()
            self.ncls[t] = len(cats)

        self._clip = None
        self._preprocess = None
        self._tok = None
        self._bert = None
        self.model = None

    # ---------- encoder dimuat lambat, hanya saat dibutuhkan ----------

    def _ensure_encoders(self):
        if self._clip is None:
            import open_clip
            self._clip, _, self._preprocess = open_clip.create_model_and_transforms(
                CLIP_MODEL, pretrained=CLIP_PRETRAINED
            )
            self._clip.eval()
        if self._bert is None:
            from transformers import AutoModel, AutoTokenizer
            self._tok = AutoTokenizer.from_pretrained(INDOBERT)
            self._bert = AutoModel.from_pretrained(INDOBERT)
            self._bert.eval()

    # ---------- pelatihan head ----------

    def train(self, exclude_index: int | None = None, epochs: int = 120):
        """Latih head MTL. exclude_index dipakai untuk leave-one-out."""
        torch.manual_seed(SEED)
        np.random.seed(SEED)
        idx = [i for i in range(len(self.df)) if i != exclude_index]
        tr = np.array(idx)

        cw = {}
        for t in self.tasks:
            cnt = np.bincount(self.y[t][tr], minlength=self.ncls[t]).astype(np.float32)
            w = np.where(cnt > 0, len(tr) / (np.maximum(cnt, 1) * (cnt > 0).sum()), 0.0)
            cw[t] = torch.tensor(w, dtype=torch.float32)

        model = MTLHead(self.X.shape[1], self.ncls)
        opt = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-4)
        losses = {t: nn.CrossEntropyLoss(weight=cw[t]) for t in self.tasks}
        Xtr = torch.tensor(self.X[tr])
        ytr = {t: torch.tensor(self.y[t][tr]) for t in self.tasks}

        model.train()
        for _ in range(epochs):
            opt.zero_grad()
            out = model(Xtr)
            loss = sum(losses[t](out[t], ytr[t]) for t in self.tasks) / len(self.tasks)
            loss.backward()
            opt.step()
        model.eval()
        self.model = model
        return model

    # ---------- fitur untuk gambar/teks baru ----------

    def features_for(self, image_path: Path, headline: str, supporting: str = ""):
        self._ensure_encoders()
        with torch.no_grad():
            im = self._preprocess(Image.open(image_path).convert("RGB")).unsqueeze(0)
            v = self._clip.encode_image(im)
            v = v / v.norm(dim=-1, keepdim=True)
            text = f"{headline} [SEP] {supporting}".strip()
            enc = self._tok(text, return_tensors="pt", truncation=True,
                            max_length=128, padding="max_length")
            h = self._bert(**enc).last_hidden_state[:, 0, :]
            h = h / h.norm(dim=-1, keepdim=True)
        return v.squeeze(0).numpy().astype(np.float32), h.squeeze(0).numpy().astype(np.float32)

    # ---------- prediksi ----------

    def predict_vector(self, x: np.ndarray):
        if self.model is None:
            self.train()
        with torch.no_grad():
            out = self.model(torch.tensor(x.reshape(1, -1)))
        hasil = {}
        for t in self.tasks:
            prob = torch.softmax(out[t][0], dim=0).numpy()
            order = prob.argsort()[::-1]
            kelas_teratas = self.maps[t][int(order[0])]
            hasil[t] = {
                "nama_task": TASKS[t],
                # Revisi 15 Sep (R2): nama_task_mudah dan setiap "kelas_tampil"
                # adalah istilah awam untuk ditampilkan. Nilai teknisnya tetap
                # dikirim apa adanya agar dapat dicocokkan dengan dataset.
                "nama_task_mudah": nama_task(t),
                "prediksi": kelas_teratas,
                "prediksi_tampil": tampil(kelas_teratas),
                "probabilitas": float(prob[order[0]]),
                "semua": [
                    {
                        "kelas": self.maps[t][int(j)],
                        "kelas_tampil": tampil(self.maps[t][int(j)]),
                        "prob": float(prob[j]),
                    }
                    for j in order
                ],
            }
        return hasil

    # ---------- Grad-CAM pada CLIP ViT ----------

    def gradcam(self, image_path: Path, txt_feat: np.ndarray, task: str,
                class_index: int | None = None):
        """Peta panas 7x7 dari blok transformer kedua dari belakang CLIP ViT-B/32."""
        self._ensure_encoders()
        if self.model is None:
            self.train()

        im = self._preprocess(Image.open(image_path).convert("RGB")).unsqueeze(0)

        simpan = {}

        def hook_fwd(_m, _i, o):
            simpan["act"] = o

        def hook_bwd(_m, _gi, go):
            simpan["grad"] = go[0]

        # Blok terakhir tidak dipakai: pada CLIP ViT hanya token CLS yang
        # dipakai untuk embedding akhir, sehingga gradien token patch di blok
        # terakhir bernilai nol. Blok kedua dari belakang masih meneruskan
        # informasi patch ke CLS melalui self-attention, sehingga gradien
        # patch di situ tidak nol.
        blok = self._clip.visual.transformer.resblocks[-2]
        h1 = blok.register_forward_hook(hook_fwd)
        h2 = blok.register_full_backward_hook(hook_bwd)

        try:
            v = self._clip.encode_image(im)
            v = v / v.norm(dim=-1, keepdim=True)
            x = torch.cat([v[0], torch.tensor(txt_feat)]).reshape(1, -1)
            out = self.model(x)
            logits = out[task][0]
            k = int(logits.argmax()) if class_index is None else class_index
            self._clip.zero_grad(set_to_none=True)
            self.model.zero_grad(set_to_none=True)
            logits[k].backward()
        finally:
            h1.remove()
            h2.remove()

        act = simpan.get("act")
        grad = simpan.get("grad")
        if act is None or grad is None:
            return None, k

        a = act.detach()
        g = grad.detach()

        # open_clip ViT dapat mengeluarkan (batch, tokens, dim) atau
        # (tokens, batch, dim). Normalkan ke (tokens, dim).
        if a.dim() == 3:
            if a.shape[0] == 1:          # (1, tokens, dim)
                a, g = a[0], g[0]
            elif a.shape[1] == 1:        # (tokens, 1, dim)
                a, g = a[:, 0, :], g[:, 0, :]
            else:
                return None, k
        else:
            return None, k

        # Catatan penting soal ViT CLIP.
        # `encode_image` hanya memakai token CLS untuk menghasilkan embedding,
        # sehingga pada blok terakhir gradien token patch bernilai nol dan
        # hanya CLS yang menerima gradien. Akibatnya rumus Grad-CAM CNN
        # (bobot = rata-rata gradien lalu dikalikan aktivasi patch)
        # menghasilkan peta kosong.
        #
        # Karena itu kami mengambil hook pada blok kedua dari belakang, di mana
        # informasi patch masih mengalir ke CLS melalui self-attention, dan
        # memakai |aktivasi x gradien| per token (Gradient x Input) sebagai
        # besaran pengaruh tiap patch. Ini bukan Grad-CAM CNN yang identik dan
        # harus disebut apa adanya di laporan.
        a = a[1:]
        g = g[1:]
        if float(g.abs().sum()) == 0.0:
            return None, k

        # Gradient x Activation per token, lalu diambil besarannya.
        cam = (a * g).sum(dim=-1).abs()

        n = cam.shape[0]
        sisi = int(round(n ** 0.5))
        if sisi * sisi != n:
            return None, k

        cam = cam.reshape(sisi, sisi).float().numpy()
        rentang = float(cam.max() - cam.min())
        if rentang > 1e-12:
            cam = (cam - cam.min()) / rentang
        else:
            cam = np.zeros_like(cam)
        return cam, k

    # ---------- peta panas terpadu untuk ketiga task ----------

    def gradcam_terpadu(self, image_path: Path, txt_feat: np.ndarray):
        """Satu peta panas yang mewakili ketiga task sekaligus.

        Revisi 15 Sep (R5): "pas ke user nanti di minta hanya satu dan sama
        dan itu harus mencakup semua". Peta per task tetap dihitung dan tetap
        tersedia untuk tampilan teknis; yang ditambahkan di sini adalah
        gabungannya.

        Setiap peta per task sudah dinormalisasi ke rentang [0, 1] oleh
        `gradcam()`, sehingga rata-rata antar-task tidak didominasi task yang
        kebetulan bergradien besar. Hasil rata-rata dinormalisasi ulang agar
        kontrasnya setara dengan peta tunggal.

        Mengembalikan (cam_gabungan, cam_per_task). `cam_gabungan` bernilai
        None bila tidak ada satu pun task yang menghasilkan peta.
        """
        per_task = {}
        for t in self.tasks:
            cam, _ = self.gradcam(image_path, txt_feat, t)
            if cam is not None:
                per_task[t] = cam

        if not per_task:
            return None, {}

        tumpuk = np.stack(list(per_task.values()), axis=0)
        gabungan = tumpuk.mean(axis=0)

        rentang = float(gabungan.max() - gabungan.min())
        if rentang > 1e-12:
            gabungan = (gabungan - gabungan.min()) / rentang
        else:
            gabungan = np.zeros_like(gabungan)

        return gabungan, per_task

    # ---------- atribusi kata (occlusion, gaya LIME sederhana; baku untuk batch) ----------

    def atribusi_kata(self, img_feat: np.ndarray, headline: str,
                      supporting: str, task: str):
        """Hilangkan satu kata, ukur penurunan probabilitas kelas terpilih.

        Ini occlusion-based attribution, bukan LIME penuh (tanpa model surrogate
        dan tanpa sampling berbobot). Lebih sederhana tetapi deterministik dan
        cukup untuk memperlihatkan kata mana yang menopang keputusan.
        """
        self._ensure_encoders()
        if self.model is None:
            self.train()

        def prob_untuk(teks_headline: str):
            with torch.no_grad():
                t = f"{teks_headline} [SEP] {supporting}".strip()
                enc = self._tok(t, return_tensors="pt", truncation=True,
                                max_length=128, padding="max_length")
                h = self._bert(**enc).last_hidden_state[:, 0, :]
                h = h / h.norm(dim=-1, keepdim=True)
                x = np.concatenate([img_feat, h.squeeze(0).numpy()]).reshape(1, -1)
                out = self.model(torch.tensor(x.astype(np.float32)))
                return torch.softmax(out[task][0], dim=0).numpy()

        dasar = prob_untuk(headline)
        k = int(dasar.argmax())
        kata = headline.split()
        skor = []
        for i in range(len(kata)):
            sisa = " ".join(kata[:i] + kata[i + 1:])
            p = prob_untuk(sisa) if sisa.strip() else dasar * 0
            skor.append({"kata": kata[i], "kontribusi": float(dasar[k] - p[k])})
        return skor, self.maps[task][k], float(dasar[k])

    # ---------- atribusi kata dengan LIME ----------

    def _prob_banyak_teks(self, img_feat: np.ndarray, daftar_teks, supporting: str,
                          task: str, ukuran_kelompok: int = 32) -> np.ndarray:
        """Hitung probabilitas semua kelas untuk banyak varian judul sekaligus.

        LIME membangkitkan banyak varian teks (baku 120; sebagian kata dihilangkan),
        lalu meminta probabilitas untuk semuanya. Memanggil IndoBERT satu per
        satu terlalu lambat, jadi diproses berkelompok.
        """
        self._ensure_encoders()
        if self.model is None:
            self.train()

        hasil = []
        with torch.no_grad():
            for i in range(0, len(daftar_teks), ukuran_kelompok):
                potongan = list(daftar_teks[i:i + ukuran_kelompok])
                gabung = [f"{t} [SEP] {supporting}".strip() for t in potongan]
                enc = self._tok(gabung, return_tensors="pt", truncation=True,
                                max_length=128, padding="max_length")
                h = self._bert(**enc).last_hidden_state[:, 0, :]
                h = h / h.norm(dim=-1, keepdim=True)
                h = h.numpy()

                img = np.repeat(img_feat.reshape(1, -1), len(potongan), axis=0)
                x = np.hstack([img, h]).astype(np.float32)
                out = self.model(torch.tensor(x))
                hasil.append(torch.softmax(out[task], dim=1).numpy())

        return np.vstack(hasil)

    def atribusi_kata_lime(self, img_feat: np.ndarray, headline: str,
                           supporting: str, task: str, n_sampel: int = 120):
        """Atribusi kata memakai LIME dengan model surrogate.

        Revisi 15 Sep (R4): metode occlusion sebelumnya menghasilkan kontribusi
        negatif untuk semua kata pada sampul "GULA-GULA DEMO BURUH", termasuk
        kata "DEMO" yang jelas tergambar pada sampul. Dosen menilai ini fatal.

        Perbedaan dengan occlusion:
          - occlusion menghapus SATU kata setiap kali, sehingga pengaruh
            gabungan antar-kata tidak terukur;
          - LIME membangkitkan banyak varian yang menghilangkan beberapa kata
            sekaligus, lalu mencocokkan regresi linear berbobot jarak pada
            varian-varian itu. Bobot tiap kata diambil dari koefisien regresi
            tersebut, sehingga memperhitungkan interaksi antar-kata.

        Diagram rancangan penelitian menyebut LIME; sampai revisi ini yang
        terpasang baru occlusion. Keduanya kini tersedia dan dapat dibandingkan.

        `n_sampel` adalah jumlah varian yang dibangkitkan. Makin besar makin
        stabil tetapi makin lambat. Diuji pada 5 sampul: 80 varian memberi
        korelasi 0,960 terhadap 200 varian dengan kata teratas sama pada 4
        dari 5 sampul, sementara waktunya turun dari 15,9 ke 6,1 detik.
        Nilai baku 120 dipilih sebagai kompromi — cukup stabil tanpa membuat
        pengguna menunggu terlalu lama.
        """
        from lime.lime_text import LimeTextExplainer

        self._ensure_encoders()
        if self.model is None:
            self.train()

        kata = headline.split()
        if not kata:
            return [], self.maps[task][0], 0.0

        dasar = self._prob_banyak_teks(img_feat, [headline], supporting, task)[0]
        k = int(dasar.argmax())

        # LIME memakai random_state agar hasilnya dapat diulang. Tanpa itu,
        # dua analisis pada sampul yang sama bisa memberi angka berbeda —
        # menyulitkan verifikasi dan pelaporan.
        explainer = LimeTextExplainer(
            class_names=self.maps[task],
            bow=False,            # posisi kata dipertahankan, kata kembar dibedakan
            split_expression=r"\s+",
            random_state=SEED,
        )

        def klasifikasi(daftar_teks):
            return self._prob_banyak_teks(img_feat, daftar_teks, supporting, task)

        penjelasan = explainer.explain_instance(
            headline,
            klasifikasi,
            labels=(k,),
            num_features=len(kata),
            num_samples=n_sampel,
        )

        # LIME mengembalikan (posisi_kata, bobot) karena bow=False.
        bobot = dict(penjelasan.as_map()[k])
        skor = [
            {"kata": w, "kontribusi": float(bobot.get(i, 0.0))}
            for i, w in enumerate(kata)
        ]
        return skor, self.maps[task][k], float(dasar[k])


# --------------------------------------------------------------------------
# Definisi domain untuk Codebook.
#
# PENTING soal asal teks. Definisi di bawah ditulis manusia berdasarkan
# pembacaan 657 catatan pemetaan makna pada dataset — BUKAN dihasilkan model
# saat runtime. Teks ini bersifat tetap (template), sehingga penjelasan yang
# tampil di antarmuka selalu dapat dilacak asalnya dan tidak mungkin mengarang.
#
# Model hanya mengklasifikasi domain; makna metaforanya berasal dari anotasi
# manusia atau definisi ini. Model tidak "memahami" makna metafora.
# --------------------------------------------------------------------------

DEFINISI_DOMAIN = {
    "HEWAN_TUBUH": {
        "judul": "Hewan dan tubuh",
        "definisi": "Metafora yang memakai hewan, bagian tubuh, atau deformasi "
                    "tubuh sebagai sumber kiasan.",
        "pola": "Pada korpus ini umumnya dipakai untuk menggambarkan sifat rakus, "
                "licik, kebohongan, atau dehumanisasi. Contoh: tikus untuk pihak "
                "yang menikmati korupsi; hidung panjang untuk janji yang diingkari.",
    },
    "PERMAINAN_KONTES": {
        "judul": "Permainan, kontes, dan panggung",
        "definisi": "Metafora yang memakai permainan, pertandingan, perlombaan, "
                    "sulap, atau panggung pertunjukan sebagai sumber kiasan.",
        "pola": "Umumnya dipakai untuk menggambarkan politik sebagai sesuatu yang "
                "diatur, dipertaruhkan, atau dipertontonkan. Contoh: perombakan "
                "kabinet sebagai drama panggung; pengadaan proyek sebagai trik sulap.",
    },
    "MESIN_INFRASTRUKTUR": {
        "judul": "Mesin, alat, dan infrastruktur",
        "definisi": "Metafora yang memakai mesin, kendaraan, alat kerja, bangunan, "
                    "atau infrastruktur sebagai sumber kiasan.",
        "pola": "Umumnya dipakai untuk menggambarkan sistem yang rusak, dikendalikan, "
                "atau dibongkar-pasang. Contoh: penghapus untuk penghilangan jejak; "
                "balok susun untuk bisnis yang diatur ulang.",
    },
    "KONSUMSI_TRANSAKSI": {
        "judul": "Konsumsi dan transaksi",
        "definisi": "Metafora yang memakai makanan, jamuan, uang, atau kegiatan "
                    "jual-beli sebagai sumber kiasan.",
        "pola": "Umumnya dipakai untuk menggambarkan pembagian keuntungan, selera "
                "pribadi penguasa, atau pilihan yang disajikan kepada publik. "
                "Contoh: pasangan calon sebagai menu pilihan.",
    },
    "BENCANA_JERAT": {
        "judul": "Bencana dan jerat",
        "definisi": "Metafora yang memakai bencana alam, api, banjir, badai, atau "
                    "alat pengekang seperti jeruji dan jerat sebagai sumber kiasan.",
        "pola": "Umumnya dipakai untuk menggambarkan ancaman yang datang, kekacauan, "
                "atau keterkungkungan. Contoh: badai untuk gelombang PHK; kebocoran "
                "untuk dana yang diselewengkan.",
    },
    "LAINNYA": {
        "judul": "Lainnya",
        "definisi": "Metafora yang sumbernya tidak masuk kelima domain di atas.",
        "pola": "Kelompok ini masih perlu ditinjau manusia. Pada dataset terdapat 63 "
                "sampul di sini, antara lain kiasan ritual pengorbanan, kematian "
                "simbolis, dan penyembunyian identitas.",
    },
    "NON_METAFORA": {
        "judul": "Tanpa metafora",
        "definisi": "Sampul yang tidak memuat metafora visual-verbal; elemen "
                    "visualnya bersifat literal.",
        "pola": "Pada korpus ini umumnya berupa edisi khusus biografi/sejarah dan "
                "foto jurnalistik. Sebanyak 83 dari 740 sampul termasuk kategori ini.",
    },
}


def _bersih(nilai) -> str:
    """Kembalikan teks yang benar-benar berisi, atau string kosong.

    Kolom kosong pada CSV terbaca sebagai NaN, lalu berubah menjadi string
    "nan" begitu dilewatkan `str()`. String itu truthy, sehingga tanpa
    penyaringan ini 83 sampul NON_METAFORA seolah-olah punya catatan
    anotator. Dipakai di seluruh pemeriksaan catatan anotator.
    """
    if nilai is None:
        return ""
    teks = str(nilai).strip()
    if teks.lower() in ("nan", "none", "null", "<na>"):
        return ""
    return teks


def _tanda(nilai: float) -> str:
    """Format angka kontribusi lengkap dengan tandanya.

    Ditulis terpisah karena sebelumnya tanda "+" dipasang permanen di dalam
    f-string, sehingga nilai negatif tercetak "+-0.023" (dilaporkan pada
    revisi 15 Sep).
    """
    return f"{nilai:+.3f}"


def zona_dominan(cam: np.ndarray):
    """Tentukan zona mana pada sampul yang paling memengaruhi keputusan.

    Grid Grad-CAM dibagi tiga baris: kepala sampul (logo dan kicker), bagian
    tengah (umumnya ilustrasi), dan kaki (headline besar, barcode).
    Pembagian ini deskriptif dan dihitung dari peta panas, bukan ditebak.
    """
    n = cam.shape[0]
    batas_atas = max(1, n // 3)
    batas_bawah = n - max(1, n // 3)
    zona = {
        "kepala sampul (logo dan judul kecil)": float(cam[:batas_atas].mean()),
        "bagian tengah (umumnya ilustrasi)": float(cam[batas_atas:batas_bawah].mean()),
        "kaki sampul (headline besar dan barcode)": float(cam[batas_bawah:].mean()),
    }
    urut = sorted(zona.items(), key=lambda kv: -kv[1])
    return urut[0][0], urut[0][1], zona


def susun_penjelasan(pred: dict, task_xai: str, kata: list, catatan: dict | None,
                     cam: np.ndarray | None, headline: str | None = None):
    """Rangkai penjelasan naratif dari komponen yang asalnya jelas.

    Setiap bagian diberi label asal:
      - "model"    : hasil prediksi/atribusi, dihitung saat itu
      - "anotator" : catatan manusia dari dataset
      - "codebook" : definisi tetap yang ditulis manusia

    Tidak ada teks yang dihasilkan model bahasa. Fungsi ini hanya menyusun.

    Catatan 6 Okt: aplikasi web tidak lagi memanggil fungsi ini; tab
    Penjelasan disusun `explanation_evidence.explain()`. Dipertahankan sebagai
    riwayat implementasi R3/R4/R5.
    """
    bagian = []

    # 0. peringatan bila teks masukan terlalu miskin untuk dipercaya.
    #
    # Ditambahkan setelah ditemukan bahwa sampul dengan headline terbaca keliru
    # (mis. hanya "TEN" — sisa logo — pada sampul "ANCANG-ANCANG JOKOWI") tetap
    # menghasilkan prediksi berikut persentasenya, tanpa isyarat apa pun bahwa
    # masukannya rusak. Angka yang tampak meyakinkan di atas masukan yang salah
    # lebih menyesatkan daripada tidak ada angka sama sekali.
    if headline is not None:
        kata_headline = [w for w in str(headline).split() if w.strip()]
        if len(kata_headline) < 2 or len(str(headline).strip()) < 8:
            bagian.append({
                "label": "Perhatian: teks judul sangat pendek",
                "asal": "model",
                "teks": (
                    f"Judul yang dianalisis hanya \"{str(headline).strip()}\". "
                    "Teks sependek ini biasanya menandakan pembacaan otomatis "
                    "gagal menangkap judul sampul — misalnya yang terbaca justru "
                    "potongan logo. Model tetap menghasilkan prediksi di bawah, "
                    "tetapi prediksi itu praktis hanya bersandar pada gambar. "
                    "Perbaiki judulnya lalu jalankan ulang agar hasilnya bermakna."
                ),
            })

    # 1. prediksi (model)
    p = pred[task_xai]
    urut2 = p["semua"][1] if len(p["semua"]) > 1 else None
    # Istilah awam dipakai di narasi (revisi 15 Sep, R2). Nama teknisnya tetap
    # tersedia pada tabel prediksi bagi pembaca yang menelusuri metodologi.
    teks_pred = (
        f"Model memprediksi {p.get('nama_task_mudah') or p['nama_task'].split('—')[-1].strip()} = "
        f"{p.get('prediksi_tampil') or tampil(p['prediksi'])} "
        f"dengan keyakinan {p['probabilitas']*100:.1f}%."
    )
    if urut2:
        teks_pred += (f" Pilihan kedua adalah "
                      f"{urut2.get('kelas_tampil') or tampil(urut2['kelas'])} "
                      f"({urut2['prob']*100:.1f}%).")
    if p["probabilitas"] < 0.40:
        teks_pred += (" Keyakinan ini rendah, sehingga prediksinya belum dapat "
                      "dianggap meyakinkan.")
    bagian.append({"label": "Prediksi model", "asal": "model", "teks": teks_pred})

    # 2. kata dominan (model)
    #
    # Revisi 15 Sep (R4): sebelumnya tanda "+" ditulis permanen, sehingga
    # kontribusi negatif tercetak sebagai "+-0.023". Lebih jauh, kata dengan
    # kontribusi negatif tetap disebut "paling menopang keputusan" — padahal
    # nilai negatif berarti kata itu justru MELEMAHKAN kelas terpilih.
    # Kasus nyata: headline "GULA-GULA DEMO BURUH" menghasilkan seluruh kata
    # bernilai negatif, sehingga tidak ada satu pun kata yang menopang.
    if kata:
        urut_kata = sorted(kata, key=lambda x: -x["kontribusi"])
        positif = [x for x in urut_kata if x["kontribusi"] > 0]
        negatif = [x for x in urut_kata if x["kontribusi"] < 0]

        if positif:
            top = positif[0]
            teks_kata = (
                f"Kata paling menopang keputusan adalah \"{top['kata']}\" "
                f"(kontribusi {_tanda(top['kontribusi'])})."
            )
            # Kata kedua hanya disebut bila teksnya berbeda dari kata pertama;
            # headline dapat memuat kata yang sama dua kali (mis. "JANJI TINGGAL JANJI").
            lain = [x for x in positif[1:]
                    if x["kata"].lower() != top["kata"].lower()]
            if lain:
                teks_kata += (f" Disusul \"{lain[0]['kata']}\" "
                              f"({_tanda(lain[0]['kontribusi'])}).")
            if negatif:
                teks_kata += (f" Sebaliknya, \"{negatif[-1]['kata']}\" justru melemahkan "
                              f"keputusan ({_tanda(negatif[-1]['kontribusi'])}).")
        else:
            # Tidak ada kata yang menopang sama sekali. Ini keadaan yang perlu
            # dinyatakan terus terang, bukan disamarkan dengan menyebut kata
            # "paling tidak melemahkan" sebagai penopang.
            paling_ringan = urut_kata[0]
            paling_berat = urut_kata[-1]
            teks_kata = (
                "Tidak ada satu pun kata pada judul yang menopang keputusan ini — "
                f"semuanya justru melemahkan. Yang paling melemahkan adalah "
                f"\"{paling_berat['kata']}\" ({_tanda(paling_berat['kontribusi'])}), "
                f"dan yang paling ringan pengaruhnya \"{paling_ringan['kata']}\" "
                f"({_tanda(paling_ringan['kontribusi'])}). "
                "Artinya keputusan model pada sampul ini tidak bertumpu pada judul, "
                "melainkan pada elemen visual atau teks pendukung."
            )

        teks_kata += (" Angka ini diperoleh dengan menghapus satu kata lalu mengukur "
                      "perubahan probabilitas kelas terpilih: nilai positif berarti "
                      "kata itu menopang, negatif berarti melemahkan.")
        bagian.append({"label": "Kata dominan", "asal": "model", "teks": teks_kata})

    # 3. zona visual dominan (model)
    if cam is not None:
        nama_zona, nilai, semua_zona = zona_dominan(cam)
        rincian = ", ".join(f"{k.split('(')[0].strip()} {v:.3f}"
                            for k, v in semua_zona.items())
        teks_zona = (
            f"Area gambar yang paling memengaruhi keputusan adalah {nama_zona}, "
            f"dengan intensitas rata-rata {nilai:.3f}. Rincian per zona: {rincian}."
        )
        if "kepala" in nama_zona or "kaki" in nama_zona:
            teks_zona += (" Perlu dicatat: area ini didominasi teks dan logo, bukan "
                          "ilustrasi. Bila prediksinya benar, kemungkinan model "
                          "bertumpu pada teks tercetak, bukan pada gambar metaforanya.")
        bagian.append({"label": "Area visual dominan", "asal": "model", "teks": teks_zona})

    # 4. pemetaan makna (anotator) atau definisi domain (codebook)
    kelas_dom = pred.get("task2_domain_sumber", {}).get("prediksi")
    # _bersih dipakai agar nilai NaN yang terbaca sebagai string "nan" tidak
    # ikut tercetak sebagai catatan anotator.
    makna = _bersih(catatan.get("pemetaan_makna")) if catatan else ""
    sumber = _bersih(catatan.get("sumber_metafora")) if catatan else ""
    if makna:
        teks_makna = (
            f"Anotator mencatat sumber metaforanya adalah "
            f"\"{sumber}\", dengan pemetaan makna: {makna}"
        )
        if not teks_makna.rstrip().endswith("."):
            teks_makna += "."
        bagian.append({"label": "Pemetaan makna metafora", "asal": "anotator",
                       "teks": teks_makna})
    elif kelas_dom and kelas_dom in DEFINISI_DOMAIN:
        d = DEFINISI_DOMAIN[kelas_dom]
        bagian.append({
            # Persis judul yang dilingkari dosen pada revisi 15 Sep:
            # "Definisi domain KONSUMSI_TRANSAKSI" -> "Definisi domain Konsumsi & Transaksi".
            "label": f"Definisi domain {tampil(kelas_dom)}",
            "asal": "codebook",
            "teks": f"{d['definisi']} {d['pola']}",
        })

    # 5. verifikasi (gabungan, tetap ditandai)
    #
    # Revisi 15 Sep: blok berlabel GABUNGAN dilaporkan tidak pernah muncul.
    # Dua sebabnya:
    #   (a) pada mode unggahan app.py mengirim catatan=None, sehingga blok ini
    #       selalu dilewati — padahal justru mode itu yang dipakai dosen;
    #   (b) 83 sampul NON_METAFORA punya sumber_metafora bernilai NaN yang
    #       berubah menjadi string "nan" (dianggap truthy), sehingga blok ini
    #       bisa lolos untuk sampul yang justru tidak bermetafora.
    # Keduanya ditangani: blok tetap tampil selama ada peta panas, dengan isi
    # yang menyesuaikan ada-tidaknya catatan anotator.
    if cam is not None:
        nama_zona, _, _ = zona_dominan(cam)
        di_tengah = "tengah" in nama_zona
        punya_catatan = bool(_bersih(catatan.get("sumber_metafora")) if catatan else "")

        if punya_catatan:
            if di_tengah:
                v = ("Area panas berada di bagian tengah, tempat ilustrasi metafora "
                     "biasanya berada. Ini sejalan dengan catatan anotator, sehingga "
                     "keputusan model tampak diambil dari elemen yang tepat.")
            else:
                v = ("Area panas TIDAK berada di bagian tengah, padahal anotator mencatat "
                     "sumber metaforanya ada pada elemen visual. Artinya prediksi model "
                     "bisa benar tetapi dengan alasan yang salah. Temuan seperti ini "
                     "justru penting dilaporkan.")
        else:
            # Tanpa catatan anotator (gambar unggahan, atau sampul tanpa metafora)
            # tidak ada pembanding manusia. Yang masih bisa dinyatakan adalah
            # letak area panasnya — dan itu tetap informasi yang berguna.
            if di_tengah:
                v = ("Area panas berada di bagian tengah, tempat ilustrasi sampul "
                     "biasanya berada. Tidak ada catatan anotator sebagai pembanding "
                     "untuk sampul ini, sehingga kesesuaiannya belum dapat "
                     "diverifikasi terhadap penilaian manusia.")
            else:
                v = ("Area panas berada di luar bagian tengah, yakni pada area yang "
                     "didominasi logo dan teks tercetak. Tidak ada catatan anotator "
                     "sebagai pembanding untuk sampul ini, tetapi pola ini sejalan "
                     "dengan temuan pada dataset: model cenderung bertumpu pada "
                     "kepala sampul, bukan pada ilustrasi metaforanya.")
        bagian.append({"label": "Verifikasi peta panas", "asal": "gabungan", "teks": v})

    return bagian


# --------------------------------------------------------------------------
# Paragraf kesimpulan berbahasa awam (revisi 15 Sep, R3)
#
# Dosen menilai penjelasan naratif di atas "terlalu teknikal buat user", lalu
# meminta "suatu kesimpulan akhir di mana hanya ada paragraf dan mudah di
# pahami user apa yang sebenarnya pesan tersirat yang coba di sampaikan oleh
# sampul itu".
#
# Paragraf ini DIRANGKAI, bukan dihasilkan model bahasa — sama seperti
# penjelasan naratif. Setiap kalimat berasal dari komponen yang sumbernya
# dapat ditunjuk: prediksi model, definisi codebook yang ditulis manusia, atau
# catatan anotator. Tidak ada LLM yang dipakai, sehingga paragraf ini tidak
# mungkin mengarang.
#
# Konsekuensinya paragraf terasa lebih kaku daripada tulisan manusia, dan
# untuk sampul di luar dataset ia hanya dapat menyebut JENIS kiasan, bukan
# makna spesifiknya. Batas ini disebut apa adanya di 02_BATASAN_TEKNIS.md.
#
# Catatan 6 Okt: blok ini adalah implementasi R3 yang lama. Ringkasan yang
# kini tampil di aplikasi disusun explanation_evidence.ringkas(); frasa
# _FRASA_DOMAIN/_MAKSUD_DOMAIN di bawah disalin ke modul itu.
# --------------------------------------------------------------------------

# Cara membaca tiap domain sebagai frasa yang mengalir dalam kalimat.
# Berbeda dari DEFINISI_DOMAIN yang berisi definisi formal.
_FRASA_DOMAIN = {
    "HEWAN_TUBUH": "perumpamaan hewan atau bagian tubuh",
    "PERMAINAN_KONTES": "perumpamaan permainan, pertandingan, atau panggung pertunjukan",
    "MESIN_INFRASTRUKTUR": "perumpamaan mesin, alat, atau bangunan",
    "KONSUMSI_TRANSAKSI": "perumpamaan makanan, uang, atau kegiatan jual-beli",
    "BENCANA_JERAT": "perumpamaan bencana atau jerat",
    "LAINNYA": "perumpamaan yang belum masuk kategori baku",
    "NON_METAFORA": "gambaran apa adanya, tanpa perumpamaan",
}

_MAKSUD_DOMAIN = {
    "HEWAN_TUBUH": "menyoroti sifat rakus, licik, atau memperlakukan pihak tertentu "
                   "sebagai kurang manusiawi",
    "PERMAINAN_KONTES": "menggambarkan politik sebagai sesuatu yang diatur, "
                        "dipertaruhkan, atau dipertontonkan",
    "MESIN_INFRASTRUKTUR": "menggambarkan sistem yang rusak, dikendalikan, atau "
                           "dibongkar-pasang",
    "KONSUMSI_TRANSAKSI": "menyoroti pembagian keuntungan atau pilihan yang "
                          "disodorkan kepada publik",
    "BENCANA_JERAT": "menggambarkan ancaman yang datang, kekacauan, atau "
                     "keterkungkungan",
    "LAINNYA": "menyampaikan kritik lewat kiasan yang masih perlu ditinjau manusia",
}


def _huruf_kecil_aman(teks: str) -> str:
    """Kecilkan huruf untuk disisipkan di tengah kalimat, tetapi jaga akronim.

    `str.lower()` polos merusak akronim yang muncul pada nama kelas, misalnya
    "Ekonomi, Bisnis & BUMN" menjadi "ekonomi, bisnis & bumn". Kata yang
    seluruhnya huruf besar dan panjangnya lebih dari satu dianggap akronim
    dan dibiarkan apa adanya.
    """
    hasil = []
    for w in str(teks).split():
        inti = w.strip(".,;:()")
        if len(inti) > 1 and inti.isupper() and inti.isalpha():
            hasil.append(w)
        else:
            hasil.append(w.lower())
    return " ".join(hasil)


def susun_kesimpulan(pred: dict, kata: list, catatan: dict | None,
                     cam: np.ndarray | None, headline: str | None = None) -> dict:
    """Satu paragraf berbahasa awam tentang apa yang disampaikan sampul.

    Mengembalikan dict berisi:
      paragraf   : teks kesimpulan
      dapat_dipercaya : bool — apakah dasarnya cukup kuat
      alasan_ragu: daftar hal yang melemahkan kesimpulan, bila ada

    Selalu mengembalikan paragraf; bila dasarnya lemah, kelemahan itu
    dinyatakan di dalam paragraf, bukan disembunyikan.

    Catatan 6 Okt: aplikasi web tidak lagi memanggil fungsi ini; ringkasan
    di tab Prediksi disusun `explanation_evidence.ringkas()`.
    """
    p1 = pred.get("task1_issue", {})
    p2 = pred.get("task2_domain_sumber", {})
    p3 = pred.get("task3_primary_entity_type", {})

    isu = p1.get("prediksi_tampil") or tampil(p1.get("prediksi", ""))
    domain_kode = p2.get("prediksi", "")
    entitas = p3.get("prediksi_tampil") or tampil(p3.get("prediksi", ""))

    kalimat = []
    ragu = []

    # --- 1. Apa yang dibicarakan -----------------------------------------
    judul = (headline or "").strip()
    if judul:
        kalimat.append(
            f"Sampul berjudul “{judul}” ini dibaca model sebagai "
            f"pembicaraan tentang {_huruf_kecil_aman(isu)}."
        )
    else:
        kalimat.append(f"Sampul ini dibaca model sebagai pembicaraan tentang "
                       f"{_huruf_kecil_aman(isu)}.")

    # --- 2. Siapa yang disorot -------------------------------------------
    if entitas:
        nama_entitas = _bersih(catatan.get("entitas")) if catatan else ""
        if nama_entitas:
            kalimat.append(
                f"Pihak yang disorot adalah {nama_entitas} "
                f"(termasuk kelompok {_huruf_kecil_aman(entitas)})."
            )
        else:
            kalimat.append(f"Pihak yang disorot termasuk kelompok {_huruf_kecil_aman(entitas)}.")

    # --- 3. Cara menyampaikannya -----------------------------------------
    # Catatan anotator jauh lebih kaya daripada template, jadi diutamakan
    # bila tersedia. Untuk sampul unggahan, jatuh ke frasa domain.
    makna = _bersih(catatan.get("pemetaan_makna")) if catatan else ""
    sumber = _bersih(catatan.get("sumber_metafora")) if catatan else ""

    if makna:
        teks_makna = makna if makna.rstrip().endswith(".") else makna + "."
        if sumber:
            kalimat.append(
                f"Kritiknya disampaikan lewat {_huruf_kecil_aman(sumber)}: {teks_makna}"
            )
        else:
            kalimat.append(f"Makna kiasannya: {teks_makna}")
    elif domain_kode == "NON_METAFORA":
        kalimat.append(
            "Sampul ini dinilai tidak memakai perumpamaan — gambarnya "
            "menyampaikan hal itu apa adanya."
        )
    elif domain_kode in _FRASA_DOMAIN:
        frasa = _FRASA_DOMAIN[domain_kode]
        maksud = _MAKSUD_DOMAIN.get(domain_kode)
        if maksud:
            kalimat.append(
                f"Kritiknya disampaikan lewat {frasa} — pada korpus Tempo, "
                f"kiasan semacam ini umumnya dipakai untuk {maksud}."
            )
        else:
            kalimat.append(f"Kritiknya disampaikan lewat {frasa}.")

    # --- 4. Seberapa kuat dasarnya ---------------------------------------
    prob2 = p2.get("probabilitas", 0.0)
    if prob2 < 0.40:
        ragu.append(f"keyakinan model atas jenis kiasan hanya {prob2*100:.0f}%")

    if kata:
        positif = [x for x in kata if x["kontribusi"] > 0]
        if positif:
            teratas = max(positif, key=lambda x: x["kontribusi"])
            # Revisi 15 Sep hal. 5: dosen meminta judul dikaitkan dengan
            # konteks di bawahnya ("Konteks Key word"), bukan sekadar
            # menyebut kata mana yang paling berpengaruh. Karena itu kata
            # kunci disandingkan langsung dengan isu yang diprediksi.
            kalimat.append(
                f"Kata “{teratas['kata']}” pada judul yang paling "
                f"mengarahkan model ke pembacaan {_huruf_kecil_aman(isu)} itu."
            )
            # Sebutkan juga kata yang justru menarik ke arah berbeda, bila ada
            # dan cukup berarti — sering kali inilah yang mengejutkan pembaca.
            negatif = [x for x in kata if x["kontribusi"] < 0]
            if negatif:
                terbawah = min(negatif, key=lambda x: x["kontribusi"])
                if abs(terbawah["kontribusi"]) >= abs(teratas["kontribusi"]) * 0.5:
                    kalimat.append(
                        f"Sebaliknya kata “{terbawah['kata']}” justru "
                        f"menariknya ke arah lain."
                    )
        else:
            ragu.append("tidak ada satu pun kata pada judul yang menopang "
                        "pembacaan ini")

    if cam is not None:
        nama_zona, _, _ = zona_dominan(cam)
        if "tengah" not in nama_zona:
            ragu.append("bagian gambar yang paling memengaruhi keputusan adalah "
                        "area logo dan teks tercetak, bukan ilustrasinya")

    if ragu:
        kalimat.append(
            "Perlu dicatat: " + "; ".join(ragu) + ". "
            "Karena itu kesimpulan di atas sebaiknya diperiksa ulang oleh "
            "pembaca, bukan diterima begitu saja."
        )
    else:
        kalimat.append(
            "Kata pada judul dan area gambar yang disorot model sejalan dengan "
            "pembacaan di atas."
        )

    return {
        "paragraf": " ".join(kalimat),
        "dapat_dipercaya": not ragu,
        "alasan_ragu": ragu,
        "asal": "anotator" if makna else "gabungan",
    }


def heatmap_overlay(image_path: Path, cam: np.ndarray, out_path: Path,
                    alpha: float = 0.62):
    """Tempelkan peta panas ke gambar asli, simpan sebagai PNG.

    Peta mentah dari ViT biasanya memusat pada sedikit patch dengan ekor
    panjang mendekati nol, sehingga bila dipetakan langsung hampir tak
    terlihat. Karena itu nilai diregangkan memakai peringkat persentil
    sebelum diwarnai — urutan patch tetap sama, hanya kontrasnya dinaikkan.
    """
    img = Image.open(image_path).convert("RGB")
    w, h = img.size

    # Regangkan kontras berbasis peringkat: patch terlemah -> 0, terkuat -> 1,
    # dan sisanya tersebar merata. Mempertahankan urutan, menaikkan keterlihatan.
    datar = cam.flatten()
    urut = datar.argsort().argsort().astype(np.float32)
    if len(datar) > 1:
        peringkat = urut / (len(datar) - 1)
    else:
        peringkat = np.zeros_like(datar)
    camr = peringkat.reshape(cam.shape) ** 1.6   # tekan area lemah

    panas = Image.fromarray((camr * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)
    p = np.asarray(panas).astype(np.float32) / 255.0

    # colormap biru -> hijau -> kuning -> merah, tanpa matplotlib
    r = np.clip(2.0 * p - 0.6, 0, 1)
    g = np.clip(1.6 * (1.0 - np.abs(p - 0.55) * 2.0), 0, 1)
    b = np.clip(1.15 - 2.0 * p, 0, 1)
    warna = np.stack([r, g, b], axis=-1)

    dasar = np.asarray(img).astype(np.float32) / 255.0
    kekuatan = (p[..., None] ** 0.85) * alpha
    hasil = dasar * (1 - kekuatan) + warna * kekuatan
    Image.fromarray((np.clip(hasil, 0, 1) * 255).astype(np.uint8)).save(out_path)
    return out_path
