"""Deterministic explanations bound to evidence (no language model).

Dua keluaran untuk pembaca:
- `ringkas()`  — ringkasan awam ketiga task (tab Prediksi).
- `explain()`  — alasan untuk task/kelas pilihan (tab Penjelasan), dengan
  bukti, asal tiap blok, dan daftar "Yang perlu dicek".
Setiap kalimat berasal dari prediksi/atribusi model, definisi codebook, atau
catatan anotator; tidak ada teks yang dikarang.
"""
from label_display import nama_task, tampil

# Frasa awam jenis kiasan dan maksud umumnya. Disalin dari `_FRASA_DOMAIN` dan
# `_MAKSUD_DOMAIN` di xai_core.py (ditulis manusia dari 657 catatan pemetaan
# makna); disalin agar modul ini tidak memuat torch/model saat diimpor.
FRASA_DOMAIN = {
    "HEWAN_TUBUH": "perumpamaan hewan atau bagian tubuh",
    "PERMAINAN_KONTES": "perumpamaan permainan, pertandingan, atau panggung pertunjukan",
    "MESIN_INFRASTRUKTUR": "perumpamaan mesin, alat, atau bangunan",
    "KONSUMSI_TRANSAKSI": "perumpamaan makanan, uang, atau kegiatan jual-beli",
    "BENCANA_JERAT": "perumpamaan bencana atau jerat",
    "LAINNYA": "perumpamaan yang belum masuk kategori baku",
}
MAKSUD_DOMAIN = {
    "HEWAN_TUBUH": "menyoroti sifat rakus, licik, atau memperlakukan pihak tertentu sebagai kurang manusiawi",
    "PERMAINAN_KONTES": "menggambarkan politik sebagai sesuatu yang diatur, dipertaruhkan, atau dipertontonkan",
    "MESIN_INFRASTRUKTUR": "menggambarkan sistem yang rusak, dikendalikan, atau dibongkar-pasang",
    "KONSUMSI_TRANSAKSI": "menyoroti pembagian keuntungan atau pilihan yang disodorkan kepada publik",
    "BENCANA_JERAT": "menggambarkan ancaman yang datang, kekacauan, atau keterkungkungan",
    "LAINNYA": "menyampaikan kritik lewat kiasan yang masih perlu ditinjau manusia",
}
# Parafrasa awam nama kelas Task 3 (tidak menambah klaim di luar nama kelas).
FRASA_PIHAK = {
    "individual": "seorang tokoh",
    "government": "pemerintah",
    "multiple_or_other": "beberapa pihak atau pihak lain",
    "civil_society_or_media": "masyarakat sipil atau media",
    "business": "pelaku usaha",
    "judiciary_or_law_enforcement": "lembaga peradilan atau penegak hukum",
    "political_party": "partai politik",
    "legislature": "lembaga legislatif",
}
ZONA_AWAM = {
    "kepala": "bagian atas sampul (area logo dan judul kecil)",
    "tengah": "bagian tengah sampul, tempat ilustrasi biasanya berada",
    "kaki": "bagian bawah sampul (area judul besar dan barcode)",
}
T1, T2, T3 = "task1_issue", "task2_domain_sumber", "task3_primary_entity_type"


def _kecil(teks):
    """Huruf kecil untuk di tengah kalimat; akronim (BUMN) tetap, '&' jadi 'dan'."""
    kata = []
    for w in str(teks).replace(" & ", " dan ").split():
        inti = w.strip(".,;:()")
        kata.append(w if len(inti) > 1 and inti.isupper() and inti.isalpha() else w.lower())
    return " ".join(kata)


def _daftar(items):
    items = [x for x in items if x]
    return items[0] if len(items) == 1 else ", ".join(items[:-1]) + " dan " + items[-1] if items else ""


def _kata(ws):
    """Daftar kata berkutip tunggal: tanpa kata kembar dan tanpa kutip ganda ("‘'Suap'’")."""
    hasil, sudah = [], set()
    for w in ws:
        k = str(w["kata"]).strip("'\"‘’“” ")
        if k and k.upper() not in sudah:
            sudah.add(k.upper())
            hasil.append(f"‘{k}’")
    return _daftar(hasil)


# Catatan anotator milik task tertentu (tanpa klaim lintas task, audit 6 Okt).
CATATAN_TASK = {"task1_issue": (), "task2_domain_sumber": ("sumber_metafora", "pemetaan_makna"),
                "task3_primary_entity_type": ("entitas",)}


def _ada(v):
    return v is not None and str(v).strip().lower() not in ("", "nan", "none")


def _persen(p):
    return f"{p*100:.1f}".replace(".", ",") + "%"


def _zona(nama):
    if not nama:
        return None
    for kunci, teks in ZONA_AWAM.items():
        if kunci in nama:
            return kunci, teks
    return None, nama


