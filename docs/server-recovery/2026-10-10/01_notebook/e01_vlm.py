"""E01 tahap 1: deskripsi literal ilustrasi (prompt A) dan klasifikasi
zero-shot Task 2 (prompt B) oleh VLM untuk 740 sampul.

Sumber tunggal untuk Kaggle dan uji lokal. Folder kernel Kaggle dibuat oleh
`kaggle_e01/siapkan_kernel.py`, yang hanya mengganti blok KONFIGURASI.
Plan: docs/plans/2026-10-08-e01-vlm-dua-tahap-kaggle.md

Uji lokal (CPU, model kecil):
    venv/bin/python 01_notebook/e01_vlm.py --model Qwen/Qwen3-VL-2B-Instruct \
        --revision 89644892e4d85e24eaac8bacfd4f463576704203 --limit 3 --batch 1 \
        --out 04_hasil_eksperimen/e01_vlm/uji_lokal_cpu
"""
import argparse
import hashlib
import json
import os
import pathlib
import re
import subprocess
import sys
import threading
import time
import traceback
import zipfile

# --- KONFIGURASI (diganti siapkan_kernel.py) ---
MODEL_ID = "Qwen/Qwen3-VL-8B-Instruct"
MODEL_REVISION = "0c351dd01ed87e9c1b53cbc748cba10e6187ff3b"
LIMIT = 0  # 0 = seluruh 740 sampul
BATCH = 4
BATAS_MENIT = 40  # tenggat internal; run berhenti rapi dan output tetap tersimpan
RESUME_SOURCE = ""  # folder /kaggle/input berisi deskripsi.jsonl/zeroshot.jsonl lama
# --- akhir KONFIGURASI ---

MAX_SISI = 1024  # sisi terpanjang gambar sebelum masuk processor (piksel)
MAX_TOKEN_A = 220
MAX_TOKEN_B = 260
KAGGLE = pathlib.Path("/kaggle/input").exists()

PROMPT_A = (
    "Ini sampul Majalah Tempo. Deskripsikan secara literal ilustrasi utamanya dalam "
    "2-4 kalimat bahasa Indonesia: tokoh, hewan, benda, tindakan, latar, dan simbol "
    "visual yang tampak beserta hubungan di antaranya. Abaikan logo majalah, tanggal, "
    "harga, barcode, dan semua tulisan. Jangan menafsirkan makna politiknya dan jangan "
    "menyebut nama tokoh, cukup gambarkan apa yang terlihat."
)

# Definisi, kriteria, dan pembeda dari docs/CODEBOOK_OPERASIONAL.md (5 Okt 2026).
# Contoh dataset di codebook sengaja tidak dimasukkan agar evaluasi tidak bocor.
CODEBOOK_TASK2 = """\
MESIN_INFRASTRUKTUR: Domain sumber berupa mesin, alat kerja, kendaraan, bangunan, infrastruktur, atau mekanisme buatan. Kriteria: ada pemetaan dari fungsi, kerusakan, pengendalian, atau kerja alat/struktur ke isu sasaran. Pembeda: alat yang tampil literal tidak otomatis metafora; alat transaksi/permainan dipilah menurut mekanisme pemetaan dominan.
PERMAINAN_KONTES: Domain sumber berupa permainan, pertandingan, kompetisi, atau panggung pertunjukan sebagai arena berstrategi. Kriteria: pemetaan memakai menang-kalah, aturan main, pemain, peran, panggung, atau pengaturan pertunjukan. Pembeda: persaingan politik literal bukan metafora; perlu sumber metaforis.
BENCANA_JERAT: Domain sumber berupa bencana, ancaman, jerat, perangkap, atau keadaan fisik terjepit. Kriteria: pemetaan memakai bahaya, kehancuran, terperangkap, atau tekanan ruang sebagai sumber makna. Pembeda: bencana aktual tanpa pemetaan dapat NON_METAFORA; bagian tubuh dalam jerat dipilah menurut mekanisme dominan.
HEWAN_TUBUH: Domain sumber berupa hewan, bagian tubuh, atau bentuk dan perilaku biologis. Kriteria: sifat hewan, anatomi, deformasi, atau perilaku tubuh dipetakan ke tokoh atau persoalan. Pembeda: potret manusia atau hewan literal tidak cukup; jika konsumsi tumpang tindih, pilih mekanisme dominan.
KONSUMSI_TRANSAKSI: Domain sumber berupa makanan, jamuan, selera, jual-beli, pembayaran, atau pertukaran keuntungan. Kriteria: ada pemetaan dari makan, memilih hidangan, berbagi jatah, atau pertukaran nilai ke persoalan sasaran. Pembeda: makanan atau uang literal tidak otomatis metafora; jika hewan merupakan sumber utama, pertimbangkan HEWAN_TUBUH.
NON_METAFORA: Sampul tanpa pemetaan metaforis visual-verbal. Kriteria: elemen dipahami secara literal dan tidak ada hubungan sumber-sasaran metaforis yang cukup. Pembeda: ketidakpastian pembaca bukan bukti tanpa metafora.
LAINNYA: Domain sumber metafora yang tidak tercakup lima domain positif lainnya. Kriteria: metafora teridentifikasi tetapi mekanisme sumbernya tidak cocok dengan kategori yang tersedia. Pembeda: berbeda dari NON_METAFORA karena tetap ada pemetaan metaforis; jangan dipakai sebagai tempat semua kasus ambigu."""
KELAS_TASK2 = [baris.split(":")[0] for baris in CODEBOOK_TASK2.splitlines()]


