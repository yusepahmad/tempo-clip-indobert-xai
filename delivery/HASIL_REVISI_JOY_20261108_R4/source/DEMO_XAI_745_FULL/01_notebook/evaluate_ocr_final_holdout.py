#!/usr/bin/env python3
"""Jalankan sekali kandidat OCR terkunci pada holdout final beku."""
import hashlib, json, re, sys, time, unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIR = ROOT / "04_hasil_eksperimen/revisi_week3/ocr_final_holdout"
MANIFEST = DIR / "manifest_frozen.json"
RESULT = DIR / "results.json"
LOCKED_SELECTOR_SHA256 = "94bb5c5ef5fd38ae7480d51f435e6c80264e150f04fdfe8f03327747a21435db"

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def norm(value):
    value = unicodedata.normalize("NFKC", value or "").upper()
    return re.sub(r"\s+", " ", re.sub(r"[^0-9A-ZÀ-ÖØ-Ý\s]", " ", value)).strip()

if RESULT.exists():
    raise SystemExit("Holdout final sudah pernah dijalankan; output tidak boleh ditimpa.")
expected_manifest = (DIR / "manifest_frozen.sha256").read_text().split()[0]
if sha(MANIFEST) != expected_manifest:
    raise SystemExit("Hash manifest final berubah.")
selector = ROOT / "02_web_demo/ocr_headline.py"
if sha(selector) != LOCKED_SELECTOR_SHA256:
    raise SystemExit("Selector tidak sama dengan kandidat yang dikunci.")

sys.path.insert(0, str(ROOT / "02_web_demo"))
import ocr_headline
manifest = json.loads(MANIFEST.read_text())
rows = []
for i, item in enumerate(manifest["items"], 1):
    image = ROOT / item["image"]
    if sha(image) != item["image_sha256"]:
        raise SystemExit(f"Hash gambar berubah: {item['sample_id']}")
    started = time.perf_counter(); output = ocr_headline.baca(image); elapsed = time.perf_counter() - started
    prediction = output.get("headline", "")
    exact = norm(prediction) == norm(item["headline_truth"])
    rows.append({**item, "headline_prediction": prediction, "exact": exact,
                 "seconds": elapsed, "ocr": output})
    print(f"[{i:02d}/80] {item['sample_id']} exact={exact} seconds={elapsed:.2f}", flush=True)

correct = sum(x["exact"] for x in rows)
report = {"schema": "tempo-ocr-final-holdout-results-v1",
          "manifest_sha256": expected_manifest,
          "selector_sha256": LOCKED_SELECTOR_SHA256,
          "count": len(rows), "exact_correct": correct,
          "exact_accuracy": correct / len(rows), "gate_required": 0.80,
          "gate_passed": correct / len(rows) >= 0.80,
          "total_seconds": sum(x["seconds"] for x in rows), "results": rows}
RESULT.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
print(json.dumps({k: report[k] for k in ("count", "exact_correct", "exact_accuracy", "gate_passed", "total_seconds")}, indent=2))
