#!/usr/bin/env python3
"""Validate supplied human files and build a non-destructive public addendum."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path

import pandas as pd
from sklearn.metrics import cohen_kappa_score

TASKS = ("task1_issue", "task2_domain_sumber", "task3_primary_entity_type")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def exact_keys(actual: pd.DataFrame, template: pd.DataFrame, keys: list[str], name: str) -> None:
    left = set(map(tuple, actual[keys].astype(str).to_numpy()))
    right = set(map(tuple, template[keys].astype(str).to_numpy()))
    if left != right or len(actual) != len(template):
        raise ValueError(f"{name}: keys differ from canonical template")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root, work, out = args.root.resolve(), args.work.resolve(), args.output.resolve()
    if out.exists():
        raise FileExistsError(out)
    (out / "inputs" / "R23").mkdir(parents=True)
    (out / "inputs" / "R34").mkdir(parents=True)
    (out / "analysis").mkdir()

    package = root / "delivery/HASIL_REVISI_JOY_20261108_R4_ANALISIS/joy_revisi_ii"
    files = {
        "r22": root / "HASIL_ISIAN/R22/R22_RESULT_REVIEW_HUMAN_20.csv",
        "a": work / "R23_A/ANOTATOR_A/annotator_A.csv",
        "b": work / "R23_B/ANOTATOR_B/annotator_B.csv",
        "r31": work / "R31/HASIL_ADJUDIKASI_60/catchall_review_60.csv",
    }
    for path in files.values():
        if not path.is_file():
            raise FileNotFoundError(path)

    # R22: exact 20 prespecified examples and complete human decisions.
    r22 = pd.read_csv(files["r22"], keep_default_na=False, dtype=str)
    t22 = pd.read_csv(package / "UNTUK_MANUSIA/R22_REVIEW_MANUSIA_20.csv", keep_default_na=False, dtype=str)
    exact_keys(r22, t22, ["sample_id"], "R22")
    required22 = ["human_reviewer_id", "human_review_date",
                  "sumber_visual_observasi_bebas_ya_tidak",
                  "memuat_kode_task2_di_sumber_visual_ya_tidak", "human_notes"]
    if r22[required22].eq("").any().any():
        raise ValueError("R22 has blank required human fields")
    for column in required22[2:4]:
        if not set(r22[column].str.lower()).issubset({"ya", "tidak"}):
            raise ValueError(f"R22 invalid yes/no value: {column}")
    r22_summary = {
        "status": "complete_human_review_20",
        "samples": len(r22),
        "free_observation": r22[required22[2]].str.lower().value_counts().sort_index().to_dict(),
        "task2_code_leak": r22[required22[3]].str.lower().value_counts().sort_index().to_dict(),
        "source_sha256": sha(files["r22"]),
        "caveat": "Human field review does not recreate historical process isolation or original timestamps.",
    }

    # R23: protocol-bound labels and reproducible Cohen kappa.
    protocol = json.loads((package / "human_inputs/annotation/protocol.json").read_text())
    a = pd.read_csv(files["a"], keep_default_na=False, dtype=str)
    b = pd.read_csv(files["b"], keep_default_na=False, dtype=str)
    expected = set(protocol["sample_ids"])
    for name, frame in (("A", a), ("B", b)):
        if not frame.sample_id.is_unique or set(frame.sample_id) != expected:
            raise ValueError(f"R23 annotator {name}: IDs differ from protocol")
        if frame[[*TASKS, "confidence_1_to_5"]].eq("").any().any():
            raise ValueError(f"R23 annotator {name}: blank required value")
        if not set(frame.confidence_1_to_5).issubset({"1", "2", "3", "4", "5"}):
            raise ValueError(f"R23 annotator {name}: confidence outside 1..5")
        for task in TASKS:
            if not set(frame[task]).issubset(protocol["labels"][task]):
                raise ValueError(f"R23 annotator {name}: invalid {task} label")
    aa, bb = a.set_index("sample_id").sort_index(), b.set_index("sample_id").sort_index()
    agreement_rows, disagreement_rows = [], []
    for task in TASKS:
        kappa = cohen_kappa_score(aa[task], bb[task], labels=protocol["labels"][task])
        agreement_rows.append({"task": task, "samples": len(aa),
                               "exact_agreement": float((aa[task] == bb[task]).mean()),
                               "cohen_kappa": float(kappa),
                               "disagreements": int((aa[task] != bb[task]).sum())})
        mismatch = aa[task] != bb[task]
        for sample_id in aa.index[mismatch]:
            disagreement_rows.append({"sample_id": sample_id, "task": task,
                                      "annotator_A": aa.at[sample_id, task],
                                      "annotator_B": bb.at[sample_id, task],
                                      "confidence_A": aa.at[sample_id, "confidence_1_to_5"],
                                      "confidence_B": bb.at[sample_id, "confidence_1_to_5"]})
    pd.DataFrame(agreement_rows).to_csv(out / "analysis/R23_AGREEMENT.csv", index=False)
    pd.DataFrame(disagreement_rows).to_csv(out / "analysis/R23_DISAGREEMENTS.csv", index=False)

    # R31: exact canonical keys and complete adjudication fields.
    r31 = pd.read_csv(files["r31"], keep_default_na=False, dtype=str)
    t31 = pd.read_csv(package / "human_inputs/catchall_review_60.csv", keep_default_na=False, dtype=str)
    exact_keys(r31, t31, ["sample_id", "task", "current_label"], "R31")
    required31 = ["proposed_label", "coherent_subgroup", "adjudication_reason", "reviewer_id"]
    if r31[required31].eq("").any().any():
        raise ValueError("R31 has blank required adjudication fields")
    r31_summary = (r31.assign(changed=r31.current_label != r31.proposed_label)
                   .groupby(["task", "current_label", "changed"], dropna=False)
                   .size().rename("items").reset_index())
    r31_summary.to_csv(out / "analysis/R31_SUMMARY.csv", index=False)

    # R34: validate five complete files and detect duplicated rating profiles.
    rating_files = sorted(work.glob("R34/**/ratings.csv"))
    if len(rating_files) != 5:
        raise ValueError("R34 requires exactly five ratings.csv files")
    frames = []
    duplicate_pairs = []
    for index, path in enumerate(rating_files, start=1):
        frame = pd.read_csv(path, keep_default_na=False, dtype=str)
        template = pd.read_csv(package / f"UNTUK_MANUSIA/PAKET_PENILAI/PENILAI_XAI_R{index}/ratings.csv",
                               keep_default_na=False, dtype=str)
        exact_keys(frame, template, ["item_id", "rater_id", "dimension"], f"R34 R{index}")
        score = pd.to_numeric(frame.score, errors="coerce")
        if score.isna().any() or not score.between(1, 5).all() or not (score % 1 == 0).all():
            raise ValueError(f"R34 R{index}: score must be complete integer 1..5")
        if frame.alasan_singkat.eq("").any():
            raise ValueError(f"R34 R{index}: blank reason")
        frames.append(frame.sort_values(["item_id", "dimension"]).reset_index(drop=True))
    for left in range(5):
        for right in range(left + 1, 5):
            scores_same = frames[left].score.equals(frames[right].score)
            reasons_same = frames[left].alasan_singkat.equals(frames[right].alasan_singkat)
            if scores_same and reasons_same:
                duplicate_pairs.append([f"R{left+1}", f"R{right+1}"])
    combined = pd.concat(frames, ignore_index=True)
    combined.to_csv(out / "analysis/R34_ALL_RATINGS.csv", index=False)
    r34_audit = {
        "status": "rejected_as_independent_raters" if duplicate_pairs else "complete_distinct_profiles",
        "files": 5, "rows": len(combined), "items": int(combined.item_id.nunique()),
        "dimensions": sorted(combined.dimension.unique()),
        "duplicate_profile_pairs": duplicate_pairs,
        "all_score_and_reason_profiles_identical": len(duplicate_pairs) == 10,
        "icc_reported": False,
        "reason": "ICC is not reported because identical copied profiles do not establish five independent human ratings." if duplicate_pairs else "",
    }

    # Preserve supplied inputs, without images or participant PII beyond coded IDs.
    shutil.copy2(files["r22"], out / "inputs/R22_REVIEW_MANUSIA_20.csv")
    shutil.copy2(files["a"], out / "inputs/R23/annotator_A.csv")
    shutil.copy2(files["b"], out / "inputs/R23/annotator_B.csv")
    shutil.copy2(files["r31"], out / "inputs/R31_ADJUDIKASI_60.csv")
    for index, path in enumerate(rating_files, start=1):
        shutil.copy2(path, out / f"inputs/R34/ratings_R{index}.csv")

    write_json(out / "analysis/R22_SUMMARY.json", r22_summary)
    write_json(out / "analysis/R23_AGREEMENT.json", {
        "status": "computed_from_supplied_labels", "source_a_sha256": sha(files["a"]),
        "source_b_sha256": sha(files["b"]), "tasks": agreement_rows,
        "caveat": "Agreement does not authenticate identity/independence; adjudicated gold remains separate.",
    })
    write_json(out / "analysis/R34_INDEPENDENCE_AUDIT.json", r34_audit)
    write_json(out / "VERIFICATION.json", {
        "status": "validated_with_r34_independence_failure",
        "r22_complete": True, "r23_complete": True, "r31_complete": True,
        "r34_complete": False, "r34_reason": r34_audit["reason"],
        "source_zip_sha256": {
            "R23_A": sha(root / "HASIL_ISIAN/R23/ANOTATOR_A.zip"),
            "R23_B": sha(root / "HASIL_ISIAN/R23/ANOTATOR_B.zip"),
            "R31": sha(root / "HASIL_ISIAN/R31/HASIL_ADJUDIKASI_60.zip"),
            "R34": sha(root / "HASIL_ISIAN/R34/HASIL_PENILAIAN_XAI_R1_R5.zip"),
        },
    })


if __name__ == "__main__":
    main()
