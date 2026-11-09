# MICRO-E14 — locked joint QLoRA, five outer folds

Training runs in Kaggle. The local scheduler submits at most two jobs, polls
their exact handles, downloads only small result artifacts, independently
verifies every fold, and aggregates exactly 740 unique OOF predictions.

## Frozen training

- Model/revision/quantization/prompts/LoRA/optimizer match E13.
- Each fold: 592 outer-training, 148 outer-test; inner split 473/119.
- Choose among epochs 1,2,3 using maximum minimum inner micro-F1; mean breaks
  ties, then earliest epoch. No outer-test model selection.
- Fold 1 reuses only E13's eligible inner history and exact initial adapter,
  after checking source/result/split/input audit. Other folds train new inner
  models and never read the E13 result.
- Refit from the exact initial adapter on all 592 outer-training rows, with
  fresh optimizer/scaler/RNG, for the chosen epoch count. One adapter provides
  all three predictions. Evaluate outer-test after refit.
- Pinned Kaggle Docker image and Python training dependencies. Save phase
  checkpoints after each epoch, including optimizer/scaler/RNG state.

`frozen_protocol.json` in the E14 results directory records the full mapping
and parameters. `build_manifest.json` records exact worker and launcher hashes.
Do not regenerate/change training payloads after submission.

## Orchestration

Use `schedule.py` to run the queue; `--once` performs one check/submission cycle.
It uses a file lock and a durable `scheduler_state.json`. Do not delete the
ledger while jobs exist. Polling failures never cause a submitted job to be
repushed. A terminal job failure stops new submissions for diagnosis.

The local computer must remain on for pending folds to be submitted and
completed results to be collected. Already submitted Kaggle training does not
depend on the local scheduler staying online. Re-running the same scheduler
resumes its ledger without launching duplicate versions.

Use `results.py --fold N` to collect and verify a completed fold. Running
`results.py` without a fold aggregates five verified folds; it fails if any
fold is missing or invalid. Validation pilot results never enter this ranking.

These are internal CV experiments on a repeatedly used corpus. A pilot that
informed the frozen configuration does not constitute independent acceptance
data. Micro-F1 and Macro-F1 are reported separately.
