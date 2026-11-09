"""EasyOCR beamsearch comparison on same30diagnosis+3lecturer images.

No production configuration change. Ground truth/protocol limitations retained.

Catatan 6 Okt: skrip riwayat (5 Okt). Tiga foto dosen dibaca dari folder induk
paket (mesin asal); di paket delivery salinannya di `06_gambar_revisi/` dipakai lebih dulu.
"""
import json
import re
import sys
import time
from pathlib import Path
import numpy as np
import torch
from PIL import Image

torch.set_num_threads(2)
package = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(package / "02_web_demo"))
from ocr_headline import _muat_easyocr, _baca_easyocr, pilih_headline

folder = package / "04_hasil_eksperimen/revisi_week3"
out = folder / "beamsearch"
out.mkdir(exist_ok=True)
diagnosis = json.loads((folder / "ocr_diagnosis.json").read_text())["results"]
baseline = json.loads((folder / "selector_comparison.json").read_text())["results"]
before = {x["sample_id"]: x["after"] for x in baseline}
cases = [{"id": x["sample_id"], "path": next((package / "05_gambar").glob(x["sample_id"]+".*")), "truth": x["truth"], "baseline": before[x["sample_id"]], "subset": "diagnosis30"} for x in diagnosis]
for x in json.loads((folder / "gambar_dosen/summary.json").read_text()):
    cases.append({"id": Path(x["file"]).stem, "path": (package/"06_gambar_revisi"/Path(x["file"]).name if (package/"06_gambar_revisi"/Path(x["file"]).name).exists() else package.parent/x["file"]), "truth": x["headline_reference_agent_visual"], "baseline": x["ocr"]["headline"], "subset": "lecturer3"})
reader = _muat_easyocr()
class BeamReader:
    def readtext(self, path, **kwargs):
        return reader.readtext(path, decoder="beamsearch", beamWidth=5, **kwargs)
wrapper = BeamReader()
normalize = lambda text: re.sub(r"\s+", " ", text.strip()).upper()
results = []
for case in cases:
    saved = out/(case["id"]+".json")
    if saved.exists():
        result = json.loads(saved.read_text(encoding="utf-8"))
    else:
        begin = time.perf_counter()
        blocks = _baca_easyocr(wrapper, case["path"])
        with Image.open(case["path"]) as image:
            height = image.height
        selected = pilih_headline(blocks, height)
        result = {"id": case["id"], "subset": case["subset"], "truth": case["truth"], "baseline": case["baseline"], "prediction": selected["headline"], "baseline_exact": normalize(case["baseline"]) == normalize(case["truth"]), "exact": normalize(selected["headline"]) == normalize(case["truth"]), "seconds": time.perf_counter()-begin, "ocr": selected}
        saved.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    results.append(result)
    print(result["id"], result["exact"], result["prediction"], flush=True)
summary = {}
for subset in ("diagnosis30", "lecturer3"):
    rows = [x for x in results if x["subset"] == subset]
    summary[subset] = {"count": len(rows), "baseline_correct": sum(x["baseline_exact"] for x in rows), "beamsearch_correct": sum(x["exact"] for x in rows), "median_seconds": float(np.median([x["seconds"] for x in rows])), "p95_seconds": float(np.percentile([x["seconds"] for x in rows],95))}
report = {"configuration": {"engine": "EasyOCR id/en CPU", "decoder": "beamsearch", "beamWidth": 5, "selector": "production .62/3.5"}, "summary": summary, "limitations": "Same previously inspected diagnosis samples; not independent validation or full-text groundtruth. Historical baseline latency used4threads and includedinitialization; beamsearch uses2threads afterinitialization, so latency is descriptive, not matched speed comparison.", "results": results}
(folder / "decoder_comparison.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(summary), flush=True)
