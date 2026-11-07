# MICRO-E13 — joint QLoRA inner pilot

Kaggle: `yusepmuhamadzazuli/tempo-micro-e13-joint-qlora-inner-pilot`.

Train 473 rows from outer fold 1 training partition; select epoch on 119
inner-validation rows. Outer-test 148 rows are not used for preprocessing,
training, epoch selection, or prediction in this pilot.

One shared Qwen3-VL LoRA adapter alternates three task objectives. Six joint
epochs give approximately two data passes per task. Select by minimum
validation micro-F1 and use mean as tie-breaker. Save best adapter and
validation probabilities each epoch. This is a pilot, not 740-sample OOF.

`build_launcher.py` generates the worker and embeds identical bytes in the
single-file Kaggle launcher. Hugging Face cache is placed in `/tmp` so large
base weights are not exported with the result.

The fixed control and practical expansion rule are saved in
`MICRO_E13_joint_qlora_inner_pilot/control.json`. The gate requires a minimum
gain of 0.03 with no task dropping more than 0.03 against the control, or all
three validation scores at least 0.70. It is a resource allocation rule, not
statistical evidence of generalization.

Retrieve only `^e13_inner_pilot/` outputs with Kaggle CLI's `--file-pattern`,
then run `verify_micro_e12_e13.py` from the parent directory after placing
`result.json` and `validation_predictions.csv` in the E13 results folder.
Never add these validation results to the OOF ranking.

`collect_micro_e13.py` retrieves the small evaluation artifacts by default.
Use `--include-checkpoints` to also download adapter weights when needed;
large checkpoint transfers are not required to verify the metrics.
