#!/usr/bin/env python3
"""Audit data/E42 dan buat paket review OCR tanpa mengubah label."""
import csv, hashlib, json
from collections import Counter, defaultdict
from pathlib import Path
from sklearn.metrics import classification_report, confusion_matrix, f1_score

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "03_data/DATASET_740_TASK2_DOMAIN.csv"
OOF = ROOT / "04_hasil_eksperimen/e42_tail_grid/oof.csv"
OCR = ROOT / "04_hasil_eksperimen/revisi_week3/ocr_final_holdout/results.json"
OUT = ROOT / "04_hasil_eksperimen/audit_targets_20261017"
DOCS = ROOT.parent / "docs"
TASKS = ["task1_issue", "task2_domain_sumber", "task3_primary_entity_type"]

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as f: return list(csv.DictReader(f))

rows, oof = read_csv(DATA), read_csv(OOF)
assert len(rows) == len(oof) == 740
by_id = {x["sample_id"]: x for x in rows}
assert set(by_id) == {x["sample_id"] for x in oof}

duplicate_hashes = defaultdict(list)
duplicate_groups = defaultdict(list)
for x in rows:
    duplicate_hashes[x["image_sha256"]].append(x)
    if x["duplicate_group_id"].strip(): duplicate_groups[x["duplicate_group_id"]].append(x)

def conflicts(groups):
    found = []
    for key, members in groups.items():
        if len(members) < 2: continue
        differing = {t: sorted({x[t] for x in members}) for t in TASKS}
        if any(len(v) > 1 for v in differing.values()):
            found.append({"key": key, "sample_ids": [x["sample_id"] for x in members],
                          "labels": differing})
    return found

task_audit = {}
for task in TASKS:
    truth = [x[f"{task}_truth"] for x in oof]
    pred = [x[f"{task}_pred"] for x in oof]
    baseline = [x[f"{task}_baseline"] for x in oof]
    labels = sorted(set(truth))
    report = classification_report(truth, pred, labels=labels, output_dict=True, zero_division=0)
    matrix = confusion_matrix(truth, pred, labels=labels)
    confusions = []
    for i, a in enumerate(labels):
        for j, b in enumerate(labels):
            if i != j and matrix[i, j]: confusions.append({"truth": a, "prediction": b, "count": int(matrix[i,j])})
    confusions.sort(key=lambda x: (-x["count"], x["truth"], x["prediction"]))
    gained = sum(p == y and b != y for y,p,b in zip(truth,pred,baseline))
    lost = sum(p != y and b == y for y,p,b in zip(truth,pred,baseline))
    task_audit[task] = {
        "labels": labels,
        "class_counts": dict(sorted(Counter(truth).items())),
        "imbalance_ratio_max_to_min": max(Counter(truth).values()) / min(Counter(truth).values()),
        "macro_f1": f1_score(truth,pred,labels=labels,average="macro",zero_division=0),
        "baseline_macro_f1": f1_score(truth,baseline,labels=labels,average="macro",zero_division=0),
        "joint_vs_baseline_gained_samples": gained,
        "joint_vs_baseline_lost_samples": lost,
        "per_class": {label: {k: report[label][k] for k in ("precision","recall","f1-score","support")} for label in labels},
        "top_confusions": confusions[:15],
    }

confidence = Counter(x["annotator_confidence"].strip() or "EMPTY" for x in rows)
audit = {
    "schema": "tempo-target-audit-v1", "dataset_sha256": sha(DATA), "oof_sha256": sha(OOF),
    "samples": len(rows), "unique_ids": len(by_id), "annotator_confidence": dict(sorted(confidence.items())),
    "exact_duplicate_hash_groups": sum(len(v)>1 for v in duplicate_hashes.values()),
    "declared_duplicate_groups": sum(len(v)>1 for v in duplicate_groups.values()),
    "conflicting_exact_duplicate_groups": conflicts(duplicate_hashes),
    "conflicting_declared_duplicate_groups": conflicts(duplicate_groups),
    "tasks": task_audit,
}
OUT.mkdir(parents=True, exist_ok=True)
(OUT/"audit.json").write_text(json.dumps(audit,ensure_ascii=False,indent=2,sort_keys=True)+"\n")

