"""Deterministic explanations bound to the current task and class."""
from label_display import nama_task, tampil


def explain(pred, task, words, annotation, cam, headline, definitions, zone):
    p = pred[task]
    label = p.get("prediksi_tampil") or tampil(p["prediksi"])
    evidence = [{"id": "prediction", "source": "MODEL", "task_id": task,
                 "class_id": p["prediksi"], "probability": p["probabilitas"]}]
    positive = sorted((w for w in words if w["kontribusi"] > 0), key=lambda w: -w["kontribusi"])
    negative = sorted((w for w in words if w["kontribusi"] < 0), key=lambda w: w["kontribusi"])
    if words:
        evidence.append({"id": "words", "source": "MODEL", "task_id": task,
                         "class_id": p["prediksi"], "values": words})
    visual = zone(cam)[0].split(" (")[0] if cam is not None else None
    if visual:
        evidence.append({"id": "visual", "source": "MODEL", "task_id": task,
                         "class_id": p["prediksi"], "zone": visual})
    definition = definitions.get(p["prediksi"])
    if definition:
        evidence.append({"id": "definition", "source": "CODEBOOK", "task_id": task,
                         "class_id": p["prediksi"], "value": definition,
                         "reference": "Codebook operasional proyek; definisi disusun atas instruksi user, bukan sumber resmi dosen"})
    annotation = annotation or {}
    notes = {k: str(v).strip() for k,v in annotation.items() if v is not None and str(v).strip().lower() not in ("", "nan", "none")}
    if notes:
        evidence.append({"id": "annotation", "source": "ANOTATOR", "value": notes})
    limitations = []
    if not headline or len(headline.split()) < 2:
        limitations.append("Headline pendek atau belum lengkap; periksa teks final.")
    if not positive:
        limitations.append("Tidak ada kata dengan kontribusi positif untuk kelas yang dijelaskan.")
    if visual and "tengah" not in visual:
        limitations.append("Zona dominan berada di luar tengah sampul; posisi saja tidak mengidentifikasi logo, teks atau ilustrasi.")
    if p["probabilitas"] < .4:
        limitations.append("Skor kelas rendah menurut aturan demo; skor ini belum dikalibrasi.")
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
    text = [f"Untuk {nama_task(task)}, model memprediksi {label} (skor {p['probabilitas']*100:.1f}%)."]
    if strategy == "perbandingan_anotasi":
        text.append("Catatan manusia pada sampel ini tersedia untuk dibandingkan; catatan tersebut bukan atribusi model.")
    if positive:
        text.append(f"Kata ‘{positive[0]['kata']}’ mendukung kelas {label} pada task ini.")
    if negative:
        text.append(f"Kata ‘{negative[0]['kata']}’ menurunkan skor kelas tersebut pada metode atribusi yang dipakai.")
    if visual:
        text.append(f"Bukti visual untuk task ini paling kuat pada {visual}; zona ini tidak mengidentifikasi objek.")
    if definition:
        d = definition if isinstance(definition,str) else definition.get("definisi", definition.get("arti", ""))
        if d: text.append(f"Definisi kelas dalam referensi demo: {d}")
    # Ordering reflects evidence availability, rather than random paraphrasing.
    if strategy == "bukti_visual" and visual:
        region = next((x for x in text if x.startswith("Bukti visual")), None)
        if region: text.remove(region); text.insert(1, region)
    if strategy == "penjelasan_kelas" and definition:
        definition_text = next((x for x in text if x.startswith("Definisi kelas")), None)
        if definition_text: text.remove(definition_text); text.insert(1, definition_text)
    text.extend(limitations)
    text.append("Periksa headline final dan bukti di atas; definisi kelas atau catatan manusia tidak membuktikan prediksi benar.")
    return {"paragraf":" ".join(text), "dapat_dipercaya":not limitations,
            "alasan_ragu":limitations, "strategi":strategy, "task_id":task,
            "class_id":p["prediksi"], "bukti":evidence,
            "asal":"GABUNGAN" if len({e["source"] for e in evidence})>1 else "MODEL"}
