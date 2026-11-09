"""E01 tahap 2: evaluasi 5-fold OOF atas keluaran VLM (e01_vlm.py).

Split sama dengan run_evaluation.py: StratifiedKFold(5, shuffle, seed 42),
stratifikasi task1_issue dengan kelas < 5 sampel digabung. Hyperparameter C
dipilih lewat inner-CV di fold latih saja; fold uji luar tidak dipakai untuk tuning.

    venv/bin/python 01_notebook/e01_evaluasi.py 04_hasil_eksperimen/e01_vlm/<run>
    venv/bin/python 01_notebook/e01_evaluasi.py --pakai-deskripsi-anotator <out>

Plan: docs/plans/2026-10-08-e01-vlm-dua-tahap-kaggle.md
"""
import argparse
import hashlib
import json
import os
import pathlib
from collections import Counter

# Satu thread BLAS per job agar total CPU = N_JOBS (server dipakai bersama).
for _var in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_var, "1")

import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix, hstack
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, precision_recall_fscore_support
from sklearn.model_selection import GridSearchCV, StratifiedKFold
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.preprocessing import StandardScaler

PAKET = pathlib.Path(__file__).resolve().parents[1]
DATA_CSV = PAKET / "03_data" / "DATASET_740_TASK2_DOMAIN.csv"
FITUR = PAKET / "03_data" / "fitur_clip_indobert_740.npz"
TASKS = ["task1_issue", "task2_domain_sumber", "task3_primary_entity_type"]
BASELINE = PAKET / "04_hasil_eksperimen" / "hasil_mtl_740_task2domain.json"
SEED = 42
GRID_C = [0.3, 1, 3, 10, 30]
N_JOBS = 8  # dibatasi agar tidak memakai seluruh CPU server bersama


def split(df):
    strat = df.task1_issue.to_numpy()
    cnt = Counter(strat)
    aman = np.array([c if cnt[c] >= 5 else "-1" for c in strat])
    return list(StratifiedKFold(5, shuffle=True, random_state=SEED).split(np.zeros(len(df)), aman))


def tfidf():
    return FeatureUnion([
        ("kata", TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, min_df=2)),
        ("huruf", TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), sublinear_tf=True, min_df=2)),
    ])


def lr():
    return LogisticRegression(max_iter=5000, class_weight="balanced")


def oof(make_X, y, folds):
    """make_X(train_idx, test_idx) -> (X_train, X_test), fitur dipelajari hanya dari fold latih."""
    pred = np.empty(len(y), dtype=object)
    for tr, te in folds:
        X_tr, X_te = make_X(tr, te)
        inner = StratifiedKFold(3, shuffle=True, random_state=SEED)
        gs = GridSearchCV(lr(), {"C": GRID_C}, cv=inner, scoring="f1_macro", n_jobs=N_JOBS)
        gs.fit(X_tr, y[tr])
        pred[te] = gs.predict(X_te)
    return pred


