"""Exercise a running E42 HTTP server, including real inference and XAI."""
import argparse
import io
import json
from pathlib import Path
import urllib.request
import urllib.parse
import uuid

ROOT = Path(__file__).resolve().parents[1]
TASKS = ("task1_issue", "task2_domain_sumber", "task3_primary_entity_type")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--upload", action="store_true")
    args = parser.parse_args()
    def request(path, data=None, headers=None):
        with urllib.request.urlopen(urllib.request.Request(args.url + path, data=data, headers=headers or {}), timeout=600) as response:
            return response.status, response.read()
    results = {"url": args.url, "date": "2026-11-13", "deployment": "local Linux; no VPS deployment"}
    status, body = request("/")
    assert status == 200 and b"<html" in body.lower()
    results["frontend"] = status
    _, body = request("/api/models")
    model = json.loads(body)
    assert (model["backend"], model["version"]) == ("e42-tail-grid", "e42-tail-grid-v1")
    results["model"] = model
    import csv
    with (ROOT / "DEMO_XAI_745_FULL/03_data/DATASET_740_TASK2_DOMAIN.csv").open(encoding="utf-8-sig") as stream:
        row = next(csv.DictReader(stream))
    def validate(output):
        assert set(output["prediksi"]) == set(TASKS)
        assert output["xai"]["model_version"] == model["version"]
        for task in TASKS:
            pred = output["prediksi"][task]
            assert pred["backend"] == model["backend"] and pred["model_version"] == model["version"]
            assert 0 <= pred["probabilitas"] <= 1
            assert abs(sum(p["prob"] for p in pred["semua"]) - 1) < 1e-5
            code, image = request(output["heatmap_per_task"][task]["url"])
            assert code == 200 and image.startswith(b"\x89PNG")
        assert output["atribusi_kata"]
        return output
    _, body = request("/api/analisis", urllib.parse.urlencode(dict(sample_id=row["sample_id"], metode_atribusi="occlusion")).encode())
    results["dataset_analysis"] = validate(json.loads(body))
    if args.upload:
        boundary = "E42Smoke" + uuid.uuid4().hex
        data = io.BytesIO()
        for name, value in dict(headline=row["headline_verified"], supporting=row["supporting_text_verified"], metode_atribusi="occlusion").items():
            data.write(f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n'.encode())
        image_path = ROOT / "DEMO_XAI_745_FULL/05_gambar" / Path(row["image_path"]).name
        data.write(f'--{boundary}\r\nContent-Disposition: form-data; name="gambar"; filename="smoke.jpg"\r\nContent-Type: image/jpeg\r\n\r\n'.encode())
        data.write(image_path.read_bytes())
        data.write(f'\r\n--{boundary}--\r\n'.encode())
        _, body = request("/api/analisis", data.getvalue(), {"Content-Type": f"multipart/form-data; boundary={boundary}"})
        results["upload_analysis"] = validate(json.loads(body))
        assert results["upload_analysis"]["xai"]["folds"] == [1, 2, 3, 4, 5]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(results, indent=2, ensure_ascii=False) + "\n")
    print("PASS", args.url, model["backend"], model["version"], "dataset + XAI", "upload + XAI" if args.upload else "", args.output)

if __name__ == "__main__":
    main()
