"""E02 smoke: neural head Task 2 terisolasi pada deskripsi VLM."""
from pathlib import Path
import json, random
import numpy as np, pandas as pd, torch
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import f1_score, accuracy_score

ROOT=Path(__file__).resolve().parents[1]; DATA=ROOT/'03_data/DATASET_740_TASK2_DOMAIN.csv'
RUN=ROOT/'04_hasil_eksperimen/e01_vlm/kaggle_full/e01_vlm'; OUT=ROOT/'04_hasil_eksperimen/e02_task2_mlp.json'
SEED=42; torch.set_num_threads(8); np.random.seed(SEED); random.seed(SEED); torch.manual_seed(SEED)
df=pd.read_csv(DATA).fillna(''); rows={r['sample_id']:r for r in map(json.loads,(RUN/'deskripsi.jsonl').read_text().splitlines())}
texts=df.sample_id.map(lambda x:rows[x]['deskripsi']).to_numpy(); le=LabelEncoder(); y=le.fit_transform(df.task2_domain_sumber)
class Net(torch.nn.Module):
 def __init__(self,d,k):
  super().__init__(); self.net=torch.nn.Sequential(torch.nn.Linear(d,128),torch.nn.ReLU(),torch.nn.Dropout(.25),torch.nn.Linear(128,k))
 def forward(self,x): return self.net(x)
def run(mode):
 pred=np.empty(len(y),dtype=int); folds=StratifiedKFold(5,shuffle=True,random_state=SEED)
 for tr,te in folds.split(texts,df.task1_issue):
  v=TfidfVectorizer(ngram_range=(1,2),sublinear_tf=True,min_df=2); a=v.fit_transform(texts[tr]); b=v.transform(texts[te]); sv=TruncatedSVD(n_components=min(128,a.shape[1]-1),random_state=SEED); xtr=torch.tensor(sv.fit_transform(a),dtype=torch.float32); xte=torch.tensor(sv.transform(b),dtype=torch.float32)
  yt=torch.tensor(y[tr]); counts=torch.bincount(yt,minlength=len(le.classes_)).float(); w=len(yt)/(len(le.classes_)*counts.clamp_min(1))
  m=Net(xtr.shape[1],len(le.classes_)); opt=torch.optim.AdamW(m.parameters(),lr=2e-3,weight_decay=1e-4)
  for _ in range(80):
   opt.zero_grad(); z=m(xtr)
   if mode=='focal':
    ce=torch.nn.functional.cross_entropy(z,yt,weight=w,reduction='none'); loss=((1-torch.exp(-ce))**2*ce).mean()
   else: loss=torch.nn.functional.cross_entropy(z,yt,weight=w)
   loss.backward(); opt.step()
  pred[te]=m(xte).argmax(1).detach().numpy()
 return {'macro_f1':round(float(f1_score(y,pred,average='macro')),4),'accuracy':round(float(accuracy_score(y,pred)),4)}
res={'protocol':'OOF5 seed42; TF-IDF+SVD per fold; Task2 neural head only','weighted_ce':run('ce'),'focal_loss':run('focal')}; OUT.write_text(json.dumps(res,indent=2)); print(json.dumps(res,indent=2))
