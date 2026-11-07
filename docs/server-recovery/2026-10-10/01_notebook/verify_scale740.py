"""Wait for full HTTP batch and audit every item/export/persisted asset.

Run after scale740_launch.json exists. In-sample output is not a metric report.

SKRIP RIWAYAT (5–6 Okt 2026): memantau job batch 740 yang id-nya tercatat di
`revisi_week3/scale740_launch.json`. Job dan asetnya ada di `02_web_demo/_jobs/`
mesin asal dan tidak ikut paket, server ditetapkan ke http://127.0.0.1:7861, dan
hasilnya MENIMPA `scale740_verification.json` serta `scale740_export.*`. Tanpa
job itu skrip ini gagal; bukti yang berlaku ada di `scale740_verification.json`
dan `scale740_resume_verification.json`.
"""
import csv
import io
import json
import math
import time
from pathlib import Path
import requests

package = Path(__file__).resolve().parents[1]
folder = package / "04_hasil_eksperimen/revisi_week3"
job_id = json.loads((folder / "scale740_launch.json").read_text())["job_id"]
base = "http://127.0.0.1:7861"
while True:
    response = requests.get(base + "/api/batch/" + job_id, timeout=60)
    response.raise_for_status()
    job = response.json()
    print(json.dumps(job["progress"]), flush=True)
    if job["status"] not in ("running", "queued"):
        break
    time.sleep(45)
assert job["status"] == "complete" and job["progress"]["success"] == 740, job["progress"]
sample_ids = [x["sample_id"] for x in job["items"]]
assert len(sample_ids) == len(set(sample_ids)) == 740
assets = 0
for item in job["items"]:
    result = item["result"]
    assert result["snapshot"]["sample_id"] == item["sample_id"]
    assert "in-sample" in result["mode"]
    task = job["task"]
    assert result["task_id"] == result["kesimpulan"]["task_id"] == task
    assert result["snapshot"]["class_id"] == result["prediksi"][task]["prediksi"]
    assert all(x.get("task_id", task) == task for x in result["evidence"])
    for prediction in result["prediksi"].values():
        score = prediction["probabilitas"]
        assert math.isfinite(score) and 0 <= score <= 1
    urls = [result["heatmap_padu_url"], result["heatmap_url"]] + [x["url"] for x in result["heatmap_per_task"].values()]
    for url in set(urls):
        assert url.startswith("/api/batch/" + job_id + "/assets/")
        assert (package / "02_web_demo/_jobs" / job_id / "assets" / url.rsplit("/", 1)[1]).is_file()
        assets += 1
    # All740 items exercise the persisted route; originals may have left cache.
    assert requests.get(base+result["heatmap_url"], timeout=30).ok
for kind in ("json", "csv"):
    response = requests.get(base+f"/api/batch/{job_id}/export/{kind}", timeout=60)
    response.raise_for_status()
    (folder / f"scale740_export.{kind}").write_text(response.text, encoding="utf-8")
    if kind == "csv":
        assert len(list(csv.reader(io.StringIO(response.text)))) == 741
    else:
        assert len(response.json()["items"]) == 740
summary = {"status": "passed", "job_id": job_id, "samples": 740, "progress": job["progress"], "assets_checked": assets, "heatmap_http_checks": 740, "snapshot_evidence_checks": 740, "csv_rows_including_header": 741, "protocol": "full HTTP batch, baseline head trained on all740; exploration in-sample, not accuracy benchmark"}
(folder / "scale740_verification.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
print(json.dumps(summary), flush=True)
