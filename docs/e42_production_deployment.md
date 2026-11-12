# E42 Linux / Gunicorn deployment

Default backend: `e42-tail-grid`. Expected version: `e42-tail-grid-v1`.
This guide describes preparation and locally tested serving, not a completed VPS deployment.

## Environment

From `DEMO_XAI_745_FULL/`, create a Python 3.10 virtual environment. The repository carries `02_web_demo/requirements-web-lock.txt` as the upstream server environment snapshot, including CPU torch/torchvision and Gunicorn. Install it in a fresh environment:

```bash
python3.10 -m venv venv
venv/bin/python -m pip install -r 02_web_demo/requirements-web-lock.txt
```

A fresh install of that entire lock was not executed here. The existing local environment was used, with Gunicorn installed for testing. Actual tested versions are recorded in `../qa/e42-production/runtime-versions.json`: Python 3.10.18, torch 2.14.0+cpu, torchvision 0.29.0+cpu, transformers 5.17.0, open_clip_torch 3.3.0, Flask 3.1.3 and Gunicorn 27.0.0. The upstream lock contains some different versions, including Gunicorn 26.2.0. Reproduce the recorded environment or validate a clean installation on the target VPS before release.

## Required assets and first-time preparation

Keep the release files in `06_models/e42-tail-grid-v1/`: manifest, five `fold*.pt`, `front_cache.npz`, `tail_initial.pt`, `bert_config.json` and `protocol.json` (about 419 MiB together). They are copied byte-for-byte from audited source commit `e0a977ece2f77ae95325fd164ca0d58a148ec5d8`; no checkpoint was replaced or trained. The dataset SHA must match the manifest. Dataset images under `05_gambar/` are needed for image endpoints and XAI.

`TEMPO_E42_ASSET_DIR` may point to another asset directory; the trusted manifest is still read from the packaged release directory. A missing file, wrong digest, manifest identity mismatch, incompatible checkpoint or invalid fold split raises visibly. Do not edit the manifest to bypass an integrity error.

For uploads, edited text, visual XAI and LIME/occlusion, prepare the exact CLIP/IndoBERT revisions pinned in the manifest. CLIP weights are about 1.71 GB; IndoBERT weights and tokenizer are additional. With network access available, run once as the **same service user**, using the same `HF_HOME` as production:

```bash
HF_HUB_OFFLINE=0 TEMPO_OFFLINE=0 venv/bin/python - <<'PYCODE'
import sys
sys.path.insert(0, '02_web_demo')
from e42_engine import E42Engine
engine = E42Engine()
engine._ensure_encoders()
print(engine.description()['backend'], engine.description()['version'])
PYCODE
```

This downloads/loads pinned backbones and validates their weight hashes, without training. It includes `open_clip_config.json` needed for preprocessing. During this task only that missing small config required a network download; the weight caches were already present. OCR is optional to the inference API but EasyOCR may require its own first-time model download. Prepare OCR separately if the service will expose `/api/ocr` offline.

Startup validates release checkpoints/cache, then loads backbones lazily. A successful `/api/models` proves checkpoint readiness, not complete backbone/OCR cache readiness. The offline encoder command below is the pre-release check for those inference/XAI backbones. Missing backbone cache must be prepared before serving traffic; it is not replaced by a baseline.

## Validate offline and run

```bash
HF_HUB_OFFLINE=1 TEMPO_OFFLINE=1 venv/bin/python 01_notebook/check_delivery.py
HF_HUB_OFFLINE=1 TEMPO_OFFLINE=1 venv/bin/python - <<'PYCODE'
import sys
sys.path.insert(0, '02_web_demo')
from e42_engine import E42Engine
engine = E42Engine()
engine._ensure_encoders()
print(engine.description()['backend'], engine.description()['version'])
PYCODE
```

For the existing local Flask launcher:

```bash
HF_HUB_OFFLINE=1 TEMPO_OFFLINE=1 bash jalankan_linux.sh
```

`TEMPO_PYTHON` overrides `venv/bin/python`; `TEMPO_HOST`/`TEMPO_PORT` select its bind address. This launcher runs the full OOF preflight in a process which exits before starting Flask. Flask's built-in server is intended for local checks. Use Gunicorn for the VPS:

```bash
TEMPO_BIND=127.0.0.1:7860 TEMPO_OFFLINE=1 venv/bin/python 02_web_demo/serve_tail.py
```

Gunicorn keeps `HF_HUB_OFFLINE=1` by default, one worker and four threads, timeout 600 seconds. It validates/loads E42 once in its worker; no additional preflight process or preload model is introduced. Five trained tails are required by the upload ensemble; CLIP and IndoBERT front are shared and loaded lazily. Requests to the mutable model context remain serialized by `MODEL_LOCK`; additional threads support HTTP, cancellation and batch APIs. Existing OMP/MKL/OPENBLAS overrides are preserved; `TEMPO_CPU_THREADS` controls torch threads (default 4, clamped 1–8). Do not multiply workers without measuring model memory on the VPS. Peak RAM/latency is hardware-dependent; no minimum VPS memory guarantee is inferred from these local checks.

If using systemd, run the absolute virtualenv Python and `02_web_demo/serve_tail.py`, set the working directory to this project and `HF_HOME` to the prepared service-user cache, and route the selected loopback port through the existing reverse proxy. No active systemd unit, Dockerfile, Compose or Procfile was present in the audited repository; no external service configuration was changed.

## Identity and overrides

Expected startup log:

```text
[init] backend=e42-tail-grid; version=e42-tail-grid-v1; 740 sampul; 5 checkpoint asli terverifikasi; CPU
```

Check `/` and `/api/models` after the worker boots. Metadata must show backend `e42-tail-grid`, version `e42-tail-grid-v1`. There is no dedicated `/health` route; a successful metadata request is the model-readiness check. Run `../scripts/e42_runtime_smoke.py` for predictions and XAI, as shown in the verification report.

Linux, Windows and Gunicorn default to E42 while preserving a nonempty explicit `TEMPO_BACKEND`. `clip-indobert-tail-rich256`, `clip-indobert-mtl`/`baseline` and `micro-e14-qlora` remain intentional alternatives; their prerequisites still apply. Baseline can train its head only when explicitly selected. Unknown values fail, without fallback. E42 Linux/Windows preflight is skipped for explicit alternative backends so the E42 checker does not block a deliberate override. Dedicated `jalankan_micro_e14_*` launchers intentionally retain E14. Archived experiment/recovery/delivery launchers are historical and were not edited.

## Scientific and operational limits

Dataset IDs use their held-out outer-fold checkpoint; uploads average five-fold probabilities and have no separately evaluated benchmark. Existing training uses 128-token cached inputs; new/edited serving text and perturbations use the inherited maximum of 256 tokens. This task does not alter training, the checkpoints, metrics or input-length protocol. XAI uses the same active E42 folds; visual maps are absolute gradient × activation and text explanations are LIME/occlusion. The historical E42 rollout notebook is a separate implementation.

The inherited `xai_contract.text_method` calls the text method occlusion even when LIME is selected; the response's `metode_atribusi` is the actual executed method. Both route to the same E42 model. Native Windows execution, a clean lock installation, OCR downloads, concurrent-load performance and VPS deployment remain outside the executed local verification.

See [source HTML](e42_source_code_documentation.html), [verification results](e42_production_verification.md) and [implementation plan](plans/2026-11-13-e42-launcher-documentation.md).