def _isu(kelas):
    return "isu di luar kategori utama" if kelas == "other_issue" else _kecil(tampil(kelas))


def ringkas(pred, headline, label=None, catatan=None):
    """Ringkasan awam tiga task. `label`/`catatan` hanya ada di mode dataset."""
    p1, p2, p3 = pred[T1], pred[T2], pred[T3]
    judul = f"sampul “{headline}”" if headline else "sampul ini"
    model = [f"Menurut model, {judul} kemungkinan membahas {_isu(p1['prediksi'])}, "
             f"dengan sorotan pada {FRASA_PIHAK.get(p3['prediksi'], _kecil(tampil(p3['prediksi'])))}."]
    dom = p2["prediksi"]
    if dom == "NON_METAFORA":
        model.append("Sampul ini dibaca sebagai gambaran apa adanya, tanpa kiasan.")
    else:
        model.append(f"Kiasannya dibaca sebagai {FRASA_DOMAIN.get(dom, _kecil(tampil(dom)))}"
                     + (f" — kiasan semacam ini biasanya {MAKSUD_DOMAIN[dom]}." if dom in MAKSUD_DOMAIN else "."))
    # Scores of different model families cannot be interpreted as joint confidence.
    keyakinan, tanda = "belum_dikalibrasi", "Prediksi model — periksa bukti dan label pembanding"
    model.append("Skor ketiga task belum dikalibrasi sebagai peluang benar. Besar skor antar-task tidak dapat dibandingkan sebagai keyakinan.")
    bagian = [{"asal": "MODEL", "teks": " ".join(model)}]
    ada_label = [t for t in (T1, T2, T3) if label and _ada(label.get(t))]
    if ada_label:
        beda = [t for t in ada_label if label[t] != pred[t]["prediksi"]]
        if not beda:
            teks = ["Pembacaan ini sejalan dengan label anotator untuk ketiga aspek." if len(ada_label) == 3 else
                    "Pembacaan ini sejalan dengan label anotator untuk "
                    + _daftar([_kecil(nama_task(t)) for t in ada_label]) + "."]
        else:
            teks = ["Anotator membacanya lain untuk " + _daftar(
                [f"{_kecil(nama_task(t))} ({tampil(label[t])})" for t in beda]) + "."]
        makna = (catatan or {}).get("pemetaan_makna")
        if makna and str(makna).strip().lower() not in ("", "nan", "none"):
            teks.append(f"Catatan anotator: “{str(makna).strip()}”")
        bagian.append({"asal": "ANOTATOR", "teks": " ".join(teks)})
    return {"paragraf": " ".join(b["teks"] for b in bagian), "bagian": bagian,
            "keyakinan": keyakinan, "tanda": tanda}


