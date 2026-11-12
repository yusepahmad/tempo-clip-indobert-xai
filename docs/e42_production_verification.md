# E42 production verification — 2026-11-13

## Outcome and provenance

Local Linux and Gunicorn serving observed `backend=e42-tail-grid`, `version=e42-tail-grid-v1`. Real dataset and upload inference produced all three tasks and real heatmaps/word explanations using the same E42 checkpoint identity. No training/fine-tuning was run. This is **local verification, not a VPS deployment**.

The starting primary folder was an October snapshot without E42 serving modules/assets. Source was audited from GitHub commit `e0a977ece2f77ae95325fd164ca0d58a148ec5d8` in `work/e42-production/`; required files were synchronized into `DEMO_XAI_745_FULL/`. Existing dataset and OOF were already identical and were not changed. Original changed files were backed up under `work/e42-before/`; synchronization provenance is `work/e42-sync.json`. No pre-existing checkpoint was overwritten; added E42 assets are byte-identical to the audited commit.

## Commands and actual results

Commands below are relative to the workspace root unless a directory is shown. Successful commands were actually executed. Test output and HTTP responses are retained under `qa/e42-production/`.

| Verification | Command / method | Observed result |
|---|---|---|
| E42 preflight | From `DEMO_XAI_745_FULL/`: `HF_HUB_OFFLINE=1 TEMPO_OFFLINE=1 venv/bin/python 01_notebook/check_delivery.py` | PASS: five checkpoints; 740/740 predictions equal canonical OOF on each of three tasks |
| Regression | From `DEMO_XAI_745_FULL/02_web_demo/`: `../venv/bin/python -m unittest test_e42_launchers test_e42_serving -v` | PASS: 11 tests; final run 22.647 s; `regression.log` |
| Linux startup | From `DEMO_XAI_745_FULL/`: `TEMPO_PORT=17861 HF_HUB_OFFLINE=1 TEMPO_OFFLINE=1 bash jalankan_linux.sh` | PASS: preflight completes, app initializes E42, frontend and metadata return 200 |
| Linux HTTP smoke | `python scripts/e42_runtime_smoke.py --url http://127.0.0.1:17861 --output qa/e42-production/linux-http.json --upload` | PASS: real dataset and image upload; three predictions, probability sums, model/XAI identity, all three PNG heatmap URLs |
| Gunicorn startup | From `DEMO_XAI_745_FULL/`: `TEMPO_BIND=127.0.0.1:17862 TEMPO_OFFLINE=1 venv/bin/python 02_web_demo/serve_tail.py` | PASS: Gunicorn 27.0.0, gthread, one worker, E42 startup identity |
| Gunicorn HTTP smoke | `python scripts/e42_runtime_smoke.py --url http://127.0.0.1:17862 --output qa/e42-production/gunicorn-http.json --upload` | PASS: same dataset/upload checks; uploads report folds [1,2,3,4,5] |
| Default LIME | Real POST `/api/analisis` on Gunicorn, first dataset ID, `task=task1_issue`, no attribution-method parameter | PASS: `metode_atribusi=lime`, four attributed words, E42 version; full response `gunicorn-lime.json` |
| Missing assets | Actual Linux and Gunicorn subprocesses with empty temporary `TEMPO_E42_ASSET_DIR` | PASS: Linux exit 1; Gunicorn worker boot failure exit 3; explicit `Artefak E42` error, no baseline-training log; real logs retained |
| Unknown backend | Actual app subprocess with `TEMPO_BACKEND=invalid-backend` | PASS: nonzero exit, explicit unknown-backend error, no baseline-training log; `invalid-backend.log` |
| Static syntax | `bash -n DEMO_XAI_745_FULL/jalankan_linux.sh`; `venv/bin/python -m py_compile` for changed serving/test/generator/smoke Python files | PASS |
| Model integrity | Recomputed SHA-256 of all nine manifest assets and compared bytes against audited checkout | PASS: `integrity.json` |
| Source screenshots | `DEMO_XAI_745_FULL/venv/bin/python scripts/build_e42_source_documentation.py` | PASS: 28 verbatim excerpts, fixed-commit file/baris links, source/excerpt hashes, exact-current-excerpt assertions |
| GitHub links | Concurrent HTTP HEAD against every unique fixed-commit source page | PASS: 10 unique pages return 200; anchors/ranges validated against `git show`; `github-links.json` |
| HTML rendering | Actual headless Chromium via Playwright, local `file://` HTML, 1440×1000 and 390×844 viewports | PASS: 28 PNGs load, no page JS errors or horizontal page overflow; source images scroll in their own panels; screenshots/JSON retained |

The regression tests cover Linux default/preflight/failure/override, Gunicorn default/override/offline/thread preservation, Windows conditional default contract, direct app default, single-worker configuration, E42 metadata and fold coverage, full OOF replay, missing/corrupt assets, manifest identity/required files, frozen eval models and refusal to train. Model construction is performed with AdamW patched to raise if startup attempts optimizer construction. Launcher-interception tests are contract checks; the HTTP/subprocess tests above provide the separate real-runtime evidence.

