"""Paired selector comparison using saved OCR blocks, without rerunning engine."""
import json
import re
import sys
import time
from pathlib import Path
from PIL import Image

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / "02_web_demo"))
from ocr_headline import pilih_headline

folder = root / "04_hasil_eksperimen/revisi_week3"
before = json.loads((folder / "ocr_diagnosis.json").read_text())
rows = []
for item in before["results"]:
    image = next((root / "05_gambar").glob(item["sample_id"] + ".*"))
    with Image.open(image) as img:
        height = img.height
    start = time.perf_counter()
    selected = pilih_headline(item["ocr"]["blok_mentah"], height)
    elapsed = time.perf_counter() - start
    predicted = re.sub(r"\s+", " ", selected["headline"].strip()).upper()
    rows.append({"sample_id": item["sample_id"], "truth": item["truth"], "before": item["prediction"], "after": predicted, "before_exact": item["exact"], "after_exact": predicted == item["truth"], "selector_seconds": elapsed})
result = {"count": len(rows), "before_correct": sum(x["before_exact"] for x in rows), "after_correct": sum(x["after_exact"] for x in rows), "caveat": "Same 30 raw OCR outputs; selector-only replay. Not independent validation, no claim of improved engine extraction or end-to-end latency.", "results": rows}
(folder / "selector_comparison.json").write_text(json.dumps(result, ensure_ascii=False, indent=2))
print(json.dumps({k: v for k, v in result.items() if k != "results"}))