def prompt_b(judul, pendukung):
    return (
        "Ini sampul Majalah Tempo.\n"
        f"Judul utama: {judul}\n"
        f"Teks pendukung: {pendukung or '-'}\n\n"
        "Tentukan domain sumber metafora visual-verbal sampul ini, yaitu dari ranah apa "
        "kiasan gambarnya diambil (bukan isu yang dibahas). Pilih tepat satu kode:\n"
        f"{CODEBOOK_TASK2}\n\n"
        "Jawab hanya dengan JSON satu baris: "
        '{"sumber_visual": "<benda/adegan yang menjadi sumber kiasan>", '
        '"domain": "<KODE>", "alasan": "<satu kalimat>"}'
    )


def sha256(data):
    return hashlib.sha256(data if isinstance(data, bytes) else data.encode()).hexdigest()


def cari_data(csv_arg, gambar_arg):
    if csv_arg:
        csv = pathlib.Path(csv_arg)
        return csv, pathlib.Path(gambar_arg) if gambar_arg else csv.parents[1] / "05_gambar"
    # Pola sama dengan kernel lama: dataset bisa ter-mount apa adanya atau sebagai ZIP.
    masukan = pathlib.Path("/kaggle/input")
    calon = list(masukan.rglob("DATASET_740_TASK2_DOMAIN.csv"))
    if not calon:
        tujuan = pathlib.Path("/kaggle/working/input_extracted")
        for arsip in masukan.rglob("tempo_benchmark_input.zip"):
            with zipfile.ZipFile(arsip) as z:
                z.extractall(tujuan)
        calon = list(tujuan.rglob("DATASET_740_TASK2_DOMAIN.csv"))
    if len(calon) != 1:
        raise RuntimeError(f"Harus tepat satu CSV dataset, ditemukan {len(calon)}")
    return calon[0], calon[0].parents[1] / "05_gambar"


def parse_b(teks):
    """Ambil kode domain dari jawaban JSON; fallback ke kode pertama yang disebut."""
    hasil = {"domain": None, "sumber_visual": None, "alasan": None, "json_valid": False}
    m = re.search(r"\{.*\}", teks, re.S)
    if m:
        try:
            obj = json.loads(m.group(0))
            hasil.update({k: obj.get(k) for k in ("domain", "sumber_visual", "alasan")})
            hasil["json_valid"] = True
        except json.JSONDecodeError:
            pass
    domain = str(hasil["domain"] or "").strip().upper()
    if domain not in KELAS_TASK2:
        sebut = [(teks.upper().find(k), k) for k in KELAS_TASK2 if k in teks.upper()]
        domain = min(sebut)[1] if sebut else None
    hasil["domain"] = domain
    return hasil


def rusak(teks):
    """Gejala umum overflow fp16: keluaran kosong atau deret tanda baca berulang."""
    t = teks.strip()
    return len(t) < 15 or bool(re.search(r"(.)\1{9,}", t))


def baca_selesai(path):
    if not path.exists():
        return set()
    return {json.loads(b)["sample_id"] for b in path.read_text().splitlines() if b.strip()}