ocr = json.loads(OCR.read_text())
failed = [x for x in ocr["results"] if not x["exact"]]
review = DOCS / "OCR_LABEL_VALIDATION_20.csv"
with review.open("w",encoding="utf-8",newline="") as f:
    fields=["sample_id","image","dataset_headline","ocr_prediction","task1_issue",
            "decision_valid_invalid_ambiguous","correct_headline_if_needed","reviewer_note"]
    w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
    for x in failed:
        w.writerow({"sample_id":x["sample_id"],"image":x["image"],
                    "dataset_headline":x["headline_truth"],"ocr_prediction":x["headline_prediction"],
                    "task1_issue":x["task1_issue"],"decision_valid_invalid_ambiguous":"",
                    "correct_headline_if_needed":"","reviewer_note":""})

lines=["# Audit Dataset dan Model E42","", "**Tanggal:** 17 Oktober 2026", "",
       "## Ringkasan", "",
       f"- Sampel/ID unik: {len(rows)}/{len(by_id)}.",
       f"- Grup hash gambar duplikat: {audit['exact_duplicate_hash_groups']}.",
       f"- Grup duplikat deklaratif: {audit['declared_duplicate_groups']}.",
       f"- Konflik label pada hash gambar identik: {len(audit['conflicting_exact_duplicate_groups'])} grup.",
       f"- Konflik label pada grup duplikat deklaratif: {len(audit['conflicting_declared_duplicate_groups'])} grup.",
       f"- Confidence anotator: `{dict(sorted(confidence.items()))}`.", "", "## Audit per task", ""]
for task,a in task_audit.items():
    lines += [f"### {task}","",f"- Macro-F1 E42: **{a['macro_f1']:.4f}**; baseline: {a['baseline_macro_f1']:.4f}.",
              f"- Rasio kelas terbesar:terkecil: **{a['imbalance_ratio_max_to_min']:.2f}:1**.",
              f"- Sampel diperbaiki terhadap baseline: {a['joint_vs_baseline_gained_samples']}; regresi: {a['joint_vs_baseline_lost_samples']}.",
              "- Tiga kelas F1 terendah: " + ", ".join(f"`{k}` {v['f1-score']:.3f}" for k,v in sorted(a['per_class'].items(),key=lambda z:z[1]['f1-score'])[:3]) + ".",
              "- Lima confusion terbesar: " + "; ".join(f"`{x['truth']}`→`{x['prediction']}` ({x['count']})" for x in a['top_confusions'][:5]) + ".",""]
lines += ["## Kesimpulan teknis","",
          "- E42 memperbaiki lebih banyak sampel daripada yang diregresikan terhadap baseline, tetapi performa kelas ekor masih membatasi Macro-F1.",
          "- Konflik label duplikat dan confidence anotator harus ditinjau sebelum eksperimen berikutnya; file JSON menyimpan daftar lengkap.",
          "- Eksperimen berikutnya harus membandingkan single-task dengan joint pada split yang sama untuk mengukur negative transfer secara langsung.",
          "- Tidak ada label yang diubah oleh audit ini.","",
          "## Artefak","", "- `DEMO_XAI_745_FULL/04_hasil_eksperimen/audit_targets_20261017/audit.json`",
          "- `docs/OCR_LABEL_VALIDATION_20.csv`", ""]
(DOCS/"AUDIT_DATASET_DAN_MODEL_E42.md").write_text("\n".join(lines),encoding="utf-8")
print(json.dumps({"status":"ok","ocr_review_rows":len(failed),"tasks":{k:v['macro_f1'] for k,v in task_audit.items()},
                  "duplicate_conflicts":len(audit['conflicting_exact_duplicate_groups'])},indent=2))
