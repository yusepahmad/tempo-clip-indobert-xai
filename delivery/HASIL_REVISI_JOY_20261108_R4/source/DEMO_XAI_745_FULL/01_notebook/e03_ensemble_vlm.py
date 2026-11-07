from pathlib import Path
import json, numpy as np, pandas as pd
from scipy.sparse import hstack
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score, accuracy_score
from sklearn.model_selection import StratifiedKFold, GridSearchCV
from sklearn.preprocessing import OneHotEncoder

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'03_data/DATASET_740_TASK2_DOMAIN.csv'
RUN=ROOT/'04_hasil_eksperimen/e01_vlm/kaggle_full/e01_vlm'
OUT=ROOT/'04_hasil_eksperimen/e03_ensemble_vlm.json'
df=pd.read_csv(DATA).fillna('')
a={r['sample_id']:r for r in map(json.loads,(RUN/'deskripsi.jsonl').read_text().splitlines())}
b={r['sample_id']:r for r in map(json.loads,(RUN/'zeroshot.jsonl').read_text().splitlines())}
text=df.sample_id.map(lambda x:a[x]['deskripsi']).to_numpy()
z=df.sample_id.map(lambda x:b[x]['domain']).to_numpy(); y=df.task2_domain_sumber.to_numpy()
folds=StratifiedKFold(5,shuffle=True,random_state=42)
def run(ensemble):
 pred=np.empty(len(y),object)
 for tr,te in folds.split(text,df.task1_issue):
  v=TfidfVectorizer(ngram_range=(1,2),sublinear_tf=True,min_df=2)
  xt=v.fit_transform(text[tr]); xe=v.transform(text[te])
  if ensemble:
   o=OneHotEncoder(handle_unknown='ignore'); qt=o.fit_transform(z[tr,None]); qe=o.transform(z[te,None]); xt=hstack([xt,qt]); xe=hstack([xe,qe])
  g=GridSearchCV(LogisticRegression(max_iter=5000,class_weight='balanced'),{'C':[.3,1,3,10,30]},cv=3,scoring='f1_macro',n_jobs=8); g.fit(xt,y[tr]); pred[te]=g.predict(xe)
 return {'macro_f1':round(float(f1_score(y,pred,average='macro')),4),'accuracy':round(float(accuracy_score(y,pred)),4)}
res={'protocol':'OOF5 seed42 inner-C; zero-shot categorical + TF-IDF','tfidf':run(False),'ensemble':run(True)}
OUT.write_text(json.dumps(res,indent=2)); print(json.dumps(res,indent=2))