def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default=MODEL_ID)
    ap.add_argument("--revision", default=MODEL_REVISION)
    ap.add_argument("--limit", type=int, default=LIMIT)
    ap.add_argument("--batch", type=int, default=BATCH)
    ap.add_argument("--batas-menit", type=float, default=BATAS_MENIT)
    ap.add_argument("--data-csv", default="")
    ap.add_argument("--gambar", default="")
    ap.add_argument("--out", default="/kaggle/working/e01_vlm" if KAGGLE else "")
    ap.add_argument("--uji-watchdog", action="store_true",
                    help="uji lokal tanpa model: tidur sampai tenggat agar watchdog terpicu")
    args = ap.parse_args()
    if not args.out:
        ap.error("--out wajib di luar Kaggle")

    mulai_run = time.perf_counter()
    tenggat = mulai_run + args.batas_menit * 60
    out = pathlib.Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    f_log, f_a, f_b = out / "tahap.log", out / "deskripsi.jsonl", out / "zeroshot.jsonl"
    meta = {"eksperimen": "E01 tahap 1", "model": args.model, "revision": args.revision,
            "batch": args.batch, "limit": args.limit, "batas_menit": args.batas_menit,
            "max_sisi": MAX_SISI, "decoding": "greedy", "tahap_detik": {}}
    kunci = threading.Lock()

    def catat(pesan):
        baris = f"{time.strftime('%H:%M:%S')} +{time.perf_counter() - mulai_run:7.1f}s {pesan}"
        print(baris, flush=True)
        with kunci, f_log.open("a") as f:
            f.write(baris + "\n")

    def tahap(nama, t_mulai):
        meta["tahap_detik"][nama] = round(time.perf_counter() - t_mulai, 1)
        catat(f"selesai: {nama} ({meta['tahap_detik'][nama]} dtk)")

    def tulis_meta(status):
        baca = lambda f: [json.loads(b) for b in f.read_text().splitlines() if b.strip()] if f.exists() else []
        hasil_a, hasil_b = baca(f_a), baca(f_b)
        detik = meta.get("detik_per_sampel", [])
        meta.update({
            "status": status,
            "jumlah_deskripsi": len(hasil_a), "jumlah_zeroshot": len(hasil_b),
            "deskripsi_rusak": sum(h["rusak"] for h in hasil_a),
            "zeroshot_tanpa_label": sum(h["domain"] is None for h in hasil_b),
            "zeroshot_json_tidak_valid": sum(not h["json_valid"] for h in hasil_b),
            "rata_detik_per_sampel_run_ini": round(sum(detik) / len(detik), 2) if detik else None,
            "estimasi_jam_740_sampel": round(sum(detik) / len(detik) * 740 / 3600, 2) if detik else None,
            "total_detik_run": round(time.perf_counter() - mulai_run, 1),
        })
        if meta.get("sampel_target") is not None:
            meta["selesai"] = len(hasil_a) == meta["sampel_target"] == len(hasil_b)
        with kunci:
            (out / "meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False))

    def watchdog():
        # Cadangan bila hang di pip/unduhan/generate: tutup rapi agar Kaggle menyimpan output.
        sisa = tenggat - time.perf_counter()
        if sisa > 0:
            time.sleep(sisa)
        catat(f"WAKTU HABIS ({args.batas_menit} menit); tahap terakhir di atas adalah tempat run berhenti")
        tulis_meta("waktu_habis")
        os._exit(0)

    threading.Thread(target=watchdog, daemon=True).start()
    catat(f"mulai; tenggat {args.batas_menit} menit")
    try:
        jalankan(args, out, f_a, f_b, meta, catat, tahap, tenggat)
        tulis_meta("selesai" if meta.get("selesai_loop") else "berhenti_sebelum_tenggat")
        catat("run berakhir normal")
    except Exception:
        # Keluar normal (bukan crash) supaya Kaggle tetap menyimpan tahap.log dan meta.json.
        catat("GAGAL:\n" + traceback.format_exc())
        tulis_meta("gagal")
    print((out / "meta.json").read_text(), flush=True)


def jalankan(args, out, f_a, f_b, meta, catat, tahap, tenggat):
    if args.uji_watchdog:
        catat("uji watchdog: tidur sampai tenggat")
        time.sleep(10**6)

    if KAGGLE:
        t = time.perf_counter()
        subprocess.run([sys.executable, "-m", "pip", "install", "-q",
                        "transformers==5.17.0", "accelerate"], check=True, timeout=900)
        tahap("pip install", t)
    import pandas as pd
    import torch
    from huggingface_hub import snapshot_download
    from PIL import Image
    from transformers import AutoModelForImageTextToText, AutoProcessor

    csv, dir_gambar = cari_data(args.data_csv, args.gambar)
    if RESUME_SOURCE:
        for nama in ("deskripsi.jsonl", "zeroshot.jsonl"):
            sumber = pathlib.Path(RESUME_SOURCE) / nama
            if sumber.exists() and not (out / nama).exists():
                (out / nama).write_bytes(sumber.read_bytes())

    df = pd.read_csv(csv).fillna("")
    if args.limit:
        df = df.head(args.limit)
    sisa = df[~df.sample_id.isin(baca_selesai(f_a) & baca_selesai(f_b))]

    cuda = torch.cuda.is_available()
    meta.update({
        "dtype": "float16" if cuda else "float32",
        "gpu": [torch.cuda.get_device_name(i) for i in range(torch.cuda.device_count())],
        "torch": torch.__version__,
        "data_csv_sha256": sha256(csv.read_bytes()),
        "prompt_a_sha256": sha256(PROMPT_A),
        "prompt_b_sha256": sha256(prompt_b("{judul}", "{pendukung}")),
        "sampel_target": len(df), "sampel_sudah_ada_saat_mulai": len(df) - len(sisa),
    })
    catat(f"data: {len(df)} sampel, {len(sisa)} belum diproses; GPU {meta['gpu']}; torch {torch.__version__}")

    t = time.perf_counter()
    snapshot_download(args.model, revision=args.revision)
    tahap("unduh bobot", t)

    t = time.perf_counter()
    processor = AutoProcessor.from_pretrained(args.model, revision=args.revision)
    processor.tokenizer.padding_side = "left"
    if cuda:
        # Hanya GPU di max_memory: lapisan yang tidak muat tidak boleh diam-diam pindah ke CPU/disk.
        n_gpu = torch.cuda.device_count()
        model = AutoModelForImageTextToText.from_pretrained(
            args.model, revision=args.revision, dtype=torch.float16,
            device_map="auto", max_memory={i: "14GiB" for i in range(n_gpu)}).eval()
        peta = getattr(model, "hf_device_map", {}) or {}
        lokasi = sorted({str(v) for v in peta.values()})
        meta["lokasi_lapisan"] = lokasi
        meta["memori_gpu_gib"] = [round(torch.cuda.memory_allocated(i) / 2**30, 2) for i in range(n_gpu)]
        catat(f"lokasi lapisan {lokasi}; memori GPU {meta['memori_gpu_gib']} GiB")
        if any(v in ("cpu", "disk") for v in lokasi):
            raise RuntimeError(f"Sebagian model di-offload ke {lokasi}; model tidak muat di GPU")
    else:
        model = AutoModelForImageTextToText.from_pretrained(
            args.model, revision=args.revision, dtype=torch.float32).eval()
    tahap("muat model", t)

    def gambar(row):
        img = Image.open(dir_gambar / pathlib.Path(row.image_path).name).convert("RGB")
        img.thumbnail((MAX_SISI, MAX_SISI))
        return img

    @torch.inference_mode()
    def generate(images, prompts, max_token):
        pesan = [[{"role": "user", "content": [{"type": "image", "image": im},
                                               {"type": "text", "text": p}]}]
                 for im, p in zip(images, prompts)]
        inputs = processor.apply_chat_template(
            pesan, tokenize=True, add_generation_prompt=True, return_dict=True,
            return_tensors="pt", padding=True).to(model.device)
        keluaran = model.generate(**inputs, max_new_tokens=max_token, do_sample=False)
        baru = keluaran[:, inputs["input_ids"].shape[1]:]
        return processor.batch_decode(baru, skip_special_tokens=True)

    n_rusak, n_proses = 0, 0
    detik = meta.setdefault("detik_per_sampel", [])
    rows = list(sisa.itertuples())
    for mulai in range(0, len(rows), args.batch):
        # Berhenti rapi bila sisa waktu tidak cukup untuk satu batch lagi (perkiraan 1,5x batch terakhir).
        if detik and time.perf_counter() + 1.5 * detik[-1] * args.batch > tenggat - 60:
            catat(f"berhenti sebelum tenggat setelah {n_proses} sampel; lanjutkan dengan RESUME_SOURCE")
            return
        bagian = rows[mulai:mulai + args.batch]
        t = time.perf_counter()
        images = [gambar(r) for r in bagian]
        teks_a = generate(images, [PROMPT_A] * len(bagian), MAX_TOKEN_A)
        teks_b = generate(images, [prompt_b(r.headline_verified, r.supporting_text_verified)
                                   for r in bagian], MAX_TOKEN_B)
        dt = time.perf_counter() - t
        with f_a.open("a") as fa, f_b.open("a") as fb:
            for r, a, b in zip(bagian, teks_a, teks_b):
                fa.write(json.dumps({"sample_id": r.sample_id, "deskripsi": a.strip(),
                                     "rusak": rusak(a)}, ensure_ascii=False) + "\n")
                fb.write(json.dumps({"sample_id": r.sample_id, "jawaban": b.strip(),
                                     **parse_b(b), "rusak": rusak(b)}, ensure_ascii=False) + "\n")
                n_rusak += rusak(a) + rusak(b)
        n_proses += len(bagian)
        detik.append(round(dt / len(bagian), 2))
        catat(f"batch [{n_proses}/{len(rows)}] {dt / len(bagian):.1f} dtk/sampel, keluaran rusak={n_rusak}")
        # Berhenti cepat bila keluaran rusak massal (mis. overflow fp16) agar kuota GPU tidak habis.
        if n_proses >= 8 and n_rusak > n_proses:
            raise RuntimeError(f"Keluaran rusak {n_rusak} dari {2 * n_proses}; periksa dtype")
    meta["selesai_loop"] = True


if __name__ == "__main__":
    main()
