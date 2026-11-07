"""E02 tahap awal: head Task 2 terisolasi pada deskripsi VLM.

Semua preprocessing dan pemilihan C dipelajari hanya pada fold training.
Eksperimen ini tidak menyentuh encoder atau aplikasi produksi.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score, accuracy_score
from sklearn.model_selection import StratifiedKFold, GridSearchCV

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "03_data/DATASET_740_TASK2_DOMAIN.csv"
RUN = ROOT / "04_hasil_eksperimen/e01_vlm/kaggle_full/e01_vlm"
OUT = ROOT / "04_hasil_eksperimen/e02_task2_head.json"
SEED = 42

df = pd.read_csv(DATA).fillna("")
rows = {r["sample_id"]: r for r in map(json.loads, (RUN / "deskripsi.jsonl").read_text().splitlines())}
text = df.sample_id.map(lambda x: rows[x]["deskripsi"]).to_numpy()
y = df.task2_domain_sumber.to_numpy()
folds = StratifiedKFold(5, shuffle=True, random_state=SEED)

def run(weight):
    pred = np.empty(len(y), dtype=object)
    for tr, te in folds.split(text, df.task1_issue):
        vec = TfidfVectorizer(ngram_range=(1, 2), analyzer="word", sublinear_tf=True, min_df=2)
        xtr, xte = vec.fit_transform(text[tr]), vec.transform(text[te])
        grid = GridSearchCV(LogisticRegression(max_iter=5000, class_weight=weight),
                            {"C": [0.3, 1, 3, 10, 30]}, cv=3,
                            scoring="f1_macro", n_jobs=8)
        grid.fit(xtr, y[tr]); pred[te] = grid.predict(xte)
    return {"macro_f1": round(float(f1_score(y, pred, average="macro")), 4),
            "accuracy": round(float(accuracy_score(y, pred)), 4)}

results = {"protocol": "OOF 5-fold seed42; inner-CV C; Task2 head only"}
for name, weight in [("none", None), ("balanced", "balanced")]:
    results[name] = run(weight)
OUT.write_text(json.dumps(results, indent=2, ensure_ascii=False))
print(json.dumps(results, indent=2, ensure_ascii=False))
