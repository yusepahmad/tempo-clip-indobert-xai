# E40 — Balanced joint CLIP–IndoBERT MMoE

Experimental candidate; not the delivery model and no0.70claim yet.

Run from this folder with projectvenv: `python checks.py`, then `python run.py`, then `python verify.py`. `root_verify.py OUTPUT_DIRECTORY` uses only stdlib for independent hash/metric verification after copying complete artifacts. Inputs are pinned legacyCLIPB32/IndoBERT cache plus auditedE36full/crop L14 and E37meanpool features. No label/rationale features or hostedAPI calls.

Nested5×2; selection maximizes the minimum of meaninnerMacroF1 across ALL THREE tasks. Baseline control is byte-equivalent numerical behavior to original sharedMTL. MMoE shares experts between tasks, with task-specific gates/heads and positive jointlosses.

Checkpoint contract: `state_dict`, full dataclass`config`, `classes` per task, `train_indices`/`test_indices`, `state_sha256` and inputhashmanifest. Model reconstructs with `JointMTL(nclasses,Config(**checkpoint['config']))`. Rawfeatureorder: B32image512, IndoBERTCLS768, L14full768, L14crop768, IndoBERTmean768, IndoBERTlast4mean768. Used candidateviews are both L14views and CLS or mean. Dropout disabled at inference. Unused featureviews do not affect predictions.

Featuregradient/checkpointroundtrip are tested; image/text XAI integration, newupload runtime and cleanpackage gates remain pending. See `docs/GOAL_DELIVERY_GATES.md` in repositoryroot. Never substitute trainingrefit accuracy for OOF Macro-F1.
