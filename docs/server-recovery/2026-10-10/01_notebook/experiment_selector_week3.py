"""Compare grouping thresholds on saved OCR; no production selector changes.

First20 historical diagnosis examples used for candidate selection. Last10
reported separately; all30 have already been inspected, so not fresh validation.
"""
import inspect
import json
import re
import sys
from pathlib import Path
from PIL import Image

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / "02_web_demo"))
import ocr_headline

folder = root / "04_hasil_eksperimen/revisi_week3"
items = json.loads((folder / "ocr_diagnosis.json").read_text())["results"]
heights = []
for item in items:
    with Image.open(next((root / "05_gambar").glob(item["sample_id"]+".*"))) as image:
        heights.append(image.height)
normalize = lambda text: re.sub(r"\s+", " ", text.strip()).upper()
source = inspect.getsource(ocr_headline.pilih_headline)
results = []
for threshold in (.45, .5, .55, .62, .7):
    for span in (3.5, 5., 7.):
        namespace = dict(vars(ocr_headline))
        candidate = source.replace('utama["tinggi"] * 0.62', f'utama["tinggi"] * {threshold}').replace('utama["tinggi"] * 3.5', f'utama["tinggi"] * {span}')
        exec(compile(candidate, "selector-experiment", "exec"), namespace)
        predictions = [namespace["pilih_headline"](x["ocr"]["blok_mentah"], height)["headline"] for x, height in zip(items, heights)]
        exact = [normalize(prediction) == x["truth"] for prediction, x in zip(predictions, items)]
        results.append({"threshold": threshold, "span": span, "diagnosis20_correct": sum(exact[:20]), "additional10_correct": sum(exact[20:]), "total30_correct": sum(exact), "predictions": predictions})
baseline = next(x for x in results if x["threshold"] == .62 and x["span"] == 3.5)
# Prefer least departure from production when diagnosis scores tie.
chosen = max(results, key=lambda x: (x["diagnosis20_correct"], -abs(x["threshold"]-.62), -abs(x["span"]-3.5)))
report = {"method": "same raw OCR blocks; grouping-only, 15 candidate configurations", "baseline": baseline, "candidate_selected_on20": chosen, "candidates": results, "limitations": "Additional10 were previously inspected; not independent confirmation. No claim about engine extraction or runtime. No production change without broader validation."}
(folder / "selector_experiment.json").write_text(json.dumps(report, ensure_ascii=False, indent=2))
print(json.dumps({"baseline": {k:v for k,v in baseline.items() if k != "predictions"}, "candidate": {k:v for k,v in chosen.items() if k != "predictions"}}))