The initial smoke harness needed correction for the CSV BOM and multipart field name (`gambar`); these were harness errors and were fixed before successful HTTP checks. Mobile HTML QA exposed table overflow, which was corrected before final screenshots. Neither issue is reported as a passing initial test.

Observed startup log:

```text
[init] backend=e42-tail-grid; version=e42-tail-grid-v1; 740 sampul; 5 checkpoint asli terverifikasi; CPU
```

Observed runtime stack is recorded in `runtime-versions.json`. Gunicorn was absent initially and installed into the existing venv for these checks. Only the missing CLIP `open_clip_config.json` was downloaded to the existing pinned Hugging Face cache. All real HTTP inference/XAI tests ran with offline mode enabled.

## Files delivered

Full primary-workspace file inventory: [changed-files.json](../qa/e42-production/changed-files.json). Main changes:

- `DEMO_XAI_745_FULL/jalankan_linux.sh`: conditional E42 default, E42-only preflight, explicit overrides preserved.
- `DEMO_XAI_745_FULL/jalankan_windows.bat`: synchronized upstream E42 conditional default; E42-only preflight.
- `DEMO_XAI_745_FULL/02_web_demo/serve_tail.py`: Gunicorn E42 default via setdefault, existing offline/thread settings retained.
- `DEMO_XAI_745_FULL/02_web_demo/app.py`: synchronize upstream E42 dispatch and frontend integration; log backend/version; correct stale module description.
- `DEMO_XAI_745_FULL/02_web_demo/e42_engine.py`: synchronize E42 checkpoint implementation; require correct manifest identity and complete required asset map.
- `DEMO_XAI_745_FULL/02_web_demo/{tail_rich_engine.py,gunicorn_conf.py,index.html,requirements-web-lock.txt}`: required upstream E42 inheritance, Gunicorn config, UI and environment snapshot.
- `DEMO_XAI_745_FULL/02_web_demo/{test_e42_launchers.py,test_e42_serving.py}` and `scripts/e42_runtime_smoke.py`: regression and real HTTP checks.
- `DEMO_XAI_745_FULL/01_notebook/check_delivery.py`: upstream E42 preflight replacing legacy checker.
- `DEMO_XAI_745_FULL/01_notebook/e42_tail_grid/`: missing historical E42 source/config scripts added verbatim; not executed for training.
- `DEMO_XAI_745_FULL/06_models/e42-tail-grid-v1/`: missing E42 manifest/assets added verbatim.
- `DEMO_XAI_745_FULL/{DELIVERY.md,MULAI_DARI_SINI.md}` and `docs/e42_production_deployment.md`: current versus historical defaults, offline cache preparation and production instructions.
- `scripts/build_e42_source_documentation.py`, `docs/e42_source_code_documentation.html`, `docs/e42_source_assets/`: reproducible HTML with 28 PNG source screenshots, plain-text excerpts and source index.
- `docs/plans/2026-11-13-e42-launcher-documentation.md`, root `CHANGELOG.md`, this verification report and `qa/e42-production/`: plan, completed change entries and execution evidence.

A mirrored review checkout under `work/e42-production/` contains the same final serving/documentation changes against the fixed GitHub commit. The implementation was initially prepared locally. Publication requested afterward is tracked in [the push plan](plans/2026-11-13-push-e42-launcher-documentation.md). Primary-file backups and downloaded audit checkout are working materials, not altered historical delivery packages.

## Limits and acceptance scope

- Native Windows `.bat` execution was not available; its conditional defaults are covered by contract tests only.
- No VPS deployment, external reverse-proxy/systemd setup, fresh virtualenv lock installation, concurrent-load benchmark, or OCR model preparation was executed.
- Checkpoint-ready metadata does not guarantee lazy backbone/OCR availability. Offline real inference/XAI succeeded here with prepared pinned backbones; follow the preparation guide on the service account.
- Preserve the existing 128-token training/cache versus 256-token serving distinction. Upload ensemble/edited inputs remain separately unevaluated; no metrics or scientific claims changed.
- The inherited XAI contract text says occlusion even on the LIME path; use response `metode_atribusi` for the executed method. Documentation traces both implementations and distinguishes historical rollout from current web gradient × activation.
- No runtime training, checkpoint replacement, historical metric rewrite or silent baseline fallback occurred. Temporary verification servers were stopped after checks.

Plan: [E42 launcher and documentation](plans/2026-11-13-e42-launcher-documentation.md). Completed changes are recorded under root `CHANGELOG.md` → `[Unreleased]` → `Fixed` / `Added` / `Changed`.

## Publication requested after local verification

Implementation commit [528b9ee](https://github.com/yusepahmad/tempo-clip-indobert-xai/commit/528b9ee413cb62350ecae8c16c883fc84aec0c90) was pushed fast-forward to `origin/main`; `git ls-remote` matched local HEAD. All 11 launcher/engine tests were executed again in the publication checkout and passed in 16.742 seconds. The publication plan and changelog record this action; it does not establish a VPS deployment.