def explain(pred, task, words, annotation, cam, headline, definitions, zone, label=None):
    p = pred[task]
    kelas = p.get("prediksi_tampil") or tampil(p["prediksi"])
    evidence = [{"id": "prediction", "source": "MODEL", "task_id": task,
                 "class_id": p["prediksi"], "score": p["probabilitas"], "score_kind": p.get("score_kind", "softmax_uncalibrated"), "model_version": p.get("model_version", "baseline-mtl-v1")}]
    positive = sorted((w for w in words if w["kontribusi"] > 0), key=lambda w: -w["kontribusi"])
    negative = sorted((w for w in words if w["kontribusi"] < 0), key=lambda w: w["kontribusi"])
    if words:
        evidence.append({"id": "words", "source": "MODEL", "task_id": task,
                         "class_id": p["prediksi"], "values": words})
    # Peta datar (semua nilai sama) tidak boleh diklaim punya zona dominan.
    datar = cam is not None and hasattr(cam, "max") and float(cam.max() - cam.min()) <= 1e-9
    visual = zone(cam)[0].split(" (")[0] if cam is not None and not datar else None
    if visual:
        evidence.append({"id": "visual", "source": "MODEL", "task_id": task,
                         "class_id": p["prediksi"], "zone": visual})
    definition = definitions.get(p["prediksi"])
    if definition:
        evidence.append({"id": "definition", "source": "CODEBOOK", "task_id": task,
                         "class_id": p["prediksi"], "value": definition,
                         "reference": "Codebook operasional proyek; definisi disusun atas instruksi user, bukan sumber resmi dosen"})
    annotation = annotation or {}
    milik = CATATAN_TASK.get(task, tuple(annotation))
    notes = {k: str(v).strip() for k, v in annotation.items() if k in milik and _ada(v)}
    if notes:
        evidence.append({"id": "annotation", "source": "ANOTATOR", "task_id": task, "value": notes})
    zona = _zona(visual)
    limitations = []
    if not headline or len(headline.split()) < 2:
        limitations.append("Judul pendek atau belum lengkap — periksa teks final.")
    if not positive:
        limitations.append("Tidak ada kata dengan kontribusi positif untuk kelas yang dijelaskan.")
    if visual and "tengah" not in visual:
        limitations.append("Model paling banyak melihat di luar bagian tengah sampul, jadi alasannya belum tentu berasal dari ilustrasi; posisi saja tidak menunjukkan objek apa yang dilihat.")
    if p["probabilitas"] < .4:
        limitations.append(f"Skor {_persen(p['probabilitas'])} tergolong rendah, dan skor model belum dikalibrasi sebagai peluang benar.")
    if limitations:
        strategy = "bukti_gabungan_terbatas"
    elif positive and visual:
        strategy = "bukti_gabungan_terbatas"
    elif positive:
        strategy = "bukti_teks"
    elif visual:
        strategy = "bukti_visual"
    elif notes:
        strategy = "perbandingan_anotasi"
    else:
        strategy = "penjelasan_kelas"
    # Missing words is a limitation, but should not hide valid visual/annotation evidence.
    if len(limitations) == 1 and not positive and headline and len(headline.split()) >= 2 and p["probabilitas"] >= .4:
        strategy = "bukti_visual" if visual else ("perbandingan_anotasi" if notes else "penjelasan_kelas")

    # Blok "Mengapa <kelas>?" — kata lalu gambar; urutan mengikuti bukti yang ada.
    alasan = []
    if positive:
        s = f"Dari judul, kata {_kata(positive[:2])} paling mendorong pilihan ini"
        s += f", sedangkan {_kata(negative[:1])} justru menariknya ke arah lain." if negative else "."
        alasan.append(s)
    elif negative:
        alasan.append(f"Tidak ada kata di judul yang mendorong pilihan ini; {_kata(negative[:2])} justru "
                      "sedikit menjauhkannya. Keputusan kemungkinan lebih bersandar pada gambar dan teks pendukung.")
    if zona:
        s = f"Di gambar, area yang paling berpengaruh ada di {zona[1]}"
        s += "." if zona[0] == "tengah" else ", bukan di bagian tengah tempat ilustrasi biasanya berada."
        alasan.insert(0, s) if strategy == "bukti_visual" else alasan.append(s)
    if not alasan:
        alasan.append("Bukti kata dan gambar untuk pilihan ini tidak tersedia.")
    blok = [{"label": f"Mengapa {kelas}?", "asal": "MODEL",
             "teks": f"Untuk {nama_task(task).lower()}, model memilih {kelas} (skor {_persen(p['probabilitas'])}). " + " ".join(alasan)}]
    if definition:
        d = definition if isinstance(definition, str) else definition.get("definisi", definition.get("arti", ""))
        if d:
            blok.append({"label": "Arti kelas ini", "asal": "CODEBOOK",
                         "teks": f"Dalam referensi demo, {kelas} berarti: "
                                 f"{d if len(d) > 1 and d[1].isupper() else d[0].lower() + d[1:]}"})
    label_task = label.get(task) if label and _ada(label.get(task)) else None
    if notes or label_task:
        bagian = []
        kutip = lambda k: notes[k].rstrip(" .")
        if notes.get("sumber_metafora"):
            bagian.append(f"sumber kiasannya “{kutip('sumber_metafora')}”")
        if notes.get("pemetaan_makna"):
            bagian.append(f"maknanya “{kutip('pemetaan_makna')}”")
        if notes.get("entitas"):
            bagian.append(f"pihak yang disorot “{kutip('entitas')}”")
        teks = "Anotator mencatat " + _daftar(bagian) + "." if bagian else ""
        if label_task:
            teks += (f" Label anotator untuk aspek ini sama: {tampil(label[task])}." if label[task] == p["prediksi"]
                     else f" Label anotator untuk aspek ini berbeda: {tampil(label[task])}.")
        if teks.strip():
            blok.append({"label": "Catatan anotator", "asal": "ANOTATOR", "teks": teks.strip()})
        if strategy == "perbandingan_anotasi":
            blok.insert(1, blok.pop())
    if label_task and label_task != p["prediksi"]:
        limitations.append(f"Label anotator berbeda ({tampil(label[task])}).")
    paragraf = " ".join(b["teks"] for b in blok)
    if limitations:
        paragraf += " Yang perlu dicek: " + " ".join(limitations)
    return {"paragraf": paragraf, "blok": blok, "cek": limitations,
            "dapat_dipercaya": not limitations, "alasan_ragu": limitations,
            "strategi": strategy, "task_id": task, "class_id": p["prediksi"], "bukti": evidence,
            "asal": "GABUNGAN" if len({e["source"] for e in evidence}) > 1 else "MODEL"}
