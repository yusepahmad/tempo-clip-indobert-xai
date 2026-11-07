"""Isolated Windows smoke using existing data/weights read-only.

Place beside 02_web_demo in week3-verification; pass training workspace root.
Flask is installed under vendor, without modifying training venv.
"""
import hashlib
import json
import platform
import sys
import time
import traceback
from pathlib import Path

here = Path(__file__).resolve().parent
base = Path(sys.argv[1])
sys.path.insert(0, str(here / "vendor"))
sys.path.insert(0, str(here / "02_web_demo"))
report = {"platform": platform.platform(), "python": sys.version, "steps": [], "status": "running"}
try:
    import torch
    torch.set_num_threads(4)
    import xai_core
    xai_core.DATA_CSV = base / "DEMO_XAI_745_FULL/03_data/DATASET_740_TASK2_DOMAIN.csv"
    xai_core.FEATURES = base / "DEMO_XAI_745_FULL/03_data/fitur_clip_indobert_740.npz"
    xai_core.DIR_GAMBAR = base / "DEMO_XAI_745_FULL/05_gambar"
    xai_core.CLIP_PRETRAINED = str(base / "weights/clip/open_clip_model.safetensors")
    xai_core.INDOBERT = str(base / "weights/indobert")
    report["data_sha256"] = hashlib.sha256(xai_core.DATA_CSV.read_bytes()).hexdigest()
    report["torch"] = torch.__version__
    import app
    app.ROOT = base / "DEMO_XAI_745_FULL"
    client = app.app.test_client()
    assert client.get("/").status_code == 200
    samples = client.get("/api/samples").get_json()
    assert len(samples) == 740
    catalog = client.get("/api/catalog").get_json()
    assert [len(x["classes"]) for x in catalog] == [10, 7, 8]
    report["steps"].append({"name": "html_samples_catalog", "status": "passed"})
    for task in app.ENG.tasks:
        start = time.perf_counter()
        response = client.post("/api/analisis", data={"sample_id": samples[0]["sample_id"], "task": task, "metode_atribusi": "occlusion"})
        assert response.status_code == 200, response.get_data(as_text=True)
        result = response.get_json()
        assert result["snapshot"]["task_id"] == task and result["kesimpulan"]["task_id"] == task
        assert all(x.get("task_id", task) == task for x in result["evidence"])
        assert result["heatmap_url"]
        assert client.get(result["heatmap_url"]).status_code == 200
        report["steps"].append({"name": task, "status": "passed", "seconds": time.perf_counter()-start})
        print(task, "passed", flush=True)
    report["status"] = "passed"
except Exception:
    report["status"] = "failed"
    report["error"] = traceback.format_exc()
finally:
    (here / "windows_verification.json").write_text(json.dumps(report, ensure_ascii=False, indent=2),encoding="utf-8")
    print(json.dumps(report, ensure_ascii=True, indent=2), flush=True)
if report["status"] != "passed":
    raise SystemExit(1)