def skor(y, pred):
    return {"macro_f1": round(float(f1_score(y, pred, average="macro", zero_division=0)), 4),
            "accuracy": round(float(accuracy_score(y, pred)), 4)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("hasil_vlm", help="folder berisi deskripsi.jsonl dan zeroshot.jsonl dari e01_vlm.py")
    ap.add_argument("--pakai-deskripsi-anotator", action="store_true",
                    help="uji alur: pakai task2_source_description sebagai pengganti deskripsi VLM")
    args = ap.parse_args()
    folder = pathlib.Path(args.hasil_vlm)
    folder.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(DATA_CSV).fillna("")
    z = np.load(FITUR)
    padat = np.hstack([z["img"], z["txt"]])
    folds = split(df)

    if args.pakai_deskripsi_anotator:
        deskripsi = df.task2_source_description.to_numpy()
        zeroshot = None
    else:
        meta = json.loads((folder / "meta.json").read_text())
        lokal = hashlib.sha256(DATA_CSV.read_bytes()).hexdigest()
        if meta["data_csv_sha256"] != lokal:
            raise SystemExit("CSV di Kaggle berbeda dengan CSV lokal; label tidak bisa dicocokkan")
        a = {r["sample_id"]: r for r in map(json.loads, (folder / "deskripsi.jsonl").read_text().splitlines())}
        b = {r["sample_id"]: r for r in map(json.loads, (folder / "zeroshot.jsonl").read_text().splitlines())}
        hilang = set(df.sample_id) - set(a) | set(df.sample_id) - set(b)
        if hilang:
            raise SystemExit(f"{len(hilang)} sampel belum punya keluaran VLM; jalankan e01_vlm.py sampai selesai")
        deskripsi = np.array([a[s]["deskripsi"] for s in df.sample_id])
        zeroshot = np.array([b[s]["domain"] or "TIDAK_VALID" for s in df.sample_id])

    rujukan = df.task2_source_description.to_numpy()

    def teks(kolom):
        def make(tr, te):
            v = tfidf().fit(kolom[tr])
            return v.transform(kolom[tr]), v.transform(kolom[te])
        return make

    def fusi(tr, te):
        v = tfidf().fit(deskripsi[tr])
        s = StandardScaler().fit(padat[tr])
        # Bobot 0,05 menyamakan skala kasar fitur padat 1.280 dimensi dengan TF-IDF ternormalisasi.
        bagian = lambda idx: hstack([v.transform(deskripsi[idx]), csr_matrix(s.transform(padat[idx]) * 0.05)]).tocsr()
        return bagian(tr), bagian(te)

    def baseline_lr(tr, te):
        s = StandardScaler().fit(padat[tr])
        return s.transform(padat[tr]), s.transform(padat[te])

    sumber = "deskripsi anotator (uji alur)" if args.pakai_deskripsi_anotator else "deskripsi VLM"
    hasil = {"sumber_deskripsi": sumber, "split": "StratifiedKFold5 seed42, strat task1_issue (<5 digabung)",
             "pemilihan_C": f"inner-CV 3-fold pada fold latih, grid {GRID_C}", "task": {}}
    prediksi_task2 = {}
    for t in TASKS:
        y = df[t].to_numpy()
        varian = {
            "(b) TF-IDF deskripsi + LR": oof(teks(deskripsi), y, folds),
            "(c) fusi deskripsi + CLIP/IndoBERT baseline + LR": oof(fusi, y, folds),
            "rujukan: CLIP/IndoBERT baseline + LR": oof(baseline_lr, y, folds),
            "rujukan: TF-IDF deskripsi anotator + LR": oof(teks(rujukan), y, folds),
        }
        if t == "task2_domain_sumber" and zeroshot is not None:
            varian = {"(a) zero-shot VLM": zeroshot, **varian}
        hasil["task"][t] = {k: skor(y, p) for k, p in varian.items()}
        if t == "task2_domain_sumber":
            prediksi_task2 = varian
        print(t, json.dumps(hasil["task"][t], indent=1, ensure_ascii=False), flush=True)

    if BASELINE.exists():
        hasil["baseline_mtl_tercatat"] = json.loads(BASELINE.read_text()).get("hasil")
    hasil["baseline_mtl_macro_f1"] = {"task1_issue": 0.438, "task2_domain_sumber": 0.3197,
                                      "task3_primary_entity_type": 0.2764}

    y2 = df.task2_domain_sumber.to_numpy()
    kelas = sorted(set(y2))
    baris = []
    for nama, p in prediksi_task2.items():
        _, rec, f1, sup = precision_recall_fscore_support(y2, p, labels=kelas, zero_division=0)
        baris += [{"varian": nama, "kelas": k, "jumlah": int(n), "recall": round(float(r), 4),
                   "f1": round(float(f), 4)} for k, r, f, n in zip(kelas, rec, f1, sup)]
    akhiran = "_anotator" if args.pakai_deskripsi_anotator else ""
    pd.DataFrame(baris).to_csv(folder / f"e01_recall_per_kelas_task2{akhiran}.csv", index=False)
    (folder / f"e01_evaluasi{akhiran}.json").write_text(json.dumps(hasil, indent=2, ensure_ascii=False))
    print(f"Disimpan di {folder}")


if __name__ == "__main__":
    main()
